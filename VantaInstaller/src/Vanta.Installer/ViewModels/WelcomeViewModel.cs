using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using Vanta.Core.Models;
using Vanta.Core.Services;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 欢迎页：选择并扫描包含 01~04 增量包的目录
/// </summary>
public partial class WelcomeViewModel : ObservableObject
{
    private readonly AppSession _session;

    /// <summary>包所在目录</summary>
    [ObservableProperty]
    private string _sourceDirectory = string.Empty;

    /// <summary>是否正在扫描</summary>
    [ObservableProperty]
    private bool _isScanning;

    /// <summary>状态提示文本</summary>
    [ObservableProperty]
    private string? _statusText;

    /// <summary>扫描结果</summary>
    [ObservableProperty]
    private PackageScanResult? _scanResult;

    /// <summary>是否可进入下一步</summary>
    public bool CanProceed => ScanResult is { CanInstall: true };

    /// <summary>是否有错误</summary>
    public bool HasErrors => ScanResult is { Errors.Count: > 0 };

    /// <summary>是否有警告</summary>
    public bool HasWarnings => ScanResult is { Warnings.Count: > 0 };

    /// <summary>是否检测到个人全量包</summary>
    public bool HasFullPackage => ScanResult?.FullPackage is not null;

    /// <summary>全量包显示文本</summary>
    public string? FullPackageText => ScanResult?.FullPackage?.DisplayText;

    public WelcomeViewModel(AppSession session)
    {
        _session = session;

        // 默认目录：命令行参数 > 程序所在目录（发布时安装器与包同目录最方便）
        var fromArgs = System.Windows.Application.Current?.Properties["SourceDirectory"] as string;
        SourceDirectory = !string.IsNullOrWhiteSpace(fromArgs)
            ? fromArgs
            : AppContext.BaseDirectory;
        _ = ScanAsync();
    }

    /// <summary>浏览选择包目录</summary>
    [RelayCommand]
    private void ChooseDirectory()
    {
        var dlg = new OpenFolderDialog
        {
            Title = "选择包含 01~04 增量包的文件夹",
            Multiselect = false,
        };
        if (dlg.ShowDialog() == true)
        {
            SourceDirectory = dlg.FolderName;
            _ = ScanAsync();
        }
    }

    /// <summary>扫描包目录</summary>
    [RelayCommand]
    private async Task ScanAsync()
    {
        if (string.IsNullOrWhiteSpace(SourceDirectory) || IsScanning)
        {
            return;
        }

        IsScanning = true;
        StatusText = "正在扫描…";

        try
        {
            // 宽松扫描：缺少 01 Base 只警告不阻止，让已装 Base 的升级场景能继续；
            // 是否必须 Base 由安装引擎按目标目录状态把关。
            var result = await Task.Run(() => PackageScanner.Scan(SourceDirectory, allowMissingBase: true));
            ScanResult = result;

            // 写入会话，供后续页面使用
            _session.SourceDirectory = SourceDirectory;
            _session.ScanResult = result;

            StatusText = result.CanInstall
                ? $"识别到 {result.Packages.Count} 个包，版本 {result.UnifiedVersion ?? "多个"}，可以安装。"
                : $"扫描完成，但有 {result.Errors.Count} 个问题无法安装。";
            if (result.CanInstall && result.MissingRequiredIds.Count > 0)
            {
                StatusText += " 缺少 01 Base：仅覆盖升级（目标已有 mpv）可继续，全新安装需补 01。";
            }
        }
        catch (Exception ex)
        {
            ScanResult = null;
            StatusText = $"扫描失败：{ex.Message}";
        }
        finally
        {
            IsScanning = false;
            OnPropertyChanged(nameof(CanProceed));
            OnPropertyChanged(nameof(HasErrors));
            OnPropertyChanged(nameof(HasWarnings));
            OnPropertyChanged(nameof(HasFullPackage));
            OnPropertyChanged(nameof(FullPackageText));
        }
    }
}
