param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,

    [string]$OutputDir = 'release'
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$SevenZip = Join-Path $Root '7z.exe'
$OutputRoot = Join-Path $Root $OutputDir
$PackageName = "mpv-full-private-v${Version}"
$Stage = Join-Path $Root "build/$PackageName"
$Archive = Join-Path $OutputRoot "$PackageName.7z"

$BaseArchive    = Join-Path $OutputRoot "01-mpv-base-v${Version}.7z"
$ExtrasArchive  = Join-Path $OutputRoot "02-mpv-extras-v${Version}.7z.001"
$FwArchive      = Join-Path $OutputRoot "03-mpv-fasterwhisper-addon-v${Version}.7z"
$ConfigArchive  = Join-Path $OutputRoot "04-mpv-config-v${Version}.7z"

foreach ($required in @($SevenZip, $BaseArchive, $ExtrasArchive, $FwArchive,
                        $ConfigArchive)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "缺少个人全量包所需文件：$required"
    }
}

if (Test-Path -LiteralPath $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}
$null = New-Item -ItemType Directory -Force -Path $Stage
$null = New-Item -ItemType Directory -Force -Path $OutputRoot

function Get-InstallerVersion {
    param([string]$FileName)
    # VantaInstaller-win-x64-v0.3.2.exe -> 0.3.2
    $marker = 'VantaInstaller-win-x64-v'
    $idx = $FileName.IndexOf($marker, [System.StringComparison]::OrdinalIgnoreCase)
    if ($idx -lt 0) { return $null }
    $ver = $FileName.Substring($idx + $marker.Length)
    $exeIdx = $ver.IndexOf('.exe', [System.StringComparison]::OrdinalIgnoreCase)
    if ($exeIdx -gt 0) { $ver = $ver.Substring(0, $exeIdx) }
    $parts = $ver.Split('.')
    if ($parts.Length -ne 3) { return $null }
    foreach ($p in $parts) {
        if (-not ($p -match '^\d+$')) { return $null }
    }
    return $ver
}

function Compare-Version {
    param([string]$A, [string]$B)
    $pa = $A.Split('.'); $pb = $B.Split('.')
    for ($i = 0; $i -lt 3; $i++) {
        $x = [int]$pa[$i]; $y = [int]$pb[$i]
        if ($x -ne $y) { return $x.CompareTo($y) }
    }
    return 0
}

function Expand-Package {
    param([string]$ArchivePath)

    Write-Host "覆盖解压：$(Split-Path -Leaf $ArchivePath)" -ForegroundColor DarkGray
    & $SevenZip x -y "-o$Stage" $ArchivePath
    if ($LASTEXITCODE -ne 0) {
        throw "解压失败：$ArchivePath"
    }
}

# 严格按公开四包的覆盖顺序合并。
Expand-Package $BaseArchive
Expand-Package $ExtrasArchive
Expand-Package $FwArchive
Expand-Package $ConfigArchive

# 打包最新 VantaInstaller（发布时候选已移入 release 目录；按版本号取最大者）
$InstallerCandidates = @(Get-ChildItem -LiteralPath $OutputRoot -File -Filter 'VantaInstaller-win-x64-v*.exe' `
    -ErrorAction SilentlyContinue)
$InstallerExe = $null
foreach ($candidate in $InstallerCandidates) {
    $ver = Get-InstallerVersion $candidate.Name
    if ($null -eq $ver) { continue }
    if ($null -eq $InstallerExe -or (Compare-Version $ver $InstallerExe.Version) -gt 0) {
        $InstallerExe = [pscustomobject]@{ Path = $candidate.FullName; Version = $ver; Name = $candidate.Name }
    }
}
if ($null -eq $InstallerExe) {
    Write-Warning 'release 目录未找到 VantaInstaller-win-x64-v*.exe，个人全量包将不包含安装器。'
} else {
    Write-Host "打包 VantaInstaller：$($InstallerExe.Name)" -ForegroundColor Gray
    Copy-Item -LiteralPath $InstallerExe.Path -Destination (Join-Path $Stage $InstallerExe.Name) -Force
}

$PrivateReadme = Join-Path $Stage 'README-个人私用全量包.txt'
@"
MPV 个人私用全量包 v${Version}

本包按以下顺序合并：
  01. 01-mpv-base-v${Version}.7z
  02. 02-mpv-extras-v${Version}.7z.001/.002
  03. 03-mpv-fasterwhisper-addon-v${Version}.7z
  04. 04-mpv-config-v${Version}.7z

并携带随包最新的 VantaInstaller（发布候选）：VantaInstaller-win-x64-v*.exe。

这是四个公开包的完整并集，包含播放器、配置、着色器、VapourSynth、Python、
Faster-Whisper、工具和公开包说明。
解压后即可按项目配置使用。

本包含个人运行时状态与工具，只限个人本地备份和使用。
不要上传 GitHub Release，不要公开分享或转售。
"@ | Set-Content -LiteralPath $PrivateReadme -Encoding UTF8

# 全量包门禁：不得套入 Release、build、tmp、Git 元数据或 Python 缓存。
$ForbiddenTopLevel = @('release', 'build', 'tmp', '.git')
foreach ($name in $ForbiddenTopLevel) {
    if (Test-Path -LiteralPath (Join-Path $Stage $name)) {
        throw "个人全量包含不允许的顶层目录：$name"
    }
}

$CacheDirs = @(Get-ChildItem -LiteralPath $Stage -Recurse -Directory -Force `
    -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -in @('__pycache__', '.pytest_cache', '.mypy_cache')
    })
if ($CacheDirs.Count -gt 0) {
    throw "个人全量包仍含缓存目录：$($CacheDirs.FullName -join ', ')"
}

$GeneratedExtensions = @(
    '.pyc', '.pyo', '.log', '.tmp', '.bak',
    '.pdb', '.obj', '.ilk', '.dmp'
)
$GeneratedFiles = @(Get-ChildItem -LiteralPath $Stage -Recurse -File -Force `
    -ErrorAction SilentlyContinue | Where-Object {
        $_.Extension.ToLowerInvariant() -in $GeneratedExtensions
    })
if ($GeneratedFiles.Count -gt 0) {
    throw "个人全量包仍含生成文件：$($GeneratedFiles.FullName -join ', ')"
}

if (Test-Path -LiteralPath $Archive) {
    Remove-Item -LiteralPath $Archive -Force
}
& $SevenZip a -t7z -mx=7 -md=64m -ms=on $Archive "$Stage\*"
if ($LASTEXITCODE -ne 0) { throw '个人全量包创建失败' }

Write-Host "个人全量包已生成：$Archive" -ForegroundColor Green
