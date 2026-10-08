### https://github.com/hooke007/mpv_PlayKit/wiki/3_K7sfunc
### RIFE (v4+) 补帧，性能要求较高，N卡专用

from fractions import Fraction
from pathlib import Path
import sys
import vapoursynth as vs
from vapoursynth import core
import k7sfunc as k7f

core.num_threads = k7f.vs_t_dft
clip = video_in

############
# 用户选项 #
############

H_Pre = 0
Model = 4262
Fps_Num = 2
Fps_Den = 1
Sc_Mode = 1
Gpu = 0
Gpu_T = 2
Ws_Size = 0
Lk_Fmt = False
## 整数，0 保留原分辨率；非零为显式性能模式处理高度
## <46|4251|426|4262> 使用的模型
## 整数，Fps_Num/Fps_Den 的值即帧率倍数
## 整数
## <0|1|2> 场景切换检测的模式，0为禁用
## 使用的显卡序号，0为排序一号
## <1|2|3> 显卡线程数
## 整数，手动约束引擎构建阶段的显存（MiB），最小值为128，设为低于此数的值即最大化利用
## <True|False> 锁定像素格式为yuv420p8

clip = k7f.FMT_CTRL(clip, h_max=H_Pre, fmt_pix=1 if Lk_Fmt else 0)
clip = k7f.RIFE_NV(clip, model=Model, int8_qnt=False, turbo=2, fps_in=container_fps, fps_num=Fps_Num, fps_den=Fps_Den, sc_mode=Sc_Mode, gpu=Gpu, gpu_t=Gpu_T, ws_size=Ws_Size)

# 只回退缺失时长，保留有效逐帧时长与原有补帧倍率。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mpv_frame_props import repair_duration
# mpv 流式节点可使用 0/0 帧率；此时按该入口原有容器帧率倍率计算。
Output_Fps = (Fraction(clip.fps_num, clip.fps_den) if clip.fps_num > 0 and clip.fps_den > 0
    else Fraction(str(container_fps)).limit_denominator(100000) * Fraction(Fps_Num, Fps_Den))
clip = repair_duration(clip, Output_Fps)

clip.set_output()
