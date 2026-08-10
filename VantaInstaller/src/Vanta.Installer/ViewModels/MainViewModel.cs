using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Wpf.Ui.Controls;

namespace Vanta.Installer.ViewModels;

/// <summary>应用模式</summary>
public enum AppMode
{
    Home,
    Install,
    Uninstall,
    Settings,
}

/// <summary>
/// 主窗口视图模型：模式状态机 + 安装向导步骤
/// 模式：Home（仪表盘）/ Install（安装向导）/ Uninstall（卸载）/ Settings（设置）
/// </summary>
public partial class MainViewModel : ObservableObject
{
    private readonly AppSession _session;
    private readonly object[] _installPages;
    private readonly HomeViewModel _home;
    private readonly UninstallViewModel _uninstall;
    private readonly SettingsViewModel _settings;

    /// <summary>安装步骤指示</summary>
    public ObservableCollection<StepItem> InstallSteps { get; } = [];

    /// <summary>卸载步骤指示</summary>
    public ObservableCollection<StepItem> UninstallSteps { get; } = [];

    /// <summary>左侧导航项</summary>
    public ObservableCollection<NavItem> NavItems { get; } = [];

    /// <summary>当前模式</summary>
    [ObservableProperty]
    private AppMode _currentMode = AppMode.Home;

    /// <summary>当前内容页视图模型</summary>
    [ObservableProperty]
    private object _currentPage = null!;

    /// <summary>当前安装步骤索引</summary>
    [ObservableProperty]
    private int _currentStep;

    // ---- 面板可见性 ----
    public bool ShowNavItems => CurrentMode is AppMode.Home or AppMode.Settings;
    public bool ShowInstallSteps => CurrentMode == AppMode.Install;
    public bool ShowUninstallSteps => CurrentMode == AppMode.Uninstall;
    public bool ShowBottomBar => CurrentMode is AppMode.Install or AppMode.Uninstall or AppMode.Settings;
    public bool ShowNextButton => CurrentMode is AppMode.Install or AppMode.Uninstall;

    /// <summary>是否显示右侧横向步骤条（安装/卸载模式）</summary>
    public bool ShowSteps => CurrentMode is AppMode.Install or AppMode.Uninstall;

    /// <summary>当前模式的步骤集合（右侧步骤条用）</summary>
    public ObservableCollection<StepItem> CurrentSteps =>
        CurrentMode == AppMode.Uninstall ? UninstallSteps : InstallSteps;

    // ---- 底部按钮状态 ----
    public bool CanGoBack => CurrentMode switch
    {
        AppMode.Install => CurrentStep > 0 && CurrentPage is not InstallViewModel { IsRunning: true },
        AppMode.Uninstall => !IsUninstallRunning,
        _ => false,
    };

    private bool IsUninstallRunning => CurrentPage is UninstallViewModel { IsRunning: true };

    /// <summary>是否可返回主页（安装/卸载进行中不可）</summary>
    public bool CanGoHome => CurrentPage is not (InstallViewModel { IsRunning: true } or UninstallViewModel { IsRunning: true });

    public bool IsLastStep => CurrentMode switch
    {
        AppMode.Install => CurrentStep == _installPages.Length - 1,
        _ => false,
    };

    public string NextButtonText => CurrentMode switch
    {
        AppMode.Install => CurrentPage switch
        {
            InstallViewModel { IsRunning: true } => "安装中…",
            InstallViewModel { IsCompleted: false } => "开始安装",
            InstallViewModel => "下一步",
            _ when IsLastStep => "完成",
            _ => "下一步",
        },
        AppMode.Uninstall when CurrentPage is UninstallViewModel { IsCompleted: true } => "返回主页",
        AppMode.Uninstall => "开始卸载",
        _ => "下一步",
    };

    public bool CanNext => CurrentMode switch
    {
        AppMode.Install => CurrentPage switch
        {
            InstallViewModel { IsRunning: true } => false,
            InstallViewModel => true,
            WelcomeViewModel w => w.CanProceed,
            LocationViewModel l => l.CanProceed,
            PackagesViewModel p => p.CanProceed,
            _ => true,
        },
        AppMode.Uninstall => CurrentPage is UninstallViewModel u && u.CanProceed,
        _ => false,
    };

    public MainViewModel()
    {
        _session = new AppSession();

        _home = new HomeViewModel(this);
        _uninstall = new UninstallViewModel(_session, this);
        _settings = new SettingsViewModel(_session);

        _installPages =
        [
            new WelcomeViewModel(_session),
            new LocationViewModel(_session),
            new PackagesViewModel(_session),
            new InstallViewModel(_session),
            new DoneViewModel(_session),
        ];

        // 订阅安装页 VM 属性变化，实时刷新按钮状态
        foreach (var page in _installPages)
        {
            if (page is ObservableObject observable)
            {
                observable.PropertyChanged += OnPagePropertyChanged;
            }
        }

        // 初始化安装步骤
        string[] installNames = ["欢迎", "安装位置", "选择组件", "开始安装", "完成"];
        for (int i = 0; i < installNames.Length; i++)
        {
            InstallSteps.Add(new StepItem { Index = i + 1, Name = installNames[i], IsCurrent = i == 0 });
        }

        // 初始化卸载步骤
        string[] uninstallNames = ["检测与选项", "执行", "完成"];
        for (int i = 0; i < uninstallNames.Length; i++)
        {
            UninstallSteps.Add(new StepItem { Index = i + 1, Name = uninstallNames[i], IsCurrent = i == 0 });
        }

        // 初始化导航项
        NavItems.Add(new NavItem { Name = "首页", Symbol = SymbolRegular.Home24, Command = GoHomeCommand, IsActive = true });
        NavItems.Add(new NavItem { Name = "安装", Symbol = SymbolRegular.ArrowDownload24, Command = StartInstallCommand });
        NavItems.Add(new NavItem { Name = "卸载", Symbol = SymbolRegular.Delete24, Command = StartUninstallCommand });
        NavItems.Add(new NavItem { Name = "设置", Symbol = SymbolRegular.Settings24, Command = OpenSettingsCommand });

        _currentStep = 0;
        _currentPage = _home;
    }

    // ============ 模式切换 ============

    /// <summary>返回主页</summary>
    [RelayCommand]
    private void GoHome()
    {
        CurrentMode = AppMode.Home;
        CurrentPage = _home;
        _home.Refresh();
        UpdatePanelState();
    }

    /// <summary>进入安装模式</summary>
    [RelayCommand]
    private void StartInstall()
    {
        CurrentMode = AppMode.Install;
        CurrentStep = 0;
        CurrentPage = _installPages[0];
        UpdatePanelState();
        UpdateSteps();
    }

    /// <summary>进入卸载模式</summary>
    [RelayCommand]
    private void StartUninstall()
    {
        CurrentMode = AppMode.Uninstall;
        CurrentPage = _uninstall;
        _uninstall.Refresh();
        UpdateUninstallSteps(0);
        UpdatePanelState();
    }

    /// <summary>刷新卸载步骤高亮（0 检测与选项 / 1 执行 / 2 完成）</summary>
    private void UpdateUninstallSteps(int index)
    {
        for (int i = 0; i < UninstallSteps.Count; i++)
        {
            UninstallSteps[i].IsCurrent = i == index;
        }
        OnPropertyChanged(nameof(CurrentSteps));
    }

    /// <summary>进入设置模式</summary>
    [RelayCommand]
    private void OpenSettings()
    {
        CurrentMode = AppMode.Settings;
        CurrentPage = _settings;
        _settings.Refresh();
        UpdatePanelState();
    }

    /// <summary>刷新主页状态（卸载/安装完成后调用）</summary>
    public void RefreshHome() => _home.Refresh();

    // ============ 安装向导 ============

    /// <summary>下一步</summary>
    [RelayCommand]
    private void Next()
    {
        if (CurrentMode == AppMode.Uninstall)
        {
            if (CurrentPage is UninstallViewModel { IsCompleted: true })
            {
                UpdateUninstallSteps(2);
                GoHome();
            }
            else if (CurrentPage is UninstallViewModel u && u.CanProceed && !u.IsRunning)
            {
                UpdateUninstallSteps(1);
                u.StartUninstall();
            }
            return;
        }

        if (CurrentMode != AppMode.Install)
        {
            return;
        }

        // 安装页：未完成时点击 = 开始安装
        if (CurrentPage is InstallViewModel installVm)
        {
            if (!installVm.IsCompleted)
            {
                if (!installVm.IsRunning)
                {
                    installVm.StartInstall();
                }
                return;
            }
        }
        else if (!CanNext)
        {
            return;
        }

        if (CurrentStep >= _installPages.Length - 1)
        {
            // 安装完成后返回主页
            GoHome();
            return;
        }

        CurrentStep++;
        CurrentPage = _installPages[CurrentStep];
        UpdateSteps();

        // 页面激活时刷新（扫描/目录等异步数据）
        switch (CurrentPage)
        {
            case LocationViewModel locationVm:
                locationVm.Refresh();
                break;
            case PackagesViewModel packagesVm:
                packagesVm.Refresh();
                break;
        }

        if (CurrentPage is DoneViewModel doneVm)
        {
            doneVm.Refresh();
        }
    }

    /// <summary>上一步</summary>
    [RelayCommand]
    private void Back()
    {
        if (CurrentMode == AppMode.Uninstall)
        {
            GoHome();
            return;
        }

        if (CurrentMode != AppMode.Install)
        {
            return;
        }
        if (CurrentStep <= 0)
        {
            return;
        }

        CurrentStep--;
        CurrentPage = _installPages[CurrentStep];
        UpdateSteps();
    }

    /// <summary>取消并退出</summary>
    [RelayCommand]
    private void Cancel()
    {
        // 安装/卸载进行中不允许直接退出
        if (CurrentPage is InstallViewModel { IsRunning: true } or UninstallViewModel { IsRunning: true })
        {
            return;
        }
        Application.Current.Shutdown();
    }

    // ============ 内部 ============

    private void OnPagePropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        OnPropertyChanged(nameof(CanNext));
        OnPropertyChanged(nameof(CanGoBack));
        OnPropertyChanged(nameof(NextButtonText));
        OnPropertyChanged(nameof(CanGoHome));
    }

    /// <summary>刷新安装步骤高亮与按钮状态</summary>
    private void UpdateSteps()
    {
        for (int i = 0; i < InstallSteps.Count; i++)
        {
            InstallSteps[i].IsCurrent = i == CurrentStep;
        }

        OnPropertyChanged(nameof(CanGoBack));
        OnPropertyChanged(nameof(IsLastStep));
        OnPropertyChanged(nameof(NextButtonText));
        OnPropertyChanged(nameof(CanNext));
    }

    /// <summary>刷新面板可见性与导航高亮</summary>
    private void UpdatePanelState()
    {
        foreach (var item in NavItems)
        {
            item.IsActive = CurrentMode switch
            {
                AppMode.Home => item.Name == "首页",
                AppMode.Install => item.Name == "安装",
                AppMode.Uninstall => item.Name == "卸载",
                AppMode.Settings => item.Name == "设置",
                _ => false,
            };
        }

        OnPropertyChanged(nameof(ShowNavItems));
        OnPropertyChanged(nameof(ShowInstallSteps));
        OnPropertyChanged(nameof(ShowUninstallSteps));
        OnPropertyChanged(nameof(ShowBottomBar));
        OnPropertyChanged(nameof(ShowNextButton));
        OnPropertyChanged(nameof(ShowSteps));
        OnPropertyChanged(nameof(CurrentSteps));
        OnPropertyChanged(nameof(CanGoBack));
        OnPropertyChanged(nameof(IsLastStep));
        OnPropertyChanged(nameof(NextButtonText));
        OnPropertyChanged(nameof(CanNext));
        OnPropertyChanged(nameof(CurrentSteps));
    }
}
