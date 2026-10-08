### https://github.com/hooke007/mpv_PlayKit/wiki/3_K7sfunc
### mvtools倍帧，一般开销

import vapoursynth as vs
from vapoursynth import core
import k7sfunc as k7f

clip = video_in

############
# 用户选项 #
############

H_Pre = 0
Recal = True
Block = True
Lk_Fmt = False
## 整数，0 保留原分辨率；非零为显式性能模式处理高度
## <True|False> 是否使用二次分析
## <True|False> 是否使用Block模式
## <True|False> 锁定像素格式为yuv420p8

clip = k7f.FMT_CTRL(clip, h_max=H_Pre, fmt_pix=1 if Lk_Fmt else 0)
clip = k7f.MVT_LQ(clip, fps_in=container_fps, fps_out=container_fps*2, recal=Recal, block=Block)

clip.set_output()
