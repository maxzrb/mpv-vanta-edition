# 3FP 与 mpv 色彩精度核查

核查日期：2026-10-04。3FP 源码固定到 `15995b807bf8a27037d2697fcdb89d13064ee247`（2026-09-30）；mpv 对照本机 `413ff0b1cd4585294803308a1a14be2fad30cede` 与随附 libplacebo v7.374.0。已静态拆解用户提供的 3FP 发行程序并反汇编内置 Shader，未启动该播放器或测量其屏幕输出；没有修改活动播放配置、菜单或 Windows HDR 设置。HDR 是本轮核心核查对象，SDR 会话只验证交换链行为。

## 结论与证据范围

FP16 scRGB 是 Windows Advanced Color 的合理承载方式，可以减少过早量化或裁剪，但不能单凭它认定色准排名。本机 mpv 已验证能建立相同类型的交换链；默认 gpu-next 的高精度处理中间纹理和最终输出格式必须分别看。显示器校色、传递函数、HDR 映射及系统合成同样决定最终结果。

“T0／第二档／不如 Windows 内置播放器”尚缺明确版本、设置、素材、参考结果和同机测量。本次没有找到可复现的三方比较；公开仓库的 [FFF.Player.Tests 入口](https://github.com/Lake1059/FFF_Project/blob/15995b807bf8a27037d2697fcdb89d13064ee247/FFF.Player.Tests/Program.vb)目前明确没有测试项。这不证明作者没有其他私下测试，也不能反向证明 mpv 更准。

## 3FP 的实现

### 9 月 30 日发行版核对

输入为 `C:\Users\maxzr\Downloads\FFF.Player.exe`，大小 39,498,324 字节，ProductVersion 为 `2026.9.30+15995b807bf8a27037d2697fcdb89d13064ee247`，SHA256 为 `4AEFD9FFFC007D17858A4C85E9EFEEC639A6FF10E97627928CA28D843CB17C1B`。

在本地临时目录拆出 .NET 托管入口和 FFF.Native.dll，并用 ILSpy 读取会话创建代码；使用 Windows D3DDisassemble 读取 DXBC。七组公开预编译 Shader 数组都在实际 Native DLL 中逐字节命中。主像素 Shader 为 ps_5_0，没有 min16／min10 精度声明；这支持区分常规 32 位浮点运算与 FP16 存储，不能称为全程 16 位运算。结果与偏移保存在 `tmp/modernization/3fp-audit/bytecode-results.json`。

发行版的原生结构保留 `SDRscRGB模式` 字段，但托管会话初始化未赋值，保持零；公开 Native 默认也为零。因此纯高位深 SDR 自动进入 scRGB 的额外策略在这个入口没有启用。HDR／广色域的请求条件与高位深 SDR 条件不同，且仍受实际输出模式和显示能力约束。此结论针对该发行版标准入口，不涵盖外部调用者主动设置策略的情况。

所提供 EXE 的拆包清单与同目录指定路径均未发现 `FFF.DolbyVision.Test.dll`；源码会从 EXE 同目录加载该扩展并核查授权状态。没有分析或绕过授权，也不能据此否定作者另行提供扩展后的能力。反编译和字节码产物仅作本地研究，未复制到配置或分发内容。

[VideoRenderer.cpp](https://github.com/Lake1059/FFF_Project/blob/15995b807bf8a27037d2697fcdb89d13064ee247/FFF.Native/3FP/Render/VideoRenderer.cpp)中的关键位置：

| 环节 | 源码行为 | 精度含义 |
|---|---|---|
| 解码输入 | FFmpeg；D3D11VA 可使用 NV12／P010／P016 | P010 占 16 位存储，但有效视频数据为 10bit |
| 纹理／转换 | 高位深 YUV 使用 R16 UNORM；部分非直接格式转 RGBA64LE | 16bit 整数暂存不等于 FP16 运算 |
| 色彩转换 | 矩阵、范围、PQ／HLG／SDR 曲线、色域转换 | 转换规则正确性独立于位数 |
| scRGB 输出 | R16G16B16A16_FLOAT；RGB_FULL_G10_NONE_P709 | FP16 线性 RGB，可携带负值和大于 1 的值 |
| Windows 与显示器 | 后续系统合成、色彩管理、输出链接及面板 | 创建 FP16 交换链不能证明整条显示链都是 16bit |

`WantsScRgbPresentationPath`（5511 行）将 HDR 或广色域列为请求条件；高位深 SDR 还要求 SDR scRGB 策略非零。`EnsureSwapChain`（2414 行）另受请求色彩模式与显示能力约束。因此“只要 10bit 就必定 FP16”并不准确。

`CreateSwapChain`（2505、2526 行）检查色彩空间支持；拒绝 scRGB 时记录原因并重建 SDR 链。能力查询有缓存，交换链拒绝有退避，显示器／策略变更后重新探测。`EffectivePaperWhiteNits`（5493 行）让 scRGB 中的 SDR 白点跟随 Windows 设置；读取失败使用回退值。这些协商、标尺与回退思路值得借鉴。

scRGB 使用 BT.709 原色并不意味着只能表示 BT.709 色域；转换后的负通道及超范围值可以表示更广颜色。FP16 是浮点编码，也不等于每通道 65536 个均匀的亮度阶梯。Microsoft 的 [Advanced Color 文档](https://learn.microsoft.com/en-us/windows/win32/direct3darticles/high-dynamic-range)说明了其系统条件、合成方式与 HDR 下 1.0 对应 80 nits 的标尺；Advanced Color SDR 则有显示参考解释，需要区分。

## 不能直接当作色准优势的部分

基础 Shader 的 `LinearOne`（491 行）固定使用 BT.709 逆 OETF；不能将它直接当作 BT.1886 显示 EOTF、sRGB 或其他标记的完整自适应处理。基础 HLG 曲线也使用固定参考峰值／指数。这些是需要用具体素材验证的差异，而不是证明某播放器普遍输赢的依据。[BT.1886 标准](https://www.itu.int/rec/R-REC-BT.1886-0-201103-I)规定的是参考显示 EOTF。

### HDR 重点：HLG 的具体算法差异

基础 HLG 路径在逆 OETF 后对 R、G、B 分别取 1.2 次幂，再乘 1000；实际内置 DXBC 也确认了这一操作。[BT.2100-2 表 5 与注 5e](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.2100-2-201807-S!!PDF-E.pdf)的参考 OOTF 使用场景亮度 `Ys = 0.2627 R + 0.6780 G + 0.0593 B`，再用同一个 `Ys^(gamma-1)` 缩放三个通道。按通道独立幂变换属于近似，灰阶一致并不代表彩色一致。

在黑位为零、参考峰值 1000 nits、gamma=1.2 条件下，数学复算如下（转换至 scRGB 前的线性 BT.2020 RGB 通道值，单位 nits）：

| HLG 编码 RGB | BT.2100 参考值 | 3FP 基础公式值 |
|---|---|---|
| (0.75, 0.75, 0.75) | (203.152, 203.152, 203.152) | 相同 |
| (0.75, 0.25, 0.25) | (161.821, 12.724, 12.724) | (203.152, 9.605, 9.605) |
| (0.25, 0.75, 0.25) | (14.888, 189.344, 14.888) | (9.605, 203.152, 9.605) |

这是算法层面的可复现差异，涉及亮度和通道比例；不是最终屏幕色差，也不是所有 HDR10／DV 路径的结论。外部动态扩展可能替换处理，需另验。模型与结果分别为 `check-hdr-math.py`、`hdr-math-results.json`，没有把 Python 双精度计算冒充 GPU 执行误差。

libplacebo 上游 [colorspace.c 的 HLG 分支](https://github.com/haasn/libplacebo/blob/master/src/shaders/colorspace.c)使用亮度加权 OOTF，并根据黑位／峰值确定参数；这里仍为 master 参考，不能代替随附二进制的像素回读。这个差异已经足以说明“FP16 就能确保所有 HDR 色准领先”的推论不成立。

### HDR10、显示适配与动态元数据

3FP 基础 PQ→scRGB 路径采用 PQ 绝对亮度解码、线性色域矩阵与 nits/80 输出，且保留转换后的负值。该分支没有使用目标峰值压缩高亮；HDR10 元数据另向 DXGI 提交，后续 Windows／驱动／显示器如何处理须实测。不能把源码中“交给显示器”注释当作实际硬件处理的证明。

正常能力门禁查询活动桌面是否至少 10bit 且为 PQ 色彩空间，强制输出选项可绕过这层判断，但交换链仍可能拒绝。检测缓存、跨屏重新探测、失败退避值得借鉴；强制输出不能创造 HDR 显示能力。

Dolby Vision、HDR10+、HDR Vivid 须逐一核查是否实际应用动态元数据，或只播放兼容基础层；“检测出格式”与“完成动态映射”应分别报告。mpv 与 3FP 比较时也必须保持相同的基础层／动态处理任务。

[HdrProcessor.cpp](https://github.com/Lake1059/FFF_Project/blob/15995b807bf8a27037d2697fcdb89d13064ee247/FFF.Native/3FP/Hdr/HdrProcessor.cpp)区分外部动态处理与 Dolby Vision 基础层／FEL 回退；没有核查外部扩展实际使用时，不能将基础层兼容播放等同于完整 RPU／FEL 处理。源码中的基础 scRGB 路径直接携带线性值，也不能笼统等同于所有内容都经过相同的显示器端色调映射。

## mpv 的对应能力

- libplacebo 的 [renderer 格式选择](https://github.com/haasn/libplacebo/blob/master/src/renderer.c)优先选择可用的 16bit 浮点中间纹理，也有能力不足时的回退。这里参考上游 master，不宣称该文件精确对应随附二进制；本机日志另确认 HDR 中间纹理实际使用 rgba16hf。
- 本机对应 [vo_gpu_next.c](https://github.com/mpv-player/mpv/blob/413ff0b1cd4585294803308a1a14be2fad30cede/video/out/vo_gpu_next.c)中，参考白可查询系统（896 行），scRGB 输出不额外按整数位深抖动（1248 行），其余量化由下游承担。使用 ICC 时仍需核查 Windows 自动色彩管理，避免重复转换，参考 [Microsoft ICC 与 Advanced Color 说明](https://learn.microsoft.com/en-us/windows/win32/wcs/advanced-color-icc-profiles)。
- [mpv 手册](https://mpv.io/manual/master/#options-d3d11-output-format)确认 rgba16f 可请求 scRGB，target-trc=scrgb 也是入口。gpu-next 的内部格式由 libplacebo 管理；添加 fbo-format=rgba32f 不能强制它成为全程 FP32 管线。

## 独立会话实际测试

本机 RX 6600、1920×1080 SDR 显示器 sRGB 模式。DXGI 查询的当前输出为 8 bits、RGB_FULL_G22_NONE_P709；这是驱动报告的输出参数，不是面板测量。使用既有 SDR 8／10bit、广色域 SDR、HDR10、HLG 合成素材，比较现有配置与独立 CLI 覆盖；视频解码使用软件路径，无 AI／Shader 增强。

| 测试 | 五类素材的实际结果 |
|---|---|
| 现有 SDR 默认配置 | libplacebo 交换链 R10G10B10A2_UNORM；目标 rgb10a2／sRGB／BT.709 |
| FP16 与匹配线性色彩空间 | R16G16B16A16_FLOAT＋RGB_FULL_G10_NONE_P709；目标 rgba16hf／scRGB／BT.709 |

两组均以当前 SDR 显示目标解释，目标报告最大亮度 80 cd/m²；该数值是配置／协商标尺，未测量屏幕亮度。后一组五类素材的 GPU 错误日志均为零。最初使用 d3d11-output-csp=auto 时曾在启动层尝试给 FP16 配 sRGB 色彩空间并报错，libplacebo 随后恢复 scRGB；改为匹配的 linear 后该错误消失。

原始证据保存在 tmp/modernization/3fp-audit/mpv-results.json；首轮记录在 mpv-results-initial-auto.json。这里证明了交换链与元数据行为，不证明 HDR 实机色准、Windows DWM 的最终合成精度或面板位深。本轮没有 Dolby Vision 素材验收、没有 HDR 显示器验收，也没有 3FP／Windows 播放器同机数值比较。

## 在 mpv 中实施的分环境方案

普通 SDR sRGB 显示环境继续保留当前默认：按源格式解码、gpu-next 高精度处理、映射至 sRGB、按输出位深抖动。强制 FP16 不会使显示器色域或亮度增加，也不保证经典 SDR 系统合成中的精度收益。

HDR 或正确配置的 Advanced Color 环境可以使用以下**待该环境实机验证**的独立实验配置。本机只验证了它能在 SDR 环境建立链，不应直接升级为默认：

```conf
# FP16 scRGB 实验配置；需核查 Windows HDR／Advanced Color 和校色状态。
vo=gpu-next
gpu-api=d3d11
d3d11-output-format=rgba16f
d3d11-output-csp=linear
target-trc=scrgb
target-prim=auto
target-colorspace-hint=yes
target-colorspace-hint-mode=target
hdr-reference-white=auto
inverse-tone-mapping=no
icc-profile=""
icc-profile-auto=no
dither-depth=auto
```

该配置只对渲染输出负责，不启用 Windows HDR，不自动校准面板，也不保证所有影片的 tone mapping 与 3FP 相同。libplacebo 有最终格式决定权，应按日志确认。HDR→HDR 显示适配与保留源亮度的输出比较应分开测试；对需要由 mpv 映射的素材，可保持 target 模式，不能把自动目标映射与其他播放器的基础层／系统映射当成同一处理任务比较。

下一步的有效验收应固定三方播放器版本、硬解／软解、源元数据、HDR 模式、系统白点、校色和输出格式；使用灰阶、PQ 亮度阶梯、范围端点、BT.2020 色块及真实 HDR／DV 片段。先比较 GPU 输出数值和参考数学模型，再在同一台 HDR 显示器上用测量仪比较亮度曲线与色差；HDR 建议报告 ΔE_ITP、SDR 可报告 ΔE00。截图与肉眼观感可辅助定位，不能代替这些测量。

## HDR 优先验收表

| 场景 | 必须核对 | 当前状态 |
|---|---|---|
| HDR10 → HDR，无需压缩的参考色块 | PQ 阶梯、黑白端点、BT.2020 矩阵、负值保留、FP16 回读 | 源码／字节码核查；真实 GPU 数值比较待测 |
| HDR10 → HDR，源峰值超过显示能力 | 实际目标峰值、由谁映射、是否重复映射、局部调光与 ABL | HDR 显示器实机待测 |
| HLG → HDR | 加权 OOTF、彩色块、黑位、系统 gamma 与峰值适配 | 基础公式差异已复算；GPU／面板待测 |
| SDR／广色域 SDR → HDR 桌面 | 传递函数、系统 SDR 白点、矩阵、ICC／ACM 是否重复转换 | 源码核查；HDR 桌面待测 |
| HDR → SDR | 目标曲线与色域映射、峰值分析、抖动；分开记录创作性映射差异 | 本机播放和元数据通过；色差待测 |
| Dolby Vision P5／P8／P7 FEL | 实际 RPU、重整形、基础层、FEL 与外部扩展状态 | 无素材验收；不宣称完整通过 |
| HDR10+／HDR Vivid | 元数据解析、动态映射是否执行、基础层回退提示 | 源码线索；外部实机待测 |
| Windows HDR 切换／跨屏／链拒绝 | 缓存失效、失败回退、重新协商、画面不失效 | 3FP 静态核查；mpv 实机场景待测 |

实施方向是保留现有 SDR 默认，并为 HDR 环境单独验证 scRGB 输出及目标亮度来源。先解决明确的管线、元数据和映射问题，再比较测量结果；目前没有依据为播放器建立“T0／第二档”排名。

具体实施顺序、当前配置缺陷和验收条件见 [mpv 色彩准确优化路线](mpv色彩准确优化路线.md)。

后续色彩管理器、准确基线、HDR 回退及本机测试已实施，当前证据与未测范围见 [色彩优化实施与验证](色彩优化实施与验证.md)。旧 HDR 自动入口已改为委托统一管理器，仍默认关闭。
