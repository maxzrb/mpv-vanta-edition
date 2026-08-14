param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,

    [string]$OutputDir = 'release',

    [switch]$IncludePrivate
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot

Write-Host "开始构建 MPV v${Version} 四个公开包" -ForegroundColor Cyan

& (Join-Path $Root 'build-01-base.ps1') -Version $Version -OutputDir $OutputDir
if ($LASTEXITCODE -ne 0) { throw '01 Base 包构建失败' }

& (Join-Path $Root 'build-02-extras.ps1') -Version $Version -OutputDir $OutputDir
if ($LASTEXITCODE -ne 0) { throw '02 Extras 包构建失败' }

& (Join-Path $Root 'build-03-fasterwhisper.ps1') -Version $Version -OutputDir $OutputDir
if ($LASTEXITCODE -ne 0) { throw '03 Faster-Whisper 扩展包构建失败' }

& (Join-Path $Root 'build-04-config.ps1') -Version $Version -OutputDir $OutputDir
if ($LASTEXITCODE -ne 0) { throw '04 Config 包构建失败' }

if ($IncludePrivate) {
    Write-Host '继续构建个人私用全量包' -ForegroundColor Yellow
    & (Join-Path $Root 'build-full-private.ps1') -Version $Version -OutputDir $OutputDir
    if ($LASTEXITCODE -ne 0) { throw '个人私用全量包构建失败' }
}

# 各子包脚本只清理自己的暂存目录；总入口统一清理 build/ 根目录
$BuildDir = Join-Path $Root 'build'
if (Test-Path -LiteralPath $BuildDir) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}

Write-Host "MPV v${Version} 打包完成：$(Join-Path $Root $OutputDir)" -ForegroundColor Green
