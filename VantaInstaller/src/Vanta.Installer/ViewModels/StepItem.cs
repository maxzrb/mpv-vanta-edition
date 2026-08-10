using CommunityToolkit.Mvvm.ComponentModel;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 向导步骤指示项（IsCurrent 带属性通知，保证左侧/横向步骤条高亮实时刷新）
/// </summary>
public partial class StepItem : ObservableObject
{
    public required int Index { get; init; }

    public required string Name { get; init; }

    /// <summary>是否当前步骤（变化时通知 UI 刷新高亮）</summary>
    [ObservableProperty]
    private bool _isCurrent;
}
