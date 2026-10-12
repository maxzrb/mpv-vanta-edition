"""默认 perceptual 色域映射与独立连续公式的误差及插值改进。"""
import json,math,os,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/color-accuracy-20261011'
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'))
t['EXCLUDED'].remove('color-range-fix.lua')
ref=runpy.run_path(str(ROOT/'tools/color-map-reference.py'))


def main():
    fixture=t['fixtures']['fixture']
    fixture.__globals__['COLORS']=[(.95,.03,.03),(.03,.95,.03),(.03,.03,.95),(.03,.95,.95),
        (.95,.03,.95),(.95,.95,.03),(.7,.4,.15),(.15,.4,.7),
        (.02,.02,.02),(.1,.1,.1),(.5,.5,.5),(.98,.98,.98),
        (.6,.45,.48),(.45,.6,.5),(.45,.5,.65),(.3,.3,.3)]
    fixture.__globals__['target_rgb']=lambda rgb,wide:rgb
    media,encoded=fixture('gamut-continuous',16,9,True,True)
    rows_out=[]
    for backend in ('d3d11','vulkan'):
        # 固定历史基线尺寸，避免生产默认加密后改变同名对照的含义。
        for variant,options in (('default',['--libplacebo-opts=lut3d_size_I=48,lut3d_size_C=32,lut3d_size_h=256']),('cubic',['--libplacebo-opts=lut3d_tricubic=yes,lut3d_size_I=48,lut3d_size_C=32,lut3d_size_h=256']),
                ('cubic-dense',['--libplacebo-opts=lut3d_tricubic=yes,lut3d_size_I=64,lut3d_size_C=48,lut3d_size_h=256']),
                ('linear-dense',['--libplacebo-opts=lut3d_size_I=96,lut3d_size_C=64,lut3d_size_h=256'])):
            rows,status=t['capture'](media,'gamut-'+variant,backend,mode='sdr',extra_args=options,
                post_configure=lambda p:p.command('set_property','target-contrast','inf'))
            final=rows[-1];assert final[0]['format']==24
            # 当前核心 SDR 白采用 80nit；同时保存实际目标，不能拿显示器名字推断。
            target=status['actual_target'];peak=target.get('max-luma') or 80
            reference=[]
            for rgb in encoded:
                linear=[t['output']['sdr_linear'](v)*80/10000 for v in rgb]
                mapped=ref['perceptual'](linear,0,peak/10000)
                reference.append([t['fixtures']['encode_srgb'](max(v,0)*10000/peak) for v in mapped])
            means=[]
            for i in range(16):
                samples=[t['pixel'](final,x,y) for y in range(i//4*64+8,i//4*64+56)
                         for x in range(i%4*64+8,i%4*64+56)]
                means.append([sum(v[c] for v in samples)/len(samples) for c in range(3)])
            errors=[abs(a-b) for rgb,r in zip(means,reference) for a,b in zip(rgb,r)]
            result=dict(backend=backend,variant=variant,max_encoded_error=max(errors),
                rms_encoded_error=math.sqrt(sum(e*e for e in errors)/len(errors)),actual=means,reference=reference,target=target,
                research_only=True,reference_calibration_complete=False,candidate_default_enabled=False)
            rows_out.append(result);print(backend,variant,result['max_encoded_error'],result['rms_encoded_error'],flush=True)
            (OUT/'gamut-continuous-results.json').write_text(json.dumps(rows_out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (OUT/'gamut-continuous-results.json').write_text(json.dumps(rows_out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
