using System.ComponentModel;
using CommunityToolkit.Mvvm.ComponentModel;
using Vanta.Core.Services;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 可下载资产项（01~05 包，勾选 + 状态）
/// </summary>
public partial class DownloadAssetItem : ObservableObject
{
    public required UpdateService.ReleaseAsset Asset { get; init; }

    public string Name => Asset.Name;

    public string SizeText => Asset.SizeText;

    /// <summary>是否选中下载</summary>
    [ObservableProperty]
    private bool _isSelected = true;

    /// <summary>本地是否已存在且大小一致</summary>
    [ObservableProperty]
    private bool _exists;

    /// <summary>状态文本（等待/下载中 xx% /完成/跳过）</summary>
    [ObservableProperty]
    private string _status = "等待";

    /// <summary>该文件下载进度（0~100，-1 未开始）</summary>
    [ObservableProperty]
    private int _progress = -1;
}
