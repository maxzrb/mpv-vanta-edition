namespace Vanta.Core.Services;

/// <summary>
/// GitHub 下载镜像。BaseUrl 为空 = 官方直连。
/// </summary>
public sealed record DownloadMirror(string Id, string Name, string? BaseUrl)
{
    /// <summary>是否官方直连</summary>
    public bool IsOfficial => string.IsNullOrEmpty(BaseUrl);

    /// <summary>
    /// 拼接镜像地址：前缀式镜像为 {BaseUrl}{原始URL}。
    /// </summary>
    public string Resolve(string originalUrl)
    {
        if (IsOfficial)
        {
            return originalUrl;
        }

        var baseUrl = BaseUrl!.TrimEnd('/');
        return originalUrl.StartsWith("https://github.com", StringComparison.OrdinalIgnoreCase)
            ? $"{baseUrl}/{originalUrl.TrimStart('/')}"
            : originalUrl;
    }
}

/// <summary>
/// 内置镜像注册表（官方 + 已复测可用的 GitHub 加速镜像）。
/// </summary>
public static class MirrorRegistry
{
    /// <summary>全部镜像（官方直连排第一，自建镜像固定放在列表末尾）</summary>
    public static IReadOnlyList<DownloadMirror> All { get; } =
    [
        new DownloadMirror("official", "官方直连（GitHub）", null),
        new DownloadMirror("gh-proxy.com", "gh-proxy.com", "https://gh-proxy.com/"),
        new DownloadMirror("ghproxy.net", "ghproxy.net", "https://ghproxy.net/"),
        new DownloadMirror("gh.xxooo.cf", "gh.xxooo.cf", "https://gh.xxooo.cf/"),
        new DownloadMirror("dl-loliland", "AerithDream 下载加速（自建）", "https://dl.loliland.cn/"),
    ];

    /// <summary>按 Id 查找镜像</summary>
    public static DownloadMirror? Find(string id) =>
        All.FirstOrDefault(m => string.Equals(m.Id, id, StringComparison.OrdinalIgnoreCase));
}
