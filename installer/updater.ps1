$fallback7z = Join-Path (Get-Location) "\7z\7zr.exe";
$useragent = "mpv-win-updater"

function Backup-Tool($Target) {
    $backup = Join-Path (Get-Location).Path ('backup\tool-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff'))
    New-Item -ItemType Directory -Path $backup -ErrorAction Stop | Out-Null
    if (Test-Path -LiteralPath $Target) {
        Copy-Item -LiteralPath $Target -Destination $backup -ErrorAction Stop
        Get-FileHash -LiteralPath $Target -Algorithm SHA256 | Select-Object Hash, Path |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'old-checksum.json') -Encoding UTF8
    }
    return $backup
}

function Get-7z {
    $7z_command = Get-Command -CommandType Application -ErrorAction Ignore 7z.exe | Select-Object -Last 1
    if ($7z_command) {
        return $7z_command.Source
    }
    $7zdir = Get-ItemPropertyValue -ErrorAction Ignore "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\7-Zip" "InstallLocation"
    if ($7zdir -and (Test-Path (Join-Path $7zdir "7z.exe"))) {
        return Join-Path $7zdir "7z.exe"
    }
    if (Test-Path $fallback7z) {
        return $fallback7z
    }
    return $null
}

function Check-7z {
    if (-not (Get-7z))
    {
        $null = New-Item -ItemType Directory -Force (Split-Path $fallback7z)
        $download_file = $fallback7z
        Write-Host "Downloading 7zr.exe" -ForegroundColor Green
        Invoke-WebRequest -Uri "https://www.7-zip.org/a/7zr.exe" -UserAgent $useragent -OutFile $download_file
    }
    else
    {
        Write-Host "7z already exist. Skipped download" -ForegroundColor Green
    }
}

function Check-PowershellVersion {
    $version = $PSVersionTable.PSVersion.Major
    Write-Host "Checking Windows PowerShell version -- $version" -ForegroundColor Green
    if ($version -le 2)
    {
        Write-Host "Using Windows PowerShell $version is unsupported. Upgrade your Windows PowerShell." -ForegroundColor Red
        throw
    }
}

function Check-Ytplugin {
    $ytdlp = Get-ChildItem "yt-dlp*.exe" -ErrorAction Ignore
    $youtubedl = Get-ChildItem "youtube-dl.exe" -ErrorAction Ignore
    if ($ytdlp) {
        return $ytdlp.ToString()
    }
    elseif ($youtubedl) {
        return $youtubedl.ToString()
    }
    else {
        return $null
    }
}

function Check-Ytplugin-In-System {
    $ytp = Get-Command -CommandType Application -ErrorAction Ignore yt-dlp.exe | Select-Object -Last 1
    if (-not $ytp) {
        $ytp = Get-Command -CommandType Application -ErrorAction Ignore youtube-dl.exe | Select-Object -Last 1
    }
    return [bool]($ytp -and ((Split-Path $ytp.Source) -ne (Get-Location)))
}

function Check-Mpv {
    $mpv = (Get-Location).Path + "\mpv.exe"
    $is_exist = Test-Path $mpv
    return $is_exist
}

function Download-Archive ($filename, $link) {
    Write-Host "Downloading" $filename -ForegroundColor Green
    Invoke-WebRequest -Uri $link -UserAgent $useragent -OutFile $filename
}

function Download-Ytplugin ($plugin, $version) {
    $link = ""
    $plugin_exe = ""
    switch -wildcard ($plugin) {
        "yt-dlp*" {
            Write-Host "Downloading $plugin ($version)" -ForegroundColor Green
            $32bit = ""
            if (-Not (Test-Path (Join-Path $env:windir "SysWow64"))) {
                $32bit = "_x86"
            }
            $link = -join("https://github.com/yt-dlp/yt-dlp/releases/download/", $version, "/", $plugin, $32bit, ".exe")
            $plugin_exe = -join($plugin, $32bit, ".exe")
        }
        "youtube-dl" {
            Write-Host "Downloading $plugin ($version)" -ForegroundColor Green
            $link = -join("https://yt-dl.org/downloads/", $version, "/youtube-dl.exe")
            $plugin_exe = "youtube-dl.exe"
        }
    }
    # 首次下载也通过官方资产 digest 验证，先暂存再替换。
    $repository = if ($plugin -like 'yt-dlp*') { 'yt-dlp/yt-dlp' } else { 'ytdl-org/youtube-dl' }
    $release = Invoke-RestMethod -Uri ("https://api.github.com/repos/$repository/releases/tags/$version") -ErrorAction Stop
    $asset = $release.assets | Where-Object name -eq $plugin_exe | Select-Object -First 1
    if (-not $asset -or $asset.digest -notmatch '^sha256:[a-f0-9]{64}$') { throw '下载工具缺少官方 SHA-256，停止更新。' }
    $stage = Join-Path (Get-Location).Path ('tmp\tool-' + [Guid]::NewGuid().ToString('N') + '.exe')
    New-Item -ItemType Directory -Force -Path (Split-Path $stage) -ErrorAction Stop | Out-Null
    Invoke-WebRequest -Uri $asset.browser_download_url -UserAgent $useragent -OutFile $stage -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $stage -Algorithm SHA256).Hash -ne $asset.digest.Substring(7)) { throw '下载工具校验失败。' }
    $backup = Backup-Tool $plugin_exe
    Copy-Item -LiteralPath $stage -Destination $plugin_exe -Force -ErrorAction Stop
    Get-FileHash -LiteralPath $plugin_exe -Algorithm SHA256 | Select-Object Hash, Path |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'new-checksum.json') -Encoding UTF8
}

function Extract-Archive ($file) {
    $7z = Get-7z
    Write-Host "Extracting" $file -ForegroundColor Green
    & $7z x -y $file
}

function Get-Latest-Mpv($Arch) {
    $api_gh = "https://api.github.com/repos/shinchiro/mpv-winbuild-cmake/releases/latest"
    $json = Invoke-WebRequest $api_gh -MaximumRedirection 0 -ErrorAction Ignore -UseBasicParsing | ConvertFrom-Json
    $asset = $json.assets | Where-Object { $_.name -match ("^mpv-" + [Regex]::Escape($Arch) + "-[0-9]{8}-git-[a-f0-9]+\.7z$") } | Select-Object -First 1
    if (-not $asset -or $asset.digest -notmatch '^sha256:[a-f0-9]{64}$') {
        throw '上游未提供唯一构建或可信 SHA-256，停止更新。'
    }
    return $asset.name, $asset.browser_download_url, $asset.digest.Substring(7)
}

function Get-Latest-Ytplugin ($plugin) {
    switch -wildcard ($plugin) {
        "yt-dlp*" {
            $link = "https://github.com/yt-dlp/yt-dlp/releases.atom"
            Write-Host "Fetching RSS feed for ytp-dlp" -ForegroundColor Green
            $resp = [xml](Invoke-WebRequest $link -MaximumRedirection 0 -ErrorAction Ignore -UseBasicParsing).Content
            $link = $resp.feed.entry[0].link.href
            $version = $link.split("/")[-1]
            return $version
        }
        "youtube-dl" {
            $link = "https://yt-dl.org/downloads/latest/youtube-dl.exe"
            Write-Host "Fetching RSS feed for youtube-dl" -ForegroundColor Green
            $resp = Invoke-WebRequest $link -MaximumRedirection 0 -ErrorAction Ignore -UseBasicParsing
            $redirect_link = $resp.Headers.Location
            $version = $redirect_link.split("/")[4]
            return $version
        }
    }
}

function Get-Latest-FFmpeg ($Arch) {
    $api_gh = "https://api.github.com/repos/shinchiro/mpv-winbuild-cmake/releases/latest"
    $json = Invoke-WebRequest $api_gh -MaximumRedirection 0 -ErrorAction Ignore -UseBasicParsing | ConvertFrom-Json
    $asset = $json.assets | Where-Object { $_.name -match ('^ffmpeg-' + [Regex]::Escape($Arch) + '-git-[a-f0-9]+\.7z$') } | Select-Object -First 1
    if (-not $asset -or $asset.digest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'FFmpeg 缺少官方 SHA-256，停止更新。' }
    return $asset.name, $asset.browser_download_url, $asset.digest.Substring(7)
}

function Get-Arch {
    # Reference: http://superuser.com/a/891443
    $FilePath = [System.IO.Path]::Combine((Get-Location).Path, 'mpv.exe')
    [int32]$MACHINE_OFFSET = 4
    [int32]$PE_POINTER_OFFSET = 60

    [byte[]]$data = New-Object -TypeName System.Byte[] -ArgumentList 4096
    $stream = New-Object -TypeName System.IO.FileStream -ArgumentList ($FilePath, 'Open', 'Read')
    $stream.Read($data, 0, 4096) | Out-Null

    # DOS header is 64 bytes, last element, long (4 bytes) is the address of the PE header
    [int32]$PE_HEADER_ADDR = [System.BitConverter]::ToInt32($data, $PE_POINTER_OFFSET)
    [int32]$machineUint = [System.BitConverter]::ToUInt16($data, $PE_HEADER_ADDR + $MACHINE_OFFSET)

    $result = "" | select FilePath, FileType
    $result.FilePath = $FilePath

    switch ($machineUint)
    {
        0      { $result.FileType = 'Native' }
        0x014c { $result.FileType = 'i686' } # 32bit
        0x0200 { $result.FileType = 'Itanium' }
        0x8664 { $result.FileType = 'x86_64' } # 64bit
    }

    $stream.Close()
    $result
}

function ExtractGitFromFile {
    $stripped = .\mpv --no-config | select-string "mpv" | select-object -First 1
    $pattern = "-g([a-z0-9-]{7})"
    $bool = $stripped -match $pattern
    return $matches[1]
}

function ExtractGitFromURL($filename) {
    $pattern = "-git-([a-z0-9-]{7})"
    $bool = $filename -match $pattern
    return $matches[1]
}

function ExtractDateFromFile {
    $date = (Get-Item ./mpv.exe).LastWriteTimeUtc
    $day = $date.Day.ToString("00")
    $month = $date.Month.ToString("00")
    $year = $date.Year.ToString("0000")
    return "$year$month$day"
}

function ExtractDateFromURL($filename) {
    $pattern = "mpv-[xi864_].*-([0-9]{8})-git-([a-z0-9-]{7})"
    $bool = $filename -match $pattern
    return $matches[1]
}

function Test-Admin
{
    $user = [Security.Principal.WindowsIdentity]::GetCurrent();
    (New-Object Security.Principal.WindowsPrincipal $user).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

function Create-XML {
@"
<settings>
  <arch>unset</arch>
  <autodelete>unset</autodelete>
  <getffmpeg>unset</getffmpeg>
</settings>
"@ | Set-Content "settings.xml" -Encoding UTF8
}

function Check-Arch($arch) {
    $get_arch = ""
    $file = "settings.xml"

    if (-not (Test-Path $file)) { Create-XML }
    [xml]$doc = Get-Content -Encoding UTF8 $file
    if ($doc.settings.arch -eq "unset") {
        if ($arch -eq "i686") {
            $get_arch = "i686"
        }
        else {
            $result = Read-KeyOrTimeout "Choose variant for 64bit builds: x86_64 or x86_64-v3 (for cpu with AVX2 support) [1=x86_64 / 2=x86_64-v3 (default=1)" "D1"
            Write-Host ""
            if ($result -eq 'D1') {
                $get_arch = "x86_64"
            }
            elseif ($result -eq 'D2') {
                $get_arch = "x86_64-v3"
            }
            else {
                throw "Please enter valid input key."
            }
        }
        $doc.settings.arch = $get_arch
        $doc.Save($file)
    }
    else {
        $get_arch = $doc.settings.arch
    }
    return $get_arch
}

function Check-Autodelete($archive) {
    $autodelete = ""
    $file = "settings.xml"

    if (-not (Test-Path $file)) { exit }
    [xml]$doc = Get-Content -Encoding UTF8 $file
    if ($doc.settings.autodelete -eq "unset") {
        $result = Read-KeyOrTimeout "Delete archives after extract? [Y/n] (default=Y)" "Y"
        Write-Host ""
        if ($result -eq 'Y') {
            $autodelete = "true"
        }
        elseif ($result -eq 'N') {
            $autodelete = "false"
        }
        else {
            throw "Please enter valid input key."
        }
        $doc.settings.autodelete = $autodelete
        $doc.Save($file)
    }
    if ($doc.settings.autodelete -eq "true") {
        if (Test-Path $archive)
        {
            Remove-Item -Force $archive
        }
    }
}

function Check-GetFFmpeg() {
    $get_ffmpeg = ""
    $file = "settings.xml"

    if (-not (Test-Path $file)) { exit }
    [xml]$doc = Get-Content -Encoding UTF8 $file
    if ($doc.settings.getffmpeg -eq "unset") {
        Write-Host "FFmpeg doesn't exist. " -ForegroundColor Green -NoNewline
        $result = Read-KeyOrTimeout "Proceed with downloading? [Y/n] (default=n)" "N"
        Write-Host ""
        if ($result -eq 'Y') {
            $get_ffmpeg = "true"
        }
        elseif ($result -eq 'N') {
            $get_ffmpeg = "false"
        }
        else {
            throw "Please enter valid input key."
        }
        $doc.settings.getffmpeg = $get_ffmpeg
        $doc.Save($file)
    }
    else {
        $get_ffmpeg = $doc.settings.getffmpeg
    }
    return $get_ffmpeg
}

function Upgrade-Mpv {
    $need_download = $false
    $remoteName = ""
    $download_link = ""
    $arch = ""

    if (Check-Mpv) {
        $file_arch = (Get-Arch).FileType
        $arch = Check-Arch $file_arch
        $remoteName, $download_link, $archiveHash = Get-Latest-Mpv $arch
        $localgit = ExtractGitFromFile
        $localdate = ExtractDateFromFile
        $remotegit = ExtractGitFromURL $remoteName
        $remotedate = ExtractDateFromURL $remoteName
        if ($localgit -match $remotegit)
        {
            if ($localdate -match $remotedate)
            {
                Write-Host "You are already using latest mpv build -- $remoteName" -ForegroundColor Green
                $need_download = $false
            }
            else {
                Write-Host "Newer mpv build available" -ForegroundColor Green
                $need_download = $true
            }
        }
        else {
            Write-Host "Newer mpv build available" -ForegroundColor Green
            $need_download = $true
        }
    }
    else {
        Write-Host "mpv doesn't exist. " -ForegroundColor Green -NoNewline
        $result = Read-KeyOrTimeout "Proceed with downloading? [Y/n] (default=y)" "Y"
        Write-Host ""

        if ($result -eq 'Y') {
            $need_download = $true
            if (Test-Path (Join-Path $env:windir "SysWow64")) {
                Write-Host "Detecting System Type is 64-bit" -ForegroundColor Green
                $original_arch = "x86_64"
            }
            else {
                Write-Host "Detecting System Type is 32-bit" -ForegroundColor Green
                $original_arch = "i686"
            }
            $arch = Check-Arch $original_arch
            $remoteName, $download_link, $archiveHash = Get-Latest-Mpv $arch
        }
        elseif ($result -eq 'N') {
            $need_download = $false
        }
        else {
            throw "Please enter valid input key."
        }
    }

    if ($need_download) {
        Download-Archive $remoteName $download_link
        if ((Get-FileHash -LiteralPath $remoteName -Algorithm SHA256).Hash -ne $archiveHash) {
            throw 'mpv 构建 SHA-256 不匹配，未替换播放器。'
        }
        Check-7z
        # 只替换整套核心文件，避免上游安装脚本覆盖本项目设置。
        $coreStage = Join-Path (Get-Location).Path ('tmp\core-update-' + [Guid]::NewGuid().ToString('N'))
        $coreBackup = Join-Path (Get-Location).Path ('backup\core-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff'))
        New-Item -ItemType Directory -Path $coreStage, $coreBackup -Force | Out-Null
        & (Get-7z) x -y "-o$coreStage" $remoteName mpv.exe mpv.com '*.dll'
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $coreStage 'mpv.exe'))) {
            throw '核心解压失败，未替换播放器。'
        }
        $coreFiles = Get-ChildItem -LiteralPath $coreStage -File
        foreach ($coreFile in $coreFiles) {
            $target = Join-Path (Get-Location).Path $coreFile.Name
            if (Test-Path -LiteralPath $target) { Copy-Item -LiteralPath $target -Destination $coreBackup -ErrorAction Stop }
        }
        Get-ChildItem -LiteralPath $coreBackup -File | Select-Object Name, @{Name='SHA256'; Expression={(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}} |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $coreBackup 'old-core-checksums.json') -Encoding UTF8
        $coreFiles | Select-Object Name, @{Name='SHA256'; Expression={(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}} |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $coreBackup 'new-core-checksums.json') -Encoding UTF8
        try {
            foreach ($coreFile in $coreFiles) {
                Copy-Item -LiteralPath $coreFile.FullName -Destination (Join-Path (Get-Location).Path $coreFile.Name) -Force -ErrorAction Stop
            }
        }
        catch {
            # 复制失败时恢复整套旧文件，避免半套核心留在安装目录。
            foreach ($coreFile in $coreFiles) {
                $target = Join-Path (Get-Location).Path $coreFile.Name
                $previous = Join-Path $coreBackup $coreFile.Name
                if (Test-Path -LiteralPath $previous) { Copy-Item -LiteralPath $previous -Destination $target -Force -ErrorAction Stop }
                elseif (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -ErrorAction Stop }
            }
            throw
        }
        Write-Host "核心旧版本保留在 $coreBackup；更新后请先完成播放回归。" -ForegroundColor Green
    }
    Check-Autodelete $remoteName
}

function Upgrade-Ytplugin {
    if (Check-Ytplugin-In-System) {
        Write-Host "yt-dlp.exe or youtube-dl.exe already exists in your system, skip the update check." -ForegroundColor Green
        return
    }
    $yt = Check-Ytplugin
    if ($yt) {
        $latest_release = Get-Latest-Ytplugin((Get-Item $yt).BaseName)
        if ((& $yt --version) -match ($latest_release)) {
            Write-Host "You are already using latest" (Get-Item $yt).BaseName "-- $latest_release" -ForegroundColor Green
        }
        else {
            Write-Host "Newer" (Get-Item $yt).BaseName "build available" -ForegroundColor Green
            $backup = Backup-Tool $yt
            & $yt --update
            if ($LASTEXITCODE -ne 0) {
                Copy-Item -LiteralPath (Join-Path $backup (Split-Path $yt -Leaf)) -Destination $yt -Force -ErrorAction Stop
                throw '解析工具自更新失败，已恢复旧版。'
            }
            Get-FileHash -LiteralPath $yt -Algorithm SHA256 | Select-Object Hash, Path |
                ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'new-checksum.json') -Encoding UTF8
        }
    }
    else {
        Write-Host "ytdlp or youtube-dl doesn't exist. " -ForegroundColor Green -NoNewline
        $result = Read-KeyOrTimeout "Proceed with downloading? [Y/n] (default=n)" "N"
        Write-Host ""

        if ($result -eq 'Y') {
            $result_exe = Read-KeyOrTimeout "Download ytdlp or youtubedl? [1=ytdlp/2=youtubedl] (default=1)" "D1"
            Write-Host ""
            if ($result_exe -eq 'D1') {
                $latest_release = Get-Latest-Ytplugin "yt-dlp"
                Download-Ytplugin "yt-dlp" $latest_release
            }
            elseif ($result_exe -eq 'D2') {
                $latest_release = Get-Latest-Ytplugin "youtube-dl"
                Download-Ytplugin "youtube-dl" $latest_release
            }
            else {
                throw "Please enter valid input key."
            }
        }
    }
}

function Upgrade-FFmpeg {
    $get_ffmpeg = Check-GetFFmpeg
    if ($get_ffmpeg -eq "false") {
        return
    }

    if (Test-Path (Join-Path $env:windir "SysWow64")) {
        $original_arch = "x86_64"
        $arch = Check-Arch $original_arch
    }
    else {
        $arch = "i686"
    }

    $need_download = $false
    $remote_name, $download_link, $archiveHash = Get-Latest-FFmpeg $arch
    $ffmpeg = (Get-Location).Path + "\ffmpeg.exe"
    $ffmpeg_exist = Test-Path $ffmpeg

    if ($ffmpeg_exist) {
        $ffmpeg_file = .\ffmpeg -version | select-string "ffmpeg" | select-object -First 1
        $file_pattern_1 = "git-[0-9]{4}-[0-9]{2}-[0-9]{2}-(?<commit>[a-z0-9]+)" # git-2023-01-02-cc2b1a325
        $file_pattern_2 = "N-\d+-g(?<commit>[a-z0-9]+)"                         # N-109751-g9a820ec8b
        $file_pattern = $file_pattern_1, $file_pattern_2 -join '|'
        $url_pattern = "git-([a-z0-9]+)"
        $file_match= [Regex]::Matches($ffmpeg_file, $file_pattern)
        $remote_match = [Regex]::Matches($remote_name, $url_pattern)
        $local_git = $file_match[0].groups['commit'].value
        $remote_git = $remote_match[0].groups[1].value

        if ($local_git -match $remote_git) {
            Write-Host "You are already using latest ffmpeg build -- $remote_name" -ForegroundColor Green
            $need_download = $false
        }
        else {
            Write-Host "Newer ffmpeg build available" -ForegroundColor Green
            $need_download = $true
        }
    }
    else {
        $need_download = $true
    }

    if ($need_download) {
        Download-Archive $remote_name $download_link
        if ((Get-FileHash -LiteralPath $remote_name -Algorithm SHA256).Hash -ne $archiveHash) { throw 'FFmpeg 校验失败。' }
        Check-7z
        # 独立工具仅取 ffmpeg.exe，绝不提取 DLL 覆盖播放器核心。
        $stage = Join-Path (Get-Location).Path ('tmp\ffmpeg-' + [Guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $stage -ErrorAction Stop | Out-Null
        & (Get-7z) x -y "-o$stage" $remote_name ffmpeg.exe
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $stage 'ffmpeg.exe'))) { throw 'FFmpeg 解压失败。' }
        $backup = Backup-Tool $ffmpeg
        Copy-Item -LiteralPath (Join-Path $stage 'ffmpeg.exe') -Destination $ffmpeg -Force -ErrorAction Stop
        Get-FileHash -LiteralPath $ffmpeg -Algorithm SHA256 | Select-Object Hash, Path |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'new-checksum.json') -Encoding UTF8
    }
    Check-Autodelete $remote_name
}

function Read-KeyOrTimeout ($prompt, $key){
    $seconds = 9
    $startTime = Get-Date
    $timeOut = New-TimeSpan -Seconds $seconds

    Write-Host "$prompt " -ForegroundColor Green

    # Basic progress bar
    [Console]::CursorLeft = 0
    [Console]::Write("[")
    [Console]::CursorLeft = $seconds + 2
    [Console]::Write("]")
    [Console]::CursorLeft = 1

    while (-not [System.Console]::KeyAvailable) {
        $currentTime = Get-Date
        Start-Sleep -s 1
        Write-Host "#" -ForegroundColor Green -NoNewline
        if ($currentTime -gt $startTime + $timeOut) {
            Break
        }
    }
    if ([System.Console]::KeyAvailable) {
        $response = [System.Console]::ReadKey($true).Key
    }
    else {
        $response = $key
    }
    return $response.ToString()
}

#
# Main script entry point
#
if (Test-Admin) {
    Write-Host "Running script with administrator privileges" -ForegroundColor Yellow
}
else {
    Write-Host "Running script without administrator privileges" -ForegroundColor Red
}

try {
    Check-PowershellVersion
    # Sourceforge only support TLS 1.2
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $global:progressPreference = 'silentlyContinue'
    Upgrade-Mpv
    Upgrade-Ytplugin
    Upgrade-FFmpeg
    Write-Host "Operation completed" -ForegroundColor Magenta
}
catch [System.Exception] {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
