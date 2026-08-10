using Vanta.Core.Models;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 跨向导页共享的安装会话状态
/// </summary>
public sealed class AppSession
{
    /// <summary>包所在目录</summary>
    public string? SourceDirectory { get; set; }

    /// <summary>包扫描结果</summary>
    public PackageScanResult? ScanResult { get; set; }

    /// <summary>目标安装目录</summary>
    public string? InstallDirectory { get; set; }

    /// <summary>选中的包编号集合</summary>
    public List<string>? SelectedPackageIds { get; set; }

    /// <summary>安装结果</summary>
    public InstallResult? InstallResult { get; set; }

    /// <summary>
    /// 安装完成后要注册的文件关联入口（null/空=不注册）。
    /// 组件页可勾选「注册多实例关联」或「注册单实例关联」，可同时勾选。
    /// </summary>
    public IReadOnlyCollection<PlaybackMode>? RegisterAssociations { get; set; }
}
