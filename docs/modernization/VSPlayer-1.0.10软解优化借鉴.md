# VSPlayer 1.0.10 软解优化核查与 mpv 对照

日期：2026-10-11。样片为 `OP-yuv444p12-SWTest.mkv`，4K、约47.952fps、AV1 Professional、12-bit 4:4:4、FLAC＋ASS。

## 结论

可以借鉴，主要思路是增加真正可运行的帧并行任务、让视频解码不阻塞音频供给、减少上传等待和字幕重复工作。不是通过降低源分辨率、位深或色度实现。我们的 mpv 已采用相同的核心 32线程／32帧策略；本轮没有发现能够继续稳定提高呈现吞吐的配置捷径。

已增加默认关闭的 `AV1-SoftDecode-Async` 预设，用有界队列把视频解码移到独立线程。本机三轮20秒窗口没有音频欠载，但掉帧没有稳定改善，额外使用约0.6～0.7GiB内存，因此未改成默认。预设前后的源截图及原始FP16输出在两个精确时间点逐字节一致，保留当前HQ、线性缩小和色彩处理。

## 版本、来源与硬件差异

用户目录仍名为 `1.0.8Test`，实际活动包的 `release.json` 为 **1.0.10**；相邻 previous 目录为1.0.9。活动包 Native API实际为18。核对上游 `v1.0.10` 固定提交 `7042772f009e4fcfbbf2e570919ce9224b066e41`，对照原生补丁和随包验收文档；两包的 `avcodec-63.dll` 大小、SHA-256相同。因此1.0.9→1.0.10的变化不能解释成这次仅更换FFmpeg解码库。

作者的[1.0.9修复记录](https://github.com/user-Wing/VS-Renderer-GUI/blob/7042772f009e4fcfbbf2e570919ce9224b066e41/docs/fix-av1-vscap-1.0.9-20261010.md)使用Ryzen 7 7840HS，原生探针约37.8fps，最终GUI开字幕约24.8fps，明确未达满帧。[1.0.10验收](https://github.com/user-Wing/VS-Renderer-GUI/blob/7042772f009e4fcfbbf2e570919ce9224b066e41/docs/validation-1.0.10.md)换为Ryzen 9 7940HX＋RTX4070 Laptop，4K完整GUI的88秒计时段提交47.88fps、零丢帧和欠载。这两组同时存在硬件、字幕处理和输出路径差异，不能把所有收益归因于1.0.10单一改动。

本机仍为i5-12600KF（6P＋4E、16逻辑线程）／RX6600／约32GiB内存。对用户实际1.0.10 Native DLL进行独立窗口测试，软件解码、1280×720、Jinc2、预缩放关闭，**不含GUI字幕**：20.196秒窗口中新视频提交约40.21fps、视频丢弃159帧、音频欠载0；源尺寸3840×2160，最终显示接口报告10-bit。提交计数来自Native快照，不是物理屏幕光学测量，不能代表完整GUI。

我们的mpv使用HQ、SDR ACM FP16输出，与该原生10-bit显示路径不完全相同。没有为追平数字而切换成另一套缩放、量化或色彩算法。12-bit本身也不表示源为HDR。

## 它具体做了什么

| 改动 | 源码证据与作用 | mpv可借鉴程度 |
|---|---|---|
| 加深dav1d帧并行 | 至少4K的444p12取 `min(逻辑线程×2,32)`，并令 `max_frame_delay=workers`；不再用通用梯子反复重开dav1d | 已在本仓库实现，并增加可用内存预算和手动参数保护 |
| 解码与session分离 | 持久工作线程处理dav1d，最多8个压缩包、单帧输出交接；session继续负责音频、时间轴、呈现；seek/flush/free前停止工作线程 | mpv已有 `vd-queue-enable`，本轮验证并提供有界可选预设 |
| 平面动态上传 | 平面R8／R16贴图使用 `D3D11_USAGE_DYNAMIC`、`MAP_WRITE_DISCARD`，按RowPitch逐行复制；让驱动轮换存储，避免更新仍在采样的同一资源 | 需要修改libplacebo／mpv核心上传实现，不能靠Lua或配置直接复制该代码 |
| 减少字幕成本 | 已知Matroska字幕轨不重复探测其它视频／音频；仅提交可见字幕位图，坐标和画布不变；静态裁剪像素／位置一致时复用合成，动画继续更新 | mpv已有libass变化标记与紧凑位图打包；不能假设它存在同样的整屏透明画布问题 |
| 保持计数诚实 | 仅在有更新画面替代时丢弃迟到帧，1.0.10移除无音频CPU路径的落后重置时钟；区分提交fps、缺口、真正丢帧和媒体进度 | 保留mpv当前同步／丢帧策略；不放宽阈值或减速来冒充实时 |

主要实现见[完整Native补丁](https://github.com/user-Wing/VS-Renderer-GUI/blob/7042772f009e4fcfbbf2e570919ce9224b066e41/patches/3fp-api18-vsrenderer-1.0.10.patch)、[平面上传补丁](https://github.com/user-Wing/VS-Renderer-GUI/blob/7042772f009e4fcfbbf2e570919ce9224b066e41/patches/3fp-software-frame-upload.patch)、[1.0.10差量补丁](https://github.com/user-Wing/VS-Renderer-GUI/blob/7042772f009e4fcfbbf2e570919ce9224b066e41/patches/3fp-api18-vsrenderer-1.0.10-update.patch)和[字幕GUI](https://github.com/user-Wing/VS-Renderer-GUI/blob/7042772f009e4fcfbbf2e570919ce9224b066e41/src/player/PlayerSubtitles.cpp)。

1.0.10的新策略将8K420p10改为16／16，**本次4K444p12仍是32／32**。验收报告明确恢复为默认不在上传前降分辨率，也没有将无收益的纹理轮换／SSE上传实验纳入发行。本轮没有借用这些降质或未证实收益的路径。

## 与当前mpv核心的对应

核对本机mpv提交 `36bf3d529059a947d6700adefeab3b421e537c19`、libplacebo `0d043c7f6f79cd3687c023454bdacbe615e4d96f`，不是只看最新手册猜测：

- [decoder wrapper](https://github.com/mpv-player/mpv/blob/36bf3d529059a947d6700adefeab3b421e537c19/filters/f_decoder_wrapper.c)已有独立解码线程与[帧队列](https://github.com/mpv-player/mpv/blob/36bf3d529059a947d6700adefeab3b421e537c19/filters/f_async_queue.c)，传递帧引用，不改变像素精度。
- [队列选项说明](https://github.com/mpv-player/mpv/blob/36bf3d529059a947d6700adefeab3b421e537c19/DOCS/man/options.rst)明确队列默认关闭；限制由字节／帧数／秒数中最小者决定，可能增加内存和seek代价，启用需在解码器初始化前完成。没有将它全局用于硬解。
- [libplacebo D3D11纹理上传](https://github.com/haasn/libplacebo/blob/0d043c7f6f79cd3687c023454bdacbe615e4d96f/src/d3d11/gpu_tex.c)的CPU指针路径仍调用 `UpdateSubresource`。这与VSPlayer的动态平面路径不同，是值得进一步做核心实验的明确位置；目前没有测量过mpv替换上传实现的收益，也没有更换当前核心。
- 当前D3D11后端没有宣告映射缓冲支持，[gpu-next直接渲染分配](https://github.com/mpv-player/mpv/blob/36bf3d529059a947d6700adefeab3b421e537c19/video/out/vo_gpu_next.c)要求相应能力，故本次 `vd-lavc-dr=no` 对照不证明关闭DR本身带来提升，未据此更改默认。
- [libass处理](https://github.com/mpv-player/mpv/blob/36bf3d529059a947d6700adefeab3b421e537c19/sub/sd_ass.c)已有 `ass_render_frame` 变化标记与打包器；gpu-next按打包后的字幕区域上传／组合，不能把VSPlayer旧GUI的4K透明整屏成本直接套到mpv。

## 本机mpv串行对照

保持完整配置、HQ、线性缩小、SDR ACM FP16、FLAC音频和默认ASS字幕（sid=1），1280×720窗口；明确软件解码，实际32／32。从媒体10秒起播，推进到15秒后观测20秒。三轮包含正／反顺序；这里只报告播放器计数，媒体推进率约1不等于全部48帧呈现。

| 配置 | 三轮20秒呈现丢帧 | 三轮音频欠载次数 | 三轮最大绝对A/V差（秒） | 峰值工作集 |
|---|---|---|---|---|
| 当前默认，队列关闭 | 290／286／264 | 1／1／0 | 0.184／0.098／0.057 | 6.64～6.71GiB |
| 独立解码＋16帧／768MiB队列 | 322／289／282 | 0／0／0 | 0.102／0.109／0.134 | 7.24～7.39GiB |

队列在该窗口内改善了音频供给稳定性；平均掉帧反而由280变为297.7，不能称为视频吞吐提升。三轮20秒不足以证明整片无欠载。8帧队列的单次掉帧406，未选用；16帧＋DR关闭单次283，但其D3D11 DR路径本就不可用，未把波动当收益。

P/E调度额外对照：同一32／32完整播放，全部逻辑处理器掉帧224、欠载1；只用P核掉帧840、欠载4、最大A/V差0.636秒。两次仅为排除明显不适合本机的候选，没有修改日常进程亲和性或优先级。

## 已交付的可选预设与准确性验收

`portable_config/profiles.conf` 新增 `AV1-SoftDecode-Async`，默认不触发：仅设置软解和视频异步队列（16帧／768MiB）；原有自动dav1d并行脚本继续按内存预算工作。没有改变任何源格式、解码滤波、HQ、线性缩小、着色器、ACM／ICC／HDR或抖动选项。

仅在需要缓解重负载软解的音频欠载时，于播放前启动：

```powershell
& "C:\Program portable\mpv2\mpv.exe" --profile=AV1-SoftDecode-Async "C:\Users\maxzr\Downloads\OP-yuv444p12-SWTest.mkv"
```

此预设明确选择软件解码；不将它作为所有格式的日常配置。关闭这次播放器后正常启动即回到普通硬解优先策略。播放中直接应用profile不等同于重新创建解码器，本轮没有增加这种菜单入口。

常规配置与预设在10.010／25.004秒精确跳转、等待解码／呈现完成并暂停同一帧后：源高位深PNG和D3D11原始RGBA16F有效像素SHA-256逐字节一致，源格式与色彩元数据一致。像素测试去掉UI叠加干扰，性能对照仍保留完整UI和ASS。

可选预设的字幕选择、暂停精确跳转、停止后恢复profile及HEVC硬解参数恢复通过；没有Lua、解码或未知专用参数错误。色彩数值专项另以该预设运行，涵盖SDR ACM白点／1024灰阶、广色域SDR、PQ／HLG及线性缩小，软件输出通过；不替代物理屏幕色准测量。

本轮工作树保留此前修改；未更换核心、提交、发布或更改版本号。profile起始备份为 `backup/vs110-study-20261011/profiles.conf`。源代码与本地数据保存在忽略目录 `tmp/modernization/vs110-study/`：packages、native20、queues、affinity、pixel-proof、profile-lifecycle、color-profile/results，以及固定源码树；没有上传用户媒体或这些依赖。

## 2026-10-11 后续：现有核心的 Vulkan 路线

后续在保持 SDR ACM FP16/scRGB、原位深和 HQ 算法的条件下，找到 Vulkan＋异步解码队列的实际收益。三轮固定 32／32 短窗掉帧约减少九成，但整片后半段仍未满帧；详见 [Vulkan软解播放性能优化](Vulkan软解播放性能优化.md)。这里补充的是现有核心的另一条后端路线，不改变本报告中 D3D11 队列对照的结论，也不要求重编译核心。
