namespace Vanta.Core.Models;

/// <summary>
/// 安装选项
/// </summary>
public sealed class InstallOptions
{
    /// <summary>包所在目录（自动扫描 01~04）</summary>
    public required string SourceDirectory { get; init; }

    /// <summary>目标安装目录</summary>
    public required string InstallDirectory { get; init; }

    /// <summary>覆盖升级前是否备份 portable_config</summary>
    public bool BackupBeforeUpgrade { get; init; } = true;

    /// <summary>保留备份份数</summary>
    public int KeepBackups { get; init; } = 5;

    /// <summary>
    /// 要安装的包选择键集合（增量包为 "编号|版本"，如 "01|1.5.2"、"04|1.5.2"；
    /// 个人全量包为 "00"）。同一编号不同版本是独立条目，用完整键区分。
    /// 为 null 时安装全部扫描到的包。
    /// </summary>
    public IReadOnlyCollection<string>? SelectedPackageKeys { get; init; }

    /// <summary>
    /// 安装完成后要注册的文件关联入口（null/空=不注册）。
    /// 为当前用户注册 mpv.exe 多实例或 umpv.exe 单实例入口；两套应用身份和 ProgID 完全独立，
    /// 可同时注册并在 Windows「打开方式」里自行选择。
    /// </summary>
    public IReadOnlyCollection<PlaybackMode>? RegisterAssociations { get; init; }

    /// <summary>
    /// 哈希校验发现风险时请求用户确认。返回 true 表示用户明确接受风险并继续；
    /// 未提供回调时默认拒绝继续，确保所有安装入口都不会静默忽略校验风险。
    /// </summary>
    public Func<PackageIntegrityResult, Task<bool>>? ConfirmIntegrityRisksAsync { get; init; }
}
