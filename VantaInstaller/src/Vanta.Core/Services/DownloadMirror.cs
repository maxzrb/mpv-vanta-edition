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
/// 内置镜像注册表（官方 + 常用 GitHub 加速镜像）。
/// </summary>
public static class MirrorRegistry
{
    /// <summary>全部镜像（官方直连排第一，其余按可用性排序）</summary>
    public static IReadOnlyList<DownloadMirror> All { get; } =
    [
        new DownloadMirror("official", "官方直连（GitHub）", null),
        new DownloadMirror("gh-proxy.com", "gh-proxy.com", "https://gh-proxy.com/"),
        new DownloadMirror("ghproxy.net", "ghproxy.net", "https://ghproxy.net/"),
        new DownloadMirror("ghfast.top", "ghfast.top", "https://ghfast.top/"),
        new DownloadMirror("mirror.ghproxy.com", "mirror.ghproxy.com", "https://mirror.ghproxy.com/"),
        new DownloadMirror("ghproxy.homeboyc.cn", "ghproxy.homeboyc.cn", "https://ghproxy.homeboyc.cn/"),
    ];

    /// <summary>按 Id 查找镜像</summary>
    public static DownloadMirror? Find(string id) =>
        All.FirstOrDefault(m => string.Equals(m.Id, id, StringComparison.OrdinalIgnoreCase));
}
