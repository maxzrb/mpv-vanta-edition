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
