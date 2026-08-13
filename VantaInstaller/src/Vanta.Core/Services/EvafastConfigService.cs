using System.Globalization;
using System.Text;

namespace Vanta.Core.Services;

/// <summary>方向键快进（evafast）可调设置</summary>
public sealed class EvafastSettings
{
    /// <summary>无字幕时的快进倍速上限（speed_cap）</summary>
    public double SpeedCap { get; set; } = 3;

    /// <summary>有字幕时的快进倍速上限（subs_speed_cap）</summary>
    public double SubsSpeedCap { get; set; } = 1.5;

    /// <summary>是否启用"显示字幕时降低倍速上限"（subs_limit）</summary>
    public bool SubsLimit { get; set; } = true;
}

/// <summary>
/// evafast（方向键快进）配置服务：读写 portable_config/script-opts/evafast.conf。
/// 只更新目标键的值，保留全部注释与行顺序；文件缺失时按默认值新建。
/// </summary>
public static class EvafastConfigService
{
    private const string SpeedCapKey = "speed_cap";
    private const string SubsSpeedCapKey = "subs_speed_cap";
    private const string SubsLimitKey = "subs_limit";

    public static string GetConfigPath(string configDirectory) =>
        Path.Combine(configDirectory, "script-opts", "evafast.conf");

    /// <summary>判断两组设置是否一致（用于跟踪未保存修改）</summary>
    public static bool SameValues(
        double speedCap, double subsSpeedCap, bool subsLimit,
        double otherSpeedCap, double otherSubsSpeedCap, bool otherSubsLimit) =>
        Math.Abs(speedCap - otherSpeedCap) < 0.001
        && Math.Abs(subsSpeedCap - otherSubsSpeedCap) < 0.001
        && subsLimit == otherSubsLimit;

    /// <summary>读取 evafast.conf 设置；文件不存在时返回默认值。</summary>
    public static EvafastSettings Load(string configDirectory)
    {
        var settings = new EvafastSettings();
        var path = GetConfigPath(configDirectory);
        if (!File.Exists(path))
        {
            return settings;
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

            if (string.Equals(key, SpeedCapKey, StringComparison.OrdinalIgnoreCase)
                && double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var speedCap)
                && speedCap > 0)
            {
                settings.SpeedCap = speedCap;
            }
            else if (string.Equals(key, SubsSpeedCapKey, StringComparison.OrdinalIgnoreCase)
                && double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var subsCap)
                && subsCap > 0)
            {
                settings.SubsSpeedCap = subsCap;
            }
            else if (string.Equals(key, SubsLimitKey, StringComparison.OrdinalIgnoreCase))
            {
                settings.SubsLimit = ParseBool(value, settings.SubsLimit);
            }
        }

        return settings;
    }

    /// <summary>
    /// 写回 evafast.conf：保留注释与行序，只更新目标键的值；缺失键追加到文件末尾。
    /// 使用 UTF-8、LF 行尾（与仓库配置一致）。
    /// </summary>
    public static void Save(string configDirectory, EvafastSettings settings)
    {
        var path = GetConfigPath(configDirectory);
        var lines = File.Exists(path)
            ? File.ReadAllLines(path, Encoding.UTF8).ToList()
            : new List<string>
            {
                "# evafast（方向键快进）配置",
                "# 无字幕时的快进倍速上限",
                "# 有字幕时的快进倍速上限（subs_limit=yes 时生效）",
                "# 是否启用字幕限速",
            };

        SetValue(lines, SpeedCapKey, FormatSpeed(settings.SpeedCap));
        SetValue(lines, SubsSpeedCapKey, FormatSpeed(settings.SubsSpeedCap));
        SetValue(lines, SubsLimitKey, settings.SubsLimit ? "yes" : "no");

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

    private static string FormatSpeed(double value) =>
        Math.Abs(value - Math.Round(value)) < 0.001
            ? ((int)Math.Round(value)).ToString(CultureInfo.InvariantCulture)
            : value.ToString("0.0", CultureInfo.InvariantCulture);

    private static bool ParseBool(string value, bool fallback) =>
        string.Equals(value, "yes", StringComparison.OrdinalIgnoreCase)
            ? true
            : string.Equals(value, "no", StringComparison.OrdinalIgnoreCase)
                ? false
                : fallback;
}
