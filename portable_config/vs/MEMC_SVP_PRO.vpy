### https://github.com/hooke007/mpv_PlayKit/wiki/3_K7sfunc
### 基于黑米奇方案的修改简化版

import vapoursynth as vs
from vapoursynth import core
import k7sfunc as k7f

clip = video_in

############
# 用户选项 #
############

H_Pre = 0
Fps_Num = 60000
Fps_Den = 1001
Abs = True
Nvof = False
Gpu = 0
Lk_Fmt = False
## 整数，0 保留原分辨率；非零为显式性能模式处理高度
## 整数， Fps_Num/Fps_Den 的计算结果即最终帧率或倍率
## 整数
## <True|False> 输出帧率(True)还是倍率(False)
## <True|False> 是否启用Optical Flow（nvidia专用）
## <0|11|12|21> 使用的显卡序号，0为排序一号
## <True|False> 是否锁定像素格式为yuv420p8

# 使用实际输入节点帧率；容器平均值只作缺失时的回退。
Source_Fps = float(clip.fps) if clip.fps_num > 0 and clip.fps_den > 0 else float(container_fps)
Target_Fps = Fps_Num / Fps_Den
if not (Abs and Source_Fps >= Target_Fps * 0.999):
    clip = k7f.FMT_CTRL(clip, h_max=H_Pre, fmt_pix=1 if Lk_Fmt else 0)
    clip = k7f.SVP_PRO(clip, fps_in=Source_Fps, fps_num=Fps_Num, fps_den=Fps_Den, abs=Abs, nvof=Nvof, gpu=Gpu)
# 目标已满足则直接输出输入帧，不降低源帧率、分辨率或位深。
clip.set_output()
