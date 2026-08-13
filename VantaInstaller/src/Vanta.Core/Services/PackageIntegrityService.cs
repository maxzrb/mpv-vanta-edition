using System.Buffers;
using System.Security.Cryptography;
using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>使用 GitHub Release 资产摘要校验安装包。</summary>
public static class PackageIntegrityService
{
    private const int BufferSize = 4 * 1024 * 1024;

    /// <summary>
    /// 校验全部选中包文件。无法联网或 Release 未提供摘要时也返回风险结果，由界面决定是否继续。
    /// </summary>
    public static async Task<PackageIntegrityResult> VerifyAsync(
        IReadOnlyCollection<VantaPackage> packages,
        string version,
        IProgress<PackageIntegrityProgress>? progress = null,
        CancellationToken ct = default)
    {
        IReadOnlyDictionary<string, string> expectedHashes;
        string? referenceError = null;
        try
        {
            var release = await UpdateService.CheckVersionAsync(version, ct).ConfigureAwait(false);
            if (release is null)
            {
                expectedHashes = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                referenceError = $"未找到 v{version} 的 GitHub Release。";
            }
            else
            {
                expectedHashes = release.Assets
                    .Where(asset => !string.IsNullOrWhiteSpace(asset.Sha256))
                    .ToDictionary(asset => asset.Name, asset => asset.Sha256!, StringComparer.OrdinalIgnoreCase);
            }
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception ex)
        {
            expectedHashes = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            referenceError = $"无法读取 GitHub Release 哈希：{ex.Message}";
        }

        var paths = packages
            .SelectMany(package => package.Files.Select(file => Path.Combine(package.SourceDirectory, file)))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
        var items = await VerifyFilesAsync(paths, expectedHashes, progress, ct).ConfigureAwait(false);
        return new PackageIntegrityResult(items, referenceError);
    }

    /// <summary>使用指定摘要校验文件；独立入口便于离线自检和回归测试。</summary>
    public static async Task<IReadOnlyList<PackageIntegrityItem>> VerifyFilesAsync(
        IReadOnlyCollection<string> paths,
        IReadOnlyDictionary<string, string> expectedHashes,
        IProgress<PackageIntegrityProgress>? progress = null,
        CancellationToken ct = default)
    {
        var totalBytes = paths.Sum(path => File.Exists(path) ? new FileInfo(path).Length : 0L);
        var processedBytes = 0L;
        var results = new List<PackageIntegrityItem>(paths.Count);

        foreach (var path in paths)
        {
            ct.ThrowIfCancellationRequested();
            var fileName = Path.GetFileName(path);
            if (!File.Exists(path))
            {
                results.Add(new PackageIntegrityItem(fileName, PackageIntegrityStatus.MissingFile, null, null, "文件不存在"));
                continue;
            }

            expectedHashes.TryGetValue(fileName, out var expected);
            try
            {
                var actual = await ComputeSha256Async(path, bytesRead =>
                {
                    var current = processedBytes + bytesRead;
                    var percent = totalBytes > 0 ? (int)Math.Clamp(current * 100 / totalBytes, 0, 100) : 100;
                    progress?.Report(new PackageIntegrityProgress(percent, fileName));
                }, ct).ConfigureAwait(false);

                var status = string.IsNullOrWhiteSpace(expected)
                    ? PackageIntegrityStatus.MissingReference
                    : string.Equals(actual, expected, StringComparison.OrdinalIgnoreCase)
                        ? PackageIntegrityStatus.Passed
                        : PackageIntegrityStatus.Mismatch;
                results.Add(new PackageIntegrityItem(fileName, status, expected, actual));
                processedBytes += new FileInfo(path).Length;
            }
            catch (OperationCanceledException)
            {
                throw;
            }
            catch (Exception ex)
            {
                results.Add(new PackageIntegrityItem(fileName, PackageIntegrityStatus.ReadError, expected, null, ex.Message));
                processedBytes += new FileInfo(path).Length;
            }
        }

        progress?.Report(new PackageIntegrityProgress(100, "校验完成"));
        return results;
    }

    private static async Task<string> ComputeSha256Async(
        string path,
        Action<long> reportBytesRead,
        CancellationToken ct)
    {
        await using var stream = new FileStream(
            path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.Read,
            BufferSize,
            FileOptions.Asynchronous | FileOptions.SequentialScan);
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        var buffer = ArrayPool<byte>.Shared.Rent(BufferSize);
        var totalRead = 0L;
        try
        {
            while (true)
            {
                var read = await stream.ReadAsync(buffer.AsMemory(0, BufferSize), ct).ConfigureAwait(false);
                if (read == 0)
                {
                    break;
                }
                hash.AppendData(buffer, 0, read);
                totalRead += read;
                reportBytesRead(totalRead);
            }
            return Convert.ToHexString(hash.GetHashAndReset());
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer);
        }
    }
}
