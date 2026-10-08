### https://github.com/hooke007/mpv_PlayKit/wiki/3_K7sfunc
### 降低彩噪，开销中等

from pathlib import Path
import sys
import vapoursynth as vs
from vapoursynth import core
import k7sfunc as k7f

# 从当前便携脚本目录导入帧属性修复，不启动检查或子进程。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mpv_frame_props import repair_duration

clip = repair_duration(video_in, container_fps)

############
# 用户选项 #
############

Nr_Lv = 30.0
## 浮点，彩噪阈值，越高的值降噪效果越明显（涂抹越重）

clip = k7f.CCD_STD(clip, nr_lv=Nr_Lv)

clip.set_output()
