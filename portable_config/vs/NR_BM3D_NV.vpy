### https://github.com/hooke007/mpv_PlayKit/wiki/3_K7sfunc
### BM3D降噪，N卡专用

from pathlib import Path
import sys
import vapoursynth as vs
from vapoursynth import core
import k7sfunc as k7f

core.num_threads = k7f.vs_t_dft
# 从当前便携脚本目录导入帧属性修复，不启动检查或子进程。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mpv_frame_props import repair_duration

clip = repair_duration(video_in, container_fps)

############
# 用户选项 #
############

Nr_Lv = [5,0,0]
Bs_Ref = 8
Bs_Out = 7
Gpu = 0
## 整数组，每平面的降噪强度
## <1|2|3|4|5|6|7|8> block_step
## <1|2|3|4|5|6|7|8> 小于等于 Bs_Ref
## 显卡序号，0为一号

clip = k7f.BM3D_NV(clip, nr_lv=Nr_Lv, bs_ref=Bs_Ref, bs_out=Bs_Out, gpu=Gpu)

clip.set_output()
