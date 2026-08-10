using Vanta.Core.Models;

namespace Vanta.Core.Services;

/// <summary>
/// 设置中心可调的 mpv.conf 配置项定义。
/// 默认值 = 当前 mpv.conf 的实际生效值（用户现状），仅覆盖安全、高频项。
/// </summary>
public static class MpvSettingsSchema
{
    /// <summary>构建全部可调配置项</summary>
    public static List<MpvOption> Build()
    {
        var list = new List<MpvOption>
        {
            // ===== 界面 =====
            new()
            {
                Key = "geometry",
                DisplayName = "窗口大小（分辨率）",
                Group = "界面",
                Type = MpvOptionType.Choice,
                DefaultValue = "",
                Choices =
                [
                    new MpvChoice("", "原始大小（自动适配）"),
                    new MpvChoice("1280x720", "1280 × 720"),
                    new MpvChoice("1366x768", "1366 × 768"),
                    new MpvChoice("1600x900", "1600 × 900"),
                    new MpvChoice("1920x1080", "1920 × 1080"),
                    new MpvChoice("2560x1440", "2560 × 1440"),
                    new MpvChoice("3840x2160", "3840 × 2160"),
                ],
                Description = "固定窗口分辨率；选择后自动停用窗口自动适配（autofit-smaller）。",
            },
            new()
            {
                Key = "window-corners",
                DisplayName = "窗口圆角",
                Group = "界面",
                Type = MpvOptionType.Choice,
                DefaultValue = "roundsmall",
                Choices =
                [
                    new MpvChoice("default", "系统默认"),
                    new MpvChoice("donotround", "直角"),
                    new MpvChoice("round", "圆角"),
                    new MpvChoice("roundsmall", "小圆角"),
                ],
            },
            new()
            {
                Key = "ontop",
                DisplayName = "窗口置顶",
                Group = "界面",
                Type = MpvOptionType.Bool,
                DefaultValue = "yes",
                Description = "播放器窗口始终置顶。",
            },
            new()
            {
                Key = "fs",
                DisplayName = "启动全屏",
                Group = "界面",
                Type = MpvOptionType.Bool,
                DefaultValue = "no",
                Description = "打开文件即全屏播放。",
            },
            new()
            {
                Key = "window-maximized",
                DisplayName = "启动最大化",
                Group = "界面",
                Type = MpvOptionType.Bool,
                DefaultValue = "no",
            },
            new()
            {
                Key = "window-affinity",
                DisplayName = "窗口关联（录屏排除）",
                Group = "界面",
                Type = MpvOptionType.Choice,
                DefaultValue = "default",
                Choices =
                [
                    new MpvChoice("default", "默认"),
                    new MpvChoice("excludefromcmcapture", "排除采集/录屏"),
                    new MpvChoice("monitor", "监控模式"),
                ],
                Description = "excludefromcmcapture：窗口完全排除在屏幕录制/采集之外。",
            },

            // ===== 解码 =====
            new()
            {
                Key = "hwdec",
                DisplayName = "硬件解码",
                Group = "解码",
                Type = MpvOptionType.Choice,
                DefaultValue = "auto-copy",
                Choices =
                [
                    new MpvChoice("auto-copy", "自动（copy 模式，推荐）"),
                    new MpvChoice("d3d11va-copy", "D3D11VA copy"),
                    new MpvChoice("d3d12va-copy", "D3D12VA copy"),
                    new MpvChoice("nvdec-copy", "NVDEC copy"),
                    new MpvChoice("no", "软解（不用硬解）"),
                ],
                Description = "建议使用 *-copy 模式以保证滤镜/着色器正常；no 为纯软解。",
            },
            new()
            {
                Key = "gpu-api",
                DisplayName = "渲染接口",
                Group = "解码",
                Type = MpvOptionType.Choice,
                DefaultValue = "d3d11",
                Choices =
                [
                    new MpvChoice("d3d11", "D3D11（推荐）"),
                    new MpvChoice("vulkan", "Vulkan"),
                    new MpvChoice("opengl", "OpenGL"),
                ],
                Description = "Windows 原生渲染推荐 d3d11；改动影响面较大。",
            },

            // ===== 播放 =====
            new()
            {
                Key = "save-position-on-quit",
                DisplayName = "记住播放位置",
                Group = "播放",
                Type = MpvOptionType.Bool,
                DefaultValue = "yes",
            },
            new()
            {
                Key = "resume-playback-check-mtime",
                DisplayName = "恢复前校验文件",
                Group = "播放",
                Type = MpvOptionType.Bool,
                DefaultValue = "yes",
                Description = "文件内容变化时不误恢复旧进度。",
            },
            new()
            {
                Key = "keep-open",
                DisplayName = "播完保持打开",
                Group = "播放",
                Type = MpvOptionType.Choice,
                DefaultValue = "no",
                Choices =
                [
                    new MpvChoice("no", "关闭（默认）"),
                    new MpvChoice("yes", "保持打开"),
                    new MpvChoice("always", "始终保持并暂停"),
                ],
            },
            new()
            {
                Key = "loop-playlist",
                DisplayName = "播放列表循环",
                Group = "播放",
                Type = MpvOptionType.Choice,
                DefaultValue = "no",
                Choices =
                [
                    new MpvChoice("no", "不循环"),
                    new MpvChoice("inf", "循环播放列表"),
                ],
            },

            // ===== 音频 =====
            new()
            {
                Key = "audio-device",
                DisplayName = "音频输出设备",
                Group = "音频",
                Type = MpvOptionType.Text,
                DefaultValue = "auto",
                Description = "auto 自动；可填设备 ID，如 wasapi/{GUID}。",
            },
            new()
            {
                Key = "audio-exclusive",
                DisplayName = "音频独占",
                Group = "音频",
                Type = MpvOptionType.Bool,
                DefaultValue = "no",
                Description = "独占模式；遇到音频卡顿可尝试开启。",
            },
            new()
            {
                Key = "audio-normalize-downmix",
                DisplayName = "环绕下混防削波",
                Group = "音频",
                Type = MpvOptionType.Bool,
                DefaultValue = "no",
            },
            new()
            {
                Key = "volume",
                DisplayName = "启动音量",
                Group = "音频",
                Type = MpvOptionType.Slider,
                DefaultValue = "100",
                Min = 0,
                Max = 100,
                Description = "播放器启动时的音量（0-100）。",
            },

            // ===== 截图 =====
            new()
            {
                Key = "screenshot-format",
                DisplayName = "截图格式",
                Group = "截图",
                Type = MpvOptionType.Choice,
                DefaultValue = "webp",
                Choices =
                [
                    new MpvChoice("webp", "WebP"),
                    new MpvChoice("jpg", "JPEG"),
                    new MpvChoice("png", "PNG"),
                    new MpvChoice("jxl", "JPEG XL"),
                ],
            },
            new()
            {
                Key = "screenshot-webp-quality",
                DisplayName = "WebP 质量",
                Group = "截图",
                Type = MpvOptionType.Slider,
                DefaultValue = "85",
                Min = 1,
                Max = 100,
            },
            new()
            {
                Key = "screenshot-jpeg-quality",
                DisplayName = "JPEG 质量",
                Group = "截图",
                Type = MpvOptionType.Slider,
                DefaultValue = "90",
                Min = 1,
                Max = 100,
            },
        };

        return list;
    }
}
