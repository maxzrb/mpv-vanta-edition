using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;

namespace Vanta.Core.Services;

/// <summary>
/// aria2c 下载服务：定位可执行文件、多线程下载、进度解析、断点续传。
/// </summary>
public sealed partial class Aria2Service
{
    private readonly string? _explicitPath;
    private string? _resolvedPath;

    /// <summary>aria2c 输出行</summary>
    public event Action<string>? OutputReceived;

    /// <summary>下载进度（文件名，0~100）</summary>
    public event Action<string, int>? ProgressChanged;

    public Aria2Service(string? explicitPath = null) => _explicitPath = explicitPath;

    /// <summary>已解析的 aria2c 路径</summary>
    public string? ResolvedPath => _resolvedPath;

    /// <summary>是否已就绪（定位成功）</summary>
    public bool IsReady => _resolvedPath is not null;

    /// <summary>
    /// 定位 aria2c：显式路径 → PATH → 仓库自带 aria2\aria2c.exe → 下载兜底。
    /// </summary>
    public async Task<string> LocateAsync()
    {
        if (_resolvedPath is not null)
        {
            return _resolvedPath;
        }

        // 1. 显式指定
        if (!string.IsNullOrEmpty(_explicitPath) && File.Exists(_explicitPath))
        {
            return _resolvedPath = _explicitPath;
        }

        // 2. PATH
        var fromPath = FindInPath("aria2c.exe");
        if (fromPath is not null)
        {
            return _resolvedPath = fromPath;
        }

        // 3. 仓库自带 aria2\aria2c.exe（向上查找）
        var bundled = FindUpwards("aria2", "aria2c.exe", 5);
        if (bundled is not null)
        {
            return _resolvedPath = bundled;
        }

        // 4. 下载 aria2c 兜底（官方 Windows 构建 1.37.0）
        var dir = Path.Combine(Path.GetTempPath(), "vanta-aria2");
        Directory.CreateDirectory(dir);
        var fallback = Path.Combine(dir, "aria2c.exe");
        if (!File.Exists(fallback))
        {
            OutputReceived?.Invoke("未找到 aria2c，正在下载 aria2 1.37.0 …");
            var url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip";
            using var http = new HttpClient();
            var zipBytes = await http.GetByteArrayAsync(url);
            var zipPath = Path.Combine(dir, "aria2.zip");
            await File.WriteAllBytesAsync(zipPath, zipBytes);

            // 解压出 aria2c.exe
            var sevenZip = new SevenZipService();
            await sevenZip.LocateAsync();
            // 用 7z 解压 zip
            await ExtractZipAsync(zipPath, dir);
        }

        if (!File.Exists(fallback))
        {
            throw new InvalidOperationException("aria2c 下载失败，无法定位。");
        }
        return _resolvedPath = fallback;
    }

    /// <summary>
    /// 下载单个文件（多线程 + 断点续传）。
    /// </summary>
    /// <param name="url">下载地址</param>
    /// <param name="outputDirectory">输出目录</param>
    /// <param name="fileName">输出文件名（null 时由 URL 推断）</param>
    /// <param name="connections">每文件连接数</param>
    public async Task DownloadAsync(
        string url,
        string outputDirectory,
        string? fileName = null,
        int connections = 16,
        CancellationToken ct = default)
        => await DownloadWithMirrorsAsync(url, outputDirectory, null, fileName, connections, ct);

    /// <summary>
    /// 使用用户指定的单个镜像下载（不自动降级，失败即报错）。
    /// </summary>
    public async Task DownloadWithMirrorAsync(
        DownloadMirror mirror,
        string url,
        string outputDirectory,
        string? fileName = null,
        int connections = 16,
        CancellationToken ct = default)
    {
        var exe = await LocateAsync();
        Directory.CreateDirectory(outputDirectory);

        // 取消时抛错，由调用方决定"暂停"或"停止"
        ct.ThrowIfCancellationRequested();

        var outName = fileName ?? Path.GetFileName(new Uri(url).AbsolutePath);
        if (string.IsNullOrEmpty(outName))
        {
            outName = "download";
        }

        var resolved = mirror.Resolve(url);
        await RunAria2Async(exe, resolved, outputDirectory, outName, connections, ct);

        // 校验文件真实存在且非空
        var full = Path.Combine(outputDirectory, outName);
        if (!File.Exists(full) || new FileInfo(full).Length == 0)
        {
            throw new InvalidOperationException($"文件未成功下载（0 字节或不存在）：{mirror.Name}");
        }

        ProgressChanged?.Invoke(outName, 100);
    }

    /// <summary>
    /// 带镜像策略下载：按镜像顺序逐个尝试，失败自动降级到下一个。
    /// 每个镜像的 aria2c 进程失败（非零码）时切换镜像重试。
    /// </summary>
    /// <param name="mirrors">候选镜像顺序（null = 仅官方直连）</param>
    /// <param name="onMirrorSwitched">切换镜像时的回调（用于 UI 提示）</param>
    public async Task DownloadWithMirrorsAsync(
        string url,
        string outputDirectory,
        IReadOnlyList<DownloadMirror>? mirrors,
        string? fileName = null,
        int connections = 16,
        CancellationToken ct = default,
        Action<DownloadMirror>? onMirrorSwitched = null)
    {
        var exe = await LocateAsync();
        Directory.CreateDirectory(outputDirectory);

        var outName = fileName ?? Path.GetFileName(new Uri(url).AbsolutePath);
        if (string.IsNullOrEmpty(outName))
        {
            outName = "download";
        }

        var candidateMirrors = mirrors is { Count: > 0 } ? mirrors : [new DownloadMirror("official", "官方", null)];

        Exception? lastError = null;
        foreach (var mirror in candidateMirrors)
        {
            ct.ThrowIfCancellationRequested();
            var resolved = mirror.Resolve(url);

            try
            {
                await RunAria2Async(exe, resolved, outputDirectory, outName, connections, ct);
                // 校验文件真实存在且非空（防止 0 字节残留被误判成功）
                var full = Path.Combine(outputDirectory, outName);
                if (!File.Exists(full) || new FileInfo(full).Length == 0)
                {
                    throw new InvalidOperationException($"文件未成功下载（0 字节或不存在）：{mirror.Name}");
                }
                ProgressChanged?.Invoke(outName, 100);
                return;
            }
            catch (Exception ex)
            {
                lastError = ex;
                onMirrorSwitched?.Invoke(mirror);
                // 清理 0 字节残留，避免影响下一个镜像的 -c 续传
                try
                {
                    var full = Path.Combine(outputDirectory, outName);
                    if (File.Exists(full) && new FileInfo(full).Length == 0)
                    {
                        File.Delete(full);
                    }
                }
                catch { }
                // 继续下一个镜像
            }
        }

        throw new InvalidOperationException(
            $"下载失败：{outName}（已尝试 {candidateMirrors.Count} 个镜像）{Environment.NewLine}{lastError?.Message}");
    }

    /// <summary>执行单个 aria2c 下载进程</summary>
    private async Task RunAria2Async(
        string exe,
        string resolvedUrl,
        string outputDirectory,
        string outName,
        int connections,
        CancellationToken ct)
    {
        var psi = new ProcessStartInfo
        {
            FileName = exe,
            // 注意：目录以反斜杠结尾时，紧贴闭合引号会变成 \" 转义引号，导致整条命令解析错乱。
            // 因此去掉结尾反斜杠（--dir 不依赖尾斜杠）。
            Arguments = $"-x {connections} -s {connections} -k 1M -c --dir=\"{outputDirectory.TrimEnd('\\')}\" --out=\"{outName}\" --summary-interval=1 --console-log-level=warn --file-allocation=none --auto-file-renaming=false \"{resolvedUrl}\"",
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        using var proc = Process.Start(psi)
            ?? throw new InvalidOperationException("无法启动 aria2c。");

        // 取消时强制结束 aria2c 进程（保留 .aria2 控制文件，支持断点续传）
        using var cancelReg = ct.Register(() =>
        {
            try
            {
                if (!proc.HasExited)
                {
                    proc.Kill(entireProcessTree: true);
                }
            }
            catch { }
        });

        var outputLines = new System.Collections.Concurrent.ConcurrentQueue<string>();
        void Collect(string line) => outputLines.Enqueue(line);

        OutputReceived += Collect;
        try
        {
            var readTasks = new[]
            {
                ReadStreamAsync(proc.StandardOutput, outName, ct),
                ReadStreamAsync(proc.StandardError, outName, ct),
            };
            await Task.WhenAll(readTasks);
            await proc.WaitForExitAsync(ct);
        }
        finally
        {
            OutputReceived -= Collect;
        }

        if (proc.ExitCode != 0 && proc.ExitCode != 1)
        {
            // aria2c 退出码 1 = 部分完成（如已存在），3 = 未找到元数据等
            throw new InvalidOperationException($"aria2c 下载失败（退出码 {proc.ExitCode}）：{resolvedUrl}");
        }

        // 退出码 1：若目标文件缺失/0 字节（例如源已删除或返回异常页），抛错并附 aria2 输出便于诊断
        var fullPath = Path.Combine(outputDirectory, outName);
        var hasFile = File.Exists(fullPath) && new FileInfo(fullPath).Length > 0;
        if (proc.ExitCode == 1 && !hasFile)
        {
            var tail = string.Join(Environment.NewLine, outputLines.TakeLast(8));
            throw new InvalidOperationException(
                $"aria2c 退出码 1 但未产生有效文件：{resolvedUrl}{Environment.NewLine}{tail}");
        }
    }

    /// <summary>读取输出流并解析进度</summary>
    private async Task ReadStreamAsync(StreamReader reader, string fileName, CancellationToken ct)
    {
        while (true)
        {
            var line = await reader.ReadLineAsync(ct);
            if (line is null)
            {
                break;
            }

            OutputReceived?.Invoke(line);
            var m = PercentRegex().Match(line);
            if (m.Success && int.TryParse(m.Groups[1].Value, out var pct))
            {
                ProgressChanged?.Invoke(fileName, Math.Clamp(pct, 0, 100));
            }
        }
    }

    /// <summary>匹配 aria2c 摘要行中的百分比，如 (45%)</summary>
    [GeneratedRegex(@"\((\d{1,3})%\)")]
    private static partial Regex PercentRegex();

    private static string? FindInPath(string exeName)
    {
        var pathEnv = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
        foreach (var dir in pathEnv.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            try
            {
                var candidate = Path.Combine(dir.Trim('"'), exeName);
                if (File.Exists(candidate))
                {
                    return candidate;
                }
            }
            catch { }
        }
        return null;
    }

    private static string? FindUpwards(string subDir, string fileName, int maxLevels)
    {
        var dir = AppContext.BaseDirectory;
        for (int i = 0; i <= maxLevels; i++)
        {
            var candidate = Path.Combine(dir, subDir, fileName);
            if (File.Exists(candidate))
            {
                return candidate;
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

    /// <summary>用 7z 解压 zip（7z 支持 zip 格式）</summary>
    private static async Task ExtractZipAsync(string zipPath, string destDir)
    {
        var sevenZip = new SevenZipService();
        await sevenZip.LocateAsync();
        var psi = new ProcessStartInfo
        {
            FileName = sevenZip.ResolvedPath!,
            Arguments = $"x -y -o\"{destDir}\" \"{zipPath}\"",
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        using var proc = Process.Start(psi);
        if (proc is not null)
        {
            await proc.WaitForExitAsync();
        }

        // 解压后找 aria2c.exe（可能在子目录）
        if (!File.Exists(Path.Combine(destDir, "aria2c.exe")))
        {
            var found = Directory.EnumerateFiles(destDir, "aria2c.exe", SearchOption.AllDirectories).FirstOrDefault();
            if (found is not null)
            {
                File.Copy(found, Path.Combine(destDir, "aria2c.exe"), overwrite: true);
            }
        }
    }
}
