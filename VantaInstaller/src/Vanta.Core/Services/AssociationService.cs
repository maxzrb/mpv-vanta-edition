using System.Runtime.InteropServices;
using Microsoft.Win32;
using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// Windows 当前用户文件关联服务。
/// 采用 mpv 上游的 Applications + Capabilities + RegisteredApplications 结构，
/// 但为多实例和单实例使用完全独立的应用身份，避免互相覆盖或误删。
/// </summary>
public static class AssociationService
{
    public sealed record AssociationResult(bool Success, string Message);

    private sealed record AssociationDefinition(
        PlaybackMode Mode,
        string ExecutableName,
        string RegisteredApplicationName,
        string ClientKeyName,
        string ProgId,
        string FriendlyName,
        string Description);

    private const string ClassesRoot = @"Software\Classes";
    private const string RegisteredApplicationsKey = @"Software\RegisteredApplications";
    private const string AppPathsRoot = @"Software\Microsoft\Windows\CurrentVersion\App Paths";
    private const string ShortcutName = "MPV Vanta Edition.lnk";
    private const string LegacyCompatMarker = "VantaLegacyCompat";
    private const string LegacyProgIdPrefix = "io.mpv.";
    private const string DocumentIconRelativePath = @"installer\associations\icons\mpv-document.ico";

    // 视频沿用旧脚本格式集合并补入 mpv 当前默认的 ivf、mj2；修改时同步 installer/associations/current-user/vanta-associations.ps1。
    private static readonly string[] VideoExtensions =
    [
        ".3g2", ".3gp", ".3gp2", ".3gpp", ".3iv", ".264", ".265",
        ".asf", ".avc", ".avi", ".divx", ".dv", ".dvr", ".dvr-ms",
        ".evo", ".evob", ".f4v", ".flc", ".fli", ".flic", ".flv",
        ".gxf", ".h264", ".h265", ".hdmov", ".hdv", ".hevc", ".ivf",
        ".m1v", ".m2t", ".m2ts", ".m2v", ".m4v", ".mj2", ".mkv",
        ".mod", ".mov", ".mp2v", ".mp4", ".mp4v", ".mpe", ".mpeg",
        ".mpeg2", ".mpeg4", ".mpg", ".mpg4", ".mpv", ".mpv2", ".mts",
        ".mtv", ".mxf", ".nsv", ".nut", ".ogm", ".ogv", ".ogx", ".qt",
        ".rm", ".rmvb", ".tod", ".trp", ".ts", ".tsa", ".tsv", ".tts",
        ".vfw", ".vob", ".vro", ".webm", ".wm", ".wmv", ".wtv", ".x264",
        ".x265", ".xvid", ".y4m", ".yuv",
    ];

    // 音频采用 mpv 当前默认集合；图片、播放列表和压缩包暂不声明关联。
    private static readonly string[] AudioExtensions =
    [
        ".aac", ".ac3", ".aiff", ".ape", ".au", ".dts", ".eac3", ".flac",
        ".m4a", ".mka", ".mp1", ".mp2", ".mp3", ".mpc", ".oga", ".ogg",
        ".ogm", ".opus", ".tak", ".thd", ".tta", ".wav", ".wma", ".wv",
    ];

    private static readonly string[] MediaExtensions = VideoExtensions
        .Concat(AudioExtensions)
        .Distinct(StringComparer.OrdinalIgnoreCase)
        .ToArray();

    private static readonly AssociationDefinition MultiInstance = new(
        PlaybackMode.MultiInstance,
        "mpv.exe",
        "MPV Vanta Edition",
        "MPV Vanta Edition",
        "MPV.Vanta.Multi.File",
        "MPV Vanta Edition",
        "MPV Vanta Edition multi-instance player");

    private static readonly AssociationDefinition SingleInstance = new(
        PlaybackMode.SingleInstance,
        "umpv.exe",
        "MPV Vanta Edition (Single Instance)",
        "MPV Vanta Edition Single Instance",
        "MPV.Vanta.Single.File",
        "MPV Vanta Edition (Single Instance)",
        "MPV Vanta Edition single-instance player");

    /// <summary>目标入口是否具备注册条件。</summary>
    public static bool CanRegister(string installDirectory, PlaybackMode mode)
    {
        if (string.IsNullOrWhiteSpace(installDirectory))
        {
            return false;
        }

        try
        {
            var directory = Path.GetFullPath(installDirectory);
            var definition = GetDefinition(mode);
            var executable = Path.Combine(directory, definition.ExecutableName);
            var mpv = Path.Combine(directory, "mpv.exe");
            return File.Exists(executable) && File.Exists(mpv);
        }
        catch
        {
            return false;
        }
    }

    /// <summary>当前用户是否已经注册指定播放入口。</summary>
    public static bool IsRegistered(PlaybackMode mode)
    {
        try
        {
            var definition = GetDefinition(mode);
            using var registeredApplications = Registry.CurrentUser.OpenSubKey(RegisteredApplicationsKey);
            var actual = registeredApplications?.GetValue(definition.RegisteredApplicationName) as string;
            var expected = $@"Software\Clients\Media\{definition.ClientKeyName}\Capabilities";
            return string.Equals(actual, expected, StringComparison.OrdinalIgnoreCase);
        }
        catch
        {
            return false;
        }
    }

    /// <summary>为当前用户注册指定播放入口，不需要管理员权限。</summary>
    public static AssociationResult Register(
        string installDirectory,
        PlaybackMode mode,
        Action<string>? progress = null)
    {
        try
        {
            progress?.Invoke("检查播放器文件与注册条件");
            if (!CanRegister(installDirectory, mode))
            {
                var missing = mode == PlaybackMode.SingleInstance ? "mpv.exe 或 umpv.exe" : "mpv.exe";
                progress?.Invoke($"检查失败：未找到 {missing}");
                return new AssociationResult(false, $"注册失败：安装目录中未找到 {missing}。");
            }

            var directory = Path.GetFullPath(installDirectory);
            var definition = GetDefinition(mode);
            var executablePath = Path.Combine(directory, definition.ExecutableName);
            var mpvPath = Path.Combine(directory, "mpv.exe");
            var iconPath = ResolveDocumentIcon(directory, mpvPath);
            var command = mode == PlaybackMode.SingleInstance
                ? $"\"{executablePath}\" \"%L\""
                : $"\"{executablePath}\" -- \"%L\"";

            // 先清理本入口的旧值，确保路径变更后不会残留失效命令。
            progress?.Invoke("清理当前入口的旧注册信息");
            RemoveDefinition(definition);

            progress?.Invoke($"写入 Applications 与 {MediaExtensions.Length} 个支持格式");
            WriteApplicationRegistration(definition, executablePath, command);
            progress?.Invoke("写入 ProgID、Capabilities 与打开命令");
            WriteCapabilitiesRegistration(definition, command, iconPath);
            var repairedLegacyCount = RepairLegacyCompatibility(directory, iconPath);
            if (repairedLegacyCount > 0)
            {
                progress?.Invoke($"修复 {repairedLegacyCount} 个旧 io.mpv.* 图标与打开命令");
            }
            progress?.Invoke("更新开始菜单媒体入口");
            EnsureStartMenuShortcut(directory, mpvPath);
            progress?.Invoke("刷新 Windows 文件关联缓存");
            RefreshShellAssociations();

            var modeText = ModeText(mode);
            progress?.Invoke($"{modeText}文件关联注册完成");
            return new AssociationResult(
                true,
                $"已为当前用户注册{modeText}文件关联，无需管理员权限。{LegacyMachineWarning()}");
        }
        catch (Exception ex)
        {
            try
            {
                RemoveDefinition(GetDefinition(mode));
                RemoveSharedShortcutIfUnused();
                RefreshShellAssociations();
            }
            catch
            {
                // 返回原始注册错误；回滚失败由下次注册或取消操作继续清理。
            }

            progress?.Invoke($"注册失败：{ex.Message}");
            return new AssociationResult(false, $"注册文件关联失败：{ex.Message}");
        }
    }

    /// <summary>取消当前用户下指定播放入口的关联。</summary>
    public static AssociationResult Unregister(PlaybackMode mode, Action<string>? progress = null)
    {
        try
        {
            progress?.Invoke("清理 Applications、ProgID 与 Capabilities");
            RemoveDefinition(GetDefinition(mode));
            progress?.Invoke("检查并清理共享开始菜单入口");
            RemoveSharedShortcutIfUnused();
            RemoveLegacyCompatibilityIfUnused();
            progress?.Invoke("刷新 Windows 文件关联缓存");
            RefreshShellAssociations();
            progress?.Invoke($"{ModeText(mode)}文件关联已取消");
            return new AssociationResult(
                true,
                $"已取消当前用户的{ModeText(mode)}文件关联。{LegacyMachineWarning()}");
        }
        catch (Exception ex)
        {
            progress?.Invoke($"取消失败：{ex.Message}");
            return new AssociationResult(false, $"取消文件关联失败：{ex.Message}");
        }
    }

    /// <summary>取消当前用户下的多实例和单实例关联。</summary>
    public static AssociationResult UnregisterAll()
    {
        try
        {
            RemoveDefinition(MultiInstance);
            RemoveDefinition(SingleInstance);
            RemoveLegacyCompatibility();
            DeleteStartMenuShortcut();
            RefreshShellAssociations();
            return new AssociationResult(
                true,
                $"已清理当前用户的多实例和单实例文件关联。{LegacyMachineWarning()}");
        }
        catch (Exception ex)
        {
            return new AssociationResult(false, $"清理文件关联失败：{ex.Message}");
        }
    }

    private static void WriteApplicationRegistration(
        AssociationDefinition definition,
        string executablePath,
        string command)
    {
        var appPath = $@"{AppPathsRoot}\{definition.ExecutableName}";
        SetString(appPath, null, executablePath);
        SetDword(appPath, "UseUrl", 1);

        var applicationPath = $@"{ClassesRoot}\Applications\{definition.ExecutableName}";
        SetString(applicationPath, "FriendlyAppName", definition.FriendlyName);
        SetString($@"{applicationPath}\shell", null, "open");
        SetString($@"{applicationPath}\shell\open\command", null, command);

        foreach (var extension in MediaExtensions)
        {
            SetString($@"{applicationPath}\SupportedTypes", extension, string.Empty);
        }
    }

    private static void WriteCapabilitiesRegistration(
        AssociationDefinition definition,
        string command,
        string iconPath)
    {
        var progIdPath = $@"{ClassesRoot}\{definition.ProgId}";
        SetString(progIdPath, null, "MPV Vanta media file");
        SetString(progIdPath, "FriendlyTypeName", "MPV Vanta media file");
        SetDword(progIdPath, "EditFlags", 0x00010000);
        SetString($@"{progIdPath}\DefaultIcon", null, $"\"{iconPath}\",0");
        SetString($@"{progIdPath}\shell", null, "open");
        SetString($@"{progIdPath}\shell\open\command", null, command);

        var capabilitiesPath = $@"Software\Clients\Media\{definition.ClientKeyName}\Capabilities";
        SetString(capabilitiesPath, "ApplicationName", definition.FriendlyName);
        SetString(capabilitiesPath, "ApplicationDescription", definition.Description);

        foreach (var extension in MediaExtensions)
        {
            SetString($@"{capabilitiesPath}\FileAssociations", extension, definition.ProgId);
        }

        SetString(RegisteredApplicationsKey, definition.RegisteredApplicationName, capabilitiesPath);
    }

    private static void RemoveDefinition(AssociationDefinition definition)
    {
        DeleteTree($@"{AppPathsRoot}\{definition.ExecutableName}");
        DeleteTree($@"{ClassesRoot}\Applications\{definition.ExecutableName}");
        DeleteTree($@"{ClassesRoot}\{definition.ProgId}");
        DeleteTree($@"Software\Clients\Media\{definition.ClientKeyName}");
        DeleteValue(RegisteredApplicationsKey, definition.RegisteredApplicationName);
    }

    private static string ResolveDocumentIcon(string installDirectory, string mpvPath)
    {
        var documentIcon = Path.Combine(installDirectory, DocumentIconRelativePath);
        return File.Exists(documentIcon) ? documentIcon : mpvPath;
    }

    /// <summary>
    /// 旧版系统级脚本使用 io.mpv.* ProgID，并把图标固定到 installer 根目录。
    /// 目录整理后不能直接修改 HKLM，也不能篡改带哈希的 UserChoice，因此仅为
    /// 确认属于当前安装目录的旧项创建带标记的 HKCU 覆盖。
    /// </summary>
    private static int RepairLegacyCompatibility(string installDirectory, string iconPath)
    {
        var repaired = 0;
        try
        {
            using var machineClasses = Registry.LocalMachine.OpenSubKey(ClassesRoot);
            if (machineClasses is null)
            {
                return 0;
            }

            foreach (var progId in machineClasses.GetSubKeyNames())
            {
                if (!progId.StartsWith(LegacyProgIdPrefix, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                try
                {
                    using var legacyKey = machineClasses.OpenSubKey(progId);
                    using var legacyIconKey = legacyKey?.OpenSubKey("DefaultIcon");
                    using var legacyCommandKey = legacyKey?.OpenSubKey(@"shell\open\command");
                    var legacyIcon = legacyIconKey?.GetValue(string.Empty) as string ?? string.Empty;
                    var legacyCommand = legacyCommandKey?.GetValue(string.Empty) as string ?? string.Empty;
                    if (!BelongsToInstallDirectory(legacyIcon, legacyCommand, installDirectory))
                    {
                        continue;
                    }

                    var useSingleInstance = legacyCommand.Contains("umpv.exe", StringComparison.OrdinalIgnoreCase);
                    var executableName = useSingleInstance ? "umpv.exe" : "mpv.exe";
                    var executablePath = Path.Combine(installDirectory, executableName);
                    if (!File.Exists(executablePath))
                    {
                        executablePath = Path.Combine(installDirectory, "mpv.exe");
                        useSingleInstance = false;
                    }

                    var command = useSingleInstance
                        ? $"\"{executablePath}\" \"%L\""
                        : $"\"{executablePath}\" -- \"%L\"";
                    var targetPath = $@"{ClassesRoot}\{progId}";
                    var friendlyType = legacyKey?.GetValue("FriendlyTypeName") as string;
                    var defaultValue = legacyKey?.GetValue(string.Empty) as string;
                    SetString(targetPath, null, defaultValue ?? "MPV media file");
                    if (!string.IsNullOrWhiteSpace(friendlyType))
                    {
                        SetString(targetPath, "FriendlyTypeName", friendlyType);
                    }
                    SetDword(targetPath, LegacyCompatMarker, 1);
                    SetString($@"{targetPath}\DefaultIcon", null, $"\"{iconPath}\",0");
                    SetString($@"{targetPath}\shell", null, "open");
                    SetString($@"{targetPath}\shell\open\command", null, command);
                    repaired++;
                }
                catch
                {
                    // 单个旧 ProgID 损坏不应阻断新版关联注册。
                }
            }
        }
        catch
        {
            // 旧版兼容修复是可选步骤，失败不影响新版 ProgID。
        }

        return repaired;
    }

    private static bool BelongsToInstallDirectory(
        string legacyIcon,
        string legacyCommand,
        string installDirectory)
    {
        var normalizedDirectory = Path.GetFullPath(installDirectory).TrimEnd('\\', '/');
        return legacyIcon.Contains(normalizedDirectory, StringComparison.OrdinalIgnoreCase)
            || legacyCommand.Contains(normalizedDirectory, StringComparison.OrdinalIgnoreCase);
    }

    private static void RemoveLegacyCompatibilityIfUnused()
    {
        if (!IsRegistered(MultiInstance) && !IsRegistered(SingleInstance))
        {
            RemoveLegacyCompatibility();
        }
    }

    private static void RemoveLegacyCompatibility()
    {
        using var userClasses = Registry.CurrentUser.OpenSubKey(ClassesRoot);
        if (userClasses is null)
        {
            return;
        }

        var ownedProgIds = new List<string>();
        foreach (var progId in userClasses.GetSubKeyNames())
        {
            if (!progId.StartsWith(LegacyProgIdPrefix, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            using var key = userClasses.OpenSubKey(progId);
            if (key?.GetValue(LegacyCompatMarker) is int marker && marker == 1)
            {
                ownedProgIds.Add(progId);
            }
        }

        foreach (var progId in ownedProgIds)
        {
            DeleteTree($@"{ClassesRoot}\{progId}");
        }
    }

    private static bool IsRegistered(AssociationDefinition definition)
    {
        using var key = Registry.CurrentUser.OpenSubKey(RegisteredApplicationsKey);
        return key?.GetValue(definition.RegisteredApplicationName) is string;
    }

    private static void EnsureStartMenuShortcut(string installDirectory, string mpvPath)
    {
        var programs = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
        if (string.IsNullOrWhiteSpace(programs))
        {
            return;
        }

        Directory.CreateDirectory(programs);
        var shortcutPath = Path.Combine(programs, ShortcutName);
        object? shell = null;
        object? shortcut = null;

        try
        {
            var shellType = Type.GetTypeFromProgID("WScript.Shell");
            if (shellType is null)
            {
                return;
            }

            shell = Activator.CreateInstance(shellType);
            if (shell is null)
            {
                return;
            }

            dynamic shellObject = shell;
            shortcut = shellObject.CreateShortcut(shortcutPath);
            dynamic shortcutObject = shortcut;
            shortcutObject.TargetPath = mpvPath;
            shortcutObject.WorkingDirectory = installDirectory;
            shortcutObject.Description = "MPV Vanta Edition";
            shortcutObject.IconLocation = $"{mpvPath},0";
            shortcutObject.Save();
        }
        catch
        {
            // 快捷方式只用于增强系统媒体控制识别，失败不应阻断文件关联。
        }
        finally
        {
            ReleaseComObject(shortcut);
            ReleaseComObject(shell);
        }
    }

    private static void RemoveSharedShortcutIfUnused()
    {
        if (!IsRegistered(MultiInstance) && !IsRegistered(SingleInstance))
        {
            DeleteStartMenuShortcut();
        }
    }

    private static void DeleteStartMenuShortcut()
    {
        var programs = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
        if (string.IsNullOrWhiteSpace(programs))
        {
            return;
        }

        try
        {
            var shortcutPath = Path.Combine(programs, ShortcutName);
            if (File.Exists(shortcutPath))
            {
                File.Delete(shortcutPath);
            }
        }
        catch
        {
            // 快捷方式清理失败不应阻断注册表关联清理。
        }
    }

    private static void ReleaseComObject(object? value)
    {
        if (value is not null && Marshal.IsComObject(value))
        {
            Marshal.FinalReleaseComObject(value);
        }
    }

    private static void SetString(string path, string? name, string value)
    {
        using var key = Registry.CurrentUser.CreateSubKey(path, writable: true)
            ?? throw new InvalidOperationException($"无法创建注册表项：HKCU\\{path}");
        key.SetValue(name ?? string.Empty, value, RegistryValueKind.String);
    }

    private static void SetDword(string path, string name, int value)
    {
        using var key = Registry.CurrentUser.CreateSubKey(path, writable: true)
            ?? throw new InvalidOperationException($"无法创建注册表项：HKCU\\{path}");
        key.SetValue(name, value, RegistryValueKind.DWord);
    }

    private static void DeleteTree(string path)
    {
        Registry.CurrentUser.DeleteSubKeyTree(path, throwOnMissingSubKey: false);
    }

    private static void DeleteValue(string path, string name)
    {
        using var key = Registry.CurrentUser.OpenSubKey(path, writable: true);
        key?.DeleteValue(name, throwOnMissingValue: false);
    }

    private static AssociationDefinition GetDefinition(PlaybackMode mode) =>
        mode == PlaybackMode.SingleInstance ? SingleInstance : MultiInstance;

    private static string ModeText(PlaybackMode mode) =>
        mode == PlaybackMode.SingleInstance ? "单实例" : "多实例";

    private static string LegacyMachineWarning()
    {
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(RegisteredApplicationsKey);
            if (key?.GetValue("mpv") is not null)
            {
                return " 检测到旧版系统级 mpv 关联；本次不会越权删除，请在删除旧安装前用旧卸载脚本以管理员身份清理一次。";
            }
        }
        catch
        {
            // 旧版项检测失败不影响当前用户关联操作。
        }

        return string.Empty;
    }

    private static void RefreshShellAssociations()
    {
        SHChangeNotify(0x08000000, 0, IntPtr.Zero, IntPtr.Zero);
    }

    [DllImport("shell32.dll")]
    private static extern void SHChangeNotify(
        uint wEventId,
        uint uFlags,
        IntPtr dwItem1,
        IntPtr dwItem2);
}
