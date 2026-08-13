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

    /// <summary>是否已经加入当前下载队列</summary>
    [ObservableProperty]
    private bool _isQueued;

    /// <summary>当前是否正在执行下载</summary>
    [ObservableProperty]
    private bool _isActive;

    /// <summary>复选框是否可操作；正在传输的当前项不能切换。</summary>
    public bool CanSelect => !Exists && !IsActive;

    /// <summary>实时下载速度（字节/秒）</summary>
    [ObservableProperty]
    private double _speedBytesPerSecond;

    /// <summary>显示用实时速度</summary>
    public string SpeedText => Aria2Service.FormatSpeed(SpeedBytesPerSecond);

    partial void OnSpeedBytesPerSecondChanged(double value) => OnPropertyChanged(nameof(SpeedText));

    partial void OnExistsChanged(bool value) => OnPropertyChanged(nameof(CanSelect));

    partial void OnIsActiveChanged(bool value) => OnPropertyChanged(nameof(CanSelect));

    /// <summary>状态文本（等待/排队中/下载中 xx% /完成/跳过）</summary>
    [ObservableProperty]
    private string _status = "等待";

    /// <summary>该文件下载进度（0~100，-1 未开始）</summary>
    [ObservableProperty]
    private int _progress = -1;
}
