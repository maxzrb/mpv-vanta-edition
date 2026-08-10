using System.Collections.ObjectModel;
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

    /// <summary>安装日志</summary>
    public ObservableCollection<string> LogLines { get; } = [];

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

    /// <summary>是否显示日志列表</summary>
    public bool HasLog => LogLines.Count > 0;

    public InstallViewModel(AppSession session)
    {
        _session = session;
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
        LogLines.Clear();

        // 日志与进度事件（后台线程触发 → 调度到 UI 线程）
        _engine.Log += line => DispatcherInvoke(() =>
        {
            LogLines.Add(line);
            OnPropertyChanged(nameof(HasLog));
        });
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
                SelectedPackageIds = _session.SelectedPackageIds,
            };

            var progress = new Progress<InstallProgress>(p =>
            {
                Percent = p.Percent;
                CurrentMessage = p.Message;
                OnPropertyChanged(nameof(PercentText));
            });

            var result = await _engine.RunAsync(options, progress);
            _session.InstallResult = result;

            // 调试：安装结果写日志文件
            try
            {
                var lines = new List<string>
                {
                    $"Success={result.Success}",
                    $"IsUpgrade={result.IsUpgrade}",
                    $"Source={options.SourceDirectory}",
                    $"Install={options.InstallDirectory}",
                    $"Selected={string.Join(",", options.SelectedPackageIds ?? [])}",
                    $"Error={result.Error}",
                    "--- Log ---",
                };
                lines.AddRange(result.Log);
                // UTF-8 带 BOM：Windows 记事本/控制台可正确显示中文与 © 符号
                var content = string.Join(Environment.NewLine, lines) + Environment.NewLine;
                File.WriteAllText(
                    Path.Combine(Path.GetTempPath(), "vanta-install-result.log"),
                    content,
                    new System.Text.UTF8Encoding(encoderShouldEmitUTF8Identifier: true));
            }
            catch { }

            IsSuccess = result.Success;
            CurrentMessage = result.Success
                ? "安装完成。"
                : $"安装失败：{result.Error}";
        }
        catch (Exception ex)
        {
            IsSuccess = false;
            CurrentMessage = $"安装异常：{ex.Message}";
            DispatcherInvoke(() => LogLines.Add($"[异常] {ex.Message}"));
        }
        finally
        {
            IsCompleted = true;
            IsRunning = false;
            OnPropertyChanged(nameof(CanProceed));
        }
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
