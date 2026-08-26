using System.IO;

namespace Vanta.Core.Services;

/// <summary>
/// 一键升级增量包下载：把最新 Release 的全部压缩包资产（01~04，含 02 分卷）
/// 按镜像顺序下载到指定目录，已存在且大小一致的自动跳过（支持 aria2 断点续传重试）。
/// </summary>
public static class UpgradePackageDownloader
{
    /// <summary>
    /// 取 Release 中全部增量包资产（文件名含 .7z 的资产，含分卷 .7z.001/.002，
    /// 排除 VantaInstaller 自身 exe），按文件名排序保证 01→04 下载顺序。
    /// </summary>
    public static IReadOnlyList<UpdateService.ReleaseAsset> GetArchiveAssets(UpdateService.UpdateInfo info) =>
        info.Assets
            .Where(a => a.Name.Contains(".7z", StringComparison.OrdinalIgnoreCase)
                        && !a.Name.StartsWith("VantaInstaller", StringComparison.OrdinalIgnoreCase))
            .OrderBy(a => a.Name, StringComparer.OrdinalIgnoreCase)
            .ToList();

    /// <summary>
    /// 逐个下载全部增量包。单文件失败按镜像顺序自动降级（与安装器自更新一致：
    /// ModelScope → GitHub 官方直连）；任一文件最终失败即抛出异常终止升级。
    /// </summary>
    /// <param name="info">最新 Release 信息</param>
    /// <param name="targetDirectory">下载目标目录</param>
    /// <param name="mirrors">镜像降级顺序</param>
    /// <param name="log">日志回调（后台线程）</param>
    /// <param name="progress">进度回调：已完成文件数、总文件数、当前文件百分比（无活动文件时为 0）</param>
    /// <param name="ct">取消令牌</param>
    public static async Task DownloadAllAsync(
        UpdateService.UpdateInfo info,
        string targetDirectory,
        IReadOnlyList<DownloadMirror> mirrors,
        Action<string> log,
        Action<int, int, int> progress,
        CancellationToken ct = default)
    {
        var assets = GetArchiveAssets(info);
        if (assets.Count == 0)
        {
            throw new InvalidOperationException("最新 Release 没有可下载的增量包资产。");
        }

        Directory.CreateDirectory(targetDirectory);
        var aria2 = new Aria2Service();
        await aria2.LocateAsync();

        var current = 0;
        void OnFileProgress(string fileName, int pct) => progress(current, assets.Count, pct);
        aria2.ProgressChanged += OnFileProgress;

        try
        {
            for (var i = 0; i < assets.Count; i++)
            {
                ct.ThrowIfCancellationRequested();
                current = i;
                var asset = assets[i];
                var full = Path.Combine(targetDirectory, asset.Name);

                if (File.Exists(full) && new FileInfo(full).Length == asset.Size)
                {
                    log($"已存在且大小一致，跳过：{asset.Name}");
                    progress(i + 1, assets.Count, 0);
                    continue;
                }

                log($"开始下载（{i + 1}/{assets.Count}）：{asset.Name}（{Models.VantaPackage.FormatSize(asset.Size)}）");
                await aria2.DownloadWithMirrorsAsync(
                    asset.Url,
                    targetDirectory,
                    mirrors,
                    asset.Name,
                    ct: ct);
                log($"下载完成：{asset.Name}");
                progress(i + 1, assets.Count, 0);
            }
        }
        finally
        {
            aria2.ProgressChanged -= OnFileProgress;
        }
    }

    /// <summary>一键升级默认镜像顺序：ModelScope 国内直连 → GitHub 官方直连</summary>
    public static IReadOnlyList<DownloadMirror> DefaultMirrors() =>
    [
        MirrorRegistry.Find("modelscope")!,
        MirrorRegistry.Find("official")!,
    ];
}
