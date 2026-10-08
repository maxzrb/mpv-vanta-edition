# 维护与回归工具

这些工具面向维护者，运行前读取脚本说明和项目状态。它们不替代根目录发布流程；回归可能启动播放器、生成素材、准备模型或写入 tmp 中的测试数据。

| 用途 | 工具 |
|---|---|
| 语法、引用、用户选项与退役检查 | check-modernization.py |
| 上游组件审计／VS 候选快照 | audit-components.py、snapshot-vs-lock.py |
| 播放、素材、统计综合验证 | validate-modernization.py |
| mpv／VS 1.0.5 原生性能对照 | benchmark-playback-compare.py、benchmark-vs105-native.py、benchmark-vs105-abi.py |
| 独立ETW呈现采集／QPC对齐分析／mpv对照 | trace-vs105-presentmon.py、analyze-vs105-presentmon.py、benchmark-mpv-presentmon.py（需官方PresentMon控制台，仅读取和停止自己创建的会话） |
| 3FP稳定段阶段计时与帧数闭合 | analyze-vs105-stages.py（读取带QPC的诊断JSON／日志） |
| D3D11／DXGI逐调用、等待栈与运行时因果实验 | trace-vs105-calls.py／.js、analyze-vs105-calls.py（仅测试进程；固定DLL校验；`--mpv`只读对照；跳过像素处理的结果不能当正常播放） |
| 独立GPU队列ETW与适配器节点核查 | trace-vs105-gpu-etw.py、analyze-vs105-gpu-etw.py、query-gpu-nodes.py、query-dxgkrnl-events.py、configure-gpu-etw-filter.py、etw-qpc-marker.py（自有会话／双QPC标记；`--lean`限制事件；DMA跨度不是纯GPU忙时） |
| AMD只读频率／功耗与独立计算对照 | query-amd-metrics.py、benchmark-amd-queue-load.py（只读ADL；限一个待完成Dispatch，不写驱动／调频设置；额外计算不是播放修复方案） |
| 普通播放／双字幕／HTTP、不同尺寸 | test-playback-compat.py、test-playback-sizes.py |
| 原菜单／一键启用／组合与错误回退 | validate-quality-menu.py、test-quality.py、test-quality-state.lua |
| 色彩状态机／旧 HDR 生命周期 | test-color-state.lua、test-color-preferences.py、test-hdr-lifecycle.lua |
| 实际色彩切换／高位深截图／范围 | validate-color-target.py、validate-color-ramp.py、validate-color-range.py |
| HDR 数学向量 | color-reference.py（非 GPU 或面板测量） |
| 原始 FP16 交换链／SDR ACM／PQ 与 HLG 数值 | test-color-output.py、gpu-readback.py／.js（仅自有诊断进程；非 DWM 或面板测量） |
| HQ 线性缩小性能 | benchmark-linear-downscale.py（三轮，预热 5 秒后至少采样 20 秒；4K→1280×720） |
| 源矩阵／范围、格式保留、真实滤镜、时长回退 | test-color-precision.py |
| 完整配置 SDR／广色域 SDR 像素、16bit组合及短片循环 | test-color-config.py（独立配置副本） |
| HDR10／HLG 静态增强一致性与模拟 scRGB 输出 | test-color-hdr-config.py（隔离副本暂停真实显示检测，不改系统HDR） |
| 手动维护 K7 色彩补丁 | apply-k7-color-fixes.py（默认只查看，--apply 应用；播放器不调用） |
| 统计和起播徽标生命周期 | test-stats-lifecycle.py、test-startup-logos.lua |
| 更新器／旧安装隔离 | test-updater.ps1、test-retired-component.ps1 |

Lua 回归用根目录 `luajit.exe`；Python 工具使用匹配的 Python。部分测试依赖 `tmp/modernization/validation/` 已生成夹具，先检查依赖再运行，不把缺夹具当成产品失败。输出默认进入忽略目录；技术摘要与结论写入 docs/modernization，状态记入 HandShake。

大分辨率硬解初始化回归：`test-hwdec-startup.py <素材路径>`（真实启动／快进／切片）、`test-hwdec-select.lua`（用户选择与当前文件作用域）。

8K队列预算定位：`benchmark-vs105-native.py --video-queue-limit 4`仅对SHA为094c19e…的1.0.5 DLL作进程内预算实验，退出回退；同参数可用于GPU ETW和逐调用工具。保持像素处理，不作为通用用户配置。Frida与lxml仅放在忽略的探针依赖目录。GPU追踪转换XML后再分析；解析大XML不要与播放测量同时执行。

色彩与播放优化候选：`benchmark-playback.py`（4K 普通播放，预热 5 秒后至少 20 秒，三轮）、`benchmark-peak-seek.py`（HDR 峰值分析与长 GOP 精确跳转）、`benchmark-startup.py`（完整配置的新增管理任务起播对比）。性能测试顺序运行，避免互相占用 GPU；不是普通用户播放前核验。

播放体验回归：`python.exe -X utf8 tools/test-playback-followup.py` 生成带黑边的低帧率素材，验证直接硬解裁剪、主 GPU 表面保留、SVP 实际补帧、简洁列表及详情翻页；`validate-quality-menu.py` 同时断言播放性能位于「其它」。`luajit.exe tools/test-quality-state.lua` 覆盖约 60fps／120fps 保留原帧、旧补帧替换与低帧率实际启用。真实素材性能结果见 `docs/modernization/播放体验回归修复-20261007.md`；采样时隔离鼠标、键盘和媒体键输入，暂停、跳转或时钟异常的轮次不计入有效结果。

维护者复测 SVP：`python.exe -X utf8 tools/benchmark-svp.py --media "本地视频路径"`，约 60fps 以上素材加 `--passthrough`。使用至少 30 秒的视频，完整配置、WASAPI 静音、1080p 窗口，每轮预热 5 秒后至少采样 20 秒，重复三轮。结果保存在 `tmp/modernization/svp-benchmark/results.json`；帧率、时钟、掉帧、CPU 单核心占用及音频欠载分开记录。它不改变原片分辨率，结果仅代表测试机器与该素材。

`isolated-config.py` 为完整配置回归建立忽略目录中的独立副本，避免修改用户历史与持久偏好。`portable_config/quality/probe.py` 与组件清单仅供维护者手动核查，起播、菜单和滤镜选择不会调用。

滤镜交接对比：`python.exe -X utf8 tools/benchmark-filter-handoff.py` 使用同一 SVP 1080p、CCD 4K 和 RIFE 4.26 DML HEVC10 夹具，串行比较直接 D3D11VA 与 copy。增强预热 5 秒后采样至少 20 秒、重复三轮，轮流改变两种路线的测试顺序；每次运行包含三次启停、暂停与精确跳转，以及关闭后 5 秒状态回归。会检查正常媒体推进、掉帧与稳态音频欠载。`--only svp --seconds 3 --rounds 1 --cycles 1` 只作短诊断，不能推广默认；`--resume` 只接受相同配置签名的完整采样。缺硬解支持、最小化、暂停及 EOF 干扰会拒绝本轮结果。性能结论不推广到其它显卡、素材和滤镜。

资源生命周期观察：`python.exe -X utf8 tools/test-filter-gpu-memory.py` 依赖上述已生成夹具，对同一进程三次滤镜启停分别记录私有内存、工作集和 Windows PDH 进程 GPU 内存。计数器不可用／退出后实例消失记作未知，不当作测得零；缓存留存不直接判作泄漏。这项与所有播放器性能测试串行运行。

带音频的组合交接：`python.exe -X utf8 tools/test-filter-av-handoff.py` 使用 640×360 HEVC10＋AAC，对直接／copy 两条路线实际测试 SVP、CCD＋SVP、CCD＋RIFE、STD 缺后端恢复原链、暂停跳转切集和整数位深／VS 交接详情。预热后的 5 秒采样用于兼容回归，不冒充三轮20秒性能结论；初始化与稳态音频事件分开。没有音轨的性能夹具不会据零欠载声称音频通过。

HDR 独立参考：`python.exe -X utf8 tools/test-hdr-gpu-reference.py` 将受控 PQ／HLG YUV44416 色块通过 GPU 转换为线性 scRGB，与独立数学参考比较，包含暗部、亮度标尺、BT.2020→709、负值与超过 scRGB 1 的值。正负分别编码后使用 16bit PNG 读回，并校验读回标尺；它不是原始 FP16 纹理读取、默认动态色调映射或物理屏幕测量。

精度描述与更新保留：`luajit.exe tools/test-render-precision.lua` 区分整数位深、浮点存储和硬解／VS 交接；`luajit.exe tools/test-color-state.lua` 同时覆盖 NaN 未知值去重及真实元数据变化。`python.exe -X utf8 tools/test-k7-patch-update.py` 在临时副本模拟已知上游覆盖，验证只读、重应用、幂等及未知文件全量拒绝；不修改生产组件，不进入起播流程。

原始浮点色彩回归：`python.exe -X utf8 tools/test-color-output.py` 在暂停创建的自有 mpv 进程中安装只读探针，在 Present 线程复制交换链至 staging，读取 RGBA16F 原始半精度数值及成功设置的 DXGI 色彩空间。先校验写入标尺和负值／超过 1 的值，再测试实际 SDR ACM、灰阶、BT.2020 色块、软件隔离的 PQ／HLG 与线性缩小。实际 SDR 部分需要系统已启用 ACM；工具不会开启它。HDR 部分注入能力并屏蔽 SDR 桌面提示／参考白覆盖，不能当作真实 HDR 桌面验收。测试保留色彩处理配置，排除遮挡画面的 UI 和窗口尺寸脚本，不修改用户历史。

维护探针使用 Frida 17.22.1，依赖放在忽略目录 `tmp/modernization/vs105-instrument/deps`；缺失时用 `python.exe -m pip install --target tmp/modernization/vs105-instrument/deps frida==17.22.1` 准备。它不进入播放器日常加载或公开包。`MPV_COLOR_TEST_EXE` 环境变量可指定待验证核心；未指定时测试根目录核心。读回会同步等待 GPU，不用于性能测量，也不证明每个中间纹理或物理显示端的精度。

8K AV1 软解定位：`python.exe -X utf8 tools/benchmark-av1-software.py "本地视频路径" --mode play --cases baseline t12-d0 t8-d0 --rounds 3`，强制 CPU 解码，保持完整 HQ／色彩配置，记录实际丢帧、音画偏差、媒体推进和 CPU 使用。`--mode decode --frames 480` 为关闭输出／音频的纯解码控制，不能当作真实播放达标。2026-10-08 用户已搁置此优化，已有结果按项目清理清单归档；工具仅供未来手动复测，不接入播放器。

起播窗口回归：`python.exe -X utf8 tools/test-window-foreground.py` 用完整隔离配置和自有遮挡窗口比较旧版／修复版，验证新启动、IPC 打开文件、最小化恢复、暂停与自动切集，以及持续置顶偏好保留。依赖 `test-playback-compat.py` 生成的 HEVC10 夹具；仅启动和销毁自有窗口，不操作其它应用。系统限制键盘焦点时以实际显示顺序验证抬窗，不冒充取得焦点。
