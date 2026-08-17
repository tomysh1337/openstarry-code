[CmdletBinding()]
param(
    [string]$DestinationRoot,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $PSScriptRoot
$skillName = Split-Path -Leaf $source
if (-not $DestinationRoot) {
    $codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
    $DestinationRoot = Join-Path $codexRoot 'skills'
}
$DestinationRoot = [System.IO.Path]::GetFullPath($DestinationRoot)
$target = Join-Path $DestinationRoot $skillName
$stage = Join-Path $DestinationRoot (".$skillName.staging." + [guid]::NewGuid().ToString('N'))
$backup = $null

function Get-TreeFingerprint([string]$Root) {
    $prefix = $Root.TrimEnd('\') + '\'
    $entries = Get-ChildItem -LiteralPath $Root -Recurse -File | ForEach-Object {
        [pscustomobject]@{
            path = $_.FullName.Substring($prefix.Length).Replace('\', '/')
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    } | Sort-Object path
    return ($entries | ConvertTo-Json -Compress)
}

New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
try {
    New-Item -ItemType Directory -Path $stage | Out-Null
    Copy-Item -Path (Join-Path $source '*') -Destination $stage -Recurse -Force
    if (-not (Test-Path -LiteralPath (Join-Path $stage 'SKILL.md'))) { throw 'staged skill is missing SKILL.md' }
    if (Select-String -Path (Join-Path $stage 'SKILL.md') -Pattern '\b(TODO|TBD)\b' -Quiet) {
        throw 'staged SKILL.md contains TODO/TBD placeholders'
    }
    $sourceFingerprint = Get-TreeFingerprint $source
    $stageFingerprint = Get-TreeFingerprint $stage
    if ($sourceFingerprint -ne $stageFingerprint) { throw 'staged skill hash does not match source' }

    if (Test-Path -LiteralPath $target) {
        if ((Get-TreeFingerprint $target) -eq $sourceFingerprint) {
            Remove-Item -LiteralPath $stage -Recurse -Force
            Write-Output "OK:already-current:$target"
            return
        }
        if (-not $Force) { throw "destination differs; rerun with -Force after reviewing: $target" }
        $backup = "$target.backup.$((Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmssfff'))"
        Move-Item -LiteralPath $target -Destination $backup
        Write-Output "OK:backup:$backup"
    }
    Move-Item -LiteralPath $stage -Destination $target
    if ((Get-TreeFingerprint $target) -ne $sourceFingerprint) { throw 'installed skill hash does not match source' }
    Write-Output "OK:installed:$target"
}
catch {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
    if ($backup -and (Test-Path -LiteralPath $backup)) {
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue }
        Move-Item -LiteralPath $backup -Destination $target -ErrorAction SilentlyContinue
    }
    throw
}
