namespace Vanta.Core.Models;

/// <summary>
/// 播放模式：决定文件关联入口与 mpv 实例行为。
/// - MultiInstance：文件关联指向 mpv.exe，每次双击新开窗口（默认）。
/// - SingleInstance：文件关联指向 umpv.exe，双击通过 IPC 复用已运行的 mpv 窗口。
/// </summary>
public enum PlaybackMode
{
    /// <summary>多实例（默认）：每个文件新开 mpv 窗口</summary>
    MultiInstance,

    /// <summary>单实例：文件经 umpv 转发到已运行的 mpv，复用同一窗口</summary>
    SingleInstance,
}
