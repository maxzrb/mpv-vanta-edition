using System.Collections.ObjectModel;
using System.IO;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using Vanta.Core.Services;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 卸载流程：检测 → 选项 → 执行 → 完成
/// </summary>
public partial class UninstallViewModel : ObservableObject
{
    private readonly AppSession _session;
    private readonly MainViewModel _main;

    /// <summary>检测到的安装信息</summary>
    [ObservableProperty]
    private InstallationDetector.InstallationInfo? _installation;

    /// <summary>是否检测到有效安装</summary>
    public bool IsDetected => Installation is { IsValid: true };

    /// <summary>是否备份配置（默认开）</summary>
    [ObservableProperty]
    private bool _backupConfig = true;

    /// <summary>是否清理注册表关联（默认关）</summary>
    [ObservableProperty]
    private bool _cleanupAssociations;

    /// <summary>是否正在执行</summary>
    [ObservableProperty]
    private bool _isRunning;

    /// <summary>是否已完成</summary>
    [ObservableProperty]
    private bool _isCompleted;

    /// <summary>是否成功</summary>
    [ObservableProperty]
    private bool _isSuccess;

    /// <summary>当前消息</summary>
    [ObservableProperty]
    private string _currentMessage = "准备就绪";

    /// <summary>卸载日志</summary>
    public ObservableCollection<string> LogLines { get; } = [];

    /// <summary>是否显示日志</summary>
    public bool HasLog => LogLines.Count > 0;

    /// <summary>结果：备份路径</summary>
    [ObservableProperty]
    private string? _backupPath;

    /// <summary>结果：释放空间</summary>
    [ObservableProperty]
    private string _freedText = string.Empty;

    /// <summary>是否可开始卸载</summary>
    public bool CanProceed => IsDetected && !IsRunning;

    /// <summary>卸载目录</summary>
    public string UninstallDirectory => Installation?.Directory ?? string.Empty;

    /// <summary>版本行</summary>
    public string VersionLine => Installation?.VersionLine ?? string.Empty;

    /// <summary>体积</summary>
    public string SizeText => Installation?.SizeText ?? string.Empty;

    public UninstallViewModel(AppSession session, MainViewModel main)
    {
        _session = session;
        _main = main;
    }

    /// <summary>页面激活时刷新检测</summary>
    public void Refresh()
    {
        var detected = string.IsNullOrWhiteSpace(_session.InstallDirectory)
            ? InstallationDetector.Detect()
            : InstallationDetector.Detect(_session.InstallDirectory);
        if (detected is null)
        {
            detected = InstallationDetector.Detect();
        }
        Installation = detected;
        if (detected is { IsValid: true })
        {
            // 后台异步填充版本与体积
            _ = LoadDetailsAsync(detected);
        }

        IsCompleted = false;
        IsRunning = false;
        LogLines.Clear();
        CurrentMessage = "准备就绪";
        OnPropertyChanged(nameof(IsDetected));
        OnPropertyChanged(nameof(CanProceed));
        OnPropertyChanged(nameof(UninstallDirectory));
        OnPropertyChanged(nameof(VersionLine));
        OnPropertyChanged(nameof(SizeText));
        OnPropertyChanged(nameof(HasLog));
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
            }
        }
        catch
        {
            // 忽略：保持仅目录信息
        }
    }

    /// <summary>浏览选择已安装的 mpv 目录</summary>
    [RelayCommand]
    private void ChooseDirectory()
    {
        var dlg = new OpenFolderDialog
        {
            Title = "选择已安装的 MPV Vanta Edition 目录",
            Multiselect = false,
        };
        if (dlg.ShowDialog() == true)
        {
            _session.InstallDirectory = dlg.FolderName;
            Refresh();
        }
    }

    /// <summary>开始卸载（由主按钮触发）</summary>
    public async void StartUninstall()
    {
        if (!CanProceed || IsRunning)
        {
            return;
        }

        IsRunning = true;
        IsCompleted = false;
        LogLines.Clear();
        CurrentMessage = "正在卸载…";

        try
        {
            var options = new UninstallEngine.UninstallOptions(
                UninstallDirectory,
                BackupConfig,
                CleanupAssociations);

            var result = await Task.Run(() =>
                UninstallEngine.RunAsync(options, line => DispatcherInvoke(() =>
                {
                    LogLines.Add(line);
                    CurrentMessage = line;
                    OnPropertyChanged(nameof(HasLog));
                })));

            IsSuccess = result.Success;
            BackupPath = result.BackupPath;
            FreedText = result.FreedText;
            CurrentMessage = result.Success
                ? $"卸载完成，释放 {result.FreedText}。"
                : $"卸载未完全成功：{result.Error}";

            if (result.FailedFiles.Count > 0)
            {
                DispatcherInvoke(() =>
                {
                    foreach (var f in result.FailedFiles.Take(20))
                    {
                        LogLines.Add($"无法删除：{f}");
                    }
                });
            }

            // 卸载后刷新主页状态
            _main.RefreshHome();
        }
        catch (Exception ex)
        {
            IsSuccess = false;
            CurrentMessage = $"卸载异常：{ex.Message}";
        }
        finally
        {
            IsCompleted = true;
            IsRunning = false;
            OnPropertyChanged(nameof(CanProceed));
        }
    }

    private static void DispatcherInvoke(Action action)
    {
        var dispatcher = Application.Current?.Dispatcher;
        if (dispatcher is null || dispatcher.CheckAccess())
        {
            action();
        }
        else
        {
            dispatcher.Invoke(action);
        }
    }
}
