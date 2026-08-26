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
    private const string TimelineBufferKey = "timeline_buffer";
    private const string TimelineBufferOpacityKey = "timeline_buffer_opacity";

    /// <summary>默认子菜单 hover 延迟（秒）：0 更跟手，调大避免快速扫过父菜单时误弹出。</summary>
    public const double DefaultMenuSubmenuDelay = 0.1;
    public const bool DefaultTimelineBuffer = true;
    public const double DefaultTimelineBufferOpacity = 0.18;

    public static string GetConfigPath(string configDirectory) =>
        Path.Combine(configDirectory, "script-opts", "uosc.conf");

    /// <summary>读取 VantaInstaller 暴露的 uosc 设置；缺失或解析失败的项使用默认值。</summary>
    public static UoscSettings Load(string configDirectory)
    {
        var path = GetConfigPath(configDirectory);
        if (!File.Exists(path))
        {
            return new UoscSettings();
        }

        var settings = new UoscSettings();
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
                && TryParseDouble(value, out var delay) && delay >= 0)
            {
                settings.MenuSubmenuDelay = delay;
            }
            else if (string.Equals(key, TimelineBufferKey, StringComparison.OrdinalIgnoreCase)
                && TryParseBoolean(value, out var enabled))
            {
                settings.TimelineBuffer = enabled;
            }
            else if (string.Equals(key, TimelineBufferOpacityKey, StringComparison.OrdinalIgnoreCase)
                && TryParseDouble(value, out var opacity) && opacity is >= 0 and <= 1)
            {
                settings.TimelineBufferOpacity = opacity;
            }
        }

        return settings;
    }

    public static double LoadMenuSubmenuDelay(string configDirectory) => Load(configDirectory).MenuSubmenuDelay;

    /// <summary>
    /// 写回 uosc.conf 的 menu_submenu_delay：保留注释与行序，只更新目标键；缺失键追加到文件末尾。
    /// 使用 UTF-8、LF 行尾（与仓库配置一致）。
    /// </summary>
    public static void Save(string configDirectory, UoscSettings settings)
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

        SetValue(lines, MenuSubmenuDelayKey, FormatNumber(settings.MenuSubmenuDelay));
        SetValue(lines, TimelineBufferKey, settings.TimelineBuffer ? "yes" : "no");
        SetValue(lines, TimelineBufferOpacityKey, FormatNumber(Math.Clamp(settings.TimelineBufferOpacity, 0, 1)));

        File.WriteAllText(path, string.Join('\n', lines) + "\n", Encoding.UTF8);
    }

    public static void SaveMenuSubmenuDelay(string configDirectory, double delay)
    {
        var settings = Load(configDirectory);
        settings.MenuSubmenuDelay = delay;
        Save(configDirectory, settings);
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

    private static bool TryParseDouble(string value, out double result) =>
        double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out result);

    private static bool TryParseBoolean(string value, out bool result)
    {
        if (string.Equals(value, "yes", StringComparison.OrdinalIgnoreCase)
            || string.Equals(value, "true", StringComparison.OrdinalIgnoreCase))
        {
            result = true;
            return true;
        }
        if (string.Equals(value, "no", StringComparison.OrdinalIgnoreCase)
            || string.Equals(value, "false", StringComparison.OrdinalIgnoreCase))
        {
            result = false;
            return true;
        }
        result = false;
        return false;
    }

    private static string FormatNumber(double value) =>
        Math.Abs(value - Math.Round(value)) < 0.001
            ? ((int)Math.Round(value)).ToString(CultureInfo.InvariantCulture)
            : value.ToString("0.0##", CultureInfo.InvariantCulture);
}

public sealed class UoscSettings
{
    public double MenuSubmenuDelay { get; set; } = UoscConfigService.DefaultMenuSubmenuDelay;
    public bool TimelineBuffer { get; set; } = UoscConfigService.DefaultTimelineBuffer;
    public double TimelineBufferOpacity { get; set; } = UoscConfigService.DefaultTimelineBufferOpacity;
}
