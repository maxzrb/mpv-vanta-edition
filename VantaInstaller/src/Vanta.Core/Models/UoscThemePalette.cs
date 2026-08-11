using System.Text.Json.Serialization;

namespace Vanta.Core.Models;

/// <summary>uosc 共享主题色板；色号来自 portable_config/script-opts/uosc-themes.json。</summary>
public sealed class UoscThemePalette
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("installerName")]
    public string? InstallerName { get; init; }

    [JsonPropertyName("accent")]
    public string Accent { get; init; } = string.Empty;

    [JsonPropertyName("accentText")]
    public string AccentText { get; init; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; init; } = string.Empty;

    [JsonIgnore]
    public string AccentDisplay => $"#{Accent}";

    [JsonIgnore]
    public string DisplayName => string.IsNullOrWhiteSpace(InstallerName) ? Name : InstallerName;
}

/// <summary>uosc 主题注册表。</summary>
public sealed class UoscThemeRegistry
{
    [JsonPropertyName("version")]
    public int Version { get; init; }

    [JsonPropertyName("default")]
    public string DefaultId { get; init; } = string.Empty;

    [JsonPropertyName("palettes")]
    public List<UoscThemePalette> Palettes { get; init; } = [];
}
