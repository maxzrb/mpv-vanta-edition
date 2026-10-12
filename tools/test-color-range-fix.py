"""真实默认校正脚本的双后端像素、范围码值及未命中旁路回归。"""
import json,os,runpy,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ['MPV_PIPELINE_OUT']=str(ROOT/'tmp/modernization/color-range-fix-20261011')
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']
t['EXCLUDED'].remove('color-range-fix.lua')


def main():
    results=[]
    for bits in (10,12):
        for matrix in (6,1,9):
            name=f'fix-{bits}-{matrix}'
            media,encoded=t['fixtures']['fixture'](name,bits,matrix,True,matrix==9)
            raw=(OUT/(name+'.yuv')).read_bytes()
            expected=[[t['output']['sdr_linear'](v) for v in rgb] for rgb in encoded]
            for backend in ('d3d11','vulkan'):
                rows,status=t['capture'](media,name,backend)
                fix=status['validation_range_fix'];post=status['validation_filtered']
                assert fix and fix['active'] and fix['state']=='已校正',fix
                assert post['pixelformat']=='yuv444p16' and post['colorlevels']=='limited',post
                assert post['gamma']=='srgb' and post['primaries']==status['validation_source']['primaries']
                source=[r for r in rows if r[0]['phase']=='input' and r[0]['format']==56 and r[0]['width']==256][:3]
                assert len(source)==3
                for plane,(m,data) in enumerate(source):
                    offset=4096 if plane==0 else 32768;span=56064 if plane==0 else 57344
                    center=0 if plane==0 else 1<<(bits-1)
                    for i in range(65536):
                        code=struct.unpack_from('<H',raw,(plane*65536+i)*2)[0]
                        mapped=struct.unpack_from('<H',data,(i//256)*m['stride']+(i%256)*2)[0]
                        assert round((mapped-offset)/span*((1<<bits)-1)+center)==code
                final=rows[-1];actual=[t['pixel'](final,i%4*64+32,i//4*64+32) for i in range(16)]
                error=max(abs(a-b) for rgb,ref in zip(actual,expected) for a,b in zip(rgb,ref))
                assert error<.00125,(name,backend,error)
                gray=max(max(actual[i])-min(actual[i]) for i in (0,1,2,3,11,12,13,14,15))
                assert gray<=.0004883,gray
                results.append(dict(bits=bits,matrix=matrix,backend=backend,maximum_linear_error=error,
                                    maximum_gray_channel_spread=gray,all_source_codes_recovered=True,fix=fix,output=post))
                print('PASS',name,backend,error,gray,flush=True)
    for bits,full in ((8,True),(10,False),(12,False),(16,True)):
        name=f'bypass-{bits}-{int(full)}'
        media,_=t['fixtures']['fixture'](name,bits,1,full,False)
        rows,status=t['capture'](media,name,'d3d11')
        assert not status['validation_range_fix']['active'],status['validation_range_fix']
        expected_fmt=f'yuv444p{bits}' if bits!=8 else 'yuv444p'
        assert status['validation_filtered']['pixelformat']==expected_fmt
        results.append(dict(test='bypass',bits=bits,full=full,active=False))
        print('PASS',name,'旁路',flush=True)
    (OUT/'automatic-fix-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
