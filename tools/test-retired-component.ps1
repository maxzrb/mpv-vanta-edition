# 在临时安装目录编译真实迁移服务，验证旧组件隔离与用户数据保留。
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$testRoot = Join-Path $root 'tmp/modernization/migration-test'
New-Item -ItemType Directory -Force -Path $testRoot | Out-Null
$source = Join-Path $root 'VantaInstaller/src/Vanta.Core/Services/RetiredComponentService.cs'
$escapedSource = [System.Security.SecurityElement]::Escape($source)
$project = @"
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0-windows</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup>
  <ItemGroup><Compile Include="$escapedSource" Link="RetiredComponentService.cs" /></ItemGroup>
</Project>
"@
[System.IO.File]::WriteAllText((Join-Path $testRoot 'MigrationTest.csproj'), $project, [System.Text.UTF8Encoding]::new($false))
$program = @'
using Vanta.Core.Services;
using System.Text;
var root = Path.Combine(AppContext.BaseDirectory, "fixture-" + Guid.NewGuid().ToString("N"));
void Write(string name, string value) {
    var path = Path.Combine(root, name); Directory.CreateDirectory(Path.GetDirectoryName(path)!);
    File.WriteAllText(path, value, new UTF8Encoding(false));
}
void Assert(bool condition, string message) { if (!condition) throw new Exception(message); }
Write("portable_config/scripts/uosc_danmaku/main.lua", "旧程序");
Write("portable_config/scripts/uosc_danmaku/downloads/用户.ass", "用户弹幕");
Write("portable_config/script-opts/uosc_danmaku.conf", "用户设置");
Write("portable_config/subs/普通字幕.srt", "字幕");
Write("backup/history/弹幕.ass", "历史备份");
RetiredComponentService.Quarantine(root, Console.WriteLine);
Assert(Directory.Exists(Path.Combine(root, "portable_config/scripts/uosc_danmaku")), "无标记旧安装不应移动");
Write("portable_config/components.lock.json", "{\"retired_components\":[\"uosc_danmaku\"]}");
RetiredComponentService.Quarantine(root, Console.WriteLine);
Assert(!Directory.Exists(Path.Combine(root, "portable_config/scripts/uosc_danmaku")), "旧程序仍会自动加载");
Assert(!File.Exists(Path.Combine(root, "portable_config/script-opts/uosc_danmaku.conf")), "专属配置未隔离");
Assert(File.ReadAllText(Path.Combine(root, "portable_config/subs/普通字幕.srt"), Encoding.UTF8) == "字幕", "字幕被改动");
Assert(File.ReadAllText(Path.Combine(root, "backup/history/弹幕.ass"), Encoding.UTF8) == "历史备份", "历史备份被改动");
Assert(Directory.GetFiles(Path.Combine(root, "backup"), "用户.ass", SearchOption.AllDirectories).Length == 1, "用户下载未保留");
var count = Directory.GetDirectories(Path.Combine(root, "backup"), "retired-components-*").Length;
RetiredComponentService.Quarantine(root, Console.WriteLine);
Assert(Directory.GetDirectories(Path.Combine(root, "backup"), "retired-components-*").Length == count, "重复执行非幂等");
Console.WriteLine("PASS 覆盖迁移／无标记兼容／用户文件保留／重复执行");
'@
[System.IO.File]::WriteAllText((Join-Path $testRoot 'Program.cs'), $program, [System.Text.UTF8Encoding]::new($false))
dotnet run --project (Join-Path $testRoot 'MigrationTest.csproj')
if ($LASTEXITCODE -ne 0) { throw '迁移测试失败' }
