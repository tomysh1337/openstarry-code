[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $skillRoot)
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    $python = (Get-Command python -ErrorAction Stop).Source
}

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
}

$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("cdk-skill-test-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    $fixture = Join-Path $temp 'fixture'
    New-Item -ItemType Directory -Path (Join-Path $fixture 'app\qml') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $fixture 'app\core') -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $fixture 'pyproject.toml') -Encoding UTF8 -Value '[project]'
    Set-Content -LiteralPath (Join-Path $fixture 'app\qml\ActivationPage.qml') -Encoding UTF8 -Value 'TextInput { placeholderText: "CDK" }'
    Set-Content -LiteralPath (Join-Path $fixture 'app\core\license.py') -Encoding UTF8 -Value 'class LicenseVerifier: pass # Ed25519 activation cache'
    Set-Content -LiteralPath (Join-Path $fixture 'update.py') -Encoding UTF8 -Value 'manifest_url = "https://updates.example.test/manifest.json"'
    Set-Content -LiteralPath (Join-Path $fixture 'MainPage.xaml') -Encoding UTF8 -Value '<ContentPage xmlns="http://xamarin.com/schemas/2014/forms" />'
    Set-Content -LiteralPath (Join-Path $fixture 'license-material.pem') -Encoding ASCII -Value '-----BEGIN PRIVATE KEY-----'

    $json = & (Join-Path $PSScriptRoot 'inspect-activation.ps1') -Path $fixture -Format json | ConvertFrom-Json
    Assert-True ($json.stacks -contains 'Qt/QML') 'Qt/QML stack should be detected'
    Assert-True (-not ($json.stacks -contains 'WPF/WinUI')) 'generic Xamarin/MAUI XAML should not be classified as WPF/WinUI'
    Assert-True ($json.activation_files.Count -ge 1) 'activation evidence should be reported'
    $privateKeyFindings = @($json.findings | Where-Object { $_.code -eq 'possible-private-key' })
    Assert-True ($privateKeyFindings.Count -ge 1) 'private key risk should be reported'
    $markdown = & (Join-Path $PSScriptRoot 'inspect-activation.ps1') -Path $fixture -Format markdown
    Assert-True (($markdown -join "`n") -match 'app/qml/ActivationPage\.qml') 'markdown report should include activation evidence paths'

    $cppFixture = Join-Path $temp 'qt-cpp-fixture'
    New-Item -ItemType Directory -Path $cppFixture | Out-Null
    Set-Content -LiteralPath (Join-Path $cppFixture 'CMakeLists.txt') -Encoding UTF8 -Value 'find_package(Qt6 REQUIRED COMPONENTS Quick Network)'
    Set-Content -LiteralPath (Join-Path $cppFixture 'ActivationBridge.cpp') -Encoding UTF8 `
        -Value 'class ActivationBridge : public QObject { Q_OBJECT Q_PROPERTY(QString state READ state) }; // -----BEGIN PRIVATE KEY-----'
    $cppJson = & (Join-Path $PSScriptRoot 'inspect-activation.ps1') -Path $cppFixture -Format json | ConvertFrom-Json
    Assert-True ($cppJson.stacks -contains 'Qt/QML') 'Qt/C++ stack should be detected'
    Assert-True (@($cppJson.findings | Where-Object { $_.code -eq 'possible-private-key' }).Count -eq 1) 'private key in Qt/C++ source should be reported'

    $release = Join-Path $temp 'release'
    New-Item -ItemType Directory -Path $release | Out-Null
    $generator = Join-Path $temp 'test-fixture.py'
    @'
import base64, hashlib, json, pathlib, sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
root = pathlib.Path(sys.argv[1])
private = Ed25519PrivateKey.generate()
public = private.public_key()
package = b"test installer bytes"
(root / "setup.exe").write_bytes(package)
manifest = {
    "schema_version": 1,
    "product": "example-product",
    "channel": "stable",
    "version": "1.2.3",
    "published_at": "2026-07-14T00:00:00Z",
    "release_notes_url": "https://updates.example.test/releases/1.2.3",
    "package": {
        "url": "https://updates.example.test/packages/setup-1.2.3.exe",
        "size": len(package),
        "sha256": hashlib.sha256(package).hexdigest(),
        "signature": base64.urlsafe_b64encode(private.sign(hashlib.sha256(package).digest())).rstrip(b"=").decode(),
    },
}
raw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
(root / "manifest.json").write_bytes(raw)
(root / "manifest.json.sig").write_text(base64.urlsafe_b64encode(private.sign(raw)).rstrip(b"=").decode())
(root / "invalid-semver.json").write_bytes(raw.replace(b'"1.2.3"', b'"1.2.3-01"'))
invalid_raw = (root / "invalid-semver.json").read_bytes()
(root / "invalid-semver.json.sig").write_text(base64.urlsafe_b64encode(private.sign(invalid_raw)).rstrip(b"=").decode())
(root / "public.pem").write_bytes(public.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
'@ | Set-Content -LiteralPath $generator -Encoding UTF8
    & $python $generator $release
    if ($LASTEXITCODE -ne 0) { throw 'fixture generation failed' }

    $validation = & (Join-Path $PSScriptRoot 'validate-update-manifest.ps1') `
        -Manifest (Join-Path $release 'manifest.json') -PublicKey (Join-Path $release 'public.pem') `
        -ExpectedProduct 'example-product' -CurrentVersion '1.0.0'
    Assert-True ($validation -match 'OK:manifest-valid') 'valid signed manifest should pass'
    $packageValidation = & $python (Join-Path $PSScriptRoot 'verify-update-manifest.py') `
        --manifest (Join-Path $release 'manifest.json') --public-key (Join-Path $release 'public.pem') `
        --package (Join-Path $release 'setup.exe') --expected-product example-product --current-version 1.0.0
    Assert-True (($packageValidation -join "`n") -match 'OK:package-crypto-valid') 'package size, hash, and Ed25519 signature should pass'
    $unsignedFailed = $false
    try {
        & (Join-Path $PSScriptRoot 'validate-update-manifest.ps1') `
            -Manifest (Join-Path $release 'manifest.json') -PublicKey (Join-Path $release 'public.pem') `
            -Package (Join-Path $release 'setup.exe') -ExpectedProduct 'example-product' `
            -CurrentVersion '1.0.0' -ExpectedPublisher 'CN=Test Publisher'
    } catch { $unsignedFailed = $_.Exception.Message -match 'Authenticode verification failed' }
    Assert-True $unsignedFailed 'unsigned Windows package should fail Authenticode enforcement'

    $wrongProductFailed = $false
    try {
        & (Join-Path $PSScriptRoot 'validate-update-manifest.ps1') `
            -Manifest (Join-Path $release 'manifest.json') -PublicKey (Join-Path $release 'public.pem') `
            -ExpectedProduct 'wrong-product'
    } catch { $wrongProductFailed = $true }
    Assert-True $wrongProductFailed 'wrong expected product should fail'

    $sameVersionFailed = $false
    try {
        & (Join-Path $PSScriptRoot 'validate-update-manifest.ps1') `
            -Manifest (Join-Path $release 'manifest.json') -PublicKey (Join-Path $release 'public.pem') `
            -ExpectedProduct 'example-product' -CurrentVersion '1.2.3'
    } catch { $sameVersionFailed = $true }
    Assert-True $sameVersionFailed 'same-version replacement should fail'

    $semverFailed = $false
    try {
        & (Join-Path $PSScriptRoot 'validate-update-manifest.ps1') `
            -Manifest (Join-Path $release 'invalid-semver.json') -PublicKey (Join-Path $release 'public.pem') `
            -ExpectedProduct 'example-product'
    } catch { $semverFailed = $_.Exception.Message -match 'leading zero|semantic version' }
    Assert-True $semverFailed 'invalid semantic version prerelease should fail'

    Set-Content -LiteralPath (Join-Path $release 'manifest.json.sig') -Encoding ASCII -Value 'invalid'
    $failed = $false
    try {
        & (Join-Path $PSScriptRoot 'validate-update-manifest.ps1') `
            -Manifest (Join-Path $release 'manifest.json') -PublicKey (Join-Path $release 'public.pem') `
            -ExpectedProduct 'example-product'
    } catch { $failed = $_.Exception.Message -match 'signature|base64url' }
    Assert-True $failed 'invalid manifest signature should fail'

    $destination = Join-Path $temp 'personal-skills'
    & (Join-Path $PSScriptRoot 'install-personal.ps1') -DestinationRoot $destination
    Assert-True (Test-Path -LiteralPath (Join-Path $destination 'building-cdk-activation\SKILL.md')) 'personal install should contain SKILL.md'
    $repeat = & (Join-Path $PSScriptRoot 'install-personal.ps1') -DestinationRoot $destination
    Assert-True ($repeat -match 'OK:already-current') 'repeat installation should be idempotent'
    Add-Content -LiteralPath (Join-Path $destination 'building-cdk-activation\SKILL.md') -Value '# local drift'
    $conflictFailed = $false
    try { & (Join-Path $PSScriptRoot 'install-personal.ps1') -DestinationRoot $destination } catch { $conflictFailed = $true }
    Assert-True $conflictFailed 'different destination should require -Force'
    $forced = & (Join-Path $PSScriptRoot 'install-personal.ps1') -DestinationRoot $destination -Force
    Assert-True (($forced -join "`n") -match 'OK:installed') 'forced update should install source'
    Assert-True (@(Get-ChildItem -LiteralPath $destination -Directory -Filter 'building-cdk-activation.backup.*').Count -eq 1) 'forced update should retain one backup'

    Write-Output 'OK:all-script-tests-passed'
}
finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
