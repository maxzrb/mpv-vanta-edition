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

    /// <summary>选中的包选择键集合（"编号|版本"，全量包为 "00"）</summary>
    public List<string>? SelectedPackageKeys { get; set; }

    /// <summary>安装结果</summary>
    public InstallResult? InstallResult { get; set; }

    /// <summary>
    /// 安装完成后要注册的文件关联入口（null/空=不注册）。
    /// 组件页可勾选「注册多实例关联」或「注册单实例关联」，可同时勾选。
    /// 默认注册多实例关联（指向 mpv.exe），避免用户安装后忘记注册文件关联；
    /// 用户显式取消后仍会保留其选择（返回组件页不重置）。
    /// </summary>
    public IReadOnlyCollection<PlaybackMode>? RegisterAssociations { get; set; } = [PlaybackMode.MultiInstance];
}
