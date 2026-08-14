namespace Vanta.Core.Models;

/// <summary>
/// 一个 Vanta 增量包（01~04）
/// </summary>
public sealed class VantaPackage
{
    /// <summary>包编号：01~04</summary>
    public required string Id { get; init; }

    /// <summary>包显示名（如 Base · 核心播放器）</summary>
    public required string DisplayName { get; init; }

    /// <summary>版本号（如 1.4.2）</summary>
    public required string Version { get; init; }

    /// <summary>主文件 / 分卷入口文件名（如 02-mpv-extras-v1.4.2.7z.001）</summary>
    public string EntryFile { get; set; } = string.Empty;

    /// <summary>分卷文件名列表（含入口，单文件包只有一项）</summary>
    public required IReadOnlyList<string> Files { get; set; }

    /// <summary>是否为必选包</summary>
    public required bool Required { get; init; }

    /// <summary>UI 勾选状态</summary>
    public bool IsSelected { get; set; } = true;

    /// <summary>分卷是否齐全</summary>
    public bool IsComplete { get; set; }

    /// <summary>缺失的分卷文件名</summary>
    public IReadOnlyList<string> MissingParts { get; set; } = [];

    /// <summary>包总大小（字节）</summary>
    public long TotalSize { get; set; }

    /// <summary>所属源目录</summary>
    public required string SourceDirectory { get; init; }

    /// <summary>完整路径（入口文件）</summary>
    public string EntryPath => Path.Combine(SourceDirectory, EntryFile);

    /// <summary>用于列表显示：01 Base · 核心播放器（v1.4.2 · 1.2 GB）</summary>
    public string DisplayText =>
        $"{Id} {DisplayName}（v{Version} · {FormatSize(TotalSize)}）";

    /// <summary>人类可读大小文本</summary>
    public string SizeText => FormatSize(TotalSize);

    /// <summary>人类可读大小</summary>
    public static string FormatSize(long bytes)
    {
        string[] units = ["B", "KB", "MB", "GB", "TB"];
        double size = bytes;
        int unit = 0;
        while (size >= 1024 && unit < units.Length - 1)
        {
            size /= 1024;
            unit++;
        }
        return $"{size:0.##} {units[unit]}";
    }
}
