using System.Windows.Controls;
using System.Windows.Media;

namespace Vanta.Installer.Views;

/// <summary>
/// InstallView 视图（占位骨架）
/// </summary>
public partial class InstallView : UserControl
{
    public InstallView()
    {
        InitializeComponent();
    }

    /// <summary>日志更新后自动滚动到底部（保持看到最新输出）</summary>
    private void LogBox_TextChanged(object sender, System.Windows.Controls.TextChangedEventArgs e)
    {
        if (LogBox is { } box)
        {
            box.ScrollToEnd();
        }
    }
}
