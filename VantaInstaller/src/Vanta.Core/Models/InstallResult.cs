namespace Vanta.Core.Models;

/// <summary>
/// 安装结果
/// </summary>
public sealed class InstallResult
{
    /// <summary>是否成功</summary>
    public bool Success { get; set; }

    /// <summary>是否为覆盖升级（目标已有 mpv.exe）</summary>
    public bool IsUpgrade { get; set; }

    /// <summary>备份目录（覆盖升级时产生）</summary>
    public string? BackupPath { get; set; }

    /// <summary>目标 mpv.exe 是否存在</summary>
    public bool MpvExists { get; set; }

    /// <summary>自检得到的 mpv 版本行</summary>
    public string? MpvVersionLine { get; set; }

    /// <summary>完整日志</summary>
    public List<string> Log { get; } = [];

    /// <summary>失败原因（Success 为 false 时）</summary>
    public string? Error { get; set; }
}
