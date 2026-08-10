using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using Vanta.Core.Models;
using Vanta.Core.Services;

namespace Vanta.Installer.ViewModels;

/// <summary>
/// 设置中心：启动、信息、目录、文件关联、配置备份/恢复、检查更新、缓存清理
/// </summary>
public partial class SettingsViewModel : ObservableObject
{
    private readonly AppSession _session;

    /// <summary>检测到的安装信息</summary>
    [ObservableProperty]
    private InstallationDetector.InstallationInfo? _installation;

    /// <summary>是否已安装</summary>
    public bool IsInstalled => Installation is { IsValid: true };

    /// <summary>是否为带 .vanta-version 标记的 Vanta 安装</summary>
    public bool IsVanta => Installation is { IsVanta: true };

    /// <summary>状态标题（区分 Vanta 安装与任意 mpv）</summary>
    public string StatusTitle => IsInstalled
        ? (IsVanta ? "MPV Vanta Edition" : "检测到 mpv（非 Vanta 安装）")
        : "尚未检测到安装";

    /// <summary>安装目录</summary>
    public string InstallDirectory => Installation?.Directory ?? string.Empty;

    /// <summary>版本行</summary>
    public string VersionLine => Installation?.VersionLine ?? string.Empty;

    /// <summary>占用空间</summary>
    public string SizeText => Installation?.SizeText ?? string.Empty;

    /// <summary>配置目录路径</summary>
    public string ConfigDirectory => Path.Combine(InstallDirectory, "portable_config");

    /// <summary>备份目录路径</summary>
    public string BackupDirectory => Path.Combine(InstallDirectory, "backup");

    /// <summary>是否可注册关联（存在 mpv-install.bat）</summary>
    public bool CanRegister =>
        IsInstalled && File.Exists(Path.Combine(InstallDirectory, "installer", "mpv-install.bat"));

    // ---- 检查更新 ----

    /// <summary>检查更新状态文本</summary>
    [ObservableProperty]
    private string _updateStatus = "尚未检查更新。";

    /// <summary>最新版本号</summary>
    [ObservableProperty]
    private string? _latestVersion;

    /// <summary>是否有新版本</summary>
    [ObservableProperty]
    private bool _hasUpdate;

    /// <summary>最新版本 Release 地址</summary>
    [ObservableProperty]
    private string? _releaseUrl;

    /// <summary>是否正在检查</summary>
    [ObservableProperty]
    private bool _isCheckingUpdate;

    // ---- 配置备份 ----

    /// <summary>历史备份列表</summary>
    public ObservableCollection<ConfigManager.BackupEntry> Backups { get; } = [];

    /// <summary>是否显示备份列表</summary>
    public bool HasBackups => Backups.Count > 0;

    /// <summary>操作结果提示</summary>
    [ObservableProperty]
    private string? _operationMessage;

    // ---- 缓存 ----

    /// <summary>缓存统计</summary>
    [ObservableProperty]
    private CacheService.CacheStats? _cacheStats;

    /// <summary>缓存体积文本</summary>
    public string CacheSizeText => CacheStats?.SizeText ?? "—";

    /// <summary>缓存明细</summary>
    public string CacheDetailText => CacheStats is { Items.Count: > 0 }
        ? string.Join(Environment.NewLine, CacheStats.Items)
        : "未发现缓存。";

    /// <summary>
    /// 当前包版本：安装标记 .vanta-version → 会话扫描结果 → 0.0.0 兜底。
    /// </summary>
    public string CurrentVersion
    {
        get
        {
            // 1. 已安装目录的版本标记（最准）
            if (IsInstalled)
            {
                var marker = Path.Combine(InstallDirectory, "portable_config", ".vanta-version");
                if (File.Exists(marker))
                {
                    try
                    {
                        var v = File.ReadAllText(marker).Trim();
                        if (!string.IsNullOrWhiteSpace(v))
                        {
                            return v;
                        }
                    }
                    catch { }
                }
            }

            // 2. 会话中的包扫描结果（兼容未安装但扫描过包目录）
            if (!string.IsNullOrWhiteSpace(_session.ScanResult?.UnifiedVersion))
            {
                return _session.ScanResult.UnifiedVersion!;
            }

            // 3. 兜底 0.0.0：无法确定时按“最旧”处理，比较结果会提示有新版本
            return "0.0.0";
        }
    }

    // ---- mpv 调节 ----

    /// <summary>mpv 配置分组</summary>
    public ObservableCollection<MpvGroupItem> MpvGroups { get; } = [];

    /// <summary>是否有未保存的 mpv 修改</summary>
    [ObservableProperty]
    private bool _mpvConfigModified;

    /// <summary>是否显示 mpv 调节区（需已安装）</summary>
    public bool ShowMpvConfig => IsInstalled;

    // ---- 增量包下载（aria2）----

    /// <summary>可下载资产列表</summary>
    public ObservableCollection<DownloadAssetItem> DownloadItems { get; } = [];

    /// <summary>下载保存目录</summary>
    [ObservableProperty]
    private string _downloadDirectory = string.Empty;

    /// <summary>是否正在下载</summary>
    [ObservableProperty]
    private bool _isDownloading;

    /// <summary>下载总体进度（0~100）</summary>
    [ObservableProperty]
    private int _downloadPercent;

    /// <summary>是否有可下载项</summary>
    public bool HasDownloadItems => DownloadItems.Count > 0;

    /// <summary>是否有选中项</summary>
    public bool CanDownload => DownloadItems.Any(d => d.IsSelected && !d.Exists) && !IsDownloading;

    /// <summary>下载是否可停止</summary>
    public bool CanStop => IsDownloading;

    // ---- 镜像选择 ----

    /// <summary>镜像选项（下拉用）</summary>
    public ObservableCollection<DownloadMirror> MirrorOptions { get; } = [];

    /// <summary>镜像下拉当前选中项</summary>
    [ObservableProperty]
    private DownloadMirror? _selectedMirror;

    /// <summary>是否正在检测镜像</summary>
    [ObservableProperty]
    private bool _isProbingMirrors;

    /// <summary>镜像检测结果文本</summary>
    [ObservableProperty]
    private string _mirrorStatus = "未检测。";

    /// <summary>逐镜像测速结果（供列表展示）</summary>
    public ObservableCollection<MirrorProbeService.ProbeResult> MirrorProbeResults { get; } = [];

    /// <summary>最近一次探测到的可用镜像（按速度排序）</summary>
    private List<MirrorProbeService.ProbeResult> _probedMirrors = [];

    /// <summary>下载取消令牌（暂停/停止用）</summary>
    private CancellationTokenSource? _downloadCts;


    /// <summary>是否显示镜像区（有可下载项时）</summary>
    public bool ShowMirrorOptions => HasDownloadItems;

    /// <summary>下载状态总文本</summary>
    public string DownloadSummary =>
        DownloadItems.Count == 0
            ? "点击“检查更新”后可列出可下载的增量包。"
            : $"共 {DownloadItems.Count} 个资产，选中 {DownloadItems.Count(d => d.IsSelected && !d.Exists)} 个待下载 · 保存到 {DownloadDirectory}";

    private List<MpvOption> _mpvAllOptions = [];
    private string? _mpvInitialContent;
    private bool _mpvLoaded;

    /// <summary>mpv.conf 路径</summary>
    private string MpvConfigPath =>
        IsInstalled ? Path.Combine(InstallDirectory, "portable_config", "mpv.conf") : string.Empty;

    public SettingsViewModel(AppSession session)
    {
        _session = session;

        // 镜像下拉：自动检测 + 各镜像
        MirrorOptions.Add(new DownloadMirror("auto", "自动检测（推荐）", null));
        foreach (var m in MirrorRegistry.All)
        {
            MirrorOptions.Add(m);
        }
        SelectedMirror = MirrorOptions[0];
    }

    /// <summary>页面激活时刷新（检测安装 + 备份列表 + 缓存统计）</summary>
    public void Refresh()
    {
        // 指定目录存在但已无效（如刚卸载残留）时不采纳，兜底从程序目录向上找可用安装
        var detected = InstallationDetector.Detect(_session.InstallDirectory);
        if (detected is not { IsValid: true })
        {
            detected = InstallationDetector.Detect();
        }
        Installation = detected;
        if (detected is { IsValid: true })
        {
            _ = LoadDetailsAsync(detected);
        }

        RefreshBackups();
        RefreshCacheStats();
        if (!_mpvLoaded)
        {
            LoadMpvSettings();
        }
        OnPropertyChanged(nameof(IsInstalled));
        OnPropertyChanged(nameof(IsVanta));
        OnPropertyChanged(nameof(StatusTitle));
        OnPropertyChanged(nameof(InstallDirectory));
        OnPropertyChanged(nameof(VersionLine));
        OnPropertyChanged(nameof(SizeText));
        OnPropertyChanged(nameof(ConfigDirectory));
        OnPropertyChanged(nameof(BackupDirectory));
        OnPropertyChanged(nameof(CanRegister));
        OnPropertyChanged(nameof(ShowMpvConfig));
    }

    /// <summary>加载 mpv.conf 配置项（仅首次/恢复时）</summary>
    private void LoadMpvSettings()
    {
        _mpvAllOptions = MpvSettingsSchema.Build();
        var conf = MpvConfigPath;
        if (File.Exists(conf))
        {
            MpvConfigService.LoadOptions(conf, _mpvAllOptions);
            _mpvInitialContent = File.ReadAllText(conf, System.Text.Encoding.UTF8);
        }
        else
        {
            _mpvInitialContent = null;
        }

        MpvGroups.Clear();
        foreach (var group in _mpvAllOptions.GroupBy(o => o.Group))
        {
            var gi = new MpvGroupItem { Name = group.Key };
            foreach (var option in group)
            {
                var item = new MpvOptionItem(option);
                item.PropertyChanged += OnMpvItemPropertyChanged;
                gi.Options.Add(item);
            }
            MpvGroups.Add(gi);
        }
        _mpvLoaded = true;
        MpvConfigModified = false;
    }

    /// <summary>更新下载目录默认值（包目录优先）</summary>
    private void EnsureDownloadDirectory()
    {
        if (!string.IsNullOrWhiteSpace(DownloadDirectory))
        {
            return;
        }
        DownloadDirectory = !string.IsNullOrWhiteSpace(_session.SourceDirectory)
            ? _session.SourceDirectory
            : AppContext.BaseDirectory;
    }

    /// <summary>检查更新成功后填充可下载资产</summary>
    private void PopulateDownloadItems(UpdateService.UpdateInfo info)
    {
        EnsureDownloadDirectory();
        DownloadItems.Clear();

        foreach (var asset in info.Assets.OrderBy(a => a.Name))
        {
            var full = Path.Combine(DownloadDirectory, asset.Name);
            var exists = File.Exists(full) && new FileInfo(full).Length == asset.Size;
            DownloadItems.Add(new DownloadAssetItem
            {
                Asset = asset,
                Exists = exists,
                Status = exists ? "已存在" : "等待",
                IsSelected = !exists,
            });
        }

        OnPropertyChanged(nameof(HasDownloadItems));
        OnPropertyChanged(nameof(CanDownload));
        OnPropertyChanged(nameof(DownloadSummary));
        OnPropertyChanged(nameof(ShowMirrorOptions));
    }

    /// <summary>选择下载目录</summary>
    [RelayCommand]
    private void ChooseDownloadDirectory()
    {
        var dlg = new OpenFolderDialog
        {
            Title = "选择增量包保存目录",
            Multiselect = false,
        };
        if (dlg.ShowDialog() == true)
        {
            DownloadDirectory = dlg.FolderName;
            OnPropertyChanged(nameof(DownloadSummary));
        }
    }

    /// <summary>镜像可用性检测</summary>
    [RelayCommand]
    private async Task ProbeMirrorsAsync()
    {
        if (IsProbingMirrors)
        {
            return;
        }

        // 用第一个待下载资产做探测 URL
        var asset = DownloadItems.FirstOrDefault(d => !d.Exists)?.Asset;
        if (asset is null)
        {
            MirrorStatus = "没有待下载资产，无法检测。";
            return;
        }

        IsProbingMirrors = true;
        MirrorStatus = "正在测试连通性与下载速度…";
        try
        {
            var results = await MirrorProbeService.ProbeAsync(
                asset.Url,
                onProgress: msg => DispatcherInvoke(() => MirrorStatus = msg));
            _probedMirrors = results.ToList();

            MirrorProbeResults.Clear();
            foreach (var r in results)
            {
                MirrorProbeResults.Add(r);
            }

            var available = results.Where(r => r.IsAvailable).ToList();
            var fastest = available
                .OrderByDescending(r => r.SpeedBytesPerSec)
                .FirstOrDefault();
            MirrorStatus = available.Count > 0
                ? $"测试完成：可用 {available.Count}/{results.Count} 个，最快 {fastest!.Mirror.Name}（{fastest.SpeedText}）"
                : "测试完成：全部镜像均不可用";
        }
        catch (Exception ex)
        {
            MirrorStatus = $"测试失败：{ex.Message}";
        }
        finally
        {
            OnPropertyChanged(nameof(MirrorProbeResults));
            IsProbingMirrors = false;
        }
    }

    /// <summary>IsDownloading 变化时刷新相关按钮状态</summary>
    partial void OnIsDownloadingChanged(bool value)
    {
        OnPropertyChanged(nameof(CanStop));
        OnPropertyChanged(nameof(CanDownload));
        OnPropertyChanged(nameof(DownloadSummary));
    }

    /// <summary>开始下载选中资产（顺序下载，aria2 多线程）</summary>
    [RelayCommand]
    private async Task StartDownloadAsync()
    {
        if (IsDownloading)
        {
            return;
        }

        var targets = DownloadItems.Where(d => d.IsSelected && !d.Exists).ToList();
        if (targets.Count == 0)
        {
            return;
        }

        IsDownloading = true;
        OperationMessage = null;
        DownloadPercent = 0;
        OnPropertyChanged(nameof(CanStop));
        OnPropertyChanged(nameof(CanDownload));

        _downloadCts = new CancellationTokenSource();
        var ct = _downloadCts.Token;

        try
        {
            var aria2 = new Aria2Service();
            await aria2.LocateAsync();

            // 确定用户选定的下载镜像（单选，不自动降级）
            DownloadMirror chosenMirror;
            if (SelectedMirror?.Id == "auto")
            {
                var fastest = _probedMirrors
                    .Where(r => r.IsAvailable && !r.Mirror.IsOfficial)
                    .OrderByDescending(r => r.SpeedBytesPerSec)
                    .FirstOrDefault();
                chosenMirror = fastest?.Mirror ?? MirrorRegistry.Find("official")!;
            }
            else
            {
                chosenMirror = SelectedMirror ?? MirrorRegistry.Find("official")!;
            }

            OperationMessage = $"将使用镜像：{chosenMirror.Name}。";
            OnPropertyChanged(nameof(DownloadSummary));

            for (int i = 0; i < targets.Count; i++)
            {
                var item = targets[i];
                if (!item.IsSelected || item.Exists)
                {
                    continue;
                }

                item.Status = "下载中 0%";
                item.Progress = 0;
                OnPropertyChanged(nameof(CanDownload));

                void OnProgress(string _, int pct)
                {
                    DispatcherInvoke(() =>
                    {
                        item.Status = $"下载中 {pct}%";
                        item.Progress = pct;
                        DownloadPercent = (int)((i + pct / 100.0) * 100 / targets.Count);
                        OnPropertyChanged(nameof(DownloadPercent));
                    });
                }

                aria2.ProgressChanged += OnProgress;
                try
                {
                    await aria2.DownloadWithMirrorAsync(
                        chosenMirror,
                        item.Asset.Url,
                        DownloadDirectory,
                        item.Name,
                        ct: ct);
                    item.Exists = true;
                    item.Status = "完成";
                    item.Progress = 100;
                }
                catch (OperationCanceledException)
                {
                    // 用户停止：当前项标记"已停止"，其余不再继续
                    item.Status = "已停止";
                    OnPropertyChanged(nameof(DownloadPercent));
                    return;
                }
                catch (Exception ex)
                {
                    item.Status = $"失败：{ex.Message}";
                }
                finally
                {
                    aria2.ProgressChanged -= OnProgress;
                }
            }

            DownloadPercent = 100;
            OperationMessage = $"下载完成（镜像：{chosenMirror.Name}）。";
        }
        catch (OperationCanceledException)
        {
            // 定位阶段取消
        }
        catch (Exception ex)
        {
            OperationMessage = $"下载失败：{ex.Message}";
        }
        finally
        {
            IsDownloading = false;
            OnPropertyChanged(nameof(CanDownload));
            OnPropertyChanged(nameof(CanStop));
        }
    }

    /// <summary>
    /// 停止下载：取消全部任务，并删除未完成文件的残留（部分文件 + .aria2 控制文件），
    /// 下次重新下载为全新开始（不做不可靠的断点续传）。
    /// </summary>
    [RelayCommand]
    private void StopDownload()
    {
        if (!IsDownloading)
        {
            return;
        }

        _downloadCts?.Cancel();
        _downloadCts = null;

        // 删除未完成选中项的部分文件与 .aria2 控制文件（真正停止，避免残留被误判为完整）
        foreach (var d in DownloadItems.Where(d => d.IsSelected && !d.Exists))
        {
            TryDelete(Path.Combine(DownloadDirectory, d.Name));
            TryDelete(Path.Combine(DownloadDirectory, d.Name + ".aria2"));
            d.Status = "等待";
            d.Progress = -1;
        }

        DownloadPercent = 0;
        OnPropertyChanged(nameof(DownloadPercent));
        OnPropertyChanged(nameof(CanStop));
        OnPropertyChanged(nameof(CanDownload));
        OperationMessage = "下载已停止，残留已清理；再次开始将全新下载。";
    }

    /// <summary>安全删除文件（忽略占用/不存在）</summary>
    private static void TryDelete(string path)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        catch { }
    }

    private void OnMpvItemPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName is nameof(MpvOptionItem.CurrentValue) or nameof(MpvOptionItem.IsModified))
        {
            MpvConfigModified = MpvGroups.SelectMany(g => g.Options).Any(o => o.IsModified);
        }
    }

    /// <summary>在 UI 线程执行操作（供后台任务回调）</summary>
    private static void DispatcherInvoke(Action action)
    {
        var dispatcher = Application.Current?.Dispatcher;
        if (dispatcher is null || dispatcher.CheckAccess())
        {
            action();
        }
        else
        {
            dispatcher.Invoke(action);
        }
    }

    /// <summary>保存 mpv 设置（备份 + 写回）</summary>
    [RelayCommand]
    private void SaveMpvSettings()
    {
        if (!IsInstalled)
        {
            return;
        }

        var conf = MpvConfigPath;
        if (!File.Exists(conf))
        {
            OperationMessage = "未找到 mpv.conf，无法保存。";
            return;
        }

        var backup = MpvConfigService.Backup(conf);

        // geometry 与自动适配联动：固定分辨率停用 autofit-smaller，原始大小恢复
        var forceCommented = new List<string>();
        var forceActive = new List<string>();
        var geo = _mpvAllOptions.FirstOrDefault(o => o.Key == "geometry");
        if (geo is not null)
        {
            if (string.IsNullOrEmpty(geo.CurrentValue))
            {
                forceCommented.Add("geometry");
                forceActive.Add("autofit-smaller");
            }
            else
            {
                forceActive.Add("geometry");
                forceCommented.Add("autofit-smaller");
            }
        }

        try
        {
            MpvConfigService.Apply(conf, _mpvAllOptions, forceCommented, forceActive);
            OperationMessage = backup is null
                ? "已保存 mpv.conf，重启 mpv 后生效。"
                : $"已保存 mpv.conf（备份 {Path.GetFileName(backup)}），重启 mpv 后生效。";
            MpvConfigModified = false;
        }
        catch (Exception ex)
        {
            OperationMessage = $"保存失败：{ex.Message}";
        }
    }

    /// <summary>恢复为初始 mpv.conf 设置</summary>
    [RelayCommand]
    private void RestoreMpvDefaults()
    {
        if (!IsInstalled || _mpvInitialContent is null)
        {
            return;
        }

        var confirm = MessageBox.Show(
            "确定恢复 mpv.conf 为初始设置吗？\n当前修改将被还原（会先备份一份）。",
            "Vanta Installer",
            MessageBoxButton.YesNo,
            MessageBoxImage.Warning);
        if (confirm != MessageBoxResult.Yes)
        {
            return;
        }

        try
        {
            var conf = MpvConfigPath;
            MpvConfigService.Backup(conf);
            File.WriteAllText(conf, _mpvInitialContent, System.Text.Encoding.UTF8);
            _mpvLoaded = false;
            LoadMpvSettings();
            OperationMessage = "已恢复为初始 mpv.conf 设置。";
        }
        catch (Exception ex)
        {
            OperationMessage = $"恢复失败：{ex.Message}";
        }
    }

    /// <summary>后台填充版本与体积</summary>
    private async Task LoadDetailsAsync(InstallationDetector.InstallationInfo info)
    {
        try
        {
            var full = await InstallationDetector.EnrichAsync(info);
            if (Installation?.Directory == info.Directory)
            {
                Installation = full;
                OnPropertyChanged(nameof(VersionLine));
                OnPropertyChanged(nameof(SizeText));
            }
        }
        catch { }
    }

    /// <summary>刷新备份列表</summary>
    private void RefreshBackups()
    {
        Backups.Clear();
        if (IsInstalled)
        {
            foreach (var b in ConfigManager.ListBackups(InstallDirectory))
            {
                Backups.Add(b);
            }
        }
        OnPropertyChanged(nameof(HasBackups));
    }

    /// <summary>刷新缓存统计</summary>
    private void RefreshCacheStats()
    {
        CacheStats = IsInstalled ? CacheService.GetCacheStats(InstallDirectory) : null;
        OnPropertyChanged(nameof(CacheSizeText));
        OnPropertyChanged(nameof(CacheDetailText));
    }

    // ============ 启动 / 目录 ============

    /// <summary>启动 mpv</summary>
    [RelayCommand]
    private void LaunchMpv()
    {
        if (!IsInstalled)
        {
            return;
        }

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = Path.Combine(InstallDirectory, "mpv.exe"),
                WorkingDirectory = InstallDirectory,
                UseShellExecute = true,
            });
        }
        catch (Exception ex)
        {
            OperationMessage = $"启动失败：{ex.Message}";
        }
    }

    /// <summary>打开安装目录</summary>
    [RelayCommand]
    private void OpenInstallDir() => OpenDirectory(InstallDirectory);

    /// <summary>打开配置目录</summary>
    [RelayCommand]
    private void OpenConfigDir() => OpenDirectory(ConfigDirectory);

    /// <summary>打开备份目录</summary>
    [RelayCommand]
    private void OpenBackupDir() => OpenDirectory(BackupDirectory);

    private void OpenDirectory(string path)
    {
        if (string.IsNullOrEmpty(path) || !Directory.Exists(path))
        {
            OperationMessage = $"目录不存在：{path}";
            return;
        }

        try
        {
            Process.Start("explorer.exe", $"\"{path}\"");
        }
        catch (Exception ex)
        {
            OperationMessage = $"打开目录失败：{ex.Message}";
        }
    }

    // ============ 文件关联 ============

    /// <summary>注册文件关联（提权调用 mpv-install.bat）</summary>
    [RelayCommand]
    private void RegisterAssociations() =>
        RunBatElevated(Path.Combine(InstallDirectory, "installer", "mpv-install.bat"), "注册文件关联");

    /// <summary>取消文件关联（提权调用 mpv-uninstall.bat）</summary>
    [RelayCommand]
    private void UnregisterAssociations() =>
        RunBatElevated(Path.Combine(InstallDirectory, "installer", "mpv-uninstall.bat"), "取消文件关联");

    private void RunBatElevated(string? batPath, string actionName)
    {
        if (string.IsNullOrEmpty(batPath) || !File.Exists(batPath))
        {
            OperationMessage = $"未找到 {batPath}";
            return;
        }

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/c \"\"{batPath}\"\"",
                WorkingDirectory = InstallDirectory,
                UseShellExecute = true,
                Verb = "runas",
            });
        }
        catch (Exception ex)
        {
            OperationMessage = $"{actionName}失败：{ex.Message}";
        }
    }

    // ============ 配置备份 / 恢复 ============

    /// <summary>手动备份配置</summary>
    [RelayCommand]
    private void BackupNow()
    {
        if (!IsInstalled)
        {
            return;
        }

        try
        {
            var path = ConfigManager.CreateBackup(InstallDirectory);
            OperationMessage = path is null
                ? "未找到 portable_config，无法备份。"
                : $"已备份到：{path}";
            RefreshBackups();
        }
        catch (Exception ex)
        {
            OperationMessage = $"备份失败：{ex.Message}";
        }
    }

    /// <summary>恢复选中备份</summary>
    [RelayCommand]
    private void RestoreBackup(ConfigManager.BackupEntry? entry)
    {
        if (entry is null || !IsInstalled)
        {
            return;
        }

        var confirm = MessageBox.Show(
            $"确定恢复到 {entry.Stamp} 的配置吗？\n当前配置会先自动备份。",
            "Vanta Installer",
            MessageBoxButton.YesNo,
            MessageBoxImage.Warning);
        if (confirm != MessageBoxResult.Yes)
        {
            return;
        }

        try
        {
            var dest = ConfigManager.Restore(InstallDirectory, entry.Path);
            OperationMessage = dest is null ? "恢复失败。" : $"已恢复到：{dest}";
            RefreshBackups();
        }
        catch (Exception ex)
        {
            OperationMessage = $"恢复失败：{ex.Message}";
        }
    }

    // ============ 检查更新 ============

    /// <summary>检查更新</summary>
    [RelayCommand]
    private async Task CheckUpdateAsync()
    {
        if (IsCheckingUpdate)
        {
            return;
        }

        IsCheckingUpdate = true;
        UpdateStatus = "正在检查…";
        try
        {
            var info = await UpdateService.CheckLatestAsync();
            if (info is null)
            {
                UpdateStatus = "检查失败：无法获取最新版本。";
                return;
            }

            LatestVersion = info.LatestVersion;
            ReleaseUrl = info.ReleaseUrl;
            HasUpdate = info.HasNewer(CurrentVersion);

            UpdateStatus = HasUpdate
                ? $"发现新版本：{info.LatestVersion}（当前 {CurrentVersion}）"
                : $"已是最新版本：{info.LatestVersion}";

            // 填充可下载资产
            PopulateDownloadItems(info);
        }
        catch (Exception ex)
        {
            UpdateStatus = $"检查失败：{ex.Message}";
        }
        finally
        {
            IsCheckingUpdate = false;
        }
    }

    /// <summary>打开 Release 页面</summary>
    [RelayCommand]
    private void OpenReleasePage()
    {
        if (string.IsNullOrEmpty(ReleaseUrl))
        {
            return;
        }

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = ReleaseUrl,
                UseShellExecute = true,
            });
        }
        catch (Exception ex)
        {
            OperationMessage = $"打开页面失败：{ex.Message}";
        }
    }

    // ============ 缓存清理 ============

    /// <summary>清理缓存</summary>
    [RelayCommand]
    private void CleanCache()
    {
        if (!IsInstalled)
        {
            return;
        }

        var confirm = MessageBox.Show(
            "确定清理播放器缓存吗？\n包括缩略图缓存、历史记录等，不影响配置。",
            "Vanta Installer",
            MessageBoxButton.YesNo,
            MessageBoxImage.Question);
        if (confirm != MessageBoxResult.Yes)
        {
            return;
        }

        try
        {
            var freed = CacheService.CleanCache(InstallDirectory);
            OperationMessage = $"已清理缓存，释放 {VantaPackage.FormatSize(freed)}。";
            RefreshCacheStats();
        }
        catch (Exception ex)
        {
            OperationMessage = $"清理失败：{ex.Message}";
        }
    }
}
