namespace Vanta.Installer.ViewModels;

/// <summary>
/// 向导步骤指示项
/// </summary>
public sealed class StepItem
{
    public required int Index { get; init; }

    public required string Name { get; init; }

    public bool IsCurrent { get; set; }
}
