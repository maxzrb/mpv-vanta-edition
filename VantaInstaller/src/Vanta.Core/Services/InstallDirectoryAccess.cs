namespace Vanta.Core.Services;

/// <summary>检查安装位置的基本写入权限；探针不创建实际安装目录。</summary>
public static class InstallDirectoryAccess
{
    public static string? GetWriteError(string directory)
    {
        if (string.IsNullOrWhiteSpace(directory))
        {
            return "请选择安装目录。";
        }

        try
        {
            var target = Path.GetFullPath(directory);
            var existing = target;
            while (!Directory.Exists(existing))
            {
                if (File.Exists(existing))
                {
                    return $"安装路径被同名文件占用：{existing}";
                }
                existing = Path.GetDirectoryName(existing);
                if (string.IsNullOrEmpty(existing))
                {
                    return $"找不到安装路径所在的磁盘或父目录：{target}";
                }
            }

            // 新装需同时具备创建子目录和写入文件的权限；已有目录则直接测试文件写入。
            string? probeDirectory = null;
            try
            {
                var probeRoot = existing;
                if (!Directory.Exists(target))
                {
                    probeDirectory = Path.Combine(existing, $".vanta-write-probe-{Guid.NewGuid():N}");
                    Directory.CreateDirectory(probeDirectory);
                    probeRoot = probeDirectory;
                }

                var probeFile = Path.Combine(probeRoot, $".vanta-write-probe-{Guid.NewGuid():N}.tmp");
                using var probe = new FileStream(probeFile, FileMode.CreateNew, FileAccess.Write,
                    FileShare.None, 1, FileOptions.DeleteOnClose);
                probe.WriteByte(0);
            }
            finally
            {
                // 仅删除本次创建的空探针目录，不递归处理任何用户目录。
                if (probeDirectory is not null && Directory.Exists(probeDirectory))
                {
                    Directory.Delete(probeDirectory);
                }
            }

            return null;
        }
        catch (Exception ex) when (ex is UnauthorizedAccessException or IOException
            or ArgumentException or NotSupportedException or System.Security.SecurityException)
        {
            return $"无法写入安装目录：{directory}。请选择当前账户可写的目录；"
                + $"若要使用受保护目录，请先确认权限。详细信息：{ex.Message}";
        }
    }
}
