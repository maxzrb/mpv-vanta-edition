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

/// <summary>字符串非空 → true；空/null → false（用于 IsOpen 等 bool 属性）</summary>
public sealed class StringNotEmptyConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        => !string.IsNullOrWhiteSpace(value as string);

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotSupportedException();
}
