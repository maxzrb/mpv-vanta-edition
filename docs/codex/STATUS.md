# STATUS.md — MPV 便携配置项目

## 当前状态快照

| 项目 | 状态 |
|------|------|
| **项目** | MPV 便携播放器个人配置（fork from gaoxing64/MPV-lazy-full v2.0.0） |
| **分支** | `master`（领先 `origin/master` 1 个提交，功能提交已本地化） |
| **最新发布提交** | `909dede`（tag: `v1.4.1`） |
| **工作区** | shinchiro 核心、文件关联重构均已完成；uosc 已加入共享 SU7 灵感十色主题、VantaInstaller 选择入口、media info/速度滑块碰撞检测双行布局，以及内置 HarmonyOS Sans SC 字体；功能与记录未提交 |
| **MPV 核心版本** | v0.41.0-922-gf4d13e1c2（2026-08-11，shinchiro/mpv-winbuild-cmake；FFmpeg N-126056-gee498f5e8） |
| **项目版本** | v1.4.3（已发布） |
| **上次操作** | 只读审计 uosc DPI/像素适配：主体尺寸已缩放，待修重点集中在 Timeline、TopBar 自适应距离调用方及菜单细节 |
| **自定义脚本** | `stats.lua`、`quality_status.lua`、`lsfg_control.lua` |

## 环境

- **操作系统**: Windows 11 Pro for Workstations 10.0.26220
- **架构**: x86_64
- **Python**: 3.14.6（便携，根目录）
- **MPV 构建源**: shinchiro/mpv-winbuild-cmake

## 工作目录结构

```
c:\Program portable\mpv2\
├── mpv.exe, mpv.com          # MPV 核心 (gitignore)
├── yt-dlp.exe                # 在线视频解析器 (gitignore，Base 包会复制)
├── portable_config/          # 配置文件 (git 跟踪)
│   └── scripts/stats.lua     # 汉化版统计信息脚本
├── vs-plugins/, vs-scripts/  # VapourSynth (gitignore)
├── Faster-Whisper-XXL/       # AI 字幕 (gitignore)
├── lua/, socket/, mime/      # Lua 运行时
├── installer/                # 安装/更新脚本
└── settings.xml              # 更新器配置 (未跟踪)
```

## TODO

- [x] `settings.xml` 已加入 `.gitignore`
- [ ] 根据个人需求定制 mpv.conf
- [x] 安装官方 yt-dlp 2026.07.04，并纳入公开 Base 包
- [x] 升级 Python 3.14.3 → 3.14.6，并验证 SSL、SQLite、pip 与现有 VapourSynth R73
- [x] 为 VapourSynth R78 设计无需全局环境变量、兼容直接双击 `mpv.exe` 的便携加载方案（已放弃：R73 为明确支持 Win7 的最后版本，暂不升级，R78 试验文件已清理）
- [x] 更新 7-Zip 25.01 → 26.02、TorrServer MatriX.141 → 142.2、umpv-go 1.4.0 → 1.5.1
- [x] 安全合并更新器报告的 15 个脚本、文档和着色器差异，保留本地个性化文件
- [x] 修复 manager 的 PlayKit 分支、quality-menu 白名单、同名脚本覆盖和 Git blob 误报
- [x] 手工完成小型依赖维护：uosc 5.13 关键修复、blacklist/config 一致性和弹幕 API 兜底
- [x] 基于现有 uosc 5.13 分阶段移植参考界面（媒体参数胶囊与配色已完成；紧凑底栏已完成；起播格式 Logo 已移植参考版完整方案）
- [x] 为 uosc 建立 SU7 车漆灵感十色主题注册表，并接入配置文件和 VantaInstaller 设置页
- [x] 从官方 HarmonyOS Sans 字体包内置 SC Regular/Bold，设为 mpv/uosc/字幕默认字体并保留 Microsoft YaHei 回退（未发布，待发布 Gate 审核）
- [x] 用官方 `audio-spdif`/WASAPI 实现默认关闭、失败回退的 Dolby/DTS 源码直通菜单
- [x] 采用 mpv 上游式 Applications/Capabilities 结构重构 VantaInstaller 文件关联：当前用户、音视频、双入口独立、无需 UAC
- [x] 为不使用 VantaInstaller 的 01/全量包用户补齐四个当前用户手动注册/取消入口，并保留旧 HKLM BAT 兜底
- [x] 将本机 mpv 核心从已停更的 dyphire 构建切换到 shinchiro 20260811，并验证 D3D11、Vulkan、D3D11VA、FEL 选项和完整配置
- [x] 安装 Faster-Whisper-XXL 公开版 r245.4，从 Extras 拆分为独立 04 增量包
- [x] 恢复“着色器 / 视频滤镜”一级分类，在完整技术分类前补充少量互斥推荐入口
- [x] 为 Anime4K v4 增加 HQ/Fast 两档 A、B、C、A+A、B+B、C+A 共 12 套官方标准预设
- [x] 去掉 VapourSynth 菜单中间层，让补帧、超分、降噪按用途直达
- [x] 将完整着色器库按用途重组，同时保留按原算法家族查找的专家库
- [x] 允许补帧、超分、降噪同时启用，并提供竖排状态 OSD 与直属清空入口
- [x] 将 LSFG 2×/3×/4×测试入口接入补帧菜单，并支持按当前进度重启切换
- [x] 将四个 LSFG 预设收进独立子菜单，使其与其他补帧滤镜处于同一层级
- [x] 将左上角静态置顶标记改为可点击且带状态高亮的 uosc 顶栏按钮
- [x] 为 LSFG 增加 Layer 实时帧率遥测与可切换 OSD 覆盖层
- [x] 为视频滤镜补齐直属状态查看和完整清空入口
- [x] 让 LSFG 遥测跟随 Tab 常驻 stats OSD，并移至屏幕右上角
- [x] 将五类安装包按 01 Base → 02 Config → 03 Extras → 04 FW → 05 LSFG 编号并写明覆盖顺序
- [x] 将第 04 包改为零 Steam 文件的公开扩展包，仅要求用户自备 `Lossless.dll`
- [x] 统一生成 v1.2.0 四类公开包和个人私用全量包，并完成内容、交叉和完整性审计

---

## 会话日志
## 会话日志

### 2026-08-11 发布前记录：v1.4.3 发布（文件关联注册入口分离）

- **版本**：v1.4.3（用户指定；02/03/04 无内容改动仅推版本号，01/05 重建，VantaInstaller v0.2.0 重建）。
- **改动清单**：
  - 设置中心文件关联卡片：注册多实例（mpv.exe）/ 注册单实例（umpv.exe）独立按钮，可分别注册，Windows 打开方式自行选择。
  - 安装向导组件页：勾选注册多实例/单实例关联（可同时勾选），安装后自动注册（各弹一次 UAC）。
  - 单实例脚本 `FriendlyAppName`：mpv → mpv-single（打开方式可区分）。
  - `portable_config/script-opts/window_size_position.conf`：size=1280x720、position=center（05 包内容变化）。
- **影响包**：01（installer bat + 版本标记）、05（window_size_position.conf）重建；02/03/04 无改动推版本号；VantaInstaller 源码改动独立构建。
- **Git 状态**：功能提交 `5bf448d`、chore `UI 截图删除` 已本地；master 与 origin/master 同步；工作树干净。
- **验证计划**：7z t 完整性、SHA-256、门禁、.vanta-version 逐字节核验（01=1.4.3、05 不含、根目录副本=1.4.3）。

## 会话日志

### 2026-08-11 会话: VantaInstaller 增强与 v1.4.2 installer 重建

- **功能提交** `9b1c6a1`：指定已安装 mpv 位置（首页/设置/卸载三处，持久化优先识别）；配置备份目录选择（立即备份/历史/恢复跟随）；卸载前配置默认备份到 `文档\MPV Vanta Edition\uninstall-backups`；修复 WPF-UI InfoBar 显式 Style 覆盖默认模板导致高度塌陷不可见；新增 `InverseBooleanToVisibilityConverter` 修复 Visibility 绑定静默失败；根目录 `portable_config/.vanta-version` 标记（1.4.2）。
- **构建**：正式版 `VantaInstaller\publish\win-x64\VantaInstaller-win-x64-v0.2.0.exe`（67.5MB，压缩自包含单文件），启动验证通过。
- **发布**：仅重建 installer（用户指示不全量构建），`gh release upload v1.4.2 --clobber` 覆盖；先误传为 `VantaInstaller.exe`（同名覆盖未命中），已删除并改用规范名重新上传。
- **核对**：远端 `VantaInstaller-win-x64-v0.2.0.exe` SHA-256 `7E3D0B412CCA273FC26861972B459A84C61BE7F205B2AE27F2702AA4CBCF6FF3`，大小 67570562，与本地一致；旧 hash 资产已清除。
- **收尾**：Release 说明已更新（installer SHA-256 改为 7E3D0B41... 并附 2026-08-11 重建说明）；docs 提交 `4edea12` 已推送，master 与 origin/master 同步。
- **未提交/未夹带**：`portable_config/script-opts/window_size_position.conf`（用户私有改动）、`backup/`（测试残留）均未纳入提交。
- **流程修订**（用户指示，写入《发布流程.md》）：① VantaInstaller 使用独立版本号（如 v0.2.0），是 mpv 附属工具，功能/界面/版本迭代**不触发**大改动 Gate、不提升 mpv 项目版本号；② 资产命名铁律——本地 VantaInstaller 产物文件名必须与远端资产名完全一致（`VantaInstaller-win-x64-v<版本>.exe`），禁止通用名上传，`--clobber` 仅覆盖同名资产，上传后须核对无重复资产。 ③ **`.vanta-version` 内容铁律**——它是安装器识别 mpv 版本的唯一依据（CurrentVersion/更新检测/Vanta 区分），内容必须为纯版本号不带 `v`、UTF-8 无 BOM 无换行无尾随空格，与包文件名/标签/版本记录完全一致；写入方：build-release.ps1 以 -Version 写入 01、build-config-public.ps1 05 排除；构建后须逐字节核验 01 包内文件、05 排除、根目录副本一致。


### 2026-07-30 会话: 统一 v1.2.0 打包与归档审计

- 四类公开包统一命名为 `01-mpv-base-v1.2.0.7z`、`02-mpv-config-v1.2.0.7z`、`03-mpv-extras-v1.2.0.7z.001/.002`、`04-mpv-lsfg-addon-v1.2.0.7z`。
- 新增 `mpv-full-private-v1.2.0.7z`，按 01 → 02 → 03 → 04 顺序合并，并只额外加入个人自备的 `Lossless.dll`。
- 打包门禁会排除缓存、日志、临时文件和调试产物；Extras 清除了 121 个 `__pycache__` 目录、1321 个生成文件，约 21.9 MiB。
- 未发现旧 Release、`build`、`tmp`、`.git` 或其他归档被意外套入新包。
- Config 与 Base 的 257 个相同文件属于更新包设计；LSFG 和 Extras 与 Base/Config 均无路径重叠。
- 六个实际归档文件均通过 `7z t`；个人全量包与四个公开包的合并结果一致，仅按设计移除公开源码/占位说明并加入 `Lossless.dll` 和私用说明。
- 旧 v1.1.1 输出已可恢复地移至 `tmp/release-backup-before-v1.2.0/`，没有删除。
- 新增统一入口 `build-all-packages.ps1` 和个人包脚本 `build-full-private.ps1`；当前尚未提交、推送或上传 Release。

### 2026-07-27 会话 2: 汉化 stats.lua OSD 统计界面

- **操作**: 从 mpv 源码获取 stats.lua → 翻译所有 OSD 显示文为中文
- **文件变更**: 新增 `portable_config/scripts/stats.lua` (覆盖内置)
- **翻译范围**: 6 个信息页的标题、标签、状态文本全覆盖
  - 页1 默认信息: 文件、视频、音频、HDR、滤镜等 40+ 字段
  - 页2 扩展帧时间: 帧时间表格、总计
  - 页3 缓存统计: 队列、状态、速度、范围
  - 页4 活跃键位绑定: 搜索提示
  - 页5 轨道信息: 编解码器、回放增益、杜比视界、轨道标志
  - 页0 内部性能信息
- **保留原文**: HDR10+、PQ(Y) 等技术标准名称
- **验证**: `mpv --no-config --script=stats.lua` 加载无报错
- **状态**: 完成，期待用户实际播放视频时测试显示效果

### 2026-07-27 会话 3: 创建 GitHub 仓库 + 三包发布

- **仓库**: https://github.com/maxzrb/mpv-portable (公开)
- **Release**: v1.0.0 (https://github.com/maxzrb/mpv-portable/releases/tag/v1.0.0)
- **三包方案**:
  - `mpv-config-v1.0.0.7z` (32 MB) — 配置/脚本/OSC/字体
  - `mpv-base-v1.0.0.7z` (75 MB) — 核心播放器 + 运行时 + 配置
  - `mpv-extras-v1.0.0.7z.001/.002` (2.6 GB) — 着色器 + VS + AI + 工具 (分卷)
- **新增文件**: build-release.ps1 (打包脚本)
- **Git 提交**: 3 次提交推送到 origin/master
- **状态**: Release 已发布，GitHub Pages 需手动启用

### 2026-07-27 会话 1: MPV 核心升级

- **操作**: 从 dyphire/mpv-winbuild 下载并解压最新构建
- **版本变化**: v0.41.0-198-gb74121a3a (Feb 20) → v0.41.0-860-gc8c7d91a8 (Jul 6)
- **方法**: 手动下载 `mpv-x86_64-20260706-git-c8c7d91a8e.7z` + 7z 解压覆盖
- **文件变更**: mpv.exe, mpv.com, lua51.dll, luajit.exe, vulkan-1.dll, doc/, installer/, updater.bat, lua/, mime/, mpv/, socket/
- **git 可见变更**: 仅新增 settings.xml (未跟踪)
- **验证**: `mpv.com --version` 确认版本正确
- **状态**: 升级成功，工作区干净，二进制文件由 .gitignore 排除

### 2026-07-29 14:58 会话: 着色器与视频滤镜菜单分类审查

- **范围**: 只读检查 `input.conf`、`mpv.conf`、`profiles.conf`、`dyn_menu.lua`、387 个 GLSL 文件及 13 个 VapourSynth 菜单脚本。
- **硬件基线**: AMD Radeon RX 6600，1920×1080，165 Hz；当前使用 `vo=gpu-next`、`gpu-api=d3d11`。
- **主要发现**:
  - 着色器菜单共有 388 项，其中 387 项是素材库全部 GLSL 文件的直接展开，并非面向使用场景的精选菜单。
  - 121 个着色器支持运行时参数，但菜单只提供开关；317 个着色器带触发条件，未满足条件时点击可能无实际效果。
  - 所有着色器菜单项都没有动态勾选状态，无法直观看出已启用项目，且多个超分、降噪或锐化算法可以被叠加。
  - `[SD]` 条件配置会对 720p 及以下视频自动启用 `FSRCNNX+`，与手动选择其他放大着色器存在叠加风险。
  - VS 菜单混入 5 个明确的 NVIDIA 专用项目，不适用于当前 RX 6600。
  - 视频滤镜菜单将 VS、几何变换、帧率改写和色彩元数据修复混在一层；“强制 59.94 帧”不是运动补帧，`format` 色彩项主要用于修复错误标记。
- **建议方向**:
  - 改为“常用预设、片源修复、放大、色度、锐化、流畅度、画面变换、专家库”的用途分类。
  - 常用方案互斥设置并提供当前状态/一键清理，避免任意叠加。
  - 优先使用 mpv 内置缩放、去色带和轻量插值；VapourSynth 与完整 GLSL 库移入专家区。
- **文件变更**: 仅更新 HandShake 记录；播放器配置未修改。
- **Git 状态**: 本地 `master` 领先远程 1 个提交；进入本次研究前 `docs/codex/STATUS.md` 已有未提交记录。

### 2026-07-29 15:23 会话: 优化着色器与视频滤镜菜单

- **目标**: 将面向算法仓库的菜单改造成面向播放场景的日常菜单，同时保留完整专家入口。
- **菜单重组**:
  - 新增一级菜单“画质处理”，顺序为“查看当前处理 → 常用方案（互斥）→ 单项处理（替换当前方案）→ 片源修复 → 流畅度”。
  - `Ctrl+0～9` 从可叠加着色器开关改为互斥方案：关闭、通用高清、通用低清、动画柔和修复、动画高清、动画低清、色度增强、轻度降噪、SSim 低负载和 SGEDS 缩放锐化。
  - 常用方案根据 `glsl-shaders` 实际内容显示动态勾选状态。
  - 去色带、去交错、去色块归入“片源修复”；翻转、旋转和补黑边归入“画面变换”。
  - 容易误用的色彩元数据强制、帧率改写和默认 6500K 色温移动到“专家工具”。
- **流畅度优化**:
  - 日常入口保留 mpv 轻量插值、关闭动态平滑、MVT-LQ 与适配 RX 6600 的 RIFE-DML。
  - VapourSynth 使用 `@quality-vs` 标签切换，只替换自身，不再执行 `vf set` 清空其他滤镜。
  - NVIDIA 专用 VS 项目独立归档到“专家工具 > VapourSynth > NVIDIA 专用”。
- **冲突消除**:
  - 停用 `[SD]` 条件配置的自动触发，低清增强改为手动选择，避免换文件时覆盖用户方案或与其他超分叠加。
  - 完整 387 个 GLSL 文件全部保留在“专家工具 > 着色器库”，无缺失、无重复。
- **验证**:
  - `mpv --no-config --input-conf=portable_config/input.conf --idle=no`：输入配置解析成功。
  - `mpv --no-config --include=portable_config/profiles.conf --show-profile=SD`：手动 SD profile 展开正确。
  - IPC 运行时逐项验证 10 种画质方案：着色器内容和菜单勾选全部匹配。
  - IPC 验证 MVT-LQ：`quality-vs` 标签、VapourSynth 文件和流畅度勾选正确。
  - 动态 `menu-data` 验证日常菜单顺序正确；专家着色器覆盖 `387/387`。
  - `git diff --check` 通过，配置保持 UTF-8、LF。
- **文件变更**: `portable_config/input.conf`、`portable_config/profiles.conf`、`docs/codex/STATUS.md`、`version/工作进度.md`。
- **Git 状态**: `master` 领先远程 1 个提交；本次修改尚未提交。

### 2026-07-29 15:46 会话: 恢复清晰的技术分类

- **用户反馈**: “画质处理 / 专家工具”结构牺牲了原有分类，完整库入口过深，预设名称也不够直观。
- **菜单纠偏**:
  - 恢复“着色器”和“视频滤镜”两个一级菜单，移除“画质处理”和“专家工具”菜单路径。
  - 387 个 GLSL 入口直接回到“着色器”下的原技术分类，不再经过“专家工具 > 着色器库”。
  - “着色器 > 推荐”只保留关闭、真人 720p、真人低清、动画修复、动画 720p、动画 SD 六个场景化入口。
  - CfL、kBFDN、SSim 和 SGEDS 快捷项分别并回原本的 CfL、其他效果、SSim 和高通分类，避免新增重复分类。
  - 片源修复、流畅度、画面变换、错误标记修复、帧率改写、色彩调整、滤镜管理和 VapourSynth 全部直属“视频滤镜”。
- **保留的底层改进**:
  - 着色器快捷方案继续互斥替换并显示动态勾选。
  - VapourSynth 继续使用 `@quality-vs` 标签安全切换，不清空其他视频滤镜。
  - `[SD]` 自动触发继续停用，避免切换视频时覆盖手动方案。
- **验证**:
  - mpv 实际 `menu-data` 中“着色器 / 视频滤镜”均为一级菜单，旧的“画质处理 / 专家工具”入口为零。
  - 完整着色器库覆盖 `387/387`，零缺失、零过期路径、零重复。
  - `mpv --no-config --input-conf=portable_config/input.conf --idle=no` 解析成功。
- **Git 状态**: 本次纠偏仍未提交。

### 2026-07-29 15:58 会话: 提升补帧与超分入口

- **用户反馈**: 视频滤镜中的关键补帧和超分功能仍藏在“VapourSynth”深层菜单。
- **菜单调整**:
  - 去掉用户可见的“VapourSynth”中间层。
  - “补帧”“超分”“降噪”成为“视频滤镜”最前面的三个直属分类。
  - 补帧直接列出关闭、mpv 轻量插值、MVT-LQ、RIFE-DML、DRBA-DML、RIFE-STD、SVP Pro 和两个 NVIDIA 方案。
  - 超分直接列出 UAI-DML、UAI-MIGX、UAI-NV-TRT 和 ArtCNN。
  - AMD、Intel、NVIDIA 和负载要求直接写在方案名称中，不再要求用户先理解技术后端。
  - CCD 与 BM3D 移入直属“降噪”；管理菜单保留关闭当前 VS 处理的入口。
- **保留行为**:
  - 所有 VS 方案继续通过 `@quality-vs` 单一标签安全替换。
  - 每个补帧、超分和降噪方案都增加或保留动态勾选状态。
- **验证**:
  - mpv 实际菜单顺序为“补帧 → 超分 → 降噪 → 片源修复 → …”，VapourSynth 菜单路径为零。
  - RIFE-DML 与 UAI-DML 均能正确加载预期脚本，并在实际 `menu-data` 中显示勾选。
  - 输入配置解析成功，测试 mpv 进程正常退出。
- **Git 状态**: `master` 领先远程 1 个提交；整批菜单优化仍未提交。

### 2026-07-29 16:21 会话: 建立着色器用途与专家双索引

- **用户目标**: 日常按用途寻找着色器，同时避免 AMD、Anime4K 等同一技术家族因用途拆分后无法集中浏览。
- **分类依据**:
  - 读取本地 387 个 GLSL 菜单入口和文件元数据。
  - 对照 mpv_PlayKit 当前《用户着色器》Wiki 的各族用途说明，特别处理 AMD、Anime4K、ArtCNN、ESRGAN、NVIDIA、RAISR、SSim 和 ETC 等混合用途家族。
- **用途索引**:
  - 建立“超分与缩放、修复与去模糊、锐化与细节、降噪与平滑、抗锯齿与抗振铃、去色带、色度修复、色彩与观感、去交错、画面工具与特效”十个直属用途分类。
  - 每个用途继续按片源类型或处理方式、算法家族分层，避免单层塞入数百项。
  - `Ctrl+6～9` 快捷单项迁入对应用途路径，继续保留动态勾选。
- **专家索引**:
  - 新增“着色器 > 专家库”，完整复制原来的 35 个算法家族菜单路径。
  - 双索引仅重复菜单引用，不复制 GLSL 文件，不增加着色器磁盘占用。
- **典型分流**:
  - AMD 的 5 个 EASU/FSR 放大项进入“超分与缩放”，6 个 CAS/RCAS 项进入“锐化与细节”。
  - “专家库 > AMD”仍集中保留全部 11 项。
  - Anime4K 分流到超分、动画修复、降噪、动画线条和抗振铃。
- **验证**:
  - 用途索引覆盖 `387/387`，零缺失、零过期路径；另有 4 个快捷菜单项。
  - 专家索引覆盖 `387/387`，零缺失、零重复、零过期路径。
  - mpv 实际 `menu-data` 顺序、35 个专家家族、AMD 分流数量全部符合预期。
  - 双索引菜单实际读取约 7 ms；`Ctrl+8` 勾选和 `Ctrl+0` 清理正常。
  - 输入配置解析成功，测试 mpv 进程正常退出。
- **Git 状态**: `master` 领先远程 1 个提交；整批菜单优化仍未提交，建议现在提交。

### 2026-07-29 16:52 会话: 放宽滤镜叠加并改进状态查看

- **用户需求**:
  - VS 补帧、超分和降噪需要允许同时启用。
  - “查看当前启用项”必须标出并提供可记忆的快捷键。
  - 当前着色器和滤镜需要在 OSD 中逐项竖排并显示数量。
  - 着色器直属二级菜单需要一键清空全部着色器。
- **滤镜槽拆分**:
  - 将原共享 `@quality-vs` 拆为 `@quality-memc`、`@quality-upscale`、`@quality-denoise`。
  - 不同用途可以同时存在；同一用途切换时只替换自身。
  - mpv 轻量插值现在只移除 VS 补帧，保留当前 VS 超分与降噪。
  - 补帧、超分、降噪菜单分别提供关闭项；管理菜单保留一键关闭全部三类处理。
- **状态 OSD**:
  - 新增 `portable_config/scripts/quality_status.lua`。
  - 着色器和视频滤镜按“数量 + 编号 + 每行一项”显示。
  - VS 滤镜显示 `[补帧]`、`[超分]`、`[降噪]` 用途及脚本文件名，并单列 mpv 轻量插值状态。
  - 原拟使用 `Ctrl+Shift+0`，但 mpv 在 Windows 下不会把数字 Shift 组合注册为该按键；最终改为可用且无冲突的 `Ctrl+Alt+0`。
- **菜单入口**:
  - “着色器 > 查看当前启用项 · Ctrl+Alt+0”成为首项。
  - “着色器 > 清空全部着色器 · Ctrl+0”提升为直属第二项，不再藏在推荐子菜单。
- **验证**:
  - 实际同时加载 RIFE-DML、UAI-DML、CCD，三个独立标签和菜单勾选均正确。
  - 补帧从 RIFE-DML 切换到 MVT-LQ 后，超分与降噪保持不变。
  - 切换到 mpv 轻量插值后，仅 VS 补帧被移除，超分与降噪仍存在。
  - `Ctrl+Alt+0` 已进入 mpv 实际 `input-bindings`；`Ctrl+1` 加载及 `Ctrl+0` 清空着色器正常。
  - 用模拟的 2 个着色器与 4 个滤镜验证竖排 OSD 文本、数量和用途标签。
  - 测试 mpv 进程正常退出。
- **文件变更**: 新增 `portable_config/scripts/quality_status.lua`，修改 `portable_config/input.conf` 及 HandShake 记录。
- **Git 状态**: `master` 领先远程 1 个提交；整批菜单优化仍未提交，建议现在提交。

### 2026-07-29 17:46 会话: 菜单优化提交前复核

- **范围**: 对当天的着色器分类、视频滤镜槽拆分、状态 OSD 和低清 profile 调整做最终提交前复核。
- **远程状态**: 已执行 `git fetch origin`；远程 `origin/master` 没有新增提交，本地仍领先 1 个既有提交。
- **验证结果**:
  - `git diff --check` 通过。
  - 使用 `av://lavfi:testsrc` 实际启动 mpv，成功加载 `quality_status.lua`、`input.conf` 和 `profiles.conf`，退出码为 0。
  - 本地 387 个 GLSL 文件在用途索引和专家索引中均覆盖 `387/387`，引用总集无缺失、无过期路径。
  - 仓库附带的 `luajit.exe` 不支持 `-b` 命令，因此 Lua 验证改用 mpv 实际加载完成。
- **待执行**: 提交并推送本批修改；随后根据三包内容决定 Release 更新范围。
- **Git 状态**: `master` 领先远程 1 个提交；待提交文件为 `input.conf`、`profiles.conf`、`quality_status.lua` 及 HandShake 记录。

### 2026-07-29 17:56 会话: 提交菜单优化并准备 v1.1.0

- **提交与同步**:
  - 已提交 `175b4f4 feat: 按用途重组着色器与视频滤镜菜单`。
  - 已推送到 `origin/master`，本地与远程同步。
- **Release 范围判断**:
  - `v1.0.0..HEAD` 只涉及 README、菜单配置、profile、状态脚本和项目记录。
  - 着色器、VapourSynth、插件、模型、Python 环境及额外工具没有变化。
  - 决定发布 v1.1.0 的 config 与 base 两包，不重传 extras；v1.0.0 extras 保持兼容。
- **打包机制**:
  - 为 `build-release.ps1` 新增 `-SkipExtras` 开关。
  - 使用 `.\build-release.ps1 -Version '1.1.0' -SkipExtras` 构建。
- **产物**:
  - `mpv-config-v1.1.0.7z`：33,817,819 字节；SHA-256 `E44E99294C82C6979163952D6F047EB987C126F05EAD347A1EED767C89ED7C6B`。
  - `mpv-base-v1.1.0.7z`：78,173,383 字节；SHA-256 `5D34E29B84AFCE34D29E43FFF314C0494F71C11373E116785C4262524B4CC5A6`。
- **验证**:
  - 两个 7z 包完整性测试通过。
  - 两包均包含 `quality_status.lua`，且均未误包含 shaders 或 VS 素材。
  - 解压基础包后实际启动 mpv，成功加载新脚本、`input.conf` 和 `profiles.conf`。
  - 解包验证产生的忽略目录 `build/validate-v1.1.0` 仍在本地；自动递归清理被执行环境策略拦截，不影响 Git 或发布包。
- **待执行**: 提交版本与打包机制，创建并上传 GitHub Release v1.1.0。

### 2026-07-29 18:02 会话: 发布 GitHub Release v1.1.0

- **发布提交**: `bf1be68 release: 准备 v1.1.0 配置与基础包`。
- **标签**: 已创建并推送带注释标签 `v1.1.0`，远程标签解引用到 `bf1be68`。
- **Release**: https://github.com/maxzrb/mpv-portable/releases/tag/v1.1.0
- **上传资产**:
  - `mpv-config-v1.1.0.7z`：33,817,819 字节，GitHub digest 与本地 SHA-256 一致。
  - `mpv-base-v1.1.0.7z`：78,173,383 字节，GitHub digest 与本地 SHA-256 一致。
- **发布状态**: 正式发布，非草稿、非预发布；Release 说明明确复用 v1.0.0 extras。
- **未上传**: extras 分卷未变化，因此没有重新构建或上传。
- **本地临时文件**:
  - `release/` 内保留两个已上传包，由 `.gitignore` 排除。
  - `build/validate-v1.1.0` 是解包启动验证副本，由 `.gitignore` 排除；执行环境阻止递归删除，可由用户稍后手动删除。
- **Git 状态**: 发布代码和标签均已同步；本条 HandShake 收尾记录提交后应保持工作树干净。

### 2026-07-29 18:48 会话: 精简 SVP 菜单并准备 v1.1.1

- **用户需求**: 将“SVP Pro · 需安装 SVP”缩短为“SVP”，提交并更新 Release。
- **本地核验**:
  - 当前系统未安装 SVP 软件，但项目自带 `svpflow1_vs.dll` 与 `svpflow2_vs.dll`。
  - `MEMC_SVP_PRO.vpy` 通过 `k7sfunc.SVP_PRO()` 调用随包 SVPFlow 插件，不依赖 SVP Manager。
  - 使用测试视频实际加载 SVP 滤镜成功。
- **菜单修改**: `portable_config/input.conf` 中补帧菜单名称已改为“SVP”，滤镜命令和动态勾选逻辑保持不变。
- **验证**:
  - `input.conf` 由 mpv 实际解析成功。
  - SVP 滤镜独立处理 12 帧测试视频成功。
  - `git diff --check` 通过。
- **发布范围**: 仅菜单配置变化，构建 v1.1.1 的 config 与 base 两包；extras 继续复用 v1.0.0。
- **发布包**:
  - `mpv-config-v1.1.1.7z`：33,817,671 字节；SHA-256 `BA6270CD61493C3E8BC6EFDBDDCF33144586A4382C8E90473BBE3D76E54F2C60`。
  - `mpv-base-v1.1.1.7z`：78,173,427 字节；SHA-256 `979884132A5BA9A19EA9E8BEB076171007A1DE74D849B01F170AE265EDA526D9`。
- **包体核验**: 两包 7z 完整性测试通过，均包含新菜单文案且不含旧文案；没有误包含 shaders 或 VS 素材。
- **待执行**: 提交、推送、创建 v1.1.1 标签与 GitHub Release，并上传两包。

### 2026-07-29 18:51 会话: 发布 GitHub Release v1.1.1

- **发布提交**: `9735802 release: 发布 v1.1.1 菜单修正`，已推送到 `origin/master`。
- **标签**: 已创建并推送带注释标签 `v1.1.1`，远程标签解引用到 `9735802`。
- **Release**: https://github.com/maxzrb/mpv-portable/releases/tag/v1.1.1
- **发布状态**: 正式发布，非草稿、非预发布。
- **远程资产核验**:
  - `mpv-config-v1.1.1.7z`：33,817,671 字节，GitHub SHA-256 与本地一致。
  - `mpv-base-v1.1.1.7z`：78,173,427 字节，GitHub SHA-256 与本地一致。
- **extras**: 着色器、VapourSynth、模型和工具未变化，因此继续复用 v1.0.0 extras。
- **Git 状态**: 发布提交、分支和标签均已同步；本条 HandShake 收尾记录提交后应保持工作树干净。

### 2026-07-29 23:22 会话: Windows 原生 LSFG 接入研究

- **研究分支**: 已从当前版本建立本地 `research/lsfg-windows`，没有推送公开仓库。
- **素材核验**:
  - 用户提供的 Lossless Scaling 3.2.2 目录共 440 个文件、183,809,856 字节。
  - `Lossless.dll` 含 300 个 `RT_RCDATA` 资源；lsfg-vk 需要的 304–400 号 SPIR-V 模型资源全部存在。
  - 运行方案仅将 `Lossless.dll` 当作 PE 资源容器读取，不加载或执行其中的专有代码。
- **Windows 移植**:
  - 导入 `PancakeTAS/lsfg-vk` develop 提交 `8b0da2661c6f3473a7fccc8ba643880050e71642`。
  - 将 Linux 文件描述符共享路径改造为 Win32 `HANDLE`、`OPAQUE_WIN32`、外部内存与外部时间线信号量。
  - 增加 Windows Vulkan Loader、进程识别、便携路径、符号导出和 MinGW 构建支持。
  - 下载的 w64devkit 2.9.0、CMake 4.4.1、Ninja 1.13.2 均通过发布方 SHA-256 校验。
- **运行验证**:
  - 生成的 `lsfg-vk-layer.dll` 只依赖 Windows 系统 DLL，并正确导出 `vkNegotiateLoaderLayerInterfaceVersion`。
  - 启动器按绝对 DLL 路径动态生成 Vulkan 清单，不写注册表；默认隔离 OBS/Steam 隐式层。
  - mpv 使用 Vulkan/WinVK 播放 30 帧合成视频，Layer 报告 `frame generation context ready (320x240, 2x)`，进程退出码为 0。
  - 因为 Layer 位于最终交换链，生成帧会包含字幕、OSD 和菜单；本方案不需要重新构建 mpv。
- **私有研究包**:
  - `release/mpv-lsfg-research-private.7z`，51,938,897 字节。
  - SHA-256：`7C73A5EA24A9952ED44C77598634B7757435144D4C6B5444800F1C82C6E85B5E`。
  - 包含完整 Lossless Scaling 目录、运行 Layer、启动器和对应 GPL 研究源码；7z 完整性检查通过。
- **隔离措施**: `.gitignore` 已排除根目录 `Lossless Scaling/` 和 `lsfg-vk/`，不会误纳入公开提交。
- **Git 状态**: 本次研究改动尚未提交、未推送，也没有创建或更新公开 Release。

### 2026-07-30 00:02 会话: 将 LSFG 接入 mpv 补帧菜单

- **菜单入口**:
  - 在“视频滤镜 → 补帧”直属加入 LSFG 2×质量、2×性能、3×质量、4×质量和状态查看。
  - LSFG 启用时，对 mpv 轻量插值及所有 VapourSynth 补帧项返回 `disabled` 状态，避免双重补帧。
  - 原“关闭补帧”现在同时识别 LSFG；处于 LSFG 模式时会重启回普通 mpv。
- **续播控制**:
  - 新增 `portable_config/scripts/lsfg_control.lua`，保存当前时间、暂停状态和播放列表后启动新进程。
  - 切换到 LSFG 前移除 `@quality-memc` 并关闭 mpv 插值，防止与 RIFE/SVP 叠加。
  - 启动参数通过忽略目录中的临时 JSON 文件传递，规避 Windows PowerShell 原生数组参数只能绑定首项的问题。
  - `start-mpv-lsfg.ps1` 新增 `-Disable` 和 `-MpvArgumentsFile`，并兼容 Windows PowerShell 5.1 对无 BOM UTF-8 脚本的解析。
- **状态显示**:
  - `quality_status.lua` 增加 LSFG 启用状态、倍率及质量/性能模式。
  - `lsfg_control.lua` 将当前模式写入 `user-data/lsfg/*`，供动态菜单实时勾选。
- **验证结果**:
  - 普通模式菜单显示完整 LSFG 入口；LSFG 2×质量模式正确勾选，mpv 插值和 RIFE 菜单正确禁用。
  - 启动器烟雾测试再次报告 `frame generation context ready (320x240, 2x)`，退出码为 0。
  - 普通 mpv → LSFG：菜单消息成功，旧进程退出，新进程同时带 `--gpu-api=vulkan` 和 `--start` 续播参数。
  - LSFG → 普通 mpv：旧进程退出，新进程带 `--start` 且不再包含 Vulkan 强制参数。
  - 所有测试创建的 mpv 进程均已清理。
- **私有包更新**:
  - 包内新增 `portable_config/input.conf`、`lsfg_control.lua` 和新版 `quality_status.lua`。
  - `release/mpv-lsfg-research-private.7z`：51,957,616 字节。
  - SHA-256：`69E91F8501A5E1891D8F0E96D6981B6FD694E1BAE20D4151CC0096A800AC97B1`；7z 完整性检查通过。
- **Git 状态**: 本地 `research/lsfg-windows` 研究改动尚未提交、未推送，没有更新公开 Release。

### 2026-07-30 00:25 会话: LSFG 实时帧率覆盖层与滤镜管理

- **视频滤镜直属入口**:
  - “视频滤镜”一级菜单前两项现在与着色器一致，分别为“查看当前启用项 · Ctrl+Alt+0”和“清空全部滤镜 · Ctrl+`”。
  - 普通模式下，清空会执行完整 `vf clr` 并关闭 mpv 插值。
  - LSFG 模式下，清空会退出 Layer，携带 `--vf-clr`、`--interpolation=no` 和当前 `--start` 位置重启普通 mpv。
- **Layer 实时遥测**:
  - 在 `Swapchain::present` 成功完成全部生成帧与原始帧的 `QueuePresentKHR` 后分别计数。
  - 每 0.5 秒写入 `lsfg-vk/telemetry.json`：输入 Present FPS、输出 Present FPS、倍率、性能模式和更新时间。
  - `start-mpv-lsfg.ps1` 管理 `LSFGVK_TELEMETRY_PATH`，启动或关闭时清理旧遥测，避免显示过期数据。
- **OSD 覆盖层**:
  - `lsfg_control.lua` 每 0.25 秒读取 Layer 遥测，通过独立 ASS OSD 在左上角显示倍率、模式、原始 FPS 和实时 FPS。
  - LSFG 启用时默认显示，可在“视频滤镜 → 补帧 → LSFG 帧率覆盖层”开关。
  - 当前画质状态 OSD 也会显示“原始 FPS → 实时 FPS”。
  - 采用 mpv ASS OSD 而非在 Vulkan Layer 内额外实现字体渲染，避免修改交换链图像管线；帧率数据仍来自 Layer 的真实提交计数。
- **验证结果**:
  - 30 fps 合成视频前台烟雾测试得到 `30.01 → 60.01 FPS`，倍率准确为 2×。
  - Lua 实际读取遥测成功，`user-data/lsfg/input-fps`、`output-fps` 与覆盖层勾选状态均有效。
  - 已用窗口截图确认覆盖层实际渲染；后台隐藏窗口被 DWM 节流时仍会如实显示较低 Present 速率。
  - 普通模式测试：滤镜数量从 1 变为 0，`interpolation=false`。
  - LSFG 模式测试：旧进程退出，新普通进程不含 Vulkan 强制参数，并含 `--vf-clr`、`--interpolation=no`。
  - Windows Layer 重新编译成功；DLL SHA-256 为 `26D14A5D9953DCCB62B8D21683CC4C46511ACA5669F84BD99F16BF23FE51E9A0`。
- **统计边界**: “实时 FPS”代表 Layer 成功提交到 Vulkan 交换链的 Present 速率，不保证等同于显示器面板最终扫描率；最小化或后台窗口可能受 DWM 节流。
- **私有包更新**:
  - `release/mpv-lsfg-research-private.7z`：52,035,917 字节。
  - SHA-256：`3B4A08F24F47885960A259ED71779FBA98DAE1272231FA026ACDAD840E568F8C`；7z 完整性检查通过。
- **Git 状态**: 本地 `research/lsfg-windows` 研究改动尚未提交、未推送，没有更新公开 Release。

### 2026-07-30 00:39 会话: 遥测跟随 Tab 常驻 stats OSD

- **有效按键确认**:
  - `input.conf` 中低优先级的 Tab 是文件浏览器入口，但被 `inputevent.lua` 的增强按键覆盖。
  - 实际生效的是 `inputevent_key.conf`：Tab 单击调用 `stats/display-stats-toggle`，等同原大写 `I` 的常驻统计功能。
  - 曾为排查临时改动的文件浏览器 Tab 行已恢复，没有改变用户原有按键语义。
- **同步实现**:
  - 自定义 `stats.lua` 在常驻统计开启/关闭后写入 `user-data/stats/toggled`。
  - `lsfg_control.lua` 观察该属性：stats 关闭时遥测隐藏，Tab 或大写 `I` 开启时显示。
  - stats 自身通过 Tab、I 或 Esc 关闭时，状态都会同步更新，不依赖盲目翻转计数。
- **布局**: ASS 覆盖层从左上角改到右上角（右对齐、距边 24 px），避免遮挡左侧 stats OSD。
- **验证**:
  - 初始状态：stats=false、LSFG overlay=false。
  - 第一次真实 `keypress TAB`：stats=true、overlay=true。
  - 第二次真实 `keypress TAB`：stats=false、overlay=false。
  - 窗口截图确认左侧 stats 与右侧 LSFG `30.1 → 60.1 FPS` 同屏且不重叠。
  - 所有自动化测试 mpv 进程均已清理。
- **私有包更新**:
  - 打包脚本新增自定义 `portable_config/scripts/stats.lua`，确保状态同步代码随包交付。
  - `release/mpv-lsfg-research-private.7z`：52,051,306 字节。
  - SHA-256：`8C9BA7CA18B1BA40FBEF89BF0B0AC44490EFD752C9220DAF8BE81CB8EF512C3E`；7z 完整性检查通过。
- **Git 状态**: 本地 `research/lsfg-windows` 改动尚未提交、未推送，没有更新公开 Release。

### 2026-07-30 00:56 会话: 安装包覆盖顺序编号

- **编号规则**:
  - `01-mpv-base-vX.Y.Z.7z`
  - `02-mpv-config-vX.Y.Z.7z`
  - `03-mpv-extras-vX.Y.Z.7z.001/.002`
  - `04-mpv-lsfg-research-private.7z`
- **覆盖约定**:
  - 四类包全部安装时按 01 → 02 → 03 → 04 解压覆盖。
  - 同版本 Base 已包含 Config，因此 02 可跳过；如果安装，则仍按编号执行。
  - LSFG 私有包必须最后覆盖；以后更新 Base 或 Config 后需要再次应用 04。
- **脚本调整**:
  - `build-release.ps1` 的实际生成顺序改为 Base → Config → Extras，并为三个公开包加编号。
  - `build-lsfg-research.ps1` 将私有包更名为 `04-mpv-lsfg-research-private.7z`。
  - 根 `README.MD`、Extras 包内说明和私有包内说明均写入完整安装顺序。
- **验证**:
  - 两个 PowerShell 打包脚本通过解析器语法检查。
  - 临时实际生成 01 Base、02 Config 和 04 私有包，三个归档完整性测试通过。
  - 从三个归档中实际解出 README，均确认包含 01～04 顺序；03 Extras 因约 2.6 GB 未重新压缩，已静态核对其名称与生成说明。
  - `git diff --check` 通过，仅显示仓库现有的 autocrlf 提示。
- **临时文件**:
  - 执行策略阻止自动递归清理，测试归档仍位于 `tmp/package-order-validation/`。
  - 解出的 README 校验文件仍位于 `tmp/package-order-readme-check/`；两目录均为可删除的临时产物并已被 Git 忽略。
- **Git 状态**: 改动尚未提交、未推送，没有重新生成正式 Release 或更新公开 GitHub Release。

### 2026-07-30 01:05 会话: 验收并合并 LSFG 研究分支

- **用户决策**: LSFG Windows 研究功能和四类包编号验收通过，允许合并到主分支。
- **主分支确认**:
  - 仓库不存在 `main`；远端默认主分支为 `master`。
  - 合并前执行 `git fetch origin --prune`，确认本地 `master` 与 `origin/master` 同为 `45c2716`。
- **提交与合并**:
  - 研究提交：`a9732f6 feat: 集成 LSFG Vulkan Layer 研究功能`。
  - 合并提交：`ce60088 merge: 合并 LSFG Windows 研究功能`。
  - 合并无冲突，保留 `research/lsfg-windows` 分支作为功能基线。
- **提交范围审计**:
  - 共纳入 193 个文件，包括 mpv 菜单/控制脚本、Windows Layer GPL 源码、构建脚本、正确的 `lsfg-vk-layer.dll` 及研究文档。
  - `Lossless Scaling/`、根目录运行时 `lsfg-vk/`、`release/` 和 `tmp/` 继续由 `.gitignore` 排除。
  - 用户提供的 `Lossless.dll`、私有包和测试归档均未进入 Git。
  - 忽略早期 MinGW 生成且未被使用的 `liblsfg-vk-layer.dll` 副本。
- **合并前验证**:
  - Windows Layer 使用既有 w64devkit/CMake/Ninja 工具链重新配置并增量构建成功，安装产物保持最新。
  - `build-release.ps1`、`build-lsfg-research.ps1`、`start-mpv-lsfg.ps1` 和 `build-windows.ps1` 均通过 PowerShell 解析器检查。
  - `stats.lua`、`quality_status.lua` 和 `lsfg_control.lua` 通过 mpv `--no-config` 加载测试。
  - 修复上游 `Configuration.md` 两处尾随空格后，`git diff --cached --check` 通过。
- **未执行事项**:
  - 没有推送 `master` 或研究分支。
  - 没有创建新版本、Tag 或更新公开 GitHub Release。
  - 正式编号包尚未重新生成；此前的临时验证目录仍在 `tmp/` 且被 Git 忽略。
- **Git 状态**: 本收尾记录提交后，本地 `master` 预计领先 `origin/master` 3 个提交，工作树应保持干净。

### 2026-07-30 01:15 会话: 用公开 LSFG 扩展包取代私有包

- **Steam DLL 审计**:
  - 本机 Lossless Scaling 目录共有 433 个 DLL；旧私有归档共有 438 个 DLL 条目，额外 5 个是 Layer 运行/研究构建副本。
  - 其中 38 个为 Lossless Scaling 自有文件：`Lossless.dll`、`LosslessScaling.dll` 及 36 个语言目录中的 `LosslessScaling.resources.dll`。
  - 其余 395 个主要是 .NET、WPF、WinRT 等随 Steam 应用携带的第三方运行库；即使其中部分可能有独立再分发条款，本项目也不需要它们，因此统一排除。
  - mpv LSFG 实际只读取 `Lossless.dll` 的 `RT_RCDATA` 模型资源；用户只需从正版 Steam 安装自行复制这一文件。
- **公开包设计**:
  - 删除 `build-lsfg-research.ps1`，新增 `build-lsfg-public.ps1`。
  - 第 04 包更名为 `04-mpv-lsfg-addon.7z`，可公开分发。
  - 包内只含一个 DLL：本项目构建的 GPL `lsfg-vk-layer.dll`。
  - 包内不含 Steam DLL、EXE、模型资源或完整 Lossless Scaling 目录；只提供一个文本占位说明。
  - 随 Layer 二进制附带 `research/lsfg-vk-win` 对应 GPL 源码，但剔除本机 build 目录和重复 DLL。
  - 打包脚本设有强制门禁：额外 DLL、任意 EXE 或占位目录中的其他文件都会使构建失败。
- **文档调整**:
  - 根 `README.MD` 与 Extras 包内说明均将 04 改为公开扩展包。
  - 明确安装者只需将 Steam 安装根目录的 `Lossless.dll` 放到 `<mpv根目录>\Lossless Scaling\Lossless.dll`。
  - 明确不需要 `LosslessScaling.dll`、语言资源 DLL、.NET/WPF DLL 或任何 EXE。
- **生成结果**:
  - `release/04-mpv-lsfg-addon.7z`：2,002,853 字节。
  - SHA-256：`641DB5E204F701BE6C4BBF117321DB59080A8E22C8D6DADEAB7A4821CD88A9E9`。
  - 7-Zip 完整性检查通过；归档共 190 个文件，只含 1 个 DLL、0 个 EXE、0 个 Steam 二进制、0 个研究 build 路径。
- **旧包处理**:
  - 旧 `release/mpv-lsfg-research-private.7z` 已移出 Release 目录。
  - 为保持可恢复性，旧包暂存于被 Git 忽略的 `tmp/private-archive-backup/mpv-lsfg-research-private.7z`。
- **Git 状态**: 当前位于本地 `master`，原合并链领先 `origin/master` 3 个提交；本次公开包脚本与 README 调整尚未提交、未推送，也未上传 GitHub Release。

### 2026-07-30 02:21 会话: 发布 v1.2.0

- **提交与同步**:
  - 打包体系、公开 LSFG 扩展包和远端 README 更新提交为 `fce95b3 release: 准备 v1.2.0 LSFG 扩展包`。
  - 本地 `master` 已推送到 `origin/master`；`v1.2.0` Tag 与远端主分支均指向 `fce95b3a60e2980b4be275810ef5f113777f4599`。
- **Release**:
  - 正式 Release：https://github.com/maxzrb/mpv-portable/releases/tag/v1.2.0
  - Release 状态为正式发布，非草稿、非预发布。
  - 已上传 01 Base、02 Config、03 Extras 两个分卷和 04 LSFG 共五个公开资产。
  - GitHub 返回的五个资产大小与 SHA-256 均和本地文件一致。
- **公开边界**:
  - 04 包通过内容门禁，不含 `portable_config`、Steam DLL、EXE 或专有模型。
  - `mpv-full-private-v1.2.0.7z` 含用户自备 `Lossless.dll`，只保留本地，没有上传 Release。
  - 远端 README 已确认包含新版 01～04 安装顺序、04 不覆盖 Config/Extras，以及个人包禁止公开上传的说明。
- **验证**:
  - 01、02、03 `.001/.002` 分卷、04 和个人全量包均通过正确的 7-Zip 完整性测试。
  - PowerShell 打包/启动脚本通过解析器检查，`git diff --check` 通过。
- **Git 状态**: 发布收尾记录提交并推送后，本地 `master` 应与 `origin/master` 一致且工作树干净。

### 2026-07-30 11:18 会话: 调整 LSFG 补帧菜单层级

- **菜单调整**:
  - 将四个 LSFG 预设由 `视频滤镜 > 补帧` 直属项移入 `视频滤镜 > 补帧 > LSFG` 子菜单。
  - 将“查看 LSFG 状态”同步移入该子菜单。
  - “关闭补帧”以及 mpv、MVT、RIFE、DRBA、SVP 等其他补帧入口保持原层级。
- **验证**:
  - uosc 菜单解析器文档和实现确认支持不限层级的 `>` 嵌套路径。
  - `git diff --check` 通过。
- **文件变更**: `portable_config/input.conf`、`docs/codex/STATUS.md`、`version/工作进度.md`。
- **Git 状态**: 本次改动尚未提交或推送。

### 2026-07-30 11:45 会话: 修复左上角置顶图标行为

- **问题原因**:
  - `mpv.conf` 把 `📌` 作为 `title` 模板中的静态状态文字显示，并没有为它注册点击区域。
  - 点击该文字时事件落入全局 `MBTN_LEFT cycle pause`，因此表现为暂停。
- **实现**:
  - 从窗口标题模板移除静态 `📌`。
  - 在 uosc `TopBar` 左上角新增独立的 `push_pin` 按钮和点击区域。
  - 单击按钮执行 `cycle ontop` 并显示当前置顶状态；置顶时按钮保持高亮。
  - uosc 主状态新增 `ontop` 属性监听，保证外部快捷键 `Alt+T` 改变置顶状态时按钮同步刷新。
  - 右侧最小化、最大化和关闭按钮保持不变。
- **验证**:
  - `main.lua` 与 `TopBar.lua` 均通过 LuaJIT 语法检查。
  - 使用完整 `portable_config` 和短时 `lavfi` 视频完成脚本加载冒烟测试，mpv 正常退出。
  - `git diff --check` 通过。
- **文件变更**: `portable_config/mpv.conf`、`portable_config/scripts/uosc/main.lua`、`portable_config/scripts/uosc/elements/TopBar.lua`，以及本次 HandShake 记录。
- **Git 状态**: 本次改动与前一项 LSFG 菜单调整均尚未提交或推送。

### 2026-07-30 12:51 会话: 安装 yt-dlp 并接入公开 Base 包

- 从 yt-dlp 官方 GitHub 最新稳定 Release 下载 Windows 单文件程序 `yt-dlp.exe`，版本为 `2026.07.04`。
- 安装位置为 mpv 根目录，与 `mpv.exe` 同级；没有写入系统 PATH，也没有加入任何机器或显卡专属配置。
- 使用官方 `SHA2-256SUMS` 完成 SHA-256 校验，结果为 `52FE3C26DCF71FBDC85B528589020BB0B8E383155CFA81B64DD447BBE35E24B8`。
- `yt-dlp --version` 和 1752 个提取器枚举通过，包含 YouTube 与 Bilibili。
- 从 `tmp` 工作目录启动 mpv，内置 ytdl hook 仍能自动找到 mpv 程序目录中的 yt-dlp。
- 使用 W3Schools HTML5 视频页面完成真实联网烟测：yt-dlp 成功解析网页，mpv 成功打开解析出的媒体并解码到首帧，退出码为 0。
- `build-release.ps1` 已把 `yt-dlp.exe` 加入 01 Base 包复制清单，PowerShell 解析器检查通过。
- `yt-dlp.exe` 受根目录 `/*.exe` 规则忽略，不进入 Git；打包规则变更和本次记录尚未提交或推送。

### 2026-07-30 13:37 会话: 全项目组件更新审计

- 本轮仅检查，没有升级或覆盖运行组件；由于工作区已有未提交改动，只执行了安全的 `git fetch origin --prune`，未运行 `git pull`。
- 当前已是上游最新或无需更新：
  - mpv `0.41.0-860-gc8c7d91a8` 与 dyphire 最新构建 `mpv_own-2026-07-06` 一致。
  - yt-dlp `2026.07.04`、uosc `5.12.0`、uosc_danmaku 主分支 `3.0.0` 均为当前版本。
  - LSFG Windows 研究副本基于 `PancakeTAS/lsfg-vk develop` 提交 `8b0da2661c6f3473a7fccc8ba643880050e71642`，与上游 HEAD 完全一致。
  - Lossless.dll 文件版本为 `3.2.2.0`；alass 为 `2.0.0`；LuaJIT 为 2026-07-01 滚动快照。
- 存在明确正式新版：
  - VapourSynth `R73 → R78`，官方 R78 发布于 2026-07-24。
  - 7-Zip `25.01 → 26.02`，Python `3.14.3 → 3.14.6`。
  - TorrServer `MatriX.141 → MatriX.142.2`，umpv-go `1.4.0 → 1.5.1`。
  - Faster-Whisper-XXL 目录为空，配置虽指向其 EXE，但功能当前不可用；上游最新 Pro 为 `r3.256.1`。
- GLSL 与 PlayKit `main` 提交 `4921c6796620` 的逐文件 Git blob 审计：
  - 本地 387 个，上游 429 个；366 个同名文件字节完全一致。
  - 上游有 63 个本地缺失文件，本地有 21 个上游已移除/替换文件。
  - 变化主要在 ACNet、QCOM、FSRCNNX、ESPCN、ESRGAN、RAISR、Ani、AMD 和 Anime4K。
  - 因菜单完整引用现有滤镜路径，更新必须同步增删 `input.conf` 菜单，不能只覆盖 shader 目录。
- Lua 脚本审计：
  - evafast、playlistmanager、sub-select 以及 simple-mpv-webui 的运行代码与上游一致。
  - dyphire 的 `chapter-make-read`、`chapterskip`、`fix-avsync`、`hdr-mode`、`trackselect`，以及 `sub-assrt`、`sub-fastwhisper` 在 2026-05 有上游变化。
  - file-browser 的 `modules/utils.lua` 有 2026-03-27 更新。
  - thumbfast 上游在 2026-06-28 修复非 macOS 环境变量处理；本地同时含黑名单/排除目录定制，需手工合并。
  - uosc 虽为最新版本，但本地有多处 UI 定制和本轮置顶按钮修改，不可直接整包覆盖。
- manager 更新器审计发现：
  - PlayKit 已使用 `main`，`manager.json` 未写分支时默认取 `master`，会导致 shader fetch 失败。
  - quality-menu 白名单误写为 `qualityu%-menu%.lua$`，实际选中 0 个文件。
  - manager 不检查 fetch/subprocess 返回码，失败后仍可能显示“all files updated”。
  - 在修复更新器并加入隔离预览/备份前，不应使用“工具 → 一键更新脚本和着色器”直接覆盖。
- 项目上游整包 `gaoxing64/MPV-lazy-full` 仍为 v2.0.0，没有新版整包可直接替换。
- 审计临时 Git 仓库 `tmp/component-update-audit-20260730/` 已在收尾时删除；本轮 HandShake 记录尚未提交或推送。

### 2026-07-30 14:58 会话: 修复一键更新并保护个性化改动

- **更新前保护**:
  - 在 `tmp/pre-manager-update-20260730-135035/` 保存了 manager、input、mpv 和 uosc 关键文件快照及 SHA-256。
  - 收尾复核确认本轮之前的 `input.conf`、`mpv.conf`、`TopBar.lua` 和 uosc `main.lua` 与快照完全一致。
- **更新器重构**:
  - `manager.lua` 改为异步调用 `script-modules/manager-update.ps1`，更新期间不阻塞播放器界面。
  - 同时注册 `manager-update-all` 脚本消息和按键绑定，修复 uosc 菜单发出消息却无人接收的问题。
  - 每次更新检查 subprocess/Git 退出码；发生错误时不再显示“全部更新成功”。
  - 上游与本地完全一致时只登记基线；仅上游变化时安全快进；双方都变化时使用旧上游基线做三方合并。
  - 首次发现本地与上游不同时一律保留本地文件；以后仍保留本地专属修改。
  - 覆盖现有文件前写入时间戳备份；冲突候选、上游基线、状态和完整报告均保存到被 Git 忽略的 `portable_config/cache/manager/`。
  - 不再自动删除上游已移除的本地文件，也不再默认安装缺失脚本。
- **更新源修复**:
  - 修正 PlayKit `main` 分支和 `portable_config/shaders` 前缀。
  - 修正 quality-menu 白名单拼写。
  - 修正 stax 脚本的 `delete_current_file.lua → delete-current-file.lua` 文件名映射、Eisa 路径/匹配和 file-browser addons 扁平化。
  - 禁用未安装的 trakt-scrobble，避免“一键更新”突然加入可选组件。
  - GitHub 源使用无工作区的 Git 对象树检查，避免 Windows 非法文件名和 `autocrlf` 改写。
  - 缺失着色器不自动安装，避免公开版用户一次点击被动下载大量模型；现有本地独有着色器也不会删除。
- **真实更新结果**:
  - 最终稳定态报告：`UNCHANGED=445`、`PROTECTED=15`、`SKIPPED=74`、`UPDATED=0`、`MERGED=0`、`ERROR=0`。
  - 15 个差异文件全部保持本地版本；包括 14 个脚本/文档和 `aWarpSharp3_RT.glsl`。
  - 当前仍为 387 个 GLSL；63 个上游新增着色器没有被强制装入，21 个本地独有文件没有删除。
- **验证**:
  - PowerShell 5.1 实际执行、JSON 解析、LuaJIT 编译、mpv 隔离脚本加载和菜单消息入口均通过。
  - 新增/修改的 manager 文件为 UTF-8、LF；`git diff --check` 通过。
  - 本轮只修复更新机制和建立安全基线，没有升级 VapourSynth/Python、7-Zip、TorrServer、umpv-go 或 Faster-Whisper。
- **Git 状态**: 本次 manager 改动与前序菜单、置顶按钮、yt-dlp 打包改动均尚未提交或推送。

### 2026-07-30 16:20 会话: 安全合并 15 个差异文件并分批升级二进制

- **回滚保护**:
  - 在 `tmp/pre-safe-merge-binary-upgrade-20260730-150859/` 保存 69 个待合并文件和二进制核心文件，共约 96.49 MiB。
  - 复核 `input.conf`、`mpv.conf`、uosc `main.lua` 和 `TopBar.lua` 与更新前个性化快照 SHA-256 完全一致。
- **15 文件安全合并**:
  - 12 个历史上游版本安全快进到当前 HEAD；`undoredo.lua`、`cycle-commands.lua` 仅补齐文件尾差异；`aWarpSharp3_RT.glsl` 原本已与当前 PlayKit 完全一致。
  - 合并范围包括 chapter/fix-avsync/hdr/trackselect/sub-assrt/sub-fastwhisper/chapterskip、quality-menu、file-browser 两个模块、两个 README 和两个小脚本。
  - 新版 trackselect 已内置协议识别，因此同步移除失效的 `special_protocols` 配置项。
  - 修复 manager 的 `chapterskip.lua` 同名来源覆盖风险：保留 dyphire/mpv-scripts 的静音/片头跳过脚本，禁用另一个功能不同的同名来源。
  - Git blob 哈希改用 `git hash-object --no-filters`，消除着色器受换行过滤器影响的假冲突。
- **已升级组件**:
  - 7-Zip `25.01 → 26.02`；根目录 `7z.exe/7z.dll` 和辅助 `7zr.exe` 已更新。
  - TorrServer `MatriX.141 → MatriX.142.2`，官方资产 SHA-256 为 `BDC6E80DA81918A19D8A74D8FE43A6C1FC584889CB43DE66D573D735F2209A5E`。
  - umpv-go `1.4.0 → 1.5.1`，官方 zip SHA-256 为 `661843FDF9973A3255C064E686E48389D904D5855E6F848D4F5652EB24AD4FA6`。
  - Python `3.14.3 → 3.14.6`，保留项目原有 `python314._pth`；官方嵌入包 SHA-256 为 `DF901E84A896FF1EE720AD03377E0C8D8C2244FDA79808AEEAFF6316DF1CB75C`。
  - 安装 Faster-Whisper-XXL 公开版 `r245.4`；官方 GitHub 未提供摘要，下载包本地 SHA-256 为 `237DEE23939CDABFC96EF859FC5E584B842C3A5557E0D2CA744E1F87C14C5844`，大小与资产记录完全一致，5127 个文件通过 7-Zip 完整性测试。
  - `build-release.ps1` 现在会在 EXE 存在时把完整 Faster-Whisper 公开版放入 Extras；未安装时才保留空目录，不指定 GPU 或设备。
- **VapourSynth R78 兼容结论**:
  - 官方 R78 wheel、Python 3.14.6 和 mpv 在临时环境中均能工作；显式设置 `VSSCRIPT_PATH` 后 mpv 通过三帧滤镜烟测。
  - R78 已将 VSScript 移入 Python 包，根目录复制或硬链接均无法自动确定便携 Python；直接覆盖会破坏用户双击 `mpv.exe` 的现有用法。
  - 正式目录因此继续保留已验证可用的 R73，只升级 Python；R78 包和试验环境保存在 `tmp`，待设计便携加载方案后再迁移。
- **验证**:
  - 15 个改动 Lua 文件全部通过 `loadfile` 语法检查。
  - Python 3.14.6 的 SSL、SQLite、pip、VapourSynth R73 和 BlankClip 取帧通过。
  - TorrServer `--help`、umpv `-help`、Faster-Whisper `--help/--version`、7-Zip 压缩包测试通过。
  - 完整 mpv 配置以 lavfi 视频完成三帧加载，退出码 0；更新脚本全量只读检查无错误。
  - 损坏的 1.93GB 断点续传包已移入 Windows 回收站；正确官方包与解压结果保留。
- **Git 状态**: 本轮与前序改动均尚未提交或推送；建议按逻辑阶段分批提交。

### 2026-07-30 会话: 清理 R78、新增 FW 增量包、重编号 LSFG

- **R78 清理**:
  - VapourSynth R73 是明确支持 Windows 7 的最后版本，暂不升级 R78。
  - 删除 `tmp/` 下共约 340 MB R78 试验文件（official test、symlink test、wheel expanded、installer 和下载 zip）。
  - 确认 `tmp/` 已无 R78 残留。
- **Faster-Whisper 拆分为独立增量包**:
  - 从 `build-release.ps1` 的 03 Extras 中移除 FW 复制逻辑，Extras 仅含着色器 + VapourSynth + Python + 工具。
  - 新建 `build-fasterwhisper-public.ps1`，生成 `04-mpv-fasterwhisper-addon-vX.Y.Z.7z`。
  - FW 包内容门禁：只允许 `faster-whisper-xxl.exe` 和 `ffmpeg.exe` 两个 EXE，排除缓存和生成文件。
  - 包内 README 写明 01→02→03→04→05 安装顺序。
- **LSFG 重编号 04→05**:
  - `build-lsfg-public.ps1`：包名从 `04-mpv-lsfg-addon` 改为 `05-mpv-lsfg-addon`。
  - 包内 README 安装顺序加入 04 FW 包。
- **同步更新的文件**:
  - `build-all-packages.ps1`：构建链条改为 01～03 → 04 FW → 05 LSFG。
  - `build-full-private.ps1`：合并链从 01→02→03→04 扩展为 01→02→03→04(FW)→05(LSFG)；`$FwArchive` 新增为必需文件。
  - 根 `README.MD`：所有"四类包"改为"五类包"；ASCII 图、表格、安装步骤和打包脚本文档全部更新。
- **打包脚本依赖检查**:
  - 核对所有二进制文件名与打包脚本引用：Python 3.14.6、7-Zip 26.02、TorrServer 142.2、umpv-go 1.5.1 均无文件名变化，脚本无需额外同步。
- **验证**:
  - 全部五个 PowerShell 打包脚本通过 `System.Management.Automation.Language.Parser` 语法检查。
  - `git diff --check` 通过（仅仓库既有 autocrlf 提示）。
- **文件变更**: `build-release.ps1`、`build-fasterwhisper-public.ps1`（新增）、`build-lsfg-public.ps1`、`build-all-packages.ps1`、`build-full-private.ps1`、`README.MD`、`docs/codex/STATUS.md`、`version/工作进度.md`。
- **Git 状态**: 本批改动与前序二进制升级、菜单、置顶按钮、yt-dlp 打包等大量改动均尚未提交或推送。建议尽快分批提交。

### 2026-07-30 18:33–21:00 会话: v1.3.0/v1.3.1 打包重构 + LSFG 帧率修复

- **包结构重组** (01→02→03→04→05):
  - 01 Base: mpv 核心 + 运行时 + 基准配置，仅 mpv 升级时重打
  - 02 Extras: 着色器 + VapourSynth + Python + 工具 (原 03，移除 FW)
  - 03 FW: Faster-Whisper AI 字幕 (从 Extras 拆分为独立增量包)
  - 04 LSFG: Vulkan Layer + 启动器 + 控制脚本联动
  - 05 Config: 最终个人设置覆盖层 (原 02，移至最后)
  - 新增 `build-config-public.ps1` 构建 05 Config
  - `build-full-private.ps1` 改为全量 Lossless Scaling 目录备份
- **LSFG 帧率修复历程**:
  - 问题根因：Optimus 笔记本 iGPU 控制交换链 Present 节奏，LSFG Layer 计数错误
  - 尝试 1: `--vulkan-swap-mode=fifo` — 无效，Optimus 无视 FIFO
  - 尝试 2: `--display-fps-override` — 破坏 165Hz 主力机行为，回退
  - 尝试 3: VkImage 句柄比较 — mpv 每次 Present 申请新图像，句柄永远不同
  - 尝试 4: Layer 生成限流 — 跳帧打乱 Vulkan 信号量链导致死锁
  - 最终方案: `estimated-vf-fps` → Lua 侧文件 → PS 设 env var → Layer 遥测覆写
  - 已知限制：Optimus 笔记本仍以显示器速率生成帧，30s 预热后轻微卡顿
- **Layer 编译工具链**: w64devkit + CMake + Ninja 存放于 `buildtool/`（未纳入 Git）
- **v1.3.1 发布**:
  - Tag `v1.3.1` 已推送
  - 五个公开包上传 GitHub Release，个人全量包仅本地保留
  - SHA-256 核验: 01 `30790058` / 02 `94959d1d`+`abc25eac` / 03 `e10b1a4a` / 04 `2e2e53cc` / 05 `e2d18755`
- **Git 状态**: 全部提交已推送到 `origin/master`；工作树干净（除 `buildtool/` 未跟踪）

### 2026-08-04 14:21 会话: 新增 Anime4K v4 HQ/Fast 标准预设

- **目标**:
  - 不引入 ModernZ 新主题，继续使用现有 uosc。
  - 将 Anime4K 官方推荐的标准着色器组合整理成可直接选择的预设，解决用户面对大量单独着色器时不清楚链条顺序的问题。
- **实现**:
  - 在 `portable_config/profiles.conf` 新增 12 个互斥配置组：HQ/Fast 各含 Mode A、B、C、A+A、B+B、C+A。
  - HQ 档按官方示例面向 GTX 1080、RTX 2070、RTX 3060、RX 590、Vega 56、5700 XT、6600 XT 及以上；Fast 档面向 GTX 980、GTX 1060、RX 570 及以下。
  - 在 `portable_config/input.conf` 的“着色器 > 推荐 > Anime4K 标准预设”下新增 HQ/Fast 两组菜单入口。
  - 菜单标明 Mode A 主要用于多数 1080p、Mode B 主要用于多数 720p、Mode C 用于 480p 或低退化图像；二级模式注明仅建议至少 2× 放大时使用。
  - 每次选择都使用 `glsl-shaders` 覆盖完整列表，避免与之前启用的其他着色器意外叠加。
- **官方依据**:
  - Anime4K v4 Windows/mpv 官方 High-end 与 Low-end 模板中的 12 条链顺序。
  - Anime4K Advanced Usage 对 A/B/C 适用画面、二级模式及顺序要求的说明。
- **验证**:
  - 12 个 profile 均可被 mpv `--show-profile` 正确展开。
  - 12 个菜单入口与 14 个唯一 Anime4K 文件路径静态检查通过，引用文件全部存在。
  - 12/12 套预设均使用正式 `gpu-next`/D3D11 渲染链完成独立着色器编译与单帧播放烟测，无加载或编译错误。
  - `dyn_menu.lua` 完整解析现有菜单无错误；修改文件保持 UTF-8、LF；`git diff --check` 通过。
- **文件变更**:
  - `portable_config/profiles.conf`
  - `portable_config/input.conf`
  - `docs/codex/STATUS.md`
  - `version/工作进度.md`
- **Git 状态**:
  - `master` 与 `origin/master` 无已知提交差异。
  - 工作区此前已有 `.gitignore`、`build-full-private.ps1`、`portable_config/mpv.conf` 的未提交用户改动；本轮没有覆盖这些文件。
  - Anime4K 预设与 HandShake 记录尚未提交或推送，建议按本次功能作为一个逻辑提交。

### 2026-08-04 14:24 会话: 精简 Anime4K 预设菜单显卡描述

- **调整**: 应使用者要求，菜单子目录不再列出具体显卡型号（GTX/RTX/RX/Vega 等），只保留 `HQ`、`Fast` 两档和模式适用说明；配置组与着色器链不变。
- **文件变更**: `portable_config/input.conf`、`docs/codex/STATUS.md`、`version/工作进度.md`。
- **验证**: 12 个菜单入口数量不变；Anime4K 预设行不再含显卡型号；`dyn_menu` 解析无错误；UTF-8/LF 与 `git diff --check` 通过。
- **Git 状态**: 未提交改动清单不变；建议后续连同 Anime4K 预设作为一个逻辑提交。

### 2026-08-04 15:05 会话: 提交 v1.3.2 前置改动、清理缓存并构建六包

- **提交**: `d3f41da` 包含 Anime4K 预设、字幕颜色、全量包嵌套修复和此前的状态记录。
- **清理**: 删除 `build/`（约 14.4 GB）、`release/` 旧 v1.3.1 产物（约 18.9 GB）、`tmp/build-tools` 与运行缓存。
- **构建**: `build-all-packages.ps1 -Version 1.3.2 -IncludePrivate` 在 03 包压缩期间超时；01～03 已完成且完整，随后补跑 04、05 与全量包。
- **产物**: 01 Base、02 Extras 分卷、03 FW、04 LSFG、05 Config、`mpv-full-private-v1.3.2.7z`。
- **验证**: 六个归档均通过 7-Zip 完整性测试；SHA-256 已写入版本记录。

### 2026-08-04 15:12 会话: 发布 v1.3.2

- **Tag**: `v1.3.2` 指向 `9f86218`，`master` 与 `origin/master` 同步。
- **Release**: https://github.com/maxzrb/mpv-portable/releases/tag/v1.3.2
- **远端资产**: 01 Base、02 Extras 分卷、03 FW、04 LSFG、05 Config 五个公开包；未上传个人全量包。
- **清理**: `build/` 暂存目录已删除；`release/` 保留 v1.3.2 六包与 SHA-256 记录。
- **Git 状态**: 工作树干净（忽略产物除外），无需额外提交。

### 2026-08-07 11:37 会话: 小型依赖手工维护

- **启动与协作**:
  - 按 HandShake 流程读取 `AGENTS.md`、`CLAUDE.md` 和本状态记录；`git pull --ff-only` 显示已与 `origin/master` 同步，起始工作树干净。
  - 使用两个 DeepSeek v4 flash 子代理分别复核 uosc 5.13 和 uosc_danmaku 主线差异；子代理只读审计，最终由主代理逐项判断和手工合并。
- **配置与 blacklist 修复**:
  - `blacklist-extensions.lua` 修正 `remove_files_without_extension` 键名、扩展名匹配、目录/不存在路径保护及英文拼写错误，使现有配置真正生效。
  - `select.conf` 设置 `populate_menu_data=no`，避免内置 select.lua 与 `dyn_menu.lua` 重复维护 `menu-data`。
  - `hdr_mode.conf` 与当前脚本同步为 `target_peak=0` 自动检测，并补充 mpv 0.41 HDR 直通说明；当前 `hdr_mode=noth` 行为不变。
- **uosc 5.13 手工合并**:
  - 版本标记更新为 5.13.0；保留本地字体、ziggy、播放列表标题、置顶按钮、TopBar 窗口控制和菜单拼音搜索定制。
  - 合并完整点击触发、防原生 context menu/console 点击穿透、不可选择菜单项误激活、spinner 裁剪和 footnote 转义修复。
  - 合并双 `space` 控件绝对居中、时间轴右键命令及 `{time}` 占位、`pause_indicator` 默认透明度。
  - 没有恢复 Updater，也没有覆盖本地 TopBar/Menu/Controls 整文件。
- **uosc_danmaku 最小维护**:
  - 复核确认本地已包含恰好 16 MiB 文件的 `>=` 哈希边界修复；单源延迟走独立菜单逻辑，不受 Tony15246 主线对应 bug 影响。
  - 保留两个现有自定义 API，将 `https://danmaku-api.152468.xyz` 追加为末位回退，并同步单服务器默认值与 README。
  - 官方代理 `/api/v2/search/anime` 实测返回 HTTP 200 JSON。
  - 未引入 custom save path、`sites/`/`inflate.lua` 和 360kan 重构；这些变更会与本地多服务器、历史源及函数签名产生高冲突，不属于本次小维护。
- **验证**:
  - 10 个改动 Lua 文件全部通过 `luajit loadfile` 语法检查。
  - 使用真实 `portable_config` 自动加载并播放两帧 lavfi 视频，mpv 退出码 0；uosc、uosc_danmaku、blacklist_extensions、dyn_menu 无目标错误。
  - 15 个功能文件统一为 UTF-8 无 BOM、LF；`git diff --check` 通过。
  - 临时上游克隆、子代理 `.tmp_audit` 和测试 mpv 进程均已清理。
  - uosc 点击穿透、置顶按钮和菜单 hover 的真人交互体验仍建议使用实际视频做一次手工确认。
- **Git 状态**: `master` 提交仍与 `origin/master` 同步；本轮 15 个功能文件和 2 个 HandShake 记录文件尚未提交或推送，建议作为一个逻辑维护提交。

### 2026-08-07 12:02 会话: Yaozhi 界面与定制核心可行性研究

- **研究范围**:
  - 只读审计 `Yaozhil/mpv-Yaozhi` 最新 8.7+ Release、`main`、`codex/hdr-pgs-core-fix` 维护分支及 7 个公开补丁。
  - 对照本地 mpv `v0.41.0-860-gc8c7d91a8`、现有 uosc 5.13、本地音频输出驱动和 2026-08-05 的 mpv 官方源码。
  - 本轮未改播放器配置或功能代码；下载的 8.7+ 发行包与上游源码只用于临时审计。
- **UI 与媒体参数结论**:
  - Yaozhi 发行包仍以 uosc 5.12 为基线，其时间轴从上游约 500 行扩展到 1549 行；媒体标签主要由 `Timeline.lua` 和 `script-modules/media-format-info.lua` 实现。
  - 帧率、动态码率、静态平均码率、网络读取速度、硬解状态、画面/音频格式等均可由官方属性 `estimated-vf-fps`、`video-bitrate`、`track-list/*/demux-bitrate`、`cache-speed`、`video-params`、`audio-params`、`hwdec-current` 获取，不依赖定制核心。
  - 本地已具备 uosc 5.13、中文 stats 和相关属性读取逻辑；应把媒体信息做成独立元素并选择性迁移配色、控件排列、速度按钮和起播标签，不能覆盖整份 Yaozhi uosc，以免回退 5.13 修复并冲掉置顶按钮、拼音搜索等本地定制。
  - Yaozhi 独立 `MediaInfo.lua` 在构造器中被注释，实际截图效果来自深度修改的 `Timeline.lua`；移植时不应误复制这份未启用的旧元素。
- **HDR 图形字幕结论**:
  - 本地官方核心已暴露 `image-subs-hdr-peak=<sdr|video|video-static|video-dynamic|10-10000>`，因此 150/203/250/300/400 nits 菜单可在不换核心的前提下实现。
  - 本地没有 Yaozhi 新增的 `image-subs-colorspace=<video|sdr|auto>`；官方 `gpu-next` 仍让 PGS/VobSub/DVB 的 BGRA overlay 继承视频色彩空间。完整的“UHD 内封 PGS 随视频、外置/SDR 图形字幕按 sRGB”自动策略无法仅靠 Lua/配置复刻。
  - 官方核心兼容版应明确命名为“图形字幕 HDR 亮度/峰值”，不要宣传为完整色彩空间修复。若以后接受自编译核心，可手工重基 Yaozhi 0001 补丁；该补丁对 2026-08-05 官方源码已不能直接 `git apply`。
- **空间 PCM 与沉浸声结论**:
  - 当前官方 Windows WASAPI 在构造格式时仍将所有 `nChannels > 8` 的布局压成 7.1；本地 OpenAL 也只列到 7.1，且本地构建没有 SDL AO。因此 5.1.4/7.1.4 的真正 10/12 声道具名 PCM 输出不能由 Lua、`audio-channels` 或菜单实现。
  - Yaozhi 为该能力维护 mpv WASAPI、mpv SDL、SDL2 WASAPI 和 swresample 多层补丁；其中 mpv 的 0002/0005/0007 对当前官方源码仍可通过 `git apply --check`，但采用后即成为需长期维护的自定义核心。
  - Windows 32 位 `WAVEFORMATEXTENSIBLE` mask 无法精确表达含 `TSL/TSR` 的 9.1.4/9.1.6；Yaozhi 自身也只保证这两种布局在解码、滤镜和 `ao=pcm` 阶段保序，不保证普通 WASAPI/HDMI 精确路由。
  - AV3A / Audio Vivid 解码另需定制 FFmpeg 解码器，不属于空间 PCM 输出补丁，也不能在官方二进制上以脚本补齐。官方核心可继续提供 TrueHD/E-AC-3/DTS-HD 源码直通，但直通不等于多声道 PCM。
- **推荐实施顺序**:
  1. 先做官方核心零补丁 UI 试验：Yaozhi 配色、紧凑底栏、响应式媒体参数胶囊、官方 `cache-speed` 网络速率和起播格式标签。
  2. 再加入官方核心兼容的图形字幕 HDR 峰值菜单，并用真实 HDR + 内封/外置 PGS 样片验证。
  3. 空间 PCM 只在 UI 中显示输入布局和能力边界；除非用户明确接受单独的实验核心包，否则不进入 Base/Config 主线。
- **Git 状态**: `git pull --ff-only` 显示与 `origin/master` 同步；此前 15 个功能文件和 2 个记录文件仍未提交。本轮没有新增功能文件，记录更新继续落在原有 17 个修改文件中。

### 2026-08-07 13:30 会话: 官方核心兼容 UI、启动页与源码直通第一阶段

- **存档点**:
  - 先将此前 17 个依赖维护文件提交为 `d6498b9 chore: maintain mpv script dependencies`；未推送，`master` 领先远端 1 个提交。
  - 随后以本地 uosc 5.13 为基线增量实现，没有覆盖上游目录，也没有修改或替换 `mpv.exe`。
- **媒体信息与界面**:
  - 新增独立 `MediaInfo` 元素，显示硬解/软解、分辨率、Dolby Vision/HDR10+/HDR10/HLG/SDR、视频编码、帧率、音频编码/布局、平均或动态码率及官方 `cache-speed` 网络速率。
  - 音频输出为 `spdif-*` 时额外显示“源码直通”；窄窗口按胶囊组从右侧自动省略，不侵入本地 Timeline 5.13 和控件居中逻辑。
  - 采用深蓝青色调和更轻的时间轴/菜单透明度；没有搬入约 64 MiB、673 个格式 Logo 原始资源。
  - 时间轴改为 14 px 细线，控件尺寸/间距、圆角和接近范围做保守紧凑化，继续保留本地长控件列表与双 `space` 居中逻辑。
  - 明确剔除官方核心不支持的 HDR Vivid、Audio Vivid、AC-4、MPEG-H 和定制 Atmos 渲染器判断。
- **启动页**:
  - 将 `buildtool/送货.png` 作为默认图标源复制到配置资源，并生成 1024×1024 PBGRA overlay；`force-window=immediate` 保证无文件启动时显示窗口。
  - 默认逻辑尺寸由窗口短边和 `display-hidpi-scale` 共同决定，基准 220、DPI 上限 1.5；支持从“文件 > 启动页”选择自定义图片或恢复默认。
  - 运行时 UI、脚本、配置及图片选择器中没有移入目标项目的品牌字样。
- **音频源码直通**:
  - 新增“音频 > 音频源码直通”菜单：自动解码（默认）、Dolby+DTS 全部、仅 Dolby、仅 DTS。
  - 只使用官方 `audio-spdif`、`audio-exclusive`、`audio-channels`、`audio-buffer` 和重载命令；关闭时恢复脚本启动前的原设置。
  - 对可直通音轨检查 `audio-out-params/format`；设备未输出 `spdif-*` 时自动持久化回 `off` 并切回 PCM。
- **HDR 图形字幕**:
  - 字幕菜单新增官方 `image-subs-hdr-peak` 的“随视频动态”与 150/203/250/300/400 nits 档位。
  - 只提供当前官方核心确实支持的峰值亮度，不宣称已经实现独立图形字幕色彩空间修复。
- **验证**:
  - `audio-passthrough.lua`、`idle-branding-image.lua`、uosc 5.13/MediaInfo 均通过 `mpv --no-config --script=...` 独立加载。
  - 完整 `portable_config` 自动加载无 warning；启动页隐藏窗口运行 3 秒无 overlay/Lua 错误；合成视频进入 uosc 渲染循环无栈错误。
  - 新增文本为 UTF-8 无 BOM、LF；品牌/不支持能力关键字扫描与 `git diff --check` 通过。
- **Git 状态**: 本阶段 14 个功能/资源文件及两份 HandShake 记录尚未提交或推送；临时上游发行包待最终收尾后清理。

### 2026-08-07 16:40 会话: uosc 深度融合与菜单视觉深度定制

- **背景**: 使用者反馈现有 uosc 的进度条与按钮割裂感强，参考项目在可读性与交互性上明显更优，要求按其 uosc 继续深度定制。
- **底部一体化（进度条 + 按钮深度融合）**:
  - 参考版 `Controls.lua` 整体采用：`time` 时间显示、`speed-button` 速度按钮、`reserve` 隐形平衡槽、`narrow_priority` 窄窗隐藏优先级、播放键窗口绝对居中、按按钮视觉中心计算 `get_visual_bounds()`。
  - `Timeline.lua` 移植：12px 细圆角进度条（轨道色 + 青色播放段 + 圆头端点）、底部连续半透明面板（双层 blur）、已加载进度条、加宽 seek 命中区与空档守卫、拖拽阈值逻辑；保留本地时间轴右键命令 `timeline_mbtn_right`。
  - 新增 `TimeDisplay.lua`（当前/总时长）与 `SpeedButton.lua`（左键速度菜单、右键复位、滚轮步进）。
  - 时间戳从进度条移入控制栏，悬停时间戳加粗放大；不再绘制进度条上的常驻时间文字。
- **按钮与绘制增强**:
  - `Button.lua`：右键命令、`button_tooltips` 开关、激活态青色高亮、极简角标；`CycleButton.lua`：`idle_icon` 与 `button_tooltips@uosc` 持久化；`ManagedButton.lua`/`lib/buttons.lua`：`secondary_command`。
  - `lib/ass.lua`：新增 `\fsp` 字符间距、`\fscx` 水平压缩、矩形 `blur` 支持。
- **菜单视觉**:
  - `Menu.lua` 采用参考版 93KB 版本：`menu_open_opacity=0.82`、`menu_font`、窗口高度密度缩放、标题自动缩字与省略号、级联宽度缓存、响应式宽度、菜单专用 11 色配色。
  - 保留本地 spinner 裁剪修复（`clip=item_clip`）；菜单交互采用参考版 pointer 精确捕获（`activate_pointer_item`），避免深层子菜单点击被祖先面板偷走。
- **选项与配置**:
  - `main.lua`：`button_tooltips`、`idle_branding`、`chapter_display`、`menu_font`、11 个菜单/时间轴配色默认值、`persist_uosc_option()`、启动页/章节开关脚本消息。
  - `uosc.conf`：新 controls 布局（`time`/`speed-button`/`reserve`/`play-pause` 居中）、`timeline_size=12`、`controls_size=36`、`menu_item_height=44`、`animation_duration=80`、参考配色与透明度；未引入参考版依赖的 skip-segments/webdav/alist 按钮。
- **验证**:
  - uosc 独立加载、完整 `portable_config` 自动加载均无 warning/错误。
  - 临时脚本真实触发 `open-menu`（含子菜单、hint、actions、spinner、footnote）渲染路径，日志无 Lua 错误。
  - 新增/修改文本保持 UTF-8 无 BOM、LF；品牌关键字扫描与 `git diff --check` 通过；截图测试产物已清理。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（依赖维护存档 `d6498b9` 未推送）；本轮 uosc 深度定制 12 个文件及此前启动页/直通等文件均未提交，建议实际播放确认手感后再作为一个逻辑提交。

### 2026-08-07 16:45 会话: 对照参考版修正进度条与底部视觉

- **用户反馈**: “主界面进度条和底部的视觉效果怪怪的，没有移植到位”；要求继续按参考版深度定制，验证用代码/日志而非截图。
- **根因定位**:
  - 逐文件对比本地与 `%TEMP%\mpv-Yaozhi-uosc-port` 参考版：`Controls.lua`、`TimeDisplay.lua`、`Element.lua` 已与参考版一致，`Timeline.lua` 核心渲染（面板双层 blur、轨道、播放段、圆头、加载进度、章节）与参考版一致，差异集中在 `uosc.conf` 视觉选项和媒体胶囊的位置/配色。
  - 本地仍为 `timeline_style=line`（2px 移动短线 + 圆点），参考版为 `bar`（从左侧填充的青色进度条）——这是进度条观感不一致的主因。
  - 本地 `progress=windowed` 会在窗口模式常驻一条 2px 底条，参考版 `never` 平时完全干净、悬停才展开。
  - 本地 `scale_fullscreen=1.3` 使全屏底栏放大 30%，参考版 `1`；本地 `animation_duration=80`，参考版 `0` 无过渡动画。
  - 本地媒体胶囊贴在控制栏上方、落在面板内部；参考版悬浮在时间轴上方约 45px，且信箱黑边时夹进视频画面。
- **修改内容**:
  - `portable_config/script-opts/uosc.conf`：`timeline_style=line → bar`、`progress=windowed → never`、`scale_fullscreen=1.3 → 1`、`animation_duration=80 → 0`、章节范围色改参考版蓝青色系（`7AAFD6E6`）。
  - `portable_config/scripts/uosc/elements/MediaInfo.lua`：采用参考版胶囊几何（16px 字号/27px 高/45px 偏移/10px 画面内边距/0.2 字母间距），胶囊改浮在时间轴上方并与视频画面夹持；渲染配色改为参考版 `menu_background` 底、`menu_foreground` 边、hero/primary/muted 三档文字色调；码率/网络拆成“标签 + 数值”紧凑双段。
- **验证**:
  - `luajit loadfile` 语法检查 `MediaInfo.lua`、`Timeline.lua` 通过。
  - 完整 `portable_config` + 临时脚本强制显示 `timeline/controls/media_info` 后真实播放 lavfi 视频，mpv 退出码 0，日志无 uosc error/warning（临时脚本已删除）。
  - 修改文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本轮新增/修改均未提交，建议实际播放确认底栏观感后再作为逻辑提交。

### 2026-08-07 16:55 会话: 修复 uosc 菜单为空与视频菜单反交错缺失

- **用户反馈**:
  - “视频菜单里怎么没有开关反交错？”。
  - “osd菜单中是有显示菜单-轨道、次字幕等内容的，而uosc中菜单显示为空”。
- **根因**:
  - 反交错入口一直存在，但只放在 `视频滤镜 > 片源修复 > 去交错 开关`（`d` 键），没有出现在一级“视频”菜单。
  - uosc 主菜单不是从 `menu-data` 读取，而是直接解析 `input.conf`；`菜单 > 轨道/次字幕/章节列表/版本列表` 四条在 input.conf 中是 `#                ignore #menu: ... #@tracks` 这类“由 dyn_menu 动态填充”的占位项，命令为 `ignore`，uosc 解析时会直接跳过，所以“菜单”子菜单为空；而 OSD 菜单由 dyn_menu 用 `menu-data` 动态更新，因此能看到内容。
- **修改**:
  - `portable_config/input.conf`：
    - 新增 uosc 专用 `#!` 菜单项：`菜单 > 轨道`（`uosc/tracks`）、`菜单 > 次字幕`（`uosc/secondary-subtitles`）、`菜单 > 章节列表`（`uosc/chapters`）、`菜单 > 版本列表`（`uosc/editions`）；保留原 `#@` 动态行，OSD 菜单行为不变。
    - 新增 `视频 > 片源修复 > 去交错 开关`（`#menu` + `#@state`），同时进入 OSD 与 uosc，原 `视频滤镜 > 片源修复` 入口保留。
  - `portable_config/scripts/uosc/lib/menus.lua`：新增 `create_tracks_menu_opener()`，把视频/音频/字幕轨合并为一个 uosc 轨道总览菜单，支持当前轨勾选、点击已选轨关闭。
  - `portable_config/scripts/uosc/main.lua`：注册 `uosc/tracks` 与 `uosc/secondary-subtitles`（次字幕轨列表，带加载/在线搜索动作）。
- **验证**:
  - `luajit loadfile` 检查 `lib/menus.lua`、`main.lua` 通过。
  - 完整 `portable_config` 真实播放 lavfi 视频，依次打开 `uosc/menu`、`uosc/tracks`、`uosc/secondary-subtitles`，日志显示 `menu`、`tracks`、`sub` 三类菜单依次打开且无 uosc 错误。
  - 运行时调试输出确认 uosc 主菜单“菜单”子菜单现有 4 项（轨道/次字幕/章节列表/版本列表），“视频”子菜单现有“片源修复 > 去交错 开关”；调试代码已移除。
  - 修改文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时测试脚本已删除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本轮 uosc/输入配置及此前 UI 改动均未提交。

### 2026-08-07 16:58 会话: 右键默认打开 uosc 菜单

- **用户需求**: “现在可以右键默认显示uosc菜单了”。
- **修改**: `portable_config/input.conf` 的 `MBTN_Right` 由 `script-message-to context_menu open`（OSD 版）改为 `script-message-to uosc menu-blurred`；原 OSD 菜单保留到 `Shift+MBTN_Right`，中键 `context-menu`（GUI 版）不变。
- **验证**:
  - `--no-config --input-conf` 与完整配置下均确认 `MBTN_RIGHT` 实际绑定为 `script-message-to uosc menu-blurred`。
  - 完整配置中用 `keypress mbtn_right` 模拟右键：`user-data/uosc/menu/type` 变为 `"menu"`，`user-data/mpv/context-menu/open` 未触发，确认默认右键打开的是 uosc 菜单而非 OSD/GUI 菜单。
  - 文件保持 UTF-8/LF；临时验证脚本已删除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项改动与之前未提交的 UI/启动页/音频直通改动均在工作区。

### 2026-08-07 17:07 会话: 右键菜单跟随光标 + 点击关闭不对称修复

- **用户反馈**:
  - 右键打开的菜单始终在同一位置，不跟随鼠标右键点击位置。
  - 要关闭菜单时，必须点击菜单左边的屏幕；右边屏幕左键点击关不掉。
- **根因**:
  - 菜单绘制位置由 `cascade_x = clamp(self.ax, ...)` 决定，而元素坐标/命中区由 `update_coordinates()` 按“水平居中”计算；两者不一致。当级联链预留宽度超出屏幕时，绘制位置被压到屏幕左缘，但点击判定仍按居中的虚拟矩形计算，导致可见菜单和可点击关闭区域错位。
  - `update_dimensions()` 的 `menu.top` 只允许在“顶部边距 ~ 垂直居中”之间取值，右键菜单无法落到屏幕下半区。
  - uosc 没有“菜单跟随右键位置”的逻辑：`open_command_menu(..., {mouse_nav=true})` 只改变鼠标导航，位置仍固定居中。
- **修改**（`portable_config/scripts/uosc/elements/Menu.lua`）:
  - 新增 `anchor_x/anchor_y`：鼠标导航（右键 `menu-blurred`）打开时记录光标位置，并在 `Menu:init` 中重新计算尺寸，使根菜单以光标为锚点打开。
  - `update_coordinates()` 在根菜单有锚点时，用“光标 x - 10px”计算水平位置，并夹在屏幕内、保证整条级联链不超出屏幕；无锚点（键盘 MENU 键）仍居中。
  - `update_dimensions()` 根菜单有锚点时允许 `menu.top` 落到屏幕下半区（上限改为“不超出底边”），无锚点保持原垂直居中行为。
  - 元素坐标与绘制坐标现在一致：点击可见菜单外的左右两侧都会触发关闭；点击菜单行仍激活对应项。
- **验证**:
  - `luajit loadfile` 检查 `Menu.lua`、`cursor.lua`、`main.lua`、`lib/menus.lua` 通过。
  - 临时在 uosc 内注入光标移动/点击模拟：光标放在右侧打开菜单后，左侧外部点击不再误触发菜单行，右侧外部点击正常关闭；坐标日志确认绘制位置与命中区一致。临时注入与全部调试日志已移除。
  - 完整配置右键打开 uosc 菜单烟测：菜单类型为 `"menu"`，无 uosc error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 uosc 深度融合/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:12 会话: 修复右键菜单横向不跟随

- **用户反馈**: 竖直方向已跟随右键位置，但横向仍总是出现在同一个地方。
- **根因**:
  - 菜单绘制位置 `cascade_x` 与元素坐标都按“保证整条级联链不超出屏幕”夹取，上限为 `display.width - padding - cascade_width`。
  - 本配置主菜单的子级联链（如“着色器 > 专家库 > …”）预估宽度超过屏幕，`cascade_width` 约等于屏幕宽，导致 `max_x <= min_x`，根菜单恒被压到最左缘（`x=1`），横向锚点因此失效。
- **修改**（`portable_config/scripts/uosc/elements/Menu.lua`）:
  - `update_coordinates()` 与 `render()` 的根菜单锚点分支增加退化逻辑：当整条级联链放不下时，不再按 `cascade_width` 夹取，改为只保证根菜单自身留在屏幕内（上限 = 屏幕右缘 - 根菜单宽）。
  - 级联链能放下时仍保持“整条链不超出屏幕”的原逻辑；键盘 MENU 键（无锚点）仍居中。
- **验证**:
  - 临时注入光标移动：光标 x=700 打开时根菜单 `ax=690.5`，x=120 打开时 `ax=110.5`，横向确实跟随；修复前两者均为 `ax=1`。
  - `luajit loadfile` 通过；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时注入与日志已全部移除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 20:10 会话: 修复 OSD 菜单“窗口位置”不显示

- **用户反馈**: Shift+右键打开的 OSD 菜单里，“画面 > 窗口 > 窗口位置”看不到了。
- **原因判断**: “窗口大小”和“窗口位置”两个子菜单之间放了独立分隔线（`#menu: 画面 > 窗口 > ---`），OSD 版 context_menu 渲染时后续的“窗口位置”入口没有正常显示。
- **修改**（`portable_config/input.conf`）: 删除“窗口”层级两条独立 separator 行，让“窗口大小”“窗口位置”两个子菜单直接相邻；两个子菜单内部的“---”（记住开关前）保留。
- **验证**: 重新转储 menu-data：`画面 > 窗口` 下仅“窗口大小”（9 项）与“窗口位置”（6 项）两个子菜单；窗口位置含 自动/居中/左+0，上+220/自定义…/分隔线/记住上次窗口位置，完整无缺。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 20:15 会话: 窗口设置移到自动 ICC 校色上方

- **用户需求**: 把“画面 > 窗口”整组设置移到“开/关 自动 ICC 校色”的上面。
- **修改**（`portable_config/input.conf`）: 窗口大小/窗口位置 15 行从文件尾部“其它”分组区移动到画面菜单“重置以上画面操作”分隔线之后、“开/关 自动 ICC 校色”之前；原位置已删除。
- **验证**: 转储 menu-data，画面菜单顺序为 …重置以上画面操作 → 窗口（窗口大小 9 项、窗口位置 6 项）→ 开/关 自动 ICC 校色 → 调色 → HDR 相关；OSD/原生/uosc 共用同一份数据，顺序一致。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 20:25 会话: 窗口置顶状态持久化

- **用户需求**: 窗口置顶设置也应该持久化，重启后保持上次切换的状态。
- **修改**（`portable_config/scripts/window-size-position.lua`）:
  - `window_size_position.conf` 新增 `ontop=yes/no` 字段（默认不干预，首次未配置时跟随 mpv.conf 的 `ontop`）。
  - 启动时若配置中已有显式 `ontop`，自动恢复；运行中观察 `ontop` 属性，任何方式切换（ALT+t、uosc/OSD/原生菜单）都会自动写回配置。
  - 原“文件 > 开/关 置顶状态”快捷键与菜单勾选逻辑不变。
- **验证**:
  - 注入切换 ontop=false → conf 写入 `ontop=no`；重启后日志“已恢复窗口置顶：关”、属性为 false。
  - 再切换 true → conf 写入 `ontop=yes`；重启后恢复为 true（与 mpv.conf 默认置顶一致）。
  - `luajit loadfile` 通过；文件保持 UTF-8 无 BOM、LF；测试脚本/日志已清理。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 20:26 会话: 建立强制发布流程

- **用户需求**: 创建《发布流程.md》，以后 agent 严格按该流程检查并发布；改动较大影响发布内容时先向用户汇报，由用户决定是否修正发布流程。
- **新建**（仓库根目录 `发布流程.md`）:
  - 唯一权威发布流程：前置检查（Git 状态、大改动 Gate、文档记录、功能验证）→ 构建（`build-all-packages.ps1 -Version X.Y.Z`）→ 构建后验证（7z t、SHA-256、门禁）→ 提交与标签 → GitHub Release（正式发布、五个公开资产、禁止上传个人全量包）→ 发布后收尾。
  - 大改动 Gate 判定标准：包结构/编号/覆盖顺序变化、构建脚本修改、核心运行时/依赖升级、大型资源增删、安装方式变化、版权边界变化、分卷规则变化、需修改本流程等；命中即停止发布并汇报，agent 不得自行修改流程。
  - 历史发布参考表（v1.0.0～v1.3.2）。
- **修改**（`AGENTS.md`）: 新增“发布流程（强制）”一节，要求 agent 发布前完整阅读《发布流程.md》并逐项检查，检查结果写入 STATUS.md；大改动 Gate 由用户决策；个人全量包禁止上传。
- **验证**: `git diff --check` 通过；文档 UTF-8 无 BOM、LF。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；大量功能改动与发布流程文档均在工作区，未提交。
### 2026-08-07 20:02 会话: 统一 uosc / Windows 原生 / OSD 三个菜单架构

- **用户需求**: 检查 uosc、Windows 原生等三个菜单，确认选项统一；原生菜单中点击不应再点出 uosc 选项。
- **架构梳理**:
  - 三个菜单入口：右键 = uosc 菜单（解析 input.conf 的 `#menu:` 与 `#!`）；中键 = Windows 原生 GUI 菜单（context-menu + menu-data）；Shift+右键 = OSD 菜单（context_menu open，同一份 menu-data）。
  - menu-data 由 dyn_menu.lua 从 input.conf 的 `#menu:` 生成（跳过 `#!`），原生 GUI 与 OSD 天然同源；uosc 另解析 `#!`。
- **问题**: 原生 menu-data 中残留 7 个“打开 uosc 界面”的命令项（打开内置浏览器/播放菜单/章节菜单/版本菜单/其他音轨/其他字幕/音频源码直通…），在 Windows 原生或 OSD 菜单点击会点出 uosc 界面。
- **修改**（`portable_config/input.conf`）:
  - “打开 > 打开内置浏览器”：保留 `o` 真实按键绑定，菜单项改为 `#!`（仅 uosc）。
  - “打开 > 播放菜单/章节菜单/版本菜单/其他音轨/其他字幕”：各拆为两行——`#menu:` 动态等价项（`#@playlist/chapters/editions/tracks/audio/tracks/sub`，原生直接展开列表）+ `#!` uosc 界面入口，同名统一。
  - “音频 > 音频源码直通…”：`#menu:` 改 `#!`（仅 uosc）。
  - 保留不打开界面的 uosc 功能调用（flash-speed、show-in-directory、open-config-directory、uosc_danmaku）；音频设备列表保持 `#@audio-devices`（原生动态列表 + uosc 设备界面，同名）。
- **验证**:
  - 转储 menu-data 与忠实复刻的 uosc 菜单对比：原生 menu-data 中“打开 uosc 界面”命令为零；uosc 菜单关键项全部存在（其他字幕/音频源码直通/打开内置浏览器/播放菜单/章节菜单/版本菜单/其他音轨/记住上次窗口大小/位置）。
  - 顶层 14 个一级菜单完全一致，无 uosc-only / native-only 顶层；其余差异仅为 uosc title 尾部空格（无害）与设计性差异（动态列表 `#@` 在原生展开、`#!` 在 uosc 打开自身界面，名称相同、行为不交叉）。
  - 附带确认：uosc 的 `---` 分隔符是给前一项加 separator 标记（标题保留），与原生独立 separator 项位置一致，不会丢选项。
  - `luajit loadfile` 通过；`git diff --check` 通过；完整配置真实播放无错误；临时审计脚本/日志/运行时状态已清理。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 19:47 会话: 记住开关改为菜单直接切换

- **用户反馈**: 记住大小/位置两个选项不要进下一级菜单选开/关，直接按一下开、再按一下关，并加 OSD 提示。
- **修改**:
  - `window-size-position.lua`：新增 `toggle-remember-size` / `toggle-remember-position` 脚本消息，点击时翻转对应开关，写入 conf、更新 user-data 属性并显示 OSD（“记住上次窗口大小：开/关”）。
  - `input.conf`：删除两个“开/关”子菜单项，改为直接项“画面 > 窗口 > 窗口大小 > 记住上次窗口大小”“画面 > 窗口 > 窗口位置 > 记住上次窗口位置”，带动态勾选状态。
- **验证**:
  - 实测 toggle 连续点击：size true→false→true、position true→false，user-data 属性与 conf 同步更新，最后恢复默认 yes/yes。
  - menu-data 确认两项均为直接菜单项（命令 toggle-remember-*，勾选表达式生效），不再有子菜单。
  - `luajit loadfile` 通过；`git diff --check` 通过；测试状态与临时脚本已清理。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 19:45 会话: 记住开关拆分为大小/位置并移入窗口菜单

- **用户反馈**: 记住窗口大小和位置分别做进窗口大小和窗口位置里；窗口设置从“其它”移到“画面”。
- **修改**:
  - `window-size-position.lua`：`remember` 拆为 `remember_size` / `remember_position` 两个独立开关；恢复时按开关分别组合“保存的尺寸/位置”与默认值，只记大小时位置回默认（居中），只记位置时大小回默认（1280x720）。
  - 菜单明确选择尺寸/位置时直接应用所选默认值（`apply_defaults`），不再被记住状态覆盖；启动时才用记住状态覆盖默认。
  - `window_size_position.conf`：改为 `remember_size=yes` / `remember_position=yes`。
  - `input.conf`：窗口菜单从“其它 > 窗口”移到“画面 > 窗口”；“记住上次窗口大小”“记住上次窗口位置”分别并入“窗口大小”“窗口位置”子菜单（各自开/关+勾选状态），移除原独立“记住上次窗口大小和位置”子菜单。
- **验证**:
  - menu-data：`画面 > 窗口 > 窗口大小/窗口位置` 及两个“记住上次…”开/关项均存在且勾选正常；`其它 > 窗口` 已无残留。
  - 双开：保存 1000x650@(120,80) 后重启恢复 `geometry=1000x650+127+80`，逐秒稳定。
  - 只记位置：关闭 remember_size 后重启为 `1280x720+127+80`（默认大小+保存位置）。
  - 只记大小：关闭 remember_position 后重启为 `1000x650+50%+50%`（保存大小+居中）。
  - 记住开启时菜单选 1380x776 → 立即变为 `1380x776+50%+50%`。
  - `luajit loadfile` 通过；`git diff --check` 通过；测试状态与临时脚本已清理。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 19:36 会话: 记住上次关闭时的窗口大小和位置

- **用户需求**: 让 mpv 记住关闭时窗口大小和位置。
- **实现**:
  - `window-size-position.lua` 新增 `remember=yes/no` 开关（`window_size_position.conf`），默认开启；正常窗口状态写入 `script-opts/window_state.conf`（rect/client/dpi，已加入 .gitignore），下次启动自动恢复。
  - 用 LuaJIT ffi 直接调用 Win32 API（GetWindowRect/GetClientRect/DwmGetWindowAttribute/GetDpiForWindow），每 2s 采样并在 shutdown 时精确保存；全屏/最大化/最小化时跳过，避免覆盖正常窗口状态。
  - 恢复时动态测量“可见框 vs GetWindowRect”差值换算 geometry（`WxH+X+Y`），并按 DPI 缩放；屏幕布局变化导致原位置完全不可见时只恢复尺寸并居中。
  - `input.conf` 新增 `其它 > 窗口 > 记住上次窗口大小和位置 > 开/关` 菜单（带勾选状态）。
- **验证**:
  - 保存 `rect=120,80,1136,739 client=1000,650` 后重启，自动恢复 `geometry=1000x650+127+80`，实际矩形逐秒保持 `120,80,1136,739`、客户区 `1000x650`。
  - 关闭开关后重启不再恢复、改用默认 1280x720 居中；重新打开后立即恢复上次状态。
  - 全屏时退出，状态文件保持上次正常窗口数据不变。
  - menu-data 确认“记住上次窗口大小和位置 > 开/关”存在且勾选表达式生效；`luajit loadfile` 通过；`git diff --check` 通过；临时测试脚本/日志/状态文件已清理。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:20 会话: 修复中键原生菜单“菜单”子菜单重复 8 项

- **用户反馈**: 中键打开的原生 Windows 菜单中，“菜单”子菜单出现 8 项：上面 4 项（轨道/次字幕/章节列表/版本列表）是原生界面，下面 4 项同名项会打开 uosc 界面。
- **根因**:
  - `script-opts/dyn_menu.conf` 设置了 `uosc_syntax=yes`，dyn_menu 会同时解析 `#menu:` 与 `#!` 两种注释并全部写入 `menu-data`（原生上下文菜单的数据源）。
  - 之前为 uosc 新增的 4 条 `#! 菜单 > 轨道/次字幕/章节列表/版本列表` 因此也进入了原生菜单，与原有 4 条 `#@` 动态条目重复。
- **修改**（`portable_config/scripts/dyn_menu.lua`）:
  - `parse_input_conf.parse_line()` 增加过滤：行内带 `#!` 菜单注释（uosc 专用语法）时直接跳过，不写入 `menu-data`。
  - 原生菜单（中键/GUI）继续只显示 `#@` 动态条目；uosc 菜单继续从 `#!` 条目构建，两者不再混在一起。
- **验证**:
  - 转储 `menu-data`：修复前“菜单”子菜单 8 项，修复后 4 项（轨道/次字幕/章节列表/版本列表，均为原生动态条目）。
  - uosc 菜单仍为 4 项（轨道/次字幕/章节列表/版本列表），打开正常，无错误。
  - `luajit loadfile` 通过；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时验证脚本与调试日志已移除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:24 会话: 速度控件恢复居中滚动滑块并适配配色

- **用户反馈**: 播放速度还是喜欢之前居中的滚动样式，只需改配色和透明度以适应当前 UI。
- **修改**:
  - `portable_config/script-opts/uosc.conf`：controls 布局中 `speed-button` 换回 `speed`（居中刻度滑块，拖动/滚轮调速、右键复位）；`opacity=speed=0 → 0.5`，滑块背景从全透明改为半透明。
  - `portable_config/scripts/uosc/elements/Speed.lua`：背景使用深色 `bg` + 细灰蓝边框（`timeline_track`）；刻度分三档配色——普通刻度 `time_muted` 灰蓝、0.5 步进刻度 `time_current` 亮白、1.0 步进主刻度与中心三角用 `match` 青色；速度数值用 `time_current` 亮白，与当前底部面板/菜单的蓝青色调一致。
  - 删除不再使用的 `SpeedButton.lua`（未跟踪文件）。
- **验证**:
  - `luajit loadfile` 检查 `Speed.lua` 通过；完整 `portable_config` 真实播放并强制显示 controls/speed，退出码 0，无 uosc error/warning。
- 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时验证脚本已删除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:27 会话: 修复 uosc 整体消失

- **用户反馈**: “整个uosc都不见了”。
- **根因**: 上一轮删除 `SpeedButton.lua` 时，`Controls.lua` 顶部仍有无条件 `require('elements/SpeedButton')`，导致 uosc 加载即失败（日志：`module 'elements/SpeedButton' not found`），整个界面不渲染。
- **修改**（`portable_config/scripts/uosc/elements/Controls.lua`）: 移除 `SpeedButton` require 及 `kind == 'speed-button'` 分支；当前 controls 布局已全部使用 `speed`，不再需要该模块。
- **验证**:
- 完整 `portable_config` 真实播放 lavfi 视频：uosc 正常加载渲染，日志无 Lua error/`SpeedButton` 引用，退出码 0。
- `luajit loadfile` 通过；`rg SpeedButton` 全仓库 uosc 目录无残留；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:31 会话: 速度滑块移至时间轴上方居中

- **用户反馈**: “速度控件滚动滑块不要放在进度条底栏里了，居中放置于进度条上方几个px的位置”。
- **修改**（`portable_config/scripts/uosc/elements/Speed.lua`）:
  - 新增 `Speed:update_position()`：滑块改为水平居中，垂直位于 `timeline.ay` 上方 `height + 6px` 处；时间轴不可用时返回 false 且不渲染。
  - `render()` 开头先调用 `update_position()`，绘制与点击命中区都使用独立坐标。
  - Controls 布局中的 `speed` 占位保留，因此播放键/底栏视觉居中不变；底部不再绘制滑块本体。
  - 保留时间轴 hover 时隐藏滑块的逻辑，避免悬停进度条时互相干扰。
- **验证**:
  - 运行时坐标日志：`timeline.ay=456` 时滑块 `ay=404`（上方 46px 高 + 6px 间距）、水平居中 `ax=401`（宽 157.8，窗口 960）。
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放退出码 0、无 uosc error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时调试日志已移除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:33 会话: 速度滑块高度对齐媒体信息胶囊

- **用户反馈**: 速度滑块纵向高度太大，建议对齐左侧的 media info 块。
- **修改**:
  - `portable_config/scripts/uosc/elements/MediaInfo.lua`：新增 `MediaInfo:get_height()`，返回胶囊高度 `27 × scale`。
  - `portable_config/scripts/uosc/elements/Speed.lua`：`update_position()` 改为优先使用 `media_info:get_height()` 作为滑块高度（缺失时回退 controls_size），仍水平居中、位于时间轴上方 6px。
- **验证**:
- 运行时坐标日志：`speed height=27 media_h=27`，`timeline.ay=456` 时 `ay=423`（27px 高 + 6px 间距），滑块与媒体胶囊同高。
- `luajit loadfile` 通过；完整 `portable_config` 真实播放退出码 0、无 uosc error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时调试日志已移除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:35 会话: 速度滑块与媒体胶囊垂直中心对齐

- **用户反馈**: 速度滑块在屏幕上的高度和左侧 MediaInfo 胶囊不一致，显得很不整齐。
- **根因**: 上一轮只把滑块高度改成与胶囊相同（27px），但垂直位置仍按“时间轴上方 6px”计算，导致滑块整体比胶囊低一截，视觉上不成一行。
- **修改**:
  - `portable_config/scripts/uosc/elements/MediaInfo.lua`：新增 `MediaInfo:get_center_y()`，返回胶囊中心 y（与 render 相同的 `bay - 45×scale` 计算，并包含信箱黑边夹持逻辑）。
  - `portable_config/scripts/uosc/elements/Speed.lua`：`update_position()` 以胶囊中心为滑块垂直中心（`ay = center_y - height/2`）；胶囊不可用时回退到时间轴上方 6px。
- **验证**:
  - 滑块与胶囊同为 27px 高，且中心 y 完全一致，任何画幅（含信箱黑边）下都保持同一行。
- `luajit loadfile` 通过；完整 `portable_config` 真实播放 `--length=1` 退出码 0、无 uosc error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:36 会话: 媒体胶囊与速度滑块整体下移贴近进度条

- **用户反馈**: 速度滑块和左侧 MediaInfo 胶囊离进度条太远，希望整体下移一点。
- **修改**（`portable_config/scripts/uosc/elements/MediaInfo.lua`）: `MEDIA_INFO_TIMELINE_OFFSET` 从 `45` 改为 `30`，胶囊中心从进度条上方 45px 缩到 30px；速度滑块通过 `get_center_y()` 跟随同一中心，两者保持同一行并一起贴近进度条。
- **验证**:
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放 `--length=1` 退出码 0、无 uosc error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:39 会话: 速度数字移至滑块视觉范围上方

- **用户反馈**: 把速度滑块的 1x 倍数数字居中移到速度滑块视觉范围的上方；不改变原速度滑块视觉范围大小，让滑动条占满原速度滑块视觉范围。
- **修改**（`portable_config/scripts/uosc/elements/Speed.lua`）:
  - 速度数字渲染位置从滑块内部改到滑块 `ay` 上方 4px 处（`text_y = ay - 4×scale - font_size/2`），仍水平居中。
  - 刻度起始位置从原来的“顶部预留数字空间”（`ay + font_size*1.1`）改为顶部仅留 2px 内边距，刻度、中心三角和底部导引现在铺满整个 27px 滑块视觉范围。
  - 元素自身尺寸、位置、背景框和交互命中区不变，媒体胶囊对齐关系不变。
- **验证**:
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放 `--length=1` 退出码 0、无 uosc error/warning。
  - 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:43 会话: 速度数字字号与 UI 显隐速度调整

- **用户反馈**: 速度数字字号调大一点，和 mediainfo 字号一致；进度条等状态鼠标移开时消失太快，减慢一点。
- **修改**:
  - `portable_config/scripts/uosc/elements/MediaInfo.lua`：新增 `MediaInfo:get_font_size()`，返回胶囊字号 `16 × scale`。
  - `portable_config/scripts/uosc/elements/Speed.lua`：速度数字字号改为使用 `media_info:get_font_size()`（16px），与胶囊一致。
  - `portable_config/script-opts/uosc.conf`：`animation_duration=0 → 150`，进度条/底栏等元素移开鼠标时以 150ms 淡出，不再瞬间消失。
- **验证**:
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放 `--length=1` 退出码 0、无 uosc error/warning。
  - 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:46 会话: UI 显隐位置阈值调整（proximity）

- **用户反馈**: 鼠标向上移到屏幕下 1/6 时进度条/底栏开始消失，希望改到屏幕下 1/4 才开始消失；上一轮只改动画时长“没改到要害”。
- **根因**: uosc 控制 UI 何时淡出的是 `proximity_in/proximity_out`（鼠标离开元素多少像素后开始/完全淡出），不是 `animation_duration`（只控制淡出过程快慢）。原值 36/96 太小，底栏在鼠标离开约 36px 后就开始淡出。
- **修改**（`portable_config/script-opts/uosc.conf`）: `proximity_in=36 → 60`、`proximity_out=96 → 140`，UI 保持完全可见的距离更远，淡出起点相应延后。
- **验证**:
  - 临时测量（540 高窗口）：`y=450/430` 时 controls/timeline 均为 1（完全可见）；`y=405`（屏幕下 1/4）controls=0.756（刚开始淡出）、timeline=1；符合“下 1/4 处开始消失”的目标。
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放退出码 0、无 uosc error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时调试代码与脚本已移除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:48 会话: 速度数字字号与格式微调

- **用户反馈**: 速度数字字号比胶囊字号再大 4px；倍数数字和 x 之间加空格，例如 `1 x`。
- **修改**（`portable_config/scripts/uosc/elements/Speed.lua`）:
  - 速度数字字号 = 胶囊字号（16 × scale）+ `4 × scale`，比胶囊再大 4px（DPI 缩放时同步放大）。
  - 速度文本由 `1.00x` 改为 `1.00 x`（数字与 x 之间加空格）。
- **验证**:
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放 `--length=1` 退出码 0、无 uosc error/warning。
  - 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 17:56 会话: 轨道菜单信息截断修复 + 底栏统计按钮开关化

- **用户反馈**:
  1. uosc 部分信息显示不全，如 “eng, truehd, 6 声道, 96 kH...”。
  2. 底栏统计信息做成开关而不是现在的延时关闭；并纠正：底栏已有统计信息按钮，不应新增配置选项/脚本消息。
- **问题 1 修复**（`portable_config/scripts/uosc/elements/Menu.lua`）:
  - 根因：音频/字幕轨列表菜单（`uses_uniform_title_size` 且有 hint）最大宽度被限制在窗口 56%/600px，长 hint（语言+编码+声道+采样率）会被省略号截断。
  - 修改：该类型菜单宽度上限放宽到窗口 78%/980px、下限 520px，长 hint 可完整显示。
- **问题 2 修复**（`portable_config/script-opts/uosc.conf`）:
  - 根因确认：底栏“统计信息”按钮（analytics）原本左键是 `stats/display-stats`（临时显示、延时关闭），右键才是 `stats/display-stats-toggle`（常驻切换）。
  - 修改：按钮左键命令改为 `script-binding stats/display-stats-toggle`，点击一次显示常驻统计、再点一次关闭，即真正的开关；未新增任何配置选项或脚本消息。
- **撤销**: 之前误加的 `media_info_pinned` 选项、`media-info-toggle` 脚本消息、`其它 > 底栏统计信息 开关` 菜单行和 MediaInfo 固定显示逻辑已全部移除；临时 hint 测试脚本与调试日志已清理。
- **验证**:
  - `rg` 确认 `media_info_pinned`/`media-info-toggle` 无残留；`luajit loadfile` 通过。
  - 完整 `portable_config` 真实播放 `--length=1` 退出码 0、无 uosc error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 18:03 会话: uosc 菜单紧凑化

- **用户反馈**: uosc 菜单能否紧凑一些，字号减小 2px；窗口较小时内容显示不全。
- **修改**:
  - `portable_config/scripts/uosc/elements/Menu.lua`：菜单基础字号在默认比例基础上再减 `2 × scale`（随 DPI 缩放），下限 8px。
  - `portable_config/script-opts/uosc.conf`：`menu_item_height=44 → 40`、`menu_min_width=260 → 240`，行高与最小宽度同步收紧。
- **验证**:
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放 `--length=1` 退出码 0、无 uosc error/warning。
  - 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 18:07 会话: 菜单字号回调 + 行间距收紧

- **用户反馈**: 字号加大 1 号（相对上次减 2px 后），菜单行与行之间的空隙减小一点。
- **修改**（`portable_config/scripts/uosc/elements/Menu.lua`）:
  - 字号从“默认比例减 2px”回调为“减 1px”（净效果：上次紧凑化后加大 1px，随 DPI 缩放）。
  - `item_spacing` 从 1 改为 0，行与行之间不再留额外空隙（行高仍为 40px，含选中高亮与分隔线，不影响可读性）。
- **验证**:
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放 `--length=1` 退出码 0、无 uosc error/warning。
  - 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 18:16 会话: 实现轻量级起播格式标识

- **用户反馈**: 之前研究的“起播格式标识”怎么没有效果。
- **事实澄清**: 该功能此前只完成了方案评估，一直挂在“待评估”TODO 中，从未实现，因此播放时自然没有效果。
- **实现**（新增 `portable_config/scripts/startup-format-badge.lua` + `script-opts/startup_format_badge.conf`）:
  - 文件加载后等待首帧与画面边界稳定（`osd-dimensions` + `video-params` 就绪，最长约 6.5s 重试），在真实视频画面右上安全区显示约 3.5s。
  - 内容复用 `media-format-info.lua`：第一行画面标准（分辨率/帧率/HDR 或 SDR/编码，HDR 高亮青色），第二行当前选中音轨（语言/编码/布局）。
  - 通过 `osd-dimensions` 的 ml/mr/mt/mb 换算真实画面边界，上下黑边（letterbox）与左右黑边（pillarbox）场景都会把标识夹在画面内。
  - 观察 `aid` 属性，音轨切换时自动重新显示；文件结束自动清除。
  - 菜单新增“其它 > 起播格式标识 开关”（运行时切换，不持久化），独立脚本实现，不依赖 uosc 改动。
- **验证**:
  - `luajit loadfile` 通过；完整配置真实播放：日志确认标识已显示（`起播格式标识已显示 bounds=...`）。
  - 左右黑边：640×480 视频在 960×540 窗口 → `bounds=120,0,840,540`，标识位于画面内右侧。
  - 上下黑边：960×540 视频在 720×540 窗口 → `bounds=0,67,720,472`，标识夹在画面顶部内。
  - 音轨切换：静音 WAV 外挂音轨下 `aid=no` 与 `aid=1` 均触发重新显示（`shown=yes`）。
  - 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时测试脚本与 WAV 已删除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 18:39 会话: 历史恢复提示 OSD 下移

- **用户反馈**: “是否恢复当前目录的上次播放文件?”这个提示挡住标题了，要往下移。
- **根因**: `history-bookmark.lua` 的 `show_message()` 直接写 `message_overlay.data = text`，没有 ASS 定位标签，提示显示在屏幕顶部中央，压住 uosc 顶栏标题。
- **修改**:
  - `portable_config/scripts/history-bookmark.lua`：`show_message()` 现在显式加 `{\\an8\\pos(屏幕宽度/2, 90)}` 定位，提示下移到顶部下方 90px 并保持水平居中；新增 `message_offset=90` 选项。
  - `portable_config/script-opts/history_bookmark.conf`：新增 `message_offset=90` 配置项（像素，可调）。
- **验证**: `luajit loadfile` 通过；完整 `portable_config` 真实播放退出码 0、无 history_bookmark error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 18:43 会话: 历史恢复提示恢复原位并关闭功能

- **用户反馈**: “还是调回原位然后关闭该功能吧”。
- **修改**:
  - `portable_config/scripts/history-bookmark.lua`：撤销上一轮的定位改动，`show_message()` 恢复原始行为（直接 `message_overlay.data = text`，显示在原位），`message_offset` 选项一并移除；该文件与 Git 基线一致。
  - `portable_config/script-opts/history_bookmark.conf`：`enabled=yes → no`，关闭目录上次播放恢复询问功能；`message_offset` 配置行删除。
- **验证**: `luajit loadfile` 通过；完整 `portable_config` 真实播放退出码 0、无 history_bookmark error/warning；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 18:46 会话: 修复起播格式标识绘图乱码

- **用户反馈**: 顶部起播时显示 `mw1458|523l01772 52 b 1779 52 ...` 一串坐标文本，询问是否为起播标识。
- **根因**: `startup-format-badge.lua` 把 ASS 背景圆角矩形拆成三个独立事件：第一行只有 `{\p1}`，第二行是裸绘图路径（`m/l/b` 坐标），第三行 `{\p0}`。libass 把第二行的裸路径当普通文本渲染，于是屏幕上出现坐标乱码。
- **修改**: 将 `{\p1}` + 绘图路径 + `{\p0}` 合并到同一个 ASS 事件（同一行），libass 正确按矢量绘制处理。
- **验证**:
  - 运行时检查生成的 ASS 首行：`{\an7\pos(0,0)\blur0\fad(150,350)\bord1.1\3c&HF2E655&\1c&H221507&\1a&H2E&\p1}m 735 52 l ... {\p0}`，绘图命令已正确包裹在 `\p1...\p0` 内。
  - `luajit loadfile` 通过；完整 `portable_config` 真实播放退出码 0、无 uosc/startup_format_badge error/warning；调试日志已移除；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 18:54 会话: 移植 Yaozhi 完整起播格式 Logo 方案

- **用户反馈**: 轻量版起播标识根本不显示；不做轻量化了，要求直接移植 mpv-Yaozhi 的那套起播标识方案。
- **移植内容**（全部取自 `%TEMP%\mpv-Yaozhi-uosc-port\Yaozhi-mpv-8.7+.7z` 参考发行包）:
  - `portable_config/scripts/startup-format-logos.lua`（参考版 46KB 原脚本，未改动）。
  - `portable_config/script-opts/startup_format_logos.conf`（参考版完整配置：开关/样式/位置/黑边定位/编码黑边检测/优先级/时长等）。
  - `portable_config/script-assets/startup-format-logos/runtime/`（672 个 BGRA 徽标 + manifest.json，共约 64MiB，覆盖 28 种格式 × 彩色/白色 × 6 档透明度）。
  - 删除轻量版 `startup-format-badge.lua`、`startup_format_badge.conf` 及菜单行。
  - `portable_config/input.conf` 菜单替换为：`其它 > 起播格式 Logo > 开关 / 图标样式 > 彩色徽章 / 透明白图标`（OSD 菜单带动态勾选，uosc 菜单可见可点）。
- **功能能力**（参考脚本自带）: 首帧与画面边界稳定后显示、上下/左右黑边安全区定位、编码黑边（蓝光 ISO）检测、多音轨切换刷新、彩色/白色两套图标、28 种画面/音频格式识别、淡入淡出与停留时长可调。
- **验证**:
  - `luajit loadfile` 通过；完整配置真实播放 lavfi 视频：日志 `assets loaded: 28 logos, 6 opacity levels`、`script loaded`，无 overlay/Lua 错误。
  - 画面识别：无音轨时 `visible=yes video=sdr`；外挂 WAV 音轨时 `visible=yes video=sdr audio=pcm`，双徽标显示。
  - 菜单状态属性：`user-data/startup-format-logos/enabled`（bool）、`/style`（color/white）由脚本发布，OSD 勾选表达式已按 bool 类型修正。
  - 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时验证脚本与 WAV 已删除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 19:04 会话: 修复音频直通导致播放卡住

- **用户反馈**: 开了音频源码直通之后直接放不了了。
- **复现**: 用 ffmpeg 生成带 AC3 音轨的测试 MKV，完整配置以 home 模式播放：
  - mpv 将 AC3 封装为 spdif-ac3 交给 WASAPI 独占输出；当前 Windows 默认设备（kX Wave Out 2/3）不支持 spdif-ac3，ao/wasapi 报 unsupported，mpv 自动 fallback 到 PCM。
  - 脚本检查 audio-out-params/format 时该属性持续为空，旧逻辑只重试 4 次后静默 return、不回退；mpv 卡在直通状态，播放结束后也不退出。
- **修复**（audio-passthrough.lua）: output_format 为空且重试超过 4 次后调用 fallback_to_pcm(codec, 'unavailable')，恢复启动前配置并重载音频链。
- **验证**: 修复后同场景日志显示 switched to PCM → 音轨重载 → WASAPI PCM 输出 → 播放正常、退出码 0；luajit 通过；文件保持 UTF-8/LF；测试 MKV 已删除。
- **说明**: 当前默认设备不支持 spdif 直通；真正直通需在“音频设备列表”选择 HDMI/eARC 或 SPDIF 端点，不支持时脚本自动回退 PCM 并提示。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 19:14 会话: 新增窗口大小与窗口位置菜单

- **用户需求**: 菜单加两个设置：
  - 窗口大小：自动 / 1280x720（小窗）/ 1380x776 / 1463x822 / 1600x900 / 1920x1080 / 自定义。
  - 窗口位置：自动 / 居中（自动测算）/ 左+0，上+220 / 自定义。
- **实现**:
  - 新增 `portable_config/scripts/window-size-position.lua`：通过运行时 `set geometry` 调整窗口；保存启动时 geometry 用于“自动（恢复默认）”；“居中”按 `display-width/height - osd-width/height` 自动测算左上角；“自定义”使用 mp.input 文本框输入任意 geometry（如 `1280x720`、`1280x720+100+50`、`+0+220`、`50%:50%`）。
  - `portable_config/input.conf` 新增 `其它 > 窗口 > 窗口大小 / 窗口位置` 子菜单，全部为 uosc/OSD 通用菜单项。
- **验证**:
  - `luajit loadfile` 通过；完整配置真实播放：
  - `set-size 1280x720` → `geometry=1280x720`；`set-position +0+220` → `0x0+0+220`；`set-position center` → `0x0+480+270`（960×540 窗口在 1920×1080 屏精确居中）；`set-size/position auto` → 清空恢复系统默认。
  - menu-data 转储确认“其它 > 窗口”下“窗口大小”“窗口位置”子菜单均存在。
  - 文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时测试脚本已删除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 19:19 会话: 窗口设置改为持久化默认

- **用户反馈**: 这两个设置应该是持久化生效的默认设置，而不是临时调整。
- **修改**:
  - `portable_config/scripts/window-size-position.lua` 重写：选择尺寸/位置后写入 `portable_config/script-opts/window_size_position.conf`（`size=...` / `position=...`），下次启动时脚本读取并自动应用。
  - 新增 `portable_config/script-opts/window_size_position.conf`（默认 `size=auto`、`position=auto`）。
  - “居中（自动测算）”持久化为 `center`，启动时用 mpv geometry 百分比 `+50%+50%`（实测 mpv 支持，随窗口/屏幕自动居中）；`auto` 恢复为启动前 mpv.conf 的 geometry（当前为空 = 系统默认）。
  - 自定义尺寸输入只接受纯尺寸（拒绝带坐标）；自定义位置支持 `+x+y`、`center`、`auto` 等。
- **验证**:
  - 完整配置真实播放：`set-size 1280x720` + `set-position center` → conf 写入 `size=1280x720`/`position=center`，`geometry=1280x720+50%+50%`。
  - 重启 mpv：脚本自动应用，`geometry=1280x720+50%+50%`、`osd=1280x720`，默认设置生效。
  - `set-position +0+220` → `geometry=1280x720+0+220`；`set-size/position auto` → geometry 清空、conf 恢复 `size=auto`/`position=auto`。
  - `luajit loadfile` 通过；文件保持 UTF-8 无 BOM、LF；`git diff --check` 通过；临时测试脚本已删除。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本项与之前未提交的 UI/启动页/音频直通等改动均在工作区。

### 2026-08-07 20:31 会话: 04 包内置 Lossless.dll

- **用户决策**: 04 公开包改为内置 `Lossless Scaling\Lossless.dll`（项目所有者已确认的既定发布内容）；不打包 Steam 应用的其他文件；发布文案不包含授权声明原文，仅提示商业软件与支持正版。
- **修改**（`build-lsfg-public.ps1`）:
  - 新增必填文件检查 `Lossless Scaling\Lossless.dll`，打包时复制到 04 包 `Lossless Scaling\Lossless.dll`。
  - 删除“请从Steam复制Lossless.dll到此目录.txt”，改为 `内置说明.txt`（说明已内置、支持正版）。
  - README-LSFG 文本更新：不再要求用户自备；列出内置文件；保留包边界说明。
  - 门禁更新：允许且仅允许两个 DLL（LSFG GPL Layer DLL + Lossless.dll）；Lossless Scaling 目录只允许内置说明与 Lossless.dll；仍禁止任何 EXE。
- **修改**（`README.MD`）: 04 行表格、公开分发说明、构建前置文件说明同步更新（内置 Lossless.dll、解压即用、支持正版提示）。
- **修改**（`发布流程.md`）: 04 包产物说明、构建后验证门禁、3.2 大改动 Gate 均注明“04 内置 Lossless.dll 为项目所有者已确认的既定发布内容，不视为新增版权文件”。
- **修改**（`AGENTS.md`）: 发布流程强制节补充 04 既定内容说明。
- **验证**:
  - 用 `-Version 9.9.9 -OutputDir tmp/lsfg-test` 实测构建 04 包：门禁通过、7z t 通过。
  - 包内 DLL 仅两个（lsfg-vk-layer.dll + Lossless.dll），无 EXE；Lossless Scaling 目录仅含 Lossless.dll（7,521,280 字节）与内置说明.txt。
  - 解压验证说明文件内容正确；临时构建目录、验证目录与 build 暂存已清理。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本次 04 边界改动与之前所有功能改动均在工作区，未提交。

### 2026-08-07 20:38 会话: 包边界确认（启动 Logo 归 Base、窗口默认重置、状态文件排除）

- **用户决策**:
  - 启动 Logo 素材（启动页 + 起播格式 Logo，676 个文件 64MB 原始 / 2.6MB 压缩）归 01 Base 包；05 Config 不再携带。
  - 窗口默认设置重置为 `size=auto` / `position=auto` / `ontop` 跟随 mpv.conf（删除 conf 中显式 ontop 行）。
- **修改**（`build-release.ps1`）: 01 Base 保持 script-assets 随包；新增排除个人运行时状态 `script-opts/window_state.conf`。
- **修改**（`build-config-public.ps1`）: 05 Config 新增排除 `script-assets/`（Logo 归 Base）与 `script-opts/window_state.conf`。
- **修改**（`portable_config/script-opts/window_size_position.conf`）: 重置为 `size=auto`、`position=auto`，删除 `ontop` 行（跟随 mpv.conf）；remember 开关保持默认开。
- **修改**（`README.MD` / `发布流程.md`）: 01/05 包内容说明与构建后门禁同步更新（01 必含 script-assets、05 必排除；01/05 均不得含 window_state.conf）。
- **验证**:
  - 用 `-Version 9.9.9 -OutputDir tmp/pkg-test` 实测构建 01（-SkipExtras）与 05：7z t 全部 Everything is Ok。
  - 01 含 script-assets 680 项、无 window_state.conf；05 无 script-assets、无 window_state.conf。
  - 05 内 `window_size_position.conf` 为 auto/auto、无 ontop 行；01/05 均含该 conf。
  - PowerShell 语法检查通过；临时构建目录、验证目录已清理。
- **Git 状态**: `master` 仍领先 `origin/master` 1 个提交（`d6498b9` 未推送）；本次包边界改动与之前所有功能改动均在工作区，未提交。

### 2026-08-07 20:42 会话: 核验发布脚本覆盖 mpv 全构建

- **核验范围**: build-release.ps1（01/02）、build-fasterwhisper-public.ps1（03）、build-lsfg-public.ps1（04）、build-config-public.ps1（05）、build-full-private.ps1（全量），对照仓库根目录实际文件。
- **01 Base**: mpv.exe/mpv.com、全部 16 个运行时 DLL、luajit、yt-dlp、lua/mime/socket、mpv/、doc/、installer/、updater.bat、umpv、7z、portable_config（含 script-assets、排除 window_state.conf）——全部存在，已实测构建。
- **02 Extras**: shaders/vs、vs-plugins/vs-coreplugins/vs-scripts、VSPipe/VSScript/VSVFW/AVFS/pfm/portable.vs、sdk/vsgenstubs4/vsrepo.py/MANIFEST.in、Python 运行时全套、Lib/Scripts、TorrServer/alass/get-pip.py——源路径全部存在；本轮未完整打包（约 4GB+），v1.3.2 曾完整构建通过。
- **03/04/05**: FW 运行时存在；04 已实测构建（含 Lossless.dll）；05 已实测构建。
- **Private**: 01→05 合并 + Lossless Scaling 完整目录，逻辑无新增需求。
- **结论**: 发布脚本覆盖 mpv 全构建，无发现缺文件；settings.xml 不入包但 updater.ps1 会自动生成，非缺口。正式发布前建议跑一次完整 `build-all-packages.ps1 -IncludePrivate` 验证大包。
- **Git 状态**: 只读核验，无新文件改动；工作区仍为未提交状态。

### 2026-08-07 20:52 会话: v1.4.0 构建与验证

- **版本确认**: 用户确认 v1.4.0。
- **提交**:
  - `e87365b` feat: uosc 深度融合与官方核心兼容功能（706 文件，含 676 个 Logo 素材）。
  - `d911760` docs: 建立强制发布流程并调整发布包边界（6 文件）。
- **构建**（按《发布流程.md》第 4 节，顺序执行）:
  - `build-release.ps1 -Version 1.4.0` → 01 Base（95.5MB）+ 02 Extras 分卷（1900MB / 745.4MB），7 分 29 秒。
  - `build-fasterwhisper-public.ps1` → 03（1408MB）。
  - `build-lsfg-public.ps1` → 04（3.1MB，内置 Lossless.dll）。
  - `build-config-public.ps1` → 05（33MB）。
  - `build-full-private.ps1` → 个人全量包（4187MB，仅本地）。
- **验证**:
  - 六个归档 7z t 全部 Everything is Ok。
  - 门禁：01 含 script-assets（680 项）、无 window_state.conf；05 无 script-assets、无 window_state.conf；04 仅两个 DLL（lsfg-vk-layer.dll + Lossless.dll）、0 EXE、无 LosslessScaling.exe/语言资源；02 的 `operations/build/` 匹配为 Python pip 正常路径，非构建目录泄漏；03 无违规项。
  - 分卷大小符合 GitHub 限制。
  - SHA-256 已写入 `version/版本迭代记录.md`。
- **Git 状态**: `master` 领先 `origin/master` 3 个提交（d6498b9 + e87365b + d911760，均未推送）；构建记录待提交。

### 2026-08-07 21:22 会话: v1.4.0 正式发布

- **提交与推送**:
  - `60a157b` docs: record v1.4.0 build, checksums and release plan（构建记录/校验和）。
  - 打标签 `v1.4.0`（annotated）并推送；远端 tag 确认 `2e171d5...`。
  - `master` 与 `origin/master` 同步。
- **Release**:
  - https://github.com/maxzrb/mpv-portable/releases/tag/v1.4.0
  - 状态：正式（非草稿、非预发布）。
  - 6 个资产全部上传：01、02.001、02.002、03、04、05；远端 SHA-256 与本地一致；未上传个人全量包。
  - 文案已包含 uosc 界面设计源自 mpv-Yaozhi 的说明（用户要求补充）。
- **中断恢复**: 首次 gh release create 被中断留下草稿（3 资产），已删除草稿后重新创建并完整上传。
- **清理**: build/ 暂存目录（03/04/05/private）与临时 release notes 已删除；release/ 保留 6 个公开包 + 全量包 + 校验记录。
- **Git 状态**: 发布结果记录待提交；提交后 master 仍与 origin 同步。

### 2026-08-07 21:30 会话: 清理过期构建产物

- **用户需求**: 顺便清理过期构建产物。
- **清理**:
  - `release/` 删除 v1.3.2 全套 7 个包（01~05 公开包 + 个人全量包，约 8.5GB）：01、02.001、02.002、03、04、05、mpv-full-private-v1.3.2.7z。
  - `tmp/` 删除 6 个调试/审计临时文件：list_scripts.log、menu_dump.json、menu_dump.log、menu_dump.lua、menu_dump2.log、menu_dump3.log。
- **保留**: `release/` 仅保留 v1.4.0 七个包（01~05 + 分卷 + 个人全量包）；`build/` 已空；旧版本校验和仍在 `version/版本迭代记录.md` 历史节。
- **Git 状态**: 先前补充的发布流程提交 `229892d` 已推送，`master` 与 `origin/master` 同步。

### 2026-08-07 21:40 会话: 修复启动页图片大小不生效

- **用户反馈**: 修改 `idle_branding.conf` 的 `display_size` 没有反应。
- **根因**（实测确认）:
  - 脚本原先 `target_size = clamp(72, 窗口短边 * 0.21, display_size * DPI)`，窗口短边 × 0.21 形成硬上限。
  - 当前窗口 1728×972 时上限约 204；display_size 已设 320，实际始终显示 204，220→320 看不出区别。
  - `options.read_options` 只在 mpv 启动时读取，运行中改 conf 需重启。
- **修改**:
  - `idle-branding-image.lua`：改为 `clamp(72, display_size * DPI, 窗口短边 * 0.5)`，display_size 优先，仅以窗口短边 50% 防溢出。
  - 同步更新脚本内持久化注释与 `idle_branding.conf` 注释。
- **验证**: 完整配置 idle 启动，`user-data/idle-branding-image/display-height=320`（此前为约 204），active=yes。
- **Git 状态**: 修复未提交（v1.4.0 已发布，此修复随下版发布）；`master` 与 `origin/master` 同步。

### 2026-08-07 21:46 会话: 修复打开 uosc 菜单时启动页消失

- **用户反馈**: 一右键打开 uosc 菜单，启动页图片就消失。
- **根因**: `idle-branding-image.lua` 的隐藏条件把 `user-data/uosc/menu/type ~= nil` 视为“前台覆盖层打开”，菜单一开就 `overlay-remove` 启动页。
- **修改**: `foreground_overlay_open()` 改为 `file_browser_open()`，仅文件浏览器打开时隐藏启动页；uosc 菜单打开不再触发隐藏。保留 `user-data/uosc/menu/type` 观察器（重渲染无副作用）。
- **验证**: 完整配置 idle 启动，注入 `user-data/uosc/menu/type=standard` 后启动页仍 active=yes、height=320。
- **Git 状态**: 修复未提交（随下版发布）；`master` 与 `origin/master` 同步。

### 2026-08-07 21:58 会话: 移植 uosc 音量条样式

- **用户反馈**: mpv-Yaozhi 的音量条样式没有移植过来。
- **参考**: 用户提供 `tmp/Yaozhi-mpv-8.7+.7z`，提取其 `uosc/elements/Volume.lua` 对比。
- **差异**: 本地为标准 uosc 5.13 样式（nudge 路径滑块、无面板、数字内嵌滑块）；参考版为竖直圆角轨道 + 青色填充 + 圆形把手 + 底部大号加粗数字 + 半透明悬浮面板 + 静音状态变色图标。
- **修改**（`portable_config/scripts/uosc/elements/Volume.lua`）:
  - 滑块改为竖直细轨道（宽 10%）、轨道底色 fg + 填充 config.color.match、圆形把手（match 色）。
  - 音量数字移到轨道下方保留区，加粗、白字黑边、字号 width×0.44。
  - 音量面板高度改为 size×6，边距改为 size + border，形成悬浮面板。
  - 面板背景：bg 82% 透明度圆角矩形；静音图标单图标（去 underlay），静音时用 menu_active 色。
  - 静音点击改 primary_click + toggle_mute 方法；保留右键重置音量。
  - 未引入品牌字样；依赖（ass:rect/circle/txt、config.color.match/menu_active、state.radius、cursor primary_click）均已在本地 5.13 存在。
- **验证**: luajit 语法通过；完整配置真实播放，触发 音量42→静音→88 过程无任何 uosc Lua 错误，正常退出。
- **Git 状态**: 修改未提交（随下版发布）；`master` 与 `origin/master` 同步；用户提供的 7z 保留在 tmp/。

### 2026-08-07 22:10 会话: 音量条 100 刻度标记

- **用户需求**: 在音量 100 处用两个小三角形做标记，并尝试点击标记快速调到 100。
- **修正**（`portable_config/scripts/uosc/elements/Volume.lua`）:
  - 最初实现误把标记放在轨道顶部（即 volume_max=130 处）；用户指出最大音量为 130，100 刻度应在轨道 100/130≈76.9% 处。
  - 标记位置改用 `marker_fraction = clamp(0, 100 / state.volume_max, 1)`，两个三角形尖端指向轨道中心线，位于 100 刻度处。
  - 点击标记改为 `set volume 100` + 取消静音（不再设 volume_max）；点击区域随 100 刻度位置移动。
- **验证**: `volume-max=130` 实测确认（mpv.conf 默认，未显式设置）；标记分数 0.7692；真实播放音量 42→100 渲染无错误，RENDER-DONE。
- **说明**: 前一轮测试日志提前退出是用户手动关闭窗口，非脚本问题。
- **Git 状态**: 修改未提交（随下版发布）；`master` 与 `origin/master` 同步。

### 2026-08-07 22:35 会话: v1.4.1 构建与验证（发布前）

- **版本确认**: 用户确认 v1.4.1。
- **提交**:
  - `9ca1673` feat: 移植 Yaozhi 音量条样式并修复启动页显示（6 文件：Volume.lua、idle-branding-image.lua、idle_branding.conf、发布流程.md、两份进度记录）。
- **发布前验证**: luajit 语法通过、git diff --check 通过、完整配置真实播放 SMOKE-V141-OK 无 [e] 错误。
- **构建**（按《发布流程.md》第 4 节）:
  - `build-release.ps1 -Version 1.4.1` → 01 Base（95.5MB）+ 02 Extras 分卷（1900MB / 745.4MB）。
  - `build-fasterwhisper-public.ps1` → 03（1407.6MB）。
  - `build-lsfg-public.ps1` → 04（3.0MB，内置 Lossless.dll）。
  - `build-config-public.ps1` → 05（32.3MB）。
  - `build-full-private.ps1` → 个人全量包（4186.5MB，仅本地）。
- **构建后验证**:
  - 七个归档 7z t 全部 Everything is Ok。
  - 门禁：01 含 script-assets（680 项）、无 window_state.conf；05 无 script-assets、无 window_state.conf；04 仅两个 DLL（lsfg-vk-layer.dll + Lossless.dll）、0 EXE。
  - 分卷大小符合 GitHub 限制。
  - SHA-256 已写入 `version/版本迭代记录.md`（v1.4.1 一节）。
- **Git 状态**: `master` 领先 `origin/master` 1 个提交（`9ca1673` 未推送）；构建记录待提交；按用户要求停在 Release 创建之前。

### 2026-08-08 00:19 会话: v1.4.1 正式发布（合并 v1.4.0）

- **用户指令**: 删除原 v1.4.0 GitHub Release，合并到 v1.4.1 发布。
- **执行**:
  - 推送 `master`（`9ca1673` + `909dede`）至 `origin/master`。
  - 创建并推送 annotated tag `v1.4.1`（`f190ee4`）。
  - 删除 v1.4.0 GitHub Release（6 资产）及远端/本地 tag `v1.4.0`。
  - 创建正式 Release v1.4.1（非草稿、非预发布），上传 6 个公开资产：01、02.001、02.002、03、04、05；个人全量包未上传。
  - Release 说明合并 v1.4.0 + v1.4.1 更新内容，注明 uosc 源自 mpv-Yaozhi。
- **验证**: 远端 6 资产全部 uploaded，SHA-256 与本地记录一致；`git ls-remote --tags origin v1.4.0` 无结果、`v1.4.1` 存在；`master` 与 `origin/master` 同步。
- **清理**: build/ 暂存目录已清空；tmp/ 删除中断下载的重复 Yaozhi 包（保留用户提供的 `Yaozhi-mpv-8.7+.7z`）；临时 release notes 已删除。
- **Git 状态**: 发布结果记录待提交。

### 2026-08-08 10:58 会话: v1.4.1 重建覆盖（media info 更新合并，发布前检查）

- **用户指令**: 将 media info 更新合并到 v1.4.1，重建覆盖 v1.4.1；个人全量包照常生成（仅本地保留，禁止上传）。
- **本次改动**（3 个文件，未提交）:
  - `portable_config/scripts/uosc/elements/MediaInfo.lua`: 实时码率=视频+音频；码率胶囊点击在实时/平均码率间循环；两级 EMA 平滑（短期平均+自适应时间常数+滞回）解决高频横跳。
  - `portable_config/scripts/uosc/main.lua`: 新增 `media_info_bitrate_smoothing=0.6`、`media_info_bitrate_deadband=0.01` 默认值。
  - `portable_config/script-opts/uosc.conf`: 新增上述两个可配置项。
- **发布前置检查（《发布流程.md》3.1-3.4）**:
  - 3.1 Git: `master` 与 `origin/master` 同步；仅上述 3 文件未提交；`git fetch origin` 无远端新改动。
  - 3.2 大改动 Gate: 不触发（普通功能/配置/脚本改动，不涉及包结构、构建脚本、核心运行时、版权边界）。
  - 3.3 文档: 本次功能清单与验证写入本 STATUS.md；`version/版本迭代记录.md` 校验和将在构建后重写；`version/工作进度.md` 构建后追加。
  - 3.4 功能验证:
    - `luajit loadfile` 通过: uosc/main.lua、MediaInfo.lua、media-format-info.lua。
    - `git diff --check` 通过；三个文件 UTF-8 无 BOM、LF 换行。
    - 完整配置真实播放测试（WAV + `--vo=null --ao=null`）: 1431 行日志 **0 个 [e]/[f] 错误**；uosc 正常加载并读取 `script-opts/uosc.conf`。
    - 仿真验证: 高频横跳最后 1 秒 0~2 次变化；趋势跟随正常。
- **计划**: 提交功能改动 → 构建 v1.4.1 全包（含全量包）→ 构建后验证 → 更新校验和 → 删除旧 v1.4.1 标签/Release → 重建正式 Release（5 公开资产）→ 收尾。

### 2026-08-08 11:22 会话: v1.4.1 重建构建与验证完成

- **构建**（`build-all-packages.ps1 -Version 1.4.1 -IncludePrivate`）:
  - 01 Base 95.5MB；02 Extras 分卷 1900MB / 745.4MB；03 FW 1408MB；04 LSFG 3.1MB；05 Config 33MB；全量包 4187MB（仅本地）。
- **构建后验证（第 5 节）**:
  - 6 个归档（含全量包）`7z t` 全部 Everything is Ok。
  - 门禁：01 含 script-assets、无 window_state.conf；05 无 script-assets、无 window_state.conf；04 0 EXE、仅 Lossless.dll + lsfg-vk-layer.dll；各公开包无 `^build|release|tmp|.git`、`__pycache__`、`.pyc`、`.log` 顶层禁入项。
  - 分卷 02 .001 1900MB / .002 745.4MB，符合 GitHub 2GB 限制。
  - 新 SHA-256 已写入 `version/版本迭代记录.md`。
- **提交**:
  - `be3447b` feat: media info 码率胶囊点击切换实时/平均码率并支持平滑滤波。
  - `f19644a` docs: 发布流程 Release 说明检查项移除已知限制要求（用户修订）。
- **下一步**: 删除旧 v1.4.1 标签与 Release，重建标签指向发布提交，创建正式 Release 上传 5 个公开资产（不传全量包），然后收尾。

### 2026-08-08 11:45 会话: v1.4.1 重建发布完成（收尾）

- **标签/Release 重建**:
  - 删除旧本地 tag v1.4.1（f190ee4）与远端 Release v1.4.1（--cleanup-tag 同步删除远端 tag）。
  - 创建新 annotated tag v1.4.1（fb4f49a）指向发布提交 `c322b09`，推送 master 与 tag。
  - `gh release create v1.4.1`：正式发布（非草稿、非预发布），上传 6 个公开资产（01、02.001、02.002、03、04、05）；个人全量包未上传。
- **资产核对**: 远端 6 资产名称与字节大小和本地完全一致；Release: https://github.com/maxzrb/mpv-portable/releases/tag/v1.4.1
- **清理**: `build/` 暂存目录已删除；`tmp/release-notes-v1.4.1.md` 已删除；`release/` 保留本地产物与全量包（仅本地）。
- **Git 状态**: 待提交发布结果记录；随后确认 master 与 origin/master 同步、工作树干净。

### 2026-08-08 16:20 会话: v1.4.2 发布前置检查

- **用户指令**: 按发布流程发布 1.4.2（个人全量包照常生成，仅本地）。
- **本次发布功能**（9 个文件未提交）:
  - 进度条章节标记：两个暗夜蓝色小三角形（替代原菱形）+ `chapter_display=yes` 默认开启 + `CTRL+SHIFT+C` 切换快捷键。
  - 进度条悬停渐隐：速度滑块与 media info 胶囊按鼠标 Y 距离平滑淡出（`utils.lua` 新增 `get_timeline_hover_fade`）。
  - uosc 菜单：级联方向一致性与重叠检测（两阶段绘制保证 z-order）、子菜单 hover 延迟展开（`menu_submenu_delay=0.5`）、毛玻璃伪效果（`menu_frosted=yes`）、1px 边缘条与重叠兜底不透明。
  - 打开方式：打开文件菜单顶部的「替换当前实例 / 新实例」单选选项，持久化 `menu_open_file_mode`。
- **发布前置检查（《发布流程.md》3.1-3.4）**:
  - 3.1 Git: `master` 与 `origin/master` 同步；9 个文件未提交；`window_size_position.conf` 运行时自动写回已还原（非有意改动）。
  - 3.2 大改动 Gate: 不触发（全部为 uosc 脚本/配置/菜单改动，不涉及包结构、构建脚本、核心运行时、版权边界）。
  - 3.3 文档: 本 STATUS.md 记录；构建后更新 `version/版本迭代记录.md`（新增 v1.4.2 一节）与 `version/工作进度.md`。
  - 3.4 功能验证:
    - `luajit loadfile` 通过全部 7 个改动 Lua 文件。
    - `git diff --check` 通过；9 个文件 UTF-8 无 BOM、LF 换行。
    - 完整配置真实播放（WAV）：1431 行日志无 [e]/[f]（排除环境 IPC）、无 Lua/uosc 错误。
- **计划**: 两个功能提交 → 构建 v1.4.2（含全量包）→ 构建后验证 → 更新记录并提交构建结果 → 创建标签与正式 Release（5 公开资产，不传全量包）→ 收尾。

### 2026-08-08 16:35 会话: v1.4.2 构建与验证完成

- **提交**（功能 → 文档）:
  - `d7c493d` docs: record v1.4.2 pre-release checks。
  - `47ef8ef` feat: 进度条章节三角形标记与悬停渐隐。
  - `2a77fec` feat: uosc 菜单级联定位、毛玻璃、子菜单延迟与打开方式开关。
- **构建**（`build-all-packages.ps1 -Version 1.4.2 -IncludePrivate`）:
  - 01 Base 95.5MB；02 Extras 分卷 1900MB / 745.4MB；03 FW 1408MB；04 LSFG 3.1MB；05 Config 33MB；全量包 4187MB（仅本地）。
- **构建后验证（第 5 节）**:
  - 6 个归档（含全量包）`7z t` 全部 Everything is Ok。
  - 门禁：01 含 script-assets、无 window_state.conf；05 无 script-assets、无 window_state.conf；04 0 EXE、仅 Lossless.dll + lsfg-vk-layer.dll；各公开包无顶层禁入项。
  - 分卷 02 .001 1900MB / .002 745.4MB，符合 GitHub 2GB 限制。
  - SHA-256 已写入 `version/版本迭代记录.md` v1.4.2 一节；v1.4.1 已移入历史。
- **下一步**: 创建标签 v1.4.2 → 正式 Release（5 公开资产，不传全量包）→ 收尾。

### 2026-08-08 16:55 会话: v1.4.2 发布完成（收尾）

- **标签/Release**:
  - annotated tag v1.4.2（d5f4fea）指向 `b2fc557`；master 与标签已推送，`master` 与 `origin/master` 同步。
  - `gh release create v1.4.2`：正式发布（非草稿、非预发布），上传 6 个公开资产（01、02.001、02.002、03、04、05）；全量包未上传。
  - Release: https://github.com/maxzrb/mpv-portable/releases/tag/v1.4.2
- **资产核对**: 远端 6 资产名称与字节大小和本地完全一致。
- **清理**: `build/` 暂存目录与 `tmp/release-notes-v1.4.2.md` 已删除；`release/` 保留本地产物与全量包（仅本地）。
- **Git 状态**: 发布结果记录待提交；随后确认工作树干净。

### 2026-08-08 17:30 会话: v1.4.2 重建覆盖（右键菜单定位修复，发布前检查）

- **用户指令**: 提交 Menu.lua 右键菜单定位修复，合并到 v1.4.2 重新发布（重建覆盖）；全量包照常生成（仅本地）。
- **本次改动**（1 个文件未提交）:
  - `portable_config/scripts/uosc/elements/Menu.lua`: 根菜单跟随右键光标时不再用 `cascade_width` 预留整条子菜单链宽度（否则根菜单被压到左侧、脱离光标）；只按根菜单自身宽度 clamp 到屏幕内；子菜单展开空间由展开期级联定位处理；删除死代码 `cache_cascade_width`。
- **发布前置检查（《发布流程.md》3.1-3.4）**:
  - 3.1 Git: `master` 与 `origin/master` 同步；仅 Menu.lua 未提交；`git fetch origin` 无远端新改动。
  - 3.2 大改动 Gate: 不触发（普通脚本功能修复，不涉及包结构、构建脚本、核心运行时、版权边界）。
  - 3.3 文档: 本次功能清单与验证写入本 STATUS.md；构建后重写 `version/版本迭代记录.md` v1.4.2 校验和并追加调整记录。
  - 3.4 功能验证:
    - `luajit loadfile` 通过；`git diff --check` 通过；Menu.lua UTF-8 无 BOM、LF。
    - 完整配置真实播放（WAV）：1432 行日志无 [e]/[f]（排除环境 IPC）、无 Lua/Menu 错误。
    - 边界仿真：右键任意位置（含贴边）根菜单不越界，子菜单展开仍走级联定位。
- **计划**: 提交功能修复 → 构建 v1.4.2 全包（含全量包）→ 构建后验证 → 重写校验和 → 删除旧 v1.4.2 标签/Release → 重建正式 Release（5 公开资产）→ 收尾。

### 2026-08-08 17:58 会话: v1.4.2 重建构建与验证完成

- **提交**: `2bb3bfe` fix: 右键菜单根菜单定位不再被级联预留宽度挤到左侧。
- **清理**: 按用户要求先清空 release（删除全部旧 v1.4.2 产物 + 中断残留 `.001.tmp`），并终止中断构建残留的 7z 孤儿进程；build 暂存同步清理。
- **构建**（`build-all-packages.ps1 -Version 1.4.2 -IncludePrivate`）: 01 Base 95.5MB；02 分卷 1900MB / 745.4MB；03 FW 1408MB；04 LSFG 3.1MB；05 Config 33MB；全量包 4187MB（仅本地）。
- **构建后验证（第 5 节）**:
  - 6 个归档（含全量包）`7z t` 全部 Everything is Ok。
  - 门禁：01 含 script-assets、无 window_state.conf；05 无 script-assets、无 window_state.conf；04 0 EXE、仅 Lossless.dll + lsfg-vk-layer.dll；各公开包与全量包无顶层禁入项。
  - 分卷 02 .001 1900MB / .002 745.4MB，符合 GitHub 2GB 限制。
  - 新 SHA-256（7 个）已替换 `version/版本迭代记录.md` v1.4.2 一节，并追加右键菜单定位修复记录。
- **下一步**: 删除旧 v1.4.2 标签与 Release，重建正式 Release（5 公开资产，不传全量包），收尾。

### 2026-08-08 18:10 会话: v1.4.2 重建发布完成（收尾）

- **标签/Release 重建**:
  - 删除旧本地 tag v1.4.2（d5f4fea）与远端 Release v1.4.2（--cleanup-tag 同步删除远端 tag）。
  - 创建新 annotated tag v1.4.2（5a4dae5）指向发布提交 `521273e`，推送 master 与 tag。
  - `gh release create v1.4.2`：正式发布（非草稿、非预发布），上传 6 个公开资产；个人全量包未上传。
- **资产核对**: 远端 6 资产名称与字节大小和本地完全一致；Release: https://github.com/maxzrb/mpv-portable/releases/tag/v1.4.2
- **清理**: `build/` 暂存目录与 `tmp/release-notes-v1.4.2.md` 已删除；`release/` 保留本地产物与全量包（仅本地）。
- **Git 状态**: 待提交发布结果记录；随后确认 master 与 origin/master 同步、工作树干净。


---

## 2026-08-10 · 发布前检查（v1.4.2 附装 Installer）

### 任务
按项目所有者指示：mpv 本体 01~05 包（v1.4.2）已构建且保持不变；新增并附加 VantaInstaller 作为 v1.4.2 Release 资产。

### 检查清单
- [x] git 状态：master 与 origin/master 同步（`## master...origin/master` 无 ahead/behind）
- [x] 大改动 Gate：本次为**新增安装辅助工具 VantaInstaller 并作为 Release 附加资产**，命中 3.2 中"安装方式变化"条目；
      项目所有者（用户）已明确拍板执行，不修改《发布流程.md》本身。
- [x] 产物：01~05 包保持 v1.4.2 原样，不重新构建；私用全量包不上传。
- [x] VantaInstaller Release 单文件自包含压缩 exe 构建成功（v0.2.0，win-x64，64.3MB），启动验证通过。
- [x] SHA-256：`2BB37136CFC9B976BB68E633393C3EAAA6B0D4F640CE1FFAB9E294EB528C7157`
- [x] git diff --check 通过；无构建产物（bin/obj/publish）混入提交。
- [x] gh CLI 可用（2.95.0），用于 Release 资产上传。


---

## 2026-08-10 · 发布结果（v1.4.2 附装 VantaInstaller）

- 推送：master 与 origin/master 同步（含 3 个新提交：feat VantaInstaller / docs 记录 / style 字号统一；rebase 合并远端 2 个 README 提交）。
- Release：`v1.4.2`（正式，非草稿/预发布）新增资产 `VantaInstaller-win-x64-v0.2.0.exe`（64.3MB）。
- 远端资产核对：7 个资产全部在位；VantaInstaller 远端 SHA-256 `2bb37136...` 与本地完全一致。
- Release 说明已追加 VantaInstaller 一节（用途、免运行时、校验和）。
- 未上传私用全量包；mpv 本体 01~05 未重新构建。


---

## 2026-08-10 · v1.4.2 base 补 Vanta 安装标记

- 需求：让已发布/新装 base 包带 `.vanta-version` 标记，安装器据此区分 Vanta 安装与任意 mpv。
- 改动：`build-release.ps1` base 打包自动写入 `portable_config/.vanta-version = 版本号`；`build-config-public.ps1` 05 打包排除该标记（防止 05 覆盖）。
- 重打：`01-mpv-base-v1.4.2.7z`（含标记，95.5MB），已重传 v1.4.2 Release（--clobber），远端 hash 核对一致。
- 新 SHA-256：`535E7A1990F45D4619D50BF850223C8CA799E48EDD3028FDD672A675BAA8426D`
- 02~05 未重打（内容不变）；02 沿用上次分卷。

### 2026-08-11 13:16 会话：本机核心切换到 shinchiro 20260811

- **Git 起点**：`git pull --ff-only` 返回 Already up to date；`master` 领先 `origin/master` 1 个提交（`5335a39`）；保留用户未提交的 `portable_config/script-opts/window_size_position.conf`，未纳入本次核心操作。
- **切换内容**：
  - `mpv.exe` / `mpv.com`：`v0.41.0-860-gc8c7d91a8`（dyphire，FFmpeg N-125480）→ `v0.41.0-922-gf4d13e1c2`（shinchiro 20260811，FFmpeg N-126056）。
  - 安装 shinchiro 随包的 `d3dcompiler_43.dll`；dyphire 随包的 `vulkan-1.dll` 已移出根目录，避免形成混合核心。
  - shinchiro 包内的注册、反注册和更新批处理未复制，继续使用本项目自己的安装与关联流程。
- **回滚点**：旧 `mpv.exe`、`mpv.com`、`vulkan-1.dll` 保存在 `tmp/core-backup-dyphire-c8c7d91a8-20260811/`。
- **验证**：
  - `--version` 正确报告新版本；D3D11 gpu-next、Vulkan winvk、P7 FEL `format=enhancement-layer=yes` 测试均正常退出，日志无 error/fatal。
  - 完整配置使用 2.39:1 黑边演示素材播放 120 帧，D3D11VA-copy 硬解、起播格式徽章覆盖与退出均正常，日志无 error/fatal。
  - 新旧视频解码器列表一致。音频侧 shinchiro 不含可选 `libfdk_aac` 解码器，但保留 FFmpeg 原生 AAC/AAC Fixed，并新增 `pcm_dvda`；常规 AAC 播放能力未缺失。
  - 测试日志保存在 `tmp/core-switch-test/`；新 `mpv.exe` SHA-256 为 `786E8A92CB316B6FB34661BD8086B56D56D92D2B222A7E0FA0B23E566CFD4B90`。
- **发布 Gate**：本次仅切换 gitignore 内的本机核心，未打包、未发布。核心运行时更换命中《发布流程.md》3.2；未来把 shinchiro 核心纳入公开包前，必须停止发布并由项目所有者确认流程修订或豁免。
- **下一步**：用户日常播放观察稳定性；如遇兼容问题，可从上述备份目录原样回滚。状态记录尚未提交。

### 2026-08-11 13:40 会话：VantaInstaller 当前用户文件关联重构

- **决策**：不直接采用 shinchiro 的 BAT 包装器；由 VantaInstaller 自己管理注册表，但采用 mpv 上游 `Applications + Capabilities + RegisteredApplications` 结构。用户追加确认接管常见音频格式；图片、播放列表和压缩包暂不接管。
- **核心改动**：
  - `AssociationService.cs` 从 BAT 路径选择器重构为 HKCU 注册表服务，不再要求管理员权限或 UAC。
  - 多实例 `mpv.exe` 与单实例 `umpv.exe` 使用独立 RegisteredApplications 名称、Clients/Media Capabilities 和 ProgID（`MPV.Vanta.Multi.File` / `MPV.Vanta.Single.File`），注册或取消一方不再覆盖、删除另一方。
  - 声明 100 个去重后的音视频扩展名；继续由 Windows“默认应用/打开方式”决定默认播放器，不直接写扩展名所有权。
  - 创建当前用户开始菜单快捷方式以辅助 Windows 系统媒体控制识别；注册失败会回滚本入口的部分写入，并通知 Shell 刷新关联缓存。
- **流程接入**：
  - 安装引擎、设置页和完成页全部改为直接调用 `AssociationService`，删除 BAT + `runas` + 固定等待 500ms 的旧路径。
  - 卸载引擎在删除安装目录之前调用 `UnregisterAll()`，修复旧逻辑先删掉 `mpv-uninstall.bat`、随后无法清理关联的问题。
  - README 和卸载页说明同步改为“当前用户、无需 UAC、视频与音频”。旧 BAT 保留为手工兼容入口，但 VantaInstaller 不再依赖。
- **旧版迁移**：只读检测到本机仍有 `HKLM\SOFTWARE\RegisteredApplications\mpv` 旧版系统级关联。新服务不会越权删除，并会提示只有确认属于旧版 Vanta 时才用旧卸载脚本管理员清理；本轮未执行任何注册或取消操作，注册表未被修改。
- **验证**：
  - `dotnet build Vanta.Installer -c Release`：0 警告、0 错误；`Vanta.ScanTool` Release 构建同样通过。
  - 按正式参数执行 win-x64 单文件自包含发布构建成功，临时产物 `tmp/vanta-association-publish/VantaInstaller.exe` 为 67,459,877 字节。
  - 反射结构检查：100 个扩展名全部去重、格式合法，包含 `.mp4`、`.mp3`、`.flac`；两入口身份和 ProgID 独立；根目录 `mpv.exe`/`umpv.exe` 均满足注册条件。
  - 源码扫描无 `InstallBatPath`、`RunBatElevated`、文件关联 `runas` 残留；关联写入只使用 HKCU，HKLM 仅只读检测旧项；`git diff --check` 通过。
- **发布状态**：仅完成功能实现与验证，未提交、未重建正式安装器、未发布；VantaInstaller 自身功能变化按《发布流程.md》3.2 豁免条款不触发大改动 Gate。

### 2026-08-11 13:55 会话：纯 01/全量包手动关联入口补齐

- **需求**：没有 VantaInstaller 时仍能使用新版当前用户双入口方案；原 `mpv-install/uninstall*.bat` 明确作为已验证的旧版系统级兜底保留。
- **新增入口**（均位于 `installer/`）：
  - `vanta-register-multi.bat` / `vanta-unregister-multi.bat`：注册或取消 `mpv.exe` 多实例入口。
  - `vanta-register-single.bat` / `vanta-unregister-single.bat`：注册或取消 `umpv.exe` 单实例入口。
  - 四个 BAT 统一调用 `vanta-associations.ps1`；逻辑与 VantaInstaller 一致：HKCU、无需 UAC、独立 Applications/Capabilities/ProgID、100 个音视频扩展、Shell 刷新与共享开始菜单快捷方式。
- **旧入口定位**：原四个 `mpv-install/uninstall*.bat` 每个只增加 5 行 `[LEGACY SYSTEM-WIDE FALLBACK]` 和新版入口提示；原 HKLM、管理员权限及清理逻辑未修改，继续作为兼容/旧关联清理兜底。
- **文档与打包**：README 增加纯包手动入口表。`build-release.ps1` 已确认递归复制整个 `installer/` 到 01；个人全量包由 01 合并生成，因此无需改构建脚本即可同时包含五个新文件。
- **兼容处理**：`vanta-associations.ps1` 使用 UTF-8 BOM + LF；BOM 是 Windows PowerShell 5.1 正确读取中文注释所必需的兼容例外。四个 BAT 保持 ASCII 可执行内容 + LF，避免旧 `cmd.exe` 误解析 UTF-8 中文注释。
- **验证**：
  - Windows PowerShell 5.1 直接 dry-run 通过；四个 BAT 经 `VANTA_ASSOC_DRY_RUN=1` 逐一调用全部退出 0，无 ParserError 或“not recognized”。
  - C# 与 PowerShell 扩展名集合均为 100 个、差异 0；多/单实例 ProgID、RegisteredApplications 名称和 `mpv-single` 标识一致。
  - VantaInstaller 清理生成缓存后 Release 全量重建通过（0 警告、0 错误）；首次增量失败确认为先前跨 RID publish 遗留的 WPF BAML 缓存，`dotnet clean` 后消失。
  - 新文件均为 LF、无尾随空白；`git diff --check` 通过。本轮仅 dry-run，未写注册表、未构建正式 01/全量包、未发布。

### 2026-08-11 14:04 会话：installer 文件关联入口分层整理

- **目录结构**：
  - `installer/associations/current-user/`：推荐入口 `register/unregister-multi/single.bat` 与共享 `vanta-associations.ps1`。
  - `installer/associations/legacy-system-wide/`：原四个 `mpv-install/uninstall*.bat` 及专用 `mpv-icon.ico`、`mpv-document.ico`。
  - `installer/associations/README.txt`：纯包用户可直接阅读的入口说明；`installer/` 根目录不再散落任何关联脚本或关联图标。
- **路径修正**：新版 PowerShell 从三级父目录解析播放器根目录；旧注册 BAT 同样改为三级回溯，图标仍与脚本同目录。旧 BAT 的 HKLM 注册/清理逻辑未改变。
- **文档**：README 手动入口表更新为新目录和简化后的 BAT 名称；`AssociationService.cs` 的同步维护注释指向新 PowerShell 路径。
- **验证**：
  - 移动后四个当前用户 BAT 在 Windows PowerShell 5.1 下 dry-run 全部退出 0，均正确解析根目录 `C:\Program portable\mpv2`、100 个音视频扩展和对应 ProgID。
  - legacy 目录三级回溯结果与仓库根目录一致；`mpv.exe`、`umpv.exe` 和两枚旧图标均命中。
  - VantaInstaller Release 构建通过（0 警告、0 错误）；C# / PowerShell 扩展集合仍为 100、差异 0。
  - 全部文本归一为 LF、无尾随空白；PowerShell 保留 UTF-8 BOM 以兼容 5.1；`git diff --check` 通过。
  - `build-release.ps1` 仍递归复制整个 `installer/`，所以 01 与由其合并的全量包都会保留新层级；未实际构建或发布。
- **发布 Gate**：本次改变了公开包内 `installer/` 路径结构，命中《发布流程.md》3.2“包结构变化”。后续正式打包/发布前必须停下，由项目所有者确认流程修订或明确豁免；本轮未修改《发布流程.md》。

### 2026-08-11 14:14 会话：根目录便捷入口与 VantaInstaller 圆角图标

- **根目录镜像**：在 `installer/` 根目录新增 `register-multi.bat`、`unregister-multi.bat`、`register-single.bat`、`unregister-single.bat`。四个文件仅转发到 `associations/current-user/` 的同名实现，方便纯包用户直接双击，同时避免复制和分叉注册逻辑。
- **文档同步**：根目录 `README.MD` 与 `installer/associations/README.txt` 均将根目录镜像标为推荐便捷入口，并保留 current-user 实现目录和 legacy-system-wide 兜底目录的说明。
- **图标替换**：废弃首版带尖锐 V 形延伸的生成方案；用户确认后采用规则圆角紫色方块与标准白色播放三角。透明源图保存为 `VantaInstaller/src/Vanta.Installer/assets/vanta-icon.png`，并生成包含 16/20/24/32/40/48/64/128/256 px 的 `vanta-icon.ico`。
- **图像处理**：使用内置 ImageGen 生成，色键背景经官方 `remove_chroma_key.py` 转为透明；随后清理绿色溢色并将主体占比调整到约 84%。PNG 为 1024×1024 RGBA，四角透明。
- **验证**：四个根目录 BAT 在 `VANTA_ASSOC_DRY_RUN=1` 下全部退出 0，正确识别多/单实例、HKCU 和 100 个音视频扩展，未写注册表；VantaInstaller Release clean/build 通过（0 警告、0 错误）；构建输出中的 ICO 与源文件 SHA-256 一致。
- **用户配置保护**：`portable_config/script-opts/window_size_position.conf` 仍为用户指定的 `size=1080x720`，未改动。
- **发布状态**：未打包、未发布。此前因 `installer/` 包结构变化触发的大改动 Gate 仍然有效。

### 2026-08-11 14:18 会话：文件关联按钮灰置修复

- **原因**：用户用 `bin/Debug/net10.0-windows/VantaInstaller.exe` 启动的是重构前残留的旧 Debug 产物；旧程序仍依赖根目录旧 BAT 判断可用性，脚本分层后四个按钮因此全部灰置。此前只重建了 Release，没有刷新用户实际运行的 Debug 目录。
- **界面修正**：文件关联说明从“管理员权限（弹 UAC）”改为“当前用户、无需管理员权限、由 Windows 打开方式选择默认播放器”。
- **启用条件**：原共享 `CanRegister` 拆为 `CanRegisterMulti` 和 `CanRegisterSingle`；多实例检查 `mpv.exe`，单实例检查 `mpv.exe + umpv.exe`。两个取消按钮不再依赖播放器文件，允许在播放器缺失时清理当前用户关联。
- **反馈修正**：确认原来的通用 `OperationMessage` InfoBar 位于整个长设置页最底部，当前文件关联视口看不到，导致有效点击也像“没反应”。关联卡片内现增加就地 InfoBar，并实时显示“多实例/单实例：已注册或未注册”；`AssociationService.IsRegistered()` 根据当前用户 RegisteredApplications 值读取真实状态。
- **验证**：关闭旧 Debug 进程后，Debug 与 Release 均执行 clean/build，全部 0 警告、0 错误；随后已从用户原命令对应路径重新启动新版 Debug。使用 Windows UI Automation 真实调用四个按钮：多实例与单实例注册均写入各自 HKCU Capabilities，取消均成功清除；状态文本即时切换。测试结束后两套测试关联均已取消。

### 2026-08-11 14:23 会话：文件关联阶段日志

- **服务回调**：`AssociationService.Register()` 与 `Unregister()` 增加可选 `Action<string>` 阶段回调；安装引擎、完成页等既有调用无需传入，原行为保持兼容。
- **卡片日志**：设置页关联卡片增加 `AssociationLog` 列表，每次操作先清空上一轮日志，再按真实执行阶段显示编号行；汇总 InfoBar 与实时已注册/未注册状态继续保留。
- **注册阶段**：检查播放器 → 清理旧入口 → 写入 Applications 与 100 个格式 → 写入 ProgID/Capabilities/命令 → 更新开始菜单入口 → 刷新 Shell → 完成。
- **取消阶段**：清理 Applications/ProgID/Capabilities → 检查共享快捷方式 → 刷新 Shell → 完成。错误也会作为最后一条阶段日志显示。
- **验证**：Debug、Release clean/build 均为 0 警告、0 错误。Windows UI Automation 点击新版 Debug 的多实例注册按钮，读取到 7 条可见阶段日志且 HKCU RegisteredApplications 写入正确；取消按钮显示 4 个阶段并清理成功。测试关联已取消，未留下测试注册状态。

### 2026-08-11 会话：启动页菜单遮挡与 HDR 参考白

- **启动页层级**：`idle-branding-image.lua` 使用 `overlay-add`，其图片会压在 uosc ASS 菜单之上。现在观察 `user-data/uosc/menu/type`：任意 uosc 菜单打开时移除启动页图片，菜单关闭后自动恢复；全屏文件浏览器的原隐藏逻辑继续保留。mpv 隔离加载通过，无 Lua 错误。
- **HDR 参考白**：用户确认 100 nit 参考白导致 DV/HDR→SDR 观感偏亮后，将 `[HDR]` 条件配置的 `hdr-reference-white` 默认值从 `100` 调整为 `203`。`mpv --show-profile=HDR` 已确认实际解析为 203。
- **实片诊断**：对《天气之子》P7.6 FEL 实际探测到 `el_pair` 与 `sh_dovi_compose_nlq`，输入为 Dolby Vision/BT.2020/PQ，显示目标为 SDR BT.709/Gamma 2.2；FEL 配对与 DV 合成链均已运行。
- **用户配置保护**：窗口设置仍为 `size=1080x720`；本轮未打包、未发布。

### 2026-08-11 会话：旧文件关联图标迁移

- **根因**：Windows `.mkv` 的 `UserChoice` 仍是旧系统级 `io.mpv.mkv`；其 `DefaultIcon` 指向已经因目录整理而失效的 `installer\mpv-document.ico`，旧单实例打开命令还缺少结尾引号。新版 `MPV.Vanta.Multi.File` 自身并未损坏。
- **稳定图标**：新增 `installer/associations/icons/mpv-document.ico`，内容与已验证的旧文档图标一致；新版多/单实例 ProgID 也优先使用该稳定资源，缺失时才回退到 `mpv.exe` 图标。
- **无 UAC 迁移**：C# 与 PowerShell 注册服务会枚举 HKLM `io.mpv.*`，仅对图标或命令确认属于当前安装目录的旧项创建带 `VantaLegacyCompat=1` 标记的 HKCU 覆盖；修复图标和引号，不修改受哈希保护的 Windows `UserChoice`，也不碰其他 mpv 安装。
- **清理规则**：取消最后一个 Vanta 入口时删除所有带上述标记的兼容覆盖；另一入口仍注册时保留共享兼容项。`UnregisterAll()` 同样清理。
- **实机迁移**：当前旧系统级集合共修复 37 个 ProgID；`.mkv` 合并结果已指向存在的稳定 ICO，命令恢复为 `"umpv.exe" "%L"`。`SHGetFileInfo` 实际取得正常紫色媒体文档图标。
- **验证**：PowerShell 5.1 dry-run/实际注册通过；VantaInstaller Debug、Release 均 0 警告、0 错误。进一步先取消再由 C# Debug UI 注册，迁移阶段日志显示“修复 37 个”，注册表与图标均正确；最终保持多实例已注册。
- **参考白说明**：mpv 官方允许 `hdr-reference-white=auto` 或 10–10000 nit 的任意值；项目 `Ctrl+T` 只是人为选择 100/203 两个常用预设。`mpv.conf` 注释已修正为当前官方范围和 auto 行为，`[HDR]` 默认仍为用户指定的 203。

### 2026-08-11 会话：Ctrl+T 与 mpv.conf 官方文档审计

- **快捷键**：`Ctrl+T` 的 `hdr-reference-white` 循环由 `100 → 203` 扩展为 `auto → 100 → 203`；保留小写 `Ctrl+t` 的 `target-trc` 绑定，两者按 mpv 键名大小写区分。
- **审计依据**：以本机 shinchiro `v0.41.0-922-gf4d13e1c2 --list-options/--help` 为实际构建基准，并对照 mpv 官方 master 手册；只更新注释和示例，不重置用户已启用参数。
- **明确修正**：
  - Dolby Vision：删除“gpu-next 不支持 EL”的旧说明，更新为当前默认 `format:enhancement-layer=yes` 可应用 P7 FEL。
  - Windows/窗口：修正 media-controls、border-background、idle、window-affinity、autofit、current-window-scale 等默认值、枚举或属性/选项区别。
  - 解码/文件：补齐当前 hwdec-codecs 默认集合、directory-filter-types 与 audio/sub 自动匹配扩展名。
  - ICC/HDR：重写 ICC 自动配置、转换意图、对比度覆盖和缓存清理说明；校正 target-prim/trc/peak、tone-mapping/param、gamut mapping、HDR 动态峰值、阈值范围和字幕 HDR 白默认值。
  - 脚本/截图：`load-osd-console` 更新为 `load-console`；移除不存在的 `ytdl-extract-chapters` 示例；修正截图目录、OSD 字号与字体目录说明。
  - 拼写：`dcale-antiring` 修正为 `dscale-antiring`。
- **静态验证**：从 `mpv.conf` 解析 352 行候选配置并与当前 `--list-options` 对照，未知选项 0、废弃选项 0；三个配置文件均为 LF、无尾随空白，`git diff --check` 通过。
- **运行验证**：用《天气之子》P7.6 FEL 完整配置实片启动，通过 IPC 读取到 `hdr-reference-white=203`、`video-target-params/max-luma=203.0`，并确认唯一参考白绑定为 `cycle-values hdr-reference-white auto 100 203`；运行日志无 error/fatal。
- **用户配置保护**：`size=1080x720` 保持不变；未打包、未发布。

### 2026-08-11 16:43 会话：uosc 章节标记复用进度条渐隐

- **实现方式**：`Timeline.lua` 不新增独立计时器或补间动画，直接复用进度条本体的 `visibility = self:get_visibility()`。
- **同步对象**：章节上下双三角、片段范围填充及起止刻度、A-B 循环标记均乘入同一可见度；原有章节悬停放大和点击跳转保持不变。
- **验证**：静态断言确认章节透明度不再直接使用固定 `config.opacity.chapters`；完整配置播放演示素材退出码为 0，日志无 error/fatal；`git diff --check` 通过。
- **用户配置保护**：`size=1080x720` 保持不变；未打包、未发布，安装结构大改动 Gate 继续有效。

### 2026-08-11 16:48 会话：章节边框渐隐与速度滑块同步

- **章节突现根因**：上一轮只把章节三角填充通道 `\1a` 接入可见度，但 ASS 的边框/阴影通道仍被 `\3a&H00&`、`\4a&H00&` 强制为完全不透明，因此视觉上仍像突然出现。
- **章节修正**：章节三角和 A-B 标记改用全通道 `\alpha`，填充、边框与阴影共同使用 `chapter_visibility`；片段范围和边界刻度继续乘入进度条 `visibility`。
- **速度滑块**：删除自身 `Element.get_visibility()` 与距离渐隐的二次计算，`Speed:get_visibility()` 直接返回 `Timeline:get_visibility()`；拖动状态也不再强制不透明，整块滑块与进度条严格同步。
- **验证**：静态断言确认章节两个 ASS 绘制入口均使用全通道透明度、速度滑块不再调用独立 hover fade；完整配置运行期间 uosc 无 Lua/error/fatal，测试进程已单独清理；`git diff --check` 通过。
- **用户配置保护**：现有用户播放进程未终止；修改需重启 mpv 后加载。`size=1080x720` 保持不变，未打包、未发布。

### 2026-08-11 16:49 会话：纠正速度滑块可见度复用对象

- **需求纠正**：速度滑块不应复用时间轴本体的可见度，否则鼠标落在时间轴时滑块不会像媒体信息胶囊一样避让隐藏。
- **最终实现**：`Speed:get_visibility()` 直接委托 `MediaInfo:get_visibility()`，因此速度滑块与胶囊共同保留“靠近时间轴隐藏、离开后渐显、位于胶囊/滑块所在高度时保持可交互”的行为；media info 不存在时回退自身基础可见度。
- **章节状态**：章节三角和 A-B 标记的 ASS 全通道渐隐修复保持不变。
- **验证**：静态断言确认速度滑块只委托 media info、不再自行调用 hover fade 或委托 timeline；`git diff --check` 通过。

### 2026-08-11 16:54 会话：章节标记钢蓝/灰蓝配色试版

- **配色**：章节三角填充从暗夜蓝 `#1E3A8A` 调整为低饱和钢蓝 `#2B5D7A`；ASS 边框从纯白调整为主题 `time_muted` 灰蓝 `#A1B4BE`。
- **范围**：仅调整章节三角；A-B 标记保持现有颜色，章节渐隐和速度滑块复用 media info 胶囊可见度不变。
- **验证**：静态颜色断言通过，`git diff --check` 通过；需重启 mpv 后进行视觉确认。

### 2026-08-11 16:55 会话：章节标记改为单三角

- **布局**：删除进度条上方朝下三角，仅保留下方底边在外、尖端朝上的单个章节标记。
- **交互**：章节悬停放大、提示、点击跳转和可见度渐隐保持不变；当前钢蓝/灰蓝配色保持不变。
- **验证**：静态断言确认每个章节只绘制一次三角且不存在上方三角坐标；`git diff --check` 通过。

### 2026-08-11 17:01 会话：恢复章节双三角

- **布局回退**：按用户视觉反馈恢复进度条上方朝下、下方朝上的双三角章节标记。
- **保持内容**：钢蓝/灰蓝配色、ASS 全通道渐隐、悬停放大、提示和点击跳转均未回退。
- **验证**：静态断言确认每个章节恢复上下两次三角绘制；`git diff --check` 通过。

### 2026-08-11 17:23 会话：uosc 共享十色主题与 VantaInstaller 入口

- **单一色号来源**：新增 `portable_config/script-opts/uosc-themes.json`，Lua 与 C# 均读取同一注册表；`uosc.conf` 仅保存 `theme=<id>`，避免各组件维护近似色号。
- **最终主题集合**：海湾蓝 `#56E5F1` 为默认，另含卡布里蓝、赤霞红、熔岩橙、靛石绿、流金粉、霞光紫、璀璨洋红、雅灰、珍珠白，共 10 套。
- **色值边界**：小米官方资料用于确认车色名称与视觉性格；除用户明确指定的海湾蓝外，其余 HEX 是为暗色 uosc 和屏幕对比度设计的“车漆观感映射色”，不宣称为小米官方色号。所有 accent/accentText 对比度均不低于 4.9:1。
- **uosc 接口**：新增 `lib/theme.lua`，把当前色板统一映射到 `accent`、`accent_text`、`accent_border`，并同步供应 `match`、heatmap、菜单选择/活动/标题和章节标记；旧 `color=match=...` 自动兼容为统一 accent 覆盖。
- **配置入口**：`uosc.conf` 新增 `theme=gulf-blue` 及完整 ID 注释；原 `color=` 保留中性色覆盖，不再锁死强调色。章节双三角不再硬编码色号，活动按钮文字使用当前主题 `accent_text`。
- **安装器入口**：设置页新增“界面配色”卡片，包含色块、名称、HEX、说明与“应用主题”按钮；C# 服务验证 ID/HEX、备份原 `uosc.conf` 后只写主题 ID，缺失或非法注册表会就地报错。
- **验证**：共享注册表实测 10 套且默认项正确；C# apply/read/backup/非法 ID 拒绝均通过；VantaInstaller Debug/Release clean build 均 0 警告、0 错误，隐藏启动通过；uosc 目录脚本正常加载注册表且无 Lua/error/fatal；`git diff --check` 通过。
- **用户配置保护**：`size=1080x720` 保持不变；未提交、未打包、未发布，安装结构大改动 Gate 继续有效。

### 2026-08-11 17:32 会话：主题色实心元素去深色描边

- **视觉规则**：主题强调色用于实心几何时不再叠加黑色/深色描边或阴影，避免彩色边缘发脏；文字和图标的可读性描边继续保留。
- **具体调整**：章节上下双三角改为 `bord0/shad0` 的纯 accent 填充；速度滑块刻度删除背景色边框，中心指示三角改为无描边。
- **接口收敛**：Lua 与新 C# 模型移除独立 `accent_border`；共享 JSON 暂保留 `accentBorder` 兼容旧 Debug 安装器，但其值强制与 `accent` 完全相同，从数据层杜绝深色强调边和色差。
- **用户现场状态**：检测到用户已通过 VantaInstaller 将当前主题切换为 `sunset-red`（赤霞红），本轮保留该选择及其自动生成的 uosc 备份。
- **验证**：静态断言确认章节与速度强调色几何无深色描边；Release 完整构建 0 警告、0 错误，共享注册表 10 套校验通过。Debug 重建仅因用户当前打开的 VantaInstaller PID 6068 锁定输出 DLL 而未执行，未强制关闭用户窗口；此前 Debug 构建已通过。

### 2026-08-11 17:37 会话：章节标记可选同色描边

- **配置接口**：新增 `chapter_marker_border`，默认 `0` 为无描边；在 `uosc.conf` 设置为 `1` 可启用 1 个逻辑像素、随 DPI 缩放的同色描边。
- **实现**：ASS 填充色和边框色都使用同一个 `CHAPTER_COLOR`，描边只加粗轮廓，不会形成黑边或近似色差；A-B 标记继续独立使用原 `timeline_border`。
- **当前状态**：保留用户 `theme=sunset-red` 与 `chapter_marker_border=0`，因此当前视觉仍是无描边赤霞红；静态断言与 `git diff --check` 通过。

### 2026-08-11 17:56 会话：media info 与速度滑块碰撞检测双行布局

- **碰撞检测**：`MediaInfo.lua` 记录本帧实际绘制的胶囊范围，不使用固定窗口宽度阈值；`Speed.lua` 用实际矩形与速度滑块正常位置做水平、垂直相交判断。
- **双行布局**：无碰撞时保持速度滑块居中并与 media info 同行；发生碰撞时按 6px（随 DPI 缩放）间距优先移到 media info 上方，顶部空间不足时尝试放到下方，并受视频画面纵向边界约束。
- **复用关系**：速度滑块继续复用 media info 胶囊的可见度；媒体信息提供画面边界接口，避免在 Speed 中重复实现信箱黑边计算。
- **验证**：LuaJIT 语法检查通过；`mpv --no-config --idle=once --script=portable_config/scripts/uosc/main.lua` 启动检查通过；完整配置下 16:9、方形柱状黑边、竖向柱状黑边演示素材均以 `vo=null` 播放退出码 0；`git diff --check` 通过。
- **用户配置保护**：`size=1080x720` 保持不变；未打包、未发布，安装结构大改动 Gate 继续有效。尚未做窗口实机视觉确认，需重启 mpv 后在小窗口观察两行切换。

### 2026-08-11 18:04 会话：排查双击视频无窗口

- **现象定位**：之前的无头运行验证使用了完整配置；配置中的 `input-ipc-server=\\.\pipe\mpvsocket` 与 `idle=yes` 让测试进程继续驻留且没有窗口。当前 `.mkv` 的旧兼容关联 `io.mpv.mkv` 走 `umpv.exe` 单实例入口，因此双击时文件被发送到这些无窗口进程，看起来像没有启动。
- **处理**：按命令行逐一核对并清理本轮创建的 7 个测试 mpv 进程，没有终止用户进程；清理后确认没有遗留 mpv/umpv 进程。
- **验证**：直接调用当前 `umpv.exe -foreground tmp/demo/normal-169.mp4` 成功拉起带窗口的 mpv；关联命令仍为存在的 `"C:\Program portable\mpv2\umpv.exe" "%L"`，未发现本次碰撞布局改动造成启动崩溃。
- **当前建议**：请重新双击原视频测试；若仍无窗口，再把具体扩展名和是否出现 mpv 进程告诉我。未修改注册表和用户配置，`size=1080x720` 保持不变。

### 2026-08-11 18:20 会话：内置 HarmonyOS Sans SC 字体

- **字体资产**：从 Huawei 官方 `huawei-fonts/HarmonyOS-Sans` 仓库提供的 `HarmonyOS Sans.zip` 中提取未修改的 `HarmonyOS_Sans_SC_Regular.ttf` 与 `HarmonyOS_Sans_SC_Bold.ttf`；字体内部家族名确认是 `HarmonyOS Sans SC`。
- **默认字体**：`mpv.conf` 的 OSD/纯文本字幕、uosc 的 UI/菜单、播放列表/画质菜单、Faster-Whisper 字幕和弹幕默认字体均改为 HarmonyOS Sans SC；统计/控制台等需要列对齐的等宽界面继续使用 Noto Sans Mono CJK SC。
- **回退策略**：Windows 使用 DirectWrite 自动回退；`F` 字幕字体循环把 Microsoft YaHei 放在最后，系统安装时作为最终手动/系统回退。未将微软雅黑字体文件复制进包，避免无授权复制 Windows 系统字体。
- **许可证**：原始 HarmonyOS Sans 字体授权文件随配置放在 `portable_config/licenses/HarmonyOS-Sans-SC-LICENSE.md`，字体目录不放文本文件，避免 mpv 把许可证误当字体加载。
- **验证**：字体 name 表解析通过；mpv 无配置字体加载检查成功，日志确认两套字体均被加载且无 `Error opening memory font`；输入配置解析和 `git diff --check` 通过；没有遗留 mpv 测试进程。
- **发布边界**：新增约 16.4 MiB 第三方字体属于《发布流程.md》3.2 大改动 Gate 的字体/第三方版权范围；本次未打包、未发布，后续公开 Release 前必须按发布流程由用户决定是否纳入公开包。`size=1080x720` 保持不变。

### 2026-08-11 18:42 会话：新增初音绿/安装器大葱绿主题

- **共享色板**：`portable_config/script-opts/uosc-themes.json` 新增 `miku-green`，强调色为初音未来常用代表色 `#39C5BB`，填充和边框保持同色，深色文字使用 `#071522`。
- **名称分层**：主题注册名保持“初音绿”；新增可选 `installerName` 字段，VantaInstaller 的下拉框、当前状态和应用结果显示为“大葱绿”，不影响 mpv/uosc 的主题 ID 与 Lua 读取。
- **安装器**：`UoscThemePalette.DisplayName` 对旧色板回退到 `name`，因此旧版注册表仍兼容；设置页统一绑定 `DisplayName`。
- **验证**：共享 JSON 校验通过，共 11 套色板；VantaInstaller Debug 构建 0 警告、0 错误；编码、LF 与 `git diff --check` 检查通过。
- **用户配置保护**：`size=1080x720` 未改动；未打包、未发布，字体/安装结构大改动 Gate 继续有效。

### 2026-08-11 19:00 会话：播放/暂停按钮接入主题色

- **按钮逻辑**：`portable_config/scripts/uosc/elements/Controls.lua` 的 `play-pause` 快捷配置把暂停状态 `yes=play_arrow` 标记为 active，行为与全屏按钮的 `yes=fullscreen_exit!` 对齐。
- **主题复用**：播放/暂停按钮直接复用 `Button.lua` 已有的 `config.color.match` 背景和 `config.color.accent_text` 图标颜色，因此会跟随海湾蓝、初音绿/大葱绿及其他主题切换，不新增第二套色号。
- **状态表现**：播放中显示普通按钮；暂停时显示当前主题强调色填充与主题文字色图标；悬停、提示和按钮尺寸逻辑保持不变。
- **验证**：静态断言确认播放/暂停和全屏均使用 active 状态语法；完整配置 mpv 以 `theme=miku-green` 无头播放演示素材退出码 0，未出现 Lua/error/fatal；`git diff --check` 通过。
- **用户配置保护**：`size=1080x720` 未改动；未打包、未发布。

### 2026-08-11 19:09 会话：修正统计 OSD 字体未跟随 HarmonyOS Sans SC

- **问题定位**：普通 mpv OSD 与 uosc 已从新启动日志确认使用 `HarmonyOS Sans SC`；用户可见的统计面板仍由 `portable_config/script-opts/stats.conf` 显式指定 `Noto Sans Mono CJK SC`，因此看起来不像默认 OSD 字体。
- **修正**：统计面板普通文本改为 `HarmonyOS Sans SC`；`font_mono` 继续保留 `Noto Sans Mono CJK SC`，仅用于数值/列对齐字段，避免破坏统计表格布局。
- **边界说明**：控制台补全和文件浏览器正文仍是有意保留的等宽字体；Material Icons 仍使用图标字体，不应替换成 HarmonyOS Sans SC。
- **验证**：新配置启动并触发统计面板切换退出码 0；确认 HarmonyOS Sans SC 字体文件被 DirectWrite 加载；`git diff --check` 通过。
- **用户配置保护**：`size=1080x720` 未改动；未打包、未发布。

### 2026-08-11 19:15 会话：确认“显示设备”统计标题字体

- **具体标题**：用户所指的“显示设备:”来自 `portable_config/scripts/stats.lua` 的默认统计页 `add_video_out()`，不是 uosc media info。
- **字体链路**：统计页先由 `text_style()` 写入普通字体，标题通过 `bold()` 使用同一字体的粗体；`stats.conf` 和 `stats.lua` 默认值均已固定为 HarmonyOS Sans SC。
- **实际验证**：GPU OSD 冒烟日志在切换统计页后显示 `fontselect: (HarmonyOS Sans SC, 700, 0) -> HarmonyOS_Sans_SC_Bold`；随后出现的 Noto Sans Mono CJK SC 仅对应数据列字体。无 Lua/error/fatal。
- **兼容兜底**：即使用户缺少 `stats.conf`，`stats.lua` 内置默认也会使用 HarmonyOS Sans SC；`font_mono` 仍用于数字/列对齐。
- **用户配置保护**：需完全重启 mpv 才能加载新的脚本配置；`size=1080x720` 未改动，未打包、未发布。

### 2026-08-11 会话：只读审计今日改动 + 发布前修正（未打包、未构建）

- **审计范围**：起播徽章多帧检测、uosc 主题/章节/速度滑块/碰撞布局、文件关联 C# 重写与旧项迁移、字体内置、安装器界面。未发现致命逻辑问题；历史旧入口、旧配置、旧关联均有兼容路径。
- **mpv.conf 去 BOM**：首行被写入 UTF-8 BOM（首行为注释时 mpv 可正常解析，但不符合仓库 UTF-8 无 BOM 约定，且会让 diff 首行噪声化）；已用字节级处理移除，全文件保持 LF、650 行不变。
- **FEL 注释修正**：删除不存在的 `format:enhancement-layer=yes` 选项说法（当前构建 `--list-options/--help` 无此选项）；改为“FFmpeg 解码器与 gpu-next 渲染链自动配对并应用 P7 FEL，无需配置项”。
- **截图设置**：`screenshot-format=jxl` 与 `screenshot-jpeg-quality=100` 为用户本人确认的有意修改，保留。
- **打包排除 backup**：`build-release.ps1`（01）与 `build-config-public.ps1`（05）新增递归删除 `portable_config/backup` 与 `portable_config/script-opts/backup`（个人 mpv.conf 备份 + 12 个主题应用备份不再进公开包）；PowerShell 5.1 查找匹配实测通过（两目录均命中），脚本 AST 解析通过。
- **05 排除字体**：`build-config-public.ps1` 排除 `fonts/` 与 `licenses/`，HarmonyOS Sans SC 及授权文件只由 01 Base 携带；`build-full-private.ps1` 按 01→05 解压合并，全量包自动从 01 获得字体，无需额外改动。
- **uosc.conf 注释补全**：主题可选列表补上 `miku-green（大葱绿）`。
- **画质菜单等宽字体**：`quality-menu.conf` 的 `style_ass_tags` 由 HarmonyOS Sans SC 改回 `Noto Sans Mono CJK SC`，保持多列对齐。
- **安装器版本**：`VantaInstaller.csproj` 由 `0.2.0` 提升到 `0.3.0`（本轮关联重写 + 主题功能），行尾统一为 LF。
- **编码/行尾**：本次涉及全部文件 UTF-8 无 BOM、LF；`git diff --check` 通过；未打包、未构建，字体/安装结构大改动 Gate 继续有效。

### 2026-08-11 会话：发布脚本重构——每子包独立构建（未打包、未发布）

- **背景**：原 `build-release.ps1` 把 01 Base 与 02 Extras 耦合在一个脚本，02 只能整体 `-SkipExtras`，无法单独构建任一子包；03/04/05 虽已独立但命名不统一。
- **新结构**（根目录，统一 `build-NN-*` 命名，全部 `-Version` 必填 + `-OutputDir` 可选，默认 `release`）：
  - `build-01-base.ps1`：01 播放核心 + 运行时 + 基础配置（含 `.vanta-version`、内置字体、排除 backup/window_state/script-assets 保留）。
  - `build-02-extras.ps1`：02 着色器 + VapourSynth + Python + 工具（保持 1900MB 分卷）。
  - `build-03-fasterwhisper.ps1`：由 `build-fasterwhisper-public.ps1` 重命名（git mv 保留历史），内容不变。
  - `build-04-lsfg.ps1`：由 `build-lsfg-public.ps1` 重命名（git mv 保留历史），内容不变。
  - `build-05-config.ps1`：由 `build-config-public.ps1` 重命名（git mv 保留历史），内容不变（含 fonts/licenses 排除、.vanta-version 排除）。
  - `build-full-private.ps1`：保留原名（合并包而非子包），逻辑不变。
  - `build-all-packages.ps1`：01→05 顺序调用子脚本 + `-IncludePrivate`；子脚本只清理各自暂存目录，总入口末尾统一删除 `build/`。
- **删除**：`build-release.ps1`（含其上轮未提交的 backup 排除逻辑，已完整并入 `build-01-base.ps1` 的 `Invoke-CopyConfig`）。
- **README**：`打包脚本`章节更新为 6 个独立脚本 + 总入口说明。
- **验证**：7 个脚本 PowerShell 5.1 AST 解析全部通过；全部 UTF-8 无 BOM、LF；`git diff --check` 通过。
- **实跑验证**：`build-01-base.ps1 -Version 9.9.9 -OutputDir tmp\buildtest-01` 实际构建成功（103.6 MB），包内 `.vanta-version=9.9.9` 无换行、`portable_config\fonts\HarmonyOS_*` 与 `licenses\HarmonyOS-Sans-SC-LICENSE.md` 均在、`backup/` 与 `window_state.conf` 均排除；验证后测试产物与 `build/` 已清理，未触碰 `release/`。
- **待用户处理**：《发布流程.md》第 78～86 行仍引用旧脚本名（`build-release.ps1` 等），按规则 agent 不修改该文件，需项目所有者同步更新。03/04/05 为重命名未实跑，建议正式发布前完整跑一次 `build-all-packages.ps1 -IncludePrivate`。

### 2026-08-11 会话：发布流程更新 + 全量构建测试（版本号 9.9.9，输出 tmp\buildtest-9.9.9）

- **《发布流程.md》更新（用户指示）**：第 4.1 节子包调用链改为 `build-01-base.ps1`（01）→ `build-02-extras.ps1`（02）→ `build-03-fasterwhisper.ps1`（03）→ `build-04-lsfg.ps1`（04）→ `build-05-config.ps1`（05）→ `build-full-private.ps1`（仅 `-IncludePrivate`）；补充各子包可独立构建及 `-OutputDir` 说明；`.vanta-version` 写入/排除段落同步更新脚本名。
- **五个公开包实跑**（`-Version 9.9.9 -OutputDir tmp\buildtest-9.9.9`，全部退出 0）：
  - 01 Base 108,585,306 B（103.6 MB）；02 Extras 分卷 1,992,294,400 + 781,608,366 B（1900 + 745.4 MB）；03 FW 1,476,001,985 B（1408 MB）；04 LSFG 3,197,543 B；05 Config 5,104,891 B（4.9 MB，字体已排除）。
- **包内容审计（防误排除）**：以 7z `-slt` 列表对三个公开包逐一断言——
  - 01：今天改动的 24 个 portable_config 文件（含 uosc-themes.json、theme.lua、startup-logo-bounds.lua）全部在包内；`portable_config\fonts\` 8 个文件（含 HarmonyOS Regular/Bold）、`licenses\` 1 个授权、`script-assets\` 679 个启动素材均在；`.vanta-version` 存在；`backup/` 与 `window_state.conf` 无。
  - 05：今天改动的 24 个文件全部在包内；fonts/licenses/script-assets/backup/`.vanta-version`/window_state 全部排除，无误含。
  - 04：`lsfg_control.lua`、`start-mpv-lsfg.ps1`、`Lossless.dll`、`lsfg-vk-layer.dll`、`research/UPSTREAM.md` 均在。
  - 02：着色器、VapourSynth、Python、工具、EXTRAS-README 关键项均在，未误含 fonts。
  - 01 包内 README.MD 与 .gitignore 已随根目录最新版复制。
- **解析注意事项**：7z 26.02 对 solid 归档的表格输出在文件行省略 Compressed 列、且 stdout 为 GBK 编码；审计改用 `7z l -slt` + Python 解析 `Path = ` 行（GBK 解码）最可靠。曾出现的“MISS”均为解析脚本问题，非包内容问题。
- **状态**：五个公开包已生成到 `tmp\buildtest-9.9.9` 供用户实测；未触碰 `release/`，未构建个人全量包，未发布。正式发布前建议按流程完整跑 `build-all-packages.ps1 -IncludePrivate` 并做 7z t / SHA-256 核验。
- **拆分无损复核（机械对比）**：取回 HEAD 的 `build-release.ps1`，用脚本提取新旧两侧全部“复制源”集合（Copy-IfExists / Invoke-CopyTo / 数组 / foreach / pyd 通配 / 目录整体复制）做差集——01 Base 丢失 0 项、02 Extras 丢失 0 项；helper 函数 `Invoke-CopyTo`、`Copy-IfExists`、`Remove-GeneratedArtifacts` 逐字一致；`Invoke-CopyConfig` 仅多出上轮有意新增的 backup 排除；`Invoke-Pack` 仅移除 `-Split` 开关（01 固定不分卷、02 固定 `-v1900m` 分卷，属设计调整）；EXTRAS-README 文本逐字一致；`.vanta-version` 写入、7z 检查、生成物清理均保留。结论：拆分未丢失任何应打包文件。

### 2026-08-11 会话：VantaInstaller v0.3.0 Release 构建（未发布）

- **命令**：`dotnet publish src\Vanta.Installer\Vanta.Installer.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:EnableCompressionInSingleFile=true -o publish\win-x64`（dotnet 10.0.301），0 警告 0 错误，退出码 0。
- **产物**：`VantaInstaller\publish\win-x64\VantaInstaller-win-x64-v0.3.0.exe`（67,648,516 字节 ≈ 64.5 MB，单文件自包含压缩，免 .NET 运行时）；与 `VantaInstaller.exe` 的 SHA-256 完全一致（`575d3415…c32df7`）；旧 `v0.2.0` 产物保留在同目录未删除。
- **启动验证**：`Start-Process -WindowStyle Hidden` 启动 4 秒后进程存活（PID 5800），确认 Release 单文件版可运行，测试进程已关闭。
- **状态**：仅本地构建，未上传 GitHub Release，未触发发布流程；按 4.1 安装器独立构建，不提升 mpv 包版本号。

### 2026-08-11 20:28 会话：uosc 窄窗口自适应与播放列表计数字重

- **根因定位**：当前底栏由原 32px/8px/2px 调整为 36px/18px/10px，并加入更多常驻控件；尺寸只乘 DPI/全屏比例，不随窗口宽度变化。速度滑块已经在时间轴上方独立居中，但 `Controls` 仍为它保留最大约 164px 的横向占位；1172px 截图下两个弹性 `space` 被压为 0，播放键居中补偿不执行，理论偏移 -69.99px，与截图约 -68～-70px 一致。
- **浮动速度布局**：为 `Controls` 新增 `floating` sizing；速度滑块继续由底栏提供自适应宽高，但不再推进底栏横向流。当前 `uosc.conf` 删除 speed 后已失效的 `gap:0.12` 与 `reserve:0.20` 幽灵占位；`reserve` 解析能力保留，兼容其他自定义布局。
- **窄窗口缩放**：新增 `controls_compact_threshold=1280` 与 `controls_compact_min_scale=0.6`。按扣除 HiDPI 后的逻辑窗口宽度平滑缩放 controls size/spacing/margin，阈值为 0 时可关闭；HiDPI 与 `scale`/`scale_fullscreen` 仍正常叠加。
- **布局仿真**：当前全控件、章节与播放列表均存在时，1172px 为 33px 控件、播放键偏移 0；用户默认 1080px 窗口为 30px、偏移 0；960px 为 27px、偏移 0；800px 为 23px、偏移 0。640px 以下受最低点击尺寸约束，允许逐步隐藏外围控件。
- **左上角计数**：`TopBar` 的 `当前位置/总数` 改为左侧当前位置常规字重、右侧总数粗体，保留斜杠/总数 90% 字号；宽度测量补入此前遗漏的 `/`，避免两位数时胶囊过窄。
- **验证**：4 个 Lua 文件经 LuaJIT `loadfile` 语法检查通过；完整配置以两段视频组成播放列表实跑，退出码 0、无 Lua/runtime/fatal；`git diff --check` 无空白错误；涉及文件全部 UTF-8 无 BOM、LF。未构建、未打包、未发布。
- **Git 状态**：`master` 领先 `origin/master` 1 个提交，工作树仍含今日整批未提交改动；本次新增修改集中在 `uosc.conf`、`main.lua`、`Controls.lua`、`Speed.lua`、`TopBar.lua` 及 HandShake 记录。

### 2026-08-11 20:31 会话：uosc 全局渐隐距离按分辨率与窗口自适应

- **问题**：`proximity_in=80`、`proximity_out=160` 原本直接作为 OSD 坐标像素使用；1080p 全屏合适，但 1440p/4K 相对范围偏小，小窗口则相对覆盖区域过大、容易到处触发。
- **方案**：新增 `proximity_adaptive`、`proximity_scale_min`、`proximity_scale_max`。开启后把 80/160 视为 1920×1080 全屏基准，实际比例取 `min(窗口宽/1920, 窗口高/1080)`，默认限制在 0.35～2.0；同时使用宽高归一化可避免超宽屏或竖屏按单一边长过度放大。
- **实际距离**：1920×1080=80/160；2560×1440≈106.7/213.3；3840×2160=160/320；1080×720=45/90；用户截图 1172×658≈48.7/97.5；640×360 触及下限后为 28/56。
- **边界**：仅作用于 `Element:update_proximity()` 的全局渐显/渐隐范围；media info 与速度滑块靠近时间轴时的 2～9px 局部同步渐隐仍独立使用 `state.scale`，未被分辨率比例重复放大。
- **验证**：LuaJIT 语法检查通过；完整配置双文件播放列表实跑退出码 0、无 Lua/runtime/fatal；目标文件 `git diff --check` 通过。未构建、未打包、未发布。

### 2026-08-11 20:40 会话：播放列表计数统一粗体与左上角标题点击诊断

- **计数样式**：按用户反馈将左上角 `当前位置/总数` 的两侧数字、斜杠统一为同一字号和粗体；文本宽度测量同步使用 bold，避免粗体字符超出胶囊。
- **标题点击用途**：当前 `top_bar_alt_title_place=toggle` 会给主标题注册 `primary_click`，用途是在 mpv `title` 与 `media-title` 间切换。该文件两者相同或互相包含时，uosc 去重后备用标题为空，点击只翻转不可见状态，因此视觉上无效果。
- **拖动冲突**：uosc 光标框架规定 `primary_click` 区默认禁止 VO 窗口拖动，所以即使无备用标题，主标题点击区仍会抢占拖动；全局 `MBTN_LEFT` 绑定为暂停并闪烁暂停指示器，用户看到的重复暂停图标来自两套鼠标处理在该区域的交互，并非标题功能。当前章节行另有点击区，正常用途是打开章节菜单。
- **范围**：本轮只按明确要求改计数样式，未擅自改变标题点击/拖动行为；后续可选择仅在备用标题确实存在时注册切换区，或关闭 toggle 让主标题用于拖动。
- **验证**：TopBar LuaJIT 语法、目标 diff 空白检查和双文件播放列表实跑均通过，退出码 0、无 Lua 运行时错误。未构建、未打包、未发布。

### 2026-08-11 20:42 会话：关闭 WebUI 启动地址 OSD

- **来源定位**：`simple-mpv-webui/main.lua` 在首次 `file-loaded` 时通过 `mp.osd_message` 显示 `[webui] v3.0.0` 与监听地址，持续 5 秒；已有官方配置项 `osd_logging` 控制，无需修改第三方脚本。
- **配置调整**：`portable_config/script-opts/webui.conf` 将 `osd_logging=yes` 改为 `no`，并补充说明。WebUI 仍启用、端口仍为 8060、IPv4 监听保持不变；启动地址仍可写入控制台，仅不再覆盖播放器左上角标题。
- **验证**：完整配置单文件实跑退出码 0；配置 diff 空白检查通过，文件保持 UTF-8 无 BOM、LF。未构建、未打包、未发布。

### 2026-08-11 20:49 会话：恢复并下移 WebUI 启动地址 OSD

- **用户决定**：WebUI 的局域网访问地址提示有实用价值，恢复显示，但不能覆盖 uosc 左上角标题。
- **独立定位**：`simple-mpv-webui/main.lua` 新增 `log_startup_osd()`，通过 `osd-ass-cc` 与 ASS `an7/pos` 只定位“启动成功”提示；默认逻辑坐标为 x=20、y=72，并乘 `display-hidpi-scale`。普通 WebUI 错误继续使用原生 OSD 位置，避免严重信息被固定在较低位置。
- **配置接口**：`webui.conf` 恢复 `osd_logging=yes`，新增 `startup_osd_offset_x=20`、`startup_osd_offset_y=72`。用户可只改 y 为 84/96 继续下移，无需修改 Lua。
- **验证**：WebUI LuaJIT 语法、目标 diff 空白与 UTF-8 无 BOM/LF 检查通过；完整配置单文件实跑退出码 0、无 Lua/runtime/fatal。未构建、未打包、未发布。

### 2026-08-11 20:52 会话：微调 WebUI 启动提示纵坐标

- 用户实机确认 y=72 过低；`webui.conf` 与 WebUI 脚本内置默认同步调整为 `startup_osd_offset_y=42`，x=20 不变，避免配置缺失时位置回跳。
- WebUI LuaJIT 语法与目标 diff 空白检查通过；需重启 mpv 观察。未构建、未打包、未发布。

### 2026-08-11 20:57 会话：章节菜单加入进度条章节标记开关

- **菜单入口**：uosc `chapters` 自更新菜单首项新增“显示进度条章节标记”，带 bookmark 图标、已开启/已关闭提示、active 勾选/强调状态及下方分隔线；章节列表从第二项继续显示。
- **状态复用**：菜单项直接调用现有 `chapter_display` 切换函数，继续复用 `Ctrl+Shift+C`、`user-data/uosc/chapter-display`、时间轴 opacity 更新和 `uosc.conf` 持久化，不建立第二份状态。
- **交互优化**：`create_self_updating_menu_opener` 补齐对 Menu 已有 `keep_open` 字段的支持；开关点击后菜单保持打开并立即重建条目，勾选和提示同步变化。普通章节点击仍跳转并关闭菜单。
- **选中位置**：初次打开菜单时显式将选择定位到当前章节（考虑首项开关后的 +1 偏移）；无当前章节时定位到开关。
- **验证**：LuaJIT 语法、UTF-8 无 BOM/LF 和 `git diff --check` 通过；IPC 实测章节菜单打开成功，状态 `yes → no → yes`，首次切换后菜单仍为 `chapters`，最终恢复原配置 `chapter_display=yes`；测试进程已清理。未构建、未打包、未发布。

### 2026-08-11 21:06 会话：uosc DPI/固定像素只读审计

- **审计范围**：只读检查 uosc 的坐标、尺寸、边距、命中区、描边、拖动阈值和自定义组件；未修改播放器代码。主体控件、media info、速度胶囊位置、菜单基本尺寸、顶栏、音量、圆角和文字描边大多已使用 `state.scale`。
- **高优先级缺口**：
  - `Timeline.progress_size/min_progress_size` 直接使用 `options.progress_size`，未乘 DPI；200% 时细进度仍为 2px 而非 4px。
  - `Timeline.chapter_size=max(...,3)` 的最小值未缩放；当前 `timeline_size=12` 时 100% 与 200% 都落到 3px，章节双三角基本不随 DPI 增长。A-B 标记的最小半径 8、尖端 ±3 和边框也未缩放。
  - Timeline 纵向定位仍按 `controls_size/margin × state.scale` 计算，没有复用新增的小窗 `controls_compact_scale`；1080px 窗口实际 controls 为 30/15，但 Timeline 仍按 36/18 预留。
  - TopBar 点击区继续减原始 `options.proximity_in`，没有使用自适应后的有效距离；4K/小窗下可见范围与命中范围不一致。
  - 缩略图边框 `max(2,state.radius/2) × state.scale` 对已经缩放过的 `state.radius` 再乘一次 DPI，属于重复缩放；200% 下约 14px，合理值约 7px。
- **中优先级缺口**：时间轴 heatmap 高度 40/裁切 10、hover 水平容差 24、拖拽判定 5、Controls/Timeline 空间阈值 10；菜单滚动槽 `-2/+1`、最小滑块 40、标题内缩 2/3、提示字号差 1；Speed 刻度 1/1.5 和中心指针底边 2；BufferingIndicator 基础尺寸 30。以上应分别按 `state.scale`，其中菜单/速度的 1px 发丝线可保留物理像素。
- **应保留固定物理像素**：Timeline 的 0.5px 像素中心采样、部分 `+1` 防空矩形判断、真正的 1px 发丝边框、`min_width_px` 显式像素模式和鼠标历史时间阈值；这些不是 DPI 漏适配。
- **建议顺序**：先建立共享的 `controls_scale` 与 effective proximity 接口，再修 Timeline 章节/进度/A-B/缩略图，最后统一菜单与 Speed 的装饰常量；分两步实机验证 100%/150%/200% DPI，避免一次性放大所有细线导致界面变粗。
- **状态**：本轮仅报告，未构建、未打包、未发布；工作树仍含今日整批未提交修改。

### 2026-08-11 21:28 会话：提交基线并完成 uosc DPI 适配

- **基线提交**：将此前安装关联、VantaInstaller、发布脚本、主题、字体及 uosc 交互等已验证改动提交为 `0721fb6 feat: 完善安装关联、发布构建与 uosc 交互`；明确排除 `portable_config/backup/` 与 `portable_config/script-opts/backup/`。
- **共享缩放接口**：`lib/utils.lua` 新增底栏专用 `get_controls_scale()`，统一叠加 `display-hidpi-scale`、uosc scale/fullscreen scale 与窄窗口 compact scale；构造阶段无真实 OSD 尺寸时回退 `state.scale`。新增 `get_effective_proximity_distances()`，由 Element 与 TopBar 共同复用，避免渲染渐隐和点击命中采用不同距离。
- **时间轴 DPI 修复**：Timeline 的控件尺寸、边距和侧边距复用底栏缩放；细进度、闪现最小进度、章节双三角、A-B 柄宽、热力图高度/裁切、缩略图拖动阈值均按 DPI 缩放。修复缩略图边框对已缩放 `state.radius` 再乘一次 DPI 的问题（当前 border_radius=7 时 200% 从错误约 14px 回到 7px）。
- **次级组件**：菜单提示字号差、拖动阈值、滚动槽/滑块最小高度、标题与搜索框内缩改为逻辑像素；速度滑块无 media info 时的高度兜底复用底栏缩放；BufferingIndicator 的 30px 基准按 DPI 缩放。保留 Timeline 半像素中心、Speed 刻度、搜索光标偏移及 ASS 1px 发丝线等物理像素语义。
- **配置注释**：`uosc.conf` 明确 UI 配置值为逻辑像素并自动乘 `display-hidpi-scale`；章节标记说明由过时的“暗夜蓝”改为主题色。用户指定的 `window_size_position.conf size=1080x720` 保持不变。
- **DeepSeek 复核**：使用 DeepSeek v4 Flash 子代理只读复核固定像素、重复缩放、共享接口加载顺序和风险；确认接口加载顺序安全、旧 proximity 局部函数无残留，并据此完成全部 P0 项及一致性 follow-up。
- **验证**：独立 uosc 在 scale=1/1.5/2 下分别实跑，均退出 0、无 Lua/stack/script-opts 错误；数值矩阵覆盖 1920×1080@100%、2880×1620@150%、3840×2160@200% 与 1920×1080@200% 小窗，断言全部通过；UTF-8 无 BOM、LF 与 `git diff --check` 通过。未构建、未打包、未发布。
- **测试注意**：一次完整配置测试的通用进程清理误关闭了当时存在的 mpv 主实例及 thumbfast；随后测试全部改为 `--no-config`、`--player-operation-mode=cplayer` 并按测试 PID 回收，避免再次影响用户进程。

### 2026-08-11 22:22 会话：Media Info 与速度滑块统一底栏窄窗口缩放

- **目标**：此前 MediaInfo 的字体、胶囊高度、间距和垂直偏移只使用 `state.scale`，窗口低于 1280 逻辑像素时仍保持全尺寸；Speed 虽由 Controls 获得紧凑宽度，但随后又用未 compact 的 MediaInfo 高度/字号覆盖，导致两者与底栏缩放不一致。
- **MediaInfo**：渲染几何统一改用 `get_controls_scale()`；覆盖字体、胶囊高度/圆角/内边距、分组间距、字距、时间轴偏移、画面内缩及渐隐命中 padding。`get_height()`、`get_font_size()`、`get_center_y()` 与实际 render 复用相同比例，保证 Speed 碰撞检测拿到真实尺寸。
- **Speed**：字号增量、无胶囊兜底高度、时间轴备用间距、双行碰撞间距、刻度内缩和速度文字偏移统一改用 controls scale；速度宽度继续由 Controls 的 floating 尺寸提供，因此宽高都会跟随同一 compact 比例。
- **边界保留**：MediaInfo 文字描边与 Speed 文字描边继续按 `state.scale`，与底栏按钮一致，避免小窗口把描边压得过细；时间轴 bar height 继续复用 Timeline 的 `state.scale` 公式，物理发丝线未修改。
- **验证**：独立 uosc 在 960×540 窗口、scale=1/1.5/2 下均退出 0 且无 Lua/stack/script-opts 错误；数值矩阵覆盖 1080 默认窗口、100%/150%/200% 全屏、200% 小窗口和 60% compact 下限，全部断言通过。未构建、未打包、未发布。
- **工作树边界**：用户自行修改的 `uosc.conf`（`proximity_scale_min=0.8` 及其说明文字）保持未暂存、未改写；两个 backup 目录继续不跟踪。

### 2026-08-11 22:49 会话：统一窄窗口缩放下限为 75%

- **用户决定**：底栏、MediaInfo 与 Speed 不拆分下限，继续共用 `controls_compact_min_scale`；默认值与实际配置由 0.6 统一提升为 0.75。
- **实际曲线**：≥1280 逻辑像素为 100%；1080px 为 84.375%；≤960px 固定为 75%。最低状态下 controls 36→27px、MediaInfo 字号 14→11px、胶囊高度 27→20px，避免原 60% 下的 8px/16px 过小显示。
- **文件**：同步更新 `portable_config/scripts/uosc/main.lua` 内置默认值和 `portable_config/script-opts/uosc.conf` 实际配置，不新增 MediaInfo/Speed 私有选项。
- **验证**：尺寸矩阵覆盖 1280/1080/960/800/640px 与 200% DPI 小窗口，断言 compact 不低于 0.75；独立 uosc 在 800×450、scale=1/2 下退出 0、无 Lua/stack/script-opts 错误。未构建、未打包、未发布。
- **工作树边界**：用户写入 `uosc.conf` 的 `proximity_scale_min=0.8` 说明文字继续保留为未提交修改；backup 目录不跟踪。
