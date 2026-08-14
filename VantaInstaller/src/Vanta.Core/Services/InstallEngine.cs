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
            // 升级场景允许缺少 01 Base：是否必须 Base 由下方按目标目录状态把关
            var scan = PackageScanner.Scan(options.SourceDirectory, allowMissingBase: true);
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
                : $"识别到 {scan.Packages.Count} 个增量包（版本 {scan.UnifiedVersion ?? "多个版本"}）");

            // 3. 选出本次要安装的包
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

            // 3.1 本次选中的包必须同版本（目录里混有旧包时扫描仅警告，这里强制把关）
            var selectedVersions = selected.Select(p => p.Version).Distinct().ToList();
            if (!wantFull && selectedVersions.Count > 1)
            {
                result.Success = false;
                result.Error = $"选中的包版本不一致：{string.Join(" / ", selectedVersions)}。请取消勾选旧版本包，只保留同一版本的组合。";
                AddLog(result.Error);
                return result;
            }

            // 4. 安装前逐文件 SHA-256 校验。所有入口都必须执行；有风险时由 UI 明确询问用户。
            var integrityVersion = wantFull ? scan.FullPackage!.Version : selectedVersions[0];
            AddLog($"开始校验 {selected.Sum(package => package.Files.Count)} 个安装包文件的 SHA-256…");
            var integrityProgress = new Progress<PackageIntegrityProgress>(p =>
            {
                GlobalProgress?.Invoke(Math.Clamp(p.Percent / 10, 0, 10));
                progress?.Report(new InstallProgress(
                    Math.Clamp(p.Percent / 10, 0, 10),
                    $"正在校验 {p.FileName}（{p.Percent}%）"));
            });
            var integrity = await PackageIntegrityService.VerifyAsync(
                selected,
                integrityVersion,
                integrityProgress,
                ct);
            if (!string.IsNullOrWhiteSpace(integrity.ReferenceError))
            {
                AddLog($"[校验警告] {integrity.ReferenceError}");
            }
            foreach (var item in integrity.Items)
            {
                AddLog(FormatIntegrityLog(item));
            }

            if (integrity.HasRisks)
            {
                progress?.Report(new InstallProgress(10, "安装包校验发现风险，等待确认"));
                var accepted = options.ConfirmIntegrityRisksAsync is not null
                    && await options.ConfirmIntegrityRisksAsync(integrity);
                if (!accepted)
                {
                    result.Success = false;
                    result.Error = "安装包哈希校验未通过或缺少可信哈希，安装已取消。";
                    AddLog("[拦截] 用户未接受校验风险，未开始备份或解压。");
                    return result;
                }
                AddLog("[高风险继续] 用户已明确忽略哈希校验风险，继续安装。");
            }
            else
            {
                AddLog($"SHA-256 校验通过：{integrity.PassedCount} 个文件。");
            }

            // 5. 目标目录状态
            result.IsUpgrade = File.Exists(Path.Combine(options.InstallDirectory, "mpv.exe"));
            AddLog(result.IsUpgrade
                ? $"目标目录已有旧版，进入覆盖升级模式：{options.InstallDirectory}"
                : $"全新安装：{options.InstallDirectory}");

            // 5.1 全新安装必须包含 01 Base；覆盖升级（目标已有 mpv）允许只升级组件/配置
            if (!wantFull && !result.IsUpgrade && !selected.Any(p => p.Id == "01"))
            {
                result.Success = false;
                result.Error = "全新安装必须包含 01 Base 包。若只是升级已安装的 mpv，请选择已安装的 mpv 目录作为安装位置（会进入覆盖升级模式，可不带 01）。";
                AddLog(result.Error);
                return result;
            }
            if (!wantFull && result.IsUpgrade && !selected.Any(p => p.Id == "01"))
            {
                AddLog("升级模式：包目录未包含 01 Base，仅升级所选组件/配置（跳过 Base）。");
            }

            // 6. 磁盘空间预检
            Directory.CreateDirectory(options.InstallDirectory);
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

            // 7. 覆盖升级前备份
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

            // 8. 按序解压
            AddLog($"将安装 {selected.Count} 个包：{string.Join(" → ", selected.Select(p => p.Id))}");
            progress?.Report(new InstallProgress(0, "开始安装"));

            for (int i = 0; i < selected.Count; i++)
            {
                ct.ThrowIfCancellationRequested();
                var pkg = selected[i];
                AddLog($"[{pkg.Id}] 开始解压 {pkg.EntryFile} …");

                // 包级进度 → 整体进度（哈希校验占前 10%，解压阶段占后 90%）
                void OnProgress(int pct)
                {
                    PackageProgress?.Invoke(pkg.EntryFile, pct);
                    var overall = 10 + (int)((i + pct / 100.0) * 90 / selected.Count);
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
                progress?.Report(new InstallProgress(10 + (int)((i + 1) * 90.0 / selected.Count), $"{pkg.DisplayName} 完成"));
            }

            // 9. 自检
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

            // 10. 写入版本标记（供检查更新识别当前包版本）；全量包模式用全量包版本，
            // 增量模式用本次选中包版本（升级只装 04 时也要更新标记到新版本）
            var installVersion = wantFull ? scan.FullPackage!.Version : selectedVersions[0];
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

            // 安装完成后注册当前用户文件关联（可选）：多实例 → mpv.exe；单实例 → umpv.exe。
            if (options.RegisterAssociations is { Count: > 0 } regModes)
            {
                foreach (var regMode in regModes)
                {
                    var modeText = regMode == PlaybackMode.SingleInstance ? "单实例" : "多实例";
                    AddLog($"正在为当前用户注册{modeText}文件关联…");
                    var associationResult = AssociationService.Register(options.InstallDirectory, regMode);
                    AddLog(associationResult.Success
                        ? associationResult.Message
                        : $"警告：{associationResult.Message}");
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

    private static string FormatIntegrityLog(PackageIntegrityItem item) => item.Status switch
    {
        PackageIntegrityStatus.Passed => $"[校验通过] {item.FileName}",
        PackageIntegrityStatus.Mismatch => $"[校验失败] {item.FileName} SHA-256 不一致（预期 {item.ExpectedSha256}，实际 {item.ActualSha256}）",
        PackageIntegrityStatus.MissingReference => $"[校验警告] {item.FileName} 没有可信的 Release SHA-256",
        PackageIntegrityStatus.MissingFile => $"[校验失败] {item.FileName} 不存在",
        PackageIntegrityStatus.ReadError => $"[校验失败] {item.FileName} 无法读取：{item.Error}",
        _ => $"[校验失败] {item.FileName} 状态未知",
    };

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

}
