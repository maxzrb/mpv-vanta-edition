namespace Vanta.Core.Models;

/// <summary>
/// 包扫描结果
/// </summary>
public sealed class PackageScanResult
{
    /// <summary>按编号排序的已识别包（01~05）</summary>
    public List<VantaPackage> Packages { get; } = [];

    /// <summary>扫描到的私用全量包文件名（仅本地，不应分发）</summary>
    public string? FullPrivateFile { get; set; }

    /// <summary>统一版本号（所有包一致时有效）</summary>
    public string? UnifiedVersion { get; set; }

    /// <summary>错误信息（有错误则不能安装）</summary>
    public List<string> Errors { get; } = [];

    /// <summary>警告信息（不阻止安装）</summary>
    public List<string> Warnings { get; } = [];

    /// <summary>是否可安装</summary>
    public bool CanInstall => Errors.Count == 0;

    /// <summary>必选但缺失的包编号</summary>
    public List<string> MissingRequiredIds { get; } = [];

    /// <summary>选中包总需磁盘空间</summary>
    public long SelectedTotalSize => Packages.Where(p => p.IsSelected).Sum(p => p.TotalSize);
}
