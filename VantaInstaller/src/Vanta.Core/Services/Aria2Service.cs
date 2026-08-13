using System.Diagnostics;
using System.Globalization;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace Vanta.Core.Services;

/// <summary>
/// Aria2 Next 下载服务：释放内置引擎、多线程下载、进度解析、断点续传。
/// </summary>
public sealed partial class Aria2Service
{
    public const string EngineVersion = "2.5.5";
    private const string EngineResourceName = "Vanta.Core.Assets.aria2-next.exe";
    private const string LicenseResourceName = "Vanta.Core.Assets.aria2-next-COPYING.txt";
    private const string EngineSha256 = "554F2F81CA53731DC9E01710CFB16081A34759F3276FF16EB4B12656C1B6E5B9";
    private readonly string? _explicitPath;
    private string? _resolvedPath;

    /// <summary>aria2c 输出行</summary>
    public event Action<string>? OutputReceived;

    /// <summary>下载进度（文件名，0~100）</summary>
    public event Action<string, int>? ProgressChanged;

    /// <summary>实时下载速度（文件名，字节/秒）</summary>
    public event Action<string, double>? SpeedChanged;

    public Aria2Service(string? explicitPath = null) => _explicitPath = explicitPath;

    /// <summary>已解析的 aria2c 路径</summary>
    public string? ResolvedPath => _resolvedPath;

    /// <summary>是否已就绪（定位成功）</summary>
    public bool IsReady => _resolvedPath is not null;

    /// <summary>
    /// 定位 Aria2 Next：显式路径优先，否则从安装器内置资源释放到版本化缓存。
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

        var dir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "VantaInstaller",
            "engines",
            $"aria2-next-{EngineVersion}");
        Directory.CreateDirectory(dir);
        var enginePath = Path.Combine(dir, "aria2-next.exe");
        if (!File.Exists(enginePath) || !HasExpectedHash(enginePath))
        {
            OutputReceived?.Invoke($"正在准备 Aria2 Next {EngineVersion} 下载引擎…");
            await ExtractResourceAsync(EngineResourceName, enginePath);
        }

        if (!File.Exists(enginePath) || !HasExpectedHash(enginePath))
        {
            throw new InvalidOperationException("Aria2 Next 下载引擎释放或校验失败。");
        }

        var licensePath = Path.Combine(dir, "COPYING.txt");
        if (!File.Exists(licensePath))
        {
            await ExtractResourceAsync(LicenseResourceName, licensePath);
        }
        return _resolvedPath = enginePath;
    }

    private static async Task ExtractResourceAsync(string resourceName, string destination)
    {
        await using var resource = Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName)
            ?? throw new InvalidOperationException($"安装器内缺少资源：{resourceName}");
        var temporary = $"{destination}.{Environment.ProcessId}.tmp";
        await using (var output = new FileStream(temporary, FileMode.Create, FileAccess.Write, FileShare.None))
        {
            await resource.CopyToAsync(output);
        }
        File.Move(temporary, destination, overwrite: true);
    }

    private static bool HasExpectedHash(string path)
    {
        try
        {
            using var stream = File.OpenRead(path);
            return Convert.ToHexString(SHA256.HashData(stream)) == EngineSha256;
        }
        catch
        {
            return false;
        }
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
        int connections = 64,
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
        int connections = 64,
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
        int connections = 64,
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
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        // 对齐 Motrix Next 的 64 分片/64 单服务器连接默认值。ArgumentList 避免空格、引号和 URL
        // 特殊字符再次经过命令行字符串解析，修复安装目录或资产名较复杂时的启动失败。
        string[] arguments =
        [
            "--no-conf",
            $"--max-connection-per-server={connections}",
            $"--split={connections}",
            "--min-split-size=1M",
            "--continue=true",
            "--allow-piece-length-change=true",
            "--enable-http-keep-alive=true",
            "--max-tries=5",
            "--retry-wait=2",
            "--connect-timeout=10",
            "--timeout=30",
            // Motrix Next 默认使用 trunc；Windows 下创建大文件开销低于预分配，也比 none 更稳定。
            "--file-allocation=trunc",
            "--auto-file-renaming=false",
            $"--dir={outputDirectory.TrimEnd('\\')}",
            $"--out={outName}",
            "--summary-interval=1",
            "--console-log-level=notice",
            "--show-console-readout=true",
            "--enable-color=false",
            "--human-readable=true",
            "--download-result=hide",
            resolvedUrl,
        ];
        foreach (var argument in arguments)
        {
            psi.ArgumentList.Add(argument);
        }

        using var proc = Process.Start(psi)
            ?? throw new InvalidOperationException("无法启动 Aria2 Next。");

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
        void Collect(string line)
        {
            outputLines.Enqueue(line);
            while (outputLines.Count > 20)
            {
                outputLines.TryDequeue(out _);
            }
        }

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
            SpeedChanged?.Invoke(outName, 0);
        }
        finally
        {
            OutputReceived -= Collect;
        }

        if (proc.ExitCode != 0)
        {
            var tail = string.Join(Environment.NewLine, outputLines.TakeLast(8));
            throw new InvalidOperationException(
                $"Aria2 Next 下载失败（退出码 {proc.ExitCode}）：{resolvedUrl}{Environment.NewLine}{tail}");
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

            var speed = ParseSpeed(line);
            if (speed.HasValue)
            {
                SpeedChanged?.Invoke(fileName, speed.Value);
            }
        }
    }

    /// <summary>匹配 aria2c 摘要行中的百分比，如 (45%)</summary>
    [GeneratedRegex(@"\((\d{1,3})%\)")]
    private static partial Regex PercentRegex();

    /// <summary>匹配 aria2 摘要中的 DL:12MiB 速度字段。</summary>
    [GeneratedRegex(@"DL:\s*(?<value>\d+(?:[\.,]\d+)?)\s*(?<unit>B|KiB|MiB|GiB|TiB|KB|MB|GB|TB)", RegexOptions.IgnoreCase)]
    private static partial Regex Aria2SpeedRegex();

    /// <summary>匹配部分 aria2 输出中的 12MiB/s 速度字段。</summary>
    [GeneratedRegex(@"(?<![A-Za-z0-9])(?<value>\d+(?:[\.,]\d+)?)\s*(?<unit>B|KiB|MiB|GiB|TiB|KB|MB|GB|TB)\s*/\s*s", RegexOptions.IgnoreCase)]
    private static partial Regex ExplicitSpeedRegex();

    private static double? ParseSpeed(string line)
    {
        var match = Aria2SpeedRegex().Match(line);
        if (!match.Success)
        {
            match = ExplicitSpeedRegex().Match(line);
        }

        if (!match.Success || !double.TryParse(
                match.Groups["value"].Value.Replace(',', '.'),
                NumberStyles.Float,
                CultureInfo.InvariantCulture,
                out var value))
        {
            return null;
        }

        var unit = match.Groups["unit"].Value.ToUpperInvariant();
        var multiplier = unit switch
        {
            "B" => 1d,
            "KB" => 1_000d,
            "MB" => 1_000_000d,
            "GB" => 1_000_000_000d,
            "TB" => 1_000_000_000_000d,
            "KIB" => 1024d,
            "MIB" => 1024d * 1024d,
            "GIB" => 1024d * 1024d * 1024d,
            "TIB" => 1024d * 1024d * 1024d * 1024d,
            _ => 0d,
        };

        return multiplier > 0 ? value * multiplier : null;
    }

    /// <summary>格式化实时下载速度。</summary>
    public static string FormatSpeed(double bytesPerSecond)
    {
        if (bytesPerSecond <= 0)
        {
            return "—";
        }

        var value = bytesPerSecond;
        var units = new[] { "B/s", "KiB/s", "MiB/s", "GiB/s", "TiB/s" };
        var index = 0;
        while (value >= 1024 && index < units.Length - 1)
        {
            value /= 1024;
            index++;
        }

        return index == 0 ? $"{value:0} {units[index]}" : $"{value:0.0} {units[index]}";
    }

}
