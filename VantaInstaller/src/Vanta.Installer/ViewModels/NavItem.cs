using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using Wpf.Ui.Controls;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 左侧导航项（首页/安装/卸载/设置）
/// </summary>
/// <summary>
/// 左侧导航项（首页/安装/卸载/设置）
/// </summary>
public partial class NavItem : ObservableObject
{
    public required string Name { get; init; }

    public required SymbolRegular Symbol { get; init; }

    public required ICommand Command { get; init; }

    /// <summary>是否当前激活（变化时通知 UI 刷新高亮）</summary>
    [ObservableProperty]
    private bool _isActive;
}
