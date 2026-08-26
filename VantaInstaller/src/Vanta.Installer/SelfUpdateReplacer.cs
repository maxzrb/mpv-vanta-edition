using System.Diagnostics;
using System.IO;

namespace Vanta.Installer;

/// <summary>
/// 安装器自更新替换：新 exe 下载并校验完成后记录路径，应用退出时由隐藏 cmd 助手完成替换。
/// 替换结果为新 exe 以规范文件名（含新版本号）落在当前 exe 同目录，并删除旧文件名的 exe，
/// 避免出现「文件名还是旧版本、内容已是新版本」的错位。
/// </summary>
public static class SelfUpdateReplacer
{
    /// <summary>待替换的新 exe 路径（null = 无待执行替换）</summary>
    public static string? PendingNewExePath { get; set; }

    /// <summary>
    /// 应用退出时调度替换脚本。任何失败均静默放弃本次替换
    /// （新 exe 保留在 updates 目录，用户可手动更换）。
    /// </summary>
    public static void ScheduleOnExit()
    {
        var newPath = PendingNewExePath;
        var oldPath = Environment.ProcessPath;
        if (string.IsNullOrEmpty(newPath) || !File.Exists(newPath)
            || string.IsNullOrEmpty(oldPath) || !Path.IsPathRooted(oldPath))
        {
            return;
        }

        // 新 exe 落点：与当前 exe 同目录、使用自带版本号的规范文件名
        var targetPath = Path.Combine(
            Path.GetDirectoryName(oldPath) ?? Environment.CurrentDirectory,
            Path.GetFileName(newPath));
        var samePath = string.Equals(targetPath, oldPath, StringComparison.OrdinalIgnoreCase);

        try
        {
            var script = Path.Combine(Path.GetTempPath(), $"vanta-self-update-{Environment.ProcessId}.cmd");
            // 运行中的 exe 被锁：move 到其路径 / del 都会失败，进程退出后自然成功。
            // 用重试循环替代 PID 检测（不依赖 find/tasklist 解析，不受 PATH 环境影响）；
            // waitfor /t 1 用作 1 秒延时（不依赖网络与控制台输入），最多重试 30 次。
            // 同名场景（当前 exe 已是规范新名）为覆盖式 move；异名场景为 move 新文件 + del 旧文件。
            File.WriteAllText(script, samePath
                ? $"""
                  @echo off
                  setlocal
                  set "NEW={newPath}"
                  set "OLD={oldPath}"
                  for /l %%i in (1,1,30) do (
                      move /y "%NEW%" "%OLD%" >nul 2>&1 && goto done
                      waitfor /t 1 vantaSelfUpdate >nul 2>&1
                  )
                  :done
                  del "%~f0" >nul 2>&1
                  endlocal
                  """
                : $"""
                  @echo off
                  setlocal
                  set "SRC={newPath}"
                  set "DST={targetPath}"
                  set "OLD={oldPath}"
                  for /l %%i in (1,1,30) do (
                      move /y "%SRC%" "%DST%" >nul 2>&1
                      if exist "%OLD%" del /f /q "%OLD%" >nul 2>&1
                      if not exist "%SRC%" if not exist "%OLD%" goto done
                      waitfor /t 1 vantaSelfUpdate >nul 2>&1
                  )
                  :done
                  del "%~f0" >nul 2>&1
                  endlocal
                  """);
            Process.Start(new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/c \"{script}\"",
                CreateNoWindow = true,
                UseShellExecute = false,
            });
        }
        catch
        {
            // 调度失败：放弃本次替换
        }
    }
}
