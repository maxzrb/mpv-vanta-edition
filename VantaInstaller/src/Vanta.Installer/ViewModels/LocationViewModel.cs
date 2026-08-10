using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using System.IO;
using Vanta.Core.Models;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 安装位置页：选择目标目录、磁盘空间预检、旧版本检测
/// </summary>
public partial class LocationViewModel : ObservableObject
{
    private readonly AppSession _session;

    /// <summary>目标安装目录</summary>
    [ObservableProperty]
    private string _installDirectory = string.Empty;

    /// <summary>是否为覆盖升级（目标已有 mpv.exe）</summary>
    [ObservableProperty]
    private bool _isUpgrade;

    /// <summary>状态提示（空间/旧版检测）</summary>
    [ObservableProperty]
    private string? _statusText;

    /// <summary>状态严重性：true=警告/错误，false=正常</summary>
    [ObservableProperty]
    private bool _statusIsWarning;

    /// <summary>是否可进入下一步</summary>
    public bool CanProceed => !string.IsNullOrWhiteSpace(InstallDirectory)
        && !StatusIsWarning;

    public LocationViewModel(AppSession session)
    {
        _session = session;
    }

    /// <summary>
    /// 页面激活时调用：重新执行默认目录查找与状态预检。
    /// </summary>
    public void Refresh()
    {
        // 命令行 --target 参数优先（静默安装/测试用）
        var fromArgs = System.Windows.Application.Current?.Properties["InstallDirectory"] as string;
        if (!string.IsNullOrWhiteSpace(fromArgs))
        {
            InstallDirectory = fromArgs;
            RefreshStatus();
            return;
        }

        // 智能默认：仅在用户尚未填写时，向上查找已安装的 mpv.exe 所在目录
        if (string.IsNullOrWhiteSpace(InstallDirectory))
        {
            InstallDirectory = FindMpvDirectory() ?? string.Empty;
        }
        RefreshStatus();
    }

    /// <summary>浏览选择安装目录</summary>
    [RelayCommand]
    private void ChooseDirectory()
    {
        var dlg = new OpenFolderDialog
        {
            Title = "选择 MPV Vanta Edition 安装目录",
            Multiselect = false,
        };
        if (dlg.ShowDialog() == true)
        {
            InstallDirectory = dlg.FolderName;
        }
    }

    partial void OnInstallDirectoryChanged(string value)
    {
        _session.InstallDirectory = value;
        RefreshStatus();
    }

    /// <summary>刷新旧版本检测与磁盘空间预检</summary>
    private void RefreshStatus()
    {
        if (string.IsNullOrWhiteSpace(InstallDirectory))
        {
            StatusText = "请选择安装目录。";
            StatusIsWarning = false;
            OnPropertyChanged(nameof(CanProceed));
            return;
        }

        // 旧版本检测
        IsUpgrade = File.Exists(Path.Combine(InstallDirectory, "mpv.exe"));

        // 目录不存在：全新安装，可自动创建（不警告）
        if (!Directory.Exists(InstallDirectory))
        {
            StatusText = $"目录不存在，将作为全新安装自动创建：{InstallDirectory}";
            StatusIsWarning = false;
            OnPropertyChanged(nameof(CanProceed));
            return;
        }

        // 磁盘空间预检（基于选中包总大小）
        var needed = _session.ScanResult?.SelectedTotalSize ?? 0;
        try
        {
            var root = Path.GetPathRoot(Path.GetFullPath(InstallDirectory)) ?? "C:\\";
            var drive = new DriveInfo(root);
            if (drive.IsReady && drive.AvailableFreeSpace < needed)
            {
                StatusText = $"磁盘空间不足：需要 {VantaPackage.FormatSize(needed)}，可用 {VantaPackage.FormatSize(drive.AvailableFreeSpace)}。";
                StatusIsWarning = true;
            }
            else
            {
                var mode = IsUpgrade ? "覆盖升级（检测到旧版 mpv）" : "全新安装";
                StatusText = $"{mode} · 需要 {VantaPackage.FormatSize(needed)} · 磁盘可用 {VantaPackage.FormatSize(drive.AvailableFreeSpace)}";
                StatusIsWarning = false;
            }
        }
        catch
        {
            var mode = IsUpgrade ? "覆盖升级（检测到旧版 mpv）" : "全新安装";
            StatusText = $"{mode} · 需要 {VantaPackage.FormatSize(needed)}";
            StatusIsWarning = false;
        }

        OnPropertyChanged(nameof(CanProceed));
    }

    /// <summary>从程序目录向上查找 mpv.exe 所在目录（最多 5 层）</summary>
    private static string? FindMpvDirectory()
    {
        var dir = AppContext.BaseDirectory;
        for (int i = 0; i < 5; i++)
        {
            if (File.Exists(Path.Combine(dir, "mpv.exe")))
            {
                return dir;
            }
            var parent = Directory.GetParent(dir);
            if (parent is null)
            {
                return null;
            }
            dir = parent.FullName;
        }
        return null;
    }
}
