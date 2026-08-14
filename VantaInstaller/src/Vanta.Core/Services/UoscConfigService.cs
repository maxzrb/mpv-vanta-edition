using System.Globalization;
using System.Text;

namespace Vanta.Core.Services;

/// <summary>
/// uosc 配置服务：读写 portable_config/script-opts/uosc.conf 的可调项。
/// 只更新目标键的值，保留全部注释与行顺序；文件缺失时按默认值新建。
/// </summary>
public static class UoscConfigService
{
    private const string MenuSubmenuDelayKey = "menu_submenu_delay";

    /// <summary>默认子菜单 hover 延迟（秒）：0 更跟手，调大避免快速扫过父菜单时误弹出。</summary>
    public const double DefaultMenuSubmenuDelay = 0.1;

    public static string GetConfigPath(string configDirectory) =>
        Path.Combine(configDirectory, "script-opts", "uosc.conf");

    /// <summary>读取 uosc.conf 的 menu_submenu_delay；文件缺失或解析失败返回默认值。</summary>
    public static double LoadMenuSubmenuDelay(string configDirectory)
    {
        var path = GetConfigPath(configDirectory);
        if (!File.Exists(path))
        {
            return DefaultMenuSubmenuDelay;
        }

        foreach (var raw in File.ReadAllLines(path, Encoding.UTF8))
        {
            var line = raw.Trim();
            if (line.Length == 0 || line.StartsWith('#'))
            {
                continue;
            }

            var eq = line.IndexOf('=');
            if (eq <= 0)
            {
                continue;
            }

            var key = line[..eq].Trim();
            var value = line[(eq + 1)..].Trim();
            if (value.Length >= 2 && value[0] == '"' && value[^1] == '"')
            {
                value = value[1..^1];
            }

            if (string.Equals(key, MenuSubmenuDelayKey, StringComparison.OrdinalIgnoreCase)
                && double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var delay)
                && delay >= 0)
            {
                return delay;
            }
        }

        return DefaultMenuSubmenuDelay;
    }

    /// <summary>
    /// 写回 uosc.conf 的 menu_submenu_delay：保留注释与行序，只更新目标键；缺失键追加到文件末尾。
    /// 使用 UTF-8、LF 行尾（与仓库配置一致）。
    /// </summary>
    public static void SaveMenuSubmenuDelay(string configDirectory, double delay)
    {
        var path = GetConfigPath(configDirectory);
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir))
        {
            Directory.CreateDirectory(dir);
        }

        var lines = File.Exists(path)
            ? File.ReadAllLines(path, Encoding.UTF8).ToList()
            : new List<string> { "# uosc 配置" };

        SetValue(lines, MenuSubmenuDelayKey, FormatDelay(delay));

        File.WriteAllText(path, string.Join('\n', lines) + "\n", Encoding.UTF8);
    }

    private static void SetValue(List<string> lines, string key, string value)
    {
        for (int i = 0; i < lines.Count; i++)
        {
            var trimmed = lines[i].TrimStart();
            if (trimmed.Length == 0 || trimmed.StartsWith('#'))
            {
                continue;
            }

            var eq = trimmed.IndexOf('=');
            if (eq <= 0)
            {
                continue;
            }

            if (string.Equals(trimmed[..eq].Trim(), key, StringComparison.OrdinalIgnoreCase))
            {
                lines[i] = $"{key}={value}";
                return;
            }
        }

        lines.Add($"{key}={value}");
    }

    private static string FormatDelay(double value) =>
        Math.Abs(value - Math.Round(value)) < 0.001
            ? ((int)Math.Round(value)).ToString(CultureInfo.InvariantCulture)
            : value.ToString("0.0#", CultureInfo.InvariantCulture);
}
