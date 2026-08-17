[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Manifest,
    [Parameter(Mandatory = $true)]
    [string]$PublicKey,
    [Parameter(Mandatory = $true)]
    [string]$ExpectedProduct,
    [string]$CurrentVersion,
    [string]$Package,
    [string]$ExpectedPublisher
)

$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $skillRoot)
$repoPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $repoPython) { $repoPython } else { (Get-Command python -ErrorAction Stop).Source }
$helper = Join-Path $PSScriptRoot 'verify-update-manifest.py'

$arguments = @($helper, '--manifest', $Manifest, '--public-key', $PublicKey, '--expected-product', $ExpectedProduct)
if ($CurrentVersion) { $arguments += @('--current-version', $CurrentVersion) }
if ($Package) { $arguments += @('--package', $Package) }
$output = & $python @arguments 2>&1
if ($LASTEXITCODE -ne 0) { throw ($output -join [Environment]::NewLine) }
$output | Write-Output

if ($Package) {
    if (-not $ExpectedPublisher) { throw 'ExpectedPublisher is required when Package is provided' }
    $signature = Get-AuthenticodeSignature -LiteralPath $Package
    if ($signature.Status -ne 'Valid' -or -not $signature.SignerCertificate) {
        throw "Authenticode verification failed: $($signature.Status) $($signature.StatusMessage)"
    }
    if (-not [string]::Equals($signature.SignerCertificate.Subject, $ExpectedPublisher, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Authenticode publisher mismatch: $($signature.SignerCertificate.Subject)"
    }
    Write-Output "OK:authenticode-valid:$($signature.SignerCertificate.Subject)"
}
