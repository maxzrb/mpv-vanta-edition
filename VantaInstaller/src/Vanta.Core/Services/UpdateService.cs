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
            && UpdateService.CompareVersions(TrimV(LatestVersion), TrimV(currentVersion)) > 0;

        private static string TrimV(string v) => v.TrimStart('v', 'V');
    }

    /// <summary>Release 资产</summary>
    public sealed record ReleaseAsset(string Name, string Url, long Size, string? Sha256)
    {
        public string SizeText => Models.VantaPackage.FormatSize(Size);
    }

    /// <summary>VantaInstaller 自身更新信息</summary>
    public sealed record InstallerUpdateInfo(
        string LatestVersion,
        string ReleaseUrl,
        string AssetUrl,
        long AssetSize);

    /// <summary>
    /// 检查 VantaInstaller 自身是否有更新：
    /// 从最新正式 Release 中找 VantaInstaller-win-x64-v*.exe 资产，
    /// 与当前安装器版本比较；无更新或网络异常返回 null。
    /// </summary>
    public static async Task<InstallerUpdateInfo?> CheckInstallerUpdateAsync(
        string? currentVersion,
        CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(currentVersion))
        {
            return null;
        }

        var info = await CheckLatestAsync(ct);
        if (info is null)
        {
            return null;
        }

        var asset = info.Assets.FirstOrDefault(a =>
            a.Name.StartsWith("VantaInstaller-win-x64-", StringComparison.OrdinalIgnoreCase)
            && a.Name.EndsWith(".exe", StringComparison.OrdinalIgnoreCase));
        if (asset is null)
        {
            return null;
        }

        var version = ParseInstallerVersion(asset.Name);
        if (version is null)
        {
            return null;
        }

        var cur = currentVersion.Trim().TrimStart('v', 'V');
        if (CompareVersions(version, cur) <= 0)
        {
            return null;
        }

        return new InstallerUpdateInfo(version, info.ReleaseUrl, asset.Url, asset.Size);
    }

    /// <summary>从资产名解析安装器版本：VantaInstaller-win-x64-v0.3.2.exe → 0.3.2</summary>
    private static string? ParseInstallerVersion(string assetName)
    {
        const string marker = "VantaInstaller-win-x64-v";
        var idx = assetName.IndexOf(marker, StringComparison.OrdinalIgnoreCase);
        if (idx < 0)
        {
            return null;
        }

        var versionPart = assetName[(idx + marker.Length)..].TrimStart('v', 'V');
        var exeIdx = versionPart.IndexOf(".exe", StringComparison.OrdinalIgnoreCase);
        if (exeIdx > 0)
        {
            versionPart = versionPart[..exeIdx];
        }

        var parts = versionPart.Split('.');
        return parts.Length == 3 && parts.All(p => int.TryParse(p, out _))
            ? versionPart
            : null;
    }

    /// <summary>简单语义化版本比较：1.4.2 &gt; 1.4.1</summary>
    internal static int CompareVersions(string a, string b)
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

    /// <summary>
    /// 查询最新 Release（仅正式版，非草稿/预发布）。
    /// </summary>
    public static async Task<UpdateInfo?> CheckLatestAsync(CancellationToken ct = default)
        => await CheckReleaseEndpointAsync("latest", ct);

    /// <summary>按版本查询正式 Release，供安装前读取 GitHub 提供的资产 SHA-256。</summary>
    public static async Task<UpdateInfo?> CheckVersionAsync(string version, CancellationToken ct = default)
    {
        var normalized = version.Trim().TrimStart('v', 'V');
        return await CheckReleaseEndpointAsync($"tags/v{normalized}", ct);
    }

    private static async Task<UpdateInfo?> CheckReleaseEndpointAsync(string endpoint, CancellationToken ct)
    {
        using var http = new HttpClient();
        http.DefaultRequestHeaders.UserAgent.ParseAdd("VantaInstaller/0.3.2");
        http.DefaultRequestHeaders.Accept.ParseAdd("application/vnd.github+json");
        http.DefaultRequestHeaders.Add("X-GitHub-Api-Version", "2022-11-28");
        http.Timeout = TimeSpan.FromSeconds(15);

        var url = $"https://api.github.com/repos/{Repo}/releases/{endpoint}";
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
                var digest = item.TryGetProperty("digest", out var d) ? d.GetString() : null;
                var sha256 = NormalizeSha256Digest(digest);
                if (!string.IsNullOrEmpty(name))
                {
                    assets.Add(new ReleaseAsset(name, assetUrl, size, sha256));
                }
            }
        }

        return new UpdateInfo(tag, html, published, assets);
    }

    private static string? NormalizeSha256Digest(string? digest)
    {
        const string prefix = "sha256:";
        if (string.IsNullOrWhiteSpace(digest)
            || !digest.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        var value = digest[prefix.Length..].Trim();
        return value.Length == 64 && value.All(Uri.IsHexDigit) ? value.ToUpperInvariant() : null;
    }

    /// <summary>
    /// 从最新正式 Release 中找到镜像测速样本。
    /// 优先取 01 base 包（体积足够大，能填满测速采样窗口，避免小样本提前 EOF 导致数值失真）；
    /// 找不到时回退到体积最大的 .7z 资产。
    /// </summary>
    public static ReleaseAsset? FindProbeAsset(UpdateInfo info)
    {
        var archives = info.Assets
            .Where(asset => asset.Name.EndsWith(".7z", StringComparison.OrdinalIgnoreCase))
            .ToList();
        if (archives.Count == 0)
        {
            return null;
        }

        return archives.FirstOrDefault(asset =>
                   asset.Name.StartsWith("01-mpv-base-", StringComparison.OrdinalIgnoreCase))
               ?? archives.OrderByDescending(asset => asset.Size).First();
    }
}
