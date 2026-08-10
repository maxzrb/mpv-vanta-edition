using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// 文件关联 / 播放模式服务。
/// 复用 mpv 自带的两套注册脚本：
/// - 多实例：mpv-install.bat / mpv-uninstall.bat（关联指向 mpv.exe）
/// - 单实例：mpv-install (single-instance).bat / mpv-uninstall (single-instance).bat（关联指向 umpv.exe）
/// </summary>
public static class AssociationService
{
    /// <summary>安装目录下 installer\ 的相对路径</summary>
    private static string InstallerDir(string installDirectory)
        => Path.Combine(installDirectory, "installer");

    /// <summary>取指定播放模式的关联注册脚本路径（不存在返回 null）</summary>
    public static string? InstallBatPath(string installDirectory, PlaybackMode mode)
    {
        var name = mode == PlaybackMode.SingleInstance
            ? "mpv-install (single-instance).bat"
            : "mpv-install.bat";
        var path = Path.Combine(InstallerDir(installDirectory), name);
        return File.Exists(path) ? path : null;
    }

    /// <summary>取指定播放模式的关联取消脚本路径（不存在返回 null）</summary>
    public static string? UninstallBatPath(string installDirectory, PlaybackMode mode)
    {
        var name = mode == PlaybackMode.SingleInstance
            ? "mpv-uninstall (single-instance).bat"
            : "mpv-uninstall.bat";
        var path = Path.Combine(InstallerDir(installDirectory), name);
        return File.Exists(path) ? path : null;
    }

}
