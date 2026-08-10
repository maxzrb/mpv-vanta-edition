using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
    /// 缓存清理服务：统计并清理配置目录（portable_config）下的缓存目录。
/// </summary>
public static class CacheService
{
    /// <summary>已知缓存目录（相对 portable_config）</summary>
    private static readonly string[] KnownCacheDirs =
    [
        "cache",
        "files/animated",
        "files/chapters",
        "files/cutfragments",
        "files/command_history.txt",
        "files/mpvHistory.log",
        "files/mpvClipboard.log",
    ];

    /// <summary>缓存统计</summary>
    public sealed record CacheStats(long Size, int FileCount, IReadOnlyList<string> Items)
    {
        public string SizeText => VantaPackage.FormatSize(Size);
    }

    /// <summary>统计配置目录下的缓存体积</summary>
    public static CacheStats GetCacheStats(string configDirectory)
    {
        var config = configDirectory;
        if (!Directory.Exists(config))
        {
            return new CacheStats(0, 0, []);
        }

        long total = 0;
        int files = 0;
        var items = new List<string>();

        foreach (var rel in KnownCacheDirs)
        {
            var full = Path.Combine(config, rel);
            if (File.Exists(full))
            {
                try
                {
                    var fi = new FileInfo(full);
                    total += fi.Length;
                    files++;
                    items.Add($"{rel} · {VantaPackage.FormatSize(fi.Length)}");
                }
                catch { }
            }
            else if (Directory.Exists(full))
            {
                try
                {
                    long dirSize = 0;
                    int dirFiles = 0;
                    foreach (var f in Directory.EnumerateFiles(full, "*", SearchOption.AllDirectories))
                    {
                        try
                        {
                            dirSize += new FileInfo(f).Length;
                            dirFiles++;
                        }
                        catch { }
                    }
                    total += dirSize;
                    files += dirFiles;
                    items.Add($"{rel} · {VantaPackage.FormatSize(dirSize)} · {dirFiles} 个文件");
                }
                catch { }
            }
        }

        return new CacheStats(total, files, items);
    }

    /// <summary>清理缓存，返回释放的空间</summary>
    public static long CleanCache(string configDirectory)
    {
        var config = configDirectory;
        if (!Directory.Exists(config))
        {
            return 0;
        }

        long freed = 0;
        foreach (var rel in KnownCacheDirs)
        {
            var full = Path.Combine(config, rel);
            try
            {
                if (File.Exists(full))
                {
                    var fi = new FileInfo(full);
                    freed += fi.Length;
                    File.Delete(full);
                }
                else if (Directory.Exists(full))
                {
                    freed += Directory.EnumerateFiles(full, "*", SearchOption.AllDirectories)
                        .Sum(f =>
                        {
                            try { return new FileInfo(f).Length; }
                            catch { return 0L; }
                        });
                    Directory.Delete(full, recursive: true);
                }
            }
            catch
            {
                // 占用或权限失败，忽略
            }
        }

        return freed;
    }
}
