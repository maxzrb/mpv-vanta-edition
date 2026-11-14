# HQ SDR 的 FATE 风格回归

使用固定样本定义和参考输出，运行真实 mpv，并将规范化结果逐字比较；这不是 FFmpeg 官方 FATE 的构建目标。播放器配置仓库不需要构建 FFmpeg，也不需要测试应用。

- 输入：`samples/hq-sdr.json`。生成无损 FFV1 灰阶和 PQ 样本；PQ 中固定 40 nits 灰块不变，周围从 20 变为 1000 nits。
- 参考：`ref/hq-sdr`。
- 实际结果与样本：`tmp/modernization/hq-sdr-fate/`。
- 使用现有 GPU 读回工具，只附加到测试创建的 mpv 进程，不改变系统 HDR、桌面校色或用户播放偏好。

在项目根目录运行：

```powershell
python -X utf8 tools/test-hq-sdr-fate.py
```

需要仓库随附的 mpv／FFmpeg、支持 D3D11 和 Vulkan 的设备，以及维护环境中的 Python `frida`。隔离安装依赖时，可通过 `PYTHONPATH` 指向其目录；无需向播放器运行环境安装 Python 包。

检查包括：FP16 原始交换链读回标尺、与独立 sRGB EOTF 参考比较的灰阶、固定 PQ 灰块对周围亮度变化的稳定性、系统白位缺失回退、切换显示身份、手动覆盖与切回标准模式。每个像素检查的线性绝对容差为 0.002；标尺容差为 0.0001。测试不声称测量了显示器的实际发光亮度。

## 通用过载追赶

```powershell
python -X utf8 tools/test-overload-policy-fate.py
python -X utf8 tools/test-overload-fate.py
```

- 固定输入：`samples/overload.json`，包含编码样本参数及播放快照时间序列。
- 参考输出：`ref/overload-policy`、`ref/overload`；真实结果与规范化参考逐字比较。
- 策略回归九行覆盖瞬态／负向声画差、持续落后、暂停／跳转／缓存保护、默认本片保持、可选恢复及指数退避、持续掉帧与计数复位、同模式重复重新同步及限频。
- 真实 mpv 使用随包 FFmpeg 生成 AV1／H.264／HEVC／VP9 固定短片，在 D3D11／Vulkan 上检查参考帧往返、暂停和轨道保存、硬解优先、换片／重启完整解码、快速关闭／停止／替换、命令行覆盖、无音轨及 HQ／标准画质切换；没有独立测试应用。
- `samples/overload-playback.lua` 仅回放固定传感输入，实际解码／定位／轨道／事件仍由真实 mpv 执行；双后端各验证持续掉帧进入、暂停保护、两次模式内重新同步且解码器打开数不增加、用户跳转保持及关闭恢复。真实 FATE 共 24 用例／12 行，不把注入传感值当作性能测量。
- 自然过载的性能对照单独使用 `tools/benchmark-overload-catchup.py`。`--full-config --native-budget` 保留日常配置和线程预算；30 秒后的 0.25 倍速段验证默认保持，传入 `--auto-recover` 则验证可选恢复，不计入正常速度性能统计。

## 着色器缓存维护

```powershell
python -X utf8 tools/test-shader-cache-fate.py
```

固定文件输入为 `samples/shader-cache.json`，11 行参考输出为 `ref/shader-cache`；实际结果保存于 `tmp/modernization/shader-cache-fate/`。使用 Windows 自带 PowerShell 5.1、真实文件锁／目录联接和两版 mpv IPC，验证普通与 AMD 模式的范围、原文件 SHA、历史／设置／ICC／GLSL 保留、越界拒绝、占用跳过、无写入预览、多实例等待、退出时新增缓存、重复请求、中文与引号路径、缺少可选模块时的旧核心兼容。D3D11／Vulkan 实际生成缓存、清理后再启动生成；执行 04 的真实复制片段核验两个 installer 文件，检查 01 收录及私包合并关系，不创建发布归档。

所有 AMD 测试均将子进程 `LOCALAPPDATA` 指向夹具，不清空真实驱动缓存；菜单测试只清理隔离配置目录。测试不伪造着色器黑帧，也不将所有 Vulkan 黑屏归因于缓存。
