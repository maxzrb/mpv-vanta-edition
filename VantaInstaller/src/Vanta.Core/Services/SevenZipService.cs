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
            // x 解压 -y 全部覆盖 -o 输出目录（-o 后无空格）
            Arguments = $"x -y -o\"{targetDirectory}\" \"{archivePath}\"",
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };

        using var proc = Process.Start(psi)
            ?? throw new InvalidOperationException("无法启动 7z 进程。");

        // 逐行读取输出，解析进度（行首为 "NN%"）
        while (true)
        {
            var line = await proc.StandardOutput.ReadLineAsync(ct);
            if (line is null)
            {
                break;
            }
            if (string.IsNullOrWhiteSpace(line))
            {
                continue;
            }

            OutputReceived?.Invoke(line);
            var m = PercentRegex().Match(line);
            if (m.Success)
            {
                ProgressChanged?.Invoke(int.Parse(m.Groups[1].Value));
            }
        }

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
