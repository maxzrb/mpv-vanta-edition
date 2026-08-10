using System.Text.Json;

namespace Vanta.Core.Services;

/// <summary>
/// 检查更新服务：查询 GitHub Releases 最新版本。
/// </summary>
public static class UpdateService
{
    /// <summary>仓库（改为新名 mpv-vanta-edition）</summary>
    public const string Repo = "maxzrb/mpv-vanta-edition";

    /// <summary>检查结果</summary>
    public sealed record UpdateInfo(
        string LatestVersion,
        string ReleaseUrl,
        string PublishedAt,
        IReadOnlyList<ReleaseAsset> Assets)
    {
        public IReadOnlyList<string> AssetNames => Assets.Select(a => a.Name).ToList();

        /// <summary>是否有可用更新（对比本地包版本）</summary>
        public bool HasNewer(string? currentVersion) =>
            !string.IsNullOrWhiteSpace(currentVersion)
            && !string.Equals(TrimV(currentVersion), TrimV(LatestVersion), StringComparison.OrdinalIgnoreCase)
            && CompareVersions(TrimV(LatestVersion), TrimV(currentVersion)) > 0;

        private static string TrimV(string v) => v.TrimStart('v', 'V');

        /// <summary>简单语义化版本比较：1.4.2 > 1.4.1</summary>
        private static int CompareVersions(string a, string b)
        {
            var pa = a.Split('.', '-').Select(s => int.TryParse(s, out var n) ? n : 0).ToArray();
            var pb = b.Split('.', '-').Select(s => int.TryParse(s, out var n) ? n : 0).ToArray();
            for (int i = 0; i < Math.Max(pa.Length, pb.Length); i++)
            {
                var x = i < pa.Length ? pa[i] : 0;
                var y = i < pb.Length ? pb[i] : 0;
                if (x != y)
                {
                    return x.CompareTo(y);
                }
            }
            return 0;
        }
    }

    /// <summary>Release 资产</summary>
    public sealed record ReleaseAsset(string Name, string Url, long Size)
    {
        public string SizeText => Models.VantaPackage.FormatSize(Size);
    }

    /// <summary>
    /// 查询最新 Release（仅正式版，非草稿/预发布）。
    /// </summary>
    public static async Task<UpdateInfo?> CheckLatestAsync(CancellationToken ct = default)
    {
        using var http = new HttpClient();
        http.DefaultRequestHeaders.UserAgent.ParseAdd("VantaInstaller/0.2");
        http.Timeout = TimeSpan.FromSeconds(15);

        var url = $"https://api.github.com/repos/{Repo}/releases/latest";
        var json = await http.GetStringAsync(url, ct);
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;

        var tag = root.TryGetProperty("tag_name", out var t) ? t.GetString() ?? "" : "";
        var html = root.TryGetProperty("html_url", out var h) ? h.GetString() ?? "" : "";
        var published = root.TryGetProperty("published_at", out var p) ? p.GetString() ?? "" : "";
        var assets = new List<ReleaseAsset>();
        if (root.TryGetProperty("assets", out var a) && a.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in a.EnumerateArray())
            {
                var name = item.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "";
                var assetUrl = item.TryGetProperty("browser_download_url", out var u) ? u.GetString() ?? "" : "";
                var size = item.TryGetProperty("size", out var s) && s.TryGetInt64(out var sz) ? sz : 0L;
                if (!string.IsNullOrEmpty(name))
                {
                    assets.Add(new ReleaseAsset(name, assetUrl, size));
                }
            }
        }

        return new UpdateInfo(tag, html, published, assets);
    }
}
