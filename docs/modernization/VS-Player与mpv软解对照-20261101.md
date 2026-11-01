# VS Player 与 mpv 的 8K AV1 软解对照

本机本片的结论是：CPU 软解吞吐不足，同时两个播放器在过载时采用不同的追赶和音频恢复策略。VS Player 不能据“画面看着顺”判定已正常完成 8K 48 fps 音画同步播放；其原包核心可复现输入音频非零、输出静音、画面落后时钟的异常状态。未修改生产配置、播放器用户 INI 或版本；全程使用命令行、IPC、文件／日志和原生诊断 API，没有使用 computer-use。

## 环境与材料

- CPU：Intel i5-12600KF，16 个逻辑处理器；GPU：AMD Radeon RX 6600。
- 视频：`C:\Users\maxzr\Downloads\ChouKaguya432048-Part.mkv`，1,640,999,953 字节；AV1 Main、7680×4320、10-bit 4:2:0、约 47.952 fps、约 117 Mb/s；AAC LC 48 kHz、5.1 声道，附 ASS 字幕。
- VS：`D:\tmp\VS-Player.exe`，1.0.16。外层自解包程序中的 `vs-player.exe`／`FFF.Native.dll` 与实际测试缓存文件 SHA-256 一致，具体哈希见 JSON。外层程序不继承日志句柄并强制原目录配置，因此对实际内层 exe 设置独立 `VSR_PLAYER_CONFIG`，复制原 INI，音量 76%、未静音、软件模式 1；没有改原 INI。
- 源码实取自 `user-Wing/VS-Renderer-GUI`，提交 `deefd4f8effc028e2bfea69fca10e859d8ff16cd`（1.0.16）；判断同时使用源码和实际二进制观测，没有仅凭 notes 推断。

## mpv：解码吞吐构成硬限制

使用完整配置隔离副本及 `--no-config`，均固定 `gpu-next`、D3D11、1280×720、软件 libdav1d。音频开启组启用 WASAPI 并静音以保留输出管线；音频关闭组为 `--audio=no`。逐组运行，不与 VS 或其他基准同时竞争 CPU。画面位置由 `time-pos` 获取，不能将其推进比例解释为音频速度。

| 条件 | 采样墙钟 | time-pos 推进 | VO 丢帧增量 | 最后声画差 |
|---|---:|---:|---:|---:|
| 完整配置，音频管线开启 | 20.44 秒 | 10.41 秒 | 436 | 11.05 秒 |
| 完整配置，关闭音频 | 20.30 秒 | 10.01 秒 | 372 | 无音频 |
| `--no-config`，音频管线开启 | 21.15 秒 | 10.00 秒 | 413 | 8.08 秒 |
| 完整配置，线程／帧延迟均设 32 | 20.89 秒 | 11.22 秒 | 516 | 10.14 秒 |

另以无配置、无音频、`vo=null`、`untimed`、不丢帧、32 线程／32 帧延迟测试纯解码：960 帧约用 45.42 秒，约 21 fps，低于片源约 48 fps。它不包含 GPU 上传／缩放／显示。移除完整配置或音频都没有恢复实时，不能将本次卡顿主要归因于 uosc、菜单脚本或音频负担。线程增大也未解决。

## VS：追赶触发，但没有恢复正常同步

完整播放器隔离运行 40 秒，默认追赶日志实际出现：

```text
CATCHUP references=1 lag_ms=4736 key_pts=5214 size=1509181
```

相同测试仅设置 `VSR_SW_REALTIME_CATCHUP=0` 时没有该事件。INI 周期保存的位置可核对播放时钟持续前进，但它不能作为画面进度证据。

[实际源码补丁](https://github.com/user-Wing/VS-Renderer-GUI/blob/deefd4f8effc028e2bfea69fca10e859d8ff16cd/patches/3fp-api20-vsrenderer-1.0.10.patch#L1477) 对 8K CFR AV1 软件解码设置参考帧追赶；进入后使用 `AVDISCARD_NONREF`。这会少解部分非参考画面，不能等同于原始每帧正常播放，也不是只显示关键帧。

随后直接调用原包同一 DLL 的 API 20 诊断接口，在自有 1280×720 渲染测试窗口中保留音频输出、软件模式及默认自适应线程，从 10 秒起播。配置／快照分别按头文件验证 112／464 字节，关键字段偏移与源码静态断言相同。以下取启动后第 15 秒至约第 34 秒的稳定采样：

| 同一核心对照 | 默认追赶开启 | 仅关闭追赶 |
|---|---:|---:|
| 采样墙钟 | 19.12 秒 | 19.09 秒 |
| 播放时钟推进 | 19.12 秒 | 19.09 秒 |
| 画面 PTS 推进 | 15.56 秒 | 9.91 秒 |
| 采样末尾画面落后时钟 | 6.43 秒 | 12.18 秒 |
| 核心接收用于呈现的画面速率 | 约 21.19 帧／秒 | 约 21.16 帧／秒 |
| 补入静音，按 48 kHz 折算 | 19.11 秒 | 19.11 秒 |
| 丢弃迟到／重叠音频，按 48 kHz 折算 | 15.62 秒 | 9.90 秒 |
| 输出电平为零的快照 | 39／39 | 39／39 |

两组输入电平均持续非零，AAC 在解码；末尾输出双声道电平均为零。软件追赶开启组的实际 `softwareVideoReferenceOnly=true`、切换计数 1，关闭组为 false／0。线程与帧延迟均为 8。这里的“接收用于呈现”是核心计数口径，不是物理屏幕实测 FPS；Qt 外层未包含在这组原生核心测试中，不能拿该速率与 mpv 直接计算性能优劣百分比。

## 无声定位：高负载恢复链路持续补静音并丢弃迟到音频

[WASAPI 实现补丁](https://github.com/user-Wing/VS-Renderer-GUI/blob/deefd4f8effc028e2bfea69fca10e859d8ff16cd/patches/3fp-api20-vsrenderer-1.0.10.patch#L730) 在播放欠载时补入静音并继续累计媒体帧；恢复期遇到落后于已推进时间线的音频，又按重叠丢弃。运行时计数与此行为一致：播放时钟继续走，但晚到音频不能恢复连续有效输出。欠载事件计数停在 3 并不表示之后有声，必须同时看静音帧／丢弃帧和电平。

最后用同一原包 DLL、同一片源、同一音量／输出设备，通过其 `SetClockOnly` 关闭内部视频解码，保留音频解码输出。连续运行约 20 秒：音频输出电平恢复非零；欠载 0、补静音 0、丢弃重叠音频 0。这排除了本次静音只是片源无音轨、AAC 不支持或原设置主动静音的解释，定位到高负载视频链路下的音频恢复问题。没有进行物理扬声器录音，结论是软件输出链路的复现证据。

因此可参考它对 8K AV1 的队列／追赶思路，但不能照搬当前恢复行为。mpv 本次表现为音频持续而视频掉队、丢帧；VS 则在维持时钟与参考帧追赶的同时进入持续静音，视频仍落后数秒。两者都未在本机实现此片的正常全帧软解播放，无法据此得出 VS 整体解码性能明显强于 mpv。

## 复现记录

汇总：`docs/modernization/vs-player-comparison-20261101.json`。

本地原始材料保留在 `tmp/vs-player-compare-20261101/`：`measure_mpv.py`、`mpv-results.json`、`measure_vs_app.py`、完整程序两组日志和 `vs-app-results.json`、`measure_vs_native.py`、`vs-native-{1,0,audio}.json`／日志，以及实取源码。mpv 日志在 `tmp/modernization/validation/vscompare-*.log`。这些为本地诊断材料，不进入公开包。

## 追加：mpv 过载参考帧追赶的可行性

用户追问 mpv 能否实现类似追赶。核查当前二进制同提交源码：mpv 原生具备 `framedrop=decoder+vo`、`vd-lavc-framedrop=nonref`，但当前 FFmpeg libdav1d 只在初始化读取 `skip_frame`，映射到 `decode_frame_type`。因此 mpv 播放中逐包改 `AVCodecContext.skip_frame` 不等于 libdav1d 同步切换参考帧解码模式。

同片无配置对照中，单启 `decoder+vo` 未明显改善；解码丢帧统计的增长也不能证明 dav1d 已减少相应解码工作。另一组从启动设置 `vd-lavc-skipframe=nonref`，末尾 AV 差为 -0.001024 秒；运行中改回 default 后末尾为 3.299801 秒；再改回 nonref 后末尾为 0.004295 秒。参考帧模式可有效追赶，但属于减少原始画面的播放策略，并非完整 48 fps 解码性能提升。

必须保留失败证据：后两次运行中 set 会触发视频解码器重建，出现 `Error parsing OBU data`，第一次重建同时记录一次音频欠载。不能将可写参数、瞬时 AV 差改善称为平滑切换验收通过。可靠自动功能需要关键帧安全重建／重新定位、进入退出迟滞、最短驻留／冷却，避开跳转、暂停、逐帧与切集；恢复完整解码时也要同样处理。脚本可做控制与有定位的切换，若要求无明显停顿的连续码流切换，需要进一步处理核心或 FFmpeg／dav1d 的解码器生命周期。不能持久化临时 nonref 解码状态。

建议功能入口为“视频 → 播放性能 → 过载追赶”直接开关，用户仅保存该功能开关，内部降级按当前文件临时启用；本轮仅验证可行性，尚未修改生产脚本或启用自动策略。

源码依据：[mpv 显示端与解码端丢帧说明](https://github.com/mpv-player/mpv/blob/36bf3d529/DOCS/man/options.rst#L1248)、[mpv 解码丢帧处理](https://github.com/mpv-player/mpv/blob/36bf3d529/video/decode/vd_lavc.c#L1189)、[FFmpeg libdav1d 初始化](https://github.com/FFmpeg/FFmpeg/blob/5d4755f7d/libavcodec/libdav1d.c#L236)。原始实取文件、两个测量脚本与结果在 `tmp/overload-catchup-20261101`，精简记录为 `docs/modernization/mpv-overload-feasibility-20261101.json`，日志在 `tmp/modernization/validation/overload-*.log`。
