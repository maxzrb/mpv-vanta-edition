# 第三方组件与分发边界（v1.6.0）

各组件遵循自身原始许可，不因播放器、配置仓库或插件总体许可而改变。版本和文件哈希见 `portable_config/components.lock.json`；本地补丁配方见 `portable_config/vs/patches/`。使用随包运行库还须遵循厂商 SDK 条款。

| 组件 | 原始来源／许可 |
|---|---|
| mpv／FFmpeg／libplacebo | [mpv](https://github.com/mpv-player/mpv)、[FFmpeg](https://ffmpeg.org/)、[libplacebo](https://github.com/haasn/libplacebo)；匹配 [shinchiro 20261008](https://github.com/shinchiro/mpv-winbuild-cmake/releases/tag/20261008) 构建；各项目 GPL／LGPL 及随附依赖许可分别适用 |
| K7sfunc | [1.8.1 源码](https://github.com/LumeCraft-Labs/K7sfunc/tree/1.8.1)；src 下 GPLv3，根目录和未另行指定部分 MIT；原始 GPL 见 K7sfunc-GPL-3.0.txt；随包 Python 源码及本地补丁保留 |
| vs-mlrt／vsort | [官方仓库](https://github.com/AmusementClub/vs-mlrt)和[版本源码／资产](https://github.com/AmusementClub/vs-mlrt/releases)；插件 GPLv3，见 vs-mlrt-GPL-3.0.txt；模型及第三方推理库许可独立，不以插件 GPL 替代 |
| zsmooth | [官方源](https://github.com/adworacz/zsmooth)，MIT；原始文本见 zsmooth-LICENSE.md |
| SVPflow1 | [官方独立库与源代码](https://www.svp-team.com/wiki/Download#libs)，GPL；原始文本见 SVPflow1-GPL-2.0.txt，源码 https://www.svp-team.com/files/gpl/svpflow1-src.zip |
| SVPflow2 | 官方个人／非商业许可，Windows 需 SVP Pro；见 SVP-libraries-personal-license.txt；**公开包不包含 svpflow2_vs.dll**。菜单和脚本接口保留，用户自行安装许可组件；本机私有文件只允许进入本地私用备份 |
| TensorRT OSS／trtexec 源码 | [NVIDIA TensorRT](https://github.com/NVIDIA/TensorRT)，Apache-2.0；见 TensorRT-Apache-2.0.txt |
| TensorRT 运行库 | [NVIDIA SDK 许可](https://docs.nvidia.com/deeplearning/tensorrt/latest/reference/sla.html)单独规定 DLL／SO 的分发条件；不将 OSS Apache 扩展到闭源运行库 |
| CUDA／cuDNN 运行库 | [CUDA 许可与分发清单](https://docs.nvidia.com/cuda/eula/index.html)、[cuDNN 许可](https://docs.nvidia.com/deeplearning/cudnn/latest/reference/eula.html)；仅作为推理后端运行库，按厂商条件使用，不修改、单独出售或冒称开源 |
| ONNX Runtime／DirectML | [ONNX Runtime](https://github.com/microsoft/onnxruntime)、[DirectML](https://github.com/microsoft/DirectML)；原始源码与二进制 SDK 分发条款分别适用 |
| RIFE 模型 | [RIFE](https://github.com/hzwer/ECCV2022-RIFE)及 [vs-mlrt 模型发布](https://github.com/AmusementClub/vs-mlrt/releases/tag/models)；原始模型归对应作者，转换并不改变授权 |
| ArtCNN／AnimeJaNai 等既有模型 | 对应模型作者原始权利与使用条件独立于推理插件；保留原文件名／作者标识，不将本项目许可覆盖模型 |

Lossless Scaling、Lossless.dll 和退役 LSFG 专有程序不属于本项目公开包。项目根 backup／trash 为本地目录，不进入公开资产。此说明不授予额外权利，也不替代各厂商原始许可。
