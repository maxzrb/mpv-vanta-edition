using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Diagnostics;
using System.IO;
using Vanta.Core.Models;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 完成页：展示安装结果、mpv 自检版本、启动 mpv / 打开目录
/// </summary>
public partial class DoneViewModel : ObservableObject
{
    private readonly AppSession _session;

    /// <summary>是否成功</summary>
    [ObservableProperty]
    private bool _isSuccess;

    /// <summary>是否为覆盖升级</summary>
    [ObservableProperty]
    private bool _isUpgrade;

    /// <summary>目标 mpv.exe 是否存在</summary>
    [ObservableProperty]
    private bool _mpvExists;

    /// <summary>mpv 版本行</summary>
    [ObservableProperty]
    private string _mpvVersion = string.Empty;

    /// <summary>备份目录</summary>
    [ObservableProperty]
    private string? _backupPath;

    /// <summary>安装目录</summary>
    [ObservableProperty]
    private string _installDirectory = string.Empty;

    /// <summary>结果摘要</summary>
    public string Summary => IsSuccess
        ? (IsUpgrade ? "覆盖升级完成！" : "全新安装完成！")
        : "安装未成功完成。";

    /// <summary>是否可启动 mpv</summary>
    public bool CanLaunch => IsSuccess && MpvExists;

    /// <summary>是否显示备份提示</summary>
    public bool HasBackup => !string.IsNullOrEmpty(BackupPath);

    /// <summary>是否可注册文件关联（目标目录存在 installer\mpv-install.bat）</summary>
    public bool CanRegister { get; private set; }

    /// <summary>注册脚本路径</summary>
    private string? RegisterBatPath => Path.Combine(InstallDirectory, "installer", "mpv-install.bat");

    /// <summary>取消注册脚本路径</summary>
    private string? UnregisterBatPath => Path.Combine(InstallDirectory, "installer", "mpv-uninstall.bat");

    public DoneViewModel(AppSession session)
    {
        _session = session;
    }

    /// <summary>从会话读取结果刷新展示</summary>
    public void Refresh()
    {
        var result = _session.InstallResult;
        if (result is null)
        {
            IsSuccess = false;
            return;
        }

        IsSuccess = result.Success;
        IsUpgrade = result.IsUpgrade;
        MpvExists = result.MpvExists;
        MpvVersion = result.MpvVersionLine ?? string.Empty;
        BackupPath = result.BackupPath;
        InstallDirectory = _session.InstallDirectory ?? string.Empty;
        CanRegister = File.Exists(RegisterBatPath);

        OnPropertyChanged(nameof(Summary));
        OnPropertyChanged(nameof(CanLaunch));
        OnPropertyChanged(nameof(HasBackup));
        OnPropertyChanged(nameof(CanRegister));
    }

    /// <summary>启动 mpv</summary>
    [RelayCommand]
    private void LaunchMpv()
    {
        if (!MpvExists)
        {
            return;
        }

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = Path.Combine(InstallDirectory, "mpv.exe"),
                WorkingDirectory = InstallDirectory,
                UseShellExecute = true,
            });
        }
        catch (Exception ex)
        {
            System.Windows.MessageBox.Show($"启动失败：{ex.Message}", "Vanta Installer");
        }
    }

    /// <summary>打开安装目录</summary>
    [RelayCommand]
    private void OpenDirectory()
    {
        if (!Directory.Exists(InstallDirectory))
        {
            return;
        }

        try
        {
            Process.Start("explorer.exe", $"\"{InstallDirectory}\"");
        }
        catch (Exception ex)
        {
            System.Windows.MessageBox.Show($"打开目录失败：{ex.Message}", "Vanta Installer");
        }
    }

    /// <summary>
    /// 注册文件关联（调用 01 包内置 installer\mpv-install.bat，需管理员提权）。
    /// </summary>
    [RelayCommand]
    private void RegisterAssociations()
    {
        RunBatElevated(RegisterBatPath, "注册文件关联");
    }

    /// <summary>取消文件关联（调用 mpv-uninstall.bat，需管理员提权）</summary>
    [RelayCommand]
    private void UnregisterAssociations()
    {
        RunBatElevated(UnregisterBatPath, "取消文件关联");
    }

    private void RunBatElevated(string? batPath, string actionName)
    {
        if (string.IsNullOrEmpty(batPath) || !File.Exists(batPath))
        {
            System.Windows.MessageBox.Show($"未找到 {batPath}", "Vanta Installer");
            return;
        }

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/c \"\"{batPath}\"\"",
                WorkingDirectory = InstallDirectory,
                UseShellExecute = true,
                // 提权：mpv-install.bat 内部要求管理员写 HKLM
                Verb = "runas",
            });
        }
        catch (Exception ex)
        {
            // 用户取消 UAC 或提权失败
            System.Windows.MessageBox.Show($"{actionName}失败：{ex.Message}", "Vanta Installer");
        }
    }
}
