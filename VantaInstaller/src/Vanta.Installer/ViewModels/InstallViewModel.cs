using System.Collections.ObjectModel;
using System.Text;
using System.Windows.Threading;
using System.IO;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using Vanta.Core.Models;
using Vanta.Core.Services;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 安装进度页：驱动 InstallEngine 并展示进度与日志
/// </summary>
public partial class InstallViewModel : ObservableObject
{
    private readonly AppSession _session;
    private readonly InstallEngine _engine = new();

    /// <summary>安装日志（命令行风格，批量刷新避免逐行卡顿）</summary>
    public string LogText { get; private set; } = string.Empty;

    /// <summary>整体进度（0~100）</summary>
    [ObservableProperty]
    private int _percent;

    /// <summary>当前解压文件名</summary>
    [ObservableProperty]
    private string _currentFile = string.Empty;

    /// <summary>当前状态消息</summary>
    [ObservableProperty]
    private string _currentMessage = "准备就绪";

    /// <summary>是否正在安装</summary>
    [ObservableProperty]
    private bool _isRunning;

    /// <summary>是否已完成</summary>
    [ObservableProperty]
    private bool _isCompleted;

    /// <summary>是否成功</summary>
    [ObservableProperty]
    private bool _isSuccess;

    /// <summary>是否可进入下一步</summary>
    public bool CanProceed => IsCompleted;

    /// <summary>进度百分比文本</summary>
    public string PercentText => $"{Percent}%";

    private readonly StringBuilder _logBuffer = new();
    private readonly object _logLock = new();
    private DispatcherTimer? _logTimer;

    public InstallViewModel(AppSession session)
    {
        _session = session;

        // 日志批量刷新：后台线程塞入缓冲，UI 定时器每 120ms 一次性追加到 LogText
        _logTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(120) };
        _logTimer.Tick += (_, _) => FlushLogBuffer();
        _logTimer.Start();
    }

    /// <summary>开始安装（由主按钮触发）</summary>
    public async void StartInstall()
    {
        if (IsRunning || IsCompleted)
        {
            return;
        }

        IsRunning = true;
        IsCompleted = false;
        IsSuccess = false;
        Percent = 0;
        CurrentMessage = "正在准备…";
        lock (_logLock)
        {
            _logBuffer.Clear();
        }
        LogText = string.Empty;
        OnPropertyChanged(nameof(LogText));

        // 日志与进度事件（后台线程触发 → 调度到 UI 线程）
        _engine.Log += line =>
        {
            lock (_logLock)
            {
                _logBuffer.AppendLine(line);
            }
        };
        _engine.PackageProgress += (file, pct) => DispatcherInvoke(() =>
        {
            CurrentFile = file;
            Percent = pct;
            OnPropertyChanged(nameof(PercentText));
        });
        _engine.GlobalProgress += pct => DispatcherInvoke(() =>
        {
            Percent = pct;
            OnPropertyChanged(nameof(PercentText));
        });

        try
        {
            var options = new InstallOptions
            {
                SourceDirectory = _session.SourceDirectory!,
                InstallDirectory = _session.InstallDirectory!,
                SelectedPackageKeys = _session.SelectedPackageKeys,
                RegisterAssociations = _session.RegisterAssociations,
                ConfirmIntegrityRisksAsync = ConfirmIntegrityRisksAsync,
            };

            var progress = new Progress<InstallProgress>(p =>
            {
                Percent = p.Percent;
                CurrentMessage = p.Message;
                OnPropertyChanged(nameof(PercentText));
            });

            var result = await _engine.RunAsync(options, progress);
            _session.InstallResult = result;

            IsSuccess = result.Success;
            CurrentMessage = result.Success
                ? "安装完成。"
                : $"安装失败：{result.Error}";
        }
        catch (Exception ex)
        {
            IsSuccess = false;
            CurrentMessage = $"安装异常：{ex.Message}";
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
            OnPropertyChanged(nameof(CanProceed));
        }
    }

    /// <summary>校验风险软拦截：默认取消，用户明确选择后才允许继续。</summary>
    private static Task<bool> ConfirmIntegrityRisksAsync(PackageIntegrityResult integrity)
    {
        var lines = new List<string>
        {
            "安装包完整性校验发现风险。文件可能下载损坏、被替换，或当前无法取得可信哈希。",
            "",
        };
        if (!string.IsNullOrWhiteSpace(integrity.ReferenceError))
        {
            lines.Add($"校验源：{integrity.ReferenceError}");
            lines.Add(string.Empty);
        }

        foreach (var item in integrity.Items.Where(item => item.IsRisk))
        {
            var reason = item.Status switch
            {
                PackageIntegrityStatus.Mismatch => "SHA-256 不一致",
                PackageIntegrityStatus.MissingReference => "缺少可信 SHA-256",
                PackageIntegrityStatus.MissingFile => "文件不存在",
                PackageIntegrityStatus.ReadError => $"读取失败：{item.Error}",
                _ => "未知校验风险",
            };
            lines.Add($"• {item.FileName}：{reason}");
        }

        lines.Add(string.Empty);
        lines.Add("建议选择“否”，重新下载风险文件。仍要忽略风险并继续安装吗？");
        var choice = MessageBox.Show(
            string.Join(Environment.NewLine, lines),
            "安装包完整性风险",
            MessageBoxButton.YesNo,
            MessageBoxImage.Warning,
            MessageBoxResult.No);
        return Task.FromResult(choice == MessageBoxResult.Yes);
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
            // 防止超大日志撑爆内存：截断保留尾部
            LogText = LogText[^500_000..] + "\n--- 日志过长已截断 ---\n";
        }
        LogText += chunk;
        OnPropertyChanged(nameof(LogText));
    }

    /// <summary>在 UI 线程执行操作</summary>
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
