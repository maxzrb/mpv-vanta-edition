using System.Text.RegularExpressions;
using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// 扫描目录中的 Vanta 增量包（01~05），校验分卷完整性与版本一致性。
/// </summary>
public static partial class PackageScanner
{
    /// <summary>已知包名 → 显示名</summary>
    private static readonly Dictionary<string, string> KnownNames = new()
    {
        ["mpv-base"] = "Base · 核心播放器",
        ["mpv-extras"] = "Extras · 着色器与运行时",
        ["mpv-fasterwhisper-addon"] = "Faster-Whisper · AI 字幕",
        ["mpv-lsfg-addon"] = "LSFG · 补帧扩展",
        ["mpv-config"] = "Config · 个人设置",
    };

    /// <summary>
    /// 必选包编号：仅 01 Base 为核心，其余（02~05）均为按需可选。
    /// 可选包缺失不阻止安装；默认全部勾选，用户可取消。
    /// </summary>
    private static readonly HashSet<string> RequiredIds = ["01"];

    /// <summary>主文件：NN-名称-vX.Y.Z.7z</summary>
    [GeneratedRegex(@"^(?<id>\d{2})-(?<name>[\w-]+?)-v(?<ver>\d+\.\d+\.\d+)\.7z$", RegexOptions.IgnoreCase)]
    private static partial Regex MainFileRegex();

    /// <summary>分卷：NN-名称-vX.Y.Z.7z.NNN</summary>
    [GeneratedRegex(@"^(?<id>\d{2})-(?<name>[\w-]+?)-v(?<ver>\d+\.\d+\.\d+)\.7z\.(?<part>\d{3})$", RegexOptions.IgnoreCase)]
    private static partial Regex PartFileRegex();

    /// <summary>扫描指定目录</summary>
    public static PackageScanResult Scan(string directory)
    {
        var result = new PackageScanResult();

        if (!Directory.Exists(directory))
        {
            result.Errors.Add($"目录不存在：{directory}");
            return result;
        }

        var files = Directory.GetFiles(directory, "*.7z*", SearchOption.TopDirectoryOnly);
        if (files.Length == 0)
        {
            result.Errors.Add($"目录中未找到任何 Vanta 增量包（*.7z）：{directory}");
            return result;
        }

        // key = "编号|版本"，同一编号+版本的所有文件归入一个包
        var group = new Dictionary<string, PackageGroup>();

        foreach (var file in files)
        {
            var name = Path.GetFileName(file);

            // 私用全量包单独标记
            if (name.StartsWith("mpv-full-private-", StringComparison.OrdinalIgnoreCase))
            {
                result.FullPrivateFile = name;
                result.Warnings.Add($"检测到私用全量包 {name}：仅限本地使用，不得公开分发。");
                continue;
            }

            var mainMatch = MainFileRegex().Match(name);
            if (mainMatch.Success)
            {
                var key = Key(mainMatch.Groups["id"].Value, mainMatch.Groups["ver"].Value);
                if (!group.TryGetValue(key, out var g))
                {
                    g = new PackageGroup(CreatePackage(mainMatch, directory));
                    group[key] = g;
                }
                g.MainFiles.Add(name);
                continue;
            }

            var partMatch = PartFileRegex().Match(name);
            if (partMatch.Success)
            {
                var key = Key(partMatch.Groups["id"].Value, partMatch.Groups["ver"].Value);
                if (!group.TryGetValue(key, out var g))
                {
                    g = new PackageGroup(CreatePartPackage(partMatch, directory));
                    group[key] = g;
                }
                g.Parts.Add((name, int.Parse(partMatch.Groups["part"].Value)));
                continue;
            }

            result.Warnings.Add($"忽略无法识别的文件：{name}");
        }

        // 汇总各包
        foreach (var (_, g) in group)
        {
            var pkg = g.Pkg;
            if (g.MainFiles.Count > 0)
            {
                // 单文件包（优先于分卷形式）
                var main = g.MainFiles[0];
                if (g.MainFiles.Count > 1)
                {
                    result.Warnings.Add($"发现同名多份主文件，使用第一个：{main}");
                }
                pkg.EntryFile = main;
                pkg.TotalSize = new FileInfo(Path.Combine(directory, main)).Length;
                pkg.IsComplete = true;
                pkg.MissingParts = [];
            }
            else
            {
                // 分卷包：.NNN 从 1 开始连续
                var ordered = g.Parts.OrderBy(p => p.Num).ToList();
                var entry = ordered.FirstOrDefault();
                if (entry.Num == 0)
                {
                    result.Errors.Add($"{pkg.Id} 号包没有任何分卷文件。");
                    continue;
                }

                // 入口文件 = 去掉 .NNN 的主名（7z 解压分卷时指定 .001 即可）
                var entryName = entry.Name;
                pkg.EntryFile = entryName;
                var fileList = new List<string> { entryName };

                var expected = 1;
                var missing = new List<string>();
                foreach (var p in ordered)
                {
                    if (p.Num == expected)
                    {
                        fileList.Add(p.Name);
                        expected++;
                    }
                    else
                    {
                        for (int i = expected; i < p.Num; i++)
                        {
                            missing.Add(entryName[..^4] + "." + i.ToString("D3"));
                        }
                        expected = p.Num + 1;
                    }
                }

                pkg.IsComplete = missing.Count == 0;
                pkg.MissingParts = missing;
                pkg.TotalSize = ordered.Sum(p => new FileInfo(Path.Combine(directory, p.Name)).Length);
            }

            result.Packages.Add(pkg);
        }

        // 按编号排序
        result.Packages.Sort((a, b) => string.CompareOrdinal(a.Id, b.Id));

        // 版本一致性
        var versions = result.Packages.Select(p => p.Version).Distinct().ToList();
        if (versions.Count == 1)
        {
            result.UnifiedVersion = versions[0];
        }
        else
        {
            result.Errors.Add($"包版本不一致：{string.Join(" / ", versions)}。请确保所有包来自同一版本。");
        }

        // 必选包检查
        var foundIds = result.Packages.Select(p => p.Id).ToHashSet();
        foreach (var rid in RequiredIds)
        {
            if (!foundIds.Contains(rid))
            {
                result.MissingRequiredIds.Add(rid);
            }
        }
        if (result.MissingRequiredIds.Count > 0)
        {
            result.Errors.Add($"缺少必选包：{string.Join("、", result.MissingRequiredIds.Select(id => $"{id} 号包"))}。");
        }

        // 分卷完整性错误
        foreach (var pkg in result.Packages.Where(p => !p.IsComplete))
        {
            result.Errors.Add($"{pkg.Id} 号包分卷不完整，缺少：{string.Join("、", pkg.MissingParts)}");
        }

        return result;
    }

    private static string Key(string id, string version) => $"{id}|{version}";

    private static VantaPackage CreatePackage(Match m, string directory) => new()
    {
        Id = m.Groups["id"].Value,
        DisplayName = GetDisplayName(m.Groups["name"].Value),
        Version = m.Groups["ver"].Value,
        EntryFile = m.Value,
        Files = [m.Value],
        Required = RequiredIds.Contains(m.Groups["id"].Value),
        IsComplete = false,
        MissingParts = [],
        TotalSize = 0,
        SourceDirectory = directory,
    };

    private static VantaPackage CreatePartPackage(Match m, string directory) => new()
    {
        Id = m.Groups["id"].Value,
        DisplayName = GetDisplayName(m.Groups["name"].Value),
        Version = m.Groups["ver"].Value,
        EntryFile = string.Empty,
        Files = [],
        Required = RequiredIds.Contains(m.Groups["id"].Value),
        IsComplete = false,
        MissingParts = [],
        TotalSize = 0,
        SourceDirectory = directory,
    };

    private static string GetDisplayName(string name) =>
        KnownNames.TryGetValue(name, out var d) ? d : name;

    /// <summary>分卷分组临时结构</summary>
    private sealed class PackageGroup(VantaPackage pkg)
    {
        public VantaPackage Pkg { get; } = pkg;

        public List<string> MainFiles { get; } = [];

        public List<(string Name, int Num)> Parts { get; } = [];
    }
}
