namespace Vanta.Core.Services;

/// <summary>镜像解析方式</summary>
public enum MirrorKind
{
    /// <summary>前缀式 GitHub 加速代理：{BaseUrl}{原始URL}</summary>
    GitHubPrefix,

    /// <summary>
    /// ModelScope 数据集映射：BaseUrl 为数据集 ID（namespace/name），
    /// GitHub Release 资产按 {tag}/{文件名} 映射到
    /// https://modelscope.cn/api/v1/datasets/{BaseUrl}/repo?Revision=master&amp;FilePath=…（匿名直链，302 至 OSS）。
    /// </summary>
    ModelScopeDataset,
}

/// <summary>
/// 下载镜像。BaseUrl 为空 = 官方直连。
/// </summary>
public sealed record DownloadMirror(string Id, string Name, string? BaseUrl, MirrorKind Kind = MirrorKind.GitHubPrefix)
{
    /// <summary>是否官方直连</summary>
    public bool IsOfficial => string.IsNullOrEmpty(BaseUrl);

    /// <summary>
    /// 拼接镜像地址：前缀式镜像为 {BaseUrl}{原始URL}，ModelScope 数据集按 Release 资产名映射。
    /// </summary>
    public string Resolve(string originalUrl)
    {
        if (IsOfficial)
        {
            return originalUrl;
        }

        return Kind switch
        {
            MirrorKind.ModelScopeDataset => ResolveModelScopeDataset(originalUrl),
            _ => ResolveGitHubPrefix(originalUrl),
        };
    }

    /// <summary>前缀式：{BaseUrl}/{github.com/...}</summary>
    private string ResolveGitHubPrefix(string originalUrl)
    {
        var baseUrl = BaseUrl!.TrimEnd('/');
        return originalUrl.StartsWith("https://github.com", StringComparison.OrdinalIgnoreCase)
            ? $"{baseUrl}/{originalUrl.TrimStart('/')}"
            : originalUrl;
    }

    /// <summary>
    /// ModelScope 数据集映射：GitHub Release 资产 {tag}/{文件名} → 数据集同路径文件。
    /// 非 GitHub Release 地址不经此镜像（原样返回，由调用方降级到其它镜像）。
    /// </summary>
    private string ResolveModelScopeDataset(string originalUrl)
    {
        const string downloadMarker = "/releases/download/";
        if (!originalUrl.StartsWith("https://github.com/", StringComparison.OrdinalIgnoreCase))
        {
            return originalUrl;
        }

        var idx = originalUrl.IndexOf(downloadMarker, StringComparison.OrdinalIgnoreCase);
        if (idx < 0)
        {
            return originalUrl;
        }

        // 路径须为 {tag}/{文件名} 两级以上，否则视为非法 Release 地址
        var path = originalUrl[(idx + downloadMarker.Length)..].TrimStart('/');
        if (string.IsNullOrWhiteSpace(path) || !path.Contains('/'))
        {
            return originalUrl;
        }

        var datasetId = BaseUrl!.Trim('/');
        var filePath = Uri.EscapeDataString(path);
        return $"https://modelscope.cn/api/v1/datasets/{datasetId}/repo?Revision=master&FilePath={filePath}";
    }
}

/// <summary>
/// 内置镜像注册表（官方 + 已复测可用的 GitHub 加速镜像 + ModelScope 国内直连）。
/// </summary>
public static class MirrorRegistry
{
    /// <summary>全部镜像（官方直连排第一，ModelScope 国内直连次之，自建镜像固定放在列表末尾）</summary>
    public static IReadOnlyList<DownloadMirror> All { get; } =
    [
        new DownloadMirror("official", "官方直连（GitHub）", null),
        new DownloadMirror("modelscope", "ModelScope 魔搭（国内直连）", "AerithDream/mpv-vanta-edition", MirrorKind.ModelScopeDataset),
        new DownloadMirror("gh-proxy.com", "gh-proxy.com", "https://gh-proxy.com/"),
        new DownloadMirror("ghproxy.net", "ghproxy.net", "https://ghproxy.net/"),
        new DownloadMirror("gh.xxooo.cf", "gh.xxooo.cf", "https://gh.xxooo.cf/"),
        new DownloadMirror("dl-loliland", "AerithDream 下载加速（自建）", "https://dl.loliland.cn/"),
    ];

    /// <summary>按 Id 查找镜像</summary>
    public static DownloadMirror? Find(string id) =>
        All.FirstOrDefault(m => string.Equals(m.Id, id, StringComparison.OrdinalIgnoreCase));
}
