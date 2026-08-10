using System.Diagnostics;
using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// 卸载引擎：备份配置（可选）→ 删除安装目录 → 清理注册表关联（可选）。
/// </summary>
public static class UninstallEngine
{
    /// <summary>卸载选项</summary>
    public sealed record UninstallOptions(
        string Directory,
        bool BackupConfig,
        bool CleanupAssociations);

    /// <summary>卸载结果</summary>
    public sealed record UninstallResult(
        bool Success,
        string? BackupPath,
        string? Error,
        long FreedBytes,
        IReadOnlyList<string> FailedFiles)
    {
        public string FreedText => VantaPackage.FormatSize(FreedBytes);
    }

    /// <summary>
    /// 执行卸载。删除前强制校验目录确为有效 mpv 安装，防止误删。
    /// </summary>
    public static async Task<UninstallResult> RunAsync(UninstallOptions options, Action<string>? log = null, CancellationToken ct = default)
    {
        log ??= _ => { };
        var dir = Path.GetFullPath(options.Directory);

        try
        {
            // 安全校验：必须是有效安装
            var detect = InstallationDetector.Detect(dir);
            if (detect is null || !detect.IsValid)
            {
                return new UninstallResult(false, null, $"目录不是有效的 Vanta mpv 安装：{dir}", 0, []);
            }

            // 1. 备份配置（可选）
            string? backupPath = null;
            if (options.BackupConfig)
            {
                var backupRoot = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "VantaInstaller", "uninstall-backups");
                log($"备份配置到：{backupRoot}");
                backupPath = BackupService.BackupConfig(dir, backupRoot, keep: 10);
            }

            // 2. 删除安装目录内容
            log("正在删除安装目录…");
            var failed = new List<string>();
            long freed = 0;

            // 先统计并删除文件（可能被占用，记录失败）
            foreach (var file in Directory.EnumerateFiles(dir, "*", SearchOption.AllDirectories))
            {
                ct.ThrowIfCancellationRequested();
                try
                {
                    var fi = new FileInfo(file);
                    freed += fi.Length;
                    File.Delete(file);
                }
                catch
                {
                    failed.Add(file);
                }
            }

            // 再删除目录（自底向上）
            foreach (var sub in Directory.EnumerateDirectories(dir, "*", SearchOption.AllDirectories)
                         .OrderByDescending(d => d.Length))
            {
                ct.ThrowIfCancellationRequested();
                try
                {
                    if (Directory.EnumerateFileSystemEntries(sub).Any())
                    {
                        continue;
                    }
                    Directory.Delete(sub, recursive: true);
                }
                catch
                {
                    // 非空或占用，忽略（已记录文件失败）
                }
            }

            // 删除空目录本身
            try
            {
                if (!Directory.EnumerateFileSystemEntries(dir).Any())
                {
                    Directory.Delete(dir, recursive: true);
                }
            }
            catch
            {
                // 根目录可能因失败文件残留
            }

            // 3. 清理注册表关联（可选，提权）
            if (options.CleanupAssociations)
            {
                var uninstallBat = Path.Combine(dir, "installer", "mpv-uninstall.bat");
                if (File.Exists(uninstallBat))
                {
                    log("调用 mpv-uninstall.bat 清理文件关联（需 UAC 确认）…");
                    await RunBatElevatedAsync(uninstallBat, Path.GetDirectoryName(dir) ?? string.Empty);
                }
            }

            var success = failed.Count == 0;
            return new UninstallResult(
                success,
                backupPath,
                success ? null : $"有 {failed.Count} 个文件删除失败（可能被占用），已保留目录。",
                freed,
                failed);
        }
        catch (OperationCanceledException)
        {
            return new UninstallResult(false, null, "卸载已取消。", 0, []);
        }
        catch (Exception ex)
        {
            return new UninstallResult(false, null, ex.Message, 0, []);
        }
    }

    /// <summary>以管理员身份运行 bat（弹 UAC）</summary>
    private static async Task RunBatElevatedAsync(string batPath, string workingDir)
    {
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/c \"\"{batPath}\"\"",
                WorkingDirectory = workingDir,
                UseShellExecute = true,
                Verb = "runas",
            });
            await Task.Delay(500);
        }
        catch
        {
            // 用户取消 UAC 或提权失败，不阻断卸载
        }
    }
}
