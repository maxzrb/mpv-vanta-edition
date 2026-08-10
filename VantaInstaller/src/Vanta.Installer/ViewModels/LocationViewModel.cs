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

    /// <summary>
    /// 实际安装目录：在用户选择的基底目录下自动创建 "MPV Vanta Edition" 子文件夹，
    /// 避免 mpv 文件散落到用户已有目录中。
    /// 例外：所选目录本身已是有效 mpv 安装（含 mpv.exe）或已叫该名时，不再嵌套（覆盖升级）。
    /// </summary>
    public string FinalDirectory
    {
        get
        {
            if (string.IsNullOrWhiteSpace(InstallDirectory))
            {
                return string.Empty;
            }

            var baseDir = InstallDirectory.TrimEnd('\\', '/');

            // 已是有效 mpv 安装目录（覆盖升级）→ 直接使用
            if (File.Exists(Path.Combine(baseDir, "mpv.exe")))
            {
                return baseDir;
            }

            // 已是 "MPV Vanta Edition" 目录（不重复嵌套）
            if (string.Equals(Path.GetFileName(baseDir), "MPV Vanta Edition", StringComparison.OrdinalIgnoreCase))
            {
                return baseDir;
            }

            return Path.Combine(baseDir, "MPV Vanta Edition");
        }
    }

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

        // 智能默认：仅在用户尚未填写时，默认安装在"安装器所在目录"下的 MPV Vanta Edition 子文件夹。
        // （FinalDirectory 会处理：若安装器目录本身已是 mpv 安装，则直接使用不嵌套 → 覆盖升级）
        if (string.IsNullOrWhiteSpace(InstallDirectory))
        {
            InstallDirectory = AppContext.BaseDirectory;
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
        // 会话记录的是实际安装目录（自动补全子文件夹后的路径）
        _session.InstallDirectory = FinalDirectory;
        OnPropertyChanged(nameof(FinalDirectory));
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

        // 旧版本检测（针对实际安装目录）
        IsUpgrade = File.Exists(Path.Combine(FinalDirectory, "mpv.exe"));

        // 目录不存在：全新安装，可自动创建（不警告）
        if (!Directory.Exists(FinalDirectory))
        {
            var createMsg = string.Equals(InstallDirectory, FinalDirectory, StringComparison.OrdinalIgnoreCase)
                ? $"将作为全新安装自动创建：{FinalDirectory}"
                : $"将在 {InstallDirectory} 下自动创建 MPV Vanta Edition 文件夹并安装";
            StatusText = createMsg;
            StatusIsWarning = false;
            OnPropertyChanged(nameof(CanProceed));
            return;
        }

        // 磁盘空间预检（基于选中包总大小）
        var needed = _session.ScanResult?.SelectedTotalSize ?? 0;
        try
        {
            var root = Path.GetPathRoot(Path.GetFullPath(FinalDirectory)) ?? "C:\\";
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

}
