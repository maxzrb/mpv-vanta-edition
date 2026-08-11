param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,

    [string]$OutputDir = 'release'
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$SevenZip = Join-Path $Root '7z.exe'
$LayerDist = Join-Path $Root 'research/lsfg-vk-win/dist/windows'
$LayerDll = Join-Path $LayerDist 'bin/lsfg-vk-layer.dll'
$LayerManifest = Join-Path $LayerDist 'share/vulkan/implicit_layer.d/VkLayer_LSFGVK_frame_generation.json'
$LosslessDll = Join-Path $Root 'Lossless Scaling/Lossless.dll'
$PackageName = "04-mpv-lsfg-addon-v${Version}"
$Stage = Join-Path $Root "build/$PackageName"
$OutputRoot = Join-Path $Root $OutputDir
$Archive = Join-Path $OutputRoot "$PackageName.7z"

foreach ($required in @($SevenZip, $LayerDll, $LayerManifest, $LosslessDll)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "缺少 LSFG 公开包所需文件：$required"
    }
}

if (Test-Path -LiteralPath $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}
$null = New-Item -ItemType Directory -Force -Path $Stage
$null = New-Item -ItemType Directory -Force -Path $OutputRoot

# 公开包交付 GPL Vulkan Layer，并内置 Lossless.dll（用户确认的既定发布内容）。
$LayerTarget = Join-Path $Stage 'lsfg-vk'
$null = New-Item -ItemType Directory -Force -Path $LayerTarget
Copy-Item -LiteralPath $LayerDll -Destination $LayerTarget
Copy-Item -LiteralPath $LayerManifest -Destination $LayerTarget
Copy-Item -LiteralPath (Join-Path $Root 'start-mpv-lsfg.ps1') -Destination $Stage

# LSFG 控制脚本自身也随包更新，避免 Lua 侧改动未包含在 Base 中
$ControlScriptDest = Join-Path $Stage 'portable_config/scripts'
$null = New-Item -ItemType Directory -Force -Path $ControlScriptDest
Copy-Item -LiteralPath (Join-Path $Root 'portable_config/scripts/lsfg_control.lua') `
    -Destination $ControlScriptDest

# 内置 Lossless.dll，解压即可使用；不复制 Steam 应用的其他文件。
$LosslessTarget = Join-Path $Stage 'Lossless Scaling'
$null = New-Item -ItemType Directory -Force -Path $LosslessTarget
Copy-Item -LiteralPath $LosslessDll -Destination (Join-Path $LosslessTarget 'Lossless.dll')
$LosslessNote = Join-Path $LosslessTarget '内置说明.txt'
@'
本目录已由 04 LSFG 扩展包内置 Lossless.dll，解压后即可使用 LSFG 补帧。
Lossless Scaling 为商业软件，尚未购买正版授权的用户请自行决定是否支持正版。
'@ | Set-Content -LiteralPath $LosslessNote -Encoding UTF8

# LSFG 菜单和状态脚本归 01/02 配置包管理。04 只增加运行层、启动器、
# 对应源码和说明，避免以后单独更新 Config 时发生跨包覆盖。

# 随二进制交付对应 GPL 源码，但排除本机 build 目录和重复的编译产物。
$ResearchTarget = Join-Path $Stage 'research/lsfg-vk-win'
$null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ResearchTarget)
Copy-Item -LiteralPath (Join-Path $Root 'research/lsfg-vk-win') `
    -Destination $ResearchTarget -Recurse

$ResearchBuild = Join-Path $ResearchTarget 'build'
if (Test-Path -LiteralPath $ResearchBuild) {
    Remove-Item -LiteralPath $ResearchBuild -Recurse -Force
}
$ResearchRuntimeBin = Join-Path $ResearchTarget 'dist/windows/bin'
if (Test-Path -LiteralPath $ResearchRuntimeBin) {
    Remove-Item -LiteralPath $ResearchRuntimeBin -Recurse -Force
}

$Readme = Join-Path $Stage 'README-LSFG公开扩展包.txt'
@"
MPV LSFG 公开扩展包 v${Version}

本包可公开分发，已内置 Lossless.dll，解压后即可开箱使用 LSFG 补帧。
Lossless Scaling 为商业软件，尚未购买正版授权的用户请自行决定是否支持正版。
本包不包含 Steam 应用的其他文件（EXE、语言资源、.NET/WPF 运行库、模型资源）。

安装与覆盖顺序：
  01. 01-mpv-base-v${Version}.7z
  02. 02-mpv-extras-v${Version}.7z.001（将 .002 放在同目录，只解压 .001）
  03. 03-mpv-fasterwhisper-addon-v${Version}.7z（可选 AI 字幕扩展）
  04. 04-mpv-lsfg-addon-v${Version}.7z（本包）
  05. 05-mpv-config-v${Version}.7z（个人设置，最后安装覆盖）

包边界说明：
  LSFG 控制脚本随本包更新以保证联动可用性。
  以后单独更新 Config 不需要重新解压本包。

包边界说明：
  LSFG 菜单、控制和状态脚本已经包含在同版本 Base/Config 中。
  本包不覆盖 Config 或 Extras 文件，以后单独更新 Config 不需要重新解压本包。

内置文件：
  Lossless Scaling\Lossless.dll
  Lossless Scaling\内置说明.txt

使用方法：
  解压到现有 mpv 根目录后，用 PowerShell 运行：
    .\start-mpv-lsfg.ps1 -Multiplier 2 "视频文件.mkv"

  也可以正常打开视频，然后进入：
    右键菜单 → 视频滤镜 → 补帧

  选择 LSFG 测试档位。菜单会保存当前进度并自动重启播放。
  LSFG 启用后按 Tab 打开常驻统计 OSD，右上角会同步显示原始与实时 Present FPS。

包内的 lsfg-vk-layer.dll 及 research/lsfg-vk-win 对应源码采用 GPL-3.0-or-later；
上游来源和导入提交见 research/lsfg-vk-win/UPSTREAM.md。
"@ | Set-Content -LiteralPath $Readme -Encoding UTF8

# 严格门禁：公开归档只允许 LSFG GPL Layer DLL 和已确认内置的 Lossless.dll，且不得含 EXE。
$StagedDlls = @(Get-ChildItem -LiteralPath $Stage -Recurse -File -Filter '*.dll')
$AllowedDlls = @(
    (Resolve-Path -LiteralPath (Join-Path $LayerTarget 'lsfg-vk-layer.dll')).Path
    (Resolve-Path -LiteralPath (Join-Path $LosslessTarget 'Lossless.dll')).Path
)
$UnexpectedDlls = @($StagedDlls | Where-Object {
    $_.FullName -notin $AllowedDlls
})
if ($UnexpectedDlls.Count -gt 0) {
    throw "公开包检测到不允许的 DLL：$($UnexpectedDlls.FullName -join ', ')"
}

$StagedExecutables = @(Get-ChildItem -LiteralPath $Stage -Recurse -File -Filter '*.exe')
if ($StagedExecutables.Count -gt 0) {
    throw "公开包检测到不允许的 EXE：$($StagedExecutables.FullName -join ', ')"
}

$LosslessFiles = @(Get-ChildItem -LiteralPath $LosslessTarget -Recurse -File)
$AllowedLosslessFiles = @(
    (Resolve-Path -LiteralPath (Join-Path $LosslessTarget 'Lossless.dll')).Path
    (Resolve-Path -LiteralPath $LosslessNote).Path
)
$UnexpectedLosslessFiles = @($LosslessFiles | Where-Object {
    $_.FullName -notin $AllowedLosslessFiles
})
if ($LosslessFiles.Count -lt 1 -or $UnexpectedLosslessFiles.Count -gt 0) {
    throw "公开包的 Lossless Scaling 目录缺少内置文件或包含不允许的文件，拒绝打包"
}

if (Test-Path -LiteralPath $Archive) {
    Remove-Item -LiteralPath $Archive -Force
}
& $SevenZip a -t7z -mx=7 -md=64m -ms=on $Archive "$Stage\*"
if ($LASTEXITCODE -ne 0) { throw 'LSFG 公开扩展包创建失败' }

Write-Host "LSFG 公开扩展包已生成：$Archive" -ForegroundColor Green
