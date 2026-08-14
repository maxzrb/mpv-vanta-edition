using System.Text;
using Vanta.Core.Models;
using Vanta.Core.Services;

Console.OutputEncoding = Encoding.UTF8;

// 用法：Vanta.ScanTool <包目录> [<目标目录>]
var sourceDir = args.Length > 0 ? args[0] : @"C:\Program portable\mpv2\release";
var targetDir = args.Length > 1 ? args[1] : string.Empty;
var installMode = args.Length >= 3 && args[1] == "--install" ? args[2] : null;

Console.WriteLine("========================================");
Console.WriteLine($"Vanta Installer · 核心逻辑自检工具");
Console.WriteLine($"扫描目录：{sourceDir}");
Console.WriteLine("========================================");

// 1. 包扫描
var scan = PackageScanner.Scan(sourceDir);
Console.WriteLine();
Console.WriteLine($"识别到 {scan.Packages.Count} 个包，统一版本：{scan.UnifiedVersion ?? "（不一致）"}");
Console.WriteLine();

foreach (var pkg in scan.Packages)
{
    var status = pkg.IsComplete ? "完整" : "分卷缺失";
    Console.WriteLine($"  [{pkg.Id}] {pkg.DisplayName}");
    Console.WriteLine($"        版本 {pkg.Version} · {VantaPackage.FormatSize(pkg.TotalSize)} · {status}");
    Console.WriteLine($"        入口 {pkg.EntryFile}");
    if (pkg.MissingParts.Count > 0)
    {
        Console.WriteLine($"        缺少 {string.Join("、", pkg.MissingParts)}");
    }
}

if (scan.FullPrivateFile is not null)
{
    Console.WriteLine($"  私用全量包（本地）：{scan.FullPrivateFile}");
}

Console.WriteLine();
if (scan.Errors.Count > 0)
{
    Console.WriteLine("[错误]");
    foreach (var e in scan.Errors)
    {
        Console.WriteLine($"  ✗ {e}");
    }
}
else
{
    Console.WriteLine("[错误] 无 ✓");
}

if (scan.Warnings.Count > 0)
{
    Console.WriteLine("[警告]");
    foreach (var w in scan.Warnings)
    {
        Console.WriteLine($"  ! {w}");
    }
}

Console.WriteLine();
Console.WriteLine($"是否可安装：{(scan.CanInstall ? "是 ✓" : "否 ✗")}");

// 2. 7z 定位
Console.WriteLine();
Console.WriteLine("----------------------------------------");
Console.WriteLine("7z 定位测试");
try
{
    var sevenZip = new SevenZipService();
    var path = await sevenZip.LocateAsync();
    Console.WriteLine($"  找到 7z：{path}");

    // 3. 用 7z l 列出 01 包开头内容（验证 7z 可执行）
    var first = scan.Packages.FirstOrDefault();
    if (first is not null && scan.CanInstall)
    {
        Console.WriteLine($"  测试：列出 {first.EntryFile} 的前几项内容");
        var lines = new List<string>();
        sevenZip.OutputReceived += lines.Add;
        await ListArchiveAsync(path, first.EntryPath, lines);
        foreach (var line in lines.Take(8))
        {
            Console.WriteLine($"    {line}");
        }
    }
}
catch (Exception ex)
{
    Console.WriteLine($"  7z 定位失败：{ex.Message}");
}

// 4. 目标目录状态（可选）
if (!string.IsNullOrEmpty(targetDir))
{
    var isUpgrade = File.Exists(Path.Combine(targetDir, "mpv.exe"));
    Console.WriteLine();
    Console.WriteLine($"目标目录：{targetDir} → {(isUpgrade ? "覆盖升级" : "全新安装")}");
}

Console.WriteLine();
Console.WriteLine("========================================");

// 5. 真实安装测试（--install <目标目录>）：只装 01 包到临时目录，验证解压+自检
if (installMode is not null)
{
    Console.WriteLine();
    Console.WriteLine("----------------------------------------");
    Console.WriteLine($"真实安装测试：{sourceDir} → {installMode}（仅 01 包）");
    try
    {
        var engine = new InstallEngine(new SevenZipService());
        var progress = new Progress<InstallProgress>(p =>
            Console.Write($"\r  {p.Percent,3}%  {p.Message,-40}"));

        // 仅安装 01 号包（若存在多个版本取第一个，按复合键选择）
        var baseKey = scan.Packages.FirstOrDefault(p => p.Id == "01")?.Key;
        var result = await engine.RunAsync(new InstallOptions
        {
            SourceDirectory = sourceDir,
            InstallDirectory = installMode,
            SelectedPackageKeys = baseKey is null ? null : [baseKey],
        }, progress);

        Console.WriteLine();
        Console.WriteLine($"  安装结果：{(result.Success ? "成功 ✓" : $"失败 ✗ {result.Error}")}");
        Console.WriteLine($"  目标 mpv.exe：{(result.MpvExists ? "存在 ✓" : "不存在 ✗")}");
        if (!string.IsNullOrEmpty(result.MpvVersionLine))
        {
            Console.WriteLine($"  mpv 版本：{result.MpvVersionLine}");
        }
        Console.WriteLine("  安装日志：");
        foreach (var line in result.Log.Take(20))
        {
            Console.WriteLine($"    {line}");
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"  安装测试异常：{ex.Message}");
    }
    Console.WriteLine();
    Console.WriteLine("========================================");
    return;
}

static async Task ListArchiveAsync(string sevenZipPath, string archivePath, List<string> lines)
{
    var psi = new System.Diagnostics.ProcessStartInfo
    {
        FileName = sevenZipPath,
        Arguments = $"l \"{archivePath}\"",
        UseShellExecute = false,
        CreateNoWindow = true,
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        StandardOutputEncoding = Encoding.UTF8,
        StandardErrorEncoding = Encoding.UTF8,
    };
    using var proc = System.Diagnostics.Process.Start(psi);
    if (proc is null)
    {
        return;
    }
    while (true)
    {
        var line = await proc.StandardOutput.ReadLineAsync();
        if (line is null)
        {
            break;
        }
        lines.Add(line);
    }
    await proc.WaitForExitAsync();
}
