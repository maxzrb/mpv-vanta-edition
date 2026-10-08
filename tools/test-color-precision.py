"""维护阶段验证源矩阵、范围、高位深保留及真实滤镜，播放器不调用。"""
import hashlib
import json
from pathlib import Path
import runpy
import vapoursynth as vs
import k7sfunc as k7f
from k7sfunc._internal import _mpv_color_spec

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/validation'
core = vs.core


def samples(frame):
    return [float(frame[i][20,20]) for i in range(3)]


def image_hash(frame):
    return hashlib.sha256(b''.join(bytes(frame[i]) for i in range(3))).hexdigest()


def rgb_reference(values,bits,matrix,full):
    # 按标准矩阵系数和整数合法范围独立计算，不调用 zimg 或 K7 参考转换。
    scale = 2 ** (bits-8)
    max_code = 2 ** bits-1
    y = values[0]/max_code if full else (values[0]-16*scale)/(219*scale)
    u = (values[1]-128*scale)/(max_code if full else 224*scale)
    v = (values[2]-128*scale)/(max_code if full else 224*scale)
    kr,kb = {1:(.2126,.0722),5:(.299,.114),6:(.299,.114),9:(.2627,.0593)}[matrix]
    kg = 1-kr-kb
    return [y+(2-2*kr)*v,y-kb*(2-2*kb)/kg*u-kr*(2-2*kr)/kg*v,y+(2-2*kb)*u]


def source(bits,matrix,full):
    fmt = core.query_video_format(vs.YUV,vs.INTEGER,bits,0,0)
    scale = 2 ** (bits-8)
    values = [128*scale,116*scale,142*scale]
    clip = core.std.BlankClip(width=64,height=64,format=fmt.id,length=4,fpsnum=24,color=values)
    # 模拟 mpv 桥接：只有旧 _ColorSpace，没有现代 _Matrix。
    return core.std.SetFrameProps(clip,_ColorSpace=matrix,_ColorRange=0 if full else 1), values


def main():
    rows=[]
    for fmt in [vs.YUV420P8,vs.YUV420P10,vs.YUV420P12,vs.YUV420P16,vs.YUV422P16,vs.YUV444P16]:
        clip=core.std.BlankClip(width=64,height=64,format=fmt,length=4)
        clip=core.std.SetFrameProps(clip,_ColorSpace=9,_ColorRange=1)
        out=k7f.FMT_CTRL(clip,h_max=0,fmt_pix=0)
        assert out.format.id==clip.format.id
        assert image_hash(out.get_frame(0))==image_hash(clip.get_frame(0))
        locked=k7f.FMT_CTRL(clip,h_max=0,fmt_pix=1)
        assert locked.format.id==vs.YUV420P8
        locked.get_frame(0)
        rows.append(dict(test='格式保留与手动锁定',input=clip.format.name,output=out.format.name,passed=True))
    for bits in [8,10,16]:
        for matrix in [1,5,6,9]:
            for full in [False,True]:
                clip,values=source(bits,matrix,full)
                actual_matrix,color_range=_mpv_color_spec(clip)
                assert actual_matrix==matrix and color_range==(0 if full else 1)
                rgb=core.resize.Bilinear(clip,format=vs.RGBS,matrix_in=actual_matrix).get_frame(0)
                error=max(abs(a-b) for a,b in zip(samples(rgb),rgb_reference(values,bits,matrix,full)))
                assert error<2e-6,(bits,matrix,full,error)
                out=k7f.CCD_STD(clip,nr_lv=30.0)
                frame=out.get_frame(0)
                code_error=max(abs(a-b) for a,b in zip(samples(frame),values))
                assert code_error<=1 and frame.props['_Matrix']==matrix
                assert frame.props['_ColorRange']==(0 if full else 1)
                rows.append(dict(test='标准矩阵与真实CCD色块',bits=bits,matrix=matrix,full=full,
                                 maximum_rgb_error=error,maximum_code_error=code_error,passed=True))
    for matrix,full,bits in [(1,False,8),(6,True,10),(9,False,10),(9,True,16)]:
        clip,values=source(bits,matrix,full)
        out=k7f.RIFE_DML(clip,model=426,turbo=True,fps_in=24,fps_num=2,fps_den=1,sc_mode=1,gpu=0,gpu_t=2)
        # 静态色块的真实模型中间帧；不以此替代动态片源的观感评估。
        frame=out.get_frame(1)
        error=max(abs(a-b) for a,b in zip(samples(frame),values))
        assert error<=2 and frame.props['_Matrix']==matrix and out.format.id==clip.format.id
        assert frame.props['_ColorRange']==(0 if full else 1)
        rows.append(dict(test='真实RIFE4.26-DML静态插值帧',matrix=matrix,full=full,bits=bits,
                         maximum_code_error=error,output=out.format.name,passed=True))
    clip,_=source(10,9,False)
    modern=core.std.SetFrameProps(clip,_Matrix=1)
    assert _mpv_color_spec(modern)[0]==1,'现代矩阵属性优先于旧属性'
    # 后端兼容格式允许降低精度，SVP 主图像格式策略保持原样。
    main_clip,analysis=k7f.FMT2YUV_SP(source(16,9,False)[0])
    assert main_clip.format.id==vs.YUV420P10 and analysis.format.id==vs.YUV420P8
    rows.append(dict(test='SVP兼容格式保持',main=main_clip.format.name,analysis=analysis.format.name,passed=True))
    repair=runpy.run_path(str(ROOT/'portable_config/vs/mpv_frame_props.py'))['repair_duration']
    for numerator,denominator in [(1,24),(1,30),(2,48),(0,1),(-1,1),(1,0),(None,None)]:
        clip,_=source(16,9,False)
        if numerator is not None:
            clip=core.std.SetFrameProps(clip,_DurationNum=numerator,_DurationDen=denominator)
        else:
            clip=core.std.RemoveFrameProps(clip,props=['_DurationNum','_DurationDen'])
        frame=repair(clip,24).get_frame(0)
        expected=(numerator,denominator) if numerator is not None and numerator>=0 and denominator>0 else (1,24)
        assert (frame.props['_DurationNum'],frame.props['_DurationDen'])==expected
        assert image_hash(frame)==image_hash(clip.get_frame(0))
        assert frame.props['_ColorSpace']==9 and frame.props['_ColorRange']==1
        rows.append(dict(test='帧时长回退与VFR／EOF属性保留',input_duration=[numerator,denominator],
                         output_duration=list(expected),passed=True))
    clip,_=source(10,9,False)
    assert repair(clip,None).get_frame(0).props['_DurationDen']==24
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'color-precision-fixes-results.json').write_text(json.dumps(
        dict(scope='源转换层与静态真实滤镜；不是面板测量或全部模型观感',trials=rows),
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS',len(rows),'格式／标准矩阵／真实CCD／RIFE-DML／兼容格式用例')


if __name__=='__main__':
    main()
