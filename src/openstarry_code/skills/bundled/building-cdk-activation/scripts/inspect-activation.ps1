[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [ValidateSet('markdown', 'json')]
    [string]$Format = 'markdown',
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$root = Get-Item -LiteralPath $Path
if (-not $root.PSIsContainer) { throw "Path must be a directory: $Path" }

$excluded = '\\(\.git|\.venv|venv|node_modules|dist|build|bin|obj|third_party|vendor)\\'
$textExtensions = @('.py', '.qml', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.cs', '.xaml', '.js', '.cjs', '.mjs', '.ts', '.tsx', '.json', '.toml', '.xml', '.config', '.ps1', '.pro', '.cmake', '.txt', '.pem', '.key')
$files = @(Get-ChildItem -LiteralPath $root.FullName -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch $excluded -and $_.Length -le 2MB })

function Get-RelativePath([string]$FullName) {
    $prefix = $root.FullName.TrimEnd('\') + '\'
    if ($FullName.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        return $FullName.Substring($prefix.Length).Replace('\', '/')
    }
    return $FullName
}

$records = foreach ($file in $files) {
    $text = ''
    if ($textExtensions -contains $file.Extension.ToLowerInvariant()) {
        try { $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop } catch { $text = '' }
    }
    [pscustomobject]@{ File = $file; Relative = Get-RelativePath $file.FullName; Text = $text }
}

$stacks = New-Object System.Collections.Generic.List[string]
if ($records | Where-Object {
    $_.File.Extension -eq '.qml' -or
    $_.Text -match 'PySide6|PyQt[56]|QtQuick|Q_OBJECT|Q_PROPERTY|Q_INVOKABLE|find_package\s*\(\s*Qt|QT\s*\+=' 
}) { $stacks.Add('Qt/QML') }
if ($records | Where-Object {
    $_.Text -match 'Microsoft\.UI\.Xaml|Microsoft\.WindowsAppSDK|PresentationFramework|<UseWPF>true</UseWPF>' -or
    ($_.File.Extension -eq '.xaml' -and $_.Text -match '<(Window|NavigationWindow)\b' -and $_.Text -match 'schemas\.microsoft\.com/winfx/2006/xaml/presentation')
}) { $stacks.Add('WPF/WinUI') }
if ($records | Where-Object { $_.File.Name -eq 'package.json' -and $_.Text -match 'electron' }) { $stacks.Add('Electron') }
if ($stacks.Count -eq 0) { $stacks.Add('Unknown') }

$activationPattern = '(?i)cdk|licen[cs]e|activation|activate|激活|授权'
$updatePattern = '(?i)auto.?update|updater|update.?manifest|check.?update|检查更新|自动更新'
$activationFiles = @($records | Where-Object { $_.Relative -match $activationPattern -or $_.Text -match $activationPattern } | Select-Object -ExpandProperty Relative -Unique)
$updateFiles = @($records | Where-Object { $_.Relative -match $updatePattern -or $_.Text -match $updatePattern } | Select-Object -ExpandProperty Relative -Unique)
$testFiles = @($records | Where-Object { $_.Relative -match '(?i)(^|/)(tests?|specs?)(/|$)|(?i)(test|spec)[_.-]' } | Select-Object -ExpandProperty Relative -Unique)

$findings = New-Object System.Collections.Generic.List[object]
foreach ($record in $records) {
    if ($record.File.Name -match '(?i)(private|signing).*(key|pem|pfx|p12)' -or $record.Text -match '-----BEGIN (ED25519 |RSA |EC )?PRIVATE KEY-----') {
        $findings.Add([pscustomobject]@{
            code = 'possible-private-key'; severity = 'critical'; confidence = 'high'; path = $record.Relative
            evidence = 'Filename or content resembles private signing material; confirm and remove it from client/public artifacts.'
        })
    }
    if ($record.File.Extension -in @('.qml', '.xaml', '.js', '.ts', '.tsx') -and $record.Text -match '(?i)Ed25519|verify\s*\(|createHash|Get-AuthenticodeSignature') {
        $findings.Add([pscustomobject]@{
            code = 'crypto-in-ui-layer'; severity = 'high'; confidence = 'medium'; path = $record.Relative
            evidence = 'Cryptographic operation appears in a presentation file; verify the trust decision is owned by a service/background process.'
        })
    }
}
if ($updateFiles.Count -eq 0) {
    $findings.Add([pscustomobject]@{ code = 'no-update-surface'; severity = 'info'; confidence = 'medium'; path = '';
        evidence = 'No update-related file or content was detected by the static scan.' })
}

$result = [ordered]@{
    root = $root.FullName
    stacks = $stacks.ToArray()
    activation_files = $activationFiles
    update_files = $updateFiles
    test_files = $testFiles
    findings = $findings.ToArray()
    note = 'Static evidence only. Confirm runtime ownership, call paths, and executed tests before concluding.'
}

if ($Format -eq 'json') {
    $rendered = $result | ConvertTo-Json -Depth 6
} else {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add('# CDK Activation and Update Inspection')
    $lines.Add('')
    $lines.Add("- Root: ``$($result.root)``")
    $lines.Add("- Stacks: $($result.stacks -join ', ')")
    $lines.Add("- Activation evidence: $($activationFiles.Count)")
    $lines.Add("- Update evidence: $($updateFiles.Count)")
    $lines.Add("- Test evidence: $($testFiles.Count)")
    foreach ($section in @(
        [pscustomobject]@{ Name = 'Activation evidence'; Paths = $activationFiles },
        [pscustomobject]@{ Name = 'Update evidence'; Paths = $updateFiles },
        [pscustomobject]@{ Name = 'Test evidence'; Paths = $testFiles }
    )) {
        $lines.Add('')
        $lines.Add("## $($section.Name)")
        if ($section.Paths.Count -eq 0) { $lines.Add('- None detected') }
        else { foreach ($evidencePath in $section.Paths) { $lines.Add("- ``$evidencePath``") } }
    }
    $lines.Add('')
    $lines.Add('## Findings')
    foreach ($finding in $findings) {
        $location = if ($finding.path) { " at ``$($finding.path)``" } else { '' }
        $lines.Add("- [$($finding.severity)] $($finding.code)$location — $($finding.evidence)")
    }
    $lines.Add('')
    $lines.Add("> $($result.note)")
    $rendered = $lines -join [Environment]::NewLine
}

if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Set-Content -LiteralPath $OutputPath -Value $rendered -Encoding UTF8
    Write-Output "OK:wrote:$OutputPath"
} else {
    Write-Output $rendered
}
