# MPV Vanta Edition

> 个人定制版 MPV 便携播放器，按编号覆盖、按需组装。
>
> Fork from [gaoxing64/MPV-lazy-full](https://github.com/gaoxing64/MPV-lazy-full) v2.0.0

## 四类包的关系

```
01 Base（核心播放器 + 基本配置，首个安装）
   ↓ 追加
02 Extras（着色器、VapourSynth、Python、工具）
   ↓ 追加
03 Faster-Whisper 扩展包（AI 语音识别运行时）
   ↓ 最终覆盖
04 Config（个人设置、OSC 主题、字体，最后安装）
```

| 顺序 | 包 | 解压即用？ | 内容 |
|------|----|------------|------|
| **01** | **Base** | ✅ 基本播放 | mpv 核心 + 运行时 + 基础配置 + 启动 Logo 素材（启动页/起播格式 Logo）+ 随包检测专用 ffmpeg（起播徽章后瞻检测） |
| **02** | **Extras** | ✗ 需要 Base | 着色器、VapourSynth 补帧/超分、Python、工具 |
| **03** | **Faster-Whisper** | ✗ 需要 Base | AI 语音识别字幕运行时；语音模型首次选择时自动下载 |
| **04** | **Config** | ✗ 需要 Base | 个人设置的最终覆盖层，最后安装；不含大型 Logo 素材（归 01） |

## 安装与覆盖顺序

四类包全部安装时，必须按文件名前缀从小到大覆盖：

1. `01-mpv-base-vX.Y.Z.7z`
2. `02-mpv-extras-vX.Y.Z.7z.001`（`.002` 放在同一目录，只解压 `.001`）
3. `03-mpv-fasterwhisper-addon-vX.Y.Z.7z`（可选 AI 字幕）
4. `04-mpv-config-vX.Y.Z.7z`（个人设置，最后安装覆盖）

包之间允许存在交集以保证各自可用性。04 作为最终覆盖层可覆盖前面所有包的同名文件。
单独更新配置只需解压 04。


个人本地也可以生成 `mpv-full-private-vX.Y.Z.7z`。它会按 01～04 的顺序合并全部
公开包，形成解压即用的一体包。
该包含个人运行时状态与工具，只限本地备份和使用，不能公开上传。

## VantaInstaller（推荐）

> 三合一辅助工具：安装 / 卸载 / 设置，单文件自包含、免 .NET 运行时，随 Release 附装。

从 [Releases](https://github.com/maxzrb/mpv-vanta-edition/releases) 下载 `VantaInstaller-win-x64-v0.3.3.exe`，双击即用。

- **安装**：扫描 01~04 增量包（或个人全量包），自动校验完整性，支持覆盖升级与配置备份；可选安装完成后自动注册文件关联。
- **卸载**：默认备份 `portable_config` 到 `文档\MPV Vanta Edition\uninstall-backups`，删除明细日志，可选清理文件关联。
- **设置**：启动/打开目录、文件关联注册（多实例/单实例）、配置备份恢复、检查更新并下载增量包（aria2 多线程 + 镜像测速）、mpv 高频设置调节（默认值即当前 mpv.conf）、缓存清理。
- **手动指定**：可指定已安装的 mpv 位置与配置备份目录，工具台优先识别。

### 文件关联：多实例 / 单实例

注册后可在 Windows「打开方式」里自行选择，两个入口名称不同：

| 入口 | 显示名 | 行为 |
|------|--------|------|
| 多实例 | **MPV Vanta Edition** | 每次双击经 `mpv.exe` 新开窗口 |
| 单实例 | **MPV Vanta Edition (Single Instance)** | 经 `umpv.exe` 通过 IPC 复用已运行的 mpv 窗口（保持 mpv 常驻时生效） |

- 设置中心「文件关联」卡片提供「注册/取消多实例关联」「注册/取消单实例关联」四个按钮，可分别注册；关联写入当前用户，无需管理员权限或 UAC。
- 安装向导「选择组件」页可同时勾选两种入口，安装完成后自动注册；两套应用身份与 ProgID 完全独立，注册或取消其中一个不会影响另一个。
- 默认声明常见视频与音频格式，但不直接篡改扩展名默认值；最终默认播放器仍由 Windows「默认应用」或「打开方式」决定。
- 新版使用 `installer\associations\icons\mpv-document.ico` 作为稳定文档图标。注册时若检测到确属当前目录的旧版 `io.mpv.*` 系统级 ProgID，会创建带标记的 HKCU 兼容覆盖，修复旧图标路径和打开命令，但不会修改 Windows 的 `UserChoice`。

仅使用 01 包或个人全量包、没有 VantaInstaller 时，可直接在 `installer\` 根目录双击以下新版当前用户镜像入口；它们会转发到 `installer\associations\current-user\` 中的唯一实现：

| 操作 | 多实例 | 单实例 |
|------|--------|--------|
| 注册 | `register-multi.bat` | `register-single.bat` |
| 取消 | `unregister-multi.bat` | `unregister-single.bat` |

四个 `mpv-install/uninstall*.bat` 已集中到 `installer\associations\legacy-system-wide\`，明确保留为**旧版系统级兜底入口**：它们写入 HKLM、需要管理员权限，主要用于兼容或清理旧注册，不作为新版默认方案。

## 下载与安装

### 方案一：使用 VantaInstaller（推荐）

下载 [Releases](https://github.com/maxzrb/mpv-vanta-edition/releases) 中的
`VantaInstaller-win-x64-v0.3.3.exe`，双击运行，在「安装」向导中选择
包含 01~04 增量包的目录（或直接勾选「下载并安装」），它会自动完成：

- 安装前对每个包做 SHA-256 校验（有风险会提醒，默认取消）
- 按 `01 Base → 02 Extras → 03 FW → 04 Config` 顺序解压覆盖到同一目录
- 可选：安装完成后自动注册文件关联（多实例/单实例，默认勾选多实例）
- 覆盖升级前自动备份 `portable_config`

### 方案二：手动解压（备选）

不安装 VantaInstaller 时，从 [Releases](https://github.com/maxzrb/mpv-vanta-edition/releases) 下载全部包，按顺序解压到**同一目录**：

1. `01-mpv-base-vX.Y.Z.7z`（核心 + 运行时 + 基础配置 + 随包检测 ffmpeg，必须）
2. `02-mpv-extras-vX.Y.Z.7z.001` 和 `.002`（着色器 + VapourSynth + Python；两个分卷放同目录，用 7-Zip 打开 `.001` 即可）
3. `03-mpv-fasterwhisper-addon-vX.Y.Z.7z`（可选，AI 字幕）
4. `04-mpv-config-vX.Y.Z.7z`（个人配置覆盖层，最后解压）

解压完成后运行 `mpv.exe` 即可。

### 方案三：只用配置

已有 mpv 播放器，只想用这套配置：

1. 下载 `04-mpv-config-vX.Y.Z.7z`
2. 解压到 mpv 的配置目录（覆盖 `portable_config/`）

### 方案四：手动组装

1. 下载任意标准 mpv Windows 构建
2. 下载 `04-mpv-config-vX.Y.Z.7z`，解压到 mpv 目录
3. 如需完整功能，再下载 `03-mpv-extras-vX.Y.Z.7z.00x` 解压

## 更新方式

- **仅更新配置**：下载最新 Config 包，解压覆盖即可
- **更新核心**：下载最新 Base 包
- **更新着色器/插件**：下载最新 Extras 包

日常小改动通常只需要更新 Config 包。

## 打包脚本

所有脚本都位于项目根目录，建议在 PowerShell 中从该目录运行。

### 一次构建四个公开包

```powershell
.\build-all-packages.ps1 -Version '1.2.0'
```

输出 01 Base、02 Extras 分卷、03 FW 和 04 Config 公开包。

### 同时构建个人私用全量包

```powershell
.\build-all-packages.ps1 -Version '1.2.0' -IncludePrivate
```

### 分别构建

```powershell
.\build-01-base.ps1 -Version '1.2.0'
.\build-02-extras.ps1 -Version '1.2.0'
.\build-03-fasterwhisper.ps1 -Version '1.2.0'
.\build-04-config.ps1 -Version '1.2.0'
.\build-full-private.ps1 -Version '1.2.0'
```

每个公开子包都有独立脚本，可单独构建，也可按需组合：

- `build-01-base.ps1`：构建 01，播放核心 + 运行时 + 基础配置（含 `.vanta-version` 版本标记与内置字体）。
- `build-02-extras.ps1`：构建 02，着色器 + VapourSynth + Python + 工具（自动分卷）。
- `build-03-fasterwhisper.ps1`：构建 03，AI 语音识别运行时。
- `build-04-config.ps1`：构建 04，个人设置最终覆盖层（不含启动 Logo 素材，归 01）。
- `build-full-private.ps1`：完整合并 01～04（仅本地）。
- `build-all-packages.ps1`：按 01→04 顺序一次构建四个公开包，`-IncludePrivate` 追加个人全量包。
- 所有脚本可用 `-OutputDir '目录名'` 修改输出目录，默认 `release`。

## 配置特性

### 音频
- WASAPI 输出，支持多声道
- 音速调整与音高校正

### 字幕
- 多语言、多格式字幕渲染
- AI 字幕生成（Faster-Whisper，需自行下载模型）
- 在线字幕下载（Assrt.net）

### 字体
- 便携包内置 HarmonyOS Sans SC Regular/Bold，mpv、uosc、纯文本字幕和相关脚本默认使用该字体，无需安装到 Windows。
- Windows 使用 DirectWrite 处理字体缺字回退；在系统存在时，最终回退到 Microsoft YaHei。统计面板的普通文本使用 HarmonyOS Sans SC，数据列和控制台补全等需要列对齐的字段仍保留 Noto Sans Mono CJK SC。
- HarmonyOS Sans SC 未被修改；原始版权与授权协议见 `portable_config/licenses/HarmonyOS-Sans-SC-LICENSE.md`。

### 界面
- 基于 [uosc](https://github.com/tomasklaen/uosc) 的现代化 OSC
- 移植了来自[杳知mpv整合包](https://github.com/Yaozhil/mpv-Yaozhi/)的优秀uosc界面，并在此基础上做了个人定制
- 弹幕系统（[uosc_danmaku](https://github.com/Loukyuu1120/uosc_danmaku)）
- 汉化统计信息 OSD

### 视频处理
- 500+ GLSL 着色器（Anime4K、FSRCNNX、ESRGAN 等 35 类）
- VapourSynth 补帧/超分/降噪（RIFE、SVP、DRBA、ArtCNN）
- HDR/SDR 自适应切换

### 快捷键
- `h/j/k/l` — 基本播放控制
- `i` — 临时显示统计信息，`I`或`TAB` — 常驻显示
- `1`~`5`/`0` — 切换统计信息页面
- `Ctrl+数字` — 快速切换着色器
- `Alt+数字` — 切换预设配置组

## 自定义

配置文件在 `portable_config/` 下：

| 文件 | 用途 |
|------|------|
| `mpv.conf` | 主配置 |
| `input.conf` | 键位绑定 + uosc 右键菜单 |
| `profiles.conf` | 条件配置组（分辨率/HDR自适应） |
| `scripts/` | Lua 脚本 |
| `script-opts/` | 脚本配置 |
| `fonts/` | 内置 HarmonyOS Sans SC 与图标字体 |
| `licenses/` | 内置第三方字体的原始授权文件 |
| `shaders/` | GLSL 着色器（Extras 包） |
| `vs/` | VapourSynth 脚本（Extras 包） |

## 项目来源

```
gaoxing64/MPV-lazy-full (v2.0.0)
    └── hooke007/MPV_lazy (原始 MPV-lazy)
    └── dyphire/mpv-config (配置参考)
    └── hooke007/mpv_PlayKit (着色器)
    └── LumeCraft-Labs/K7sfunc (VapourSynth 脚本)
    └── Yaozhil/mpv-Yaozhi (uosc界面参考)
```

## License

本项目各组件的许可证见各自源文件。原始项目按原作者 dyphire 的许可证约定执行。
