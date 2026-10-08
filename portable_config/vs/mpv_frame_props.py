"""仅在实际 VS 处理时补齐缺失帧时长，保留有效可变帧率信息。"""
from fractions import Fraction
import vapoursynth as vs


def repair_duration(clip,source_fps):
    try:
        rate=Fraction(str(source_fps)).limit_denominator(100000)
    except (ValueError,TypeError,ZeroDivisionError):
        rate=Fraction(clip.fps_num,clip.fps_den) if clip.fps_num>0 and clip.fps_den>0 else Fraction(0)
    if rate<=0:
        return clip
    duration=1/rate

    def repair(n,f):
        props=f.props
        num=props.get('_DurationNum')
        den=props.get('_DurationDen')
        # 桥接的 0/1 EOF 占位帧须保持；正常正时长不改，包含 VFR。
        if isinstance(num,int) and isinstance(den,int) and num>=0 and den>0:
            return f
        copy=f.copy()
        copy.props['_DurationNum']=duration.numerator
        copy.props['_DurationDen']=duration.denominator
        return copy

    return vs.core.std.ModifyFrame(clip,clips=clip,selector=repair)
