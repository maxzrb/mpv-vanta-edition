using System.Text;
using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// mpv.conf 的结构化读取与安全写回。
/// 原则：保留全部注释与行顺序，只改目标行；保存前自动备份。
/// </summary>
public static class MpvConfigService
{
    /// <summary>mpv.conf 中的一行（含解析结果）</summary>
    public sealed class MpvLine
    {
        public string Raw { get; set; } = string.Empty;

        public bool IsComment { get; set; }

        public string? Key { get; set; }

        public string? Value { get; set; }

        public bool HasEquals { get; set; }

        public string? TrailingComment { get; set; }

        public bool IsBlank { get; set; }
    }

    // ============ 解析 ============

    /// <summary>把 mpv.conf 文本解析为行列表</summary>
    public static List<MpvLine> ParseLines(string content)
    {
        var lines = content.Replace("\r\n", "\n").Split('\n').ToList();
        var result = new List<MpvLine>(lines.Count);

        foreach (var raw in lines)
        {
            var line = new MpvLine { Raw = raw.TrimEnd('\r') };
            line.IsBlank = string.IsNullOrWhiteSpace(line.Raw);
            var trimmed = line.Raw.TrimStart();
            var indentLen = line.Raw.Length - trimmed.Length;
            var body = line.Raw;

            if (string.IsNullOrWhiteSpace(body))
            {
                result.Add(line);
                continue;
            }

            // 注释行：行首 #（允许缩进）
            if (trimmed.StartsWith('#'))
            {
                line.IsComment = true;
                var afterHash = trimmed[1..].TrimStart();
                if (TryParseKeyValue(afterHash, out var key, out var value, out var hasEq, out var trailing))
                {
                    line.Key = key;
                    line.Value = value;
                    line.HasEquals = hasEq;
                    line.TrailingComment = trailing;
                }
                result.Add(line);
                continue;
            }

            // 非注释行
            if (TryParseKeyValue(trimmed, out var k, out var v, out var he, out var tc))
            {
                line.Key = k;
                line.Value = v;
                line.HasEquals = he;
                line.TrailingComment = tc;
            }
            result.Add(line);
        }

        return result;
    }

    /// <summary>
    /// 解析 "key=value # 注释" 或 "key"（裸=yes）。
    /// 引号内的 # 与空格不当作分隔。
    /// </summary>
    private static bool TryParseKeyValue(string text, out string key, out string? value, out bool hasEquals, out string? trailing)
    {
        key = string.Empty;
        value = null;
        hasEquals = false;
        trailing = null;

        if (string.IsNullOrWhiteSpace(text))
        {
            return false;
        }

        // 用引号感知扫描，找到行尾注释起点（# 且不在引号内）
        var hashIndex = -1;
        var inQuote = false;
        for (int i = 0; i < text.Length; i++)
        {
            var c = text[i];
            if (c == '"')
            {
                inQuote = !inQuote;
            }
            else if (c == '#' && !inQuote)
            {
                hashIndex = i;
                break;
            }
        }

        var main = hashIndex >= 0 ? text[..hashIndex].TrimEnd() : text.TrimEnd();
        if (hashIndex >= 0)
        {
            trailing = text[hashIndex..].TrimEnd();
        }

        if (string.IsNullOrWhiteSpace(main))
        {
            return false;
        }

        var eq = main.IndexOf('=');
        if (eq < 0)
        {
            // 裸 key = yes
            key = main.Trim();
            value = "yes";
            hasEquals = false;
            return true;
        }

        key = main[..eq].Trim();
        var valPart = main[(eq + 1)..].Trim();
        value = Unquote(valPart);
        hasEquals = true;
        return !string.IsNullOrEmpty(key);
    }

    private static string Unquote(string value) =>
        value.Length >= 2 && value[0] == '"' && value[^1] == '"'
            ? value[1..^1]
            : value;

    private static string QuoteIfNeeded(string value) =>
        value.Contains(' ') || value.Contains('#') ? $"\"{value}\"" : value;

    // ============ 读取 ============

    /// <summary>从文件读取配置项当前值并标注行状态</summary>
    public static void LoadOptions(string confPath, IReadOnlyList<MpvOption> options)
    {
        if (!File.Exists(confPath))
        {
            return;
        }

        var lines = ParseLines(File.ReadAllText(confPath, Encoding.UTF8));
        foreach (var opt in options)
        {
            // 取第一个匹配行（mpv.conf 顶层键基本唯一）
            var line = lines.FirstOrDefault(l => string.Equals(l.Key, opt.Key, StringComparison.OrdinalIgnoreCase));
            if (line is null)
            {
                continue;
            }

            if (line.IsComment)
            {
                // 注释行 = 未启用，生效值就是默认值（不读注释里的示例值）
                opt.WasActive = false;
                opt.WasCommented = true;
                opt.CurrentValue = opt.DefaultValue;
            }
            else
            {
                opt.WasActive = true;
                opt.WasCommented = false;
                opt.CurrentValue = line.Value ?? opt.DefaultValue;
            }
        }
    }

    // ============ 写回 ============

    /// <summary>
    /// 应用配置修改并写回文件。
    /// </summary>
    /// <param name="confPath">mpv.conf 路径</param>
    /// <param name="options">全部配置项（含默认值与当前值）</param>
    /// <param name="forceCommentedKeys">强制注释的键（如固定分辨率时停用 autofit-smaller）</param>
    /// <param name="forceActiveKeys">强制启用的键（恢复自动适配）</param>
    /// <param name="log">日志回调</param>
    public static void Apply(
        string confPath,
        IReadOnlyList<MpvOption> options,
        IReadOnlyList<string>? forceCommentedKeys = null,
        IReadOnlyList<string>? forceActiveKeys = null,
        Action<string>? log = null)
    {
        log ??= _ => { };
        if (!File.Exists(confPath))
        {
            throw new FileNotFoundException("未找到 mpv.conf", confPath);
        }

        var lines = ParseLines(File.ReadAllText(confPath, Encoding.UTF8));

        // 1. 强制操作（先执行，options 循环再写具体值）
        if (forceCommentedKeys is not null)
        {
            foreach (var key in forceCommentedKeys)
            {
                CommentKey(lines, key, log);
            }
        }
        if (forceActiveKeys is not null)
        {
            foreach (var key in forceActiveKeys)
            {
                ActivateKey(lines, key, log);
            }
        }

        // 2. 各选项
        foreach (var opt in options)
        {
            var line = lines.FirstOrDefault(l => string.Equals(l.Key, opt.Key, StringComparison.OrdinalIgnoreCase));

            // 未修改：保持原样
            if (!opt.IsModified)
            {
                continue;
            }

            if (line is null)
            {
                // 键不存在：追加到文件末尾（带分组注释）
                AppendOption(lines, opt, log);
                continue;
            }

            // 键存在：重写
            SetOptionLine(line, opt, log);
        }

        File.WriteAllText(confPath, string.Join('\n', lines.Select(l => l.Raw)), Encoding.UTF8);
    }

    /// <summary>注释掉某键的行（保留内容）</summary>
    private static void CommentKey(List<MpvLine> lines, string key, Action<string> log)
    {
        foreach (var line in lines)
        {
            if (string.Equals(line.Key, key, StringComparison.OrdinalIgnoreCase) && !line.IsComment)
            {
                line.Raw = "#" + line.Raw;
                line.IsComment = true;
                log($"已停用：{key}");
            }
        }
    }

    /// <summary>启用某键的行（取消注释，保留原值；无值则用默认 yes）</summary>
    private static void ActivateKey(List<MpvLine> lines, string key, Action<string> log)
    {
        foreach (var line in lines)
        {
            if (string.Equals(line.Key, key, StringComparison.OrdinalIgnoreCase) && line.IsComment)
            {
                // 恢复原始内容（去掉行首的 # 与可能的空格）
                var raw = line.Raw.TrimStart();
                if (raw.StartsWith('#'))
                {
                    raw = raw[1..].TrimStart();
                }
                line.Raw = raw;
                line.IsComment = false;
                log($"已启用：{key}");
            }
        }
    }

    /// <summary>重写配置行（取消注释、写新值、保留尾注释）</summary>
    private static void SetOptionLine(MpvLine line, MpvOption opt, Action<string> log)
    {
        var value = opt.CurrentValue;

        if (opt.Type == MpvOptionType.Bool && value.Equals("no", StringComparison.OrdinalIgnoreCase))
        {
            // bool 关闭：注释掉整行
            if (!line.IsComment)
            {
                line.Raw = "#" + line.Raw;
                line.IsComment = true;
            }
            log($"已设置：{opt.Key}=no（注释）");
            return;
        }

        // 其余：启用并写 key=value（bool yes 写裸 key）
        var body = opt.Type == MpvOptionType.Bool
            ? opt.Key
            : $"{opt.Key}={QuoteIfNeeded(value)}";

        var trailing = line.TrailingComment is null ? string.Empty : " " + line.TrailingComment;
        line.Raw = body + trailing;
        line.IsComment = false;
        line.Key = opt.Key;
        line.Value = value;
        line.HasEquals = opt.Type != MpvOptionType.Bool;
        log($"已设置：{opt.Key}={value}");
    }

    /// <summary>在文件末尾追加新配置行（带分组说明）</summary>
    private static void AppendOption(List<MpvLine> lines, MpvOption opt, Action<string> log)
    {
        var value = opt.CurrentValue;
        string body;
        if (opt.Type == MpvOptionType.Bool && value.Equals("no", StringComparison.OrdinalIgnoreCase))
        {
            body = $"#{opt.Key}";
        }
        else if (opt.Type == MpvOptionType.Bool)
        {
            body = opt.Key;
        }
        else
        {
            body = $"{opt.Key}={QuoteIfNeeded(value)}";
        }

        lines.Add(new MpvLine
        {
            Raw = "",
            IsBlank = true,
        });
        lines.Add(new MpvLine { Raw = $"# === {opt.Group} === 由 Vanta Installer 添加" });
        lines.Add(new MpvLine
        {
            Raw = body,
            Key = opt.Key,
            Value = value,
            HasEquals = opt.Type != MpvOptionType.Bool,
        });
        log($"已新增：{opt.Key}={value}");
    }

    /// <summary>备份 mpv.conf 到 backup\ 目录，返回备份路径</summary>
    public static string? Backup(string confPath)
    {
        if (!File.Exists(confPath))
        {
            return null;
        }

        var dir = Path.Combine(Path.GetDirectoryName(confPath) ?? ".", "backup");
        Directory.CreateDirectory(dir);
        var stamp = DateTime.Now.ToString("yyyyMMdd-HHmmss");
        var dst = Path.Combine(dir, $"mpvconf-{stamp}.conf");
        File.Copy(confPath, dst, overwrite: true);
        return dst;
    }
}
