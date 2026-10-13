# 从已有运行环境字体生成 OSD 精简目录，避免把重复字体副本提交到 Git。
param(
    [string]$FontProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$FontProjectRoot = (Resolve-Path -LiteralPath $FontProjectRoot).Path
$FontManifestPath = Join-Path $PSScriptRoot 'osd-fonts-manifest.json'
$FontManifest = Get-Content -LiteralPath $FontManifestPath -Encoding UTF8 -Raw | ConvertFrom-Json
$FontSourceDirectory = Join-Path $FontProjectRoot 'portable_config/fonts'
$FontOutputDirectory = Join-Path $FontSourceDirectory 'osd'

# 先检查全部源字体，缺文件或版本不匹配时不生成不完整的目录。
if (-not $VerifyOnly) {
    foreach ($FontEntry in $FontManifest.files) {
        $FontSource = Join-Path $FontSourceDirectory $FontEntry.name
        if (-not (Test-Path -LiteralPath $FontSource -PathType Leaf)) {
            throw "缺少字体：$FontSource。请先恢复现有 Base 运行包中的完整字体。"
        }
        if ((Get-FileHash -LiteralPath $FontSource -Algorithm SHA256).Hash -ne $FontEntry.sha256) {
            throw "字体版本与清单不同：$($FontEntry.name)。请使用本轮对应的原始字体。"
        }
    }
    $null = New-Item -ItemType Directory -Path $FontOutputDirectory -Force
    foreach ($FontEntry in $FontManifest.files) {
        Copy-Item -LiteralPath (Join-Path $FontSourceDirectory $FontEntry.name) -Destination (Join-Path $FontOutputDirectory $FontEntry.name) -Force
    }
}
foreach ($FontEntry in $FontManifest.files) {
    $FontOutput = Join-Path $FontOutputDirectory $FontEntry.name
    if (-not (Test-Path -LiteralPath $FontOutput -PathType Leaf)) {
        throw "OSD 字体缺失：$FontOutput。请先执行不带 -VerifyOnly 的生成命令。"
    }
    if ((Get-FileHash -LiteralPath $FontOutput -Algorithm SHA256).Hash -ne $FontEntry.sha256) {
        throw "OSD 字体校验失败：$($FontEntry.name)"
    }
}
Write-Output "OSD 字体已校验：$(@($FontManifest.files).Count) 个文件，目录 $FontOutputDirectory"
