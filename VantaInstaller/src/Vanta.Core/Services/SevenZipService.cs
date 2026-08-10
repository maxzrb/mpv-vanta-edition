using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace Vanta.Core.Services;

/// <summary>
/// 7-Zip 定位与解压服务。
/// 定位顺序：显式路径 → PATH → 注册表 → 仓库自带 7z\7z.exe → 下载 7zr.exe
/// </summary>
public sealed partial class SevenZipService
{
    private readonly string? _explicitPath;
    private string? _resolvedPath;

    /// <summary>7z 原始输出行</summary>
    public event Action<string>? OutputReceived;

    /// <summary>解压进度（0~100）</summary>
    public event Action<int>? ProgressChanged;

    public SevenZipService(string? explicitPath = null) => _explicitPath = explicitPath;

    /// <summary>已解析的 7z 可执行文件路径</summary>
    public string? ResolvedPath => _resolvedPath;

    /// <summary>
    /// 定位 7z.exe（必要时下载 7zr.exe 兜底）。
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
        var fromPath = FindInPath("7z.exe");
        if (fromPath is not null)
        {
            return _resolvedPath = fromPath;
        }

        // 3. 注册表
        var regPath = FindInRegistry();
        if (regPath is not null)
        {
            return _resolvedPath = regPath;
        }

        // 4. 仓库自带 7z\7z.exe（向上查找）
        var bundled = FindUpwards("7z", "7z.exe", 4);
        if (bundled is not null)
        {
            return _resolvedPath = bundled;
        }

        // 5. 下载 7zr.exe 到临时目录（7-Zip 精简版，支持 .7z 格式）
        var fallback = Path.Combine(Path.GetTempPath(), "vanta-7zr.exe");
        if (!File.Exists(fallback))
        {
            OutputReceived?.Invoke("未找到 7z.exe，正在下载 7zr.exe …");
            using var http = new HttpClient();
            var data = await http.GetByteArrayAsync("https://www.7-zip.org/a/7zr.exe");
            await File.WriteAllBytesAsync(fallback, data);
        }

        return _resolvedPath = fallback;
    }

    /// <summary>
    /// 解压归档到目标目录。分卷只需传入 .001 作为入口。
    /// </summary>
    public async Task ExtractAsync(string archivePath, string targetDirectory, CancellationToken ct = default)
    {
        var exe = await LocateAsync();
        Directory.CreateDirectory(targetDirectory);

        var psi = new ProcessStartInfo
        {
            FileName = exe,
            // x 解压 -y 全部覆盖 -bsp1 强制进度输出到 stdout（重定向时默认关闭进度）
            Arguments = $"x -y -bsp1 -o\"{targetDirectory}\" \"{archivePath}\"",
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        using var proc = Process.Start(psi)
            ?? throw new InvalidOperationException("无法启动 7z 进程。");

        // 7z 进度输出在重定向下默认关闭，需 -bsp1 强制；行格式 "NN% ..."（\n 结尾）
        // 或旧版 \r 覆盖。改用逐块读取 + 手动按 \r/\n 拆行，实时解析 NN% 并转发输出。
        var progress = new ProgressTextParser();
        await ReadStreamIncrementalAsync(proc.StandardOutput, ct, (line, isProgress, pct) =>
        {
            if (isProgress)
            {
                ProgressChanged?.Invoke(pct);
            }
            else if (!string.IsNullOrWhiteSpace(line))
            {
                OutputReceived?.Invoke(line);
            }
        }, progress);

        var errorText = await proc.StandardError.ReadToEndAsync(ct);
        await proc.WaitForExitAsync(ct);

        if (proc.ExitCode != 0)
        {
            throw new InvalidOperationException(
                $"7z 解压失败（退出码 {proc.ExitCode}）：{errorText.Trim()}");
        }
    }

    /// <summary>测试归档完整性（7z t）</summary>
    public async Task TestAsync(string archivePath, CancellationToken ct = default)
    {
        var exe = await LocateAsync();
        var psi = new ProcessStartInfo
        {
            FileName = exe,
            Arguments = $"t \"{archivePath}\"",
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        using var proc = Process.Start(psi)
            ?? throw new InvalidOperationException("无法启动 7z 进程。");

        var errorText = await proc.StandardError.ReadToEndAsync(ct);
        await proc.WaitForExitAsync(ct);

        if (proc.ExitCode != 0)
        {
            throw new InvalidOperationException($"7z 完整性测试失败（退出码 {proc.ExitCode}）：{errorText.Trim()}");
        }
    }

    [GeneratedRegex(@"^\s*(\d{1,3})%")]
    private static partial Regex PercentRegex();

    /// <summary>
    /// 增量读取进程输出流，按 \r/\n 拆行回调。
    /// 7z 的解压进度是同一行用 \r 反复刷新（如 "40% - file"），
    /// 拆行时遇到 \r 视为进度更新（行首 NN%），\n 视为完整日志行。
    /// </summary>
    private static async Task ReadStreamIncrementalAsync(
        StreamReader reader,
        CancellationToken ct,
        Action<string, bool, int> onLine,
        ProgressTextParser parser)
    {
        var buffer = new char[4096];
        var pending = new StringBuilder();

        while (true)
        {
            var read = await reader.ReadAsync(buffer, ct);
            if (read <= 0)
            {
                break;
            }

            for (int i = 0; i < read; i++)
            {
                var c = buffer[i];
                if (c == '\n')
                {
                    // 完整行（换行结尾）
                    FlushLine(pending, onLine, parser, isCarriageReturnLine: false);
                }
                else if (c == '\r')
                {
                    // 回车：7z 进度刷新标记，把当前累积内容作为进度行处理
                    FlushLine(pending, onLine, parser, isCarriageReturnLine: true);
                }
                else
                {
                    pending.Append(c);
                }
            }
        }

        // 尾部残留（无终止符）
        if (pending.Length > 0)
        {
            FlushLine(pending, onLine, parser, isCarriageReturnLine: false);
        }
    }

    private static void FlushLine(
        StringBuilder pending,
        Action<string, bool, int> onLine,
        ProgressTextParser parser,
        bool isCarriageReturnLine)
    {
        var text = pending.ToString().Trim();
        pending.Clear();

        // 无论 \r 还是 \n 结尾，只要行首是 NN% 一律按进度处理（避免进度行刷进日志）
        if (parser.TryParse(text, out var pct))
        {
            onLine(text, true, pct);
            return;
        }

        // 只有 \r 结尾且非进度：可能是不完整段，跳过（避免半行噪音）
        if (isCarriageReturnLine)
        {
            return;
        }

        onLine(text, false, 0);
    }

    /// <summary>解析 7z 进度文本（如 "40% 12 file" 或 "40% - 文件"）</summary>
    private sealed class ProgressTextParser
    {
        public bool TryParse(string text, out int percent)
        {
            percent = 0;
            if (string.IsNullOrWhiteSpace(text))
            {
                return false;
            }

            var m = PercentRegex().Match(text);
            if (m.Success)
            {
                percent = int.Parse(m.Groups[1].Value);
                return true;
            }
            return false;
        }
    }

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
            catch
            {
                // 忽略无效路径
            }
        }
        return null;
    }

    private static string? FindInRegistry()
    {
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(
                @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\7-Zip");
            var loc = key?.GetValue("InstallLocation") as string;
            if (!string.IsNullOrEmpty(loc))
            {
                var candidate = Path.Combine(loc, "7z.exe");
                if (File.Exists(candidate))
                {
                    return candidate;
                }
            }
        }
        catch
        {
            // 注册表读取失败忽略
        }
        return null;
    }

    /// <summary>从当前目录向上查找相对路径（用于定位仓库自带 7z）</summary>
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
}
