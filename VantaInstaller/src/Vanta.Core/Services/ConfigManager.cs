using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// 配置备份 / 恢复 / 列表管理。
/// </summary>
public static class ConfigManager
{
    /// <summary>备份目录根（安装目录下 backup\）</summary>
    public static string BackupRoot(string installDirectory) =>
        Path.Combine(installDirectory, "backup");

    /// <summary>备份项信息</summary>
    public sealed record BackupEntry(string Path, string Stamp, long Size)
    {
        public string DisplayText => $"{Stamp} · {VantaPackage.FormatSize(Size)}";
    }

    /// <summary>
    /// 手动备份配置目录到 backup\。
    /// </summary>
    public static string? CreateBackup(string configDirectory, string backupRoot, int keep = 10)
        => BackupService.BackupConfig(configDirectory, backupRoot, keep);

    /// <summary>列出历史备份（按时间倒序）</summary>
    public static List<BackupEntry> ListBackups(string backupRoot)
    {
        if (!Directory.Exists(backupRoot))
        {
            return [];
        }

        return Directory.EnumerateDirectories(backupRoot, "portable_config-*")
            .Select(dir =>
            {
                var name = Path.GetFileName(dir);
                var stamp = name.StartsWith("portable_config-") ? name["portable_config-".Length..] : name;
                var size = SafeDirSize(dir);
                return new BackupEntry(dir, stamp, size);
            })
            .OrderByDescending(b => b.Stamp)
            .ToList();
    }

    /// <summary>
    /// 从指定备份恢复到安装目录的 portable_config（先备份当前，再整体替换）。
    /// </summary>
    public static string? Restore(string configDirectory, string backupRoot, string backupPath, int keepBefore = 10)
    {
        if (!Directory.Exists(backupPath))
        {
            return null;
        }

        // 恢复前先备份当前状态
        BackupService.BackupConfig(configDirectory, backupRoot, keepBefore);

        var dest = configDirectory;
        if (Directory.Exists(dest))
        {
            Directory.Delete(dest, recursive: true);
        }
        Directory.CreateDirectory(dest);

        CopyDirectory(backupPath, dest);
        return dest;
    }

    private static long SafeDirSize(string dir)
    {
        try
        {
            return Directory.EnumerateFiles(dir, "*", SearchOption.AllDirectories)
                .Sum(f =>
                {
                    try { return new FileInfo(f).Length; }
                    catch { return 0L; }
                });
        }
        catch
        {
            return 0;
        }
    }

    private static void CopyDirectory(string sourceDir, string destDir)
    {
        Directory.CreateDirectory(destDir);
        foreach (var file in Directory.EnumerateFiles(sourceDir, "*", SearchOption.TopDirectoryOnly))
        {
            File.Copy(file, Path.Combine(destDir, Path.GetFileName(file)), overwrite: true);
        }
        foreach (var sub in Directory.EnumerateDirectories(sourceDir, "*", SearchOption.TopDirectoryOnly))
        {
            CopyDirectory(sub, Path.Combine(destDir, Path.GetFileName(sub)));
        }
    }
}
