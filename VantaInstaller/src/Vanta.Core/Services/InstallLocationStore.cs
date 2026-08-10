using System.Text.Json;

namespace Vanta.Core.Services;

/// <summary>
/// 记忆上次安装位置（安装器用户级设置，不写入 mpv 目录）。
/// 存储位置：%LOCALAPPDATA%\VantaInstaller\settings.json
/// </summary>
public static class InstallLocationStore
{
    private sealed class StoreData
    {
        public string? LastInstallDirectory { get; set; }
    }

    private static string StorePath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "VantaInstaller",
        "settings.json");

    /// <summary>读取上次安装位置（无记录返回 null）</summary>
    public static string? GetLastInstallDirectory()
    {
        try
        {
            if (!File.Exists(StorePath))
            {
                return null;
            }
            var json = File.ReadAllText(StorePath);
            var data = JsonSerializer.Deserialize<StoreData>(json);
            return string.IsNullOrWhiteSpace(data?.LastInstallDirectory)
                ? null
                : data.LastInstallDirectory;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>保存上次安装位置（传 null 清除）</summary>
    public static void SaveLastInstallDirectory(string? directory)
    {
        try
        {
            var dir = Path.GetDirectoryName(StorePath);
            if (dir is not null)
            {
                Directory.CreateDirectory(dir);
            }
            var data = new StoreData { LastInstallDirectory = directory };
            File.WriteAllText(StorePath, JsonSerializer.Serialize(data));
        }
        catch
        {
            // 记忆失败不影响主流程
        }
    }
}
