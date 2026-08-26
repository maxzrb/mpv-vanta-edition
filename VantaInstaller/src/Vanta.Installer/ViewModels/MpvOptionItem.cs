using System.Collections.ObjectModel;
using System.Globalization;
using CommunityToolkit.Mvvm.ComponentModel;
using Vanta.Core.Models;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// mpv 配置项 UI 包装：提供可双向绑定的 Bool / Slider / Choice / Text 视图
/// </summary>
public partial class MpvOptionItem : ObservableObject
{
    public MpvOption Option { get; }

    public MpvOptionItem(MpvOption option) => Option = option;

    public string Key => Option.Key;

    public string DisplayName => Option.DisplayName;

    public string Description => Option.Description ?? string.Empty;

    public MpvOptionType Type => Option.Type;

    public IReadOnlyList<MpvChoice> Choices => Option.Choices ?? [];

    public bool IsModified => Option.IsModified;

    /// <summary>当前值（字符串，直接映射 mpv.conf 值）</summary>
    public string CurrentValue
    {
        get => Option.CurrentValue;
        set
        {
            Option.CurrentValue = value;
            OnPropertyChanged();
            OnPropertyChanged(nameof(BoolValue));
            OnPropertyChanged(nameof(SliderValue));
            OnPropertyChanged(nameof(SliderDisplayValue));
            OnPropertyChanged(nameof(IsModified));
        }
    }

    /// <summary>开关值（Bool 类型用）</summary>
    public bool BoolValue
    {
        get => string.Equals(Option.CurrentValue, "yes", StringComparison.OrdinalIgnoreCase);
        set => CurrentValue = value ? "yes" : "no";
    }

    /// <summary>滑块值（Slider 类型用）</summary>
    public double SliderValue
    {
        get
        {
            var raw = Option.CurrentValue.Trim();
            if (Option.ValueSuffix.Length > 0
                && raw.EndsWith(Option.ValueSuffix, StringComparison.OrdinalIgnoreCase))
            {
                raw = raw[..^Option.ValueSuffix.Length].TrimEnd();
            }
            return double.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out var value)
                ? value
                : 0;
        }
        set
        {
            var normalized = Option.Step > 0
                ? Math.Round(value / Option.Step) * Option.Step
                : value;
            CurrentValue = normalized.ToString("0.##", CultureInfo.InvariantCulture) + Option.ValueSuffix;
        }
    }

    /// <summary>滑块右侧显示值，单位与配置序列化分离。</summary>
    public string SliderDisplayValue
    {
        get
        {
            var suffix = Option.DisplaySuffix.Length > 0 ? Option.DisplaySuffix : Option.ValueSuffix;
            return SliderValue.ToString("0.##", CultureInfo.InvariantCulture)
                + (suffix.Length > 0 ? $" {suffix}" : string.Empty);
        }
    }
}

/// <summary>mpv 配置分组（界面/解码/播放/音频/截图）</summary>
public sealed class MpvGroupItem
{
    public required string Name { get; init; }

    public ObservableCollection<MpvOptionItem> Options { get; } = [];
}
