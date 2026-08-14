using System.Text.RegularExpressions;
using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// 扫描目录中的 Vanta 增量包（01~04），校验分卷完整性与版本一致性。
/// </summary>
public static partial class PackageScanner
{
    /// <summary>已知包名 → 显示名</summary>
    private static readonly Dictionary<string, string> KnownNames = new()
    {
        ["mpv-base"] = "Base · 核心播放器",
        ["mpv-extras"] = "Extras · 着色器与运行时",
        ["mpv-fasterwhisper-addon"] = "Faster-Whisper · AI 字幕",
        ["mpv-config"] = "Config · 个人设置",
    };

    /// <summary>
    /// 必选包编号：仅 01 Base 为核心，其余（02~04）均为按需可选。
    /// 可选包缺失不阻止安装；默认全部勾选，用户可取消。
    /// </summary>
    private static readonly HashSet<string> RequiredIds = ["01"];

    /// <summary>主文件：NN-名称-vX.Y.Z.7z</summary>
    [GeneratedRegex(@"^(?<id>\d{2})-(?<name>[\w-]+?)-v(?<ver>\d+\.\d+\.\d+)\.7z$", RegexOptions.IgnoreCase)]
    private static partial Regex MainFileRegex();

    /// <summary>分卷：NN-名称-vX.Y.Z.7z.NNN</summary>
    [GeneratedRegex(@"^(?<id>\d{2})-(?<name>[\w-]+?)-v(?<ver>\d+\.\d+\.\d+)\.7z\.(?<part>\d{3})$", RegexOptions.IgnoreCase)]
    private static partial Regex PartFileRegex();

    /// <summary>个人全量包：mpv-full-private-vX.Y.Z.7z</summary>
    [GeneratedRegex(@"^mpv-full-private-v(?<ver>\d+\.\d+\.\d+)\.7z$", RegexOptions.IgnoreCase)]
    private static partial Regex FullPrivateVersionRegex();

    /// <summary>扫描指定目录</summary>
    /// <summary>
    /// 扫描指定目录。
    /// </summary>
    /// <param name="directory">包目录</param>
    /// <param name="allowMissingBase">
    /// 是否允许缺少 01 Base 包（已安装升级场景：目标目录已有 mpv 时可不带 Base 升级组件/配置）。
    /// 为 false（全新安装场景）时缺少 01 会作为错误阻止安装。
    /// </param>
    public static PackageScanResult Scan(string directory, bool allowMissingBase = false)
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

                // 解析为可安装的全量包（Id="00"，解压即用一体包）
                var ver = FullPrivateVersionRegex().Match(name).Groups["ver"].Value;
                if (!string.IsNullOrEmpty(ver))
                {
                    result.FullPackage = new VantaPackage
                    {
                        Id = "00",
                        DisplayName = "Full · 个人全量包",
                        Version = ver,
                        EntryFile = name,
                        Files = [name],
                        Required = false,
                        IsComplete = true,
                        MissingParts = [],
                        TotalSize = new FileInfo(Path.Combine(directory, name)).Length,
                        SourceDirectory = directory,
                    };
                }
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
                var fileList = new List<string>();

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
                pkg.Files = fileList;
                pkg.TotalSize = ordered.Sum(p => new FileInfo(Path.Combine(directory, p.Name)).Length);
            }

            result.Packages.Add(pkg);
        }

        // 按编号排序
        result.Packages.Sort((a, b) => string.CompareOrdinal(a.Id, b.Id));

        // 同编号多版本去重：同一编号存在多个版本时只保留版本号最大的包，
        // 其余降级为警告并从列表移除。常见于包目录同时保留新旧版本（如
        // 01 base 1.5.1 与 1.5.2）；旧版本不参与安装与版本一致性，避免
        // 组件页出现重复编号、安装混版本以及“下一步”被卡。
        var keepById = new Dictionary<string, VantaPackage>();
        var dropped = new List<VantaPackage>();
        foreach (var pkg in result.Packages)
        {
            if (!keepById.TryGetValue(pkg.Id, out var existing))
            {
                keepById[pkg.Id] = pkg;
                continue;
            }
            if (UpdateService.CompareVersions(pkg.Version, existing.Version) > 0)
            {
                dropped.Add(existing);
                keepById[pkg.Id] = pkg;
            }
            else
            {
                dropped.Add(pkg);
            }
        }
        foreach (var d in dropped)
        {
            result.Warnings.Add($"检测到同一编号的多个版本：{d.DisplayText} 将被忽略，使用 {keepById[d.Id].DisplayText}。");
        }
        foreach (var d in dropped)
        {
            result.Packages.Remove(d);
        }

        // 版本一致性（仅增量包；全量包是独立一体包，不参与）。
        // 宽松模式（升级场景目录常混有旧版包）下降级为警告，实际安装时由引擎
        // 对"本次选中的包"强制同版本，避免升级被旧包目录卡住。
        var versions = result.Packages.Select(p => p.Version).Distinct().ToList();
        if (versions.Count == 1)
        {
            result.UnifiedVersion = versions[0];
        }
        else if (versions.Count > 1)
        {
            if (allowMissingBase)
            {
                result.Warnings.Add($"检测到多个版本：{string.Join(" / ", versions)}。安装时仅允许选中同一版本的包组合。");
            }
            else
            {
                result.Errors.Add($"包版本不一致：{string.Join(" / ", versions)}。请确保所有包来自同一版本。");
            }
        }

        // 必选包检查：存在全量包时放宽（全量包解压即用，无需 01~04 齐全）；
        // allowMissingBase=true（已安装升级）时缺少 01 只警告不阻止，
        // 由安装引擎根据目标目录是否已有 mpv.exe 最终把关（全新安装仍需 01）。
        if (result.FullPackage is null)
        {
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
                if (allowMissingBase)
                {
                    result.Warnings.Add(
                        $"缺少 {string.Join("、", result.MissingRequiredIds.Select(id => $"{id} 号包"))}（01 Base 不在包目录中）。"
                        + "若目标目录已安装 mpv（覆盖升级）可继续；全新安装必须包含 01 Base 包。");
                }
                else
                {
                    result.Errors.Add($"缺少必选包：{string.Join("、", result.MissingRequiredIds.Select(id => $"{id} 号包"))}。");
                }
            }
        }
        else
        {
            result.Warnings.Add("检测到个人全量包：可直接安装全量包（解压即用），增量包可不齐全。");
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
