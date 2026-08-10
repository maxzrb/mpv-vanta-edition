using System.Diagnostics;
using System.Text;

namespace Vanta.Core.Services;

/// <summary>
/// 镜像连通性测速：逐个对 GitHub 官方源与每个镜像做稳定吞吐测速。
/// 方法：预热跳过握手/TTFB，固定 2 秒采样窗口计算吞吐（避免小样本与握手时间干扰）。
/// </summary>
public static class MirrorProbeService
{
    /// <summary>测速采样窗口（毫秒）：固定时长测吞吐</summary>
    private const int ProbeWindowMs = 2000;

    /// <summary>测速最大拉取字节数（8MB，防超快链路无限拉取）</summary>
    private const long MaxProbeBytes = 8 * 1024 * 1024;

    /// <summary>预热字节数（8KB，覆盖连接/TLS/首字节，不计入测速）</summary>
    private const long WarmupBytes = 8 * 1024;

    /// <summary>探测结果</summary>
    public sealed record ProbeResult(DownloadMirror Mirror, bool IsAvailable, long ElapsedMs, long Downloaded)
    {
        /// <summary>估算速度（字节/秒），基于实际下载字节数与耗时</summary>
        public double SpeedBytesPerSec =>
            IsAvailable && ElapsedMs > 0 && Downloaded > 0
                ? Downloaded * 1000.0 / ElapsedMs
                : 0;

        /// <summary>人类可读速度</summary>
        public string SpeedText
        {
            get
            {
                if (!IsAvailable)
                {
                    return "—";
                }
                var mb = SpeedBytesPerSec / (1024.0 * 1024.0);
                if (mb >= 1)
                {
                    return $"{mb:0.0} MB/s";
                }
                var kb = SpeedBytesPerSec / 1024.0;
                return $"{kb:0} KB/s";
            }
        }

        /// <summary>状态文本（仅采样耗时；不可用时显示不可用，避免与速度列重复）</summary>
        public string StatusText => IsAvailable
            ? $"采样{ElapsedMs}ms"
            : "不可用";
    }

    /// <summary>
    /// 对指定 URL 逐个测速所有镜像（官方源也测），按可用性与吞吐降序返回。
    /// 逐个串行测速，避免并发抢带宽导致数值失真。
    /// </summary>
    /// <param name="originalUrl">GitHub 原始下载地址</param>
    /// <param name="mirrors">候选镜像（null 时用全部）</param>
    /// <param name="onProgress">每个镜像开始测速时的回调（用于 UI 展示进度）</param>
    /// <param name="ct">取消令牌</param>
    public static async Task<IReadOnlyList<ProbeResult>> ProbeAsync(
        string originalUrl,
        IEnumerable<DownloadMirror>? mirrors = null,
        Action<string>? onProgress = null,
        CancellationToken ct = default)
    {
        var candidates = (mirrors ?? MirrorRegistry.All).ToList();
        var results = new List<ProbeResult>(candidates.Count);

        for (int i = 0; i < candidates.Count; i++)
        {
            ct.ThrowIfCancellationRequested();
            onProgress?.Invoke($"正在测试 {candidates[i].Name}（{i + 1}/{candidates.Count}）…");
            results.Add(await ProbeOneAsync(candidates[i], originalUrl, ct));
        }

        return results
            .OrderBy(r => r.IsAvailable ? 0 : 1)
            .ThenByDescending(r => r.SpeedBytesPerSec)
            .ToList();
    }

    /// <summary>探测单个镜像</summary>
    private static async Task<ProbeResult> ProbeOneAsync(
        DownloadMirror mirror,
        string originalUrl,
        CancellationToken ct)
    {
        var url = mirror.Resolve(originalUrl);
        try
        {
            using var http = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(15),
            };
            http.DefaultRequestHeaders.UserAgent.ParseAdd("VantaInstaller/0.2");
            http.DefaultRequestHeaders.Range = new System.Net.Http.Headers.RangeHeaderValue(0, MaxProbeBytes - 1);

            using var response = await http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, ct);
            if (!response.IsSuccessStatusCode && response.StatusCode != System.Net.HttpStatusCode.PartialContent)
            {
                return new ProbeResult(mirror, false, 0, 0);
            }

            await using var stream = await response.Content.ReadAsStreamAsync(ct);
            var buffer = new byte[64 * 1024];

            // 预热：读完首批 8KB，覆盖连接/TLS/首字节延迟，不计入测速
            long warm = 0;
            while (warm < WarmupBytes)
            {
                var read = await stream.ReadAsync(buffer, ct);
                if (read <= 0)
                {
                    break;
                }
                warm += read;
            }

            if (warm == 0)
            {
                return new ProbeResult(mirror, false, 0, 0);
            }

            // 固定窗口测稳定吞吐
            var sw = Stopwatch.StartNew();
            long total = 0;
            while (sw.ElapsedMilliseconds < ProbeWindowMs && total < MaxProbeBytes)
            {
                ct.ThrowIfCancellationRequested();
                var read = await stream.ReadAsync(buffer, ct);
                if (read <= 0)
                {
                    break;
                }
                total += read;
            }
            sw.Stop();

            if (total == 0)
            {
                return new ProbeResult(mirror, false, sw.ElapsedMilliseconds, 0);
            }

            return new ProbeResult(mirror, true, sw.ElapsedMilliseconds, total);
        }
        catch
        {
            return new ProbeResult(mirror, false, 0, 0);
        }
    }
}
