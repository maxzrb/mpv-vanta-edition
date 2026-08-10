# MPV Vanta Edition

> 个人定制版 MPV 便携播放器，按编号覆盖、按需组装。
>
> Fork from [gaoxing64/MPV-lazy-full](https://github.com/gaoxing64/MPV-lazy-full) v2.0.0

## 五类包的关系

```
01 Base（核心播放器 + 基本配置，首个安装）
   ↓ 追加
02 Extras（着色器、VapourSynth、Python、工具）
   ↓ 追加
03 Faster-Whisper 扩展包（AI 语音识别运行时）
   ↓ 追加
04 LSFG 扩展包（补帧，含控制脚本以保证联动可用性）
   ↓ 最终覆盖
05 Config（个人设置、OSC 主题、字体，最后安装）
```

| 顺序 | 包 | 解压即用？ | 内容 |
|------|----|------------|------|
| **01** | **Base** | ✅ 基本播放 | mpv 核心 + 运行时 + 基础配置 + 启动 Logo 素材（启动页/起播格式 Logo） |
| **02** | **Extras** | ✗ 需要 Base | 着色器、VapourSynth 补帧/超分、Python、工具 |
| **03** | **Faster-Whisper** | ✗ 需要 Base | AI 语音识别字幕运行时；语音模型首次选择时自动下载 |
| **04** | **LSFG** | ✗ 需要 Base | GPL Vulkan Layer、启动器、控制脚本、源码；内置 Lossless.dll |
| **05** | **Config** | ✗ 需要 Base | 个人设置的最终覆盖层，最后安装；不含大型 Logo 素材（归 01） |

## 安装与覆盖顺序

五类包全部安装时，必须按文件名前缀从小到大覆盖：

1. `01-mpv-base-vX.Y.Z.7z`
2. `02-mpv-extras-vX.Y.Z.7z.001`（`.002` 放在同一目录，只解压 `.001`）
3. `03-mpv-fasterwhisper-addon-vX.Y.Z.7z`（可选 AI 字幕）
4. `04-mpv-lsfg-addon-vX.Y.Z.7z`（可选补帧扩展）
5. `05-mpv-config-vX.Y.Z.7z`（个人设置，最后安装覆盖）

包之间允许存在交集以保证各自可用性。04 包含 LSFG 控制脚本以保联动，
05 作为最终覆盖层可覆盖前面所有包的同名文件。单独更新配置只需解压 05。

`04` 已内置 LSFG 补帧所需的 `Lossless.dll`，解压后即可开箱使用。
Lossless Scaling 为商业软件，尚未购买正版授权的用户请自行决定是否支持正版。


个人本地也可以生成 `mpv-full-private-vX.Y.Z.7z`。它会按 01～05 的顺序合并全部
公开包，并加入完整 `Lossless Scaling` 目录备份，形成解压即用的一体包。
该包含有个人购买软件中的专有文件，只能本地备份和使用，不能公开上传。

## 下载与安装

### 方案一：完整安装（推荐）

从 [Releases](https://github.com/maxzrb/mpv-vanta-edition/releases) 下载：

1. 下载 `01-mpv-base-vX.Y.Z.7z`
2. 下载 `03-mpv-extras-vX.Y.Z.7z.001` 和 `.002`（两个分卷都需要）
3. 解压 Base 包到你想要的位置
4. 解压 Extras 包到**同一目录**（用 7-Zip 打开 `.001` 即可）
5. 运行 `mpv.exe`

```
最终目录结构：
mpv-vanta-edition/
├── mpv.exe
├── portable_config/    ← Config 包的完整内容
│   ├── mpv.conf
│   ├── scripts/        ← 所有 Lua 脚本
│   ├── shaders/        ← Extras 包的着色器
│   └── vs/             ← Extras 包的 VapourSynth 脚本
├── vs-plugins/         ← Extras 包的 VS 插件
├── lua51.dll, vulkan-1.dll, ...
└── ...
```

### 方案二：只用配置

已有 mpv 播放器，只想用这套配置：

1. 下载 `02-mpv-config-vX.Y.Z.7z`
2. 解压到 mpv 的配置目录（覆盖 `portable_config/`）

### 方案三：手动组装

1. 下载任意标准 mpv Windows 构建
2. 下载 `02-mpv-config-vX.Y.Z.7z`，解压到 mpv 目录
3. 如需完整功能，再下载 `03-mpv-extras-vX.Y.Z.7z.00x` 解压

## 更新方式

- **仅更新配置**：下载最新 Config 包，解压覆盖即可
- **更新核心**：下载最新 Base 包
- **更新着色器/插件**：下载最新 Extras 包

日常小改动通常只需要更新 Config 包。

## 打包脚本

所有脚本都位于项目根目录，建议在 PowerShell 中从该目录运行。

### 一次构建五个公开包

```powershell
.\build-all-packages.ps1 -Version '1.2.0'
```

输出 01 Base、02 Extras 分卷、03 FW、04 LSFG 和 05 Config 公开包。

### 同时构建个人私用全量包

```powershell
.\build-all-packages.ps1 -Version '1.2.0' -IncludePrivate
```

构建 04 或全量包前，需要项目根目录已经存在本地提供的：

```text
Lossless Scaling\Lossless.dll
```

04 公开包会把该 DLL 内置到 `Lossless Scaling\` 目录，解压后即可使用 LSFG 补帧。

### 分别构建

```powershell
.\build-release.ps1 -Version '1.2.0'
.\build-lsfg-public.ps1 -Version '1.2.0'
.\build-full-private.ps1 -Version '1.2.0'
```

- `build-release.ps1`：构建 01 Base + 02 Extras。
- `build-fasterwhisper-public.ps1`：构建 03，AI 语音识别运行时。
- `build-lsfg-public.ps1`：构建 04，含控制脚本以保证联动可用性。
- `build-config-public.ps1`：构建 05，个人设置最终覆盖层（不含启动 Logo 素材，归 01）。
- `build-full-private.ps1`：完整合并 01～05，并加入完整 Lossless Scaling 目录备份。
- 所有脚本可用 `-OutputDir '目录名'` 修改输出目录。

## 配置特性

### 音频
- WASAPI 输出，支持多声道
- 音速调整与音高校正

### 字幕
- 多语言、多格式字幕渲染
- AI 字幕生成（Faster-Whisper，需自行下载模型）
- 在线字幕下载（Assrt.net）

### 界面
- 基于 [uosc](https://github.com/tomasklaen/uosc) 的现代化 OSC
- 弹幕系统（[uosc_danmaku](https://github.com/Loukyuu1120/uosc_danmaku)）
- 汉化统计信息 OSD

### 视频处理
- 500+ GLSL 着色器（Anime4K、FSRCNNX、ESRGAN 等 35 类）
- VapourSynth 补帧/超分/降噪（RIFE、SVP、DRBA、ArtCNN）
- HDR/SDR 自适应切换

### 快捷键
- `h/j/k/l` — 基本播放控制
- `i` — 临时显示统计信息，`I` — 常驻显示
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
| `shaders/` | GLSL 着色器（Extras 包） |
| `vs/` | VapourSynth 脚本（Extras 包） |

## 项目来源

```
gaoxing64/MPV-lazy-full (v2.0.0)
    └── hooke007/MPV_lazy (原始 MPV-lazy)
    └── dyphire/mpv-config (配置参考)
    └── hooke007/mpv_PlayKit (着色器)
    └── LumeCraft-Labs/K7sfunc (VapourSynth 脚本)
```

## License

本项目各组件的许可证见各自源文件。原始项目按原作者 dyphire 的许可证约定执行。
