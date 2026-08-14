param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,

    [string]$OutputDir = 'release'
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$SevenZip = Join-Path $Root '7z.exe'
$PackageName = "05-mpv-config-v${Version}"
$Stage = Join-Path $Root "build/$PackageName"
$OutputRoot = Join-Path $Root $OutputDir
$Archive = Join-Path $OutputRoot "$PackageName.7z"

if (-not (Test-Path -LiteralPath $SevenZip)) {
    throw "找不到 7z.exe"
}

if (Test-Path -LiteralPath $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}
$null = New-Item -ItemType Directory -Force -Path $Stage
$null = New-Item -ItemType Directory -Force -Path $OutputRoot

# 复制 portable_config（排除大型素材：shaders/vs 归 Extras，script-assets 启动 Logo 归 Base）
$configDest = Join-Path $Stage 'portable_config'
$configSrc = Join-Path $Root 'portable_config'
Write-Host "复制 portable_config/（排除 shaders vs script-assets cache files）..." -ForegroundColor Gray
$null = New-Item -ItemType Directory -Force $configDest
Copy-Item -Recurse -Force "$configSrc\*" $configDest
foreach ($exclude in @('shaders', 'vs', 'cache', 'files')) {
    $exPath = Join-Path $configDest $exclude
    if (Test-Path $exPath) { Remove-Item -Recurse -Force $exPath }
}
# 内置 HarmonyOS Sans SC 字体与其授权文件归 01 Base，05 Config 不重复携带
foreach ($exclude in @('fonts', 'licenses')) {
    $exPath = Join-Path $configDest $exclude
    if (Test-Path $exPath) { Remove-Item -Recurse -Force $exPath }
}
# 备份目录两级约定：
# - 项目根 backup/ = 用户级备份，不进公开包（也不在 portable_config 复制范围内）
# - portable_config 下各 backup/（如 backup、script-opts/backup、scripts/backup）= 开发级备份，
#   是开发升级过程中淘汰但曾可用的脚本/配置，体积小，随包保留以便回滚
# 启动 Logo 素材（启动页/起播格式 Logo）归 01 Base，Config 不重复携带
$assetsPath = Join-Path $configDest 'script-assets'
if (Test-Path $assetsPath) { Remove-Item -Recurse -Force $assetsPath }
    # 个人运行时状态（窗口记忆）不进公开包
    $stateFile = Join-Path $configDest 'script-opts/window_state.conf'
    if (Test-Path $stateFile) { Remove-Item -Force $stateFile }

    # Vanta 安装标记由 01 Base 写入，05 Config 不得覆盖（防止 05 覆盖版本标记）
    $vantaMarker = Join-Path $configDest '.vanta-version'
    if (Test-Path $vantaMarker) { Remove-Item -Force $vantaMarker }

# 项目说明文件：显式目标路径复制（README.MD 必须随 05 包分发）
foreach ($file in @('README.MD', '.gitignore')) {
    $src = Join-Path $Root $file
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $Stage $file) -Force
    }
}

# 打包前校验 README.MD 已进入构建目录（缺失即终止）
if (-not (Test-Path -LiteralPath (Join-Path $Stage 'README.MD'))) {
    throw 'README.MD 未进入 05 构建目录，终止打包。'
}

# 清理缓存
$cacheDirs = @(Get-ChildItem -LiteralPath $Stage -Recurse -Directory -Force `
    -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -in @('__pycache__', '.pytest_cache', '.mypy_cache')
    } | Sort-Object FullName -Descending)
foreach ($dir in $cacheDirs) {
    Remove-Item -LiteralPath $dir.FullName -Recurse -Force
}

$Readme = Join-Path $Stage 'README-Config包.txt'
@"
MPV Vanta Edition 05 Config v${Version}
==================================

这是最终覆盖层，包含个人定制的脚本、OSC 主题、字体和设置。
安装顺序上排最后，可覆盖前面所有包的同名文件。

安装与覆盖顺序：
  01. 01-mpv-base-v${Version}.7z
  02. 02-mpv-extras-v${Version}.7z.001（将 .002 放在同目录，只解压 .001）
  03. 03-mpv-fasterwhisper-addon-v${Version}.7z（可选）
  04. 04-mpv-lsfg-addon-v${Version}.7z（可选）
  05. 05-mpv-config-v${Version}.7z（本包，最后安装）

如果只更新配置，只需解压本包覆盖即可，无需重新安装 01～04。
"@ | Set-Content -LiteralPath $Readme -Encoding UTF8

if (Test-Path -LiteralPath $Archive) {
    Remove-Item -LiteralPath $Archive -Force
}
& $SevenZip a -t7z -mx=7 -md=64m -ms=on $Archive "$Stage\*"
if ($LASTEXITCODE -ne 0) { throw 'Config 包创建失败' }

Write-Host "Config 包已生成：$Archive" -ForegroundColor Green
