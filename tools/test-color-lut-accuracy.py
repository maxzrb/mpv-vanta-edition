"""比较默认 ICC 查找表与更高采样精度的实际输出；不改映射意图。"""
import json,math,os,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/color-accuracy-20261011'
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'))
t['EXCLUDED'].remove('color-range-fix.lua')


def main():
    icc=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline-icc.py'))['profile']()
    results=[]
    for bits,matrix in ((10,1),(12,9)):
        name=f'accuracy-icc-{bits}-{matrix}'
        media,encoded=t['fixtures']['fixture'](name,bits,matrix,True,matrix==9)
        reference=[[math.sqrt(t['output']['sdr_linear'](v)) for v in rgb] for rgb in encoded]
        for backend in ('d3d11','vulkan'):
            for size in ('auto','128x128x128'):
                rows,status=t['capture'](media,name+'-'+size,backend,mode='icc',icc_profile=icc,
                                       extra_args=['--icc-3dlut-size='+size])
                final=rows[-1];assert final[0]['format']==24
                means=[]
                for i in range(16):
                    samples=[t['pixel'](final,x,y) for y in range(i//4*64+8,i//4*64+56)
                             for x in range(i%4*64+8,i%4*64+56)]
                    means.append([sum(v[c] for v in samples)/len(samples) for c in range(3)])
                errors=[abs(a-b) for rgb,ref in zip(means,reference) for a,b in zip(rgb,ref)]
                row=dict(bits=bits,matrix=matrix,backend=backend,size=size,
                         maximum_mean_encoded_error=max(errors),rms_mean_encoded_error=math.sqrt(sum(e*e for e in errors)/len(errors)))
                results.append(row);print(row,flush=True)
    (OUT/'icc-size-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
