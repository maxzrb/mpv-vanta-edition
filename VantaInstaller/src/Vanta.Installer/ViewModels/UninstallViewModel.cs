using System.Text;
using System.Windows;
using System.Windows.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using Vanta.Core.Services;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 卸载流程：检测 → 选项 → 执行 → 完成。
/// 全部状态变化通过 [ObservableProperty] 自动通知 + partial 方法联动派生属性，
/// 并实时通知 MainViewModel 刷新主按钮与步骤条。
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

    /// <summary>是否为带 .vanta-version 标记的 Vanta 安装</summary>
    public bool IsVanta => Installation is { IsVanta: true };

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

    /// <summary>卸载日志（命令行风格，批量刷新）</summary>
    public string LogText { get; private set; } = string.Empty;

    /// <summary>结果：备份路径</summary>
    [ObservableProperty]
    private string? _backupPath;

    /// <summary>结果：释放空间</summary>
    [ObservableProperty]
    private string _freedText = string.Empty;

    /// <summary>是否可开始卸载</summary>
    public bool CanProceed => IsDetected && !IsRunning && !IsCompleted;

    /// <summary>是否显示"检测与选项"阶段（未执行且未完成时）</summary>
    public bool ShowOptions => !IsRunning && !IsCompleted;

    /// <summary>是否显示日志</summary>
    public bool HasLog => !string.IsNullOrEmpty(LogText);

    /// <summary>卸载目录</summary>
    public string UninstallDirectory => Installation?.Directory ?? string.Empty;

    /// <summary>版本行</summary>
    public string VersionLine => Installation?.VersionLine ?? string.Empty;

    /// <summary>体积</summary>
    public string SizeText => Installation?.SizeText ?? string.Empty;

    private readonly StringBuilder _logBuffer = new();
    private readonly object _logLock = new();
    private readonly DispatcherTimer _logTimer;

    public UninstallViewModel(AppSession session, MainViewModel main)
    {
        _session = session;
        _main = main;

        // 日志批量刷新：后台线程入缓冲，UI 定时器 120ms 合并追加，避免逐行卡顿
        _logTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(120) };
        _logTimer.Tick += (_, _) => FlushLogBuffer();
        _logTimer.Start();
    }

    // ---- IsRunning / IsCompleted 变化 → 联动刷新派生属性与主按钮 ----

    partial void OnIsRunningChanged(bool value)
    {
        OnPropertyChanged(nameof(CanProceed));
        OnPropertyChanged(nameof(ShowOptions));
        // 通知 MainViewModel 刷新主按钮（卸载中禁用"开始卸载"、隐藏"返回主页"等）
        _main.NotifySubViewModelChanged();
    }

    partial void OnIsCompletedChanged(bool value)
    {
        OnPropertyChanged(nameof(CanProceed));
        OnPropertyChanged(nameof(ShowOptions));
        _main.NotifySubViewModelChanged();
    }

    partial void OnInstallationChanged(InstallationDetector.InstallationInfo? value)
    {
        OnPropertyChanged(nameof(IsDetected));
        OnPropertyChanged(nameof(IsVanta));
        OnPropertyChanged(nameof(CanProceed));
        OnPropertyChanged(nameof(UninstallDirectory));
        OnPropertyChanged(nameof(VersionLine));
        OnPropertyChanged(nameof(SizeText));
    }

    /// <summary>页面激活时刷新检测</summary>
    public void Refresh()
    {
        var detected = string.IsNullOrWhiteSpace(_session.InstallDirectory)
            ? InstallationDetector.Detect()
            : InstallationDetector.Detect(_session.InstallDirectory);
        // 指定目录存在但已无效（如刚卸载残留）时不采纳，兜底向上查找
        if (detected is not { IsValid: true })
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
        lock (_logLock)
        {
            _logBuffer.Clear();
        }
        LogText = string.Empty;
        CurrentMessage = "准备就绪";
        OnPropertyChanged(nameof(LogText));
        OnPropertyChanged(nameof(HasLog));
        OnPropertyChanged(nameof(CanProceed));
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
        IsSuccess = false;
        lock (_logLock)
        {
            _logBuffer.Clear();
        }
        LogText = string.Empty;
        CurrentMessage = "正在卸载…";
        OnPropertyChanged(nameof(LogText));
        OnPropertyChanged(nameof(HasLog));

        // 通知主按钮与步骤条：进入"执行"步骤
        _main.NotifySubViewModelChanged();
        _main.UpdateUninstallStep(1);

        try
        {
            var options = new UninstallEngine.UninstallOptions(
                UninstallDirectory,
                BackupConfig,
                CleanupAssociations);

            var result = await Task.Run(() =>
                UninstallEngine.RunAsync(options, line =>
                {
                    // 只入缓冲（批量刷新），不做逐行跨线程 DispatcherInvoke，避免删除大量文件时卡顿
                    lock (_logLock)
                    {
                        _logBuffer.AppendLine(line);
                    }
                }));

            IsSuccess = result.Success;
            BackupPath = result.BackupPath;
            FreedText = result.FreedText;
            CurrentMessage = result.Success
                ? $"卸载完成，释放 {result.FreedText}。"
                : $"卸载未完全成功：{result.Error}";

            if (result.FailedFiles.Count > 0)
            {
                lock (_logLock)
                {
                    foreach (var f in result.FailedFiles.Take(20))
                    {
                        _logBuffer.AppendLine($"无法删除：{f}");
                    }
                }
            }

            // 卸载后刷新主页状态
            _main.RefreshHome();

            // 卸载成功：清空会话指向的已删除目录，后续检测走程序目录向上查找
            _session.InstallDirectory = null;
            // 清除记忆的上次安装位置（已卸载，不再指向已删目录）
            InstallLocationStore.SaveLastInstallDirectory(null);
        }
        catch (Exception ex)
        {
            IsSuccess = false;
            CurrentMessage = $"卸载异常：{ex.Message}";
            lock (_logLock)
            {
                _logBuffer.AppendLine($"[异常] {ex.Message}");
            }
            FlushLogBuffer();
        }
        finally
        {
            IsCompleted = true;
            IsRunning = false;
            FlushLogBuffer();

            // 卸载完成：重新检测安装状态（session 目录已清，向上查找其他可用安装或 null）
            Installation = InstallationDetector.Detect();
        OnPropertyChanged(nameof(IsDetected));
        OnPropertyChanged(nameof(IsVanta));
        OnPropertyChanged(nameof(CanProceed));
        OnPropertyChanged(nameof(UninstallDirectory));

            // 通知主按钮与步骤条：进入"完成"步骤
            _main.UpdateUninstallStep(2);
            _main.NotifySubViewModelChanged();
        }
    }

    /// <summary>把缓冲日志一次性追加到 LogText（UI 线程）</summary>
    private void FlushLogBuffer()
    {
        string chunk;
        lock (_logLock)
        {
            if (_logBuffer.Length == 0)
            {
                return;
            }
            chunk = _logBuffer.ToString();
            _logBuffer.Clear();
        }

        if (LogText.Length > 1_000_000)
        {
            LogText = LogText[^500_000..] + "\n--- 日志过长已截断 ---\n";
        }
        LogText += chunk;
        OnPropertyChanged(nameof(LogText));
        OnPropertyChanged(nameof(HasLog));
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
