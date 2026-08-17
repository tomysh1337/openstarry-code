[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$Task,

    [ValidateSet(
        'security-reverse',
        'engineering',
        'cloud-ops',
        'frontend-creative',
        'docs-research',
        'automation-catalog'
    )]
    [string]$Group,

    [ValidateRange(1, 100)]
    [int]$Limit = 8,

    [switch]$IncludeSources,

    [switch]$Json
)

$skillRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$finder = Join-Path $skillRoot 'skill-library-router\scripts\find_local_skill.py'

if (-not (Test-Path -LiteralPath $finder -PathType Leaf)) {
    throw "Local skill index was not found: $finder"
}

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    $python = $py.Source
    $pythonArgs = @('-3')
}
else {
    $fallback = Get-Command python -ErrorAction SilentlyContinue
    if (-not $fallback) {
        throw 'Python 3 is required to query the local skill index.'
    }
    $python = $fallback.Source
    $pythonArgs = @()
}

$finderArgs = @($finder, $Task, '--limit', $Limit)
if ($Group) {
    $finderArgs += @('--group', $Group)
}
if ($IncludeSources) {
    $finderArgs += '--include-sources'
}
if ($Json) {
    $finderArgs += '--json'
}

& $python @pythonArgs @finderArgs
exit $LASTEXITCODE
