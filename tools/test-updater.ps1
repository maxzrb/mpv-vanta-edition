# 只载入待测函数；不执行更新器入口，不下载或替换真实播放器。
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseInput((Get-Content -Encoding UTF8 -Raw (Join-Path $root 'installer/updater.ps1')), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw '更新器语法错误' }
$wanted = @('Get-Latest-Mpv', 'Get-Latest-FFmpeg', 'Backup-Tool', 'Upgrade-Ytplugin')
foreach ($function in $ast.FindAll({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst]}, $true)) {
    if ($function.Name -in $wanted) { Invoke-Expression $function.Extent.Text }
}
$mpvName, $mpvUrl, $mpvHash = Get-Latest-Mpv 'x86_64'
$ffmpegName, $ffmpegUrl, $ffmpegHash = Get-Latest-FFmpeg 'x86_64'
if ($mpvName -notmatch '^mpv-x86_64-\d{8}-git-[a-f0-9]+\.7z$' -or $mpvHash.Length -ne 64) { throw '核心资产匹配错误' }
if ($ffmpegName -notmatch '^ffmpeg-x86_64-git-[a-f0-9]+\.7z$' -or $ffmpegHash.Length -ne 64) { throw '工具资产匹配错误' }
$testDirectory = Join-Path $root ('tmp/modernization/updater-test-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testDirectory | Out-Null
Set-Location -LiteralPath $testDirectory
$script:fixture = Join-Path $testDirectory 'fixture.ps1'
$program = @'
param([string]$action)
if ($action -eq '--version') { 'old'; exit 0 }
[System.IO.File]::WriteAllText($PSCommandPath, 'broken update', [System.Text.UTF8Encoding]::new($false))
exit 1
'@
[System.IO.File]::WriteAllText($script:fixture, $program, [System.Text.UTF8Encoding]::new($false))
$hash = (Get-FileHash -LiteralPath $script:fixture -Algorithm SHA256).Hash
function Check-Ytplugin-In-System { return $false }
function Check-Ytplugin { return $script:fixture }
function Get-Latest-Ytplugin { return 'new' }
$caught = $false
try { Upgrade-Ytplugin } catch { $caught = $true }
if (-not $caught -or (Get-FileHash -LiteralPath $script:fixture -Algorithm SHA256).Hash -ne $hash) { throw '失败工具未恢复' }
if ((Get-ChildItem backup -Filter old-checksum.json -Recurse).Count -ne 1) { throw '缺少旧版校验值' }
Write-Output 'PASS 官方资产选择／工具自更新失败恢复／旧版哈希保留'
