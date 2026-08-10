using System.Collections.ObjectModel;
using System.ComponentModel;
using CommunityToolkit.Mvvm.ComponentModel;
using Vanta.Core.Models;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 组件选择页：从扫描结果动态生成可勾选包列表
/// </summary>
public partial class PackagesViewModel : ObservableObject
{
    private readonly AppSession _session;

    /// <summary>包勾选项列表</summary>
    public ObservableCollection<PackageItem> Packages { get; } = [];

    /// <summary>是否可进入下一步（至少一个选中）</summary>
    public bool CanProceed => Packages.Any(p => p.IsSelected);

    /// <summary>汇总文本</summary>
    public string SummaryText => $"共 {Packages.Count} 个包，选中 {Packages.Count(p => p.IsSelected)} 个 · 需要 {VantaPackage.FormatSize(_session.ScanResult?.SelectedTotalSize ?? 0)}";

    public PackagesViewModel(AppSession session)
    {
        _session = session;
    }

    /// <summary>
    /// 页面激活时调用：从会话中的扫描结果重建勾选列表。
    /// （页面 VM 在向导创建时即构造，但扫描是异步的，需在导航进入时刷新）
    /// </summary>
    public void Refresh()
    {
        // 保留用户已勾选状态（返回本页时不重置）
        var previousSelection = Packages.ToDictionary(p => p.Id, p => p.IsSelected);
        Packages.Clear();

        if (_session.ScanResult is { } scan)
        {
            // 个人全量包：解压即用一体包，与 01~05 增量包二选一（默认不选）
            if (scan.FullPackage is { } full)
            {
                var fullItem = new PackageItem(full)
                {
                    // 保留用户之前的选择；全新扫描默认不选全量包
                    IsSelected = previousSelection.TryGetValue("00", out var s) && s,
                };
                fullItem.PropertyChanged += OnItemPropertyChanged;
                Packages.Add(fullItem);
            }

            foreach (var pkg in scan.Packages)
            {
                var item = new PackageItem(pkg);
                if (previousSelection.TryGetValue(pkg.Id, out var selected))
                {
                    item.IsSelected = selected;
                }
                // 全量包被选中时增量包保持禁用（返回本页不重置互斥状态）
                if (previousSelection.TryGetValue("00", out var fullSel) && fullSel)
                {
                    item.IsEnabled = false;
                }
                item.PropertyChanged += OnItemPropertyChanged;
                Packages.Add(item);
            }
        }

        // 同步选中状态到会话
        _session.SelectedPackageIds = Packages.Where(p => p.IsSelected).Select(p => p.Id).ToList();
        OnPropertyChanged(nameof(CanProceed));
        OnPropertyChanged(nameof(SummaryText));
    }

    private void OnItemPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(PackageItem.IsSelected))
        {
            // 强互斥联动：
            // - 勾选全量包 → 取消并禁用所有增量包（避免混装出问题）
            // - 取消全量包 → 恢复增量包可勾选（保持已选状态）
            // - 勾选任一增量包 → 自动取消全量包
            if (sender is PackageItem item && item.Id == "00")
            {
                foreach (var other in Packages.Where(p => p.Id != "00"))
                {
                    other.IsSelected = !item.IsSelected;
                    other.IsEnabled = !item.IsSelected;
                }
            }
            else if (sender is PackageItem inc && inc.IsSelected)
            {
                var full = Packages.FirstOrDefault(p => p.Id == "00");
                if (full is { IsSelected: true })
                {
                    full.IsSelected = false;
                    foreach (var other in Packages.Where(p => p.Id != "00"))
                    {
                        other.IsEnabled = true;
                    }
                }
            }

            // 同步到会话，供安装页读取
            _session.SelectedPackageIds = Packages
                .Where(p => p.IsSelected)
                .Select(p => p.Id)
                .ToList();

            OnPropertyChanged(nameof(CanProceed));
            OnPropertyChanged(nameof(SummaryText));
        }
    }
}

/// <summary>
/// 可观察的包勾选项（包装 VantaPackage，支持选中状态通知）
/// </summary>
public partial class PackageItem : ObservableObject
{
    /// <summary>底层包数据</summary>
    public VantaPackage Package { get; }

    public string Id => Package.Id;

    public string DisplayName => Package.DisplayName;

    public string Version => Package.Version;

    public string SizeText => VantaPackage.FormatSize(Package.TotalSize);

    public bool IsRequired => Package.Required;

    public bool IsComplete => Package.IsComplete;

    public string StatusText => IsComplete ? "完整" : $"分卷缺失：{string.Join("、", Package.MissingParts)}";

    /// <summary>是否选中</summary>
    [ObservableProperty]
    private bool _isSelected = true;

    /// <summary>是否可勾选（全量包选中时增量包禁用，避免混装）</summary>
    [ObservableProperty]
    private bool _isEnabled = true;

    public PackageItem(VantaPackage package)
    {
        Package = package;
        IsSelected = package.IsSelected;
    }
}
