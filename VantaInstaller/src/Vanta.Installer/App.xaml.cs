using System.Windows;
using System.IO;
using Wpf.Ui.Appearance;

namespace Vanta.Installer;

/// <summary>
/// 应用入口：启动时应用浅色主题
/// </summary>
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // 全局异常日志（诊断用）
        DispatcherUnhandledException += (_, args) =>
        {
            try
            {
                File.WriteAllText(
                    Path.Combine(Path.GetTempPath(), "vanta-installer-crash.log"),
                    args.Exception.ToString());
            }
            catch { }
        };

        // 支持命令行参数（也服务于静默安装）：
        //   VantaInstaller.exe [包目录]            —— 位置参数指定包目录
        //   VantaInstaller.exe --packages <dir>    —— 显式指定包目录
        //   VantaInstaller.exe --target <dir>      —— 预填目标安装目录
        var packagesDir = GetArgValue(e.Args, "--packages");
        var targetDir = GetArgValue(e.Args, "--target");
        if (packagesDir is null && e.Args.Length > 0 && !e.Args[0].StartsWith('-'))
        {
            packagesDir = e.Args[0];
        }

        if (!string.IsNullOrEmpty(packagesDir) && Directory.Exists(packagesDir))
        {
            Properties["SourceDirectory"] = Path.GetFullPath(packagesDir);
        }
        if (!string.IsNullOrEmpty(targetDir))
        {
            Properties["InstallDirectory"] = Path.GetFullPath(targetDir);
        }

        // 应用 Vanta 浅色主题（跟随系统强调色）
        ApplicationThemeManager.Apply(ApplicationTheme.Light);
    }
    /// <summary>解析 --key value 形式的命令行参数</summary>
    private static string? GetArgValue(string[] args, string key)
    {
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (string.Equals(args[i], key, StringComparison.OrdinalIgnoreCase))
            {
                return args[i + 1];
            }
        }
        return null;
    }
}
