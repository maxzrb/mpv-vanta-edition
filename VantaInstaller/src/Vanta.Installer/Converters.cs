using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace Vanta.Installer;

/// <summary>布尔取反（true→false）</summary>
public sealed class InverseBooleanConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => value is true ? false : true;

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => value is true ? false : true;
}

/// <summary>
/// 布尔取反 → Visibility（false→Visible，true→Collapsed）。
/// 说明：InverseBooleanConverter 返回 bool，而 WPF 的 Visibility 属性不会自动把 bool 转 Visibility，
/// 直接用于 Visibility 绑定会静默失败（元素保持默认 Visible）。因此 Visibility 场景必须用本转换器。
/// </summary>
public sealed class InverseBooleanToVisibilityConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => value is true ? Visibility.Collapsed : Visibility.Visible;

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotSupportedException();
}

/// <summary>字符串非空 → true；空/null → false（用于 IsOpen 等 bool 属性）</summary>
public sealed class StringNotEmptyConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => !string.IsNullOrWhiteSpace(value as string);

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotSupportedException();
}
