using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Windows;
using System.Windows.Controls.Primitives;
using System.Windows.Threading;
using CommunityToolkit.Mvvm.Input;
using Vanta.Core.Services;
using Vanta.Core.Models;
using Vanta.Installer.ViewModels;
using Vanta.Installer.Views;

// 使用真实 WPF 绑定、视图模型和内置下载引擎回归，不执行解压、关联或正式发布。
internal static class Program
{
    [STAThread]
    private static int Main()
    {
        var app = new Vanta.Installer.App();
        app.InitializeComponent();
        SynchronizationContext.SetSynchronizationContext(new DispatcherSynchronizationContext());
        var task = RunAsync(app);
        var frame = new DispatcherFrame();
        _ = task.ContinueWith(_ => app.Dispatcher.BeginInvoke(() => frame.Continue = false));
        Dispatcher.PushFrame(frame);
        try
        {
            task.GetAwaiter().GetResult();
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            return 1;
        }
    }

    private static async Task RunAsync(Application app)
    {
        var root = Path.Combine(Path.GetTempPath(), "VantaRescanRegression", Guid.NewGuid().ToString("N"));
        var initial = Path.Combine(root, "初始 空目录");
        var custom = Path.Combine(root, "自选 下载目录");
        Directory.CreateDirectory(initial);
        Directory.CreateDirectory(custom);
        await CheckDirectoryAccessAsync(root);
        app.Properties["SourceDirectory"] = initial;

        var main = new MainViewModel();
        var session = GetField<AppSession>(main, "_session");
        var welcome = (WelcomeViewModel)GetField<object[]>(main, "_installPages")[0];
        var settings = GetField<SettingsViewModel>(main, "_settings");
        await WaitForScanAsync(welcome);
        Check(!welcome.CanProceed, "启动时空目录不可继续");

        var view = new WelcomeView { DataContext = welcome };
        await Dispatcher.Yield(DispatcherPriority.ApplicationIdle);
        var button = Descendants(view).OfType<ButtonBase>()
            .Single(b => Equals(b.Content, "重新扫描"));
        button.GetBindingExpression(ButtonBase.CommandProperty)!.UpdateTarget();
        Check(ReferenceEquals(button.Command, welcome.ScanCommand), "重新扫描按钮绑定到真实生成的命令");

        // 下载由真实 aria2 引擎完成，HTTP 服务器只监听本机并提供小型扫描占位数据。
        await DownloadAsync(settings, initial, "01-mpv-base-v1.6.4.7z");
        main.StartInstallCommand.Execute(null);
        Check(!main.CanNext, "重新进入安装时扫描完成前不可下一步");
        await WaitForScanAsync(welcome);
        Check(welcome.CanProceed && main.CanNext && welcome.ScanResult!.Packages.Count == 1,
            "同一进程下载完成后进入安装即可识别");

        await File.WriteAllTextAsync(Path.Combine(initial, "04-mpv-config-v1.6.4.7z"), "扫描占位", Encoding.UTF8);
        await ((IAsyncRelayCommand)button.Command!).ExecuteAsync(null);
        Check(welcome.ScanResult!.Packages.Count == 2, "点击重新扫描可识别后来新增的包");

        await DownloadAsync(settings, custom, "01-mpv-base-v1.6.4.7z");
        Check(session.SourceDirectory == custom, "自选目录下载成功后交接给安装会话");
        main.StartInstallCommand.Execute(null);
        await WaitForScanAsync(welcome);
        Check(welcome.SourceDirectory == custom && welcome.CanProceed
            && session.ScanResult!.Packages.All(p => p.SourceDirectory == custom),
            "安装页自动扫描实际下载目录，且不复用旧目录结果");

        // 同一调度周期连续请求两个目录，验证不会把旧扫描结果写到新路径。
        welcome.SourceDirectory = initial;
        var pending = welcome.ScanCommand.ExecuteAsync(null);
        session.SourceDirectory = custom;
        welcome.Refresh();
        await pending;
        await WaitForScanAsync(welcome);
        Check(welcome.SourceDirectory == custom && welcome.ScanResult!.Packages.Count == 1
            && session.ScanResult!.Packages.All(p => p.SourceDirectory == custom),
            "扫描期间切换目录会补扫，路径和结果一致");

        welcome.SourceDirectory = Path.Combine(root, "不存在");
        await welcome.ScanCommand.ExecuteAsync(null);
        Check(!welcome.CanProceed && !main.CanNext && session.ScanResult is { CanInstall: false },
            "扫描无效目录后不会沿用上次可安装状态");
        Console.WriteLine($"PASS: 全部回归通过；临时样本目录 {root}");
    }

    private static async Task CheckDirectoryAccessAsync(string root)
    {
        var writable = Path.Combine(root, "可写位置");
        Directory.CreateDirectory(writable);
        Check(InstallDirectoryAccess.GetWriteError(writable) is null, "已有可写目录通过权限检查");
        var missing = Path.Combine(writable, "尚未创建", "MPV Vanta Edition");
        Check(InstallDirectoryAccess.GetWriteError(missing) is null && !Directory.Exists(missing),
            "可写父目录通过检查，且不提前创建安装目录");
        Check(!Directory.EnumerateFileSystemEntries(writable).Any(), "写入探针正常清理");
        var occupied = Path.Combine(writable, "同名文件");
        await File.WriteAllTextAsync(occupied, "占位", Encoding.UTF8);
        Check(InstallDirectoryAccess.GetWriteError(Path.Combine(occupied, "播放器")) is not null,
            "同名文件阻挡安装路径时明确失败");

        // 仅在本次临时夹具设置当前用户的拒绝写入 ACL，不修改 Program Files 或其他系统目录。
        var blocked = new DirectoryInfo(Path.Combine(root, "受限位置"));
        blocked.Create();
        var originalAcl = blocked.GetAccessControl();
        var deniedAcl = blocked.GetAccessControl();
        var sid = WindowsIdentity.GetCurrent().User!;
        deniedAcl.AddAccessRule(new FileSystemAccessRule(sid, FileSystemRights.Write,
            InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
            PropagationFlags.None, AccessControlType.Deny));
        blocked.SetAccessControl(deniedAcl);
        try
        {
            Check(InstallDirectoryAccess.GetWriteError(blocked.FullName) is not null,
                "拒绝写入的已有目录被拦截");
            var target = Path.Combine(blocked.FullName, "MPV Vanta Edition");
            Check(InstallDirectoryAccess.GetWriteError(target) is not null && !Directory.Exists(target),
                "受限父目录下的全新安装被拦截");
            var session = new AppSession();
            var location = new LocationViewModel(session) { InstallDirectory = blocked.FullName };
            Check(location.StatusIsWarning && !location.CanProceed
                && location.StatusText!.Contains("无法写入安装目录"),
                "安装位置页给出权限提示并禁止下一步");
            var result = await new InstallEngine().RunAsync(new InstallOptions
            {
                SourceDirectory = Path.Combine(root, "不存在的包目录"),
                InstallDirectory = target,
                RegisterAssociations = [PlaybackMode.MultiInstance],
            });
            Check(!result.Success && result.Error!.Contains("无法写入安装目录")
                && result.Log.Count == 1 && result.BackupPath is null && !Directory.Exists(target),
                "独立安装引擎在工具定位、扫描、备份、解压及关联注册前拦截权限错误");

            location.InstallDirectory = writable;
            Check(location.CanProceed && !location.StatusIsWarning,
                "切换回可写目录后恢复下一步");
        }
        finally
        {
            blocked.SetAccessControl(originalAcl);
        }
    }

    private static async Task DownloadAsync(SettingsViewModel settings, string directory, string name)
    {
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        var port = ((IPEndPoint)listener.LocalEndpoint).Port;
        var payload = Encoding.UTF8.GetBytes("仅供扫描回归的下载占位数据");
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        var serve = Task.Run(async () =>
        {
            using var client = await listener.AcceptTcpClientAsync(timeout.Token);
            await using var stream = client.GetStream();
            using var reader = new StreamReader(stream, Encoding.ASCII, leaveOpen: true);
            while (!string.IsNullOrEmpty(await reader.ReadLineAsync(timeout.Token))) { }
            var header = Encoding.ASCII.GetBytes($"HTTP/1.1 200 OK\r\nContent-Length: {payload.Length}\r\nConnection: close\r\n\r\n");
            await stream.WriteAsync(header, timeout.Token);
            await stream.WriteAsync(payload, timeout.Token);
        });

        settings.DownloadDirectory = directory;
        settings.SelectedMirror = MirrorRegistry.Find("official");
        settings.DownloadItems.Clear();
        var item = new DownloadAssetItem
        {
            Asset = new UpdateService.ReleaseAsset(name, $"http://127.0.0.1:{port}/{name}", payload.Length, null),
        };
        settings.DownloadItems.Add(item);
        await settings.StartDownloadCommand.ExecuteAsync(null).WaitAsync(TimeSpan.FromSeconds(30));
        Check(item.Exists && item.Status == "完成", $"内置引擎下载成功：{directory}");
        await serve;
        Check((await File.ReadAllBytesAsync(Path.Combine(directory, name))).SequenceEqual(payload),
            "下载文件内容与本机 HTTP 响应一致");
    }

    private static async Task WaitForScanAsync(WelcomeViewModel welcome)
    {
        var deadline = DateTime.UtcNow.AddSeconds(10);
        do
        {
            await Task.Delay(10);
            if (DateTime.UtcNow > deadline) throw new TimeoutException("等待扫描超时");
        } while (welcome.IsScanning);
    }

    private static T GetField<T>(object obj, string name) =>
        (T)obj.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(obj)!;

    private static IEnumerable<DependencyObject> Descendants(DependencyObject parent)
    {
        foreach (var child in LogicalTreeHelper.GetChildren(parent).OfType<DependencyObject>())
        {
            yield return child;
            foreach (var nested in Descendants(child)) yield return nested;
        }
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
        Console.WriteLine($"PASS: {message}");
    }
}
