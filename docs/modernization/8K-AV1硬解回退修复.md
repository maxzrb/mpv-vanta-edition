# ChouKaguya 8K AV1 软解回退排查与修复

日期：2026-10-05。本机 RX 6600，mpv shinchiro 20261004；用户片段 `ChouKaguya432048-Part.mkv`，大小 1,640,999,953 字节，容器时长 111.874 秒。

## 结论

回退来自当前配置的迟到硬解切换。原默认 `d3d11va-copy` 已成功解码，`8k-fix` 等 `video-params` 可读后才把 hwdec 改为 auto-safe，导致解码器在处理 AV1 数据过程中重建。完整脚本配置下出现 `Invalid repeated frame header OBU`／`Failed to read packet`，mpv 尝试其他硬解后回退软件解码。

本片源实际是 AV1 Main、7680×4320、47.952fps、YUV420 10bit、BT.709／BT.1886、有限范围的 SDR；音频 AAC 5.1，含 ASS 字幕。硬件支持不是本次回退的阻碍，ICC／HDR 目标也没有导致此回退。不能据这个定位排除片源其他位置或其他设备上的不同问题。

## 对照证据

| 条件 | 本机观察 |
|---|---|
| 最小配置，启动即指定 d3d11va | 首帧和后续采样硬解成功；快进仍保持 d3d11va |
| 最小配置，启动即指定 d3d11va-copy | 首帧成功输出 P010 |
| 原完整配置 | 先复制硬解成功，迟到 8k-fix 修改 hwdec 后报 AV1 解码错误，实际 hwdec-current=no |
| 原配置禁用外部脚本 | 短测未回退；说明触发受初始化和缓存时序影响，不能据此单独指责某个界面脚本 |
| 完整配置，启动即指定 auto-safe | 未复现 AV1 硬解错误／软解回退 |
| 修复后完整配置，三次启动／快进／小文件切换／切回 | 大片源全部保持 d3d11va，小文件恢复 d3d11va-copy，无硬解错误与软件回退 |

首轮两帧测试未覆盖稍后发生的回退；最终采用持续播放、快进和切片，并检查实际 hwdec-current 与日志。时间推进和掉帧采样不作为长期性能成绩。已有 LG HDR60 极限吞吐结论不因此改变。

## 修正

新增 MIT 本地脚本 `portable_config/scripts/hwdec-select.lua`，使用 [mpv on_preloaded 钩子](https://mpv.io/manual/master/#hooks) 在轨道初始化前读取 track-list 的 demux-w／demux-h。符合既有大分辨率阈值时，使用 file-local-options/hwdec 选择 auto-safe，当前文件结束由 mpv 清除。

保留主配置默认复制硬解；仅对既有 d3d11va-copy、D3D11 输出环境选择大分辨率路线，不覆盖用户显式软解或其他后端。单视频轨或显式指定轨道可判定，多视频轨自动选择及尺寸未知时保守保持原值；不在播放中再尝试补切后端。

`8k-fix` 配置组保留为手动兼容入口，移除自动条件，避免与预加载脚本竞争。单纯把条件改成 current-tracks/video/demux-w 仍会迟到，已实际复现并放弃：on_preloaded 时 current-tracks/video 尚未选定，而 track-list 已有容器尺寸。

当前规则减少解码后拷贝，不保证任意 8K48／60 持续实时，也不改变色彩精度、同步或增强默认值。用户在运行中主动切换后端仍可能重建解码器，这不属于预加载选择保护范围。

## 验证与回退

`tools/test-hwdec-startup.py <本地大分辨率文件>`：真实三轮测试启动、30 秒精确快进、小文件切换和返回；同时核对选择日志早于硬解尝试。`test-hwdec-select.lua`：显式软解／其他后端、普通文件、未知尺寸、多视频轨、当前文件作用域检查。配置／语法检查通过：133 Lua、29 Python。

修改前配置备份为 `backup/hwdec-startup-20261005-002656/profiles.conf`；校验清单见 [硬解修正清单](hwdec-upgrade-manifest.json)。回退需要同时恢复该配置并把新增 hwdec-select.lua 移出自动加载目录；不要只恢复旧自动条件后保留两套自动策略。

原始技术日志与采样位于忽略目录 tmp/modernization/kaguya-hwdec 和 tmp/modernization/validation/hwdec-startup-*.log。完整配置日志可能包含自动目录播放列表，不公开；摘要结果只保存技术属性。本轮没有改源文件／驱动／Windows HDR，没有使用 Computer Use，没有打包或发布。
