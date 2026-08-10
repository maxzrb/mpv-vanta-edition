using System.Text.Json;

namespace Vanta.Core.Services;

/// <summary>
/// 安装器用户级设置存储（不写入 mpv 目录）。
/// 存储位置：%LOCALAPPDATA%\VantaInstaller\settings.json
/// - LastInstallDirectory：记忆上次安装位置（安装成功写入 / 卸载成功清除）
/// - ManualMpvPath：用户手动指定的已安装 mpv 位置（优先级高于记忆位置）
/// - ManualBackupPath：用户手动指定的配置备份目录位置
/// </summary>
public static class InstallLocationStore
{
    private sealed class StoreData
    {
        public string? LastInstallDirectory { get; set; }
        public string? ManualMpvPath { get; set; }
        public string? ManualBackupPath { get; set; }
    }

    private static string StorePath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "VantaInstaller",
        "settings.json");

    /// <summary>读取持久化设置（无记录/损坏返回空对象）</summary>
    private static StoreData Read()
    {
        try
        {
            if (!File.Exists(StorePath))
            {
                return new StoreData();
            }
            var json = File.ReadAllText(StorePath);
            return JsonSerializer.Deserialize<StoreData>(json) ?? new StoreData();
        }
        catch
        {
            return new StoreData();
        }
    }

    /// <summary>写回持久化设置（失败不影响主流程）</summary>
    private static void Write(StoreData data)
    {
        try
        {
            var dir = Path.GetDirectoryName(StorePath);
            if (dir is not null)
            {
                Directory.CreateDirectory(dir);
            }
            File.WriteAllText(StorePath, JsonSerializer.Serialize(data));
        }
        catch
        {
            // 记忆失败不影响主流程
        }
    }

    /// <summary>读取上次安装位置（无记录返回 null）</summary>
    public static string? GetLastInstallDirectory()
        => string.IsNullOrWhiteSpace(Read().LastInstallDirectory)
            ? null
            : Read().LastInstallDirectory;

    /// <summary>保存上次安装位置（传 null 清除）</summary>
    public static void SaveLastInstallDirectory(string? directory)
    {
        var data = Read();
        data.LastInstallDirectory = string.IsNullOrWhiteSpace(directory) ? null : directory;
        Write(data);
    }

    /// <summary>读取用户手动指定的已安装 mpv 位置（无记录返回 null）</summary>
    public static string? GetManualMpvPath()
        => string.IsNullOrWhiteSpace(Read().ManualMpvPath)
            ? null
            : Read().ManualMpvPath;

    /// <summary>保存用户手动指定的已安装 mpv 位置（传 null 清除）</summary>
    public static void SaveManualMpvPath(string? directory)
    {
        var data = Read();
        data.ManualMpvPath = string.IsNullOrWhiteSpace(directory) ? null : directory;
        Write(data);
    }

    /// <summary>读取用户手动指定的配置备份目录（无记录返回 null）</summary>
    public static string? GetManualBackupPath()
        => string.IsNullOrWhiteSpace(Read().ManualBackupPath)
            ? null
            : Read().ManualBackupPath;

    /// <summary>保存用户手动指定的配置备份目录（传 null 清除）</summary>
    public static void SaveManualBackupPath(string? directory)
    {
        var data = Read();
        data.ManualBackupPath = string.IsNullOrWhiteSpace(directory) ? null : directory;
        Write(data);
    }
}
