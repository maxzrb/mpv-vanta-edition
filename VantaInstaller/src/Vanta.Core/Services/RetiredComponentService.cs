using System.Text.Json;

namespace Vanta.Core.Services;

/// <summary>按新版配置标记隔离旧组件；用户文件与历史备份均保留。</summary>
public static class RetiredComponentService
{
    public static void Quarantine(string installDirectory, Action<string> log)
    {
        var root = Path.TrimEndingDirectorySeparator(Path.GetFullPath(installDirectory));
        var marker = Path.Combine(root, "portable_config", "components.lock.json");
        if (!File.Exists(marker)) return;
        using var document = JsonDocument.Parse(File.ReadAllText(marker, System.Text.Encoding.UTF8));
        if (!document.RootElement.TryGetProperty("retired_components", out var retired) ||
            !retired.EnumerateArray().Any(item => item.GetString() == "uosc_danmaku")) return;
        var relativePaths = new[]
        {
            Path.Combine("portable_config", "scripts", "uosc_danmaku"),
            Path.Combine("portable_config", "script-opts", "uosc_danmaku.conf"),
        };
        var backup = Path.Combine(root, "backup", "retired-components-" + DateTime.Now.ToString("yyyyMMdd-HHmmss-fffffff"));
        foreach (var relative in relativePaths)
        {
            var source = Path.GetFullPath(Path.Combine(root, relative));
            var prefix = Path.EndsInDirectorySeparator(root) ? root : root + Path.DirectorySeparatorChar;
            if (!source.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                throw new IOException("旧组件路径越出安装目录。");
            // 同样检查父目录，避免通过 portable_config 等目录链接越界移动。
            for (var parent = new DirectoryInfo(Path.GetDirectoryName(source)!);
                 parent.FullName.Length > root.Length; parent = parent.Parent!)
            {
                if (parent.Exists && (parent.Attributes & FileAttributes.ReparsePoint) != 0)
                    throw new IOException("旧组件父目录是链接，请手动检查：" + relative);
            }
            if (!File.Exists(source) && !Directory.Exists(source)) continue;
            // 不跟随用户创建的链接，避免触及安装目录外的文件。
            if ((File.GetAttributes(source) & FileAttributes.ReparsePoint) != 0)
                throw new IOException("旧组件路径是链接，请手动检查：" + relative);
            var target = Path.Combine(backup, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            if (Directory.Exists(source)) Directory.Move(source, target);
            else File.Move(source, target);
            log("已隔离旧组件（可在 backup 恢复）：" + relative);
        }
    }
}
