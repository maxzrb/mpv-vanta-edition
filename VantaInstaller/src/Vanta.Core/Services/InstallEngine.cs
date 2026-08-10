using System.Diagnostics;
using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// 安装引擎：扫描包 → 校验 → 备份 → 按序解压 → 自检。
/// </summary>
public sealed class InstallEngine
{
    /// <summary>日志行</summary>
    public event Action<string>? Log;

    /// <summary>当前解压包进度（文件名，0~100）</summary>
    public event Action<string, int>? PackageProgress;

    /// <summary>整体进度（0~100）</summary>
    public event Action<int>? GlobalProgress;

    private readonly SevenZipService _sevenZip;

    public InstallEngine(SevenZipService? sevenZip = null) => _sevenZip = sevenZip ?? new SevenZipService();

    /// <summary>
    /// 执行安装/覆盖升级。
    /// </summary>
    public async Task<InstallResult> RunAsync(InstallOptions options, IProgress<InstallProgress>? progress = null, CancellationToken ct = default)
    {
        var result = new InstallResult();
        Log ??= _ => { };

        // 日志助手：同时写入 result.Log 并通过 Log 事件实时推送 UI（方法级，catch 也可用）
        void AddLog(string line)
        {
            result.Log.Add(line);
            Log?.Invoke(line);
        }

        try
        {
            // 1. 定位 7z
            var sevenZipPath = await _sevenZip.LocateAsync();
            AddLog($"7z：{sevenZipPath}");

            // 2. 扫描包
            var scan = PackageScanner.Scan(options.SourceDirectory);
            foreach (var e in scan.Errors)
            {
                AddLog($"[错误] {e}");
            }
            if (!scan.CanInstall)
            {
                result.Success = false;
                result.Error = string.Join(Environment.NewLine, scan.Errors);
                return result;
            }
            // 全量包模式：用户选中 "00"（个人全量包）时，只解压全量包（解压即用一体包），忽略增量包
            var wantFull = options.SelectedPackageIds?.Contains("00") == true;
            AddLog(wantFull
                ? $"检测到个人全量包 v{scan.FullPackage!.Version}（解压即用一体包），将跳过增量包安装"
                : $"识别到 {scan.Packages.Count} 个增量包（统一版本 v{scan.UnifiedVersion}）");

            // 3. 目标目录状态
            result.IsUpgrade = File.Exists(Path.Combine(options.InstallDirectory, "mpv.exe"));
            AddLog(result.IsUpgrade
                ? $"目标目录已有旧版，进入覆盖升级模式：{options.InstallDirectory}"
                : $"全新安装：{options.InstallDirectory}");

            // 4. 磁盘空间预检
            Directory.CreateDirectory(options.InstallDirectory);
            List<VantaPackage> selected;
            if (wantFull)
            {
                if (scan.FullPackage is null)
                {
                    result.Success = false;
                    result.Error = "未找到个人全量包，无法安装。";
                    return result;
                }
                selected = [scan.FullPackage];
                AddLog($"选择安装个人全量包：{scan.FullPackage.EntryFile}（v{scan.FullPackage.Version}，解压即用一体包）");
            }
            else
            {
                selected = (options.SelectedPackageIds is null)
                    ? scan.Packages
                    : scan.Packages.Where(p => options.SelectedPackageIds.Contains(p.Id)).ToList();
            }
            if (selected.Count == 0)
            {
                result.Success = false;
                result.Error = "没有选中的包，无法安装。";
                return result;
            }

            var needed = selected.Sum(p => p.TotalSize);
            var root = Path.GetPathRoot(Path.GetFullPath(options.InstallDirectory)) ?? "C:\\";
            var drive = new DriveInfo(root);
            if (drive.IsReady && drive.AvailableFreeSpace < needed)
            {
                result.Success = false;
                result.Error = $"磁盘空间不足：需要 {VantaPackage.FormatSize(needed)}，可用 {VantaPackage.FormatSize(drive.AvailableFreeSpace)}。";
                return result;
            }
            AddLog($"磁盘空间充足：需要 {VantaPackage.FormatSize(needed)}");

            // 5. 覆盖升级前备份
            if (result.IsUpgrade && options.BackupBeforeUpgrade)
            {
                var backupRoot = Path.Combine(options.InstallDirectory, "backup");
                result.BackupPath = BackupService.BackupConfig(
                    Path.Combine(options.InstallDirectory, "portable_config"),
                    backupRoot,
                    options.KeepBackups);
                AddLog(result.BackupPath is null
                    ? "未发现 portable_config，跳过备份。"
                    : $"已备份配置到：{result.BackupPath}");
            }

            // 6. 按序解压
            AddLog($"将安装 {selected.Count} 个包：{string.Join(" → ", selected.Select(p => p.Id))}");
            progress?.Report(new InstallProgress(0, "开始安装"));

            for (int i = 0; i < selected.Count; i++)
            {
                ct.ThrowIfCancellationRequested();
                var pkg = selected[i];
                AddLog($"[{pkg.Id}] 开始解压 {pkg.EntryFile} …");

                // 包级进度 → 整体进度（当前包占 90%，跨包滚动）
                void OnProgress(int pct)
                {
                    PackageProgress?.Invoke(pkg.EntryFile, pct);
                    var overall = (int)((i * 100.0 + pct * 0.9) / selected.Count);
                    GlobalProgress?.Invoke(overall);
                    progress?.Report(new InstallProgress(overall, $"正在解压 {pkg.DisplayName}"));
                }
                void OnOutput(string line)
                {
                    // 7z 原始输出进日志，方便观察解压明细
                    AddLog($"    {line}");
                }

                _sevenZip.ProgressChanged += OnProgress;
                _sevenZip.OutputReceived += OnOutput;
                try
                {
                    await _sevenZip.ExtractAsync(pkg.EntryPath, options.InstallDirectory, ct);
                }
                finally
                {
                    _sevenZip.ProgressChanged -= OnProgress;
                    _sevenZip.OutputReceived -= OnOutput;
                }

                AddLog($"[{pkg.Id}] 完成");
                progress?.Report(new InstallProgress((int)((i + 1) * 100.0 / selected.Count), $"{pkg.DisplayName} 完成"));
            }

            // 7. 自检
            var mpvExe = Path.Combine(options.InstallDirectory, "mpv.exe");
            result.MpvExists = File.Exists(mpvExe);
            if (result.MpvExists)
            {
                result.MpvVersionLine = await TryGetMpvVersionAsync(mpvExe);
                AddLog($"自检通过：{result.MpvVersionLine}");
            }
            else
            {
                AddLog("警告：安装后未找到 mpv.exe，请检查是否选择了 01 号包。");
            }

            // 8. 写入版本标记（供检查更新识别当前包版本）；全量包模式用全量包版本
            var installVersion = wantFull ? scan.FullPackage!.Version : scan.UnifiedVersion;
            if (!string.IsNullOrWhiteSpace(installVersion))
            {
                try
                {
                    var marker = Path.Combine(options.InstallDirectory, "portable_config", ".vanta-version");
                    var markerDir = Path.GetDirectoryName(marker);
                    if (markerDir is not null)
                    {
                        Directory.CreateDirectory(markerDir);
                        File.WriteAllText(marker, installVersion.Trim());
                        AddLog($"已写入版本标记：{installVersion}");
                    }
                }
                catch (Exception ex)
                {
                    AddLog($"警告：写入版本标记失败 {ex.Message}");
                }
            }

            // 记忆上次安装位置（下次检测优先命中）
            InstallLocationStore.SaveLastInstallDirectory(options.InstallDirectory);
            AddLog($"已记忆安装位置：{options.InstallDirectory}");
            // 新装/覆盖升级后清除此前的手动指定，避免工具台继续指向旧位置
            InstallLocationStore.SaveManualMpvPath(null);
            AddLog("已清除手动指定的 mpv 位置");

            // 安装完成后注册文件关联（可选）：多实例 → mpv.exe；单实例 → umpv.exe（各弹一次 UAC）
            if (options.RegisterAssociations is { Count: > 0 } regModes)
            {
                foreach (var regMode in regModes)
                {
                    var modeText = regMode == PlaybackMode.SingleInstance ? "单实例" : "多实例";
                    var bat = AssociationService.InstallBatPath(options.InstallDirectory, regMode);
                    if (bat is null)
                    {
                        AddLog($"警告：未找到 {modeText} 关联脚本（installer\\mpv-install*.bat），跳过注册。");
                    }
                    else
                    {
                        AddLog($"正在注册{modeText}文件关联（{Path.GetFileName(bat)}，需 UAC 确认）…");
                        await RunBatElevatedAsync(bat, options.InstallDirectory);
                        AddLog($"已触发{modeText}文件关联注册。");
                    }
                }
            }

            result.Success = true;
            progress?.Report(new InstallProgress(100, "安装完成"));
            return result;
        }
        catch (OperationCanceledException)
        {
            result.Success = false;
            result.Error = "安装已取消。";
            return result;
        }
        catch (Exception ex)
        {
            result.Success = false;
            result.Error = ex.Message;
            AddLog($"[异常] {ex.Message}");
            return result;
        }
    }

    private static async Task<string?> TryGetMpvVersionAsync(string mpvExe)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = mpvExe,
                Arguments = "--version",
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                // mpv 以 UTF-8 输出版本信息；不显式指定会按系统 GBK 解码导致 © 变乱码
                StandardOutputEncoding = System.Text.Encoding.UTF8,
                StandardErrorEncoding = System.Text.Encoding.UTF8,
            };
            using var proc = Process.Start(psi);
            if (proc is null)
            {
                return null;
            }
            var line = await proc.StandardOutput.ReadLineAsync();
            await proc.WaitForExitAsync();
            return line;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>以管理员身份运行 bat（弹 UAC）；用户取消或失败不阻断安装</summary>
    private static async Task RunBatElevatedAsync(string batPath, string workingDir)
    {
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/c \"\"{batPath}\"\"",
                WorkingDirectory = workingDir,
                UseShellExecute = true,
                Verb = "runas",
            });
            await Task.Delay(500);
        }
        catch
        {
            // 用户取消 UAC 或提权失败，不阻断安装
        }
    }
}
