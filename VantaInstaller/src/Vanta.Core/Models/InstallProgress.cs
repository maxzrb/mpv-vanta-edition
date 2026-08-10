namespace Vanta.Core.Models;

/// <summary>
/// 安装进度通知
/// </summary>
public sealed record InstallProgress(int Percent, string Message);
