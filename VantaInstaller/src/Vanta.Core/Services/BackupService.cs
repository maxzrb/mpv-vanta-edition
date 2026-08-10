namespace Vanta.Core.Services;

/// <summary>
/// 覆盖升级前的配置备份服务。
/// </summary>
public static class BackupService
{
    /// <summary>
    /// 备份目标目录的 portable_config 到 backupRoot。保留最近 keep 份。
    /// </summary>
    /// <returns>备份目录路径；源不存在时返回 null</returns>
    public static string? BackupConfig(string installDirectory, string backupRoot, int keep = 5)
    {
        var src = Path.Combine(installDirectory, "portable_config");
        if (!Directory.Exists(src))
        {
            return null;
        }

        var stamp = DateTime.Now.ToString("yyyyMMdd-HHmmss");
        var dst = Path.Combine(backupRoot, $"portable_config-{stamp}");
        CopyDirectory(src, dst);

        Prune(backupRoot, keep);
        return dst;
    }

    /// <summary>递归复制目录</summary>
    private static void CopyDirectory(string sourceDir, string destDir)
    {
        Directory.CreateDirectory(destDir);

        foreach (var file in Directory.EnumerateFiles(sourceDir, "*", SearchOption.TopDirectoryOnly))
        {
            var destFile = Path.Combine(destDir, Path.GetFileName(file));
            File.Copy(file, destFile, overwrite: true);
        }

        foreach (var sub in Directory.EnumerateDirectories(sourceDir, "*", SearchOption.TopDirectoryOnly))
        {
            CopyDirectory(sub, Path.Combine(destDir, Path.GetFileName(sub)));
        }
    }

    /// <summary>仅保留最近 keep 份备份，删除更旧的</summary>
    private static void Prune(string backupRoot, int keep)
    {
        if (!Directory.Exists(backupRoot))
        {
            return;
        }

        var backups = Directory.EnumerateDirectories(backupRoot, "portable_config-*")
            .OrderByDescending(d => d)
            .ToList();

        foreach (var old in backups.Skip(keep))
        {
            try
            {
                Directory.Delete(old, recursive: true);
            }
            catch
            {
                // 删除失败（占用等）不影响安装
            }
        }
    }
}
