<#
.SYNOPSIS
    MPV Vanta Edition 01 Base package builder
.DESCRIPTION
    Creates the first numbered public package (installed first):
      - 01-mpv-base-vX.Y.Z.7z     Core player + runtime + base config
.PARAMETER Version
    Version number, e.g. "1.0.0"
.PARAMETER OutputDir
    Output directory relative to repo root. Default: release
.EXAMPLE
    .\build-01-base.ps1 -Version "1.0.0"
    .\build-01-base.ps1 -Version "1.0.0" -OutputDir "release"
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,

    [string]$OutputDir = "release"
)

$ErrorActionPreference = "Stop"
$RootDir = $PSScriptRoot
Set-Location $RootDir

# Tools
$7z = Join-Path $RootDir "7z.exe"
if (-not (Test-Path $7z)) {
    Write-Error "Cannot find 7z.exe. Run this script from the mpv root directory."
    exit 1
}

# Output directory
$null = New-Item -ItemType Directory -Force (Join-Path $RootDir $OutputDir)
$BuildDir = Join-Path $RootDir "build"

# 包名编号同时表示解压覆盖顺序。
$BaseName = "01-mpv-base-v${Version}"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  MPV Vanta Edition 01 Base Builder v${Version}" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# Helper functions
# ============================================================

function Invoke-Pack {
    param([string]$ArchiveName, [string]$SourceDir, [string]$Description)
    $archivePath = Join-Path $OutputDir $ArchiveName
    Write-Host "[PACK] ${Description}" -ForegroundColor Yellow
    Write-Host "       Output: ${archivePath}.7z" -ForegroundColor Gray

    if (Test-Path "${archivePath}.7z") { Remove-Item -Force "${archivePath}.7z" }

    & $7z a -t7z -mx=7 -md=64m -ms=on "${archivePath}.7z" "$SourceDir\*"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Packaging failed: ${Description}"
        exit 1
    }

    # 归档内验证根级 README.MD 确实进入（精确匹配根级条目，避免误匹配 portable_config\README.md）
    $readmeIn = (& $7z l -ba "${archivePath}.7z" | Select-String ' README\.MD$' -CaseSensitive)
    Write-Host "       [verify] archive root README.MD present: $($null -ne $readmeIn)"

    $size = (Get-Item "${archivePath}.7z").Length
    $sizeMB = [math]::Round($size / 1MB, 1)
    Write-Host "       Done (${sizeMB} MB)" -ForegroundColor Green
    Write-Host ""
}

function Invoke-CopyTo {
    param([string]$Dest, [string[]]$Sources)
    foreach ($src in $Sources) {
        $target = Join-Path $Dest $src
        $parent = Split-Path $target -Parent
        if (-not (Test-Path $parent)) {
            $null = New-Item -ItemType Directory -Force $parent
        }
        $srcPath = Join-Path $RootDir $src
        if (Test-Path $srcPath) {
            Copy-Item -Recurse -Force $srcPath $target
        }
    }
}

function Invoke-CopyConfig {
    param([string]$Dest)
    $configDest = Join-Path $Dest "portable_config"
    $configSrc = Join-Path $RootDir "portable_config"
    Write-Host "       Copying portable_config/ (excluding shaders vs cache files; keeping script-assets)..." -ForegroundColor Gray
    $null = New-Item -ItemType Directory -Force $configDest
    Copy-Item -Recurse -Force "$configSrc\*" $configDest
    # Remove heavy content (goes into extras)
    foreach ($exclude in @("shaders", "vs", "cache", "files")) {
        $exPath = Join-Path $configDest $exclude
        if (Test-Path $exPath) { Remove-Item -Recurse -Force $exPath }
    }
    # 个人测试/主题应用产生的备份目录不进公开包（portable_config/backup 与 script-opts/backup）
    $backupDirs = @(Get-ChildItem -Path $configDest -Recurse -Directory -Filter "backup" `
        -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
    foreach ($dir in $backupDirs) {
        Remove-Item -LiteralPath $dir.FullName -Recurse -Force
    }
    # 新旧 stats.lua 同时进包：放行 scripts/backup 下的 stats 原版备份（兜底），其它备份仍排除
    $statsBackupSrc = Join-Path $configSrc 'scripts\backup'
    $statsBackupDest = Join-Path $configDest 'scripts\backup'
    if (Test-Path -LiteralPath $statsBackupSrc) {
        $statsBackups = @(Get-ChildItem -LiteralPath $statsBackupSrc -File -Filter 'stats-original-*.lua' `
            -ErrorAction SilentlyContinue)
        foreach ($f in $statsBackups) {
            $null = New-Item -ItemType Directory -Force -Path $statsBackupDest
            Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $statsBackupDest $f.Name) -Force
        }
    }
    # 个人运行时状态（窗口记忆）不进公开包
    $stateFile = Join-Path $configDest "script-opts/window_state.conf"
    if (Test-Path $stateFile) { Remove-Item -Force $stateFile }
}

function Copy-IfExists {
    param([string]$Source, [string]$DestDir)
    $src = Join-Path $RootDir $Source
    if (Test-Path $src) { Copy-Item $src $DestDir }
}

function Remove-GeneratedArtifacts {
    param([string]$TargetRoot)

    # 只清理明确由运行/编译过程生成的文件，不删除 Python 包自带的 tests 或源码。
    $cacheDirs = @(Get-ChildItem -LiteralPath $TargetRoot -Recurse -Directory -Force `
        -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -in @('__pycache__', '.pytest_cache', '.mypy_cache')
        } | Sort-Object FullName -Descending)
    foreach ($dir in $cacheDirs) {
        Remove-Item -LiteralPath $dir.FullName -Recurse -Force
    }

    $generatedExtensions = @(
        '.pyc', '.pyo', '.log', '.tmp', '.bak',
        '.pdb', '.obj', '.ilk', '.dmp'
    )
    $generatedFiles = @(Get-ChildItem -LiteralPath $TargetRoot -Recurse -File -Force `
        -ErrorAction SilentlyContinue | Where-Object {
            $_.Extension.ToLowerInvariant() -in $generatedExtensions
        })
    foreach ($file in $generatedFiles) {
        Remove-Item -LiteralPath $file.FullName -Force
    }
}

# ============================================================
# Base Package
# ============================================================
Write-Host "--- [1/1] Base Package ---" -ForegroundColor Magenta
$BaseBuild = Join-Path $BuildDir $BaseName
if (Test-Path $BaseBuild) { Remove-Item -Recurse -Force $BaseBuild }
$null = New-Item -ItemType Directory -Force $BaseBuild

# Config content
Invoke-CopyConfig $BaseBuild

# Vanta 安装标记：供安装器区分"Vanta 安装"与"任意 mpv"
$vantaMarker = Join-Path $BaseBuild "portable_config/.vanta-version"
Set-Content -Path $vantaMarker -Value $Version -Encoding UTF8 -NoNewline
Write-Host "       Vanta 标记: .vanta-version = $Version" -ForegroundColor Gray

# MPV core
Write-Host "       Copying mpv core..." -ForegroundColor Gray
Copy-IfExists "mpv.exe" $BaseBuild
Copy-IfExists "mpv.com" $BaseBuild

# 随包自带的检测专用 ffmpeg（起播徽章后瞻用；gyan.dev essentials_build 全解码精简版）
Write-Host "       Copying bundled ffmpeg (lookahead detection)..." -ForegroundColor Gray
Invoke-CopyTo $BaseBuild @("ffmpeg")

# 在线视频解析器（与 mpv.exe 同目录时由 ytdl_hook 自动发现）
Copy-IfExists "yt-dlp.exe" $BaseBuild

# Runtime DLLs
Write-Host "       Copying runtime DLLs..." -ForegroundColor Gray
$runtimeDlls = @(
    "lua51.dll", "d3dcompiler_43.dll",
    "sqlite3.dll", "libcrypto-3.dll", "libssl-3.dll", "libffi-8.dll",
    "concrt140.dll", "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll",
    "msvcp140_atomic_wait.dll", "msvcp140_codecvt_ids.dll",
    "vccorlib140.dll", "vcruntime140.dll", "vcruntime140_1.dll",
    "vcruntime140_threads.dll"
)
foreach ($dll in $runtimeDlls) { Copy-IfExists $dll $BaseBuild }
Copy-IfExists "luajit.exe" $BaseBuild

# Lua runtime
Write-Host "       Copying Lua runtime..." -ForegroundColor Gray
Invoke-CopyTo $BaseBuild @("lua", "mime", "socket")

# MPV data
Invoke-CopyTo $BaseBuild @("mpv", "doc")

# Installer tools
Write-Host "       Copying installer tools..." -ForegroundColor Gray
Invoke-CopyTo $BaseBuild @("installer", "updater.bat")

# Single-instance tool
Copy-IfExists "umpv.exe" $BaseBuild
Copy-IfExists "umpv.conf" $BaseBuild

# 7z extractor (needed to unpack extras)
Invoke-CopyTo $BaseBuild @("7z.exe", "7z.dll", "7z")

# 项目说明文件：显式目标路径复制（README.MD 必须随 01 包分发）
Invoke-CopyTo $BaseBuild @("README.MD", ".gitignore")

# 打包前校验 README.MD 已进入构建目录（缺失即终止，避免发布无说明文档的包）
if (-not (Test-Path (Join-Path $BaseBuild "README.MD"))) {
    Write-Error "README.MD 未进入 01 构建目录，终止打包。"
    exit 1
}

Remove-GeneratedArtifacts $BaseBuild
Invoke-Pack $BaseName $BaseBuild "Base (core player + runtime + config)"

# ============================================================
# Cleanup (only this package's staging directory)
# ============================================================
if (Test-Path $BaseBuild) { Remove-Item -Recurse -Force $BaseBuild }

# ============================================================
# Done
# ============================================================
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  01 Base Build Complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Get-ChildItem -Path (Join-Path $OutputDir "$BaseName.7z*") -ErrorAction Ignore | ForEach-Object {
    $sizeMB = [math]::Round($_.Length / 1MB, 1)
    Write-Host "  $($_.Name)  (${sizeMB} MB)" -ForegroundColor White
}
Write-Host ""
Write-Host "Output directory: $(Resolve-Path $OutputDir)" -ForegroundColor Cyan
Write-Host "Next step: Create GitHub Release and upload these files" -ForegroundColor Cyan
