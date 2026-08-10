using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Controls.Primitives;
using Vanta.Installer.ViewModels;
using Wpf.Ui.Controls;

namespace Vanta.Installer;

/// <summary>
/// 主窗口：Vanta 工具台外壳（模式导航 + 页面切换动画）
/// </summary>
public partial class MainWindow : FluentWindow
{
    public MainWindow()
    {
        InitializeComponent();

        // 窗口/任务栏图标：优先用 exe 同级 assets 下的图标（运行时文件）
        var iconPath = Path.Combine(AppContext.BaseDirectory, "assets", "vanta-icon.ico");
        if (!File.Exists(iconPath))
        {
            // 开发时回退到项目 assets
            iconPath = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "assets", "vanta-icon.ico");
        }
        if (File.Exists(iconPath))
        {
            Icon = new System.Windows.Media.Imaging.BitmapImage(new Uri(iconPath));
        }

        var vm = new MainViewModel();
        DataContext = vm;
        // 页面切换联动：左侧导航/步骤高亮变化的同时，右侧内容淡入上移
        vm.PropertyChanged += OnVmPropertyChanged;
    }

    private void OnVmPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(MainViewModel.CurrentPage))
        {
            // 等新页面渲染完成后再播放入场动画
            Dispatcher.BeginInvoke(System.Windows.Threading.DispatcherPriority.Loaded, new Action(AnimatePageIn));
        }
    }

    /// <summary>页面入场动画：淡入 + 轻微上移（180ms 缓出）</summary>
    private void AnimatePageIn()
    {
        PageHost.Opacity = 0;
        PageHost.RenderTransform = new TranslateTransform(0, 14);

        var storyboard = new Storyboard();

        var fade = new DoubleAnimation
        {
            From = 0,
            To = 1,
            Duration = TimeSpan.FromMilliseconds(180),
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut },
        };
        Storyboard.SetTarget(fade, PageHost);
        Storyboard.SetTargetProperty(fade, new PropertyPath(UIElement.OpacityProperty));
        storyboard.Children.Add(fade);

        var slide = new DoubleAnimation
        {
            From = 14,
            To = 0,
            Duration = TimeSpan.FromMilliseconds(180),
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut },
        };
        Storyboard.SetTarget(slide, PageHost);
        Storyboard.SetTargetProperty(slide, new PropertyPath("(UIElement.RenderTransform).(TranslateTransform.Y)"));
        storyboard.Children.Add(slide);

        storyboard.Begin();
    }

    /// <summary>点击品牌区返回主页</summary>
    private void Brand_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        if (DataContext is MainViewModel vm)
        {
            vm.GoHomeCommand.Execute(null);
        }
    }

    /// <summary>苹果按钮：关闭</summary>
    private void CloseButton_Click(object sender, RoutedEventArgs e) => Close();

    /// <summary>苹果按钮：最小化</summary>
    private void MinimizeButton_Click(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;

    /// <summary>苹果按钮：最大化/还原</summary>
    private void MaximizeButton_Click(object sender, RoutedEventArgs e)
    {
        WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
    }

    private const int WmNcLButtonDown = 0xA1;
    private const int HtCaption = 0x2;

    [DllImport("user32.dll")]
    private static extern bool ReleaseCapture();

    [DllImport("user32.dll")]
    private static extern IntPtr SendMessage(IntPtr hWnd, int msg, IntPtr wParam, IntPtr lParam);

    /// <summary>
    /// 全窗口拖拽：挂载在窗口级 Preview（隧道第一站），任何区域都能响应；
    /// 用 Win32 HTCAPTION 系统拖动，不依赖 DragMove，不与滚动/捕获冲突。
    /// </summary>
    private void Window_PreviewMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ChangedButton != MouseButton.Left || e.ButtonState != MouseButtonState.Pressed)
        {
            return;
        }

        // 先判断是否命中交互控件：命中则一律交给控件处理（不拖动、不响应双击最大化）
        if (IsInteractiveHit(e.OriginalSource as DependencyObject))
        {
            return;
        }

        // 空白区域：双击切换最大化/还原，单击拖动窗口
        if (e.ClickCount == 2)
        {
            WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
            return;
        }

        // 交给系统拖动窗口（发送 HTCAPTION 命中测试）
        var handle = new WindowInteropHelper(this).Handle;
        ReleaseCapture();
        SendMessage(handle, WmNcLButtonDown, (IntPtr)HtCaption, IntPtr.Zero);
        e.Handled = true;
    }

    /// <summary>
    /// 判断鼠标按下的原始元素是否位于交互控件内。
    /// 支持 Visual 与 ContentElement（Run/TextElement）双树遍历，确保点击按钮文字不被误判为空白。
    /// </summary>
    private static bool IsInteractiveHit(DependencyObject? current)
    {
        while (current is not null)
        {
            // 弹层（Popup）内的元素：下拉列表项、菜单项、ToolTip 等，一律视为交互
            if (current.GetType().Name == "PopupRoot")
            {
                return true;
            }

            if (current is ButtonBase or TextBox or System.Windows.Controls.PasswordBox
                or System.Windows.Controls.ComboBox or System.Windows.Controls.CheckBox
                or System.Windows.Controls.RadioButton or System.Windows.Controls.Slider
                or System.Windows.Controls.Primitives.ScrollBar or System.Windows.Controls.ProgressBar
                or System.Windows.Controls.ListBox or System.Windows.Controls.ListView
                or System.Windows.Controls.DataGrid
                or System.Windows.Controls.Primitives.MenuBase)
            {
                return true;
            }

            // Visual 走可视化树；ContentElement（Run/TextElement）走逻辑树，二者都要支持
            current = current switch
            {
                System.Windows.Media.Visual or System.Windows.Media.Media3D.Visual3D => VisualTreeHelper.GetParent(current),
                System.Windows.ContentElement content => System.Windows.ContentOperations.GetParent(content),
                _ => null,
            };
        }

        return false;
    }
}
