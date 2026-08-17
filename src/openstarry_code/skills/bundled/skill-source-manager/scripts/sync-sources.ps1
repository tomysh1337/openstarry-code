[CmdletBinding()]
param(
    [string]$SourceRoot = (Join-Path $HOME ".codex\skill-sources"),
    [switch]$SkipWebCatalogs
)

$ErrorActionPreference = "Stop"

Get-ChildItem -LiteralPath $SourceRoot -Directory | ForEach-Object {
    if (Test-Path -LiteralPath (Join-Path $_.FullName ".git")) {
        Write-Host "Updating $($_.Name)"
        & git -C $_.FullName pull --ff-only
        if ($LASTEXITCODE -ne 0) {
            throw "git pull failed for $($_.FullName)"
        }
    }
}

if (-not $SkipWebCatalogs) {
    $catalogs = @(
        @{
            Directory = "skillhub-cn"
            File = "catalog-top-100.json"
            Url = "https://api.skillhub.cn/api/skills?page=1&pageSize=100&sortBy=installs&order=desc"
        },
        @{
            Directory = "alibaba-skills"
            File = "index.html"
            Url = "https://skills.alibaba.org.cn/"
        },
        @{
            Directory = "skillsbot-cn"
            File = "index.html"
            Url = "https://www.skillsbot.cn/"
        }
    )
    foreach ($catalog in $catalogs) {
        $directory = Join-Path $SourceRoot $catalog.Directory
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
        Invoke-WebRequest -UseBasicParsing $catalog.Url -OutFile (Join-Path $directory $catalog.File)
        Write-Host "Refreshed $($catalog.Directory)/$($catalog.File)"
    }
}
