<#
.SYNOPSIS
    MPV Vanta Edition 02 Extras package builder
.DESCRIPTION
    Creates the second numbered public package (optional, installed after 01):
      - 02-mpv-extras-vX.Y.Z.7z.001/.002   Shaders + VapourSynth + Python + Tools (split volumes)
.PARAMETER Version
    Version number, e.g. "1.0.0"
.PARAMETER OutputDir
    Output directory relative to repo root. Default: release
.EXAMPLE
    .\build-02-extras.ps1 -Version "1.0.0"
    .\build-02-extras.ps1 -Version "1.0.0" -OutputDir "release"
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
$ExtrasName = "02-mpv-extras-v${Version}"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  MPV Vanta Edition 02 Extras Builder v${Version}" -ForegroundColor Cyan
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
    if (Test-Path "${archivePath}.7z.001") {
        Remove-Item -Force "${archivePath}.7z.*"
    }

    # Split volumes: max 1900MB each (< GitHub 2GB limit)
    & $7z a -t7z -mx=7 -md=64m -ms=on -v1900m "${archivePath}.7z" "$SourceDir\*"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Packaging failed: ${Description}"
        exit 1
    }

    $size = (Get-ChildItem "${archivePath}.7z.*" | Measure-Object -Property Length -Sum).Sum
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
# Extras Package
# ============================================================
Write-Host "--- [1/1] Extras Package ---" -ForegroundColor Magenta
$ExtrasBuild = Join-Path $BuildDir $ExtrasName
if (Test-Path $ExtrasBuild) { Remove-Item -Recurse -Force $ExtrasBuild }
$null = New-Item -ItemType Directory -Force $ExtrasBuild

# Shaders
Write-Host "       Copying shaders (~129MB)..." -ForegroundColor Gray
$shadersSrc = Join-Path $RootDir "portable_config\shaders"
$shadersDst = Join-Path $ExtrasBuild "portable_config\shaders"
if (Test-Path $shadersSrc) {
    $null = New-Item -ItemType Directory -Force $shadersDst
    Copy-Item -Recurse -Force "$shadersSrc\*" $shadersDst
}

# VapourSynth scripts
Write-Host "       Copying VapourSynth scripts..." -ForegroundColor Gray
$vsScriptsSrc = Join-Path $RootDir "portable_config\vs"
$vsScriptsDst = Join-Path $ExtrasBuild "portable_config\vs"
if (Test-Path $vsScriptsSrc) {
    $null = New-Item -ItemType Directory -Force $vsScriptsDst
    Copy-Item -Recurse -Force "$vsScriptsSrc\*" $vsScriptsDst
}

# VapourSynth plugins (the big one)
Write-Host "       Copying VapourSynth plugins (~4GB)..." -ForegroundColor Gray
Invoke-CopyTo $ExtrasBuild @("vs-plugins", "vs-coreplugins", "vs-scripts")

# VapourSynth binaries
Write-Host "       Copying VapourSynth binaries..." -ForegroundColor Gray
$vsBinaries = @(
    "VSPipe.exe", "VSScript.dll", "VSScriptPython38.dll",
    "VSVFW.dll", "AVFS.exe", "pfm-192-vapoursynth-win.exe",
    "portable.vs"
)
foreach ($b in $vsBinaries) { Copy-IfExists $b $ExtrasBuild }

# VS SDK + tools
Invoke-CopyTo $ExtrasBuild @("sdk", "vsgenstubs.py", "vsgenstubs4", "vsrepo.py", "MANIFEST.in")

# Python runtime
Write-Host "       Copying Python runtime (~130MB)..." -ForegroundColor Gray
$pythonFiles = @(
    "python.exe", "pythonw.exe", "python314.dll",
    "python314.zip", "python3.dll", "python314._pth", "python.cat"
)
foreach ($pf in $pythonFiles) { Copy-IfExists $pf $ExtrasBuild }
foreach ($pyd in Get-ChildItem "$RootDir\*.pyd" -ErrorAction Ignore) {
    Copy-Item $pyd.FullName $ExtrasBuild
}
Invoke-CopyTo $ExtrasBuild @("Lib", "Scripts")

# Other tools
Write-Host "       Copying extra tools..." -ForegroundColor Gray
foreach ($tool in @("TorrServer-windows-amd64.exe", "alass.exe", "get-pip.py")) {
    Copy-IfExists $tool $ExtrasBuild
}

# Extras 包内说明同时保留完整的覆盖顺序，避免用户只下载分卷时漏看根 README。
$extrasReadme = Join-Path $ExtrasBuild "EXTRAS-README.txt"
@"
MPV Vanta Edition 02 Extras v${Version}
==================================

安装与覆盖顺序：
  01. 01-mpv-base-vX.Y.Z.7z
  02. 02-mpv-extras-vX.Y.Z.7z.001（本包；将 .002 放在同目录，只解压 .001）
  03. 03-mpv-fasterwhisper-addon-v${Version}.7z（可选 AI 字幕扩展）
  04. 04-mpv-config-v${Version}.7z（个人设置，最后安装覆盖）

Contains:
- Shaders (portable_config/shaders/)    129 MB
- VapourSynth plugins (vs-plugins/)     ~4 GB
- VapourSynth scripts (portable_config/vs/)
- Python runtime                        127 MB
- Extra tools (TorrServer, alass)       75 MB
"@ | Set-Content $extrasReadme -Encoding UTF8

Remove-GeneratedArtifacts $ExtrasBuild

# Extras uses split volumes due to size
Invoke-Pack $ExtrasName $ExtrasBuild "Extras (shaders + VS + Python + tools)"

# ============================================================
# Cleanup (only this package's staging directory)
# ============================================================
if (Test-Path $ExtrasBuild) { Remove-Item -Recurse -Force $ExtrasBuild }

# ============================================================
# Done
# ============================================================
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  02 Extras Build Complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Get-ChildItem -Path (Join-Path $OutputDir "$ExtrasName.7z*") -ErrorAction Ignore | ForEach-Object {
    $sizeMB = [math]::Round($_.Length / 1MB, 1)
    Write-Host "  $($_.Name)  (${sizeMB} MB)" -ForegroundColor White
}
Write-Host ""
Write-Host "Output directory: $(Resolve-Path $OutputDir)" -ForegroundColor Cyan
Write-Host "Next step: Create GitHub Release and upload these files" -ForegroundColor Cyan
