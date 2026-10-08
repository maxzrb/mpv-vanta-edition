### https://github.com/hooke007/mpv_PlayKit/wiki/3_K7sfunc
### ArtCNN 放大，性能要求很高，N卡专用

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

H_Pre = 0
Lt_Hd = True
Model = 8
Gpu = 0
Gpu_T = 2
St_Eng = False
Ws_Size = 0
H_Max = 0
Lk_Fmt = False
## 整数，0 保留原分辨率；非零为显式性能模式处理高度
## <True|False> 是否对超过HD分辨率（720P）的源进行处理
## <6|7|8> 使用的模型
## 使用的显卡序号，0为排序一号
## <1|2|3> 使用的显卡线程数
## <True|False> 是否使用静态引擎（需要对不同分辨率的源各进行预处理）；动态引擎自适应不同分辨率（64²→DCI2K）
## <0~1024> 约束显存（MiB），静态引擎的最小值为128（动态引擎自动双倍），设为低于此数的值即为不限制
## 整数，0 不限制输出高度
## <True|False> 是否锁定像素格式为yuv420p8

clip = k7f.FMT_CTRL(clip, h_max=H_Pre, fmt_pix=1 if Lk_Fmt else 0)
clip = k7f.ARTCNN_NV(clip, lt_hd=Lt_Hd, model=Model, gpu=Gpu, gpu_t=Gpu_T, st_eng=St_Eng, ws_size=Ws_Size)
clip = k7f.FMT_CTRL(clip, h_max=H_Max, fmt_pix=1 if Lk_Fmt else 0)

clip.set_output()
