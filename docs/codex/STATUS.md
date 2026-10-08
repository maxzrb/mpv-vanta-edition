# STATUS.md — MPV 便携配置项目

## 当前状态快照

| 项目 | 状态 |
|------|------|
| **项目** | MPV 便携播放器个人配置（fork from gaoxing64/MPV-lazy-full v2.0.0） |
| **用户核心优先级** | SDR／HDR 色彩显示准确优先；用户对超分／补帧不感兴趣，增强仅作为现有可选模块维护，不以模型数量或增强效果定义项目价值 |
| **分支** | `master` 与 `origin/master` 同步；`v1.5.7` 标签已推送，发布已完成 |
| **最新发布提交** | `7e302f8`（tag: `v1.5.7`，已推送） |
| **工作区** | 发布前输入审计与707项可回退归档完成；起播／IPC打开／最小化抬窗修复与回归通过；此前色彩／HQ／滤镜改动保留；尚未提交／打包／发布 |
| **MPV 核心版本** | 本地 v0.41.0-1107-g36bf3d529（shinchiro 20261008；FFmpeg N-127242-g5d4755f7d；libplacebo v7.374.0 / 0d043c7，含 99e80abd 浮点截断修复）；未发布 |
| **项目版本** | v1.5.7（已正式发布）；下一版 v1.6.0 已由用户确认，尚未构建 |
| **上次操作** | 2026-10-08 15:29 用户确认下一版v1.6.0，并授权按流程发布正式Release；准备与回归完成，等待3.2升级Gate决定 |
| **当前排查** | 8K48软解优化已按用户要求搁置，不自动继续；下一版v1.6.0已确认，安装器独立版本尚未改；核心与运行时升级命中发布流程3.2 Gate，本次Gate已获用户一次性豁免，正式发布构建与校验进行中 |
| **自定义脚本** | quality.lua、quality_status.lua、color-target.lua、display-color.lua＋display-color-native.lua、hdr-mode.lua、stats.lua＋system_metrics.lua、startup-format-logos.lua（保留用户定制） |

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
│   └── scripts/stats.lua     # yosh-wang 汉化版统计信息脚本（自动翻译+CPU/GPU 监控）
├── vs-plugins/, vs-scripts/  # VapourSynth (gitignore)
├── Faster-Whisper-XXL/       # AI 字幕 (gitignore)
├── lua/, socket/, mime/      # Lua 运行时
├── installer/                # 安装/更新脚本
└── settings.xml              # 更新器配置 (未跟踪)
```

## TODO

- [x] 下一版本发布准备、可回退清理及起播前台显示修复（2026-10-08）
- [ ] 发布执行：用户确认版本及3.2 Gate处理后再构建；02第三方插件／模型分发许可沿用已有待补证事项，不以输入审计替代授权
- [ ] 搁置：本机8K48 AV1软解性能优化；仅用户明确恢复后继续

- [x] 删除低功耗档／默认 HQ／菜单排序／直属清空；SDR ACM 与 ICC 分工、FP16 最终截断核心修复、线性缩小及原始读回验证（2026-10-08）

- [x] 色彩原生状态／NaN去重、CCD同帧率完成事件、真实精度详情与K7补丁覆盖恢复回归（2026-10-08）
- [x] PQ／HLG独立GPU数值参考、18组交接三轮20秒／54次启停、资源观察、带音频组合与HDR状态回归（2026-10-08）
- [ ] 可选优化候选：RIFE首次初始化的短停顿／音频欠载，高分辨率CCD并行效率和内存；需独立测量，不自动降质或增加播放前核验

- [x] 修复负／缺失帧时长导致的短片EOF撤链；保留有效VFR与EOF占位，CCD＋RIFE循环／长片时钟／跳转通过

- [x] 色彩精度核查及3FPlayer固定提交源码对照（2026-10-07）；区分普通FP16渲染、滤镜精度、最终输出及面板
- [x] 修正RIFE／DRBA／超分／CCD等固定709矩阵与范围，兼容现代／旧桥接属性；601／709／2020 NCL软件回归通过
- [x] 通用包装层保留可桥接整数YUV高位深与色度；模型IO精度及SVP兼容格式保持原样；本机DML16bit实播通过
- [x] 补完整配置SDR／广SDR像素参考与HDR静态组合回归、模拟FP16输出；真实屏幕测量不作为本轮完成条件

- [x] 播放体验后续修复：裁剪硬解误报与实际旁路、SVP 目标满足时原帧保留、低帧率三轮回归、简洁滚动状态及播放性能迁至其它（2026-10-07）

- [x] 恢复所有滤镜一键请求，移除解锁、普通流程组件扫描与模拟试跑，分离 RIFE 后端
- [x] 修复色彩事务／恢复失败重试／外部覆盖／免重建／显示身份偏好与用户设置所有权
- [x] 增加 RIFE 4.26／Heavy，更新 K7sfunc 1.8.1、VSORT v15.16 与 zsmooth 0.20.0，归档重复旧 SVP
- [x] 完成三轮硬解／缩放／峰值分析／长 GOP／起播对比，推广 auto-safe，保留手动性能档与实验零复制
- [x] 本轮结果报告、摘要 JSON、回退快照与 HandShake 记录更新（2026-10-06）
- [ ] 可选后续实机补充：真实HDR色准、NVIDIA／Intel、DV与更多素材（不作为本轮软件验收条件，未以模拟结果替代）

- [x] `settings.xml` 已加入 `.gitignore`
- [x] 根据个人需求定制 mpv.conf
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

## v1.5.2 发布前置检查清单（2026-08-13）

### 3.1 工作区与 Git 状态
- [x] `git status --short --branch`：`master` 与 `origin/master` 同步（0 领先/0 落后）；`git fetch origin` 后无远端新改动。
- [x] 未提交改动（按逻辑整理中）：VantaInstaller v0.3.2 系列源码（Aria2 Next 下载核心、安装前 SHA-256 校验、测速样本、下载目录刷新、版本号动态化、默认注册多实例、关联显示名）、`installer/associations` 三个关联脚本显示名、`portable_config`（一键更新撤下 + 维护者审计工具降级 + stats 解码方式）、`docs/cf-github-proxy-worker.js` 与 `tools/`（下载站 KV 自动快照）、AGENTS/CLAUDE/.gitignore、STATUS/工作进度/版本迭代/README。
- [x] 未跟踪临时文件：`docs/worker代码备份.js`、`portable_config/backup/`、`portable_config/script-opts/backup/` → 已加入 .gitignore（不提交）；`VantaInstaller/src/Vanta.Core/Assets/`（aria2-next.exe + COPYING）与 `THIRD-PARTY-NOTICES.md` 为需提交的授权文件。

### 3.2 发布内容影响评估（大改动 Gate）
- 本次发布内容 = mpv 版本 Z+1 至 v1.5.2；VantaInstaller 附属工具 v0.3.2（功能/界面/版本迭代，流程明确不触发 Gate）；关联脚本显示名文本；下载站 Worker（独立 Cloudflare 部署，不进 01~05 包）。
- 公开包数量/编号/命名/覆盖顺序：**不变**（01~05）。构建脚本 `build-*.ps1`：**无改动**。mpv 核心/运行时：**无升级**。大型资源增删：**无**。安装/启动方式结构：**无变化**（仅 FriendlyAppName 显示名文本）。VantaInstaller 构建方式/产物形态：不变（单文件自包含 publish）。分卷规则：不变。
- 第三方版权边界：Aria2 Next 2.5.5（GPL-2.0-or-later）随 VantaInstaller 内置，已新增 THIRD-PARTY-NOTICES.md 与 COPYING.txt 资源；不进 01~05 公开包，不属公开包 Gate。
- 结论：**不触发大改动 Gate**，走标准流程。

### 3.3 文档与记录检查
- [x] STATUS.md 本清单已更新；[x] version/工作进度.md 已追加发布准备条目；[x] version/版本迭代记录.md 已建立 v1.5.2 当前版本并归档 v1.5.1；[x] README.MD 已更新 VantaInstaller v0.3.2 与关联显示名。

### 3.4 功能验证
- [x] 完整配置播放测试视频：无 [e]/[f] 错误行；uosc、dyn_menu、startup_format_logos、gpu-next 等正常加载（startup_format_logos 的 "Subprocess failed: killed" 为 2 帧测试截断，非真实错误）。
- [x] Lua 语法检查：portable_config/scripts + script-modules 共 138 个脚本 loadfile 全部通过（FAIL 0）。
- [x] `git diff --check`：通过（仅 CRLF warning，无尾随空格错误）。
- [x] 脚本配置与 script-opts 一致，UTF-8 无 BOM、LF 换行。

---

## v1.5.0 发布前置检查清单（2026-08-11）

### 3.1 工作区与 Git 状态
- [x] `git status --short --branch`：`master` 领先 `origin/master` 6 个提交（0721fb6 / 5335a39 / d40c3dd / 36e7738 / c0e3742 / 5e8486e）；`git fetch origin` 后无远端新改动。
- [x] 未提交改动：`portable_config/script-opts/uosc.conf`（注释更新 + proximity_scale_min=0.8 行尾随空格）、`发布流程.md`（第 3 条警告语强化）；`portable_config/backup/`、`portable_config/script-opts/backup/` 未跟踪（打包脚本会排除，不提交）。
- [x] 待提交整理：uosc.conf 尾随空格清理后提交（当前 0 行尾随空格）；发布流程.md 强化条款已纳入提交（f141442）。

### 3.2 发布内容影响评估（大改动 Gate）
- 命中 Gate 项：mpv 核心切换（dyphire → shinchiro 20260811）、构建脚本重构（build-01~05 + build-all-packages.ps1）、安装/关联方式变化、内置 HarmonyOS Sans SC 字体（01 携带）、VantaInstaller 0.3.0。以上均为用户此前明确要求并已批准/测试的既定内容。
- **新发现（需用户决策）**：`build-01-base.ps1` 运行时 DLL 清单仍为 dyphire 时代，包含 `vulkan-1.dll`（根目录不存在，被静默跳过）、不含 shinchiro 必需 `d3dcompiler_43.dll`（根目录已有 4.48MB）→ 01 包将缺 D3D11 编译依赖，需在脚本清单补入该文件（构建脚本修改，命中 Gate，待用户确认）。
- VantaInstaller 0.2.0 → 0.3.0：附属工具版本迭代，不触发 Gate；csproj 已是 0.3.0，publish 已有 v0.3.0.exe，源码无改动可沿用。

### 3.3 文档与记录检查
- [x] STATUS.md 本清单已更新；[x] version/工作进度.md 已追加；[x] version/版本迭代记录.md 已更新 v1.4.3 → v1.5.0；[x] README.MD 已更新 VantaInstaller v0.3.0。

### 3.4 功能验证
- [x] 完整配置 idle 启动 6 秒：无 [e]/[f]/error，uosc、uosc_danmaku、startup-format-logos、webui、stats、lsfg_control 等全部正常加载。
- [x] Lua 语法检查：portable_config/scripts + script-modules 共 138 个脚本 loadfile 全部通过（FAIL 0）。
- [x] `git diff --check`：通过（仅 发布流程.md CRLF warning，无尾随空格错误）。
- [x] 脚本配置与 script-opts 一致，UTF-8 无 BOM、LF 换行（uosc.conf 行尾空格待清理）。

---

## 会话日志
### 2026-08-13 私用全量包内置 VantaInstaller + 发布流程统一候选目录

- `build-full-private.ps1`：从 `release/` 按版本号取最新 VantaInstaller 打包到私包根级（无候选告警跳过），私包 README 同步。
- 《发布流程.md》（用户授权）：VantaInstaller 候选先移入 `release/` 再统一上传；4.1/4.2/5/7 更新。
- 私包重建 `mpv-full-private-v1.5.2.7z`：根级含 v0.3.2 exe（SHA-256 与 `release/` 候选一致 `52A186D9...`），新 SHA-256 `D444AE10...1766`；7z t 通过；仅本地保留。
- 最新 v0.3.2 候选已放入 `release/`（与远端一致）。

### 2026-08-13 VantaInstaller 启动自动检查自身更新 + 下载徽标

- `UpdateService.CheckInstallerUpdateAsync`（找 VantaInstaller-win-x64-v*.exe 资产、解析版本、比较）；MainViewModel 启动异步检查 + `OpenInstallerUpdateCommand`；MainWindow 左下角版本号右侧徽标按钮。
- 验证：版本解析/比较 5 用例全过；Debug/Release 启动探针存活；提交 `c3ac48e` 推送；重建 v0.3.2 并 `--clobber` 上传（SHA-256 `52A186D9...7D7C8A`，与远端一致）。当前最新即 v0.3.2，徽标不自我提示。

### 2026-08-13 v1.5.2 资产重传（evafast 可调 + README 加固随发布生效）

- 提交 `57b1be1`（feat）+ `3a82d18`（docs）推送；01/05 重建 + VantaInstaller v0.3.2 重建。
- `gh release upload v1.5.2 --clobber` 覆盖上传 01、05、exe；远端 7 资产大小与本地一致、无重复、无私包；02/03/04 未变。
- 新校验和：01 `7B7F0AE9`、05 `0E3743B0`、exe `6AB6645C`，已写入版本迭代记录"补充重传"节。

### 2026-08-13 v1.5.2 之后：01/05 README 加固 + evafast 方向键快进选项（未发布）

- **README 核实纠正**：此前"01/05 包从不携带根级 README"为解析误判（`7z -ba` 正则漏匹配 5 字段行）；`7z l -slt` 确认 v1.5.1/v1.5.2 包一直含根级 README.MD。构建脚本加固（显式复制 + 打包前校验 + 归档内验证），本地重建 01/05（含最新安装说明）。
- **evafast 可调**：`evafast.lua` 新增 `subs_limit`；VantaInstaller 新增 EvafastConfigService，「mpv 调节」卡片内新增「方向键快进」分组（无字幕/有字幕倍速滑条 + 字幕限速开关），保存并入「保存 mpv 设置」按钮。
- **验证**：VantaInstaller Debug 构建 0 警告 0 错误；evafast.lua LuaJIT 通过；01/05 根级 README 确认存在且最新。
- **状态**：未构建全套、未上传；本地重建 01/05 新校验和已记录（6A4D.../1A34...），待用户决定重新发布或并入下一版本。

### 2026-08-13 v1.5.2 发布完成（流程 6~8）

- **构建**：`build-all-packages.ps1 -Version 1.5.2 -IncludePrivate` 一次通过（约 25.7 分钟）；VantaInstaller v0.3.2 Release 重建（最新源码，SHA-256 `7307B41147B4FFE30B47E2E107391F5169BAD8CD7723EF6BDA4915094B734808`，启动探针 4 秒存活）。
- **验证**：7z t 全过；SHA-256 全部写入版本迭代记录；门禁通过（01 含 script-assets/fonts/ffmpeg/.vanta-version=1.5.2；05 全排除；04 仅 Lossless.dll+GPL；顶层无 release/build/tmp/.git/__pycache__）；01 包内 `.vanta-version` 逐字节 `1.5.2`，根目录同步。
- **提交与推送**：功能/文档 4 提交 + 构建记录 `1987f90` + 安装说明 `52a82fd`；标签 `v1.5.2` 推送；master 与 origin 同步、工作树干净。
- **Release**：https://github.com/maxzrb/mpv-vanta-edition/releases/tag/v1.5.2 （正式）；7 个公开资产大小与本地 SHA-256 一致、无重复资产、无私包；误传 release-notes 资产已删。
- **安装说明与时俱进**：README/Release 说明以 VantaInstaller 为推荐安装方式，手动解压降为备选；01/05 包内从不携带根级 README（历史行为），未触发重建。

### 2026-08-12 v1.5.1 发布完成（流程 6~8）

- **构建**：`build-all-packages.ps1 -Version 1.5.1 -IncludePrivate` 一次通过，耗时约 21.6 分钟；01 包首次携带 `ffmpeg/ffmpeg.exe`（98.3MB，7z 后 129.9MB）。
- **验证**：7z t 全过；SHA-256 全部写入版本迭代记录；门禁扫描通过（01 含 script-assets/fonts/ffmpeg/.vanta-version=1.5.1；05 全部排除；04 仅 Lossless.dll + GPL 源码）；根目录 `.vanta-version` 已同步 1.5.1；VantaInstaller v0.3.0 沿用（SHA-256 与 v1.5.0 一致）。
- **提交**：`b2511ca`（发布前置记录）、`327728b`（构建记录/校验和）→ 标签 `v1.5.1` → 推送 master+tags。
- **Release**：https://github.com/maxzrb/mpv-vanta-edition/releases/tag/v1.5.1 （正式，非草稿/预发布）；7 个公开资产上传完毕，大小与本地 SHA-256 逐字节一致、无重复资产、无私包。
- **状态**：发布完成；master 与 origin 同步、工作树干净。

### 2026-08-12 v1.5.1 发布前置检查（流程 3.1~3.4）

- **版本号**：用户指定 v1.5.1（Z+1，小功能修复补足；杳知 8.12 跟进与后瞻检测优化）。
- **3.1 Git 状态**：`master` 与 `origin/master` 同步（0/0）；仅 `docs/codex/STATUS.md` TODO 清理未提交；backup 目录继续不跟踪。
- **3.2 大改动 Gate 评估**：本次发布内容 = 后瞻单路/双路统一、40s 快速深探针、第二确认窗、采样分辨率提升、随包 ffmpeg（均为 8/12 已提交并推送的功能/脚本改动）。**01 包首次携带 ffmpeg（约 +26MB 压缩）属"大型资源增删/包体积变化"**，但为用户 8/12 明确要求并亲自提供文件、且本次指令再次确认（"看一下 ffmpeg 有没有进入 01 包的打包脚本，然后执行发布流程"），视为用户已批准的既定内容；包结构 01~05 不变、构建脚本无新改动。其余项（VantaInstaller 0.3.0 沿用、README/发布流程为文档同步）不触发 Gate。
- **3.3 文档检查**：STATUS/工作进度/版本迭代/README 将在发布各阶段同步更新（本记录即 3.3 前置项）。
- **3.4 功能验证**：Lua 130/130 语法通过；完整配置 idle 启动无 `[e]/[f]/error`（auto_profiles 条件评估为 v 级正常提示）；`git diff --check` 通过；ffmpeg 已确认在 `build-01-base.ps1`（`Invoke-CopyTo @("ffmpeg")`，根目录 `ffmpeg/ffmpeg.exe` 98.3MB 存在）。
- **状态**：前置检查通过，准备构建。

### 2026-08-12 15:08 会话：杳知 8.12 跟进收尾（提交+推送+文档）

- **提交**：起播 Logo 后瞻单路/双路统一、40 秒快速深探针、第二确认窗、随包 ffmpeg 等共 16 个提交（`1259500`→`549468a`）已提交并推送 `origin/master`，工作区干净（backup 目录继续不跟踪）。
- **构建脚本适配核验**：build-01 已含随包 ffmpeg 复制（`Invoke-CopyTo @("ffmpeg")`，缺失跳过保护）；01/05 均递归排除 backup 目录；`script-modules/startup-logo-bounds.lua` 随 portable_config 整目录复制；02/03/04 不涉及，无需改动。
- **文档**：README 01 包描述补"随包检测专用 ffmpeg"；《发布流程.md》4.2 产物清单 01 行与第 5 节门禁清单补 ffmpeg 核验项；版本迭代记录新增"未发布：v1.5.0 之后的累积改动（杳知 8.12 跟进）"；工作进度补收尾记录。
- **镜像站**：mirror.loliland.cn 下载服务已从服务器 Caddy 关闭（保留 emby/media），服务器上 4.3G release 副本已清理；`vanta-web` 防火墙链保留保护 emby 回源。
- **状态**：待提交上述文档收尾改动；未构建、未打包、未发布。

### 2026-08-12 14:25 会话：单路/双路后瞻逻辑统一（未提交）

- **用户约束**：单路与双路必须是同一方案的不同并发度，不能在采样点、判定门槛或回退策略上分叉。
- **重构**：合并为 `run_common_plan(concurrency)`；两种模式共同使用固定 40 秒快速深探针、相同近端/深端补测计划、黑边优先、无黑边门槛、视觉回退和锚点冻结。唯一模式差异为困难补测每批启动 `1` 或 `2` 个 ffmpeg。
- **配置统一**：正式键改为 `encoded_bar_fast_probe=40`；旧 `encoded_bar_parallel_fast_probe` 作为隐藏兼容键保留，值 >=0 时仍可覆盖，避免已有配置失效。菜单名称改为“后瞻方案·单路检测（实验性）/双路检测（实验性）”。
- **真实样片一致性**：铃芽 AV1：单路 1.71/1.74 秒，双路 1.78/1.75 秒，均完整画幅；Radioactive Emergency 窄黑边：单路 1.36/1.37 秒，双路 1.36/1.38 秒，均识别上下黑边。两类常见路径只需快速深探针，因此两种模式实际峰值均为 1。
- **困难回退**：构造 40 秒探针为黑屏、其他时段为全幅内容的 80 秒视频，强制进入补测。单路约 1.18~1.22 秒、峰值 1；双路约 0.89~0.93 秒、峰值 2；结论均为无黑边，残留 0，无 Lua 错误。
- **验证**：`git diff --check` 通过；未构建、未打包、未提交。

### 2026-08-12 14:18 会话：AV1 稀疏发行方片头快速深探针（未提交）

- **样片**：`D:\read\铃芽之旅...aomav1...webm`。旧双路模式在 3~10 秒得到三帧全幅亮画面、10~30 秒得到黑屏/稀疏字幕，六样本耗尽后仍无法形成后窗共识，实跑 9.5 秒仍未结算；问题不是单帧 AV1 seek 本身（约 0.4~1.4 秒），而是确认窗恰好落在长发行方片头。
- **时间窗**：深确认窗由 10~30 秒改为 30~75 秒，避开常见发行方黑屏/字幕。双路模式在首帧稳定时预启动后瞻，不再等三次 screenshot-raw 结束；当前帧若先发现可信黑边仍可取消后瞻。
- **快速深探针**：新增 `encoded_bar_parallel_fast_probe=40`。双路先检测固定 40 秒深帧；若其内容充分，黑边扫描有结果则采用黑边，无结果则直接确认完整画幅；只有该深帧仍稀疏/黑屏才进入原随机补测。固定点避免随机落到 AV1 慢 GOP。
- **探针基准**：40 秒：AV1 平均 1.28 秒、HEVC 0.94 秒；50 秒：1.27/1.43；60 秒：0.76/2.26。默认选 40 秒作为综合最优；偏重 AV1 用户可手动改 60。
- **最终验证**：铃芽双路三次检测结算 1.26/1.27/1.35 秒，含配置 `delay=0.45` 后徽章实际显示 1.73/1.75/1.80 秒；结果均为完整画幅，ffmpeg 残留 0，无 Lua 错误。窄黑边 HEVC 样片 40 秒探针约 0.91~0.97 秒正确识别黑边。
- **放弃方案**：两个深 AV1 seek 同时并发会争抢资源（铃芽 4.14~7.19 秒）；复用低覆盖当前帧投票不成立且会触发 fallback（3.37~9.42 秒）；降低每进程线程数平均更慢。以上均未保留。
- **状态**：`git diff --check` 通过；未构建、未打包、未提交。

### 2026-08-12 13:56 会话：后瞻单路/双路并发可选模式（未提交）

- **模式设计**：保留 `mode=current` 为“后瞻方案·单路（实验性）”，新增 `mode=parallel` 为“后瞻方案·双路并发（实验性）”；旧配置无需迁移。uosc 菜单“其它 > 起播格式 Logo > 检测模式”已加入两个独立勾选入口，杳知视觉与不检测模式保持不变。
- **并发调度**：双路模式按（近端1+远端1）→（近端2+远端2）→（近端3+远端3）成对执行，每轮最多两个 ffmpeg；任一路命中可信黑边立即结算并通过 `mp.abort_async_command` 取消同组另一请求，回调补充临时文件清理。单路模式继续交错串行。
- **样片对比**：`Radioactive Emergency S01E04` 从 13 秒歧义起点各测 3 次。单路日志时间 3.94 / 3.17 / 3.30 秒，平均约 3.47 秒，峰值 1；双路 2.88 / 3.33 / 2.44 秒，平均约 2.88 秒，峰值 2。六次均正确识别上下 0.0556，结算后 ffmpeg 残留 0，无 Lua 错误。
- **无黑边回归**：35 秒 1080p 合成片，单路约 1.98 秒、双路约 1.61 秒，均完成六样本并正确确认无黑边；峰值分别为 1/2，残留均为 0。
- **文件**：修改 `startup-format-logos.lua`、`startup_format_logos.conf`、`input.conf`；HandShake 记录同步更新。`git diff --check` 通过。未构建、未打包、未提交。

### 2026-08-12 13:50 会话：确认窗交错采样加速（未提交）

- **原因**：上一版虽然把峰值降到单 ffmpeg，但必须串行耗尽 3 个近端黑屏/不可信样本，才开始 10~30 秒确认窗；样片 13 秒歧义起点因此约需 6 秒。
- **优化**：把执行顺序改为近端1→远端1→近端2→远端2→近端3→远端3；第一帧仍保留 3~4 秒近端快速响应，若不可信则第二帧立即寻找更后的正片。仍为单进程、4 线程串行，任一可信黑边立即停止。
- **样片验证**：13 秒歧义起点重复 3 次，均仅解码两帧并正确识别上下 0.0556；日志完成时间 3.18 / 3.34 / 3.83 秒，较约 6 秒缩短 36%~47%；峰值均为 1 个 ffmpeg，无 Lua 错误。
- **无黑边回归**：35 秒 1920×1080 合成片按交错顺序完成六样本，约 1.8 秒正确确认无黑边，峰值 1 个 ffmpeg，无错误。
- **边界**：若继续追求约 2 秒，需要有限并发或硬件解码，会重新提高起播峰值或引入跨显卡/解码格式兼容风险；当前方案是低峰值与响应速度间的稳健折中。未构建、未打包、未提交。

### 2026-08-12 13:44 会话：降低后瞻检测起播性能峰值（未提交）

- **瓶颈**：旧后瞻每窗并发启动 3 个 ffmpeg，各自打开文件并软件解码一帧 4K DV/HEVC；进入第二确认窗会再并发 3 个。响应快，但起播瞬间 CPU、磁盘与进程峰值较高。
- **基准**：样片 24 秒单帧解码，自动线程平均墙钟 1.13 秒 / CPU 5.54 秒；4 线程平均 1.22 秒 / CPU 3.22 秒。4 线程只慢约 0.09 秒，CPU 工作量下降约 42%。
- **优化**：新增 `encoded_bar_ffmpeg_threads=4`；同一时间只运行一个 ffmpeg，按采样时间串行短 seek；任一帧发现可信黑边立即结束本窗，不再解码剩余样本。没有改成连续解码到最晚时间点，避免为了取三帧连续解码十几秒 4K 视频。
- **验证**：样片从 20 秒黑屏启动，首个样本命中时约 2.9 秒完成；从 13 秒歧义段启动，首窗不可信后进入确认窗，约 6.0 秒正确识别上下 0.0556；两者实测峰值均为 1 个 ffmpeg。35 秒 1920×1080 无黑边合成片经过两窗六样本约 2.1 秒正确确认无黑边，峰值仍为 1。无 Lua error/stack traceback；`git diff --check` 通过。
- **取舍**：歧义片头显示徽章可能比三路并发晚约 2~4 秒，但播放器起播更平稳；常见首帧命中只解码一次。未构建、未打包、未提交。

### 2026-08-12 13:37 会话：后瞻方案双时间窗修复（未提交）

- **样片**：`F:\download\Radioactive.Emergency.S01E04.We.Always.Have.Options.2160p.NF.WEB-DL.DDP.5.1.Atmos.DV.H.265-BlackTV.mkv`（DV Profile 5，3840×2160）；正片为上下约 120px 窄黑边，片头在全幅亮画面、稀疏暗画面和黑屏之间切换。
- **根因**：旧聚合规则允许首窗任意一帧内容充分的全幅片头直接确认“无黑边”，置信门槛低于“有黑边”，导致徽章过早锁到右上角；640×360 分辨率不是主因，该分辨率能稳定测得上下各 20px（0.0556）。
- **修复**：保留 3~10 秒首窗随机三采样；首窗发现可信黑边即采用，只有无黑边/不可信时才进入 10~30 秒分层随机三采样。后窗任一可信黑边优先；确认无黑边需至少两帧共识；仍无可信结论才回退当前帧复检。徽章依旧仅在结论确定后显示并冻结，不会显示后跳位。
- **配置**：新增 `encoded_bar_confirm_lookahead=30`、`encoded_bar_confirm_samples=3`，确认终点不超过视频时长；前者小于等于首窗终点可关闭第二窗。
- **验证**：离线 0.5 秒步进分析 3~30 秒共 55 帧（黑边 21 / 无边 19 / 不可信 15）；隔离 mpv 从 20 秒黑屏启动，首窗三帧均识别 0.0556；从 13 秒歧义场景重复三次均在约 4 秒正确锁边；强制首窗单个不可信样本后，第二窗同时遇到全幅画面与窄黑边，仍在约 5.2 秒正确锁边。无 Lua error/stack traceback；`git diff --check`、UTF-8 无 BOM、LF 检查通过。
- **Git**：`master` 领先远端 15 个既有提交；本次修改 `startup-format-logos.lua` 与 `startup_format_logos.conf` 尚未提交；backup 目录保持不跟踪。未构建、未打包、未推送。

### 2026-08-12 会话：v1.5.0 发布结果（关机中断恢复）

- 2026-08-11 晚 `gh release create v1.5.0`（正式）成功；上传公开资产时意外关机，关机前完成 01/04/05/VantaInstaller-v0.3.0 四资产。
- 2026-08-12 恢复：`gh release upload` 补齐 02 分卷与 03 FW 包（约 12 分钟）。
- 最终核对：远端 7 个公开资产全部 `uploaded`，SHA-256 与本地逐字节一致（01 204B98DCC… / 02.001 220B18209… / 02.002 E252F55C0… / 03 2C38210A4… / 04 3F0BD15C2… / 05 7CA8AF172… / VantaInstaller 575D34155…），无重复资产，无私包；`mpv-full-private-v1.5.0.7z` 仅本地。
- Release：https://github.com/maxzrb/mpv-vanta-edition/releases/tag/v1.5.0
- 收尾：版本迭代记录补充发布结果、工作进度追加、本文件快照更新；随后提交 `docs: record v1.5.0 release results` 并推送。

### 2026-08-11 会话：v1.5.0 发布构建（主版本提升 + VantaInstaller v0.3.0）

- **前置检查**：Git 同步（fetch 后无远端新改动）；138 个 Lua 脚本语法全过；完整配置 idle 启动无 error；缺漏文件核验发现唯一缺漏——01 运行时清单 vulkan-1.dll（dyphire 残留、根目录不存在）缺 shinchiro 必需 d3dcompiler_43.dll（已批准修复）。
- **提交**：`d9e76e2` build-01 Base 运行时 DLL 适配 shinchiro（d3dcompiler_43.dll）；`307950b` uosc 渐隐下限注释补充（值保持 0.8）；`f141442` 发布流程强化全功能包校验条款 + README VantaInstaller v0.3.0 + 本文件前置检查记录。
- **构建**：`build-all-packages.ps1 -Version 1.5.0 -IncludePrivate` 一次通过，01~05 + 私包共 7 个归档（约 8.17GB，私包 4204MB）；私包合并 01→05 + 完整 Lossless Scaling，不受构建脚本拆分影响。
- **验证**：7z t 全部 Ok；SHA-256 全部写入版本迭代记录；门禁扫描无顶层 release/build/tmp/.git、无 .pyc/.log/.pdb/.tmp/.bak/__pycache__；01 含 script-assets/fonts/d3dcompiler_43.dll/mpv.exe、不含 vulkan-1.dll/window_state.conf、`.vanta-version` 逐字节=1.5.0（无 BOM/换行/v）；05 不含 .vanta-version/script-assets/window_state.conf/fonts；04 仅 LSFG Layer + Lossless.dll + GPL 源码；根目录 `.vanta-version` 已同步 1.5.0。
- **VantaInstaller v0.3.0**：csproj=0.3.0，源码最新修改 19:34 早于产物 20:03，沿用现成构建；启动验证通过；SHA-256 `575D341555B990B3FCF7A1BE9F43030AB046AD04EC333F8FB0760CEBC2C32DF7`。
- **待办**：提交构建记录（含 .vanta-version=1.5.0）→ 标签 v1.5.0 → 推送 → 创建 Release 上传 01~05 + VantaInstaller v0.3.0 → 发布后收尾。

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

### 2026-08-11 22:52 会话：音量条复用统一窄窗口缩放

- **实现**：Volume 容器宽度/高度、窗口边缘间距、悬浮背景外扩，VolumeSlider 的配置边框与 100 刻度命中 padding 均改用 `get_controls_scale()`；轨道、把手、数字和静音按钮继续由容器尺寸派生，因此整体与底栏、MediaInfo、Speed 同步缩放。
- **边界**：音量文字描边和全局圆角仍沿用 `state.scale/state.radius`，与底栏按钮一致，避免小窗口把发丝线压得过细；不新增音量专用下限。
- **尺寸**：volume_size=40 时，1280px=40、1080px=34、≤960px=30；200% DPI 的 960 逻辑像素小窗为 60px，统一受 75% compact 下限约束。
- **验证**：尺寸矩阵覆盖 1280/1080/960/800/640px 与 200% DPI 小窗口；独立 uosc 在 800×450、scale=1/2、volume=right 下退出 0，无 Lua/stack/script-opts 错误。未构建、未打包、未发布。
- **工作树边界**：用户的 `proximity_scale_min=0.8` 说明文字继续保持未提交；backup 目录不跟踪。

### 2026-08-13 00:15 · VantaInstaller v0.3.1 镜像更新收尾

- **修改**：`MirrorRegistry.All` 移除 `ghfast.top`、`mirror.ghproxy.com`、`ghproxy.homeboyc.cn`；补入 `gh.xxooo.cf`；列表末尾固定加入 `dl.loliland.cn`（AerithDream 下载加速，自建）。
- **验证**：针对 v1.5.1 Release 资产的 Range 测试中，官方、`gh-proxy.com`、`ghproxy.net`、`gh.xxooo.cf`、`dl.loliland.cn` 均返回 `206`、正确 `Content-Range` 与 `Accept-Ranges`；未将 DNS/TLS/403/404 或短窗口吞吐不完整的候选纳入注册表。
- **安装器**：`VantaInstaller` 版本提升至 v0.3.1，镜像探测与更新请求 User-Agent 同步；Release 单文件构建 0 警告、0 错误，最终产物 SHA-256 为 `04F43D321755F44DA8BC1CF834981FD4BCD74E9EB2A5AFA88C6EC83D2F1902B0`。
- **发布边界**：mpv v1.5.1 包和公开 Release 未改动；README 仍指向当前公开的 v0.3.0，v0.3.1 仅作为本地待附加安装器产物记录。
- **Git**：本次源码与记录改动待提交；`portable_config/backup/`、`portable_config/script-opts/backup/` 为既有未跟踪目录，继续排除。

### 2026-08-13 01:35 · VantaInstaller v0.3.2 下载体验与测速样本更新

- **下载队列**：修复下载中开始按钮因异步命令默认禁止并发而灰掉的问题；StartDownloadCommand 允许并发触发，下载进行中勾选新资产并再次点击即可追加队列。排队项可取消勾选，停止只清理当前选中/排队/活动项目的未完成残留。
- **实时速度**：Aria2Service 解析 aria2 摘要的 DL: 字段并发出速度事件；资产行展示单项速度，进度条右侧展示总速度，完成/失败/停止时清零。
- **测速样本**：ProbeMirrorsAsync 每次重新查询最新正式 Release，固定选择 05-mpv-config-*.7z；当前 API 样本为 05-mpv-config-v1.5.1.7z。用户最终确认采用最新 Release 的 05 包，不再使用 Base 包样本。
- **Aria2 调整**：加入 --no-conf、连接数/重试/超时/断点续传/无预分配及稳定输出参数；没有直接将 Aria2 Next 二进制加入包，避免未经确认改变运行时与许可证边界。Motrix Next 官方实现采用 Aria2 Next sidecar、持久会话和 RPC 管理，与当前按资产启动 aria2c 的轻量实现存在架构差异。
- **验证**：dotnet build -c Release --no-restore 与 dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:EnableCompressionInSingleFile=true 均通过，0 警告、0 错误；启动探针 4 秒存活后按 PID 回收。VantaInstaller-win-x64-v0.3.2.exe 大小 67,652,806 字节，SHA-256 BC9E75147ADDA714193DA0AF24AA261570760BCA458961194A05643D7E2A781D。
- **发布边界**：未执行 mpv 包构建、未上传 Release；mpv v1.5.1 与公开安装器 v0.3.0 不变。源码/记录待提交；两个 backup 目录继续保持未跟踪。

### 2026-08-13 10:43 · VantaInstaller 下载核心替换为 Aria2 Next

- **故障根因**：复现旧 aria2 1.37.0 在 `--max-connection-per-server=64` 下立即退出；旧核心允许范围仅 1–16，因此此前对齐 Motrix Next 的 64 连接参数反而令所有下载失败。
- **核心替换**：内置 Aria2 Next 2.5.5 Windows x64 官方资产，首次下载时释放到 `%LOCALAPPDATA%\VantaInstaller\engines\aria2-next-2.5.5`；缓存复用和释放完成后均校验 SHA-256 `554F2F81CA53731DC9E01710CFB16081A34759F3276FF16EB4B12656C1B6E5B9`，不再搜索 PATH、旧 aria2 或在线拉取 1.37.0。
- **授权边界**：新增 `VantaInstaller/THIRD-PARTY-NOTICES.md`，GPL-2.0-or-later 全文作为资源嵌入并在引擎目录释放为 `COPYING.txt`；官方二进制未修改。
- **Motrix Next 对照**：采用其当前默认的单文件 64 分片、单服务器 64 连接，并将文件分配改为 `trunc`；保留 HTTP keep-alive。VantaInstaller 继续顺序处理资产队列，避免多个大包各自 64 连接并发争抢带宽；未引入对单文件持续吞吐无实质帮助的常驻 RPC 生命周期。
- **稳健性**：进程参数改用 `ProcessStartInfo.ArgumentList`，消除目录、文件名或 URL 中空格/特殊字符的二次解析问题；所有非零退出码均判定失败并附最近输出，不再把残留的部分文件误判为成功；诊断队列限制为最近 20 行。
- **实测**：最新 05 包完整下载成功（5,114,786 字节，退出码 0）；通过服务层下载 04 包到含空格目录/文件名成功（3,197,223 字节，SHA-256 与 Release 记录一致）；01 包 20 秒短测建立 64 连接，速度由约 1.5 MiB/s 上升至峰值约 7.5 MiB/s。
- **构建**：Release build 与自包含压缩单文件 publish 均为 0 警告、0 错误；启动探针 4 秒存活。最终复构建的 `VantaInstaller-win-x64-v0.3.2.exe` 大小 69,637,539 字节，SHA-256 `E031783BA5A30AA2A965FAB3F04168342917A156E40763A759630224D0B33E8C`。
- **发布边界**：未构建 mpv 包、未上传 Release、未改 mpv v1.5.1；本次安装器源码、二进制资源和记录待提交，两个 backup 目录继续保持未跟踪。

### 2026-08-13 11:22 · VantaInstaller 安装前 SHA-256 风险校验

- **用户规则**：每次安装必须先校验，但校验风险是软拦截；全部通过时直接继续，哈希不一致、文件不可读、文件缺失或无法取得可信摘要时必须提醒，默认取消，用户仍可明确选择忽略风险继续安装。
- **可信来源**：`UpdateService` 读取 GitHub Release API 资产的 `digest=sha256:...`，新增按包版本查询对应 tag 的能力；不维护易过时的内置哈希表。网络/API 不可用或旧 Release 无 digest 时记为缺少可信哈希，同样进入风险确认。
- **校验链路**：`PackageIntegrityService` 使用 4 MiB 顺序异步缓冲逐文件计算 SHA-256；校验位于目标目录创建、升级备份和 7-Zip 解压之前。核心层未提供确认回调时默认拒绝继续，避免命令行或未来入口静默绕过。
- **分卷修正**：修复 `PackageScanner` 的分卷 `Files` 未回写且入口分卷被临时列表重复加入的问题；02 现在准确列出 `.001/.002`，两卷均独立校验。
- **界面**：校验占整体进度前 10%，显示当前文件和文件内百分比；风险弹窗列出每个问题文件和原因，并明确建议重新下载，默认按钮为“否”。用户选“是”后日志记录 `[高风险继续]`。
- **验证**：本地 v1.5.1 的 02 两卷共约 2.6 GiB 均与 GitHub digest 一致，计算约 3.2 秒；字节损坏样本判定 `Mismatch`，无摘要样本判定 `MissingReference`；引擎级拒绝测试得到 2 个风险项，确认目标目录未创建且没有进入解压。
- **构建**：Release build/publish 均 0 警告、0 错误，最终单文件启动探针 4 秒存活；`VantaInstaller-win-x64-v0.3.2.exe` 大小 69,644,904 字节，SHA-256 `3550985CC380678239F28ACC7EC515E39F57E86D8111D600CCC8F504C8E2485F`。
- **边界**：此前 evafast 1.5×/3× 跳变只读确认是字幕限速设计，未修改；未构建/发布 mpv 包、未上传 Release，两个 backup 目录继续不跟踪。

### 2026-08-13 11:24 · 一键更新脚本与着色器功能去留评估

- **范围**：只读审计 `manager.lua`、`manager.json`、`manager-update.ps1`、`input.conf` 入口、构建脚本和现有 manager 缓存；未修改功能文件。
- **安全性**：当前更新器不是直接覆盖器。缺失文件不安装、上游删除不删除本地文件；首次本地/上游不同会保护本地，后续依赖旧上游基线三方合并，覆盖前有备份和冲突候选。uosc、uosc_danmaku、stats、起播 Logo和 Vanta 自定义脚本均不在更新源中。
- **当前实测**：发布构建明确排除 `portable_config/cache`，当前也无 manager state；DryRun 对 17 个源（15 个启用）得到 `UPDATED=0/MERGED=0/PROTECTED=5/ERROR=0`，保护 hdr-mode、trackselect、sub-fastwhisper 和 webui 两个文件。所有源均 `install_missing=false`。
- **风险与价值**：自动三方合并只能证明文本无冲突，不能验证高度定制后的语义、配置和菜单引用；着色器目录与 `input.conf` 菜单强耦合，单独更新同名 GLSL 无整体验证。该功能还依赖包外系统 Git，并会绕过 Vanta 的版本化发布、安装前哈希和回归验证，形成同版本不同内容。当前 DryRun 又无任何实际可更新文件，用户入口价值很低。
- **建议**：不再面向普通用户保留“工具 → 一键更新脚本和着色器”；保留 manager 源码作为维护者上游审计/候选合并工具，默认仅 DryRun，禁用着色器源或拆成独立审计入口。正式脚本/着色器更新只经人工复核后进入 Vanta 版本包。

### 2026-08-13 11:36 · 撤下用户更新入口并降级为维护者审计工具

- **普通入口撤下**：删除 `input.conf` 中 `M` 快捷键及“工具 → 一键更新脚本和着色器”菜单标记；全局检索确认不再存在旧 `manager-update-all` 消息和菜单文本。
- **退出播放器运行面**：原 `scripts/manager.lua` 移到 `script-modules/MAINTAINER-ONLY-WARNING-upstream-audit.lua`，因此不会被 mpv 自动加载；只保留无按键的 `maintainer-audit-upstreams-read-only` 显式消息供维护者按需加载脚本后调用。
- **明确警示命名**：原 `manager-update.ps1`、`manager.json` 分别改为 `MAINTAINER-ONLY-WARNING-upstream-audit.ps1`、`MAINTAINER-ONLY-WARNING-upstream-sources.json`；AGENTS/CLAUDE 结构说明同步更新。
- **默认只读门禁**：PowerShell 无参数时强制 DryRun，不写 state/report/baseline、不合并或覆盖；只有显式 `-ApplyReviewedChanges` 才可应用。`-DryRun` 与应用开关同时使用会报错。DryRun 临时 staging 自动清理，空缓存目录也删除。
- **验证**：LuaJIT 语法、PowerShell 解析通过；evafast 单源默认调用退出 0、`state_written=false/report_written=false/cache_exists=false`；完整 portable_config 播放两帧退出 0，日志无 dyn_menu/stack/load 错误，维护者 Lua 未自动加载，菜单引用为 0。模拟构建复制确认三个新文件会进入 01/05/全量配置，但旧文件均不存在。
- **边界**：未运行 `-ApplyReviewedChanges`，没有更新任何脚本/着色器或建立基线；未构建/发布 mpv 包，前序 VantaInstaller 工作树继续保留。

### 2026-08-13 11:40 · TAB 状态页补齐实际解码方式

- **根因**：`stats.lua` 已读取正确的 `hwdec-current`，但旧代码把 `no` 和空值都过滤，因此软解时整行消失，只剩 `current-gpu-context` 的“图形接口”，容易把渲染 API 误认为硬件解码状态。
- **修复**：视频区始终显示 `解码方式`；`hwdec-current=no` 显示“软件解码”，实际硬解显示“硬件解码（后端）”，初始化前显示“未知（解码器尚未初始化）”。该行不再依赖 codec-desc 是否存在。
- **消歧**：原“图形接口”改名“渲染接口”，明确它只代表 VO/GPU 上下文，不代表解码路径。
- **实测**：同一 H.264 文件在 `hwdec=no` 下属性为 `no`，`auto-safe` 为 `d3d11va`，显式 copy 为 `d3d11va-copy`；完整配置以 `d3d11va-copy` 播放通过，stats 无错误。LuaJIT 语法和 `git diff --check` 通过。
- **边界**：仅修改 `portable_config/scripts/stats.lua` 和记录，未改硬解配置、未构建或发布。
### 2026-08-14 12:57 · stats.lua 更换为 yosh-wang 汉化版（原版备份兜底）

- **需求**：用户提供 https://github.com/yosh-wang/mpv-stats.lua-zh-chinese-translation- ，要求换用其汉化版 stats.lua，原版不删、保留兜底。
- **兼容性核对**：GitHub 版是 mpv 内置 stats.lua（同步上游 de0f2f9，2026-02-10）的「自动翻译模块·全局替换版」，另集成 CPU/GPU 实时占用监控（PowerShell Get-CimInstance / nvidia-smi / typeperf 回退链，全部内置、无额外文件）；binding 名 `stats/display-stats`、`stats/display-stats-toggle`、`stats/display-page-*` 与 input.conf（i/I）及 osc_lazy.lua 底栏按钮联动一致；现有 `script-opts/stats.conf` 选项全部兼容，无未知选项警告。
- **改动文件**：
  - `portable_config/scripts/stats.lua`：GitHub 汉化版（112,050 字节 / 3002 行，UTF-8 无 BOM，CRLF→LF 对齐仓库规范）。
  - `portable_config/scripts/backup/stats-original-20260814.lua`：原版完整备份（68,978 字节，位于脚本目录下相对 backup，随 git 跟踪进包）。
  - `portable_config/mpv.conf` 第 526 行注释补充汉化版来源。
- **功能移植**：新版缺仓库自定义的 `user-data/stats/toggled` 状态同步（osc 底栏/lsfg_control.lua 依赖），已移植两处：`process_key_binding` 末尾按 `display_timer:is_enabled() and not oneshot` 写真实开关状态；启动时初始化为 false。
- **验证**：① 隔离加载 `--no-config --script=` 退出 0、无 Lua 错误；② 集成测试（临时 config-dir 含 `load-stats-overlay=no` + 真实 stats.conf）确认以 `stats` 名称加载、读取 stats.conf、无警告；③ bindlist 模式 stdout 输出中文按键页标题「活动按键绑定」；④ IPC 实测 `user-data/stats/toggled` 初始 false → toggle 后 true → 再 toggle 后 false，与 lsfg_control 预期一致。
- **差异说明**：README 所述 `toggle-stats-page-*`/`toggle-stats`/`close-stats` script-message 接口在当前 main 代码中不存在（本仓库仅用 script-binding，不受影响）；上游 `hwdec-current` 前缀由翻译表 `["HW:"]="硬解："` 覆盖，旧版内联「解码方式」行不再内联，功能等价。
- **边界**：未构建/发布 mpv 包、未上传 Release；仅配置目录改动，backup 目录与临时目录不跟踪。
### 2026-08-14 13:10 · 修复汉化版 stats 软解时解码方式被过滤

- **需求**：用户反馈更换为 yosh-wang 汉化版后，软解时 `hwdec-current=no` 仍被过滤，解码方式整行消失（与 2026-07-27/08-13 记录的旧版同源问题）。
- **根因**：新版保留上游 `append_property(s, "hwdec-current", ..., {no=true, [""]=true}, true)`，excluded 表把 `no`（软解）与空串一并过滤。
- **修复**：移植旧版已验证方案——视频区始终显示 `解码方式:`：`hwdec=no` 显示「软件解码」，有值显示「硬件解码（后端）」如 `d3d11va-copy`，未初始化显示「未知（解码器尚未初始化）」；该行不再依赖 codec-desc 存在，从 `if track and append(codec-desc)` 内移入 `if track` 内。
- **实测**：临时 config-dir + 日志钩子抓取 ASS 输出——软解 `hwdec-current=no` → `解码方式: 软件解码`；`--hwdec=d3d11va-copy` → `解码方式: 硬件解码（d3d11va-copy）`；加载无 Lua 错误。
- **边界**：仅改 `portable_config/scripts/stats.lua`（并记录），未构建/发布 mpv 包。
### 2026-08-14 13:30 · 新旧 stats.lua 同时打包 + 备份改放 scripts/backup

- **用户要求**：① 旧版 stats.lua 留在原文件夹（scripts/）内做相对 backup，不挪到项目根 backup；② 打包脚本确保新旧 stats.lua 都进包。
- **备份位置调整**：`portable_config/backup/stats-original-20260814.lua` → `portable_config/scripts/backup/stats-original-20260814.lua`（未忽略，随 git 跟踪）。
- **打包脚本**：`build-01-base.ps1`（Invoke-CopyConfig）与 `build-05-config.ps1` 在删除全部 backup 目录后，放行 `scripts/backup/stats-original-*.lua` 回构建目录，实现新旧 stats 同时进包；其它备份目录仍排除，不违背发布流程「backup 不进公开包」精神（stats 兜底是用户明确要求）。
- **实测**：临时 `-Version 9.9.9` 构建 01 与 05 包，`7z l` 均确认包含 `portable_config/scripts/stats.lua`（112,702 字节，新版）与 `portable_config/scripts/backup/stats-original-20260814.lua`（68,978 字节，旧版）；私用全量包为 01~05 合并，自动跟随。构建产物与 build/ 已清理。
- **边界**：本次仅提交功能/脚本改动与打包放行逻辑；未实际发布（未定新版本号、未建 Release）。
### 2026-08-14 13:45 · 备份目录两级约定：开发级 backup 随包保留，用户级不进包

- **用户设计**：项目根 `backup/` 为用户级备份（用户设置备份），不进包；`portable_config` 等 config 目录下的 `backup/` 为开发级备份（开发升级过程中淘汰但曾可用的脚本/配置，体积小），随包保留以便回滚。
- **打包脚本**：`build-01-base.ps1` / `build-05-config.ps1` 移除"删除全部 backup 目录"与"仅放行 stats"逻辑，改为保留 `portable_config` 下所有 backup（`backup/`、`script-opts/backup/`、`scripts/backup/`）进包；根 `backup/` 不在复制范围内，自然不进包。个人运行时状态 `script-opts/window_state.conf` 仍排除。
- **.gitignore**：取消忽略 `portable_config/backup/` 与 `portable_config/script-opts/backup/`（开发级备份可 git 跟踪、随版本化）；保留 `/backup/`（用户级）与 `/docs/worker*备份*.js` 忽略。
- **文档**：《发布流程.md》3.2 节新增"备份目录约定（既定发布内容）"说明（开发级进包不触发 Gate）、5 节新增备份约定核验项；AGENTS.md 重要约定新增第 7 条 Backup 两级约定。
- **实测**：临时 `-Version 9.9.9` 构建 01/05，`7z l` 确认包内包含 `portable_config/backup/mpvconf-*.conf`、`portable_config/script-opts/backup/uosc-theme-*.conf`（12 个）、`portable_config/scripts/backup/stats-original-*.lua`；私用全量包由 01~05 合并自动跟随。产物与 build/ 已清理。
- **边界**：本次为流程/脚本/约定修改，未实际发布（未定版本号、未建 Release）；《发布流程.md》按用户明确指示修改，仅补充 backup 约定，未改动既有流程规则。
### 2026-08-14 14:10 · VantaInstaller 暴露 uosc 子菜单弹出延迟（menu_submenu_delay）

- **背景**：用户反馈 uosc 菜单交互慢，定位为 `script-opts/uosc.conf` 的 `menu_submenu_delay`（保护性 0.3s 防误弹出）；用户已调至 0.1s，并要求在 VantaInstaller「mpv 调节」中暴露可调。
- **新增 `UoscConfigService.cs`**（Vanta.Core.Services）：读写 `uosc.conf` 的 `menu_submenu_delay`，保留注释与行序、缺失键追加、UTF-8/LF、目录自动创建；默认值 0.1。
- **SettingsViewModel.cs**：新增 `UoscMenuSubmenuDelay`（默认 0.1）、`UoscMenuModified`、`LoadUoscMenuSettings`、`RefreshUoscMenuModified`；`CanSaveMpvSettings` 纳入 uosc；`SaveMpvSettings` 一并写回 uosc.conf。
- **SettingsView.xaml**：mpv 调节卡片新增「菜单交互」分组（子菜单弹出延迟滑块 0~0.5s，步进 0.05s，显示秒数），说明文案：0 更跟手，调大避免快速扫过父菜单时误弹出。
- **uosc.conf**：`menu_submenu_delay` 0.3 → 0.1（用户实测值，与安装器默认一致）。
- **验证**：临时控制台单测 11 项全过（读取/替换键保留注释与其它键/0 整数格式/缺失键追加/缺失文件默认/自动建目录/重新加载）；`dotnet build -c Release` 0 警告 0 错误。
- **边界**：VantaInstaller 附属工具功能改动不触发发布 Gate；未递增安装器版本号、未 publish 重建、未上传。
### 2026-08-14 15:00 · uosc 底部迷你进度线（普通小窗口 1.2px 已播进度）+ 菜单开关

- **需求**：参考杳知 mpv 整合包 8.14「丝滑 Morph」的迷你进度线——普通小窗口播放时保留 1.2px 已播放进度，只显示主题色已播部分，不绘制未播放轨道/整宽底板；做成「其它」菜单开关，默认开启。
- **方案**：uosc 5.13 原生支持 `progress=windowed` + `progress_size` 迷你进度条，但仓库版 Timeline.lua 的 progress 绘制乘了 `visibility`（收起时=0 导致迷你线不显示），需移植杳知版的 `bar_visibility`/`track_visibility` 逻辑。
- **Timeline.lua**：`render` 新增 `has_minimized_progress`/`bar_visibility`/`track_visibility`——迷你进度时 progress 强制可见、轨道/加载条不绘制；`bar_height` 收起时跟随 `progress_size`（1.2px）、展开过渡到正常条高；圆形手柄仍跟随 visibility（迷你时不画圆点）。`decide_progress_size` 增加暂停（pause）、待机（is_idle）、播放结束（eof_reached）自动隐藏；新增 `on_prop_is_idle`/`on_prop_eof_reached` 钩子，`on_prop_pause` 触发重算。
- **main.lua**：新增 `mini-progress-toggle` script-message（切换 progress=windowed/never，持久化到 uosc.conf，发布 `user-data/uosc/mini-progress` 状态），参照 chapter-display-toggle 模板。
- **uosc.conf**：`progress=never` → `windowed`，`progress_size=2` → `1.2`（默认开启）。
- **input.conf**：`其它 > 底部迷你进度线 > 开/关`，快捷键 `CTRL+ALT+b`，带勾选状态。
- **验证**：luajit 语法通过；隔离环境端到端——初始 `user-data/uosc/mini-progress=yes` → `script-message mini-progress-toggle` 后变 `no` 且 uosc.conf 持久化为 `progress=never`，再 toggle 恢复 `windowed`；完整配置加载无 uosc 错误。测试中发现隔离环境缺 `script-modules/media-format-info.lua` 会导致 uosc 加载失败（测试环境问题，非代码问题）。
- **边界**：仅配置/脚本改动，未构建/发布 mpv 包；uosc 为仓库定制脚本，改动随包分发。
### 2026-08-14 15:30 · 修复迷你进度线位置与暂停行为

- **用户反馈**：① 迷你线与进度条同位置，悬浮在画面上而非播放器底部，影响观感；② 暂停时迷你线消失。
- **根因**：上一版只在 Timeline 收起位置（画面内 self.by，控制栏上方）显示迷你线；且加了暂停/待机/播放结束自动隐藏（用户不需要）。
- **修复（Timeline.lua）**：
  - `render` 中 `has_minimized_progress` 时，迷你线横向铺满窗口（bax=window_border, bbx=display.width-window_border），垂直贴到窗口底部（hit_bby=display.height-window_border）；进度几何改用 `bar_width = bbx-bax` 而非 `self.width`，展开时回到控制栏内嵌位置。
  - `decide_progress_size` 移除 pause/is_idle/eof_reached 隐藏条件，恢复仅按 progress 模式判断；移除 on_prop_is_idle/on_prop_eof_reached 钩子，on_prop_pause 恢复为 request_render。
- **验证**：隔离环境 + 真实 GPU VO + 渲染日志钩子——迷你线 `bax=1 bbx=1279 bay=717 bby=719`（窗口 1280x720），横向铺满、贴底 1.2px、progress 随播放推进、vis=0；暂停后迷你线仍显示且保持贴底。测试钩子未入库。
- **边界**：仅改 Timeline.lua，未构建/发布。
### 2026-08-14 16:00 · VantaInstaller 主题切换不再产生备份 + 清理历史堆积

- **问题**：`UoscThemeService.ApplyTheme` 每次应用主题都把整个 uosc.conf（约 18KB）复制到 `script-opts/backup/uosc-theme-<时间戳>.conf`，无数量上限——8/11 调试一次就积了 12 份，会无限增长。
- **修复**：主题切换只改 `uosc.conf` 的 `theme=xxx` 一行、不碰其它配置，色板注册表 `uosc-themes.json` 本身已版本化可随时换回，因此 **ApplyTheme 改为不再产生备份**（返回 void）；SettingsViewModel 提示文案去掉"备份：xxx"。
- **清理**：删除历史 13 份 `uosc-theme-*.conf` 残留（约 230KB，git 已跟踪 12 份 + 未跟踪 1 份），`script-opts/backup/` 现为空。
- **验证**：单测——应用主题前后 backup 文件数 0→0、theme 正确更新、`menu_submenu_delay`/`progress` 等其它行原样保留；Release 构建 0 警告 0 错误。
- **边界**：仅安装器逻辑与备份清理；mpv.conf 的 `MpvConfigService.Backup`（保存设置才触发、频率低）保持不变。uosc.conf `theme` 已为用户当前值 lava-orange（一并提交）。

### 2026-08-14 16:30 · 停止 LSFG 接入并改为四包结构

- **决策**：LSFG 深挖（10bit swapchain 格式转换、telemetry、present 节奏诊断）后仍无 SVP 的丝滑效果，用户决定整体放弃 LSFG 接入；SVP 方案本就通过 VapourSynth 接入 mpv，不受影响。
- **回退**：`git reset --hard e3813dd`（丢弃今天 7 个 lsfg 研究提交，保留 stats 汉化/迷你进度线/菜单延迟/备份约定/主题不备份等功能）。
- **废弃目录**：新建根 `trash/` 收纳全部 LSFG 相关文件（.gitignore 忽略、不进公开包）：build-04-lsfg.ps1、start-mpv-lsfg.ps1、lsfg_control.lua、research/lsfg-vk-win（183 文件）、lsfg-vk/、Lossless Scaling/、release/04-mpv-lsfg-addon-*.7z。
- **菜单/脚本**：input.conf 恢复 `CTRL+` `vf clr ""`、补帧菜单恢复「关闭补帧」+ mpv/VapourSynth 选项、移除 `user-data/lsfg` 状态条件；quality_status.lua 移除 LSFG 块。
- **打包**：04 LSFG 废除；`build-05-config.ps1` → `build-04-config.ps1`，公开包变为 01/02/03/04（04 = Config 最终覆盖层）；build-all-packages 构建四包；build-full-private 不再含 LSFG/Lossless Scaling。
- **流程/文档**：发布流程.md 改 01~04、移除 Lossless.dll 既定内容条款、新增根 trash 不进包约定；README、下载站 worker、.gitignore、AGENTS.md 同步。
- **验证**：全部 build 脚本 PowerShell AST 解析通过；quality_status.lua luajit 语法通过；git grep 确认跟踪文件无 lsfg 功能残留（历史记录保留）。
- **边界**：不构建、不发布；提交分三次（chore 回退/移除、build 打包脚本、docs 流程文档）。

### 2026-08-14 18:00 · 跟进杳知 8.13/8.14 起播徽章（新 SDR 徽章 + 位置稳定性修复）

- **素材**：对比杳知 8.14 包，差异仅 `logo-sdr-*` 24 bgra + manifest.json；替换为 8.13 新版 SDR 徽章（manifest v21→v23，body-only + 7 色彩虹框），旧素材 25 文件备份至 `script-assets/backup/startup-format-logos-sdr-v21-20260814/`。
- **脚本**：`startup-logo-bounds.lua` 移植 `merge_stable`；`startup-format-logos.lua` yaozhi 模式复检改为多次一致确认 + `bar_anchor_locked` 单文件锁定一次；后瞻稀疏复检吸收多次一致（两次黑边共识/两次无黑边共识，耗尽兜底）。
- **验证**：luajit 全过；merge_stable 单测通过；完整配置真实播放正常（SDR 徽章淡入、yaozhi 模式黑边样本无错误）；assets loaded 28 logos。
- **其他评估**：音轨/字幕策略本地已合理；AList 与 ASS 色彩模式不适用/已有。
- **边界**：仅配置/脚本/素材，未构建未发布。

### 2026-08-14 18:40 · VantaInstaller v0.3.3（四包跟进 + 放宽 Base 强制）

- **问题**：公开包改 01~04 后安装器仍按旧结构；且扫描强制要求 01 Base，Base 已装好的升级场景（只下载 04 Config）被卡住。
- **改动**：
  - `PackageScanner.Scan(directory, allowMissingBase=false)`：宽松模式缺 01 只警告、版本不一致降级警告（升级目录常混旧包）。
  - `InstallEngine`：扫描走宽松模式；新增把关——全新安装必须含 01（目标目录无 mpv.exe 时），覆盖升级可不带 01；本次选中包强制同版本；`.vanta-version` 按选中包版本写入。
  - UI：欢迎页/组件页文案改 01~04；组件页缺 Base 时显示黄色提示（覆盖升级可继续）。
  - 版本：今日统一锁定 v0.3.3（不递增）。
- **验证**：build 0 警告 0 错误；引擎三场景实测通过；ScanTool 严格模式不变；单文件 publish 成功，发布候选已放 release/。
- **边界**：附属工具，不触发 Gate；mpv 包未构建。

### 2026-08-14 19:10 · VantaInstaller v0.3.3（同编号多版本目录无法下一步）

- **问题**：同 Id 多版本（如 01×1.5.1/1.5.2）→ PackagesViewModel.Refresh 的 ToDictionary 重复键异常 → 向导卡住。
- **修复**：PackageScanner 同 Id 只保留最高版本（旧版警告忽略）；PackagesViewModel ToDictionary 改 GroupBy 容错。
- **验证**：build 0 警告 0 错误；扫描/引擎多版本场景实测通过；v0.3.3 发布候选已放 release/。

### 2026-08-14 19:30 · VantaInstaller v0.3.3（每个包带版本标签，多版本全保留）

- **需求**：多版本包目录不再自动丢旧版，每个版本独立显示可自选。
- **改动**：VantaPackage.Key（编号|版本）复合键；PackageScanner 移除去重、多版本降为警告；选择模型改 SelectedPackageKeys；组件页加版本标签胶囊。
- **验证**：build 0 警告 0 错误；扫描/引擎多版本场景实测通过；发布候选 v0.3.3 已更新（版本号未递增）。

### 2026-08-14 20:00 · 私包跳过 03 Faster-Whisper（占位目录 + 说明）

- **原因**：03 约 1.4GB，私包合并耗时明显，个人不用 AI 字幕。
- **改动**：build-full-private.ps1 移除 03 required 与解压，改为 Faster-Whisper-XXL 占位目录 + 03包解压后覆盖于此.txt；README 同步。
- **验证**：语法通过；最小包（无 03）实测构建成功、占位文件在包内；测试产物已清理。
- **边界**：仅私包脚本改动，公开包不受影响。

## 发布前检查清单（2026-08-14，未发布，等待用户 Gate 决策）

### 3.1 工作区与 Git 状态
- [x] `git status --short --branch`：`master...origin/master [ahead 16]`，工作区干净（无未提交/未跟踪）。
- [x] `git fetch origin`：远端无新改动。
- [x] 未提交改动已全部按逻辑整理为 16 个提交（今天全部功能/构建/文档改动均已提交）。
- [x] 本地领先 origin 16 个提交，尚未推送（发布前需推送或按流程处理）。

### 3.2 大改动 Gate 评估（命中 → 必须停止发布并汇报）
- [x] **公开包数量/编号/覆盖顺序变化**：01~05 → 01~04（04 LSFG 废除，05 Config 改为 04）→ **命中**
- [x] **构建脚本/产物生成方式修改**：build-04-lsfg 废除、build-05→build-04、build-all 改四包、私包跳过 03 → **命中**
- [x] **修改了发布流程文件本身**（7dc4b5c 改为四包结构、新增 trash 约定）→ **命中**
- [x] **大型资源增删/包体积变化**：LSFG 相关（Lossless.dll、lsfg-vk、research 183 文件）移入 trash 不再进包；私包不再合并 03（约 -1.4GB）→ 命中
- [x] **VantaInstaller 附属工具 v0.3.3**：功能/界面/版本迭代，按流程**不触发** Gate（但安装器构建产物形态无变化，沿用 publish 单文件流程）
- [x] **第三方版权边界**：公开包不再包含 Lossless.dll（商业软件）→ 原"04 内置 Lossless.dll 既定内容"条款已随流程修改移除
- **结论：命中大改动 Gate，停止发布，需用户决定豁免或调整后继续。**

### 3.3 文档与记录检查
- [x] `docs/codex/STATUS.md`：本清单即记录（当前）。
- [x] `version/工作进度.md`：今日 16 次改动均有条目（12:57~20:00）。
- [ ] `version/版本迭代记录.md`：仍为 v1.5.2 旧结构（01→05、含 LSFG），**新版本发布时须更新当前版本一节**（发布前待办）。
- [x] `README.MD`：已同步四包结构（四类包关系、安装顺序 01→04、打包脚本说明）。
- [ ] **`.vanta-version` 根目录本地副本仍为 `1.5.2`**：发布新版本时须由 build-01 按新版本写入（发布时自动更新，本地副本发布后同步）。

### 3.4 功能验证
- [x] 完整配置真实播放：修复后日志无 `[e]/[f]` 级别错误（此前发现并修复两处：① input.conf 补帧菜单 8 行 `#@state=` 结尾多余右括号；② scripts/backup 缺 main.lua 导致 mpv `Cannot find main.*`）。徽章脚本正常加载（assets loaded 28 logos）、SDR 徽章正常淡入、后瞻 ffmpeg 正常启动。
- [x] 涉及 Lua 脚本语法检查全部通过：startup-format-logos.lua、startup-logo-bounds.lua、quality_status.lua、stats.lua（luajit loadfile 退出码 0）。
- [x] 菜单表达式一致性：input.conf 全部 74 条 `#@state=` 表达式经 luajit 编译通过（0 失败）。
- [x] UTF-8 无 BOM / LF：今日改动脚本/配置全部无 BOM、无 CRLF。
- [x] `git diff --check` / `--cached --check` 通过。

### 其他核查
- [x] 完整构建实测（2026-08-14）：01/02/03/04 四包 + 全量私包全部构建成功（测试版本 9.9.9），产物内容核验正确（无 lsfg、backup 进包、script-assets 随 01、04 排除 .vanta-version/script-assets、02 分卷 1900MB/745MB 合规、私包含 v0.3.3 安装器）。
- [x] 安装器发布候选：`release/VantaInstaller-win-x64-v0.3.3.exe` 就绪（69.65MB）。
- [ ] **发布时待办**：确认新版本号 → 更新 `version/版本迭代记录.md` 当前版本 → 执行 `build-all-packages.ps1 -Version X.Y.Z -IncludePrivate` → 第 5 节构建后验证（7z t、SHA-256、.vanta-version 逐字节、门禁）→ 第 6~8 节提交/标签/Release/收尾。

## 二轮全面验证（2026-08-14，用户要求杜绝未检查出的用户可见 bug）

### 发布流程调整（用户已授权，提交 06ce29b）
- 4.2 私包产物描述：合并 01/02/04 + Faster-Whisper-XXL 占位（不合并 03）
- 第 5 节私包核验补充 03 占位说明文件
- 第 2 节补充：安装器版本号由用户锁定，agent 不得擅自递增/改名
- 第 10 节历史参考补 v1.5.1/v1.5.2（tag 已核实存在）

### 功能验证矩阵（二轮，全部通过）
- [x] **全量 Lua 语法**：portable_config/scripts + script-modules 共 137 个 .lua（不含 backup）全部 luajit loadfile 通过；backup 内 2 个备份文件作为可回滚备份不参与运行检查。
- [x] **input.conf 表达式**：74 条 `#@state=` 全部编译通过（0 失败）；关键快捷键完整（CTRL+` 清空滤镜、ALT+i 轻量插值、CTRL+ALT+b 迷你线、起播 Logo 开关、质量状态）。
- [x] **完整配置真实播放**（normal-169，240 帧，--idle=no 覆盖启动页）：正常退出码 0，无 [e]/[f]；quality_status/quality_menu/startup_format_logos/stats/uosc/uosc_danmaku/dyn_menu 全部加载成功；徽章素材加载（28 logos）、SDR 徽章淡入、mini-progress=yes、dyn_menu 菜单加载正常。
- [x] **起播徽章四模式**（黑边样本 cinema-letterbox）：current / yaozhi / parallel / none 均正常退出、0 错误；current/parallel 后瞻解析正常（bar lookahead resolved，锚点计算正确）。
- [x] **软解播放**（--hwdec=no，180 帧）：0 错误；日志确认 Using software decoding；stats.lua 软解显示路径（hwdec-current=no → "软件解码"）代码走查正确。
- [x] **backup 目录脚本包**：main.lua 空脚本包正常加载（无 Cannot find main.*），stats-original 不会被自动加载；无副作用。
- [x] **配置现状**：uosc.conf progress=windowed / progress_size=1.2（迷你线）、menu_submenu_delay=0.1、theme=gulf-blue（海湾蓝默认）；stats.lua 软解修复逻辑在代码中确认。
- [x] **无 LSFG 残留**：quality_status.lua 已无 LSFG 块；git diff 确认 lsfg_control.lua 删除（-304 行）。
- [x] **UTF-8 无 BOM / LF / git diff --check**：此前已通过。
- [x] **打包边界**：此前完整构建实测（01~04 + 私包）产物核验正确（无 lsfg、backup 进包、script-assets 随 01、04 排除 .vanta-version/script-assets、02 分卷合规、私包含 v0.3.3 安装器与 03 占位）。
- [x] **安装器**：此前引擎三/多版本场景实测通过；v0.3.3 发布候选就绪。

### 结论
- 今日全部改动经两轮验证：无已知用户可见 bug。
- 仍未发布；大改动 Gate 命中状态不变，待用户决定是否发布。

## 发布结果（2026-08-15，v1.5.3）

- GitHub Release：https://github.com/maxzrb/mpv-vanta-edition/releases/tag/v1.5.3（正式版，非草稿/预发布）。
- 资产核对：6 个公开资产远端大小与 SHA-256 全部与本地一致（01/02.001/02.002/03/04/VantaInstaller-v0.3.3），无重复、无 diag 残留；私包未上传。
- 上传过程：曾遇 GitHub 上行线路波动（0.3~0.7MB/s）暂停；诊断确认非本地带宽（百度网盘正常、直连 GitHub 真实 IP 亦慢、走代理也慢）；线路恢复后（3MB/s+）并行上传完成。
- 收尾：版本迭代记录/工作进度/本文件已更新；master 与 origin/master 同步（发布提交 164c77f + 收尾提交）。

### 2026-08-17 12:17 · MediaInfo 胶囊编码识别逻辑核查

- `portable_config/scripts/uosc/elements/MediaInfo.lua` 只负责调用 `MediaFormatInfo.collect()` 并展示 `info.video_codec`；识别逻辑在 `portable_config/script-modules/media-format-info.lua`。
- `read_snapshot()` 读取 `video-codec`、`current-tracks/video` 等 mpv 属性；`build_context()` 又把视频轨道字段、`video-codec`、文件名、媒体标题和完整路径拼接，并经 `compact()` 去掉标点后用于子串匹配。
- `VIDEO_CODEC_RULES` 按顺序扫描，`AVC` 规则位于 `AV1` 之前；`contains()` 是无边界的纯子串查找。因此真实 `video_codec=av1` 时，只要标题、文件名或路径含 `avc`，就会先返回 `AVC`。模拟验证覆盖标题、文件名、目录和轨道字段组合，均复现该误判；仅标题写 `AV1` 也能在真实属性缺失时被识别为 AV1。
- 同一上下文污染也会影响动态范围/音频标签：标题中的 `Dolby Vision`、`HLG`、`Atmos` 可分别触发对应标签。此次未修改代码，待用户确认后再按“权威轨道属性优先、标题/路径仅作受限兜底”的方向修复。
- 验证命令：`luajit.exe -e ... media-format-info.lua`（合成快照测试）；`mpv.exe --version` 正常。记录前代码工作树为 `master...origin/master` 且干净；当前仅新增本次两份 HandShake 记录文件。

### 2026-08-17 12:27 · 核对杳知 mpv 8.17 编码识别修复

- 来源：GitHub Release `mpv-Yaozhi_整合包`，资产 `Yaozhi-mpv-8.17.7z`，发布说明明确声称视频格式只按当前真实轨道/解复用器/解码器识别。
- 包内活动链路：`scripts/uosc/elements/Timeline.lua` 加载 `script-modules/media-format-info.lua`，`build_media_info_segments()` 使用 `MediaFormatInfo.collect()`；`uosc/main.lua` 的独立 `elements/MediaInfo` 构造器仍被注释，实际胶囊走 Timeline。
- `media-format-info.lua` 新增 `detect_snapshot_video_codec()`，只检查 `video-codec`、选中视频轨的 `codec`/`demux-codec`/`codec-desc`/`decoder-desc`/`format`，不再把文件名、标题、路径用于基础视频编码判定。
- 发布包 LuaJIT 合成快照验证：真实 AV1 + 标题 AVC、文件名 x265/HEVC、目录污染均返回 AV1；真实 HEVC + 文件名 AV1 返回 HEVC；仅标题 AV1 且无真实视频属性返回空值。
- 保留风险：包内备用 `scripts/uosc/elements/MediaInfo.lua` 仍直接用 `video-params/codec` 加文件名判断，存在旧误判逻辑；但当前 `main.lua` 未启用该元素。动态范围/音频识别仍可使用标题/路径上下文，这是发布说明允许的补充元数据兜底范围。

### 2026-08-17 12:37 · 修复本仓库 MediaInfo 编码识别优先级

- `portable_config/script-modules/media-format-info.lua`：将视频编码识别拆为独立字段检测；按真实 `video-codec`、视频轨道 `codec`/`demux-codec`/`codec-desc`/`decoder-desc`/`format`，再按文件名，最后按媒体标题的顺序返回。路径不再参与基础视频编码判断。
- `portable_config/scripts/uosc/elements/MediaInfo.lua`：补充观察 `video-codec`、`filename`、`media-title`，切轨或属性变化后及时刷新胶囊。
- 边界修复：实际候选字段统一为空字符串，避免 Lua `ipairs` 在缺失字段处提前停止，导致跳过后续轨道属性。
- 验证：LuaJIT 语法通过；5 组合成快照优先级断言通过（真实轨道覆盖文件名/标题、文件名覆盖标题、标题兜底、路径忽略）；完整 `mpv.exe --config-dir=portable_config` 播放真实 AV1 样片 2 帧，uosc 与媒体模块加载正常，无 `[e]/[f]` 或 Lua 错误；`git diff --check` 通过（仅已有 LF→CRLF 警告）。

### 2026-08-17 12:50 · 新增进度条时间显示模式与统一时长格式

- `portable_config/scripts/uosc/main.lua`：保留默认 `playtime-remaining`，新增 `time-display-toggle` 消息，在播放时长/剩余时长与播放时长/总时长之间切换；切换后持久化 `destination_time`，并发布 `user-data/uosc/time-display` 供菜单状态使用。
- `update_human_times()` 改为先计算左右原始秒数，再用两者绝对值较大的时长统一调用 `format_time()`；总时长超过一小时且当前进度较短时，左侧会保留小时位（如 `00:15:01/01:15:55`）。
- `portable_config/input.conf`：新增 `CTRL+ALT+m` 和“其它 > 时间显示”菜单入口，当前为总时长模式时显示勾选状态。
- `portable_config/script-opts/uosc.conf`：补充模式切换说明；默认仍为播放时长/剩余时长。
- 验证：LuaJIT `main.lua`/`TimeDisplay.lua` 语法通过；完整配置默认启动发布 `time-display=remaining`；临时探针切换 `total` 后日志确认 `destination_time=total` 已持久化、状态发布为 `total`，随后恢复正式配置；`git diff --check` 通过。完整配置测试另有既存 `undoredo.lua`/`simplehistory.lua` 错误，与本次时间显示无关。

### 2026-08-17 13:00 · 时间区域支持鼠标点击切换

- `portable_config/scripts/uosc/elements/TimeDisplay.lua`：在可见的完整时间显示矩形上注册 `primary_click` 命中区，点击后向 uosc 发送 `time-display-toggle`。
- 点击、`CTRL+ALT+m` 和“其它 > 时间显示”菜单共用同一消息处理器，因此模式状态、OSD 提示与 `uosc.conf` 持久化行为完全一致。
- 验证：TimeDisplay LuaJIT 语法通过；完整配置真实 AV1 样片短启动无 uosc/TimeDisplay 错误；`git diff --check` 通过。

### 2026-08-17 13:11 · MediaInfo 与其它视频信息显示文本污染审计

- 本轮只审计，未修改识别代码。此前基础视频编码修复有效：真实 `video-codec`/轨道字段优先，文件名其次，媒体标题最后，路径不参与；合成快照确认真实 AV1 配合旧 H.265 文件名及 AVC 标题仍返回 AV1。
- MediaInfo 动态范围仍把轨道文本、文件名、媒体标题和完整路径混为同一上下文。复现：真实 SDR + 文件名 `DOVI` 返回 Dolby Vision；真实 PQ + 文件名 `HDR10Plus` 返回 HDR10+。Dolby Vision、HDR Vivid、HLG 等均存在同类文本触发路径。
- MediaInfo 音频格式仍会被文件名、媒体标题、路径及轨道标题误导。复现：真实 AAC + 文件名 `Atmos` 返回 Dolby Atmos；真实 AAC + 媒体标题 `DTS-HD MA` 返回 DTS-HD MA。
- 声道布局存在两处问题：候选数组首项为 `nil` 时 Lua `ipairs` 立即停止，后续真实布局可能不检查；文件名布局又先于真实声道数回退。复现：真实 6 声道 + 文件名 `2.0` 返回 2.0；真实 `7.1.4`/12 声道在首候选缺失时返回 `12ch`。
- 其它准确性边界：`hwdec-current` 空值被显示为软解；未知视频编码（如 FFV1）不显示，未知音频编码可回退为原始 `audio-codec` 大写；宽银幕分辨率按宽或高阈值粗分，`2560x1080` 显示 1440P QHD、`3840x1600` 显示 4K UHD。
- 独立起播 Logo 默认 `filename_fallback=yes`，视频 Dolby Vision/HDR Vivid/HDR10+/HDR10/HLG 会读取文件名、标题和路径；音频 Logo 已有限制，只允许单音轨且与真实 Dolby/DTS codec 家族兼容的文本兜底。`stats.lua`、dyn_menu/uosc 轨道菜单直接使用 mpv 轨道/参数字段，未发现文件名参与格式推断；quality-menu 展示 yt-dlp 的格式 JSON 字段，也不以媒体标题推断格式。
- 格式覆盖：视频明确映射 VVC、AVS3、AVS2、AVS+、HEVC、EVC、AVC、AV1、VP9、VP8、MPEG-2、MPEG-4、VC-1、ProRes、Theora、JPEG XL、WebP；MPEG-1、H.263、MJPEG、FFV1、HuffYUV、DNxHD/DNxHR、CineForm、Dirac、APV、rawvideo、WMV1/2、VP6、RealVideo 等无明确映射。音频覆盖 Dolby/DTS、Audio Vivid、AC-4、MPEG-H、AAC 系、FLAC/ALAC/WavPack/TAK/TTA/APE/WMA/Opus/Vorbis/MP3/PCM/MLP，未映射格式仍显示原始值。
- 验证：使用根目录 `luajit.exe` 调用 `MediaFormatInfo.from_snapshot()` 完成 10 组合成快照与 4 组分辨率测试；工作树仍包含此前 8 个未提交文件，本轮仅改动本状态文件和 `version/工作进度.md` 的审计记录。

### 2026-08-17 13:27 · MediaInfo 胶囊移除文件名/标题格式兜底

- `portable_config/script-modules/media-format-info.lua`：删除 filename、media-title、path、轨道 title 和任意 metadata 文本参与格式推断；视频/音频只读取当前轨道 codec、profile、demux/decoder 字段、video/audio params 和受限结构化元数据白名单。
- 动态范围仅接受 Dolby Vision profile/level、HDR Vivid、HDR10+/静态 HDR 元数据及真实 transfer/gamma；无可靠字段返回“动态范围未知”。视频/音频无法映射但存在真实 codec 时显示真实 codec 名称，完全缺失时分别显示“未知视频格式”“未知音频格式”。
- 声道布局移除文件名回退并修复空候选截断；无布局和声道数时显示“声道未知”。`hwdec-current` 为空时胶囊显示“解码未知”，不再误报软解；无音轨时不显示虚假的未知音频段。
- `portable_config/scripts/uosc/elements/MediaInfo.lua`：移除 filename/media-title 属性观察，增加 `video-frame-info` 观察；按 HW/SW/UNKNOWN 三态显示解码方式。
- 验证：LuaJIT 16 组合成快照断言、结构化元数据断言、目标脚本语法和 mpv 无配置单帧启动均通过；完整配置真实样片退出码 0。完整配置日志仍有既存 auto_profiles 条件警告，与本次改动无关；`git diff --check` 通过。

### 2026-08-17 14:41 · 8K VP9 60fps 硬解卡顿诊断

- 样片 `F:\演示片\DOLBY_VISION_CES\8K 秘鲁 HDR画质 60FPS FUHD Peru HDR 60FPS FUHD .webm` 的真实轨道是 VP9 Profile 0、7680x4320、59.9401fps、yuv420p、BT.709，平均码率约 68.7Mbps；文件名中的 Dolby Vision/HDR 不符合轨道参数。
- 设备为 AMD Radeon RX 6600，显示器 1920x1080 144Hz。完整配置日志确认初始 `auto-copy` 会先尝试 `vp9-d3d11va-copy`，随后 `[8k-fix]` 正确应用 `hwdec=auto-safe` 并重启为原生零拷贝 `d3d11va`，所以持续卡顿不是 8K 条件配置未生效。
- 无用户配置基线（原生 `d3d11va`、`video-sync=audio`、禁用插值/去色带、bilinear 缩放）播放 12 秒仍记录 526 次 `drop-vo`、仅 194 次视频绘制；`vo=gpu` 基线为 460 次 `drop-vo`、260 次视频绘制。`gpu-next` 有影响，但改用旧渲染器仍不足以流畅，说明 RX 6600 的 VP9 8K60 解码余量与 mpv 的呈现/驱动队列共同成为瓶颈。
- 完整配置另有启动阶段附加负载：起播 Logo 的编码黑边后瞻从约 3.17 秒启动独立 ffmpeg 软件解码 8K VP9 帧，到约 9.81 秒才返回，约持续 6.6 秒；这会放大刚起播时的卡顿，但不能解释禁用全部用户脚本后的持续丢帧。
- FFF Player 设置仅能确认“解码方式=2”，本地没有其后端映射或运行统计，不能据此断言它使用哪种硬解 API；更平滑的合理差异是不同的硬解后端、帧队列、丢帧策略或更直接的 D3D/Vulkan 呈现路径。
- 本轮只诊断并生成 `tmp/mpv-8k-*.log` 与 stats 临时记录，未修改任何播放配置。若继续修复，优先顺序应是：8K 时关闭起播 Logo 的 ffmpeg 黑边后瞻，再建立专用低负载渲染配置，最后对比 D3D11VA/AMF/Vulkan 可用路径。

### 2026-08-17 14:52 · uosc 菜单与隐藏时间轴缩略图交互穿透修复

- 根因：`Timeline:render()` 在时间轴不可见时仍按扩展 seek 命中区计算 `seek_hovered`，缩略图分支未检查菜单状态；菜单覆盖到该区域时，底层时间轴继续向 thumbfast 请求预览。
- `portable_config/scripts/uosc/elements/Timeline.lua`：菜单存在且未处于关闭动画时，立即清除缩略图、阻止 `seek_hovered`、停止注册时间轴的点击/滚轮命中区。菜单关闭后时间轴恢复原本交互。
- `portable_config/scripts/uosc/elements/Menu.lua`：菜单创建时主动调用 `Timeline:clear_thumbnail()`，避免菜单打开前一帧已经显示的缩略图残留。
- 验证：两文件 LuaJIT 语法检查通过；完整配置短启动日志无 uosc/Menu/Timeline Lua 错误，并确认菜单创建路径向 thumbfast 发送 `clear`；`git diff --check` 通过。实际窗口交互需人工打开菜单并将光标移到原问题区域复核。

### 2026-08-17 14:56 · uosc 底栏单轨计数显示

- `portable_config/scripts/uosc/elements/Controls.lua`：字幕、音频、视频控件的 badge 条件由 `sub/audio/video > 1` 改为 `> 0`。
- 结果：存在一条轨道时相应图标显示 `1`；不存在该类型轨道时不显示数字。播放列表、章节、版本仍保留“多于一项才显示计数”的原有规则。
- 验证：Controls.lua LuaJIT 语法通过；规则断言确认三个轨道均为 `>0` 且 playlist/chapters/editions 仍为 `>1`；`git diff --check` 通过。

### 2026-08-17 15:03 · MediaInfo 真实 codec 映射扩展

- `portable_config/script-modules/media-format-info.lua` 视频映射新增：MPEG-1、MS MPEG-4、H.263、WMV1/2、DNxHD/DNxHR、CineForm、FFV1、HuffYUV、Dirac、APV、HAP、MJPEG、JPEG 2000、VP6、RealVideo、RAW；已有常见编码规则不变。
- 音频映射新增：Dolby E、MPEG Layer I/II、泛 MPEG Audio、Musepack、Speex、AMR-NB/WB、ATRAC、ADPCM、G.711 A-law/mu-law。`mpa` 不再错误显示为 MP3，而是在真实 codec 无法细分层级时显示 MPEG Audio。
- 修复规则顺序边界：ATRAC3plus 的实际 codec 文本含 `ac3`，现优先匹配 ATRAC，避免误报 Dolby Digital。
- 所有新增识别仍只读取当前选中轨道、解码器及受限结构化元数据；合成快照额外验证真实 FFV1/MP2 不会被轨道标题 AV1 HDR/Dolby Atmos 覆盖。
- 验证：15 个视频与 13 个音频新增映射快照通过；三个目标 Lua 文件语法通过；完整配置日志确认 MediaInfo/起播 Logo 均加载共享模块，启动阶段未见 Lua 错误。`--frames=1` 受既有自动播放脚本影响持续加载后续文件，30 秒后人工停止测试进程，无遗留进程；`git diff --check` 通过。

### 2026-08-17 15:18 · 今日 MediaInfo 与 uosc 改动鲁棒性复核

- MediaInfo、共享格式模块与起播 Logo 的实际调用链已复核：编码、动态范围、声道布局、解码方式和起播格式 Logo 只使用当前选中轨道、解码器、视频/音频参数及受限结构化元数据；文件名和媒体标题不参与格式判定。轨道标题仅在真实字段缺失时作为受限兜底，且音频不得跨真实 codec 家族细化。
- `MediaInfo.lua` 的网络速度标签由路径协议文本改为 mpv `demuxer-via-network` 状态，并观察该属性刷新；避免本地特殊路径、伪协议或 URL 文本造成“网络”误报。
- `uosc.conf` 保持原默认“播放时长/剩余时长”；新增的“播放时长/总时长”仍可通过点击时间区、菜单和 `CTRL+ALT+m` 切换。
- 起播 Logo 内仍有一组未调用的旧识别辅助函数；运行时只走共享 `media-format-info.lua`，故不影响当前结果。后续重构时应删除该死代码，防止维护者误接回不受限的旧逻辑。
- 验证：今日 8 个修改 Lua 文件 `loadfile` 解析通过；合成快照确认真实 FFV1/SDR/AAC 覆盖伪造文件名、媒体标题及不兼容轨道标题，轨道标题只在真实信息缺失时兜底；`git diff --check` 通过（仅既有文档 LF→CRLF 警告）。

### 2026-08-17 15:31 · v1.5.4 发布前检查

- **3.1 工作区与 Git**：`git status --short --branch` 已核对 13 个待发布改动（MediaInfo、起播 Logo、uosc、记录文件）；`git fetch origin` 成功，`master` 与 `origin/master` 均指向 `71ebb3f`，远端无未合并改动。功能改动、构建记录、发布结果将按流程分提交。
- **3.2 大改动 Gate**：不触发。公开包仍为 01 Base → 02 Extras → 03 Faster-Whisper → 04 Config；所有今日运行时改动均在 `portable_config/`，`build-01-base.ps1` 与 `build-04-config.ps1` 递归复制该目录。未改构建脚本、运行时、安装方式、包边界或第三方版权内容。
- **发布覆盖核验**：01 复制全部 `portable_config`（仅既有的 shaders/vs/cache/files 排除）；04 同样复制本次文件，且按既有边界排除 `script-assets`、fonts、licenses、`.vanta-version`。故共享模块、uosc、input.conf 和 script-opts 均会进入 01/04；起播 Logo 素材继续仅进入 01。
- **3.3 文档**：STATUS 与工作进度已追加；版本记录已切换为 v1.5.4 发布准备中并归档 v1.5.3；README 的安装顺序与包结构无变化，无需更新。
- **3.4 验证**：139 个 `scripts`/`script-modules` Lua 文件逐个 `loadfile` 通过；11 个本次 Lua/conf 改动为 UTF-8 无 BOM、LF；`git diff --check` 通过（仅 STATUS/工作进度已有 LF→CRLF 警告）。完整配置以 8K VP9 实样片加载并呈现，MediaInfo/uosc/起播 Logo 均已加载，未见本次目标 `error/fatal`；单帧参数被既有自动播放脚本带入后续文件，测试已超时结束，无残留 mpv 进程。
- **安装器**：VantaInstaller 源码无本次改动，沿用 `release/VantaInstaller-win-x64-v0.3.3.exe` 候选（69,653,458 bytes），无需重建或提升其独立版本。

### 2026-08-17 15:52 · v1.5.4 构建与本地门禁

- **构建**：执行 `build-all-packages.ps1 -Version 1.5.4` 成功，生成 01 Base、02 Extras 两卷、03 Faster-Whisper、04 Config；构建暂存 `build/` 已清理。
- **完整性**：全部归档 `7z t` 通过；02 分卷大小为 1,900 MB / 745.4 MB，符合 GitHub 限制。
- **内容门禁**：今日修改文件均在 01/04；01 含 `script-assets/`、`ffmpeg/ffmpeg.exe`、`.vanta-version=1.5.4`；04 排除 `script-assets/`、fonts、licenses、`.vanta-version`、`window_state.conf`。公开包无顶层 release/build/tmp/.git、项目根 backup、日志、pyc、Lossless 专有文件。
- **校验和**：01 `85F6CF77304C1D90B747FDAB971C203D6E080772FBB71B0B0B7A862EDF94C5E7`；02.001 `13C16A8D45AF98F8C0668DE8817946E16FD2FEB0A1AE1CC8AF29A8DD6FB35496`；02.002 `5CAF3795E9207E85E4A7A0AE0C58A69A9DE8E0A349FE726A04FAC119E22F048C`；03 `A320E9966AF0985CB9B216CE7912588AAF476B5D790B3C760CCC9B7517C4CCB8`；04 `19F7CF212F44E7AF12BC53B53C262D561F1D5B058E51A0AE22ADC7B541736621`；安装器 v0.3.3 `CB75EDA922D68C82A320589C0F47224C09481A99D76D32B73749BC6A03527D58`。
- **安装器与运行验证**：沿用 v0.3.3 安装器启动 4 秒探针通过；完整配置 8K VP9 实样片加载并呈现，无本次目标 `error/fatal`。既有 `auto_profiles` 条件警告和自动播放脚本超时已知且无残留进程。
- **下一步**：提交构建记录，创建并推送 `v1.5.4` 标签，使用 `gh release create` 上传 6 个公开资产；禁止上传私用全量包。

### 2026-08-17 16:06 · 暂停上传并完成个人私包

- **上传状态**：GitHub v1.5.4 草稿已创建，但上传速度异常；已终止 `gh` 上传进程。草稿当前只有 `04-mpv-config-v1.5.4.7z`，状态仍为 draft、非正式发布；未继续上传其他资产，也未上传私用全量包。
- **个人私包**：执行 `build-full-private.ps1 -Version 1.5.4 -OutputDir release` 成功，生成 `release/mpv-full-private-v1.5.4.7z`（3,004,654,678 bytes）；包含 01/02/04、Faster-Whisper 占位说明和 v0.3.3 安装器，不合并 03 运行时。
- **私包验证**：`7z t` 为 `Everything is Ok`；SHA-256 `D56D8E9299E7E51C7A1F9D755783046B315485D71C7594DC8C2EA17FEBA0C9A5`。该文件仅本地保留，禁止上传 GitHub Release。
- **待办**：后续恢复发布前需决定是否保留/删除当前草稿并补传其余公开资产；当前不要将草稿标记为正式发布。私包构建脚本留下的 `build/mpv-full-private-v1.5.4` 暂存目录待下次发布收尾时清理。

### 2026-08-17 16:38 · v1.5.4 直连上传与正式发布完成

- **降速根因**：Steam++ 正在监听本机 `80/443`，并持续把 `github.com`、`api.github.com`、`uploads.github.com` 写入 `hosts` 指向 `127.0.0.1`；`gh` 的上传连接实际经过 Steam++ 本地转发，速度约 500 KiB/s。仅修改 `hosts` 时规则会被立即写回。
- **环境处理**：临时退出 `Steam++.exe` 与 `Steam++.Accelerator.exe`，注释三条 GitHub 映射并刷新 DNS；解析恢复为 `github.com=20.205.243.166`、`api.github.com=20.205.243.168`、`uploads.github.com -> 20.205.243.161`。系统目录保留 `hosts.v154-upload-20260817-161841.bak` 与 `hosts.v154-upload-20260817-161958.bak`；重新启用 Steam++ 的 GitHub 加速后可能再次写回规则。
- **速度验证**：`gh` 上传连接核实为本机 `192.168.0.12` 直连 `20.205.243.161:443`；10 秒网卡采样稳定约 6.75-6.97 MiB/s。五个待传资产批量上传用时约 12 分 22 秒，命令退出码 0。
- **远端校验**：6 个公开资产均为 `uploaded`，远端大小与 GitHub `digest` SHA-256 逐项匹配本地；无多余资产、无个人私包。Release 已由草稿转为正式发布，非预发布：https://github.com/maxzrb/mpv-vanta-edition/releases/tag/v1.5.4 。
- **收尾**：删除 `build/mpv-full-private-v1.5.4` 暂存目录（11,747 个文件、约 5.0 GB）；`release/mpv-full-private-v1.5.4.7z` 仍仅在本地保留。本记录纳入发布收尾提交并推送。

### 2026-08-23 20:20 · VantaInstaller v0.3.4：ModelScope 魔搭镜像 + 自更新走镜像

- **镜像改动**：`DownloadMirror` 新增 `MirrorKind`（GitHubPrefix / ModelScopeDataset），注册表在自建镜像前新增 `modelscope`（`AerithDream/mpv-vanta-edition`）。映射规则：GitHub Release 资产 `{tag}/{文件名}` → `https://modelscope.cn/api/v1/datasets/AerithDream/mpv-vanta-edition/repo?Revision=master&FilePath={tag}%2F{文件名}`（URL 形状依据 ModelScope 官方 SDK v1.18 源码）。非 GitHub Release 地址不经该镜像，原样返回由调用方降级。
- **自更新改造**：`MainViewModel` 自更新按钮由浏览器直链改为镜像下载（`Aria2Service.DownloadWithMirrorsAsync` + `MirrorRegistry.All` 逐镜像降级，GitHub digest SHA-256 校验后启动新版并退出，全部失败回退浏览器兜底）；`InstallerUpdateInfo` 增加 `Sha256`，`PackageIntegrityService.ComputeSha256Async` 改 public 供跨工程复用；UA 统一升至 `VantaInstaller/0.3.4`。
- **验证**：Release 构建 0 警告 0 错误；`tmp/modelscope-resolve-test` 8 项断言全部通过；魔搭公开数据集（modelscope/chinese-poetry-collection）实测：匿名直链可用、Range 截断正常（200 + 截断正文，aria2 单连接降级不影响正确性）、百分号编码正确解码（`%2F` 子目录路径即官方 SDK 生产形态）、缺失文件返回 404（aria2 非零退出 → 自动降级下一镜像）；候选 exe 启动探针 3 秒存活（主窗口 Vanta Installer）。
- **候选产物**：`release/VantaInstaller-win-x64-v0.3.4.exe`（69,655,216 bytes），SHA-256 `A9E1C2718665739976662A50FAB1C48D3DA071117BD41F950254D0639AAF5736`；未创建 Release、未上传任何资产。
- **发布流程修订（经用户批准由 agent 代改）**：新增 7.1「同步上传 ModelScope 数据集（魔搭国内镜像）」检查项；第 8 节收尾新增 ModelScope 同步结果记录项；README.MD「方案二」增加魔搭下载渠道说明。
- **待办（用户侧）**：在魔搭创建公开数据集 `AerithDream/mpv-vanta-edition`，按 `v1.5.4/` 子目录上传六个公开资产（01、02.001、02.002、03、04、VantaInstaller exe）；首次上传时验证 02.001（1,900 MB）是否触及魔搭单文件上限，必要时改用 git/LFS 上传。数据集未就绪前安装器中该镜像显示「不可用」，属预期。

### 2026-08-23 21:05 · ModelScope 数据集创建与 v1.5.4 资产上传完成

- **命名空间更正**：本地魔搭登录账号为 AerithDream（非 maxzrb），`maxzrb` 命名空间创建 403；改用 `AerithDream/mpv-vanta-edition`。安装器 `MirrorRegistry`、README、发布流程 7.1、临时测试工程已同步改为该 ID；受影响的 GitHub 仓库引用已核对未被误改。
- **数据集**：已创建公开数据集 https://modelscope.cn/datasets/AerithDream/mpv-vanta-edition （visibility=5，license=other，描述注明为 GitHub Releases 同步镜像）。
- **上传**：v1.5.4 六个公开资产全部上传至 `v1.5.4/` 子目录（01、02.001、02.002、03、04、VantaInstaller v0.3.3 exe），单文件最大 1,992,294,400 字节的 02.001 上传成功，未触及魔搭单文件上限；上传脚本 `tmp/ms-upload.py`，日志 `tmp/ms-upload.log`。
- **核验**：SDK 文件列表逐一比对六个资产远端大小与本地一致；04（5,141,026 B）与 01（136,427,649 B）全量匿名下载回测 SHA-256 均与发布记录一致（04 `19F7CF21…621`、01 `85F6CF77…C5E7`）。无私用全量包上传。
- **候选重建**：数据集 ID 变更后重建 `release/VantaInstaller-win-x64-v0.3.4.exe`（69,655,226 bytes），SHA-256 `3C015888403BB52D1DE20A86D49B0F8C2898422E240292437B5F03AA45182934`，启动探针通过；仍未创建 Release、未上传。
- **注意**：现网已发布的 v0.3.3 安装器不含 ModelScope 镜像条目，该镜像随 v0.3.4 及后续版本生效；当前用户可经 README 的魔搭数据集链接手动下载。

### 2026-08-23 21:30 · 默认下载镜像改为 ModelScope

- **原自动机制（记录备查）**：设置页镜像下拉默认「自动检测（推荐）」且不持久化；下载时若仍为 auto，取最近一次「镜像检测」结果中可用且非官方的镜像按实测吞吐取最快，从未检测或全不可用则回落官方直连；测速仅在用户点击「镜像检测」时进行（逐镜像串行、8KB 预热 + 2 秒吞吐窗口、上限 32MB）。显式选中某镜像时单镜像下载、不自动降级。
- **本次改动**：`MirrorRegistry` 中 ModelScope 移至官方直连之后（自建镜像仍末尾），设置页默认选中 `modelscope`（下拉首项仍为自动检测，更名为「自动检测（测速择优）」）；自动机制本身未改。自更新走 `MirrorRegistry.All` 顺序降级，ModelScope 现为第二顺位。
- **验证与候选**：映射/顺序测试 8 项全过；重建 `release/VantaInstaller-win-x64-v0.3.4.exe`（69,655,231 bytes），SHA-256 `7F798AEFC327CB4E0F404612DD880231C51D90C22872E2F8A44F85912FE5E554`，启动探针通过；未创建 Release、未上传。

### 2026-08-23 21:55 · 移除镜像自动检测；自更新改为 ModelScope→GitHub 与关闭时替换

- **移除自动检测**：设置页镜像下拉删除「自动检测」选项（原默认项，从未测速时实际回落官方直连），`StartDownloadAsync` 删除 auto 分支，`_probedMirrors` 字段移除；下拉仅保留具体镜像，默认仍为 ModelScope。「镜像检测」按钮的逐镜像测速列表保留（供手动对比选择，不再参与自动选择）。
- **自更新降级顺序**：由全注册表顺序改为固定 `[modelscope, official]`——先 ModelScope 数据集，失败降级 GitHub 官方直连；两者皆失败仍回退浏览器直链。
- **关闭时替换升级**：下载并校验通过后不再立即启动新版退出，而是记录 `SelfUpdateReplacer.PendingNewExePath`、按钮显示「已下载·关闭后自动升级」；应用退出（OnExit）时调度隐藏 cmd 助手，以 `move /y` 重试循环（最多 30 次、waitfor 1s 延时）在进程解锁后把新 exe 覆盖到当前 exe 路径，脚本自清理。不依赖 tasklist/find 解析（规避非常规 PATH 环境下 find 被 GNU 工具遮蔽的问题）。
- **验证**：Release 构建 0 警告 0 错误；替换脚本隔离语义测试通过（目标 exe 运行期间 move 被挡、新文件原地保留；进程退出后 move 成功、哈希与新版一致、脚本自清理）；沙箱环境的挂起删除语义下最终态同样正确。候选重建 `release/VantaInstaller-win-x64-v0.3.4.exe`（69,655,720 bytes），SHA-256 `B0B7FE312114DE62641F5D18ED56CA2DC08F74EE3DB0C273C1B757AF3E481FA1`，启动探针通过；未创建 Release、未上传。

### 2026-08-23 22:20 · v0.3.5 发布：GitHub v1.5.4 与魔搭安装器资产替换（用户指定测试版）

- **版本**：应用户指定编译 v0.3.5（csproj、UA 字符串同步 0.3.5）；候选 `release/VantaInstaller-win-x64-v0.3.5.exe`（69,655,736 bytes），SHA-256 `12AA0706591045FC8B608A33D840CB404DCD83100A2C53562FE758E2395572C1`，启动探针通过。
- **GitHub v1.5.4 资产替换**：先按 REST 数字资产 ID 删除旧 `VantaInstaller-win-x64-v0.3.3.exe`（GraphQL 节点 ID 会 404），再上传 v0.3.5（`gh release upload --clobber`）。远端核对：恰好 6 个资产、单一安装器资产、state=uploaded、远端 digest `sha256:12aa0706…` 与本地一致；Release 说明中安装器文件名与校验和已同步更新（v0.3.5 / 12AA0706…）。
- **魔搭同步（发布流程 7.1）**：`v1.5.4/VantaInstaller-win-x64-v0.3.5.exe` 上传完成，匿名全量回测 SHA 与 GitHub digest 一致。注意：魔搭 API 禁止删除文件（10020301011 Deletion restricted to web console），旧 v0.3.3 仍留在数据集 `v1.5.4/` 中，不影响更新器（按 GitHub 文件名精确映射），如需完全对齐可在网页端手动删除。
- **文档**：README 安装器版本引用更新为 v0.3.5；`version/版本迭代记录.md` v1.5.4 节以带日期注记方式更新（保留 v0.3.3 历史 SHA）。
- **大改动 Gate**：不触发——VantaInstaller 附属工具版本迭代（发布流程 3.2 明确豁免），01~04 公开包未动。
- **测试提示（用户）**：运行本地 v0.3.4 候选即可见「有新版 0.3.5」徽标，点击应经魔搭下载（约 70MB）、SHA 校验后显示「已下载·关闭后自动升级」，关闭程序后 exe 应被自动替换；再次启动版本应为 v0.3.5 且徽标消失。

### 2026-08-23 22:50 · v0.3.6：自更新替换改为「规范新文件名落地 + 删除旧名」

- **问题（用户实测反馈）**：v0.3.5 自更新后内容已升级但 exe 文件名未变（替换为 move 覆盖到旧路径，文件名保留旧版本号）。
- **修复**：`SelfUpdateReplacer` 改为两段式——异名场景把新 exe 以自带版本号的规范文件名 move 到当前 exe 同目录，并在进程退出后 `del` 旧文件名的 exe；同名场景（当前 exe 已是规范新名）保持覆盖式 move 重试。重试/延时机制不变（move/del 失败即重试，waitfor 1s，上限 30 次）。
- **验证**：隔离语义测试六项全过（新名文件即时落地、旧名运行期间保留、退出后删除、内容哈希正确、源文件消费、脚本自清理；测试脚本汇总判定的 FAIL 为脚本自身在判定前删除了目录的顺序问题，不影响结论）。
- **发布**：v0.3.5 资产已从 GitHub v1.5.4 删除并上传 v0.3.6（远端 digest `sha256:da56b55b…` 与本地一致、单一安装器资产）；Release 说明、README、版本迭代记录同步更新；魔搭 `v1.5.4/VantaInstaller-win-x64-v0.3.6.exe` 已上传并匿名回测哈希一致。魔搭数据集中 v0.3.3 / v0.3.5 两个旧 exe 仍留存（API 禁删，网页端可清理）。
- **候选**：`release/VantaInstaller-win-x64-v0.3.6.exe`（69,655,892 bytes），SHA-256 `DA56B55B5BC511BA83E1557CB0B3B3BC7015D2A3D4C469E7BF240E69FC79F92B`，启动探针通过。

### 2026-08-23 23:25 · v0.3.7：首页自动检测 mpv 版本并显示更新建议

- **功能**：启动/回到首页时，检测到 Vanta 安装则读取 `portable_config\.vanta-version`，与 GitHub 最新正式 Release 比对（`UpdateService.CheckLatestAsync`）；有新版时首页「当前安装」卡片下方显示「MPV Vanta Edition 有可用更新」建议卡（含版本对比文本与「去更新」按钮）。非 Vanta 安装、无版本标记、网络失败均静默不显示。
- **实现**：`HomeViewModel.UpdateMpvUpdateSuggestionAsync`（会话内缓存 Release 查询，仅本地版本变化时重查）；`MainViewModel.GoSettingsForUpdate` 跳转设置页并自动执行 `CheckUpdateCommand`；`HomeView.xaml` 新增建议卡片（样式对齐现有 ui:Card/按钮规范）。
- **发布**：GitHub v1.5.4 资产 v0.3.6 删除、v0.3.7 上传（digest `sha256:fdabf457…` 与本地一致、单一安装器资产），Release 说明同步；魔搭 `v1.5.4/VantaInstaller-win-x64-v0.3.7.exe` 上传并匿名回测哈希一致。README/版本迭代记录同步更新。
- **候选**：`release/VantaInstaller-win-x64-v0.3.7.exe`（69,656,780 bytes），SHA-256 `FDABF457F1A5959D103838B35D5376932D0BC9F6AA8680FD63C0140DC3FEDA62`，启动探针通过。
- **说明**：魔搭数据集中 v0.3.3/v0.3.5/v0.3.6 旧 exe 留存（API 禁删，网页端可清理）；启动时首页建议与安装器自更新检查各自独立请求一次 GitHub API，互不影响。

### 2026-08-23 23:59 · v0.3.8：一键升级（自动下载全部增量包并执行覆盖升级）

- **功能**：首页更新建议卡新增「一键升级」。检测到 Vanta 安装时：查询最新 Release → 将全部增量包资产（01、02 两卷、03、04，排除安装器 exe）下载到 `文档\MPV Vanta Edition\packages\vX.Y.Z\`（ModelScope→GitHub 降级，已存在且大小一致的跳过，aria2 断点续传）→ 直接进入安装页自动执行覆盖升级（复用 InstallEngine 的配置备份、SHA-256 风险拦截、进度与完成页）。未检测到 Vanta 安装或网络异常回退设置页手动流程；升级不改动文件关联。
- **实现**：`Vanta.Core/Services/UpgradePackageDownloader.cs`（资产筛选 + 逐包下载，进度回调统一「已完成数/总数/当前百分比」口径）；`AppSession.UpgradeReleaseInfo` 触发安装页下载阶段（进度分段：下载 0~45%、安装 45~100%）；`MainViewModel.OneClickUpgradeAsync` 组装会话并直跳安装页自启。
- **验证**：Release 构建 0 警告 0 错误；映射/顺序/资产筛选测试 9 项全过（新增资产筛选断言）；候选启动探针通过。端到端升级需远端出现 v1.5.5+ Release 实测（当前 v1.5.4 已是最新，无法真实触发）。
- **发布**：GitHub v1.5.4 资产 v0.3.7 删除、v0.3.8 上传（digest `sha256:fe2c8b20…` 与本地一致、单一安装器资产），Release 说明同步；魔搭 `v1.5.4/VantaInstaller-win-x64-v0.3.8.exe` 上传并匿名回测哈希一致（首次回测传输中断，断点续传重试后完整）。README/版本迭代记录同步。
- **候选**：`release/VantaInstaller-win-x64-v0.3.8.exe`（69,658,983 bytes），SHA-256 `FE2C8B20D56F94B721C9067DEC69F89DE10C2A16244A901F65959EBA045865E7`。

### 2026-08-24 00:15 · v0.3.9：一键升级入口调整与下载目录改临时目录

- **入口调整（按用户要求）**：首页更新建议卡按钮恢复为「去更新」（跳设置页自动检查更新，文本相应更新）；「一键升级」按钮移至设置页「检查更新和下载增量包」卡片下方独立卡片，点击后全自动（下载 + 覆盖升级）。`SettingsViewModel` 新增 `MainViewModel` 引用透出命令（构造函数签名变更，仅 MainViewModel 一处调用）。
- **下载目录**：一键升级增量包下载目录由 `文档\MPV Vanta Edition\packages\vX.Y.Z\` 改为 `%TEMP%\VantaInstaller\upgrade\vX.Y.Z\`（按用户要求放 tmp；同版本重复升级仍可跳过已存在文件/断点续传，临时目录由系统清理策略回收）。
- **发布**：GitHub v1.5.4 资产 v0.3.8 删除、v0.3.9 上传（digest `sha256:5bbd5b79…` 与本地一致、单一安装器资产），Release 说明同步；魔搭 `v1.5.4/VantaInstaller-win-x64-v0.3.9.exe` 上传并匿名回测哈希一致。README/版本迭代记录同步。
- **候选**：`release/VantaInstaller-win-x64-v0.3.9.exe`（69,659,190 bytes），SHA-256 `5BBD5B791AEC0B22CACCAB59B9E055EB933D16035779F399D555380E13B58AC8`，Release 构建 0 警告 0 错误、启动探针通过。

### 2026-08-24 00:35 · v0.3.10：侧栏版本号/更新徽标布局微调

- **布局**：侧栏底部版本号/更新徽标整体右移 13px 与导航图标左缘对齐（原 Margin 0→13）；更新徽标由版本号右侧改为版本号正下方 4px（StackPanel 改纵向，徽标左对齐不拉伸）。
- **发布**：GitHub v1.5.4 资产 v0.3.9 删除、v0.3.10 上传（digest `sha256:b57191ef…` 与本地一致、单一安装器资产），Release 说明同步；魔搭 `v1.5.4/VantaInstaller-win-x64-v0.3.10.exe` 上传并匿名回测哈希一致。README/版本迭代记录同步。
- **候选**：`release/VantaInstaller-win-x64-v0.3.10.exe`（69,659,423 bytes），SHA-256 `B57191EFE4A2C2E188486942FDE62D12DB582B86D2B6E3A9B295A7E6311FAE44`，构建 0 警告、启动探针通过。（注：本次首次构建进程被取消后重建，最终产物为含完整布局调整的版本。）

### 2026-08-24 00:50 · v0.3.11：更新徽标恢复版本号右侧（仅保留右移）

- **布局回退（按用户要求）**：撤销 v0.3.10 的「徽标移至版本号下方 4px」纵向布局，恢复徽标在版本号右侧横向排列；仅保留整行右移 13px 与导航图标左缘对齐。
- **发布**：GitHub v1.5.4 资产 v0.3.10 删除、v0.3.11 上传（digest `sha256:dde403a1…` 与本地一致、单一安装器资产），Release 说明同步；魔搭 `v1.5.4/VantaInstaller-win-x64-v0.3.11.exe` 上传并匿名回测哈希一致。README/版本迭代记录同步。
- **候选**：`release/VantaInstaller-win-x64-v0.3.11.exe`（69,659,198 bytes），SHA-256 `DDE403A109C6F8F9673BF55A47E95D15374CB9291F744A671EA7E2611E928AAF`，构建 0 警告、启动探针通过。

### 2026-08-26 17:03 · uosc 进度条双向缓冲提示 + VantaInstaller 设置入口

- **uosc 状态**：`demuxer-cache-state/seekable-ranges` 的规范化结果新增为 `state.cached_ranges`；时间线取包含当前播放点的连续缓存区间，当前位置之前表达后向缓冲，之后表达前向缓冲，旧协议以 `cache-duration` 兜底前向范围。
- **绘制**：`Timeline.lua` 新增主题强调色缓冲层，默认透明度 0.18；缓冲层复用进度条 `bar_visibility`，因此展开时间线、窗口底部迷你进度线及渐隐动画保持同步。新增 `timeline_buffer` / `timeline_buffer_opacity`，保留原版 `timeline_cache=no` 避免纹理重复。
- **VantaInstaller**：`UoscConfigService` 统一读写菜单延迟、双向缓冲开关和透明度，保留注释/行序/UTF-8 LF；设置页新增开关与 5%～40% 透明度滑块，纳入既有“保存 mpv 设置”修改检测。
- **验证**：`dotnet build VantaInstaller/src/Vanta.Installer/Vanta.Installer.csproj -c Debug --no-restore` 通过（0 警告、0 错误）；配置服务 0.18→0.27 往返、布尔值和注释保留探针通过；完整 mpv 配置加载短 lavfi 视频时 uosc 无 Lua/加载错误；`git diff --check` 通过；目标文件均为 UTF-8 无 BOM、LF。
- **Git**：`git fetch --prune` 后 `HEAD...origin/master = 0/0`；工作树原先已有 VantaInstaller、README、发布记录等未提交改动，本次只增量修改 6 个功能文件及两份 HandShake 记录，未提交。

### 2026-08-26 17:12 · 双向缓冲可见性修正与本地缓存启用

- **用户反馈与根因**：本地文件看不到缓冲是因为 mpv 默认 `cache=auto` 通常不为普通本地文件启用 demuxer 缓存；`demuxer-readahead-secs=15` 只限制已启用缓存的预读，并不负责开启缓存。网络视频的后向范围已经进入 `state.cached_ranges`，但此前与不透明的已播放进度使用同一强调色整高叠加，视觉上不可辨。
- **修正**：`mpv.conf` 新增 `cache=yes`，本地与网络统一启用缓存，继续受现有 `demuxer-max-bytes=300MiB`、`cache-secs=15`、`demuxer-readahead-secs=15` 约束。`Timeline.lua` 改为后向缓冲用当前主题 `accent_text` 斜纹覆盖已播放实心段，前向缓冲用浅 `accent` 覆盖未播放轨道；两侧在播放点分界，并继续共用 `bar_visibility` 和 `timeline_buffer_opacity`。
- **安装器文案**：VantaInstaller 设置页说明同步为“左侧后向斜纹 / 右侧前向浅色”，现有开关与透明度滑块继续同时控制两侧。
- **验证**：120 秒本地测试视频在约 28.03 秒时，mpv IPC 返回包含播放点的 `seekable-ranges=0.00～119.97`，确认本地前后向缓存同时存在；完整配置 uosc 加载无 Lua 错误；VantaInstaller Debug 构建 0 警告/0 错误；`git diff --check` 通过。

### 2026-08-26 17:20 · VantaInstaller 暴露完整 mpv 缓存设置

- **设置组**：`MpvSettingsSchema` 新增“缓存”分组，暴露 `cache`（开启/自动/关闭）、`demuxer-max-bytes`（32～1024 MiB）、`demuxer-max-back-bytes`（0～512 MiB）、`cache-secs`（1～120 秒）、`demuxer-readahead-secs`（0～120 秒）。文案明确后向缓存按字节限制、对应时长随码率变化。
- **单位滑块**：`MpvOption` 新增 `Step`、`ValueSuffix`、`DisplaySuffix`；`MpvOptionItem` 使用 InvariantCulture 解析/量化滑块，界面显示 `300 MiB`，配置写回 `300MiB`，其它无单位滑块保持兼容；滑块值显示宽度增至 70。
- **默认配置**：`mpv.conf` 将后向缓存上限从注释示例改为显式 `demuxer-max-back-bytes=50MiB`，安装器读取确定值；缓存相关注释修正为前向/后向的真实含义。
- **验证**：VantaInstaller Debug 构建 0 警告/0 错误；真实加载 `mpv.conf` 后五项值为 `yes / 300MiB / 50MiB / 15 / 15`；MiB 滑块显示与序列化通过；隔离写回 `no / 384MiB / 64MiB / 20 / 12` 五项均正确且保留中文注释。

### 2026-08-26 17:23 · 缓冲斜纹不再侵入播放圆点

- **问题**：bar 样式为保证后向斜纹覆盖已播放实心段，缓冲层绘制在进度之后，也会覆盖播放圆点靠近缓冲边界的部分。
- **修正**：`Timeline.lua` 将实心进度和播放圆点拆分为两个绘制函数；缓冲层与热图完成后最后绘制圆点，确保圆点始终为完整主题色且处于最上层，前后向缓存范围本身不截断。
- **验证**：完整 mpv 配置短视频运行探针无 Lua/uosc 错误；`git diff --check` 通过。

### 2026-08-26 17:29 · 迷你进度线排除缓存 + 其它菜单持久化开关

- **迷你进度线**：`Timeline.draw_buffer()` 在 `has_minimized_progress` 时直接返回；普通窗口底部 1.2 px 迷你进度线只显示已播放进度，不绘制前向浅色或后向斜纹。展开时间轴行为不变。
- **运行时入口**：uosc 新增 `timeline-buffer-toggle` 脚本消息及 `user-data/uosc/timeline-buffer` 状态发布；`input.conf` 新增“其它 > 时间轴双向缓冲 > 开/关”，动态菜单根据 user-data 显示勾选状态。
- **持久化**：开关默认沿用 `timeline_buffer=yes`；运行时切换立即调用 `persist_uosc_option()` 写回 `uosc.conf`。VantaInstaller 开关继续读写同一配置项，文案明确仅作用于展开时间轴。
- **验证**：mpv IPC 实测 `yes → no → yes`，user-data 分别发布 `no/yes`，最终文件为 `timeline_buffer=yes`；VantaInstaller Debug 构建 0 警告/0 错误；`git diff --check` 通过。

### 2026-08-26 17:42 · v1.5.5 发布前置审计

- **版本确认**：用户确认 mpv 项目版本 `1.5.5`；VantaInstaller 因源码继续增加完整缓存设置和 uosc 缓冲入口，必要递增为独立版本 `0.3.12`。
- **3.1 Git**：已执行 `git fetch --prune`；`HEAD...origin/master = 0/0`。当前未提交改动按功能、安装器、配置、文档和记录归入本次发布；`.zcode/` 计划文件不纳入提交/包。
- **3.2 Gate**：不触发。包数量/编号/覆盖顺序、构建脚本、7-Zip 参数、mpv 核心/运行时、安装方式、版权边界和分卷规则均不变；VantaInstaller 功能/界面变化按流程明文豁免。
- **3.3 文档**：`version/版本迭代记录.md` 已建立 v1.5.5 当前版本和待补校验区；README 安装器名称更新为 v0.3.12；本条记录作为发布前清单，构建后补 SHA-256、资产和最终状态。
- **3.4 构建入口**：已审阅 `build-all-packages.ps1`、`build-01-base.ps1`、`build-02-extras.ps1`、`build-03-fasterwhisper.ps1`、`build-04-config.ps1`、`build-full-private.ps1`；均覆盖当前 portable_config/安装器候选/私包既定边界，无需修改发布流程或构建脚本。

### 2026-08-26 18:12 · v1.5.5 本地构建与归档验收

- **构建**：`build-all-packages.ps1 -Version 1.5.5 -IncludePrivate` 退出码 0；01 Base、02 Extras（`.001/.002`）、03 Faster-Whisper、04 Config、`mpv-full-private-v1.5.5.7z` 均生成，构建暂存 `build/` 已清理。
- **安装器**：VantaInstaller v0.3.12 的 Release self-contained single-file 发布候选启动探针通过；私包内置 exe 与 `release/VantaInstaller-win-x64-v0.3.12.exe` SHA-256 均为 `820010E22CD82A7AB1E3E9B78F5E9B0B5E6E6A1D8CFDA6CCAD7906F617492BFA`。
- **完整性**：五个归档逐一执行 `7z t` 并全部返回 `Everything is Ok`；02 分卷为 1,992,294,400 + 781,554,918 bytes，单卷低于 2 GB。
- **内容门禁**：01 含启动素材、随包 `ffmpeg/ffmpeg.exe` 和版本标记；02 含 shaders/VapourSynth；03 含 Faster-Whisper 运行时；04 含 uosc 配置且排除启动素材/fonts/licenses/版本标记/window state；私包含 Faster-Whisper 占位说明但不含 03 运行时。所有公开包和私包均无 release/build/tmp/.git、Python 缓存、日志、Lossless/Steam 专有文件。
- **版本标记**：根目录和 01 包内 `portable_config/.vanta-version` 均为 `1.5.5`（UTF-8、无 BOM、无换行）。
- **SHA-256**：01 `26DC2054870D8CBF5DB5CBF047C45C5933FF309D6F0E0C3B73C01F8E4F02DA34`；02.001 `728E4ABD722783378859A2454576EFE1C8B807BF351C55E4B8F8BA66379A67DA`；02.002 `B3FFEF6FA0378C2CFA8DE2BFE20987FB5A7C87BE15339C0AD3343EDFCB9937E5`；03 `D929EE669F8FCD8CBAD69D99D9CE5CC0D4CD9BA581C60D0A5387CEBC64AE06F0`；04 `B0106B0403605156A8B3014852C23B150EAF97AF7087FF45EADCCFBFE472B52B`；Installer `820010E22CD82A7AB1E3E9B78F5E9B0B5E6E6A1D8CFDA6CCAD7906F617492BFA`；私包 `2CCF6B2AAEA74DA491AE7493DC754230E89620CC5545A73FC7607045863CD67A`（仅本地）。
- **下一步**：提交本构建记录，创建并推送 `v1.5.5` 标签，随后上传 GitHub 6 个公开资产；私包不得上传。ModelScope 同步结果在远端发布后补录。

### 2026-08-26 18:42 · v1.5.5 正式发布与镜像收尾

- **GitHub Release**：标签 `v1.5.5` 已推送；Release `https://github.com/maxzrb/mpv-vanta-edition/releases/tag/v1.5.5` 已正式发布，`isDraft=false`、`isPrerelease=false`，恰好 6 个公开资产，无重复/临时资产，无私用全量包。
- **远端核验**：6 个 GitHub 资产的大小与远端 digest SHA-256 逐项匹配本地：01 `26DC2054870D8CBF5DB5CBF047C45C5933FF309D6F0E0C3B73C01F8E4F02DA34`；02.001 `728E4ABD722783378859A2454576EFE1C8B807BF351C55E4B8F8BA66379A67DA`；02.002 `B3FFEF6FA0378C2CFA8DE2BFE20987FB5A7C87BE15339C0AD3343EDFCB9937E5`；03 `D929EE669F8FCD8CBAD69D99D9CE5CC0D4CD9BA581C60D0A5387CEBC64AE06F0`；04 `B0106B0403605156A8B3014852C23B150EAF97AF7087FF45EADCCFBFE472B52B`；Installer `820010E22CD82A7AB1E3E9B78F5E9B0B5E6E6A1D8CFDA6CCAD7906F617492BFA`。
- **Release Note**：已根据用户追加规范调整为只保留更新内容；每条变更单独一行，使用 `[新增]`、`[更改]`、`[移除]` 前缀，不再放安装顺序、校验和或安装器说明。
- **ModelScope**：`AerithDream/mpv-vanta-edition/v1.5.5/` 六个公开资产均上传成功；六条匿名直链 HTTP 200 且 Content-Length 与本地一致；01、04、VantaInstaller 下载回测 SHA-256 与本地一致。私包未上传。
- **流程更新**：按用户明确要求，《发布流程.md》已追加 Release Note 规则，并将旧的“说明包含安装顺序/校验和”要求改为“Release Note 只保留更新内容，其余信息写入版本记录或包内 README”。
- **收尾提交**：本条将与流程规范增量一并提交为 `docs: record v1.5.5 release results`；保留用户原有的《发布流程.md》其它未提交改动与 `.zcode/` 临时目录，不做清理或覆盖。

### 2026-08-27 17:43 · uosc MediaInfo 左上角误显问题定位

- **现象**：鼠标靠近播放器左上角时，底部 MediaInfo 媒体参数胶囊再次渐显。
- **根因**：`MediaInfo` 在 `Element:init()` 时继承默认坐标 `(0,0,0,0)`，实际绘制胶囊时只保存 `layout_x/layout_y/layout_width`，没有调用 `set_coordinates()` 更新自身命中矩形；因此接近左上角原点会被误判为接近 `media_info`。
- **历史**：`MediaInfo.lua` 随提交 `e87365b`（2026-08-07）首次加入；v1.3.2 及更早没有该文件，v1.4.1～v1.5.5 均包含同一遗漏，期间没有补上命中坐标同步。
- **交互核对**：胶囊中的硬解、分辨率、动态范围、视频编码、帧率、音频编码、声道布局和网络/码率均为状态展示；只有“实时码率/平均码率 + 数值”区域注册了点击，用于循环切换两种码率显示。
- **本次变更**：未修改运行代码或配置；仅记录诊断。后续若修复，应让 MediaInfo 的实际绘制范围参与自身 proximity 计算，同时保留胶囊的码率点击命中区。
- **Git 状态**：保留用户已有的 `发布流程.md` 未提交改动和 `.zcode/` 未跟踪目录，未做清理。

### 2026-08-27 17:58 · uosc 底部显隐链修复

- **显隐关系**：保留 `Controls → Timeline/MediaInfo → Speed` 的既有锚定关系；`Controls` 和 `Timeline` 的 proximity 改为只计算鼠标 Y 轴距离，`MediaInfo` 禁用自身 proximity，`Speed` 继续直接复用 MediaInfo 可见度。
- **左上角误显**：MediaInfo 不再让基类默认 `(0,0,0,0)` 参与显隐，鼠标靠近左上角不会再暴露底部胶囊。
- **悬停渐隐**：移除 `get_timeline_hover_fade()` 的水平范围门槛，并将速度区域保持可见判断改为仅检查 Y 轴；同一高度水平移动不改变底部组件显隐。
- **改动文件**：`portable_config/scripts/uosc/elements/Element.lua`、`Controls.lua`、`Timeline.lua`、`MediaInfo.lua`、`lib/utils.lua`。
- **验证**：139 个 Lua 文件 LuaJIT `loadfile` 全部通过；完整配置空闲启动 6 秒和短视频 3 帧启动均退出码 0，未发现 `[e]/[f]`、Lua error 或 `Cannot find`；目标文件 UTF-8 无 BOM/LF，`git diff --check` 通过（仅 Git 的 LF→CRLF 提示）。
- **Git 状态**：功能代码及两份 HandShake 记录为本轮改动；继续保留用户已有的 `发布流程.md` 改动和 `.zcode/` 未跟踪目录，未提交。

## 2026-08-27 18:25

### v1.5.6 发布准备与 02/03 复用规则

- **流程决定**：用户明确批准将“02/03 打包输入确认未变化后原样复用上一版本归档”的规则写入《发布流程.md》，用于节约大型资源包重复压缩时间；该流程文件变更已获授权，不再按 §3.2 阻断本次发布。
- **复用核验**：`portable_config/shaders`、`portable_config/vs`、`vs-plugins`、`vs-coreplugins`、`vs-scripts` 和 `Faster-Whisper-XXL` 均无 Git 跟踪改动，且相对 v1.5.5 产物时间点没有文件修改；来源 v1.5.5 归档 `7z t` 已通过，待复制后对新文件名再次测试。
- **发布构成**：01/04 因含本次 uosc 修复将重建；02 两卷和 03 计划逐字节复制为 v1.5.6 规范文件名；VantaInstaller v0.3.12 因源码无改动沿用；私用全量包本次不重建、不上传。
- **记录状态**：已建立 v1.5.6 版本记录占位；待完成构建、内容门禁、GitHub Release、ModelScope 同步和发布后收尾。

## 2026-08-27 18:53

### v1.5.6 本地构建与发布前验收

- **产物**：01 Base 和 04 Config 已用 v1.5.6 重建；02 两卷、03 Faster-Whisper 与 v1.5.5 来源归档逐字节一致后改名复用；VantaInstaller v0.3.12 因源码无改动沿用。
- **归档测试**：新文件名下 01、02（两卷）、03、04 均 `7z t` 通过；02 分卷分别为 1,992,294,400 和 781,554,918 bytes，均低于 2 GiB。
- **内容门禁**：01 的 `script-assets/`、`ffmpeg/ffmpeg.exe`、`.vanta-version` 存在；04 排除启动素材、fonts、licenses、`.vanta-version` 和 `window_state.conf`；公开包无根级 backup、构建/发布泄漏、缓存、调试产物或 Lossless/Steam 专有文件。
- **版本标记**：根目录和 01 包内 `.vanta-version` 均为 5 bytes 的 `1.5.6`，无 BOM、无换行；`build/` 暂存已清理。
- **运行验证**：139 个 Lua 文件语法通过；完整配置空闲 6 秒、短视频 3 帧（显式 `--idle=no`）和 VantaInstaller 启动探针通过。
- **校验和**：本地 SHA-256 已写入 `version/版本迭代记录.md`；待提交构建记录、推送 v1.5.6 标签、创建 GitHub Release 并同步 ModelScope。

## 2026-08-27 19:16

### v1.5.6 GitHub/ModelScope 发布收尾

- **GitHub**：v1.5.6 Release 已为正式、非草稿、非预发布状态，共 6 个公开资产；远端文件名、大小和 GitHub digest SHA-256 均与本地一致。
- **ModelScope**：`AerithDream/mpv-vanta-edition/v1.5.6/` 六个公开资产上传成功；匿名直链均 HTTP 200，`Content-Length` 与本地一致；私用全量包未上传。
- **提交与标签**：`master` 与 `origin/master` 已同步，`v1.5.6` 标签已推送；待将本次发布收尾记录提交为 `docs: record v1.5.6 release results`。
- **版本边界**：用户随后提出的 HDR 参考白亮度档位扩展属于下一次配置变更，未混入已发布的 v1.5.6。

## 2026-08-27 19:26

### v1.5.6 HDR 参考白亮度档位覆盖

- **用户决定**：将 `Ctrl+T` 序列从 `auto → 100 → 203` 扩展为 `auto → 50 → 80 → 100 → 203 → 300 → 400`，并明确覆盖现有 v1.5.6 Release。
- **代码改动**：已修改 `portable_config/input.conf`，仅增加 `hdr-reference-white` 的循环档位；mpv 支持范围和其它 HDR 参数不变。
- **资产范围**：配置进入 01 Base 与 04 Config，因此只需重建并覆盖这两个同名资产；02 两卷、03 和 VantaInstaller v0.3.12 保持原资产。
- **远端策略**：保留现有 v1.5.6 标签，待本地构建/验证通过后使用同名 `--clobber` 覆盖 GitHub 01/04，并覆盖 ModelScope 对应文件；Release Note 与版本记录同步增加本次更改。

## 2026-08-27 19:32

### v1.5.6 HDR 覆盖修订本地构建完成

- **包内配置**：01 Base 与 04 Config 均已重建，包内 `input.conf` 已核验包含 `hdr-reference-white auto 50 80 100 203 300 400`。
- **本地验收**：01/04 新归档 `7z t` 通过，内容门禁、根目录和 01 包内 `1.5.6` 版本标记、02/03 原样复用字节校验均通过。
- **功能验收**：完整配置空闲启动 6 秒、短视频 3 帧启动通过；02/03 和 VantaInstaller v0.3.12 未重新构建。
- **新校验和**：01 `8076F0B0591E0BEB1552B23BE3BAED5B5F3A75FC13A37F0D71367EC2A83C877C`（136,429,758 bytes）；04 `AA09A779B4D875ADBDF2F692571FA9DA129FAE423067821928013C314543AB45`（5,142,281 bytes）。
- **远端状态**：GitHub/ModelScope 仍需用新 01/04 覆盖；02/03/Installer 远端资产保持不变。

## 2026-08-27 19:46

### v1.5.6 HDR 覆盖与私包完成

- **GitHub 覆盖**：01/04 同名资产已使用 `--clobber` 覆盖；6 项资产无重复，新的本地 SHA-256 与 GitHub digest 全部一致，Release 保持正式非草稿状态，Release Note 已同步 HDR 档位说明。
- **ModelScope 覆盖**：01/04 同名文件上传完成；六项匿名直链均 HTTP 200、大小一致，覆盖后的 01/04 下载 SHA-256 与本地一致。
- **私包**：按用户要求在上传完成后生成 `release/mpv-full-private-v1.5.6.7z`；`7z t`、门禁、HDR 配置、`1.5.6` 标记、Faster-Whisper 占位说明和内置安装器 SHA-256 均通过。私包未上传。
- **私包校验**：3,004,610,217 bytes；SHA-256 `D84E2D8FFD5DB1FDC333AC22166AEFCC826715798F1C7E2C9CAB541E95047ECC`；构建暂存已清理。
- **记录状态**：待提交 HDR 覆盖及私包生成的最终记录；v1.5.6 标签保持原标签，不重新打标签。

## 2026-09-05 19:56

### HDR 参考白默认值与持久化

- **用户需求**：HDR 参考白亮度不应每次打开都回到 203；默认使用 `auto`，查询失败时以 203 兜底，并持久化用户通过 `Ctrl+T` 选择的值。
- **代码改动**：`portable_config/mpv.conf` 将 `hdr-reference-white=auto` 设为显式全局默认；`portable_config/profiles.conf` 移除 `[HDR]` 中的固定值，避免每次 HDR 文件载入覆盖持久化值；`portable_config/script-opts/persist_properties.conf` 将 `hdr-reference-white` 加入已有 `volume,vf` 持久化白名单。
- **持久化决策**：依赖 mpv 官方 `auto` 行为；当前配置注释已说明 Windows 显示器查询失败时回退到 `203 cd/m²`。不在条件 profile 中再次写入 203/auto，以免覆盖已恢复的用户选择。
- **验证**：`git pull --ff-only` 已是最新；LuaJIT 语法通过；`input.conf` mpv 解析退出码 0；`mpv --show-profile=HDR` 确认 profile 不再包含 `hdr-reference-white`；完整配置 `idle=no` 启动 smoke test 退出码 0；隔离 mpv 往返测试确认 `auto → 100 → 保存 100 → 下次启动恢复 100`；3 个修改文件均为 UTF-8 无 BOM、LF，`git diff --check` 通过。
- **未改动**：`portable_config/input.conf` 的 7 档 `Ctrl+T` 序列保持 `auto → 50 → 80 → 100 → 203 → 300 → 400`；项目版本和已发布资产不变，本次未执行打包或发布。
- **Git 状态**：`master` 与 `origin/master` 同步；本次修改的 3 个 HDR 配置文件未提交；用户原有 `portable_config/script-opts/window_size_position.conf` 修改及 `.zcode/` 未跟踪目录均保留。
- **下一步**：建议用户实际播放 HDR 片源，用 `Ctrl+T` 选择一个值并重启 mpv 确认；提交前可将本次 3 个配置文件单独 `git add`，不要误纳入用户已有改动。

## 2026-09-05 20:15

### 全局设置持久化审计与补充

- **审计结果**：窗口尺寸/位置/置顶、音频直通模式、启动页、idle 图片、uosc 界面状态和音量已有独立或统一持久化；GLSL 着色器按现有约束不跨启动恢复。
- **本次纳入统一白名单**：`audio-device`、`title-bar`、`tone-mapping`、`hdr-compute-peak`、`hr-seek-framedrop`，以及字幕字体、ASS 样式覆盖、视频信息传递、颜色兼容、时序修复、bidi 兼容和黑边输出等全局字幕偏好。
- **边界决策**：轨道选择、速度、延迟、画面变换、循环、逐文件滤镜和可见性等受 `reset-on-next-file` 约束的状态不持久化；`target-trc`、`target-colorspace-hint`、ICC、gamut、混合字幕、PGS 输出等会被 profile 改写的选项不纳入；声道/独占模式继续交由音频直通脚本管理。
- **profile 处理**：`HDR2SDR` 中的 `tone-mapping=auto` 和 `hdr-compute-peak=auto` 保留为启动默认，持久化脚本启动后恢复用户值；未发现条件 profile 对新增白名单的运行时覆盖。
- **验证**：新增白名单下临时隔离 mpv 完成“写入 JSON → 第二次启动读回”的往返测试；LuaJIT 语法、完整配置 `HDR` 启动、profile/输入配置检查及 `git diff --check` 均通过；测试临时目录和脚本已清理。
- **未改动**：项目版本、发布资产、`input.conf` 的 HDR 7 档快捷键序列和用户已有的 `window_size_position.conf`、`.zcode/` 均保持原状；本次未执行打包或发布。
- **Git 状态**：`master` 与 `origin/master` 同步；本次 3 个配置文件及 HandShake 记录未提交，用户已有改动继续保留。
- **下一步**：建议实际切换一次新增菜单项并重启确认体验；提交时只暂存本次配置与记录文件，避免带入用户已有改动。

## 2026-08-27 19:33

### v1.5.6 覆盖后生成私用全量包

- **用户追加决定**：先完成 GitHub/ModelScope 的 01/04 同名资产覆盖及远端核验，再生成私用全量包。
- **私包范围**：使用覆盖后的 v1.5.6 01、原样复用的 02、覆盖后的 04，加上 Faster-Whisper 占位说明和最新 VantaInstaller；私包只在本地保留，禁止上传。

## 2026-09-05 20:32

### v1.5.7 发布前置检查

- **版本确认**：用户确认 Z 版本号加 1；当前版本由 v1.5.6 提升为 v1.5.7，VantaInstaller 继续使用独立版本 v0.3.12。
- **3.1 Git**：已执行 `git status --short --branch` 和 `git fetch origin`；`master` 与 `origin/master` 同步。当前未提交项包含本次配置/记录改动，以及用户已有的 `portable_config/script-opts/window_size_position.conf` 和 `.zcode/`；后两者不纳入发布提交。
- **3.2 Gate**：不触发。本次为 `portable_config` 普通配置/脚本选项变更，不改包结构、构建入口、核心运行时、安装方式、版权边界或发布流程。
- **3.3 文档**：已建立 v1.5.7 当前版本记录；README 安装顺序、包结构和下载方式无变化，不需修改。
- **3.4 功能**：Lua 语法、完整配置启动、HDR profile、输入配置、持久化往返、UTF-8 无 BOM/LF 和 `git diff --check` 已通过。
- **构建覆盖**：`build-01-base.ps1` 和 `build-04-config.ps1` 会递归带入本次 `portable_config` 改动；02/03 输入目录无 Git 改动，计划按 4.1.1 核验后逐字节复用 v1.5.6；VantaInstaller 源码无改动，沿用 v0.3.12 候选。
- **发布计划**：完成 01/04 构建、02/03 来源归档下载/核验/复用、私用全量包本地构建与门禁后，提交功能/版本记录，创建并推送 `v1.5.7` 标签，发布 GitHub 六项公开资产，再同步 ModelScope 六项资产；私包禁止上传。
- **风险与待办**：当前 `release/` 为空，02/03 v1.5.6 来源归档和规范命名的 VantaInstaller 需从现有本地候选/远端补齐；完成后补写全部 SHA-256、资产大小和远端核验结果。

## 2026-09-05 21:18

### v1.5.7 本地构建与发布前门禁

- 01、02 两卷、03、04 均已从本地输入重建并通过 `7z t`、内容边界、版本标记和分卷大小检查；公开候选共六项，installer 沿用 v0.3.12。
- 147 个 Lua 文件语法检查、完整配置实际启动 smoke test 和 VantaInstaller 启动探针通过；完整配置退出码为 0，测试源仅出现既有 `auto_profiles` 元数据缺失警告。
- 私用全量包仅保留一份完整产物 `release/mpv-full-private-v1.5.7.7z`，已含 installer，不上传任何公开发布渠道；`build/` 临时目录已清理。
- 本地 SHA-256 与大小已写入 `version/版本迭代记录.md`；待提交构建记录、推送 `v1.5.7` 标签、创建 GitHub Release、同步 ModelScope 并补写远端核验结果。

## 2026-09-05 22:11

### v1.5.7 GitHub 与 ModelScope 发布完成

- GitHub `v1.5.7` Release 已正式发布，状态为非草稿、非预发布，恰好包含 6 个公开资产；文件名、大小和 GitHub digest SHA-256 与本地逐项一致。
- ModelScope `AerithDream/mpv-vanta-edition/v1.5.7/` 六项公开资产上传成功；匿名直链全部 HTTP 200，`Content-Length` 与本地逐项一致。
- 私用全量包 `release/mpv-full-private-v1.5.7.7z` 仍只保留本地一份完整产物，含 installer，未上传 GitHub 或 ModelScope；公开 `release/` 目录保留 6 项发布文件和该私包。
- `v1.5.7` 标签及 `master` 已推送；最终收尾记录已整理，提交后再次确认构建暂存目录、工作区和远端同步状态。

## 2026-09-06 11:19

### Hills 外部播放器 Emby 起播失败排查

- **用户问题**：Hills Windows 外部 mpv 播放 Emby 网络视频时，取链/缓冲等待期间看起来约 2–3 秒就停止。
- **已确认现象**：`portable_config/files/mpv.log:1` 的 mpv 命令行媒体参数已经包含 `.../embyhttps://cdn...`；`0.247s` 启动的 yt-dlp 预解析在 `4.343s` 以 HTTP 403 失败，随后 mpv 在 `4.383s` 请求同一个坏地址，`6.982s` 收到 HTTP 403，并在 `6.983s` 记录 `loading failed (reason 4)`。
- **责任边界**：Hills 注入的 `hills_external_reporter.lua` 仅监听并输出播放事件，不改 URL。坏 URL 在 mpv 启动参数阶段已经存在，优先级高于 mpv 缓存和网络超时配置，具体来源仍需在 Hills 外部播放器与 Emby/线路返回值之间确认。
- **mpv 配置审计**：本地 `mpv.conf` 已启用 `cache=yes`、`demuxer-max-bytes=300MiB`、`cache-secs=15`、`demuxer-readahead-secs=15`；本机构建 `--list-options` 显示 `network-timeout` 默认 60 秒、`cache-pause-initial` 默认关闭。故当前 2–3 秒停止不是 mpv 默认网络超时。`ytdl_hook.conf` 的 `try_ytdl_first=yes` 与只匹配 URL 末尾 `.mkv` 的排除规则，会让带签名查询参数的 `.mkv?...` 先额外触发 yt-dlp 探测。
- **验证命令**：`git pull --ff-only`（Already up to date）；mpv `--version`/`--list-options`；LuaJIT 模式检查；读取 Hills 1.3.1.0 外部报告脚本；日志时间线和脱敏 URL 形状检查；坏地址与截取出的 CDN 地址的 curl 状态探测均未产生可用媒体响应。
- **本次文件变化**：仅追加本状态记录和 `version/工作进度.md`；未修改 `portable_config` 配置/脚本、Hills 文件或用户已有的 `portable_config/script-opts/window_size_position.conf`，未更新版本号、未打包/发布。
- **下一步**：优先升级 Hills Windows 客户端并复测命令行 URL 是否仍出现 `/embyhttps://`；若 URL 修复后仍有额外等待，再单独调整 ytdl 预解析排除规则。项目版本保持 v1.5.7。
- **Git**：开始排查前 `master...origin/master` 同步；工作区原有 `window_size_position.conf` 修改和 `.zcode/` 未跟踪目录继续保留，本次状态/进度记录改动尚未提交。

## 2026-09-06 12:54

### Hills 1.4.1.0 内置与外部 mpv 网络路径对比

- **版本与组件**：本机 Hills Appx 已为 `Mountains.HillsLite 1.4.1.0`；安装包内同时存在独立的 `data/player/HillsPlayer.exe` 和 `libmpv-2.dll`，不是调用项目根目录的外部 `mpv.exe`。
- **内置播放器证据**：HillsPlayer 的 mpv 日志记录其通过 `http://<Emby>/emby/videos/.../original.mkv` 会话地址播放，并设置 `Hills Windows/1.0.1` User-Agent；该次打开约 0.15 秒完成，随后成功读流并以 `success` 结束。
- **外部播放器证据**：最新 `portable_config/files/mpv.log` 的启动参数已直接收到 `https://cdnfhnfile.115cdn.net/.../*.mkv?...`，不再有 `.../embyhttps://`；yt-dlp 约 3.176 秒收到 HTTP 403，mpv 随后在约 3.395 秒记录 HTTP 403 和 `loading failed (reason 4)`。
- **签名验证**：对当前外部 URL 做不下载媒体的 Range 探测，直连、显式 HTTP/SOCKS 代理、浏览器 User-Agent、Referer 和 HTTP/1.1 均返回 AliyunOSS `invalid signature`；因此不是 mpv 的 2–3 秒缓存/超时，而是 Hills 外部流程传出的直链签名或取链时机不正确。显式代理也未改变结果。
- **结论与边界**：内置播放器由 Hills 自己取得新鲜 Emby 会话流，外部模式只接收 Hills 已经生成的单个 CDN URL，且 reporter Lua 仍仅上报事件。外部修复应让 Hills 刷新并传递有效签名 URL，或改传 Emby 会话地址/中转地址；仅调大 `network-timeout`、`cache-secs` 或关闭 yt-dlp 不能修复 403。
- **本次文件变化**：仅更新本状态记录和 `version/工作进度.md`；未修改 `portable_config`、Hills 文件、用户已有 `window_size_position.conf` 或版本/发布资产。未记录签名 URL、API key 或请求 ID。


## 2026-10-04 12:59 · 播放与画质现代化、本机回归及杳知徽标更新（未发布）

- **范围与授权**：按用户已批准方案实施；追加跟进杳知起播徽标。Windows 10/11 为目标，不再受 Win7 约束。本轮不打包、不发布、不修改《发布流程.md》，版本仍 v1.5.7。开始时 `git pull --ff-only` 已同步；未创建提交／推送。
- **初始工作区**：既有 STATUS、工作进度、startup_format_logos.conf、window_size_position.conf 和 .zcode/ 已单独保留；两份用户选项与初始备份逐字节相同。初始备份及旧核心／工具在忽略目录 `backup/modernization-20261004/`。
- **组件**：验证官方资产 digest 后替换 shinchiro 20261004 整套核心（mpv/FFmpeg/libplacebo），升级 yt-dlp 2026.08.19、TorrServer MatriX.145.1；uosc 5.13.0 和 umpv 1.5.1 保留。17 项现有上游逐源审计，366 Shader 一致，定制差异保留，合并 hdr-mode 的失败恢复与轮询修复。
- **VS 决策**：R80 的 Python 导入通过，隔离直接 mpv 测试在初始化退出 1，证据 `tmp/modernization/vs80-test.log`；维持 Python 3.14.6＋R73＋K7sfunc 1.3.1 现有整套，10012 个文件及 Python 包元数据锁定。K7sfunc 新版 1.8.1 不单独交付；插件／模型无可靠版本时以 SHA-256 标识。未知来源／专有授权须在以后公开打包前补证。未改系统 PATH。
- **弹幕退役**：移除活动目录、专属配置、菜单／按键／审计入口；共享依赖与历史开发备份保留。新安装器检测退役标记后隔离到根 backup，保留目录内下载数据，拒绝跟随链接；真实迁移源码测试通过。旧公开安装器和手动解压不能自行清理残留，文档写明操作步骤。
- **增强**：新增 quality.lua／quality/probe.py、状态与模型准备菜单。默认 AI、Shader 超分、去色带与轻量时间插值关闭；固定降噪→AI 超分→AI 补帧顺序，推荐同类互斥，原分辨率无预缩小，720p 性能方案显式标注。只清理三项自有标签及自有 Shader；取消／超时／切片使旧回调失效，准备完成仍需用户手动启用。HDR／广色域推荐增强暂时封锁，AMD 不开放 NVIDIA 专用后端。
- **统计**：独立 Windows 原生 CPU／PDH GPU 指标模块；关闭停止采样、异步不重叠、切片失效、布局缓存／动态限频。修正覆盖层字体坐标尺度并重新做完整三轮测试。兼容查询关闭／切片取消测试通过。
- **色彩**：默认 gpu-next、d3d11va-copy、BT.709/sRGB 目标，不强制 scRGB／HDR，不自动叠加创意调整。状态分别显示原始／推断源参数、滤镜输出、目标与亮度标尺、ICC、交换链未知。3FP 仅参考能力与标尺／回退思路；不复制渲染器，不采用 T0 排名，不把源位深、中间 FP16、交换链和面板统称 16bit。
- **杳知徽标**：官方 1.0.6-2 资产 SHA-256 已核验，manifest v23→v24，新增 24 张 DRA 素材并保留 MIT 署名。视频徽标不等待迟到音轨、几何就绪触发已差异合并；保留本地真实格式优先、四种黑边模式、用户双路／白色选项。格式识别与 DRA 预览、双字幕截图复核通过；DRA 音频实际解码仍需素材。
- **验证**：131 个活动 Lua、23 个 Python/VPY 语法通过，Shader 引用零缺失、无活动弹幕入口；Windows PowerShell 5 解析与更新器官方资产选择／自更新失败回滚通过（UTF-8 BOM 兼容中文脚本）；Vanta.Core 构建 0 警告／错误。真实完整配置 HEVC 8/10bit、广色域 SDR、带静态标记 HDR10、HLG，原色／传递函数断言通过。早期丢标签的 H.264 结果作废。HEVC 10bit 硬解、WASAPI 初始化、双字幕、HTTP 文件播放、AI 24→48fps、重复选择、快进、组合顺序、取消、切片、失败回退均通过。
- **性能实测**：固定 1280×720 24fps，旧／新 stats 关闭／首次打开／反复开关／持续显示各 3×6 秒，共 24 次，未新增掉帧／错时／延迟；新版外部查询全部 0，旧持续三轮 18/22/18。主进程 CPU 未测得下降，不计旧子进程 CPU；新版文字尺度变化包含在测试中，不宣称总体降耗。额外 720p60／1080p23.976 无掉帧，2160p30 短起播窗口累计 1 帧，记录而非隐藏。
- **交付**：`docs/modernization/实施报告.md`、`升级和回退.md`、上游／新旧核心／逐次统计／播放／尺寸 JSON、`portable_config/components.lock.json` 与 tools 下复核脚本。运行时二进制、候选资产、日志、截图和备份受 Git 忽略；仅同步 Git 不能复现整个本地环境。
- **待验证／下次交接**：NVIDIA、Intel、HDR 显示输出、Dolby Vision P5/P7/P8、真实高负载长时段与仪器色准未验收，表已交付。R80 需整套隔离解决便携 VSScript 后再升级。将来发布必须按发布流程 3.2 提交核心／运行时／包内容 Gate，由用户决定，不自动豁免。建议保留本轮 Git 提交后再切设备；当前有未提交改动。


## 2026-10-04 13:02 · 最终差异与菜单校验

- 推荐增强和色彩入口已去重；完整 Shader 用途库／专家库保留。再次通过 131 Lua／23 Python 语法、引用／退役入口、用户选项逐字节、徽标素材完整性、发布流程未改和 git diff --check。更新器 Windows PowerShell 5 直接 ParseFile 与失败回滚测试通过。
- 本轮文件均为 UTF-8／LF；用户两份既有选项保留原始字节。新增 UTF-8 BOM 仅用于兼容 Windows PowerShell 5 解析中文的维护更新器／测试脚本。没有测试会话或后台准备进程遗留。
- 未创建提交／推送／新发布；当前仍保留用户既有修改及本轮未提交实现，切设备前建议先提交并另存忽略的运行时和备份。


## 2026-10-04 13:20 · 菜单架构规划（建议稿，未实施）

- 应用户请求审阅 input.conf 和 quality 动态菜单。问题为画面处理／窗口／导航入口分散、完整 Shader 双索引与旧配置组重复、重置范围和子页面标题不明确。
- 建议一级收敛为打开、播放、画面、音频、字幕、界面、工具；着色器提升为画面 → 着色器；保留完整算法库、常用组合和快捷键，移除第二套完整 Shader 重复展开。
- 规划、功能迁移表、关闭范围、状态规则及三阶段实施写入 docs/modernization/菜单架构规划.md。仅形成建议，未改 input.conf、脚本或快捷键，不视为用户已批准该架构。
- 现有现代化工作区保持未提交，不打包／发布；下一步依用户反馈定稿菜单再实施。


## 2026-10-04 13:32 · 菜单规划补充可选组件边界

- 用户指出着色器与 nv／滤镜组件在分发中可独立安装。规划改为画面下着色器、VS／AI 滤镜、内置处理分区；NVIDIA 后端额外检查显卡支持。
- 补充缺组件简洁灰色入口、逐方案依赖检查、实际准备结果、启用前复查、重新检测与非全量安装验收矩阵。不假设包标记等于组件齐全；不改变现有包编号／发布流程。
- 仅更新 docs/modernization/菜单架构规划.md 与记录，未改真实菜单／快捷键；旧高级入口能力检查仍是待实施要求。


## 2026-10-04 13:54 — 菜单架构实施（Asia/Shanghai）

- 用户已确认按前述规划更新实际菜单；使用 HandShake，阅读 AGENTS.md、STATUS 与规划；INDEX 不存在。git pull --ff-only 提示 Already up to date，master 与 origin/master 同步。
- input.conf 收敛为打开／播放／画面／音频／字幕／界面／工具；底部最小化／退出保留。原快捷键集合与原 Shader 组合效果保留；常用 Shader 快捷键接入同一动作目录；全部 VF 清空同步管理状态。
- quality.lua＋quality_shaders.lua＋quality/shaders.json：Shader 与 VS／AI 分区，387 个既有 GLSL 引用、34 类算法、完整预设链保留；缺文件置灰／启用复核，手动 Shader 与推荐超分／补帧互斥；来源查看／逐项移除／全部清空。Shader 不加载 VS，VS 首次打开才核查组件；NVIDIA 专用方案检查显卡。关闭菜单后异步结果不会重新打开旧页面。
- 模型／推理 DLL 最终能力仍在后台准备验证，VS 整套校验未放宽。不得将菜单「点击准备」等同于已完成推理；未改变手动高级项跨文件策略。
- 验证通过：tools/check-modernization.py（132 Lua、24 Python、用户既有选项字节保留、发布流程未改）；test-menu-architecture.py（真实全配置／基础／Shader 菜单树、快捷键集合与引用）；test-shader-menu.lua（缺包／缺文件／完整组合／启用复核／互斥／状态管理）；test-quality-state.lua（四种组件组合、异步故障、NVIDIA 拦截、清空状态同步）；test-quality.py（AMD DirectML 实际准备／启用／重复选择／快进／CCD→超分→补帧／切片清理）；git diff --check。真实截图 tmp/modernization/menu-shaders.png 与 menu-vs.png 已视觉检查。
- 变更说明见 docs/modernization/菜单架构规划.md 和 README。回退备份 backup/menu-architecture-20261004/input.conf 与 scripts/quality.lua 是本次改动前的版本，不覆盖此前现代化；临时测试配置与素材位于 tmp/modernization/。
- Git 工作区保留此前未提交改动及 .zcode/；本轮未提交、未推送、未打包、未发布，未修改发布流程与版本号。完成逻辑检查后建议分批 git add／git commit 保留里程碑；NVIDIA／Intel 实机仍待外部验证。


## 2026-10-04 15:22 — 回退菜单架构实施（Asia/Shanghai）

- 用户明确要求回退，仅撤销最近一次菜单架构改动。input.conf 与 quality.lua 从 backup/menu-architecture-20261004/ 恢复并逐字节核对。
- 新增 quality_shaders.lua、quality/shaders.json、两项菜单测试移入 backup/menu-architecture-20261004/reverted-152218/；此前 test-quality-state.lua 恢复原故障注入测试；README 恢复原菜单说明。规划文件标记为已回退，历史记录保留。
- 此前现代化组件、VS 锁定、统计、色彩、弹幕移除、徽标与用户既有设置保持原状。停止本轮架构实施，后续调整范围需依用户具体指示。
- 未提交、未推送、未打包、未发布；master 与 origin/master 同步，工作区仍有此前未提交改动。
- 回退验证通过：原配置／脚本与菜单前备份逐字节一致；原增强故障注入、131 Lua／23 Python 语法、Shader 引用、用户选项保留及 git diff --check 全部通过。


## 2026-10-04 16:13 — 用户要求暂停实施，调查两类菜单（Asia/Shanghai）

- 用户最终改用「着色器／视频滤镜」两个一级分类，窗口设置明确留在画面；此前「NV 独立包」是用户记忆误差。当前打包清单 Extras 同时包含 Shader／VS／Python，未发现独立 NV 包。
- 暂停前 input.conf 已局部迁移、合并重复 Shader 用途索引、保留快捷键，增加视频滤镜分区；quality.lua 已按 Shader／VS 菜单过滤、增加原预设依赖检查、允许保留手动 Shader 组合。Lua 故障注入与 check-modernization.py 在最后一组菜单入口新增之前通过；后续尚未做完整菜单／组合实机回归，不能宣称完成或稳定交付。
- 用户随后明确「先等等，调查和规划」，已停止配置／脚本变更。本轮仅只读调查与文档记录。此前现代化与既有用户设置保留；局部调整前基线在 backup/menu-local-adjust-20261004/，不自行回退或继续实施。
- 调查官方 mpv 手册、PlayKit GLSL／K7sfunc／FAQ 与 input_uosc 示例，建议一级分处理体系、二级按用途、三级具体方案，完整库保留额外算法目录；单项组合和完整预设必须区分。Shader 阶段在 vf 后且 HOOK 有固定约束，deband／interpolation 不应冒充 GLSL 或 VS。
- 最新规划附在 docs/modernization/菜单架构规划.md；替代早先七类一级架构建议。等待用户明确后续实施范围。未提交、未推送、未打包、未发布；工作区仍含此前未提交改动。
- 本轮 git diff --check 发现中间配置 input.conf 末尾多余空行；因用户要求停止实施，没有继续修改配置，后续验收时处理。

## 2026-10-04 16:46 — 局部菜单与公开精选方案完成

用户授权采用公开优质方案并以桌面 RTX 3050／4060／5060 Ti 作为低／中／高负载参考，允许合理时执行。保留熟悉一级入口，着色器／视频滤镜分开；窗口设置在画面，统计／截图归工具、速度／循环归导航。没有恢复此前已回退的七入口全面重构。

- 精选 Shader：低档 FSRCNNX 8＋Anime4K Fast A/B/C；中档 ArtCNN C4F16＋Anime4K HQ A/B/C；高档 ArtCNN C4F32＋HQ A+A/B+B/C+A（至少 2×）。每项是独立选择，不把同档方案自动叠加。依据 Anime4K 官方完整组合与 ArtCNN 作者说明；性能档位是规划参考，非上游实测型号映射。
- 常用单项按用途分组，完整算法库及原方案保留；相对于局部调整前备份，387 个 Shader 文件引用全部保留，绑定键无增删。整套 Shader 预设只替换本类链，VS 状态独立；分别清空含本类手动项。快速 Shader 与 VS 超分状态也独立保存，回归覆盖互不移除。
- 缺 Shader 阻止执行；VS 根据组件／后端／GPU／准备结果判断能力；渲染器轻量插值与 deband 不混入 VS 分类页。精选入口仍阻止未经验证的 HDR／广色域处理。
- 验证通过：131 Lua／24 Python 语法及现代化检查；test-quality-state.lua 故障与跨类状态回归；validate-quality-menu.py 真实 IPC 菜单、五种精选预设、十二组 Anime4K、2× 门禁、双类独立清空、缺文件、切片和广色域门禁。真实 VS 超分菜单截图检查后端提示及禁用状态。git diff --check 通过。报告在 tmp/modernization/validation/quality-menu-results.json。
- RX 6600 上 ArtCNN C4F32 首次切换观察到约 160 秒编译等待，入口已提示首次编译可能较慢。该观察不是持续播放耗时；320×180 功能回归不能代替 1080p／4K 性能、色准或 NVIDIA 代表型号验收，后者保留外部实机待测。
- README 与菜单架构规划同步；备份仍为 backup/menu-local-adjust-20261004/。保留所有本轮先前工作区修改和用户定制。没有提交、推送、打包、发布或修改《发布流程.md》。

## 2026-10-04 17:04 — 仅恢复着色器与视频滤镜原方案

用户反馈两类菜单更混乱，明确要求恢复原方案、其他整理保留。以当前已发布 HEAD 的原始两类菜单路径为基准，恢复着色器的推荐、用途分类、专家库与视频滤镜的补帧、超分、降噪、片源修复等；逐项比对 797 个着色器路径与 33 个视频滤镜路径完全一致。新增 3050／4060／5060 Ti 性能档位撤下，三个 Preset-* 配置移除，旧常规配置组回到其它。

窗口设置仍在画面；工具中的统计、截图／导出及导航中的速度循环、书签保留。快捷键恢复原着色器方案（Ctrl+0 清空 Shader、Ctrl+1/2/3 为原推荐预设），工具中的系统恢复／状态菜单保留但解除冲突绑定。没有整体回退 input.conf，也没有回退核心、弹幕移除、组件锁定、统计与徽标等先前工作。

底层保留缺文件检查、Shader／VS 独立状态和后台准备机制，VS 静态菜单首次选择可自行触发组件核查；未开放的 DRBA／SVP／NV ArtCNN 旧位置保持禁用，不恢复直接加载失败滤镜。README、菜单说明与验证工具同步。操作前备份：backup/menu-two-restore-20261004-170037/。

验证通过：Lua 131／Python 24 语法和现代化检查；test-quality-state.lua 包含静态 VS 首次核查与两类状态独立测试；实际 mpv IPC 验证原目录生成、旧推荐方案、十二组 Anime4K、分别清空、缺文件、切片及广色域门禁；原两类路径完全恢复，其他整理入口仍存在；git diff --check 通过。工作区仍有先前现代化及用户修改，未提交／推送／打包／发布，《发布流程.md》未修改。

## 2026-10-04 17:08 — 五组基础画面操作归入画面

按用户明确要求，将视频滤镜中的「片源修复、画面变换、修复错误标记、帧率改写、色彩调整」五组共 13 项移至画面，画面变换与现有去黑边入口合并同组。仅修改菜单路径和分组位置，命令、快捷键与状态表达式逐字保留；着色器及其他菜单不变。操作前 input.conf 备份：backup/menu-picture-groups-20261004-170835/input.conf。静态核查五组不再位于视频滤镜，十三项命令／绑定不变。未提交、打包或发布。

## 2026-10-04 17:17 — 三种菜单同步核查

确认右键 uosc 从 input.conf 解析，Shift+右键 OSD 与中键原生菜单共用 dyn_menu 从同一 input.conf 生成的 menu-data。实际 mpv IPC 核查五组均在画面，视频滤镜无残留；uosc 主菜单成功打开。未修改活动配置。已运行播放器需重启，避免继续使用启动时缓存的旧菜单。

## 2026-10-04 18:51 — 3FP 发行版与 HDR 色彩管线核查

静态拆解用户提供的 FFF.Player.exe（2026.9.30+15995b807bf8a27037d2697fcdb89d13064ee247；SHA256 4AEFD9FFFC007D17858A4C85E9EFEEC639A6FF10E97627928CA28D843CB17C1B）。使用临时 ILSpy 与系统 D3DDisassemble，七组内置 Shader 与固定提交预编译数组逐字节一致；区分常规浮点计算、FP16 存储与最终输出。标准托管入口未设置 SDRscRGB模式，保持零，不能概括为任意 10bit SDR 自动进入 FP16。

HDR 为核心核查对象。基础 PQ→scRGB 有绝对亮度、负通道与 nits/80 标尺；基础 HLG 按 RGB 独立幂变换，与 BT.2100 加权 OOTF 不同，数学复算显示灰阶一致而彩色通道比例不同，不冒充 GPU 回读或最终面板色差。指定 EXE 同目录及拆包清单无 FFF.DolbyVision.Test.dll，外部授权扩展与基础层回退需分别验收；没有分析或绕过授权。

本机 mpv 五类素材各比较默认与 FP16，共十个独立会话；匹配 linear 后五类 GPU 错误为零，实际 FP16 scRGB 链确认。目标仍 SDR，不能宣称 HDR 实机色准通过。首轮 auto 初始化色彩空间不匹配及后续恢复保留证据。报告：docs/modernization/3FP与mpv色彩精度核查.md，含二进制证据、HLG 公式对照、实验配置及 HDR 优先验收表。研究工具与原始证据仅位于忽略目录 tmp/modernization/3fp-audit/，未纳入分发。

公开 T0／第二档／不如 Windows 播放器的排名缺同机测量依据。HDR 显示器、NVIDIA／Intel、真实 DV 素材及仪器色差测量仍待外部验收。本轮未启动 3FP GUI、未修改活动配置、菜单或 Windows HDR；未提交、打包、发布或修改发布流程。

## 2026-10-04 19:12 — 完善 mpv 色彩准确优化路线

用户要求完善色彩优化路线。本轮审计 mpv.conf、profiles.conf、hdr-mode.lua／hdr_mode.conf、quality_status.lua 与色彩菜单，结合发行版核查及官方文档，新增 docs/modernization/mpv色彩准确优化路线.md，并与 3FP 核查报告互链。

明确 P0 准确基线、P1 HDR 协商与统一状态管理、P2 诊断及数学／GPU 回读、P3 HDR 面板／多 GPU／动态格式验收。发现全局 HDR2SDR 启用 hdr-contrast-recovery=0.30；旧 HDR 脚本读取 target_contrast 属性有误、按亮度阈值判断 HDR 且恢复 SDR 写死 203。这些列为优先待修项；脚本当前 hdr_mode=noth，未启用。区分参考 ICC 与本机校准、FP16 请求与实际输出、源信息补齐与已知目标能力、HDR 格式识别与动态元数据执行。

保留现有菜单，色彩目标在画面；SDR 默认保留，HDR 优先验证 FP16 scRGB，并规划 PQ 兼容与明确 SDR 回退。每类亮度标尺、显示信息来源、跨屏失效、异步回调、运行时不可写选项／VO 重建、映射责任、功能／GPU／仪器三层验收与回退条件均写入路线。

本轮仅文档规划和记录，未改变活动配置、菜单、Windows HDR 或发布流程，未运行新增播放验收、未提交／发布。既有工作区修改保留；活动修复与 HDR 实机测量尚未实施，不能宣称已经优化完成。

## 2026-10-04 19:32 — 8K AV1 HDR60 实素材掉帧排查

用户提供 Downloads 中 LG OLED The Wild 8K HDR60 视频，实际 7680×4320／59.94fps／10bit AV1／BT.2020 PQ。mpv 当前配置及最小／fast、复制／直接／零复制硬解、关闭 VSync、Vulkan、禁脚本与纯解码对照共 13 个独立 mpv 会话。全部关闭；源文件与活动配置不变。

当前 8k-fix 成功选择 d3d11va，Shader／vf 为空，插值／去色带关闭。最小与轻量路线仍丢帧，copy 更慢；Vulkan 与 vo=null 硬解请求回退软件，不能算有效硬解对照。PDH 单次播放器 Video Codec 引擎约 99.6%，低 CPU；预热后的两次禁脚本播放仍明显掉帧。独立 gyan FFmpeg 2026-08-09 工具纯硬解 GPU 帧输出 null，起始快进预解码等待单独剔除，末段约 45.3fps，低于59.94fps；不是所有显卡／驱动／8K素材的普遍硬件上限证明。

新增 docs/modernization/8K-AV1掉帧排查.md，列出实际时长、推进与掉帧差分、渲染 pass、方法限制和处理建议，与色彩路线互链。原始数据／日志位于 tmp/modernization/，不分发个人路径及历史信息。优先建议 4K HDR60 或离线单独转换；未转码、未改驱动／Windows HDR／默认渲染精度，未提交／打包／发布。

## 2026-10-04 19:45 — VS Renderer-Player 1.0.4 同步与观感调查

只读核查用户提供便携包文档和 player.ini：3FP 核心／解码、预解码开启，文档说明原画直通与 VS 增强不同，增强路径有最新目标帧调度／自动降载；不能直接套用到本次原画 8K。包使用修改的 API14 3FP，源码基点获取失败，未把其他版本阈值冒充其实际实现。未启动 VS GUI 或修改其 INI，实际 GUI 呈现帧率／节奏尚未测量。

随包 FFmpeg 对同一片源纯硬解末段约45.2fps，前轮工具约45.3fps；没有证据证明 CLI 解码器突破60fps。独立 mpv framedrop=no 为零掉帧但墙钟10.10秒推进7.56秒，内部 avsync3.59秒，测试ao=null不能当听感测量。发现8k-fix强制audio覆盖启动display-resample；作废首轮显示同步对照，加载后IPC重设再验证，实际display-resample、165Hz，10.89秒推进8.84秒、VO丢帧增502，吞吐问题仍在。

新增 docs/modernization/VS播放器同步策略对照.md，与8K报告互链；原始数据tmp/modernization/vs-player-audit/。解释均匀低帧率、缓冲、降载与完整60fps的区别，不断言VS观感必然来自不同步。后续拆开8K硬解选择与同步策略，实测GUI唯一帧呈现／时钟／间隔分布。活动配置及视频未改，全部测试播放器关闭，未提交／打包／发布，先前工作区修改保留。


## 2026-10-04 21:14 — 色彩准确路线软件实施与本机验证

- 用户授权「推进并完成色彩准确优化路线」，继续实施而非只读规划；保留原着色器／视频滤镜及画面分类，没有重新设计一级菜单。既有未提交改动不回退。
- 新增 color-target.lua／color-target.conf；菜单三种实现共享 input.conf 的五个色彩入口。SDR／可信系统 ICC、受能力门禁的 scRGB→PQ→SDR、有界协商、重复点击幂等、切片旧结果失效、跨屏重检、只恢复本系统拥有的值。HDR 状态仍标实机色准待测；不可定位流拒绝需要重建的 HDR 路线。
- profiles.conf 的 HDR2SDR 对比度恢复 0.30→0，观感值留作 HDR-Contrast-Optional；8k-fix 保留 auto-safe，删除强制 video-sync=audio。旧 hdr-mode 默认不启用观察器，手动启用时按 PQ／HLG／DV 检测并委托新管理器，暂停有界等待、切片取消、只恢复自行改变前的系统 HDR。状态页分源／有效输入／滤镜输出／实际渲染目标与系统报告，不能确认的交换链／动态 HDR 执行标未知。
- 调试发现直接逐项改 D3D11 选项会多次重建 VO，产生格式错配及 HEVC 参考帧错误；apply-profile 单次也不能避免参考帧丢失。已用暂停状态＋暂撤原视频轨＋目标写入＋恢复视频轨的事务修复，最终模拟能力协商日志无 GPU／解码错误。早期 .4 秒回退检查不稳定，改为有界状态等待，后续回归通过。真实 HDR 硬解与远程重建仍待覆盖。
- 验证通过：132 Lua／28 Python；test-color-state（含未知／不可定位门禁、重复点击、写入失败、两级超时、旧回调、所有权、状态提示保持、视频轨／暂停恢复）；test-hdr-lifecycle；五类编码素材 validate-color-target（原生菜单新入口、SDR／ICC／恢复、源标记保持、实际 SDR 门禁、模拟能力实际 F16 scRGB 与回退，日志无错误）；RGB16 GPU PNG 1024 灰阶保留、最大采样码误差 0；10bit full／limited 端点；PQ／HLG／负值／FP16 数学参考。现有增强菜单、普通 HEVC10 硬解／音频／双字幕／HTTP 文件回归通过；git diff --check 无空白错误，只有已有 autocrlf 提示。
- 夹具初版 FFmpeg 的隐式范围转换曾污染端点，已固定输入／输出标记并验证无损解码 Y 为 0、64、940、1023。范围结果 limited=0/0/65534/65535，full=50/4150/60268/65535；这是 GPU 截图结果，不是显示仪器或线性纹理回读。
- 交付 docs/modernization/色彩优化实施与验证.md、color-validation-results.json、color-upgrade-manifest.json，更新路线／3FP核查／实施报告／同步报告／升级回退与 README；components.lock 新增色彩本地策略及许可。快照 backup/color-accuracy-20261004-203559/，五个原文件可单独恢复，移出新增管理器／选项，组件锁只撤 color_management，不全仓库 reset。
- 完成范围：P0／P1 软件和本机功能完成；P2 按需诊断、数学／GPU 截图及范围工具完成，未取得原生线性纹理回读；P3 HDR 面板／仪器／NVIDIA／Intel／完整 DV、动态 HDR 仍待外部验收。未进行 3FP／Windows 播放器 HDR 同机色准排名；不把 SDR 或模拟能力结果认定为 HDR 色准通过。
- Git：本轮开始 git pull --ff-only Already up to date，master／origin/master 仍为 7e302f8（v1.5.7）；工作区含本轮及既有修改，未提交。无打包／发布、无《发布流程.md》修改。需要保存既有差异后再按逻辑提交；版本不升，不更新版本迭代记录。
- 下一步：按报告外部表取得 HDR 显示器和测量条件，先完成原生线性回读与 HDR10／HLG 亮度／色块，再测多 GPU／真实拒绝／远程硬解重建与完整动态格式；VS GUI 帧节奏仍待实测。发布必须另走发布流程及 Gate。


## 2026-10-04 21:23 — 简化 ICC 用户提示

- 按用户要求移除色彩选择后的 Windows ACM 核查／可信性长提示；ICC 仅显示「色彩目标：系统 ICC」，状态页不再要求用户确认可信，菜单简化为「SDR · 系统 ICC」。技术核查依据留在维护文档，色彩设置与能力门禁不变。
- 同步原有故障回归的 ICC 预期及配置校验值。工作区原有未提交修改保留，未提交／打包／发布。
- 验证：色彩状态故障回归 PASS；git diff --check PASS。


## 2026-10-04 21:44 — 暂停 VS 对比，清理归档与项目架构整理

- 用户确认顺滑表现来自作者内部测试版本，并非已下载的 VS Renderer-Player，取消当前性能测试；没有启动 VS GUI、没有新 GUI／性能采样。此前尝试 Computer Use 发现原生接口不可用，用户明确禁止后没有再使用；后续不借 GUI 数据推断内部版。对照报告追加暂停及版本边界。
- 本轮先读 AGENTS／STATUS／Git 与当前目录，git pull --ff-only 返回 Already up to date。既有现代化、用户窗口／徽标和 .zcode 差异保留，没有 reset／提交／发布。
- 检查引用与现有构建源确认 mpv/fonts.conf 与 shinchiro 原始包逐字节相同，是字体支持目录，不能清理；便携 Python／VS 和其锁定运行库、四种诊断 BAT 原编码、关联脚本、开发备份及 v1.5.7 release 保留。
- 使用 PowerShell LiteralPath 原生搬移，先验证所有源在工作区、目标在指定 backup／trash 归档内、无覆盖目标和根级目录链接。185 项归档：tmp 原先 131 文件＋50历史目录；误生成空 $gateDir、_nul 和个人 dxdiag 诊断；过时 installer/configure-opengl-hq.bat。没有永久删除。普通文件逐个搬移前后 SHA-256 相同；目录整体移动，未递归计算内容哈希。
- 用户级归档 backup/project-cleanup-20261004-213930/，含 archive-manifest.json；过时 BAT 到 trash/project-cleanup-20261004-213930/installer/。原报告中的旧 tmp 路径按清单映射到新位置。tmp 根仅保留 modernization，本轮研究／夹具／原始证据仍可用；不公开个人日志／诊断数据。
- 新增 docs/项目架构.md、tools/README.md，更新 README／AGENTS 目录职责与当前支持，强调根运行库保持加载路径，活动配置只有 portable_config，开发／用户备份分开，tools 与 docs 和 doc 各有职责。本轮没有挪动构建入口或修改《发布流程.md》。
- 验证 PASS：185 项源／目标存在性和文件校验、字体与 shinchiro 包一致、文档链接；check-modernization：132 Lua、28 Python、Shader／退役入口、统计／用户选项／徽标／发布流程；普通 HEVC10 硬解、静音音频设备、双字幕、DRA 预览、HTTP 文件；git diff --check 无空白错误。测试进程正常结束。
- Git 仍 master／origin/master 7e302f8（v1.5.7），工作区不干净，含此前未提交修改及本轮文档／旧 BAT 删除。未打包／发布，版本未变。后续发布须复核退役入口与前轮组件 Gate；性能对照恢复前需取得对应内部版本、明确用户授权继续测试。HDR／多 GPU 等原未测验收仍待设备。


## 2026-10-05 00:34 — ChouKaguya 8K AV1 软解回退修复

- 用户询问 Downloads/ChouKaguya432048-Part.mkv 为何回退。读取实际 mpv 解码信息：AV1 Main、7680×4320、47.952fps、YUV42010、limited、BT.709／BT.1886 SDR，容器 111.874 秒；不是 HDR。源文件未改。
- 首帧最小 d3d11va／copy 均成功，完整配置却在首帧后 8k-fix 改 hwdec 后出现 Invalid repeated frame header OBU／Failed to read packet，硬解失败后转软解。禁脚本短测和初始 auto-safe 不回退，体现时序竞态，不能把短首帧通过当完整功能通过。
- 首次尝试 current-tracks/video/demux-w 条件仍迟到，真实回归失败；on_preloaded 实测 current-tracks 空而 track-list 尺寸已知。最终新增 hwdec-select.lua（MIT），on_preloaded 按可确定轨道尺寸写 file-local-options/hwdec。保留主配置 copy；显式 no／其他后端、非 D3D11、普通视频、未知尺寸、多轨 auto 不覆盖。旧 8k-fix 保留手动配置组，移除自动条件。
- PASS：真实完整配置三次启动、30 秒精确快进、普通文件回到 d3d11va-copy、切回保持 d3d11va，日志无硬解错误／软件回退，选择发生在尝试硬解前；模拟作用域与用户后端保护；check-modernization 133 Lua／29 Python 与引用、用户选项、徽标、发布流程检查。
- 备份 backup/hwdec-startup-20261005-002656/profiles.conf。报告 docs/modernization/8K-AV1硬解回退修复.md 和 hwdec-upgrade-manifest.json；更新工具／架构／回退文档与 components.lock 本地时序策略、当前色彩清单哈希。根运行库／色彩／同步默认未改。
- 初始 ffprobe 在本机 ffmpeg 目录及旧 VS 路径不存在，未下载替代工具；改用 mpv 实际帧信息确认位深色彩。独立 FFmpeg 探测显示 pixel format 未指定，未据此误判不支持。没有使用 Computer Use，也没有恢复 VS 性能对照。
- git pull --ff-only Already up to date；master／origin/master 7e302f8，保留既有未提交改动，未提交／打包／发布。原始日志可能含目录播放列表，不公开。此修复只保证本机当前初始化回归，不宣称任意 8K 实时吞吐或全显卡支持。


## 2026-10-05 10:21 — VS 1.0.5 正式包与 mpv 性能研究

- 用户重新授权以正式包和 ChouKaguya 8K AV1 片段继续对照；未使用 Computer Use。隔离解压 tmp/modernization/vs105，未覆盖已安装播放器或正式 INI、未修改视频或播放／显示默认设置。读取 AGENTS、STATUS 与既有调查；本轮开始 git pull --ff-only Already up to date，master／origin/master 7e302f8。
- 原包 SHA256 f2c80dd377e667b5cc64d3a1801219d0d15ec5a5fbbef4bd4f4a93b74a7e7c9d；实际 FFF.Native.dll 094c19e0658235dafa0c5b5d46e59c211c9390632c71794aad45e4dcfe95de50／API16，区别包内后续文档 FF49CFC 构建。取得官方 GitHub 420dd3ee 源码的 perf-3fp／ThreeFpApi ABI 和 MIT 许可，只使用该实际 DLL。
- 新增 benchmark-playback-compare.py、benchmark-vs105-native.py、benchmark-vs105-abi.py，创建自有可见 HWND，真实音频时钟／DXGI Present，以 IPC／C ABI／PID 级 PDH 测试，未操作 VS GUI。基础客户区 1280×720；完整 mpv 保留窗口脚本约1238×696。每组3次、15秒位置起约20秒墙钟，共39次，全部探针已退出。
- 实测：完整 mpv 硬解基本实时，复测新增掉帧0/0/7（探索6/0/0）；基础硬解0/0/0；准确sRGB补测1280×720、三次0/0/0、进度约1.000、GPU passes约6.61ms。所有硬解样本 d3d11va，解码掉帧增量0，无软解回退。3FP默认Jinc净接受25.26fps、双线性25.73、D3D11原生30.65；请求tearing+pacing后Jinc26.65，未恢复实时。强制软解mpv约0.598倍／12.30核，3FP约0.612倍／12.50核、净接受14.71fps。
- 3FP Present等待约28–38ms，解码计数接近源fps而接受帧显著少；不能仅归因Jinc或同步选项，也不能凭计数定位驱动／DWM具体机制。样片为SDR；交换链10bit不等于物理显示8bit或处理中间FP16，不作HDR／色准排名。GUI Qt、字幕、自动VS增强／降级及物理扫描未测，不能宣称完整 vs-player.exe 全面不如mpv。
- 证据：docs/modernization/VS-1.0.5与mpv播放性能对照.md；原始JSON分别在tmp/modernization/vs105-results、vs105-controlled、vs105-color-matched，汇总vs105-comparison-summary.json。PDH未采集的早期轮次没有补造GPU数据。软解IPC高负载实际14–15点，用真实墙钟差；初次按每组21点的审计断言失败，核对为采样延迟后改按有效时间／模式／尺寸验证，39次元数据与解码掉帧不变量通过。
- PASS：check-modernization 133 Lua／32 Python、Shader／弹幕活动入口、统计、用户既有选项逐字节、徽标、发布流程；新工具 py_compile、git diff --check。tmp包与结果受gitignore保护。仅新增维护工具／专项报告并更新tools README和记录，保留原未提交变更，未提交／打包／发布，版本不变，《发布流程.md》不变。下次如继续GUI／PresentMon／长时／HDR对照，应先明确口径和可用非CU统计接口；不替换此包为内部版本。


## 2026-10-05 10:28 — 对齐作者性能验收条件

- 再次对齐作者两套记录：4070 Jinc为1080p／4K→8K，780M 8K→4K的零掉帧使用204f2a37候选DLL（纹理slice直用、保留队列、三缓冲／有效两帧排队），并非本包094c19e DLL；候选明确不自动发布。780M为4K60Hz／算法519／120秒起60秒窗口，本轮1080p165Hz／原生算法7／片段10秒起20秒窗口。不同哈希不能独自证明缺某补丁，需构建核对。更新专项报告，收窄同步开关结论，不断言作者错误或3FP固有性能落后；作者同条件mpv也零新增掉帧。无新增播放试验或配置改动。


## 2026-10-05 10:33 — 正式DLL继承关系与8K测试澄清

- 用户指出正式DLL可能为昨晚候选的后续迭代，重新核查支持此可能：PE UTC 2026-10-04 17:09:46（本地10/5 01:09:46）、PDB build/bd-native-source，二进制含性能补丁的GPU_PROFILE／PRESENT_PROFILE和UTF16 VSR_3FP_PROFILE。不能按不同哈希／候选未自动发布推断未继承修复。确认用户所指780M确实测8K辉夜姬原片；4070较低分辨率→8K为另一组测试，不应混用作解释。
- 新增一次算法519、VSR_3FP_PROFILE=1的路径诊断，无CU。20秒净接受29.80fps、0.917倍、287掉帧、VideoProcessor模式1；包含预热日志平均GPU上传0.000635ms、合成30.94ms、Present CPU30.73ms。说明已有诊断／上传优化相关实现，未证明全部补丁和精确提交继承；合成含调度等待，开启诊断数据不替换原39次三轮成绩。结果tmp/modernization/vs105-lineage/native-519-profile.json/.log。更新报告澄清版本解释和片源，未改配置／工具，测试进程已正常退出。


## 2026-10-05 10:52 — VS1.0.5丢帧阶段诊断

- 用户要求定位VS1.0.5具体丢帧环节并解释780M／RX6600差异。新增QPC稳定段边界、输出尺寸／质量参数和显式headless控制；新增analyze-vs105-stages.py统计区间均值／P95／PTS跳跃／计数闭合，更新tools README及专项报告。
- 新增4次诊断：519的720p／1080p、513的720p、无渲染呈现硬解控制。稳定段解码／接受／丢弃分别873／604／270（队列-1）、896／603／293、918／516／402、964／964／0；全部计数闭合、合并增量0。720p提交PTS缺失270与掉帧一致。公开PlayerSession迟到判断在渲染提交前，容差max(2帧,50ms)，结合VS补丁与实测支持后解码迟到丢弃；精确DLL源码映射未取得，不宣称源码行断点追踪。
- 稳定段：519 720p GPU上传0.00052ms／合成37.13ms／Present CPU等待28.25ms P95 73.38ms；1080p仍约30fps。513 GPU合成9.66ms但Present37.48ms P95 96.91ms，约25.66fps。GPU区间含共享上下文依赖，不能当纯shader耗时或与CPU等待相加。可见组音频欠载31–43，headless 0。
- 同DLL headless硬解控制47.955fps、1.00005倍、0掉帧／0欠载／0DXGI Present；这不是可见播放成绩，与已有mpv实时结果一起定位渲染／呈现背压，反驳简单硬件解不了8K48解释。具体VP／解码共享队列／驱动／DWM等待仍需ETW或匹配源码计时，不把问题全部归给某个API。
- RX6600驱动32.0.21045.5002，780M作者32.0.21030.2001；AMD官方资料区分媒体能力与3D规模，RDNA2／RDNA3不能直接推出视频性能胜负。活动主显示为RX6600的ASUS，GameViewer虚拟输出均未连接桌面；没有因此乱归因虚拟适配器。
- 原始与分析：tmp/modernization/vs105-drop-stage/*.json/.log/*-stages.json；4组元数据／计数断言通过，新工具py_compile，check-modernization 133Lua／33Python等通过。测试进程正常退出，无CU／驱动变更／刷新率变更／配置改动。工作区仍master未提交且保留既有修改，未打包发布。


## 2026-10-05 11:29 — VS／mpv ETW呈现探针

新增独立PresentMon ETW采集、QPC稳定段分析和mpv呈现对照工具，完成5次采集。VS原生两次Present间隔约32.6ms，mpv准确SDR基础配置约20.85ms；已提交帧几乎均有显示事件。VS实际切换到Independent Flip、SyncInterval=0、允许tearing后仍约30fps，说明普通DWM合成不是充分解释；主要损失仍是提交前迟到丢弃。所有组未发现HybridPresent。

mpv稳定段保持D3D11硬解、准确sRGB、1280×720，输出／解码新增丢帧均为0；启动预热前已有58个输出丢帧，未宣称全程零掉帧。VideoBusy字段双方均为0且不可信，不能据此拆出解码耗时或把进程GPU忙区间当纯Shader成本。完整VS界面、实际光学输出与780M同条件复现仍未验收；下一层需帧ID／纹理slice／VideoProcessorBlt／GPU栅栏／Present／帧延迟等待关联探针。

官方PresentMon v2.6.0校验值、原始CSV、JSON、会话及命令证据在tmp/modernization/vs105-probes/；未安装服务，未提升权限，仅读取目标PID且只停止自己的随机ETW会话。首次自动退出等待超时但CSV有效，已修复主动结束自己会话；其余4次返回码均0，无遗留会话。check-modernization通过133 Lua／36 Python及引用／用户选项检查，git diff --check通过。报告和tools/README已更新。默认配置、驱动、刷新率不改，未使用Computer Use，未提交／打包／发布，既有工作区修改保留。

## 2026-10-05 14:06 — 持续追踪解码表面与图形队列依赖（尚未完成根因收敛）

- 用户要求继续直至根因明确；本轮不以“呈现慢”结束。新增trace-vs105-calls.py/.js、analyze-vs105-calls.py、trace-vs105-gpu-etw.py、query-gpu-nodes.py、query-amd-metrics.py，并扩展两个原生／mpv测试宿主的可选暂停复制和只读AMD传感器。Frida17.22.1仅放tmp/modernization/vs105-instrument/deps；固定FFF二进制调用点要求094c19e…哈希，运行时改写只在自己的测试进程，不改磁盘DLL。
- 最关键因果对照：Shader保留全部Draw、跳过Copy为47.953fps／963解码963接受0丢帧0欠载；保留Copy跳过Draw24.17fps丢458；只复制64×64仍23.13fps丢495；原生跳过VPBlt47.969fps／964解码964接受0丢帧0欠载。跳过像素处理均为无效画面控制，不能当可用优化。完整逐调用Shader基线23.02fps，Present均值40.97ms，AMD内部NtWaitSingle P95 84.39ms；跳过复制／VP后长等待消失。
- 完整像素策略未修复：目标绑定520→8、源绑定520→512、纹理池22→12、Copy1 DISCARD＋目标SRV、实际设备Latency3→2、解码后／复制后Flush、复制移到Render接收阶段均未恢复实时。独立22纹理确实接入decoder view和输出Frame，源描述变Array1，却降7.76fps，未验收图片，不能当修复。早期独立纹理挂错VideoDevice索引5，后来修为7并加22纹理激活检查；旧无效数据保留但排除。
- 显式复制完成等待：Present8.52ms、CopyCompletionWait49.02ms、16.80fps、进度0.666倍；显式解码完成等待：Present7.45ms、DecodeCompletionWait22.68ms、31.37fps、进度0.729倍且欠载168。等待位置转移不是成功。Pause后100次相同完整8K复制＋GPU完成查询平均4.00ms/max5.87，64×64均值0.96ms；暂停前后decoded708/presented293/presents295/时钟不变。支持持续解码和图形读表面的重叠依赖是主要长等待来源。
- DxgKrnl独立会话成功，无需改权限；WPR GPU失败0xc5585011未改策略。shader-gpu-etw.etl174MB，tracerpt XML约1.825GB（外部工具编码原样保留），1,605,056事件／ETL丢失0，部分XML schema无法解释事件保留RawData。解析到tmp内gpu-queue-summary.json，解析代码本轮为内联，尚未做可复用分析脚本。QPC锚为首CalibrateGpuClockTask CpuClock和TimeCreated差值，按目标PID31904／Context稳定段筛选。同RX适配器PDH映射node0=3D、14=VideoCodec；图形排队66.82ms，视频49.53ms；已匹配0等待14为480次、14等待0为209次，尚有unknown来源。DMA跨度可能包含等待／抢占，不当纯GPU忙时长。全关键字追踪有开销，不能替代正式成绩；后续收窄关键字再对比mpv。
- Local预算7378MiB、目标用量最高2142MiB，未见该采样段预算耗尽。等待栈仅amdxx64模块偏移，无私有符号，不能命名内部驱动函数。实际源P0107680×4352 Array22，复制可见7680×4320；不再追究错误复制高度。
- mpv同COM探针：前几次未捕获Copy1是SetMultithreadProtected切换入口后漏刷新，不能据此说mpv零复制；已刷新Context1索引115。有效mpv-copy1-refresh：476次Copy1＋476次Present，源Array14 Bind520、目标Bind8、flags2，输出和解码新增drop0，进度1.0019，Present6.09ms。双方CreateVideoDecoder描述28字节和Config100字节逐字节一致。mpv设备创建flags0，VSflags32；去掉VS BGRAflag仍20.43fps。禁用VSR_3FP_PROFILE仍22.37fps，不是该原生诊断开关独自导致。
- 当前正进行AMD驱动只读PMLog采样对照（shader-amd已完成，mpv-amd正在运行；不调用Setter），补查实际图形／内存频率与功耗；VCN传感器当前不被驱动支持，不能把缺失当0或已读出媒体频率。随后继续解码／提交节奏、资源生命周期与GPU队列比较，尚无能保留有效画面恢复实时的修改；不要声称根因已确定到源码行或修复成功。
- 专项报告与tools README已补逐调用／GPU队列和实验边界。14:06 check-modernization通过133 Lua／41 Python，node --check通过，git diff --check通过（既有Git autocrlf提示不改变实际文件编码）。仓库master与origin/master仍同步，已有现代化和用户修改未提交且保留；不提交、不发布、不打包、不改发布流程，不使用Computer Use。下一步需要继续，不要求用户重新批准。

## 2026-10-05 16:17 — 8K队列预算根因与完整处理复测

- 正式094c19e DLL反汇编确认RVA 0x9310是128MiB／单帧估算并限制2–8帧，预算指令RVA 0x93ba。8K P010约94.92MiB，落到两帧下限；公开源码饱和条件queueLimit-1。原快照队列0–1帧。
- 仅进程内修改预算到398131200字节形成四帧上限，不跳过Copy／Draw／VP、不改原文件／系统设置。原预算Frida对照22.9486fps丢487；重新加预算47.9480fps零丢帧。无Frida原预算26.8188fps丢380、欠载32。
- 无Frida完整Shader三轮47.9858／47.9573／47.9486fps；VP三轮47.9615／47.9737／47.9426fps；六轮丢帧／合并／音频欠载0，解码与接受闭合，时钟1.00005倍。原生宿主可直接--video-queue-limit 4；核验SHA、原指令、保护恢复／指令缓存刷新。进程退出回退。
- 新双QPC标记ETW原预算VS／mpv图形队列66.73／3.89ms、视频队列50.01／13.57ms；修改VS后3.12／11.07ms，事件600733丢失0、帧962/962/0、音频欠载0。DMA视频跨度39.06→37.56ms不作为纯运算耗时；结束残差21.2µs在包络内。
- 旧CalibrateGpuClock配对约263ms锚点差异，未核验窗口；分析器默认拒绝旧锚点（显式兼容例外）。精简无标记试跑无效。工具新增独立标记、TDH ID查询、ID过滤；解析XML与性能采集串行。
- 不成功的控制：复制后释放帧引用14.27fps；GPU优先级7、宿主mpv.exe名称、20ms解码节流均不恢复；外加负载提高GFX频率仍慢且竞争GPU，不能据此排除所有DVFS。驱动ADL不提供VCN频率。完整实验详见播放对照报告。
- Frida加载阶段挂钩偶发卡住的试跑均排除并停止自有进程；预算实验迁移到宿主在DLL加载完、设备创建前直接改内存。原DLL SHA复核未变，不留下运行中的测试进程／会话。
- 已确认本机具体触发策略和有效缓解，未交付替换DLL，不声称GUI／HDR／其他片源通过；780M不同驱动和环境为何不触发需外部同包复现。建议上游区分硬件引用与软件图像队列预算，保留表面池余量和有限时间提前量。mpv不加入此补丁。
- 本轮无提交、打包、发布、驱动／刷新率变更，既有工作区修改保留。验证结果见后续核验记录。

## 2026-10-05 16:35 — 默认Jinc与跳转回归补齐

- Jinc原预算24.6626fps、丢427／欠载30；四帧限制三轮47.9409／47.9776／47.9536fps，新增丢帧／合并／欠载均0，正常时钟。持续播放有效缓解覆盖默认Jinc、双线性Shader及VP。
- 新宿主--seek-cycle：稳定段第6秒请求媒体60秒，记录控制事件和阶段；含控制事件的逐调用／GPU分析器拒绝直接整窗归一。原／四／八帧均约2秒目标位置等待，不能判为队列修改新引入问题，也不凭快照证明扫描画面。
- 媒体65秒后，原预算22.9822fps、新增丢381／欠载30；四帧47.9995fps、八帧47.9473fps，恢复段丢帧／欠载0。过渡四帧新增丢95、八帧33（各一次，非三轮对比）；仍不能称为完整启动／seek修复。未出现持续失败状态或软解回退。
- 验证：45份tools Python／VS vpy语法、Frida JS语法、git diff --check通过；磁盘DLL SHA仍094c19e…。本轮不改Lua，既有Lua验证结果不冒充重跑。没有打包／发布／外发消息。
- 后续仅在需要可交付的上游修复时：基于准确源码重构硬件引用队列预算并验证启动／seek、不同片源和HDR；已有本机根因及缓解证据已闭环。不要再次停在“Present慢”，也不要把未知AMD私有函数命名为确诊驱动缺陷。

## 2026-10-05 17:10 — 色彩准确与播放性能继续优化研判

- 用户要求先研判并汇报概览，再研究SDR／HDR色准、性能、兼容及健壮性；用户明确面向公开配置、多种硬件、稳健默认与可选模式。本轮不实施播放配置变更，不要求额外确认研究工作。
- 读取AGENTS、HandShake、STATUS快照与专项报告；docs/codex/INDEX.md不存在，直接沿STATUS工作。git pull --ff-only已是最新；master与origin/master同步，工作区既有大量现代化／用户修改保留。
- 新报告：docs/modernization/色彩与性能继续优化研判-20261005.md；公开证据：continued-audit-results-20261005.json，含本次被测活动文件SHA-256。原始探针与隔离日志在忽略tmp/modernization/continued-audit-20261005及validation，不公开个人日志。
- 六个状态探针复现：同目标HDR切集重建、恢复写入失败仍报可用且丢失重试基线、重复选择不检查外部改写、HDR支持标记变化未使能力签名失效、增强reset覆盖后续同步修改、专家Shader入口未经过推荐HDR保真门禁。专家差异不等于证明Shader错色；夹具不等于HDR实机故障。同模式target-trc漂移在真实IPC复现。
- 四组已有Lua回归、color-reference数学通过；check-modernization检查133 Lua／46 Python及引用通过，静态历史stats核对不算重跑性能测试。五类隔离软解素材SDR↔ICC切换源属性保持；640×360 HEVC10两条D3D11VA路径启动／跳转保持，日志无错误。均无HDR面板色准、新4K性能基准或提升百分比结论。
- 直接配置发现：常规色彩快捷入口绕管理器、HDR菜单术语不精确、持久化仍含vf。当前本机持久化vf为空，映射／参考白auto，不能声称实际已受残留滤镜影响。
- 路线：先修恢复与错误汇总／同目标免重建／状态漂移／增强所有权，再收敛常规菜单与持久化；随后三轮测直接与copy硬解、缩放和峰值候选；HDR面板、多GPU、动态格式与长时测试独立验收。保留高精度颜色解释，不将VS的进程预算补丁当mpv通用设置。
- 未改活动配置、脚本、核心、驱动、Windows HDR、发布流程或持久化用户文件；测试全部使用隔离no-config与独立IPC，不加载persist_properties。自有播放器正常关闭。git diff --check通过，既有autocrlf提示未转换实际文件；无提交、打包、发布。


## 2026-10-06 21:28 — 滤镜恢复、色彩状态与播放性能计划实施完成

- 承接已批准计划与 HandShake；保留既有脏工作区。master 与 origin/master 同步、发布仍为 v1.5.7；不执行提交／打包／发布，不修改发布流程。
- `quality.lua` 统一直接启用：四个旧硬编码禁用菜单恢复；真实初始化、具体 traceback、失败恢复前链、取消／切集／新选择令旧回调失效。普通流程没有组件扫描、显卡名核查、整包校验或模拟帧子进程。HDR／广色域／倍率只提示；VS 并发请求 4；上游变化重建已有补帧，保留降噪→超分→补帧与 Shader 组合。
- 通用 RIFE 使用 ORT／DML，不依赖缺失 core.rife；STD／NCNN 的失败只影响实际 STD 选择。保留 4.25 Lite，新增 DML／TRT 的 4.26／Heavy；DML 三模型实际播放通过，NVIDIA 路线未冒充验收。
- 新 `color-target.lua` 自动匹配已知显示目标，未知用 SDR sRGB；手动／外部覆盖会话内保留，主动重选可重新应用、恢复自动匹配可解除覆盖。恢复失败保留选项和播放轨道重试基线，重建／定位失败事务回滚；同目标切集无撤轨。切集取消旧定位恢复。ICC／峰值按显示身份及桌面 HDR 模式保存，手动 ICC 换屏也不沿用另一屏的记录。
- 更新 input.conf、quality_status、hwdec-select、profiles、persist_properties 与脚本选项；更正 HDR 输出标记／峰值分析、精确跳转的含混标签。移除跨启动临时 vf／片源修正，保留用户历史 JSON；长期偏好保留。禁用增强时只恢复仍等于最后写入值的同步／插值／去色带，失败显示错误并可重试。
- 本地组件 K7sfunc 1.3.1→1.8.1、VSORT v15.16 配套依赖、zsmooth 0.20.0 generic x86_64（MIT 原许可证留存）。ORT 1.23.0、VS R73、TRT v15.14 保留；旧 SVP flow2 4.3 与现用 4.6 重复加载，旧 DLL 移入本地 backup。维护清单 31 个改动相关条目与实际哈希相符，全部登记路径存在，不成为用户播放前核验。
- 功能验证：test-quality-state.lua、test-color-state.lua（含持续轨道恢复失败重试）、test-hwdec-select.lua、test-hdr-lifecycle.lua 通过；test-quality.py 11 实播案例与四类组合至少 20 秒正常推进；validate-quality-menu.py 完整菜单／十二 Anime4K／HDR广色域允许选择／清空隔离通过。ArtCNN 首次编译约 24 秒，测试允许真实初始化时间，不增加模拟预热。
- 色彩验证：validate-color-target.py 五类实际素材 SDR8／10、广色域 SDR、HDR10、HLG，实际 scRGB FP16 软件协商、外部覆盖与重选通过；test-color-preferences.py 两次启动、显示 UID／桌面模式隔离、ICC 换屏及同目标无撤轨通过。validate-color-ramp.py 16bit GPU 截图最大码值误差 0、1024 灰阶；validate-color-range.py 10bit 全／有限范围端点通过，不等同仪器或中间纹理测量。
- 完整配置 test-playback-compat.py：HEVC10 D3D11VA、WASAPI 静音设备、双字幕、HTTP、菜单／徽标通过；test-playback-sizes.py 720p60／1080p23.976／2160p30 通过，均用 isolated-config.py 防止污染用户历史与持久设置。
- benchmark-playback.py 同 4K30 H264＋AAC／1080p165Hz SDR，预热 5 秒、至少 20 秒、三轮交替：direct／copy／低功耗／高质量 CPU 单逻辑核心百分比中位数 6.586／17.104／5.678／6.095；显示掉帧分别 0,10,0／42,300,56／0,1,0／6,26,21。copy 一轮发生一次真实音频欠载（两行日志）；媒体时钟正常，解码掉帧全部 0。直接硬解 CPU 相对 copy 下降约 61.5%，默认推广 auto-safe；保留正常 GPU 表面复制，不默认零复制，不自动降低画质。高质量保留手动。
- `benchmark-playback.py --verify-direct` 补三轮相同条件逐半秒稳定性核查，全部零显示／解码掉帧、零音频欠载／错误，时钟 0.9984～0.9992；持续掉帧增长断言通过。
- benchmark-peak-seek.py：640×360 HDR10→SDR 峰值 auto／no 各三轮至少 20 秒、掉帧 0；CPU 中位数 6.362／0.614，关闭改变映射故保留 auto。长 GOP 五次精确定位、各三轮，中位数 no／yes 0.138／0.075 秒，缺 SVP／音频组合验收，暂不推广。benchmark-startup.py 管理器／相同完整配置去除管理脚本各三轮，就绪中位数 0.586／0.585 秒，冷缓存差异明显，无稳定收益支持额外起播改动。
- 最终 check-modernization.py 133 Lua／55 Python 语法、Shader 引用、统计与徽标、用户选项逐字节保留、发布流程未修改通过；git diff --check 通过，既有 autocrlf 提示不改变文件 UTF-8／LF。
- 交付：docs/modernization/滤镜恢复与色彩性能优化结果-20261006.md、optimization-results-20261006.json、README.MD、tools/README.md 与历史报告当前入口。回退源路径清单在 backup/optimization-20261005-before/manifest.json，37 项；含配置、旧 K7sfunc 和旧 VSORT 配套依赖。原始素材／日志在 tmp 忽略目录。测试自有播放器均退出，不终止用户进程。
- 本机 `mpv.com --no-config --vd=help` 有 AV1／dav1d，没有 AV2；原始列表留在 tmp/modernization/optimization-20261005/decoder-list.txt。
- 范围限制：真实 HDR 面板色准与 NVIDIA／Intel、动态 HDR／DV 执行、非可定位 HDR 网络流和 1080p／4K AI 实时性能未验收。全部增强可主动尝试，不因此设解锁门槛。下一步仅外部设备验收或用户另行指定；建议提交当前阶段便于回滚，不替用户提交。

## 2026-10-07 16:29 — 播放体验回归修复完成

- 用户决定：固定 59.94fps 目标；达到目标保留原帧，不重复运动估计；只保留全分辨率 SVP；8K 为用户测试素材，明确不纳入此次验收。
- dynamic-crop.lua：移除未启用检测时的旧硬解警告；实播发现 lavfi 不自动下载 D3D11 帧，改为检测旁路显式 hwdownload＋原 hw-pixelformat，主链 GPU 表面保留。直接／copy／软件／HDR10 P010 实际裁剪及原色／PQ／矩阵／范围保持通过。
- quality.lua／MEMC_SVP_PRO.vpy：约60fps／更高帧率保留原帧，Lua 普通链不添加 VS；后端也有目标满足时直通；外部帧率改写采用保守实际初始化分支。无模型准备、核验、降分辨率或运动参数降级。外部帧率保守分支覆盖调用测试，未冒充任意外部链实机验收。
- quality_status.lua／color-target.lua：简洁启用项与详细色彩状态分开，通过 uosc 滚动显示，键盘信息项忽略处理且保持页面；无 uosc 时分页 OSD；截图确认可查看详情末项。input.conf 五个性能入口归入「其它」，取消后台准备改为取消启用。
- 实播：预热5秒后每轮>=20秒，三轮顺序执行且隔离输入。实际4K约60fps原帧保留、1080p23.976全分辨率SVP、4K30全分辨率SVP全部零显示／解码丢帧、零音频欠载，时钟比分别0.99965～1.00013／0.99967～1.00028／1.00028～1.00085。一次被鼠标暂停干扰的旧轮次已排除。
- 测试：test-quality-state.lua、test-color-state.lua、test-playback-followup.py、validate-quality-menu.py 通过；新增 benchmark-svp.py 实際完成4K30三轮；check-modernization.py 133Lua／57Python与资源／用户选项回归通过；git diff --check通过。普通起播／选择／菜单日志仍无组件扫描或模拟试跑。
- 交付：docs/modernization/播放体验回归修复-20261007.md、playback-fixes-results-20261007.json，README和tools文档同步。六个活动文件原件位于 backup/playback-fixes-20261006-before/，含清单。用户播放路径不写入公开结果。
- Git：master 与已知 origin/master 同步；全部既有脏修改保留；未提交、打包、发布，推荐按功能审阅并提交。版本未变化。真实HDR面板／NVIDIA／Intel等仍未验收。


## 2026-10-07 16:59 色彩精度核查与3FPlayer对照

- 用户提供3FPlayer仓库后，按此前色彩准确／处理精度优化范围继续核查；使用HandShake记录，不引入播放前核验。
- 普通渲染日志确有FP16纹理，隔离sRGB GPU截图现有1024灰阶最大码值误差0；纠正其范围，不能代表完整配置／所有滤镜／HDR面板。
- 实际FMT_CTRL测试：4208／42010保持；42012／42016／44416均转42010。固定709与2020NCL测试色块RGBS最大分量差0.014399（模型输入，不是最终滤镜色差）。
- 对应核心VS桥接写_ColorSpace而非_Matrix等字段，并通过_MP_IMAGE保留原图属性；仅检查输出标签会漏掉中途转换错误。
- 3FPlayer源码固定3fef8eb67d49da6dc92ab265cb67c07768895e5b；HDR FP16 scRGB、SDR8／10bit、像素回读与优化前后等价测试；未构建／执行，未做播放器色准排名。
- 文件：docs/modernization/色彩精度核查与3FPlayer对照-20261007.md、docs/modernization/color-precision-audit-20261007.json、STATUS与version/工作进度。运行库／播放默认未改；后续修复TODO已补。
- 验证：手动VS五种格式实际输出帧与矩阵数值，审阅现有截图结果和源码；可选bm3dcuda_rtc.dll初始化错误126已注明，测试不使用该后端。
- Git：master与origin/master现有状态同步；工作区有既有大量修改，均保留；未提交／打包／发布，无项目版本变更。


## 2026-10-07 17:59 源色彩与滤镜精度优化完成

- 用户明确：以理论标准和软件验证为目标，不要求专业测量；模型／后端精度尊重实际支持和体验，不强制高位深导致报错或卡顿。
- 已应用：K7七文件源矩阵与范围、FMT_CTRL整数YUV格式保留；六个非补帧入口修复源无效时长；八个RIFE入口只回退无效输出时长。模型RGBH／RGBS和推理FP16／FP32不改，SVP8／10主路径不改。
- 42用例通过：标准矩阵独立复算、格式、真实CCD／RIFE-DML静态色块、有效VFR／EOF属性保留；完整配置五类GPU色块最大码值误差38／1／1／110／98。
- 16bit CCD＋RIFE长片稳态 20.055 秒，时钟比 0.998323，显示／解码掉帧0；短片循环与跳转通过。短片每次重建模型仍有初始化开销，不将其混入稳态或冒充性能收益。
- HDR10／HLG增强一致性通过，CCD差异0／0，组合差异0／7；隔离副本暂停真实显示检测以保持模拟能力，实际rgba16hf／scRGB及SDR回退通过，未改变Windows HDR。
- 最终验证：test-quality.py 11项实际启用／组合／STD缺失回退／无预检子进程通过；两项Lua状态回归、ICC偏好、PQ／HLG数学、133Lua／62Python语法、资源引用与git diff --check通过。
- 修正测试夹具的输入范围声明并逐字节解码回读；原先偏差来自夹具，不修改播放器色彩默认来迎合错误输入。最初完整配置测试写入的6条本轮测试历史已定向清理并备份，其他历史原字节保留；后续完整配置测试均使用隔离副本。
- 运行库修改配方与GPL署名／许可、手动应用工具及对应组件摘要已保存；维护工具不接入起播／菜单／选择。三个根backup快照包含原件和清单。
- 报告：docs/modernization/源色彩与滤镜精度优化结果-20261007.md；摘要color-precision-fixes-results-20261007.json；工具README、STATUS与工作进度更新。原核查报告保留为修改前记录。
- Git：master与origin/master现有状态同步；工作区 102 条状态含大量既有修改，未覆盖；未提交／打包／发布，未改发布流程或项目版本。

### 2026-10-07 20:22 — FP16 处理链路边界复查

- 同工具延续，沿用 AGENTS.md 与 STATUS 状态；工作区既有修改保留，不重复拉取。
- 复查十份既有真实 GPU 日志：五类素材×默认／scRGB 均实际创建 rgba16hf、rgb16hf；不是仅列出支持格式。
- 当前配置无主动低位深 FBO 覆盖；十处低位深 Shader FORMAT 都是辅助 TEXTURE，不误判成主图像 8bit。
- 区分 GPU 中间缓冲、模型／VS 整数交接、最终输出和系统显示；不能宣称任意组合全程 FP16。上游 fallback 解释与本机二进制证据分别标注。
- 新增 docs/modernization/FP16处理链路边界核查-20261007.md；无运行配置修改、无新播放器测试、无新增播放核验；未提交／打包／发布。

### 2026-10-08 11:12 — 延续优化：状态修复与独立 HDR 参考（进行中）

- 用户明确继续已讨论的优化路线；应用 HandShake，同工具、同工作区延续，保留既有大量未提交修改，未再次 pull／提交／发布。
- `quality.lua` 新增真实 video-reconfig 完成事件，修复同帧率 CCD 已工作但显示启用中；`color-target.lua` 原生表去重并将两个未知 NaN 视作相同，短诊断逐帧重复状态广播由数百降至3次。状态／滤镜／精度 Lua 回归通过。
- 精度详情明确整数有效位深、浮点存储及实际硬解／VS交接；不从最终输出推断全部内部阶段。
- PQ／HLG 独立GPU参考通过，最大通道误差0.539／0.610 cd/m²；正负分离16bit PNG测量，不是原始FP16、默认动态映射或面板验收。K7补丁已知版本覆盖恢复／只读／幂等／未知版本全量拒绝通过；生产7文件仍为已应用状态。
- 三轮性能尚未收尾。2轮与手动菜单验证进程区间重叠已排除，隔离留档后串行重测；不同配置、最小化或短诊断均不混入最终三轮结论。菜单功能验证本身通过。4K CCD性能不足已有证据，不自动降低分辨率。
- 修改前3个脚本已归档到 backup/modernization-20261008-before-handoff，保留旧优化；结果报告当前是草稿，须补齐统计、资源与真实UI／HDR状态回归后方可报完成。GPU测试须串行，当前 benchmark-filter-handoff.py --resume 正在运行。版本仍v1.5.7。

### 2026-10-08 11:57 — 完成滤镜交接与HDR数值优化

- 完成已讨论四项：交接性能与恢复、独立HDR参考、精度可观察性、组件更新补丁保留。没有新增普通流程组件核验／解锁／二次点击，没有强制模型FP16，没有修改硬解／性能档／色彩目标默认。
- 修复 quality.lua 同帧率已初始化却卡在启用中；color-target.lua 原生字段比较替代JSON键序签名，两个未知NaN视为同一值。18份完整日志状态发布2～4次，真实显示／亮度／覆盖变化仍通过。
- quality_status.lua 正确加载 render-precision.lua，明确整数有效位深、浮点存储、实际GPU／copy／VS交接，不由最终输出推断全链路。单元与完整配置P01010bit、模拟HDR实际rgba16hf详情通过，简洁／详情截图人工检查通过。
- benchmark-filter-handoff.py：相同SVP1080p23.976、CCD4K30、RIFE4.26DML640×360HEVC10，直接／copy，各预热5秒后三轮至少20秒；18组54次启停暂停精确跳转，关闭后5秒时钟0.9919～1.0051，GPU／copy原格式、源尺寸、解码器和活动链恢复。SVP和RIFE稳态无显示／解码掉帧；CCD4K两路不实时，不推广；没有统一copy稳定收益，默认保持。2轮菜单运行重叠、旧配置、最小化与短诊断排除留档，最终无GPU维护测试并行。
- SVP／CCD性能夹具无音轨，不能据零日志宣称音频通过。test-filter-av-handoff.py另用HEVC10＋AAC对两路验证SVP、CCD+SVP、CCD+RIFE、STD缺后端原链恢复、暂停跳转切集与实际精度详情，8个预热后5秒兼容样本时钟0.9955～1.0000，零掉帧／稳态音频欠载。RIFE性能六轮加载／重初始化阶段每轮4个实际欠载事件仍保留；稳态20秒均为零。
- test-filter-gpu-memory.py三次启停PDH观察：关闭后GPU专用内存SVP约187.8MiB、RIFE77.6MiB、CCD469.3MiB的平台，无持续增长；私有内存有波动，不证明长期无泄漏。VS／DML大部分资源释放，renderer／Python／driver缓存不强制清空；退出无实例不冒充测得零。
- test-hdr-gpu-reference.py PQ／HLG分别16色块独立参考通过，最大通道误差0.539／0.610cd/m²，固定逐通道阈值0.10+0.002×abs(reference)。正负分离16bitPNG与校准常量读回，非原始FP16、默认动态映射或面板验收。test-color-hdr-config.py HDR10／HLG静态CCD／组合差异0／0与0／7码值，模拟能力实际FP16scRGB及恢复SDR通过；WindowsHDR不变。
- 维护补丁工具 apply-k7-color-fixes.py 重构隔离root入口；test-k7-patch-update.py验证已知上游覆盖恢复、默认只读、幂等、其它补丁保留、未知文件全量拒绝。生产7文件只读核查均已应用，核心运行库本轮未改。
- 最终验证：Lua134／Python67语法、状态3项、既有所有权／HDR生命周期、菜单、playback-followup裁剪直接／copy／软解／HDR10及分页、color-preferences身份保存和同目标免撤轨全部通过。git diff --check无空白错误，仅仓库原有autocrlf提示，未改Git设置。
- 交付 docs/modernization/滤镜交接与HDR数值优化-20261008.md、filter-handoff-hdr-results-20261008.json、tools/README.md；修改前3脚本保存在backup/modernization-20261008-before-handoff含SHA清单，忽略目录测试原件不进公开包。HandShake与中文进度更新；版本仍1.5.7，不改版本迭代记录。
- Git：master／HEAD f7c6cab，103项工作区变更，绝大部分为此前工作；保留全部既有修改，未pull／提交／打包／发布。建议用户整体审阅后再提交，切换代理／设备前保留本记录。测试进程均已关闭。


### 2026-10-08 12:18 — 对照本地改造与 mpv-Yaozhi

- 用户询问大幅改造后与常规整合包（以mpv-Yaozhi为例）的差异；已读AGENTS、STATUS及10月4日至8日专项报告，核查当前mpv.conf、quality.lua、color-target.lua、精度模块与K7补丁配方。旧实施报告是历史行为，以10月6日至8日结果为准。
- 公开资料：核查Yaozhil/mpv-Yaozhi主分支README与Releases；最新1.0.6-2条目明确为公开版，旧内测条目的“稳定版1.0.2”不作为当前状态。杳知也有自维护核心、原盘导航、沉浸声、AI安全回退和统计优化，不能笼统称为简单脚本堆叠。
- 本地主要差异：统一显示目标与可信ICC偏好；源矩阵／范围和高位深格式修正；降噪→超分→补帧组合及真实失败恢复；一键尝试、没有播放前组件认证；直接硬解默认及手动性能档；分阶段精度状态与维护回归／补丁配方；退役弹幕而保留字幕。UI／起播徽标保留杳知来源，非独有原创。
- 结论边界：本地10月改造未进入公开v1.5.7；没有双方同条件性能／色准实测，不宣称全面领先、全链路FP16、4K AI普遍实时或真实HDR面板色准已验收。61.5%CPU下降仅为本机直接／copy对照。
- 本次未修改活动配置、运行库或安装器，未运行新的播放器性能测试；仅更新本记录与中文进度。git pull --ff-only返回Already up to date；master／HEAD f7c6cab，103项工作区变更保留。未提交／打包／发布，版本不变。
- 来源：https://github.com/Yaozhil/mpv-Yaozhi/blob/main/README.md 及 https://github.com/Yaozhil/mpv-Yaozhi/releases/tag/mpv-Yaozhi-1.0.6-2 。


### 2026-10-08 12:21 — 用户明确项目定位与维护优先级

- 用户明确：对超分、补帧等画质增强不感兴趣；首要关注SDR和HDR下色彩显示的准确。增强作为已经存在的模块，需要维护。
- 后续分析与改动以源矩阵／范围／原色／传递函数、显示目标匹配、HDR映射与输出标尺、可信ICC、输出精度和软件数值验证为优先依据。增强模块的维护重点是兼容、正确色彩交接、可关闭、失败恢复和不干扰普通播放；新增模型、扩充算法或追求增强效果不属于默认工作目标，需用户明确要求。
- 保留用户既有增强模块、菜单和选择权，本次不调整运行配置，不据此删除功能。颜色准确的判断不以饱和度／锐度／顺滑度或模型数量代替；软件数值验证与真实显示端测量分开说明。
- 仅更新STATUS当前快照与中文进度；项目版本保持v1.5.7，既有103项工作区变更保留，未提交／打包／发布。


### 2026-10-08 12:27 — 核查正常播放色彩准确与FP16后续优化方向

- 用户关注SDR／HDR色彩正确性和全链路16bit精度，要求对照Lake1059/FFF_Project寻找值得优化处；本次为源码／资料评估，不实施配置变更。
- 已读取本地10月7日精度边界报告、3FP对照及路线，并沿用10月7日至8日已完成源矩阵／高位深修复和PQ／HLG独立数值结果；不将旧报告的缺陷重新认定为未修复。
- FFF_Project远端master核查为12d8afca95c29fb9cc5101a8d4991b4a83af0d36；在忽略目录reference克隆fetch并用git show固定提交读取VideoRenderer.cpp，未切换原3fef8eb工作树。源码可见HDR／scRGB FP16输出、经典SDR源8／10bit输出及可选高位深SDR scRGB策略；支持原始半浮点交换链像素／区域读回。源码不能支持“Windows最强色准”的普遍排名。网络raw初次502／超时，后由git取回；未执行第三方播放器。
- 本地具体候选：color-target.lua仅以HDR开关区分显示模式，偏好key为uid+hdr-status，尚无独立SDR Advanced Color／ACM策略；需核查系统／应用ICC职责及校色变化时偏好失效，而非直接强制所有SDR scRGB。微软文档区分SDR Advanced Color参考白与HDR scRGB80nit标尺。
- 普通HQ／Balanced为linear-downscaling=no、cscale=bilinear；HighQuality开启线性缩小。候选为不含AI的线性缩小、色度位置／重建与混合色边像素回归，先测平均亮度／色差及播放负载，再决定默认；不机械启用线性放大。
- 当前数学GPU验证已包含PQ／HLG正负值与高位深PNG编码读回，但不是原始FP16纹理／交换链采样；补充直接浮点读回需独立诊断工具或诊断核心，不能仅靠Lua或16bitPNG完成。现有流程不新增起播预检。
- HDR后续重点为完整默认配置下的亮度保真区间、超峰值映射、动态峰值／场景切换、SDR在HDR桌面的参考白与OSD／字幕合成、输出量化／抖动；不能把隔离转换通过等同于默认映射全部通过。
- FP16浮点与整数16bit不同；源8／10bit和最终8／10bit输出不等于中间处理错误，禁止为了名称把全部输入／输出强制同格式。增强模块仅保持兼容维护。
- 来源：FFF_Project固定提交VideoRenderer.cpp；https://learn.microsoft.com/en-us/windows/win32/direct3darticles/high-dynamic-range 、https://learn.microsoft.com/en-us/windows/win32/wcs/advanced-color-icc-profiles 、https://mpv.io/manual/master/ 。
- 本次未运行新的播放器／色差测试，未更换运行库；仅追加STATUS／工作进度与忽略目录参考源码。既有103项工作区改动保留，未提交／打包／发布，版本仍v1.5.7。

## 2026-10-08 13:49 — 菜单整理与 SDR ACM／FP16 色彩优化收尾

- 用户指令：删除 bilinear 低功耗档，默认 HQ；其它放工具和最小化之间；视频滤镜只保留直属全清空；继续色彩准确优化。全程保留此前修改，未发布／提交／改项目版本。
- 起始 master／f7c6cab 与 origin 同步，git pull --ff-only 已为最新；起始 103 个脏工作区条目，本轮收尾 105 个条目（不是文件总数），未覆盖已有 VS／安装器等修改。
- 活动配置：Performance-LowPower 与菜单／状态映射删除；旧低功耗偏好降级默认 HQ，用户保存高质量仍尊重。默认 HQ 线性缩小；其它排序已在真实菜单树与截图验证；清空 VF 直接可达并覆盖外部 VF，Shader 独立清空。
- 新增 display-color 原生只读 DisplayConfig v2 检测与低频变化发布。本机实际 WCG／SDR ACM 识别成功；经典 SDR、ACM、HDR／未知边界分开，镜像目标歧义不猜测。
- color-target：SDR ACM 用 BT.709 线性 FP16 scRGB／工作白 1.0、Windows 负责终端校色，不叠加显示 ICC；ICC 保存／关联上下文校验；scRGB 取消前置抖动及自动驱动黑位补偿，显式对比度仍尊重。手动 SDR 随桌面 ACM 状态调整输出编码，用户意图保持。
- 输出配对用同一 apply-profile；包括原生 profile 部分失败回滚、免重建、恢复重试与空 target-gamut→auto 的等价恢复／去重。缺 profiles 的独立脚本环境保留降级路径。
- 核心原始读回发现旧 libplacebo 92b5ac6 最后输出无条件夹到 0～1；官方修复 99e80abd 恰为其后继。校验官方资产 SHA，先验证隔离核心后更新本地匹配 mpv.exe／mpv.com／DLL／手册；新核心 36bf3d529／libplacebo 0d043c7。内嵌 FFmpeg 同步更新，独立 ffmpeg 工具未替换；components.lock 仅更新对应核心／色彩字段。
- 原始 FP16 数值：标尺／负值／超过 1、实际 SDR ACM 1024 灰阶、广色域 SDR、软件隔离 PQ／HLG、线性缩小均通过。PQ／HLG 注入能力并隔离 SDR 桌面提示／参考白覆盖，非真实 HDR 桌面；FP16 存储不等同所有阶段 16bit 有效精度。
- 性能：4K→1280×720，完整配置、直接 D3D11VA、WASAPI 静音，预热 5 秒后采样≥20秒，线性／非线性各三轮；六轮所有掉帧／延迟／错时计数为零，时钟 0.99869～1.00017，无错误或音频欠载。GPU fresh 平均阶段总和中位数 2.021735→2.051011ms（约+1.45%），CPU 单核心 5.99→7.36%。早期窗口受工作区尺寸限制的轮次未计入最终固定尺寸结果。
- 回归命令：test-color-output.py、benchmark-linear-downscale.py、test-color-preferences.py、validate-quality-menu.py、test-playback-compat.py、test-color-config.py、test-color-hdr-config.py；Lua test-color-state／test-quality-state／test-hdr-lifecycle／test-render-precision；check-modernization（Lua136／Python70）。全部通过。追加 H2648 完整配置 D3D11VA／实际 ACM 无错误；H26410 菜单素材在本机软件回退，未计为硬解通过。
- 报告 docs/modernization/SDR-ACM与FP16输出优化-20261008.md；结果 color-output-results-20261008.json；新旧 SHA 与来源 color-output-core-manifest-20261008.json。维护 Frida 17.22.1 仅在忽略依赖目录，日常播放不注入、不增加预扫描。
- 最终校验：正式摘要／核心清单 JSON 可解析，实际核心及锁定文件 SHA 一致，活动代码／配置 UTF-8 LF，git diff --check 通过；master 与 origin 同步，工作区仍有 105 个条目。
- 回退 backup/color-accuracy-menu-20261008-before/ 保留本轮前配置及匹配核心；新增检测文件回退时一并移走。版本仍 v1.5.7，未来发布核心／运行时变化必须执行发布流程 Gate；本轮未改发布流程、提交、打包、上传。
- 可选后续保持：真实 HDR／仪器测量、其它 GPU、动态 DV 和 RIFE 初始化／CCD 性能独立优化；没有阻碍本轮收尾的依赖。切换设备前建议审阅并提交配置差异，另行保存忽略的运行时及备份；不要全仓库 reset。

## 2026-10-08 15:21 — 用户搁置8K软解优化；发布准备、项目清理与起播抬窗

- 用户已将目标改为“先搁置优化，做下个版本的预发布工作、清理项目文件”，随后要求修复起播不在桌面前面。本轮作为原任务转向，不继续性能优化、不推广实验参数。
- 已完整读取发布流程／项目架构，沿用 HandShake；git fetch origin 后 master／origin 差异0／0。起始大批未提交改动保留，没有reset、暂存、提交、推送或创建标签。
- 搁置性能证据：纯解码单轮约27～28fps；完整HQ三轮基线媒体推进中位数0.5445、12线程0.5701、8线程0.5760，均有大量VO丢帧，均非8K48达标。目标7840HS为用户提供的暂定型号，CPU-Z分数不能线性外推。9轮原始结果已归档，摘要 av1-software-paused-20261008.json；未降低位深／处理精度。
- 清理：backup/project-cleanup-20261008-151325/archive-manifest.json 记录707项（551文件、156目录）；独立文件移动前后SHA一致，目录同盘整体移动未逐文件哈希，无永久删除。保留当前色彩／播放夹具、探针deps、用户cache/files、核心／VS／模型、开发backup及release。旧参考源码、ETW/XML、下载解包、R80候选、一次性脚本及生成缓存已归档。
- .gitignore新增.zcode与Python生成缓存规则；保留本地计划文件，不纳入发布提交；新增／改动文件UTF-8 LF。起播脚本及选项默认启用；不改用户window_size_position.conf。
- 起播修复：window-foreground.lua＋window_foreground.conf；有效原生HWND获取后一次申请前台，后台激活限制时原生短暂抬升并立即还原普通层级，不写ontop。窗口等待最多2秒，结束／退出取消；自动EOF下一集、暂停／继续不抬窗。保持原持久置顶与非Windows降级。
- 原生回归：test-window-foreground.py用自有遮挡窗口与完整隔离配置，旧版起播／IPC重新打开仍被遮挡，修复后抬到上面；最小化恢复、保存ontop=no、原生TOPMOST为false、暂停和自动切集均通过。系统拒绝部分键盘焦点请求时显示顺序仍通过，不声明强制焦点。结果 window-foreground-results-20261008.json；专项报告 起播窗口前台修复-20261008.md。
- 3.1：fetch、分支差异、工作区审阅完成；未提交改动仍须按功能／构建／结果逻辑整理，发布前未满足干净提交要求。
- 3.2：触发Gate，涉及mpv核心、Python／关键VS插件／模型升级与安装更新／退役迁移交付；停止打包／发布。发布流程本身未改。需要用户决定流程修订或豁免；既有第三方组件许可待补证项仍须解决，不能视为已获授权。
- 3.3：docs/发布准备-20261008.md完成内容、包归属、发布草稿与Gate清单，架构及工具说明更新；STATUS／中文进度追加。项目仍v1.5.7；.vanta-version逐字节1.5.7；安装器仍0.3.12，版本均未擅自递增。
- 3.4：check-modernization通过Lua137／Python72、Shader引用、既有用户选项逐字节、徽标素材与流程未改检查；test-playback-compat通过HEVC10硬解／音频／双字幕／HTTP／DRA；validate-quality-menu、test-updater官方资产选择／失败恢复、test-retired-component迁移保留与幂等通过；git diff --check通过。
- 输入只读审计：10,019核心／VS锁定文件逐个SHA256一致，新增／修改活动配置与安装文件均有现有包归属，四包输入无缺失、禁止缓存／日志／根backup/tmp泄漏或Lossless/LSFG命名；不等价实际新归档验证。完整清单与脚本SHA在tmp/release-prep-20261008/；pip包内部合法operations/build源码保留，不误判为根build泄漏。
- 构建入口六个PowerShell语法通过，未修改；VantaInstaller源码Release编译0警告／0错误，仅编译检查，不是单文件发布产物。旧release安装器不含迁移改动，实际发布需重建独立候选。01／02／04需重建；03输入数量／字节与上版相同，仅为复用候选，仍需完整4.1.1证明。
- 第4～5新包／7z完整性／SHA／版本标记／覆盖安装／全功能验收未执行；第6～8标签／上传／镜像未执行。本次“预发布工作”为本地准备，流程规定GitHubRelease必须正式发布，不创建prerelease。
- 当前工作区不干净；版本和Gate决定后再整理提交。切换设备前建议审阅并提交功能／文档，忽略运行时和归档须另行同步，禁止全仓库reset。

## 2026-10-08 15:29 — 用户确认v1.6.0并要求按流程发布

- 用户选择下一版1.6.0，随后明确要求准备完成后按发布流程发布新Release；后续正式发布、构建与流程内提交／标签／公开资产／镜像同步已授权，不再重复征询一般发布权限。
- 尚需用户单独决定流程3.2升级Gate：核心、Python／VS关键插件与模型变动。安装器退役迁移是附属功能，自身不单独触发Gate；此前日志中将其并列交付影响不代表它单独触发Gate。
- 发布报告已对齐v1.6.0；当前已发布版本标记仍1.5.7，构建前再同步，安装器独立版本尚未改。未开始包构建、标签、推送或上传。
- 补测原来ontop=yes时原生TOPMOST与mpv选项均保持true，窗口报告／JSON更新；现有check-modernization与diff检查通过。
- 03来源包7z t通过，SHA E139FB897C53B1610B62CD6A4C6A0E57C8D2544225005F720EC43FD1F927E2B2与v1.5.7记录一致；输入5121文件／4714825519bytes一致，最新修改2025-04-13。Gate后可按4.1.1复制为新版本规范名并复测，尚未生成新文件。
- 归档707项目标全部存在、moved标记全部为true；仅isolated／migration-test／lua-files.txt因后续验证重新生成源路径，不覆盖归档。107项Git状态条目，master与origin同步，既有修改保留。
- 当前等待用户决定一次性豁免或修订发布流程。决定后继续完整发布检查，包括既有第三方组件许可核对；不得把Gate豁免当作公开分发授权证明。

## 2026-10-08 15:41 — 用户允许发布，执行v1.6.0

- 用户回复“可以发布”，本次核心／运行时／插件模型升级Gate一次性豁免；四包编号、覆盖顺序、发布流程保持。继续全部授权构建／校验／提交／标签／上传／镜像流程，不重复确认。
- 第三方分发补证发现SVPflow2官方个人／非商业专有许可，Windows须SVP Pro；按强制禁止专有组件规则从02公开包排除该DLL。菜单／接口保留，本机文件不动；私用包从本机补入且绝不公开。02及私包脚本增加明确排除／本地保留规则，是本次已授权发布的必要内容修正，范围已向用户说明。
- 补GPL文本与来源，SVPflow1 GPL来源独立于SVPflow2许可；TensorRT OSS Apache与SDK运行库分发授权分别核对，不将总体GPL覆盖厂商SDK。NVIDIA SDK许可原始页面保存在忽略调查目录。
- 安装器新增迁移功能，为避免与旧exe混淆，必要补丁版本独立递增0.3.12→0.3.13，不影响mpv1.6.0。根.vanta-version已写纯1.6.0（UTF8无BOM无换行）。
- git fetch已同步0／0，gh账号认证可用，远端尚无v1.6.0Release；预计01／02／04重建，03原样复用已验证v1.5.7来源。

## 2026-10-08 16:13 — 用户要求优先开箱即用，恢复既有SVP整合边界

- 用户明确指示“不用管许可边界，之前也是正常发布的”“优先保证开箱即用”，覆盖前述临时SVP排除方案。恢复02全部既有SVP运行组件和私包正常并集，删除新增public_distribution排除字段，README不再要求另装SVP。保留作者原始许可／来源文本，不作额外授权声明。
- 仅终止自己创建的02-v1.6.0压缩进程；无公开资产上传。02重新构建；01此前含临时SVP说明和排除清单，必须重建以与最终README／锁定文件一致。04尚未构建。
- 7734955为功能提交；d122216修复维护ABI工具的既有CRLF暂存检查问题；efdf1d2临时SVP排除随后撤销，历史保留。全portable Lua139、活动Lua137／Python72通过。
- 安装器单文件0.3.13构建完成；首个探针在窗口尚未创建时过早判失败，需改为有界等待有效窗口后再检查，并非已证实产品启动失败。
