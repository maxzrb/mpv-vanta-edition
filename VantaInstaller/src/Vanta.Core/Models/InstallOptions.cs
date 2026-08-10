namespace Vanta.Core.Models;

/// <summary>
/// 安装选项
/// </summary>
public sealed class InstallOptions
{
    /// <summary>包所在目录（自动扫描 01~05）</summary>
    public required string SourceDirectory { get; init; }

    /// <summary>目标安装目录</summary>
    public required string InstallDirectory { get; init; }

    /// <summary>覆盖升级前是否备份 portable_config</summary>
    public bool BackupBeforeUpgrade { get; init; } = true;

    /// <summary>保留备份份数</summary>
    public int KeepBackups { get; init; } = 5;

    /// <summary>
    /// 要安装的包编号集合（如 ["01","02","05"]）。
    /// 为 null 时安装全部扫描到的包。
    /// </summary>
    public IReadOnlyCollection<string>? SelectedPackageIds { get; init; }

    /// <summary>
    /// 安装完成后要注册的文件关联入口（null/空=不注册）。
    /// 多实例注册 mpv.exe、单实例注册 umpv.exe；两者是独立入口，可同时注册，
    /// 注册后可在 Windows「打开方式」里自行选择用哪个打开。
    /// </summary>
    public IReadOnlyCollection<PlaybackMode>? RegisterAssociations { get; init; }
}
