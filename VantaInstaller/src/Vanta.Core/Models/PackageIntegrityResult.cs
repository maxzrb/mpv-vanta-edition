namespace Vanta.Core.Models;

/// <summary>单个安装包文件的 SHA-256 校验状态。</summary>
public enum PackageIntegrityStatus
{
    Passed,
    Mismatch,
    MissingReference,
    MissingFile,
    ReadError,
}

/// <summary>单个安装包文件的校验结果。</summary>
public sealed record PackageIntegrityItem(
    string FileName,
    PackageIntegrityStatus Status,
    string? ExpectedSha256,
    string? ActualSha256,
    string? Error = null)
{
    public bool IsRisk => Status != PackageIntegrityStatus.Passed;
}

/// <summary>安装前全部选中包的校验结果。</summary>
public sealed record PackageIntegrityResult(
    IReadOnlyList<PackageIntegrityItem> Items,
    string? ReferenceError = null)
{
    public bool HasRisks => Items.Any(item => item.IsRisk);

    public int PassedCount => Items.Count(item => !item.IsRisk);

    public int RiskCount => Items.Count(item => item.IsRisk);
}

/// <summary>哈希计算进度。</summary>
public sealed record PackageIntegrityProgress(int Percent, string FileName);
