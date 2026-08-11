[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('register', 'unregister')]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [ValidateSet('multi', 'single')]
    [string]$Mode,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# 与 VantaInstaller AssociationService 保持一致：当前用户、双身份、音视频关联。
$ClassesRoot = 'Software\Classes'
$RegisteredApplicationsKey = 'Software\RegisteredApplications'
$AppPathsRoot = 'Software\Microsoft\Windows\CurrentVersion\App Paths'
$ShortcutName = 'MPV Vanta Edition.lnk'
$LegacyCompatMarker = 'VantaLegacyCompat'
$LegacyProgIdPrefix = 'io.mpv.'
$DocumentIconRelativePath = 'installer\associations\icons\mpv-document.ico'

$VideoExtensions = @(
    '.3g2', '.3gp', '.3gp2', '.3gpp', '.3iv', '.264', '.265',
    '.asf', '.avc', '.avi', '.divx', '.dv', '.dvr', '.dvr-ms',
    '.evo', '.evob', '.f4v', '.flc', '.fli', '.flic', '.flv',
    '.gxf', '.h264', '.h265', '.hdmov', '.hdv', '.hevc', '.ivf',
    '.m1v', '.m2t', '.m2ts', '.m2v', '.m4v', '.mj2', '.mkv',
    '.mod', '.mov', '.mp2v', '.mp4', '.mp4v', '.mpe', '.mpeg',
    '.mpeg2', '.mpeg4', '.mpg', '.mpg4', '.mpv', '.mpv2', '.mts',
    '.mtv', '.mxf', '.nsv', '.nut', '.ogm', '.ogv', '.ogx', '.qt',
    '.rm', '.rmvb', '.tod', '.trp', '.ts', '.tsa', '.tsv', '.tts',
    '.vfw', '.vob', '.vro', '.webm', '.wm', '.wmv', '.wtv', '.x264',
    '.x265', '.xvid', '.y4m', '.yuv'
)

$AudioExtensions = @(
    '.aac', '.ac3', '.aiff', '.ape', '.au', '.dts', '.eac3', '.flac',
    '.m4a', '.mka', '.mp1', '.mp2', '.mp3', '.mpc', '.oga', '.ogg',
    '.ogm', '.opus', '.tak', '.thd', '.tta', '.wav', '.wma', '.wv'
)

$MediaExtensions = @($VideoExtensions + $AudioExtensions | Sort-Object -Unique)

$Definitions = @{
    multi = @{
        ExecutableName = 'mpv.exe'
        RegisteredApplicationName = 'MPV Vanta Edition'
        ClientKeyName = 'MPV Vanta Edition'
        ProgId = 'MPV.Vanta.Multi.File'
        FriendlyName = 'mpv'
        Description = 'MPV Vanta Edition multi-instance player'
    }
    single = @{
        ExecutableName = 'umpv.exe'
        RegisteredApplicationName = 'MPV Vanta Edition (Single Instance)'
        ClientKeyName = 'MPV Vanta Edition Single Instance'
        ProgId = 'MPV.Vanta.Single.File'
        FriendlyName = 'mpv-single'
        Description = 'MPV Vanta Edition single-instance player'
    }
}

function Set-RegistryString {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Name,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value
    )

    $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($Path, $true)
    if ($null -eq $key) {
        throw "Cannot create registry key: HKCU\$Path"
    }
    try {
        $key.SetValue($Name, $Value, [Microsoft.Win32.RegistryValueKind]::String)
    }
    finally {
        $key.Dispose()
    }
}

function Set-RegistryDword {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][int]$Value
    )

    $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($Path, $true)
    if ($null -eq $key) {
        throw "Cannot create registry key: HKCU\$Path"
    }
    try {
        $key.SetValue($Name, $Value, [Microsoft.Win32.RegistryValueKind]::DWord)
    }
    finally {
        $key.Dispose()
    }
}

function Remove-RegistryTree {
    param([Parameter(Mandatory = $true)][string]$Path)
    [Microsoft.Win32.Registry]::CurrentUser.DeleteSubKeyTree($Path, $false)
}

function Remove-RegistryValue {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($Path, $true)
    if ($null -eq $key) {
        return
    }
    try {
        $key.DeleteValue($Name, $false)
    }
    finally {
        $key.Dispose()
    }
}

function Remove-Definition {
    param([Parameter(Mandatory = $true)][hashtable]$Definition)

    Remove-RegistryTree "$AppPathsRoot\$($Definition.ExecutableName)"
    Remove-RegistryTree "$ClassesRoot\Applications\$($Definition.ExecutableName)"
    Remove-RegistryTree "$ClassesRoot\$($Definition.ProgId)"
    Remove-RegistryTree "Software\Clients\Media\$($Definition.ClientKeyName)"
    Remove-RegistryValue $RegisteredApplicationsKey $Definition.RegisteredApplicationName
}

function Test-DefinitionRegistered {
    param([Parameter(Mandatory = $true)][hashtable]$Definition)

    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($RegisteredApplicationsKey)
    if ($null -eq $key) {
        return $false
    }
    try {
        return $null -ne $key.GetValue($Definition.RegisteredApplicationName)
    }
    finally {
        $key.Dispose()
    }
}

function Write-ApplicationRegistration {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Definition,
        [Parameter(Mandatory = $true)][string]$ExecutablePath,
        [Parameter(Mandatory = $true)][string]$Command
    )

    $appPath = "$AppPathsRoot\$($Definition.ExecutableName)"
    Set-RegistryString $appPath '' $ExecutablePath
    Set-RegistryDword $appPath 'UseUrl' 1

    $applicationPath = "$ClassesRoot\Applications\$($Definition.ExecutableName)"
    Set-RegistryString $applicationPath 'FriendlyAppName' $Definition.FriendlyName
    Set-RegistryString "$applicationPath\shell" '' 'open'
    Set-RegistryString "$applicationPath\shell\open\command" '' $Command

    foreach ($extension in $MediaExtensions) {
        Set-RegistryString "$applicationPath\SupportedTypes" $extension ''
    }
}

function Write-CapabilitiesRegistration {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Definition,
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string]$IconPath
    )

    $progIdPath = "$ClassesRoot\$($Definition.ProgId)"
    Set-RegistryString $progIdPath '' 'MPV Vanta media file'
    Set-RegistryString $progIdPath 'FriendlyTypeName' 'MPV Vanta media file'
    Set-RegistryDword $progIdPath 'EditFlags' 65536
    Set-RegistryString "$progIdPath\DefaultIcon" '' ('"{0}",0' -f $IconPath)
    Set-RegistryString "$progIdPath\shell" '' 'open'
    Set-RegistryString "$progIdPath\shell\open\command" '' $Command

    $capabilitiesPath = "Software\Clients\Media\$($Definition.ClientKeyName)\Capabilities"
    Set-RegistryString $capabilitiesPath 'ApplicationName' $Definition.FriendlyName
    Set-RegistryString $capabilitiesPath 'ApplicationDescription' $Definition.Description

    foreach ($extension in $MediaExtensions) {
        Set-RegistryString "$capabilitiesPath\FileAssociations" $extension $Definition.ProgId
    }

    Set-RegistryString $RegisteredApplicationsKey $Definition.RegisteredApplicationName $capabilitiesPath
}

function Ensure-StartMenuShortcut {
    param(
        [Parameter(Mandatory = $true)][string]$InstallDirectory,
        [Parameter(Mandatory = $true)][string]$MpvPath
    )

    $programs = [Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)
    if ([string]::IsNullOrWhiteSpace($programs)) {
        return
    }

    $shell = $null
    $shortcut = $null
    try {
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut((Join-Path $programs $ShortcutName))
        $shortcut.TargetPath = $MpvPath
        $shortcut.WorkingDirectory = $InstallDirectory
        $shortcut.Description = 'MPV Vanta Edition'
        $shortcut.IconLocation = "$MpvPath,0"
        $shortcut.Save()
    }
    catch {
        Write-Warning "Start Menu shortcut was not created: $($_.Exception.Message)"
    }
    finally {
        if ($null -ne $shortcut -and [Runtime.InteropServices.Marshal]::IsComObject($shortcut)) {
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shortcut)
        }
        if ($null -ne $shell -and [Runtime.InteropServices.Marshal]::IsComObject($shell)) {
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shell)
        }
    }
}

function Remove-StartMenuShortcutIfUnused {
    if ((Test-DefinitionRegistered $Definitions.multi) -or
        (Test-DefinitionRegistered $Definitions.single)) {
        return
    }

    $programs = [Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)
    if ([string]::IsNullOrWhiteSpace($programs)) {
        return
    }

    $shortcutPath = Join-Path $programs $ShortcutName
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath -Force -ErrorAction SilentlyContinue
    }
}

function Repair-LegacyCompatibility {
    param(
        [Parameter(Mandatory = $true)][string]$InstallDirectory,
        [Parameter(Mandatory = $true)][string]$IconPath
    )

    $repaired = 0
    $machineClasses = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey($ClassesRoot)
    if ($null -eq $machineClasses) {
        return $repaired
    }

    try {
        foreach ($progId in $machineClasses.GetSubKeyNames()) {
            if (-not $progId.StartsWith($LegacyProgIdPrefix, [StringComparison]::OrdinalIgnoreCase)) {
                continue
            }

            $legacyKey = $null
            $legacyIconKey = $null
            $legacyCommandKey = $null
            try {
                $legacyKey = $machineClasses.OpenSubKey($progId)
                if ($null -eq $legacyKey) {
                    continue
                }
                $legacyIconKey = $legacyKey.OpenSubKey('DefaultIcon')
                $legacyCommandKey = $legacyKey.OpenSubKey('shell\open\command')
                $legacyIcon = if ($null -ne $legacyIconKey) { [string]$legacyIconKey.GetValue('') } else { '' }
                $legacyCommand = if ($null -ne $legacyCommandKey) { [string]$legacyCommandKey.GetValue('') } else { '' }
                if ($legacyIcon.IndexOf($InstallDirectory, [StringComparison]::OrdinalIgnoreCase) -lt 0 -and
                    $legacyCommand.IndexOf($InstallDirectory, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
                    continue
                }

                $useSingle = $legacyCommand.IndexOf('umpv.exe', [StringComparison]::OrdinalIgnoreCase) -ge 0
                $legacyExecutable = Join-Path $InstallDirectory $(if ($useSingle) { 'umpv.exe' } else { 'mpv.exe' })
                if (-not (Test-Path -LiteralPath $legacyExecutable -PathType Leaf)) {
                    $legacyExecutable = Join-Path $InstallDirectory 'mpv.exe'
                    $useSingle = $false
                }
                $repairedCommand = if ($useSingle) {
                    '"{0}" "%L"' -f $legacyExecutable
                }
                else {
                    '"{0}" -- "%L"' -f $legacyExecutable
                }

                $targetPath = "$ClassesRoot\$progId"
                $defaultValue = [string]$legacyKey.GetValue('')
                if ([string]::IsNullOrWhiteSpace($defaultValue)) {
                    $defaultValue = 'MPV media file'
                }
                Set-RegistryString $targetPath '' $defaultValue
                $friendlyType = [string]$legacyKey.GetValue('FriendlyTypeName')
                if (-not [string]::IsNullOrWhiteSpace($friendlyType)) {
                    Set-RegistryString $targetPath 'FriendlyTypeName' $friendlyType
                }
                Set-RegistryDword $targetPath $LegacyCompatMarker 1
                Set-RegistryString "$targetPath\DefaultIcon" '' ('"{0}",0' -f $IconPath)
                Set-RegistryString "$targetPath\shell" '' 'open'
                Set-RegistryString "$targetPath\shell\open\command" '' $repairedCommand
                $repaired++
            }
            catch {
                # 单个旧 ProgID 损坏不应阻断新版关联注册。
            }
            finally {
                if ($null -ne $legacyCommandKey) { $legacyCommandKey.Dispose() }
                if ($null -ne $legacyIconKey) { $legacyIconKey.Dispose() }
                if ($null -ne $legacyKey) { $legacyKey.Dispose() }
            }
        }
    }
    finally {
        $machineClasses.Dispose()
    }

    return $repaired
}

function Remove-LegacyCompatibilityIfUnused {
    if ((Test-DefinitionRegistered $Definitions.multi) -or
        (Test-DefinitionRegistered $Definitions.single)) {
        return
    }

    $userClasses = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($ClassesRoot)
    if ($null -eq $userClasses) {
        return
    }

    $owned = @()
    try {
        foreach ($progId in $userClasses.GetSubKeyNames()) {
            if (-not $progId.StartsWith($LegacyProgIdPrefix, [StringComparison]::OrdinalIgnoreCase)) {
                continue
            }
            $key = $userClasses.OpenSubKey($progId)
            try {
                if ($null -ne $key -and [int]$key.GetValue($LegacyCompatMarker, 0) -eq 1) {
                    $owned += $progId
                }
            }
            finally {
                if ($null -ne $key) { $key.Dispose() }
            }
        }
    }
    finally {
        $userClasses.Dispose()
    }

    foreach ($progId in $owned) {
        Remove-RegistryTree "$ClassesRoot\$progId"
    }
}

function Refresh-ShellAssociations {
    if ($null -eq ('VantaAssociationNative' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class VantaAssociationNative
{
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(
        uint eventId, uint flags, IntPtr item1, IntPtr item2);
}
'@
    }

    [VantaAssociationNative]::SHChangeNotify(
        0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
}

function Show-LegacyMachineWarning {
    try {
        $key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey($RegisteredApplicationsKey)
        if ($null -eq $key) {
            return
        }
        try {
            if ($null -ne $key.GetValue('mpv')) {
                Write-Warning 'A legacy system-wide mpv registration still exists. Confirm it belongs to an old Vanta installation before using the legacy administrator uninstall BAT files.'
            }
        }
        finally {
            $key.Dispose()
        }
    }
    catch {
        # 旧版项检测失败不影响当前用户关联操作。
    }
}

$Definition = $Definitions[$Mode]
$InstallDirectory = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$ExecutablePath = Join-Path $InstallDirectory $Definition.ExecutableName
$MpvPath = Join-Path $InstallDirectory 'mpv.exe'
$DocumentIconPath = Join-Path $InstallDirectory $DocumentIconRelativePath
if (-not (Test-Path -LiteralPath $DocumentIconPath -PathType Leaf)) {
    $DocumentIconPath = $MpvPath
}
$ModeText = if ($Mode -eq 'single') { 'single-instance' } else { 'multi-instance' }

if ($DryRun) {
    Write-Host "Dry run: action=$Action mode=$Mode scope=HKCU"
    Write-Host "Executable: $ExecutablePath"
    Write-Host "ProgID: $($Definition.ProgId)"
    Write-Host "Media extensions: $($MediaExtensions.Count)"
    exit 0
}

try {
    if ($Action -eq 'register') {
        if (-not (Test-Path -LiteralPath $MpvPath -PathType Leaf)) {
            throw "mpv.exe was not found: $MpvPath"
        }
        if (-not (Test-Path -LiteralPath $ExecutablePath -PathType Leaf)) {
            throw "$($Definition.ExecutableName) was not found: $ExecutablePath"
        }

        $Command = if ($Mode -eq 'single') {
            '"{0}" "%L"' -f $ExecutablePath
        }
        else {
            '"{0}" -- "%L"' -f $ExecutablePath
        }

        # 先删除本入口旧值，避免移动目录后留下失效路径。
        Remove-Definition $Definition
        Write-ApplicationRegistration $Definition $ExecutablePath $Command
        Write-CapabilitiesRegistration $Definition $Command $DocumentIconPath
        $repairedLegacyCount = Repair-LegacyCompatibility $InstallDirectory $DocumentIconPath
        Ensure-StartMenuShortcut $InstallDirectory $MpvPath
        Refresh-ShellAssociations
        Write-Host "Registered the $ModeText entry for the current user. No administrator rights are required."
        if ($repairedLegacyCount -gt 0) {
            Write-Host "Repaired $repairedLegacyCount legacy io.mpv.* icon and command entries for the current user."
        }
    }
    else {
        Remove-Definition $Definition
        Remove-StartMenuShortcutIfUnused
        Remove-LegacyCompatibilityIfUnused
        Refresh-ShellAssociations
        Write-Host "Unregistered the $ModeText entry for the current user."
    }

    Show-LegacyMachineWarning
    exit 0
}
catch {
    if ($Action -eq 'register') {
        try {
            Remove-Definition $Definition
            Remove-StartMenuShortcutIfUnused
            Refresh-ShellAssociations
        }
        catch {
            # 返回原始错误；下次注册或取消会继续清理当前入口。
        }
    }

    Write-Error $_.Exception.Message
    exit 1
}
