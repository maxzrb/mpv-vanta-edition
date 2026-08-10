using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using System.Windows.Input;
using Vanta.Core.Services;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 主页仪表盘：展示已安装状态与三大模式入口
/// </summary>
public partial class HomeViewModel : ObservableObject
{
    private readonly MainViewModel _main;

    /// <summary>检测到的安装信息（未安装为 null）</summary>
    [ObservableProperty]
    private InstallationDetector.InstallationInfo? _installation;

    /// <summary>是否已安装</summary>
    public bool IsInstalled => Installation is { IsValid: true };

    /// <summary>是否为带 .vanta-version 标记的 Vanta 安装</summary>
    public bool IsVanta => Installation is { IsVanta: true };

    /// <summary>安装目录</summary>
    public string InstallDirectory => Installation?.Directory ?? string.Empty;

    /// <summary>版本行</summary>
    public string VersionLine => Installation?.VersionLine ?? string.Empty;

    /// <summary>占用空间</summary>
    public string SizeText => Installation?.SizeText ?? string.Empty;

    /// <summary>用户手动指定的已安装 mpv 位置（持久化，优先识别）</summary>
    public string ManualMpvPath => InstallLocationStore.GetManualMpvPath() ?? string.Empty;

    /// <summary>是否有手动指定位置</summary>
    public bool HasManualPath => !string.IsNullOrWhiteSpace(ManualMpvPath);

    /// <summary>是否显示"清除手动指定"（已检测到安装且存在手动指定时）</summary>
    public bool ShowManualClear => IsInstalled && HasManualPath;

    /// <summary>状态标题</summary>
    public string StatusTitle => IsInstalled
        ? (IsVanta ? "MPV Vanta Edition 已安装" : "检测到 mpv（非 Vanta 安装）")
        : "尚未检测到安装";

    /// <summary>状态副标题</summary>
    public string StatusSubtitle => IsInstalled
        ? $"{InstallDirectory} · {SizeText}"
        : "使用“安装”模式将 01~05 增量包安装到指定位置。";

    /// <summary>进入安装模式</summary>
    public ICommand StartInstallCommand => _main.StartInstallCommand;

    /// <summary>进入卸载模式</summary>
    public ICommand StartUninstallCommand => _main.StartUninstallCommand;

    /// <summary>进入设置模式</summary>
    public ICommand OpenSettingsCommand => _main.OpenSettingsCommand;

    public HomeViewModel(MainViewModel main)
    {
        _main = main;
        Refresh();
    }

    /// <summary>重新检测安装状态</summary>
    public void Refresh()
    {
        var detected = InstallationDetector.Detect();
        Installation = detected;
        if (detected is { IsValid: true })
        {
            // 后台异步填充版本与体积，避免大目录遍历卡顿
            _ = LoadDetailsAsync(detected);
        }

        OnPropertyChanged(nameof(IsInstalled));
        OnPropertyChanged(nameof(IsVanta));
        OnPropertyChanged(nameof(InstallDirectory));
        OnPropertyChanged(nameof(VersionLine));
        OnPropertyChanged(nameof(SizeText));
        OnPropertyChanged(nameof(StatusTitle));
        OnPropertyChanged(nameof(StatusSubtitle));
        OnPropertyChanged(nameof(ManualMpvPath));
        OnPropertyChanged(nameof(HasManualPath));
        OnPropertyChanged(nameof(ShowManualClear));
    }

    /// <summary>后台填充版本与体积（不阻塞 UI）</summary>
    private async Task LoadDetailsAsync(InstallationDetector.InstallationInfo info)
    {
        try
        {
            var full = await InstallationDetector.EnrichAsync(info);
            if (Installation?.Directory == info.Directory)
            {
                Installation = full;
                OnPropertyChanged(nameof(VersionLine));
                OnPropertyChanged(nameof(SizeText));
                OnPropertyChanged(nameof(StatusSubtitle));
            }
        }
        catch
        {
            // 忽略：保持仅目录信息
        }
    }

    /// <summary>指定已安装的 mpv 位置（Vanta 或任意 mpv）</summary>
    [RelayCommand]
    private void ChooseManualPath()
    {
        var dlg = new OpenFolderDialog
        {
            Title = "指定已安装的 mpv 位置",
            Multiselect = false,
        };
        if (dlg.ShowDialog() == true)
        {
            InstallLocationStore.SaveManualMpvPath(dlg.FolderName);
            Refresh();
        }
    }

    /// <summary>清除手动指定，恢复自动检测</summary>
    [RelayCommand]
    private void ClearManualPath()
    {
        InstallLocationStore.SaveManualMpvPath(null);
        Refresh();
    }
}
