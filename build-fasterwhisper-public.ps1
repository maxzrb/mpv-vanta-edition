param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,

    [string]$OutputDir = 'release'
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$SevenZip = Join-Path $Root '7z.exe'
$FwDir = Join-Path $Root 'Faster-Whisper-XXL'
$FwExe = Join-Path $FwDir 'faster-whisper-xxl.exe'
$PackageName = "03-mpv-fasterwhisper-addon-v${Version}"
$Stage = Join-Path $Root "build/$PackageName"
$OutputRoot = Join-Path $Root $OutputDir
$Archive = Join-Path $OutputRoot "$PackageName.7z"

foreach ($required in @($SevenZip, $FwExe)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "缺少 Faster-Whisper 增量包所需文件：$required"
    }
}

if (Test-Path -LiteralPath $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}
$null = New-Item -ItemType Directory -Force -Path $Stage
$null = New-Item -ItemType Directory -Force -Path $OutputRoot

# 复制完整 Faster-Whisper-XXL 公开版
Write-Host "复制 Faster-Whisper-XXL ..." -ForegroundColor Gray
Copy-Item -LiteralPath $FwDir -Destination (Join-Path $Stage 'Faster-Whisper-XXL') -Recurse

# 清理运行缓存
$fwCacheDirs = @(Get-ChildItem -LiteralPath $Stage -Recurse -Directory -Force `
    -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -in @('__pycache__', '.pytest_cache', '.mypy_cache')
    } | Sort-Object FullName -Descending)
foreach ($dir in $fwCacheDirs) {
    Remove-Item -LiteralPath $dir.FullName -Recurse -Force
}

$Readme = Join-Path $Stage 'README-FasterWhisper扩展包.txt'
@"
MPV Faster-Whisper 扩展包 v${Version}

本包为 mpv-vanta-edition 的 AI 语音识别字幕扩展，可公开分发。
语音模型由 Faster-Whisper 在首次选择时自动下载。

安装与覆盖顺序：
  01. 01-mpv-base-v${Version}.7z
  02. 02-mpv-extras-v${Version}.7z.001（将 .002 放在同目录，只解压 .001）
  03. 03-mpv-fasterwhisper-addon-v${Version}.7z（本包）
  04. 04-mpv-lsfg-addon-v${Version}.7z（可选补帧扩展）
  05. 05-mpv-config-v${Version}.7z（个人设置，最后安装覆盖）

包边界说明：
  Faster-Whisper 菜单和控制脚本已经包含在 Base/Config 中。
  本包不覆盖 Config 或 Extras 文件，以后单独更新 Config 不需要重新解压本包。

Contains:
- Faster-Whisper-XXL public r245.4        ~4.4 GB (runtime only)
"@ | Set-Content -LiteralPath $Readme -Encoding UTF8

# 门禁：所有 EXE 必须位于 Faster-Whisper-XXL 目录内（官方发行自带）
$fwStageDir = Join-Path $Stage 'Faster-Whisper-XXL'
$StagedExecutables = @(Get-ChildItem -LiteralPath $Stage -Recurse -File -Filter '*.exe' `
    -ErrorAction SilentlyContinue)
$UnexpectedExes = @($StagedExecutables | Where-Object {
    $_.FullName -notlike "$fwStageDir\*"
})
if ($UnexpectedExes.Count -gt 0) {
    throw "Faster-Whisper 包检测到 FW 目录外的 EXE：$($UnexpectedExes.FullName -join ', ')"
}

# 禁止的运行时/构建产物
$GeneratedExtensions = @(
    '.pyc', '.pyo', '.log', '.tmp', '.bak',
    '.pdb', '.obj', '.ilk', '.dmp'
)
$GeneratedFiles = @(Get-ChildItem -LiteralPath $Stage -Recurse -File -Force `
    -ErrorAction SilentlyContinue | Where-Object {
        $_.Extension.ToLowerInvariant() -in $GeneratedExtensions
    })
if ($GeneratedFiles.Count -gt 0) {
    throw "Faster-Whisper 包仍含生成文件：$($GeneratedFiles.FullName -join ', ')"
}

if (Test-Path -LiteralPath $Archive) {
    Remove-Item -LiteralPath $Archive -Force
}
& $SevenZip a -t7z -mx=7 -md=64m -ms=on $Archive "$Stage\*"
if ($LASTEXITCODE -ne 0) { throw 'Faster-Whisper 增量包创建失败' }

Write-Host "Faster-Whisper 增量包已生成：$Archive" -ForegroundColor Green
