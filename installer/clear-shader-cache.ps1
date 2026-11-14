# 仅隔离可再生的编译缓存；等待播放器退出，避免退出时旧缓存被重新写回。
[CmdletBinding()]
param(
    [string]$ConfigDirectory = (Join-Path (Split-Path $PSScriptRoot -Parent) 'portable_config'),
    [ValidateSet('mpv', 'amd-vulkan')][string]$Mode = 'mpv',
    [string]$ShaderCacheDirectory,
    [int]$WaitForProcessId = 0,
    [ValidateRange(0, 86400)][int]$MaxWaitSeconds = 86400,
    [switch]$Inspect
)
$ErrorActionPreference = 'Stop'
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8

function FullPath([string]$Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd([char[]]'\/')
}
function Assert-NoLink([string]$Path) {
    # 检查全部现存祖先，不跟随目录联接、符号链接或重解析点。
    $current = $Path
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Reparse point is not a cache cleanup target: $current"
            }
        }
        $next = Split-Path $current -Parent
        if ($next -eq $current) { break }
        $current = $next
    }
}
function Assert-Child([string]$Path, [string]$Root) {
    if (-not $Path.StartsWith($Root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path outside the allowed cache root: $Path"
    }
    Assert-NoLink $Path
}
function File-Hash([string]$Path) {
    # 使用基础运行库，不依赖不同 PowerShell 版本的模块搜索路径。
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '') }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}
function Cache-Files([string]$Directory, [string]$Kind) {
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { return }
    # 逐层检查后再枚举，禁止递归工具先跟随联接再做过滤。
    foreach ($item in @(Get-ChildItem -LiteralPath $Directory -Force)) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            $script:skipped.Add([pscustomobject]@{source=$item.FullName; reason='reparse-point'})
        } elseif ($item.PSIsContainer) {
            if ($Kind -eq 'mpv') { Cache-Files $item.FullName $Kind }
        } elseif ($Kind -eq 'mpv' -or $item.Name -match '^[0-9a-fA-F]+(?:_\d+)?\.parc$') {
            [pscustomobject]@{source=$item.FullName; kind=$Kind; root=$script:roots[$Kind]; bytes=$item.Length}
        }
    }
}
function Save-Report {
    Assert-NoLink $script:reportDirectory
    $null = New-Item -ItemType Directory -Force -Path $script:reportDirectory
    $temporary = $script:reportPath + '.' + $PID + '.tmp'
    [IO.File]::WriteAllText($temporary, ($script:report | ConvertTo-Json -Depth 8), $utf8)
    for ($attempt = 0; $attempt -lt 10; $attempt++) {
        try {
            Assert-NoLink $script:reportPath
            if ([IO.File]::Exists($script:reportPath)) { [IO.File]::Replace($temporary, $script:reportPath, [NullString]::Value) }
            else { [IO.File]::Move($temporary, $script:reportPath) }
            return
        } catch {
            if ($attempt -eq 9) { throw }
            Start-Sleep -Milliseconds 50
        }
    }
}
function Players-Running {
    if ($script:parentProcess) {
        $script:parentProcess.Refresh()
        if (-not $script:parentProcess.HasExited) { return $true }
    }
    # 同时等待其他标准 mpv 实例和缩略图子进程；从不结束用户进程。
    return @((Get-Process -Name 'mpv', 'mpvnet' -ErrorAction SilentlyContinue)).Count -gt 0
}

$mutex = $null
$held = $false
try {
    $config = FullPath $ConfigDirectory
    Assert-NoLink $config
    if (-not (Test-Path -LiteralPath (Join-Path $config 'mpv.conf') -PathType Leaf)) {
        throw 'ConfigDirectory must contain mpv.conf'
    }
    $allowed = FullPath (Join-Path $config 'cache/shaders_cache')
    $shader = $allowed
    if ($ShaderCacheDirectory) { $shader = FullPath $ShaderCacheDirectory }
    if (-not $shader.Equals($allowed, [StringComparison]::OrdinalIgnoreCase)) { Assert-Child $shader $allowed }
    Assert-NoLink $shader
    $script:roots = @{mpv=$shader}
    if ($Mode -eq 'amd-vulkan') {
        if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is unavailable' }
        $driver = FullPath (Join-Path $env:LOCALAPPDATA 'AMD/VkCache')
        Assert-NoLink $driver
        $script:roots['amd-vulkan'] = $driver
    }
    $script:skipped = [Collections.Generic.List[object]]::new()
    $files = @()
    foreach ($kind in @($script:roots.Keys | Sort-Object)) { $files += @(Cache-Files $script:roots[$kind] $kind) }
    $script:reportDirectory = Join-Path $config 'files'
    $script:reportPath = Join-Path $script:reportDirectory 'shader-cache-cleanup.json'
    Assert-NoLink $script:reportDirectory
    Assert-NoLink $script:reportPath
    if ($Inspect) {
        $pending = $false
        if (Test-Path -LiteralPath $script:reportPath) {
            try {
                $previous = [IO.File]::ReadAllText($script:reportPath, $utf8) | ConvertFrom-Json
                if ($previous.status -in @('waiting', 'cleaning')) {
                    $worker = Get-Process -Id $previous.worker_pid -ErrorAction SilentlyContinue
                    if ($worker -and $worker.ProcessName -in @('powershell', 'pwsh')) {
                        $created = [DateTimeOffset]::Parse($previous.requested_at).UtcDateTime
                        $started = $worker.StartTime.ToUniversalTime()
                        $pending = $started -le $created -and $started -gt $created.AddMinutes(-2)
                    }
                }
            } catch { $pending = $false }
        }
        [pscustomobject]@{status='inspect'; mode=$Mode; roots=$script:roots; count=$files.Count; pending=$pending; skipped=@($script:skipped.ToArray())} | ConvertTo-Json -Depth 5
        exit 0
    }
    # 同一配置仅保留一个待执行任务，避免退出时两次隔离同一批文件。
    $hash = [Security.Cryptography.SHA256]::Create()
    $key = [BitConverter]::ToString($hash.ComputeHash($utf8.GetBytes($config.ToLowerInvariant()))).Replace('-', '')
    $hash.Dispose()
    $mutex = [Threading.Mutex]::new($false, ('Local\mpv-shader-cleanup-' + $key))
    try { $held = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $held = $true }
    if (-not $held) { Write-Output 'A cleanup task is already pending for this configuration.'; exit 0 }
    $script:report = [ordered]@{status='waiting'; mode=$Mode; worker_pid=$PID; requested_at=[DateTimeOffset]::Now.ToString('o'); moved=0; skipped=0; backup=$null; error=$null}
    Save-Report
    $script:parentProcess = $null
    if ($WaitForProcessId -gt 0) {
        $script:parentProcess = Get-Process -Id $WaitForProcessId -ErrorAction SilentlyContinue
        if ($script:parentProcess) { $null = $script:parentProcess.Handle }
    }
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $announced = $false
    while (Players-Running) {
        if (-not $announced) { Write-Output 'Waiting for mpv processes to exit. No process will be terminated.'; $announced = $true }
        if ($watch.Elapsed.TotalSeconds -ge $MaxWaitSeconds) { throw 'Timed out waiting for mpv to exit; no cleanup was performed.' }
        Start-Sleep -Milliseconds 400
    }
    # 等待结束后重新枚举，包含 mpv 在关闭阶段最后写入的缓存。
    $script:skipped.Clear()
    $files = @()
    foreach ($kind in @($script:roots.Keys | Sort-Object)) {
        Assert-NoLink $script:roots[$kind]
        $files += @(Cache-Files $script:roots[$kind] $kind)
    }
    $backupBase = FullPath (Join-Path (Split-Path $config -Parent) 'backup/shader-cache')
    Assert-NoLink $backupBase
    $backup = Join-Path $backupBase ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    Assert-Child $backup $backupBase
    $null = New-Item -ItemType Directory -Force -Path $backup
    $moved = [Collections.Generic.List[object]]::new()
    $script:report.status, $script:report.backup = 'cleaning', $backup
    Save-Report
    foreach ($file in $files) {
        try {
            $source = FullPath $file.source
            Assert-Child $source $file.root
            $relative = $source.Substring($file.root.Length).TrimStart([char[]]'\/')
            $destination = FullPath (Join-Path (Join-Path $backup $file.kind) $relative)
            Assert-Child $destination $backup
            $null = New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent)
            $digest = File-Hash $source
            # 仅移动已核对的单个文件，不递归删除缓存目录或其他用户数据。
            Move-Item -LiteralPath $source -Destination $destination
            $moved.Add([pscustomobject]@{source=$source; backup=$destination; sha256=$digest; bytes=$file.bytes})
        } catch {
            $script:skipped.Add([pscustomobject]@{source=$file.source; reason=$_.Exception.Message})
        }
        # 每个文件结束都记录，进程中断后仍可依据清单恢复已隔离文件。
        [IO.File]::WriteAllText((Join-Path $backup 'manifest.json'), (@{moved=@($moved.ToArray()); skipped=@($script:skipped.ToArray())} | ConvertTo-Json -Depth 6), $utf8)
    }
    [IO.File]::WriteAllText((Join-Path $backup 'manifest.json'), (@{moved=@($moved.ToArray()); skipped=@($script:skipped.ToArray())} | ConvertTo-Json -Depth 6), $utf8)
    $script:report.moved, $script:report.skipped = $moved.Count, $script:skipped.Count
    $script:report.status = 'complete'
    if ($script:skipped.Count -gt 0) { $script:report.status = 'partial' }
    $script:report['completed_at'] = [DateTimeOffset]::Now.ToString('o')
    Save-Report
    $script:report | ConvertTo-Json -Depth 5
    if ($script:skipped.Count -gt 0) { exit 2 }
} catch {
    if ($held -and $script:report) {
        $script:report.status, $script:report.error = 'failed', $_.Exception.Message
        Save-Report
    }
    Write-Error $_
    exit 1
} finally {
    if ($held) { $mutex.ReleaseMutex() }
    if ($mutex) { $mutex.Dispose() }
}
