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

    /// <summary>状态消息（信息栏 Message；未检测到安装时提示先安装）</summary>
    public string StatusMessage => IsInstalled
        ? InstallDirectory
        : "请先使用“安装”模式安装 MPV Vanta Edition。";

    /// <summary>版本行</summary>
    public string VersionLine => Installation?.VersionLine ?? string.Empty;

    /// <summary>占用空间</summary>
    public string SizeText => Installation?.SizeText ?? string.Empty;

    /// <summary>用户手动指定的已安装 mpv 位置（持久化，优先识别）</summary>
    public string ManualMpvPath => InstallLocationStore.GetManualMpvPath() ?? string.Empty;

    /// <summary>是否有手动指定位置</summary>
    public bool HasManualPath => !string.IsNullOrWhiteSpace(ManualMpvPath);

    /// <summary>是否显示"清除手动指定"（已检测到安装且存在手动指定时）</summary>
    public bool ShowManualClear => IsInstalled && HasManualPath;

    /// <summary>配置目录路径（mpv 调节、缓存清理等操作目标）</summary>
    public string ConfigDirectory => Path.Combine(InstallDirectory, "portable_config");

    /// <summary>用户手动指定的配置备份目录（持久化，优先于安装目录下 backup\）</summary>
    public string ManualBackupPath => InstallLocationStore.GetManualBackupPath() ?? string.Empty;

    /// <summary>是否有手动指定备份目录</summary>
    public bool HasManualBackupPath => !string.IsNullOrWhiteSpace(ManualBackupPath);

    /// <summary>是否显示"清除备份指定"（存在手动指定备份目录时）</summary>
    public bool ShowBackupClear => HasManualBackupPath;

    /// <summary>备份目录路径：手动指定优先，否则用安装目录下 backup\</summary>
    public string BackupDirectory => HasManualBackupPath
        ? ManualBackupPath
        : Path.Combine(InstallDirectory, "backup");

    /// <summary>是否可注册多实例关联（检测到有效 mpv.exe）</summary>
    public bool CanRegisterMulti =>
        IsInstalled && AssociationService.CanRegister(InstallDirectory, PlaybackMode.MultiInstance);

    /// <summary>是否可注册单实例关联（检测到有效 mpv.exe 与 umpv.exe）</summary>
    public bool CanRegisterSingle =>
        IsInstalled && AssociationService.CanRegister(InstallDirectory, PlaybackMode.SingleInstance);

    /// <summary>多实例入口是否已为当前用户注册</summary>
    public bool IsMultiAssociationRegistered =>
        AssociationService.IsRegistered(PlaybackMode.MultiInstance);

    /// <summary>单实例入口是否已为当前用户注册</summary>
    public bool IsSingleAssociationRegistered =>
        AssociationService.IsRegistered(PlaybackMode.SingleInstance);

    /// <summary>文件关联实时状态</summary>
    public string AssociationStatus =>
        $"多实例：{(IsMultiAssociationRegistered ? "已注册" : "未注册")}　　单实例：{(IsSingleAssociationRegistered ? "已注册" : "未注册")}";

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

    /// <summary>文件关联卡片内的就地操作结果</summary>
    [ObservableProperty]
    private string? _associationMessage;

    /// <summary>本次文件关联操作的阶段日志</summary>
    public ObservableCollection<string> AssociationLog { get; } = [];

    /// <summary>是否已有文件关联阶段日志</summary>
    public bool HasAssociationLog => AssociationLog.Count > 0;

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

    // ---- uosc 主题 ----

    /// <summary>从共享 JSON 注册表加载的主题色板。</summary>
    public ObservableCollection<UoscThemePalette> ThemeOptions { get; } = [];

    /// <summary>主题下拉当前选中项。</summary>
    [ObservableProperty]
    private UoscThemePalette? _selectedTheme;

    /// <summary>主题卡片内操作结果。</summary>
    [ObservableProperty]
    private string? _themeMessage;

    /// <summary>已安装时显示主题卡片；注册表异常会在卡片内提示。</summary>
    public bool ShowThemeSettings => IsInstalled;

    // ---- 方向键快进（evafast）----

    /// <summary>无字幕时的快进倍速上限</summary>
    [ObservableProperty]
    private double _evafastSpeedCap = 3;

    /// <summary>有字幕时的快进倍速上限</summary>
    [ObservableProperty]
    private double _evafastSubsSpeedCap = 1.5;

    /// <summary>是否启用"显示字幕时降低倍速上限"</summary>
    [ObservableProperty]
    private bool _evafastSubsLimit = true;

    /// <summary>加载时的 evafast 初始值（判断是否有未保存修改）</summary>
    private double _evafastInitialSpeedCap = 3;
    private double _evafastInitialSubsSpeedCap = 1.5;
    private bool _evafastInitialSubsLimit = true;

    /// <summary>evafast 设置是否有未保存修改</summary>
    public bool EvafastModified =>
        !EvafastConfigService.SameValues(
            EvafastSpeedCap, EvafastSubsSpeedCap, EvafastSubsLimit,
            _evafastInitialSpeedCap, _evafastInitialSubsSpeedCap, _evafastInitialSubsLimit);

    /// <summary>保存按钮可用：mpv.conf 或 evafast 任一有修改</summary>
    public bool CanSaveMpvSettings => MpvConfigModified || EvafastModified;

    /// <summary>evafast 设置是否已加载（避免重复读盘）</summary>
    private bool _evafastLoaded;

    /// <summary>evafast 设置操作结果。</summary>
    [ObservableProperty]
    private string? _evafastMessage;

    partial void OnEvafastSpeedCapChanged(double value) => RefreshEvafastModified();

    partial void OnEvafastSubsSpeedCapChanged(double value) => RefreshEvafastModified();

    partial void OnEvafastSubsLimitChanged(bool value) => RefreshEvafastModified();

    /// <summary>刷新 evafast 修改状态与保存按钮可用性</summary>
    private void RefreshEvafastModified()
    {
        OnPropertyChanged(nameof(EvafastModified));
        OnPropertyChanged(nameof(CanSaveMpvSettings));
    }

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

    /// <summary>当前下载总速度（字节/秒）</summary>
    [ObservableProperty]
    private double _downloadSpeedBytesPerSecond;

    /// <summary>当前下载总速度文本</summary>
    public string DownloadSpeedText => Aria2Service.FormatSpeed(DownloadSpeedBytesPerSecond);

    private int _downloadTotalCount;
    private int _downloadCompletedCount;
    private int _downloadFailureCount;
    private UpdateService.UpdateInfo? _latestReleaseInfo;

    /// <summary>是否有可下载项</summary>
    public bool HasDownloadItems => DownloadItems.Count > 0;

    /// <summary>是否有选中项</summary>
    public bool CanDownload => DownloadItems.Any(d => d.IsSelected && !d.Exists && !d.IsQueued);

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
            : $"共 {DownloadItems.Count} 个资产，选中 {DownloadItems.Count(d => d.IsSelected && !d.Exists)} 个待下载，队列 {DownloadItems.Count(d => d.IsQueued)} · 保存到 {DownloadDirectory}";

    private List<MpvOption> _mpvAllOptions = [];
    private string? _mpvInitialContent;
    private bool _mpvLoaded;

    /// <summary>mpv.conf 路径</summary>
    private string MpvConfigPath =>
        IsInstalled ? Path.Combine(ConfigDirectory, "mpv.conf") : string.Empty;

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
        // 优先全局检测（手动指定 > 记忆位置 > 向上查找）；会话目标目录作为兜底
        var detected = InstallationDetector.Detect();
        if (detected is not { IsValid: true } && !string.IsNullOrWhiteSpace(_session.InstallDirectory))
        {
            detected = InstallationDetector.Detect(_session.InstallDirectory);
        }
        Installation = detected;
        if (detected is { IsValid: true })
        {
            _ = LoadDetailsAsync(detected);
        }

        RefreshBackups();
        RefreshCacheStats();
        LoadUoscThemes();
        LoadEvafastSettings();
        if (!_mpvLoaded)
        {
            LoadMpvSettings();
        }
        OnPropertyChanged(nameof(IsInstalled));
        OnPropertyChanged(nameof(IsVanta));
        OnPropertyChanged(nameof(StatusTitle));
        OnPropertyChanged(nameof(StatusMessage));
        OnPropertyChanged(nameof(InstallDirectory));
        OnPropertyChanged(nameof(VersionLine));
        OnPropertyChanged(nameof(SizeText));
        OnPropertyChanged(nameof(ConfigDirectory));
        OnPropertyChanged(nameof(ManualBackupPath));
        OnPropertyChanged(nameof(HasManualBackupPath));
        OnPropertyChanged(nameof(ShowBackupClear));
        OnPropertyChanged(nameof(BackupDirectory));
        OnPropertyChanged(nameof(CanRegisterMulti));
        OnPropertyChanged(nameof(CanRegisterSingle));
        RefreshAssociationState();
        OnPropertyChanged(nameof(ShowMpvConfig));
        OnPropertyChanged(nameof(ShowThemeSettings));
        OnPropertyChanged(nameof(ManualMpvPath));
        OnPropertyChanged(nameof(HasManualPath));
        OnPropertyChanged(nameof(ShowManualClear));
    }

    /// <summary>指定已安装的 mpv 位置（Vanta 或任意 mpv）</summary>
    [RelayCommand]
    private void ChooseManualPath()
    {
        var dlg = new OpenFolderDialog
        {
            Title = "指定已安装的 mpv 位置",
            Multiselect = false,
        };
        if (dlg.ShowDialog() == true)
        {
            InstallLocationStore.SaveManualMpvPath(dlg.FolderName);
            Refresh();
        }
    }

    /// <summary>清除手动指定，恢复自动检测</summary>
    [RelayCommand]
    private void ClearManualPath()
    {
        InstallLocationStore.SaveManualMpvPath(null);
        Refresh();
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

    /// <summary>加载共享主题注册表和 uosc.conf 当前选择。</summary>
    private void LoadUoscThemes()
    {
        ThemeOptions.Clear();
        SelectedTheme = null;
        if (!IsInstalled)
        {
            ThemeMessage = null;
            return;
        }

        try
        {
            var registry = UoscThemeService.LoadRegistry(ConfigDirectory);
            foreach (var palette in registry.Palettes)
            {
                ThemeOptions.Add(palette);
            }

            var selectedId = UoscThemeService.ReadSelectedTheme(ConfigDirectory, registry.DefaultId);
            SelectedTheme = ThemeOptions.FirstOrDefault(
                p => p.Id.Equals(selectedId, StringComparison.OrdinalIgnoreCase))
                ?? ThemeOptions.FirstOrDefault(
                    p => p.Id.Equals(registry.DefaultId, StringComparison.OrdinalIgnoreCase));
            ThemeMessage = SelectedTheme is null
                ? "主题注册表中没有可用色板。"
                : $"当前：{SelectedTheme.DisplayName}（{SelectedTheme.AccentDisplay}）";
        }
        catch (Exception ex)
        {
            ThemeMessage = $"主题加载失败：{ex.Message}";
        }

        ApplyUoscThemeCommand.NotifyCanExecuteChanged();
    }

    partial void OnSelectedThemeChanged(UoscThemePalette? value)
    {
        ApplyUoscThemeCommand.NotifyCanExecuteChanged();
    }

    private bool CanApplySelectedTheme() => IsInstalled && SelectedTheme is not null;

    /// <summary>把选中的主题 ID 写入 uosc.conf；所有色号继续由共享 JSON 提供。</summary>
    [RelayCommand(CanExecute = nameof(CanApplySelectedTheme))]
    private void ApplyUoscTheme()
    {
        if (SelectedTheme is null)
        {
            return;
        }

        try
        {
            var backup = UoscThemeService.ApplyTheme(ConfigDirectory, SelectedTheme.Id);
            ThemeMessage = $"已应用 {SelectedTheme.DisplayName}（{SelectedTheme.AccentDisplay}），备份：{Path.GetFileName(backup)}；重启 mpv 后生效。";
        }
        catch (Exception ex)
        {
            ThemeMessage = $"主题应用失败：{ex.Message}";
        }
    }

    /// <summary>加载 evafast（方向键快进）设置，仅首次/未加载时读取。</summary>
    private void LoadEvafastSettings()
    {
        if (_evafastLoaded || !IsInstalled)
        {
            return;
        }

        try
        {
            var settings = EvafastConfigService.Load(ConfigDirectory);
            // 先记录初始值，再赋值（赋值触发的 OnXxxChanged 会据此判断未修改）
            _evafastInitialSpeedCap = settings.SpeedCap;
            _evafastInitialSubsSpeedCap = settings.SubsSpeedCap;
            _evafastInitialSubsLimit = settings.SubsLimit;
            EvafastSpeedCap = settings.SpeedCap;
            EvafastSubsSpeedCap = settings.SubsSpeedCap;
            EvafastSubsLimit = settings.SubsLimit;
            _evafastLoaded = true;
            RefreshEvafastModified();
        }
        catch (Exception ex)
        {
            EvafastMessage = $"方向键快进设置加载失败：{ex.Message}";
        }
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
        _latestReleaseInfo = info;
        DownloadItems.Clear();

        foreach (var asset in info.Assets.OrderBy(a => a.Name))
        {
            var full = Path.Combine(DownloadDirectory, asset.Name);
            var exists = File.Exists(full) && new FileInfo(full).Length == asset.Size;
            var item = new DownloadAssetItem
            {
                Asset = asset,
                Exists = exists,
                Status = exists ? "已存在" : "等待",
                IsSelected = !exists,
            };
            item.PropertyChanged += OnDownloadItemPropertyChanged;
            DownloadItems.Add(item);
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

    /// <summary>切换保存目录后重新评估各下载项的存在状态。</summary>
    partial void OnDownloadDirectoryChanged(string value)
    {
        RefreshDownloadItemStates();
    }

    /// <summary>
    /// 按当前 DownloadDirectory 重新核对每个下载项：
    /// 旧目录里已下载完成的包在新目录下不存在时恢复为“等待 / 可勾选”，
    /// 新目录里已存在完整文件的包标记为“已存在”并取消勾选，
    /// 避免“换保存目录后旧目录的完成状态残留、无法再次下载”的问题。
    /// </summary>
    private void RefreshDownloadItemStates()
    {
        foreach (var item in DownloadItems)
        {
            // 正在传输中的项不打断（保存按钮在下载期间已禁用，正常不会出现）
            if (item.IsActive)
            {
                continue;
            }

            var full = Path.Combine(DownloadDirectory, item.Name);
            var exists = File.Exists(full) && new FileInfo(full).Length == item.Asset.Size;
            if (exists == item.Exists)
            {
                continue;
            }

            item.Exists = exists;
            if (exists)
            {
                // 新目录已有完整文件：标记已存在并取消勾选
                item.Status = "已存在";
                item.Progress = 100;
                item.IsQueued = false;
                item.IsSelected = false;
                item.SpeedBytesPerSecond = 0;
            }
            else
            {
                // 旧目录的完成状态失效：恢复为等待并重新勾选，允许再次下载
                item.Status = "等待";
                item.Progress = -1;
                item.IsQueued = false;
                item.IsSelected = true;
                item.SpeedBytesPerSecond = 0;
            }
        }

        OnPropertyChanged(nameof(CanDownload));
        OnPropertyChanged(nameof(DownloadSummary));
    }

    /// <summary>镜像可用性检测</summary>
    [RelayCommand]
    private async Task ProbeMirrorsAsync()
    {
        if (IsProbingMirrors)
        {
            return;
        }

        IsProbingMirrors = true;
        try
        {
            // 始终用最新正式 Release 的大体积包（优先 01 base）测速，
            // 避免小样本在采样窗口内提前 EOF、以及被当前勾选项或旧版本包影响。
            var latest = await UpdateService.CheckLatestAsync();
            _latestReleaseInfo = latest;
            var asset = latest is null ? null : UpdateService.FindProbeAsset(latest);
            if (asset is null)
            {
                MirrorStatus = "最新 Release 没有找到可用的测速样本包，无法检测。";
                return;
            }

            MirrorStatus = $"正在拉取最新 {asset.Name} 测试连通性与下载速度…";
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

    /// <summary>下载项选择变化时立即刷新开始按钮，使下载中追加任务可用。</summary>
    private void OnDownloadItemPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (sender is not DownloadAssetItem item)
        {
            return;
        }

        if (e.PropertyName == nameof(DownloadAssetItem.IsSelected))
        {
            // 已排队但尚未开始的项目取消勾选时，从队列移出；当前正在传输的项目不受影响。
            if (!item.IsSelected && item.IsQueued && !item.IsActive)
            {
                item.IsQueued = false;
                item.Status = "等待";
                item.Progress = -1;
                item.SpeedBytesPerSecond = 0;
            }

            OnPropertyChanged(nameof(CanDownload));
            OnPropertyChanged(nameof(DownloadSummary));
        }
    }

    partial void OnDownloadSpeedBytesPerSecondChanged(double value) => OnPropertyChanged(nameof(DownloadSpeedText));

    /// <summary>IsDownloading 变化时刷新相关按钮状态</summary>
    partial void OnIsDownloadingChanged(bool value)
    {
        OnPropertyChanged(nameof(CanStop));
        OnPropertyChanged(nameof(CanDownload));
        OnPropertyChanged(nameof(DownloadSummary));
    }

    /// <summary>把当前勾选项加入下载队列。</summary>
    private int QueueSelectedDownloads()
    {
        if (!IsDownloading)
        {
            _downloadTotalCount = 0;
            _downloadCompletedCount = 0;
            _downloadFailureCount = 0;
            DownloadSpeedBytesPerSecond = 0;
            DownloadPercent = 0;
        }

        var added = 0;
        foreach (var item in DownloadItems.Where(d => d.IsSelected && !d.Exists && !d.IsQueued))
        {
            item.IsQueued = true;
            item.Status = "排队中";
            item.Progress = 0;
            item.SpeedBytesPerSecond = 0;
            _downloadTotalCount++;
            added++;
        }

        OnPropertyChanged(nameof(CanDownload));
        OnPropertyChanged(nameof(DownloadSummary));
        return added;
    }

    /// <summary>刷新队列总体进度。</summary>
    private void RefreshDownloadPercent(DownloadAssetItem? active = null, int activePercent = 0)
    {
        if (_downloadTotalCount <= 0)
        {
            DownloadPercent = 0;
            return;
        }

        var activePart = active is null ? 0d : Math.Clamp(activePercent, 0, 100) / 100d;
        DownloadPercent = (int)Math.Clamp(
            (_downloadCompletedCount + activePart) * 100 / _downloadTotalCount,
            0,
            100);
    }

    /// <summary>开始下载当前队列；下载中再次点击会把新勾选项追加到队列。</summary>
    [RelayCommand(AllowConcurrentExecutions = true)]
    private async Task StartDownloadAsync()
    {
        var added = QueueSelectedDownloads();
        if (IsDownloading)
        {
            if (added > 0)
            {
                OperationMessage = $"已加入 {added} 个下载任务，当前任务完成后继续。";
            }
            return;
        }

        if (added == 0)
        {
            return;
        }

        IsDownloading = true;
        OperationMessage = null;
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

            OperationMessage = $"下载引擎：Aria2 Next {Aria2Service.EngineVersion}；镜像：{chosenMirror.Name}。";
            OnPropertyChanged(nameof(DownloadSummary));

            while (true)
            {
                var item = DownloadItems.FirstOrDefault(d => d.IsQueued && !d.Exists && !d.IsActive);
                if (item is null)
                {
                    break;
                }

                item.IsActive = true;
                item.Status = "下载中 0%";
                item.Progress = 0;

                void OnProgress(string _, int pct)
                {
                    DispatcherInvoke(() =>
                    {
                        item.Status = $"下载中 {pct}%";
                        item.Progress = pct;
                        RefreshDownloadPercent(item, pct);
                    });
                }

                void OnSpeed(string _, double speed)
                {
                    DispatcherInvoke(() =>
                    {
                        item.SpeedBytesPerSecond = speed;
                        DownloadSpeedBytesPerSecond = speed;
                    });
                }

                aria2.ProgressChanged += OnProgress;
                aria2.SpeedChanged += OnSpeed;
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
                    item.SpeedBytesPerSecond = 0;
                    _downloadCompletedCount++;
                    RefreshDownloadPercent();
                }
                catch (OperationCanceledException)
                {
                    // 用户停止：当前项标记"已停止"，其余不再继续
                    item.Status = "已停止";
                    throw;
                }
                catch (Exception ex)
                {
                    item.Status = $"失败：{ex.Message}";
                    item.SpeedBytesPerSecond = 0;
                    _downloadFailureCount++;
                    _downloadCompletedCount++;
                    RefreshDownloadPercent();
                }
                finally
                {
                    aria2.ProgressChanged -= OnProgress;
                    aria2.SpeedChanged -= OnSpeed;
                    item.IsActive = false;
                    item.IsQueued = false;
                    item.SpeedBytesPerSecond = 0;
                }
            }

            DownloadPercent = _downloadTotalCount > 0 ? 100 : 0;
            OperationMessage = _downloadFailureCount == 0
                ? $"下载队列完成（镜像：{chosenMirror.Name}）。"
                : $"下载队列完成，但有 {_downloadFailureCount} 个任务失败（镜像：{chosenMirror.Name}）。";
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
            foreach (var item in DownloadItems.Where(d => d.IsQueued && !d.IsActive && !d.Exists))
            {
                item.IsQueued = false;
                if (item.Status == "排队中")
                {
                    item.Status = "等待";
                }
            }

            DownloadSpeedBytesPerSecond = 0;
            IsDownloading = false;
            _downloadCts?.Dispose();
            _downloadCts = null;
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
        foreach (var d in DownloadItems.Where(d => (d.IsSelected || d.IsQueued || d.IsActive) && !d.Exists))
        {
            TryDelete(Path.Combine(DownloadDirectory, d.Name));
            TryDelete(Path.Combine(DownloadDirectory, d.Name + ".aria2"));
            if (!d.IsActive)
            {
                d.IsQueued = false;
                d.Status = "等待";
            }
            d.Progress = -1;
            d.SpeedBytesPerSecond = 0;
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
            OnPropertyChanged(nameof(CanSaveMpvSettings));
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

            // 方向键快进（evafast.conf）有修改时一并保存
            var savedParts = new List<string>();
            if (EvafastModified)
            {
                EvafastConfigService.Save(ConfigDirectory, new EvafastSettings
                {
                    SpeedCap = EvafastSpeedCap,
                    SubsSpeedCap = EvafastSubsSpeedCap,
                    SubsLimit = EvafastSubsLimit,
                });
                _evafastInitialSpeedCap = EvafastSpeedCap;
                _evafastInitialSubsSpeedCap = EvafastSubsSpeedCap;
                _evafastInitialSubsLimit = EvafastSubsLimit;
                savedParts.Add("方向键快进设置");
            }

            var baseMsg = backup is null
                ? "已保存 mpv.conf"
                : $"已保存 mpv.conf（备份 {Path.GetFileName(backup)}）";
            OperationMessage = savedParts.Count > 0
                ? $"{baseMsg} 与 {string.Join("、", savedParts)}，重启 mpv 后生效。"
                : $"{baseMsg}，重启 mpv 后生效。";
            MpvConfigModified = false;
            RefreshEvafastModified();
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
            foreach (var b in ConfigManager.ListBackups(BackupDirectory))
            {
                Backups.Add(b);
            }
        }
        OnPropertyChanged(nameof(HasBackups));
    }

    /// <summary>刷新缓存统计</summary>
    private void RefreshCacheStats()
    {
        CacheStats = IsInstalled ? CacheService.GetCacheStats(ConfigDirectory) : null;
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

    /// <summary>选择配置备份目录（持久化；立即备份/历史备份/恢复均跟随）</summary>
    [RelayCommand]
    private void ChooseBackupDirectory()
    {
        var dlg = new OpenFolderDialog
        {
            Title = "选择配置备份目录",
            Multiselect = false,
        };
        if (dlg.ShowDialog() == true)
        {
            InstallLocationStore.SaveManualBackupPath(dlg.FolderName);
            Refresh();
        }
    }

    /// <summary>清除手动指定备份目录，恢复安装目录下 backup\</summary>
    [RelayCommand]
    private void ClearBackupDirectory()
    {
        InstallLocationStore.SaveManualBackupPath(null);
        Refresh();
    }

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

    /// <summary>为当前用户注册多实例文件关联（指向 mpv.exe）</summary>
    [RelayCommand]
    private void RegisterMultiAssociations()
    {
        RunAssociationAction(PlaybackMode.MultiInstance, register: true);
    }

    /// <summary>为当前用户注册单实例文件关联（指向 umpv.exe）</summary>
    [RelayCommand]
    private void RegisterSingleAssociations()
    {
        RunAssociationAction(PlaybackMode.SingleInstance, register: true);
    }

    /// <summary>取消当前用户的多实例文件关联</summary>
    [RelayCommand]
    private void UnregisterMultiAssociations()
    {
        RunAssociationAction(PlaybackMode.MultiInstance, register: false);
    }

    /// <summary>取消当前用户的单实例文件关联</summary>
    [RelayCommand]
    private void UnregisterSingleAssociations()
    {
        RunAssociationAction(PlaybackMode.SingleInstance, register: false);
    }

    private void RunAssociationAction(PlaybackMode mode, bool register)
    {
        AssociationMessage = null;
        AssociationLog.Clear();
        OnPropertyChanged(nameof(HasAssociationLog));

        void AddAssociationStage(string message)
        {
            AssociationLog.Add($"{AssociationLog.Count + 1}. {message}");
            OnPropertyChanged(nameof(HasAssociationLog));
        }

        var result = register
            ? AssociationService.Register(InstallDirectory, mode, AddAssociationStage)
            : AssociationService.Unregister(mode, AddAssociationStage);
        AssociationMessage = result.Message;
        OperationMessage = result.Message;
        RefreshAssociationState();
    }

    private void RefreshAssociationState()
    {
        OnPropertyChanged(nameof(IsMultiAssociationRegistered));
        OnPropertyChanged(nameof(IsSingleAssociationRegistered));
        OnPropertyChanged(nameof(AssociationStatus));
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
            var path = ConfigManager.CreateBackup(ConfigDirectory, BackupDirectory);
            OperationMessage = path is null
                ? "未找到配置目录，无法备份。"
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
            var dest = ConfigManager.Restore(ConfigDirectory, BackupDirectory, entry.Path);
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
            _latestReleaseInfo = info;

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
            var freed = CacheService.CleanCache(ConfigDirectory);
            OperationMessage = $"已清理缓存，释放 {VantaPackage.FormatSize(freed)}。";
            RefreshCacheStats();
        }
        catch (Exception ex)
        {
            OperationMessage = $"清理失败：{ex.Message}";
        }
    }
}
