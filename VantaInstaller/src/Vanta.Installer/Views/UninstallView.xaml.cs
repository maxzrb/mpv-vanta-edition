using System.Windows.Controls;

namespace Vanta.Installer.Views;

/// <summary>
/// 卸载流程视图
/// </summary>
public partial class UninstallView : UserControl
{
    public UninstallView()
    {
        InitializeComponent();
    }

    /// <summary>日志更新后自动滚动到底部</summary>
    private void UninstallLogBox_TextChanged(object sender, System.Windows.Controls.TextChangedEventArgs e)
    {
        if (UninstallLogBox is { } box)
        {
            box.ScrollToEnd();
        }
    }
}
