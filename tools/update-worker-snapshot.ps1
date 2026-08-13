<#
.SYNOPSIS
  Update the built-in release snapshot (FALLBACK_RELEASE) of the dl.loliland.cn
  download-station Cloudflare Worker.

.DESCRIPTION
  OPTIONAL. Normally the Worker maintains its own snapshot automatically: the
  /api/latest endpoint writes every successful GitHub API response into a
  Cloudflare KV binding (SNAPSHOT_KV), and a Cron Trigger refreshes that KV on
  schedule. So after a release you do NOT need to touch the Worker at all.

  This script only rewrites the hard-coded FALLBACK_RELEASE constant in
  docs/cf-github-proxy-worker.js, which is the very last fallback when the KV
  is empty/unbound. Run it if you want the built-in snapshot to be current too
  (e.g. first deployment without KV, or as belt-and-braces), then redeploy the
  Worker to Cloudflare.

.PARAMETER Repo
  Target repository. Default: maxzrb/mpv-vanta-edition.

.PARAMETER WorkerPath
  Path to the Worker source file. Default: docs/cf-github-proxy-worker.js
  relative to the repository root.

.PARAMETER Token
  Optional GitHub token to raise API quota; falls back to env GITHUB_TOKEN.

.EXAMPLE
  pwsh -File tools\update-worker-snapshot.ps1
#>
[CmdletBinding()]
param(
    [string]$Repo = 'maxzrb/mpv-vanta-edition',
    [string]$WorkerPath = (Join-Path $PSScriptRoot '..\docs\cf-github-proxy-worker.js'),
    [string]$Token = ''
)

$ErrorActionPreference = 'Stop'

$workerFull = [System.IO.Path]::GetFullPath($WorkerPath)
if (-not (Test-Path -LiteralPath $workerFull)) {
    throw "Worker source file not found: $workerFull"
}

Write-Host "Fetching latest release from $Repo ..." -ForegroundColor Cyan
$headers = @{
    'User-Agent' = 'vanta-dl-snapshot'
    'Accept'     = 'application/vnd.github+json'
}
if (-not $Token) { $Token = $env:GITHUB_TOKEN }
if ($Token) { $headers['Authorization'] = "Bearer $Token" }

try {
    $resp = Invoke-WebRequest -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers $headers -TimeoutSec 30
}
catch {
    throw "GitHub API request failed: $($_.Exception.Message)"
}
$release = $resp.Content | ConvertFrom-Json

# Keep published_at as the original ISO-8601 string (PowerShell converts it to
# a localized DateTime otherwise, which would break the frontend's Date parsing).
$publishedAt = [string]$release.published_at
if ($resp.Content -match '"published_at"\s*:\s*"([^"]+)"') {
    $publishedAt = $matches[1]
}

# ---- Build the snapshot JSON by hand so 'assets' is always an array ----
function ConvertTo-JsonString([string]$value) {
    # Escape backslashes and double quotes for JSON
    return $value.Replace('\', '\\').Replace('"', '\"')
}

$assetLines = @()
for ($i = 0; $i -lt $release.assets.Count; $i++) {
    $a = $release.assets[$i]
    $comma = if ($i -lt $release.assets.Count - 1) { ',' } else { '' }
    $assetLines += "        {"
    $assetLines += "            `"name`": `"$(ConvertTo-JsonString ([string]$a.name))`","
    $assetLines += "            `"size`": $([long]$a.size),"
    $assetLines += "            `"content_type`": `"$(ConvertTo-JsonString ([string]$a.content_type))`","
    $assetLines += "            `"browser_download_url`": `"$(ConvertTo-JsonString ([string]$a.browser_download_url))`""
    $assetLines += "        }$comma"
}

$json = @(
    '{'
    "    `"tag_name`": `"$(ConvertTo-JsonString ([string]$release.tag_name))`","
    "    `"name`": `"$(ConvertTo-JsonString ([string]$release.name))`","
    "    `"published_at`": `"$(ConvertTo-JsonString $publishedAt)`","
    "    `"html_url`": `"$(ConvertTo-JsonString ([string]$release.html_url))`","
    '    "assets": ['
    $assetLines
    '    ]'
    '}'
) -join "`n"

# ---- Replace the FALLBACK_RELEASE block in the Worker source ----
$content = [System.IO.File]::ReadAllText($workerFull, [System.Text.Encoding]::UTF8)
$pattern = 'const FALLBACK_RELEASE = \{[\s\S]*?\n\}'
if ($content -notmatch $pattern) {
    throw 'FALLBACK_RELEASE block not found in Worker source; nothing replaced.'
}

$replacement = "const FALLBACK_RELEASE = $json"
$newContent = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern, $replacement)

# ---- Write back: UTF-8 without BOM + LF line endings (repo convention) ----
$newContent = $newContent -replace "`r`n", "`n"
[System.IO.File]::WriteAllText($workerFull, $newContent, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "Updated: $workerFull" -ForegroundColor Green
Write-Host "  Version: $($release.tag_name)"
Write-Host "  Assets:  $($release.assets.Count)"
Write-Host ''
Write-Host 'Next: redeploy docs/cf-github-proxy-worker.js to Cloudflare Workers (dl.loliland.cn).' -ForegroundColor Yellow
