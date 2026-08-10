using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace Vanta.Core.Models;

/// <summary>mpv 配置项类型</summary>
public enum MpvOptionType
{
    /// <summary>开关（yes/no，启用写裸 key，关闭写注释）</summary>
    Bool,

    /// <summary>下拉选择</summary>
    Choice,

    /// <summary>滑块（数值）</summary>
    Slider,

    /// <summary>文本输入</summary>
    Text,
}

/// <summary>下拉选项（值 + 显示标签）</summary>
public sealed record MpvChoice(string Value, string Label);

/// <summary>
/// 一个可在设置中心调节的 mpv.conf 配置项。
/// CurrentValue 支持属性通知，供 UI 双向绑定。
/// </summary>
public sealed class MpvOption : INotifyPropertyChanged
{
    /// <summary>mpv.conf 键名</summary>
    public required string Key { get; init; }

    /// <summary>显示名（中文）</summary>
    public required string DisplayName { get; init; }

    /// <summary>分组（界面 / 解码 / 播放 / 音频 / 截图）</summary>
    public required string Group { get; init; }

    /// <summary>类型</summary>
    public required MpvOptionType Type { get; init; }

    /// <summary>初始生效值（= 当前 mpv.conf 实际设置）</summary>
    public required string DefaultValue { get; init; }

    /// <summary>可选值（Choice 用）</summary>
    public IReadOnlyList<MpvChoice>? Choices { get; init; }

    /// <summary>滑块范围</summary>
    public double Min { get; init; }

    /// <summary>滑块范围上限</summary>
    public double Max { get; init; }

    /// <summary>说明</summary>
    public string? Description { get; init; }

    /// <summary>当前值（UI 双向绑定）</summary>
    public string CurrentValue
    {
        get => _currentValue;
        set
        {
            if (_currentValue != value)
            {
                _currentValue = value;
                OnPropertyChanged();
            }
        }
    }

    /// <summary>行是否原本启用（非注释）</summary>
    public bool WasActive { get; set; }

    /// <summary>行是否原本被注释</summary>
    public bool WasCommented { get; set; }

    /// <summary>是否已修改（相对默认值）</summary>
    public bool IsModified => !string.Equals(CurrentValue, DefaultValue, StringComparison.OrdinalIgnoreCase);

    /// <summary>当前值对应的显示标签</summary>
    public string DisplayValue
    {
        get
        {
            if (Choices is null)
            {
                return CurrentValue;
            }
            var choice = Choices.FirstOrDefault(c => c.Value == CurrentValue);
            return choice?.Label ?? CurrentValue;
        }
    }

    private string _currentValue = string.Empty;

    public event PropertyChangedEventHandler? PropertyChanged;

    private void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
