using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// uosc 主题服务：VantaInstaller 与 Lua 共用同一份 JSON 色板，只向 uosc.conf 写入 theme ID。
/// </summary>
public static partial class UoscThemeService
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    public static string GetRegistryPath(string configDirectory) =>
        Path.Combine(configDirectory, "script-opts", "uosc-themes.json");

    public static string GetConfigPath(string configDirectory) =>
        Path.Combine(configDirectory, "script-opts", "uosc.conf");

    public static bool CanConfigure(string configDirectory) =>
        File.Exists(GetRegistryPath(configDirectory)) && File.Exists(GetConfigPath(configDirectory));

    /// <summary>读取并验证共享主题注册表。</summary>
    public static UoscThemeRegistry LoadRegistry(string configDirectory)
    {
        var path = GetRegistryPath(configDirectory);
        if (!File.Exists(path))
        {
            throw new FileNotFoundException("未找到 uosc 共享主题注册表。", path);
        }

        var json = File.ReadAllText(path, Encoding.UTF8);
        var registry = JsonSerializer.Deserialize<UoscThemeRegistry>(json, JsonOptions)
            ?? throw new InvalidDataException("uosc 共享主题注册表为空。 ");
        if (registry.Version <= 0 || registry.Palettes.Count == 0)
        {
            throw new InvalidDataException("uosc 共享主题注册表缺少版本或色板。 ");
        }

        var ids = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var palette in registry.Palettes)
        {
            if (!ThemeIdRegex().IsMatch(palette.Id)
                || string.IsNullOrWhiteSpace(palette.Name)
                || !HexColorRegex().IsMatch(palette.Accent)
                || !HexColorRegex().IsMatch(palette.AccentText))
            {
                throw new InvalidDataException($"uosc 主题色板格式无效：{palette.Id}");
            }
            if (!ids.Add(palette.Id))
            {
                throw new InvalidDataException($"uosc 主题 ID 重复：{palette.Id}");
            }
        }

        if (!ids.Contains(registry.DefaultId))
        {
            throw new InvalidDataException($"uosc 默认主题不存在：{registry.DefaultId}");
        }
        return registry;
    }

    /// <summary>读取 uosc.conf 当前 theme；不存在时返回注册表默认项。</summary>
    public static string ReadSelectedTheme(string configDirectory, string defaultId)
    {
        var path = GetConfigPath(configDirectory);
        if (!File.Exists(path))
        {
            return defaultId;
        }

        foreach (var line in File.ReadLines(path, Encoding.UTF8))
        {
            var match = ThemeLineRegex().Match(line);
            if (match.Success)
            {
                return match.Groups[1].Value.Trim();
            }
        }
        return defaultId;
    }

    /// <summary>
    /// 验证主题后写入 uosc.conf。仅替换 theme 一行，不改动其它配置，
    /// 因此不产生备份（色板注册表 uosc-themes.json 本身已版本化，可随时换回）。
    /// </summary>
    public static void ApplyTheme(string configDirectory, string themeId)
    {
        var registry = LoadRegistry(configDirectory);
        if (!registry.Palettes.Any(p => p.Id.Equals(themeId, StringComparison.OrdinalIgnoreCase)))
        {
            throw new ArgumentOutOfRangeException(nameof(themeId), $"未知 uosc 主题：{themeId}");
        }

        var path = GetConfigPath(configDirectory);
        if (!File.Exists(path))
        {
            throw new FileNotFoundException("未找到 uosc.conf。", path);
        }

        var normalized = File.ReadAllText(path, Encoding.UTF8)
            .Replace("\r\n", "\n", StringComparison.Ordinal)
            .Replace('\r', '\n');
        var lines = normalized.Split('\n').ToList();
        var replaced = false;
        for (var i = 0; i < lines.Count; i++)
        {
            if (!ThemeLineRegex().IsMatch(lines[i]))
            {
                continue;
            }
            lines[i] = $"theme={themeId}";
            replaced = true;
            break;
        }

        if (!replaced)
        {
            var insertAt = lines.Count > 0 && lines[^1].Length == 0 ? lines.Count - 1 : lines.Count;
            lines.Insert(insertAt, $"theme={themeId}");
        }

        File.WriteAllText(path, string.Join('\n', lines), new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
    }

    [GeneratedRegex(@"^[a-z0-9][a-z0-9-]*$", RegexOptions.CultureInvariant)]
    private static partial Regex ThemeIdRegex();

    [GeneratedRegex(@"^[0-9A-Fa-f]{6}$", RegexOptions.CultureInvariant)]
    private static partial Regex HexColorRegex();

    [GeneratedRegex(@"^\s*theme\s*=\s*([^#;\s]+)\s*(?:[#;].*)?$", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex ThemeLineRegex();
}
