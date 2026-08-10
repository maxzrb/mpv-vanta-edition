using System.Diagnostics;

namespace Vanta.Core.Services;

/// <summary>
/// 已安装 Vanta mpv 的检测服务。
/// 零侵入：不写入任何 marker，靠目录特征（mpv.exe + portable_config\mpv.conf）识别。
/// </summary>
public static class InstallationDetector
{
    /// <summary>检测结果</summary>
    public sealed record InstallationInfo(
        string Directory,
        bool HasMpv,
        bool HasConfig,
        bool HasInstallerScripts,
        string? VersionLine,
        long TotalSize)
    {
        /// <summary>是否为有效安装</summary>
        public bool IsValid => HasMpv && HasConfig;

        /// <summary>人类可读体积</summary>
        public string SizeText => Models.VantaPackage.FormatSize(TotalSize);
    }

    /// <summary>
    /// 快速检测已安装目录（仅存在性检查，不统计体积/版本，避免大目录卡顿）。
    /// 优先用指定目录，否则从程序目录向上查找（最多 10 层）。
    /// </summary>
    public static InstallationInfo? Detect(string? directory = null)
    {
        if (!string.IsNullOrWhiteSpace(directory) && Directory.Exists(directory))
        {
            return Inspect(directory);
        }

        var dir = AppContext.BaseDirectory;
        for (int i = 0; i < 10; i++)
        {
            if (Directory.Exists(dir))
            {
                var info = Inspect(dir);
                if (info.IsValid)
                {
                    return info;
                }
            }

            var parent = Directory.GetParent(dir);
            if (parent is null)
            {
                return null;
            }
            dir = parent.FullName;
        }

        return null;
    }

    /// <summary>
    /// 后台填充详情：mpv 版本 + 目录体积（耗时操作，供 UI 异步调用）。
    /// </summary>
    public static Task<InstallationInfo> EnrichAsync(InstallationInfo info, CancellationToken ct = default)
        => Task.Run(() =>
        {
            var version = info.HasMpv
                ? TryGetVersionLine(Path.Combine(info.Directory, "mpv.exe"))
                : null;

            long size = 0;
            try
            {
                size = Directory.EnumerateFiles(info.Directory, "*", SearchOption.AllDirectories)
                    .Sum(f =>
                    {
                        ct.ThrowIfCancellationRequested();
                        try { return new FileInfo(f).Length; }
                        catch { return 0L; }
                    });
            }
            catch
            {
                // 部分文件不可读或取消时忽略
            }

            return info with { VersionLine = version, TotalSize = size };
        }, ct);

    /// <summary>检查单个目录是否为有效安装</summary>
    private static InstallationInfo Inspect(string directory)
    {
        var mpvPath = Path.Combine(directory, "mpv.exe");
        var configPath = Path.Combine(directory, "portable_config", "mpv.conf");
        var hasMpv = File.Exists(mpvPath);
        var hasConfig = File.Exists(configPath);
        var hasScripts = Directory.Exists(Path.Combine(directory, "installer"));

        // 注意：此处不做体积统计与版本查询（耗时），由 EnrichAsync 后台填充
        return new InstallationInfo(directory, hasMpv, hasConfig, hasScripts, null, 0);
    }

    /// <summary>读取 mpv --version 首行（显式 UTF-8，避免 © 乱码）</summary>
    private static string? TryGetVersionLine(string mpvPath)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = mpvPath,
                Arguments = "--version",
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8,
                StandardErrorEncoding = System.Text.Encoding.UTF8,
            };
            using var proc = Process.Start(psi);
            if (proc is null)
            {
                return null;
            }
            var line = proc.StandardOutput.ReadLine();
            proc.WaitForExit(2000);
            return line;
        }
        catch
        {
            return null;
        }
    }
}
