"""诊断候选：单线程范围规范化的整数可逆性与数值精度，不写生产配置。"""
import json,os,runpy,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']


def main():
    os.environ['MPV_PIPELINE_RANGE_NORMALIZE']='1';results=[]
    try:
        for bits in (10,12):
            for matrix in (6,1,9):
                name=f'range-candidate-{bits}-{matrix}'
                media,encoded=t['fixtures']['fixture'](name,bits,matrix,True,matrix==9)
                raw=(OUT/(name+'.yuv')).read_bytes()
                expected=[[t['output']['sdr_linear'](v) for v in rgb] for rgb in encoded]
                for backend in ('d3d11','vulkan'):
                    rows,status=t['capture'](media,name,backend)
                    source=[r for r in rows if r[0]['phase']=='input' and r[0]['format']==56]
                    assert len(source)==3
                    for plane,row in enumerate(source):
                        for i in range(16):
                            x=i%4*64+32;y=i//4*64+32
                            original=struct.unpack_from('<H',raw,(plane*65536+y*256+x)*2)[0]
                            mapped=t['pixel'](row,x,y)
                            recovered=round((mapped-4096)/56064*(2**bits-1)) if plane==0 else round((mapped-32768)/57344*(2**bits-1)+2**(bits-1))
                            assert recovered==original,(bits,matrix,backend,plane,original,mapped,recovered)
                    final=rows[-1];actual=[t['pixel'](final,i%4*64+32,i//4*64+32) for i in range(16)]
                    error=max(abs(a-b) for rgb,ref in zip(actual,expected) for a,b in zip(rgb,ref));assert error<.00125,error
                    filtered=status['validation_filtered']
                    assert filtered['pixelformat']=='yuv444p16' and filtered['colorlevels']=='limited',filtered
                    assert filtered['w']==256 and filtered['h']==256 and filtered['gamma']=='srgb'
                    results.append(dict(bits=bits,matrix=matrix,backend=backend,integer_reconstruction_exact=True,
                                        maximum_linear_error=error,post_filter=filtered,production_enabled=False))
                    print('PASS',bits,matrix,backend,error,flush=True)
    finally:os.environ.pop('MPV_PIPELINE_RANGE_NORMALIZE',None)
    (OUT/'range-candidate-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
