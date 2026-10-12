"""色域表加密不改变同色域经典SDR和源色域scRGB；核对整帧RGBA字节。"""
import hashlib, json, os, runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/gamut-general-20261012';OUT.mkdir(parents=True,exist_ok=True)
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));t['EXCLUDED'].remove('color-range-fix.lua')
f=runpy.run_path(str(ROOT/'tools/gamut-study-fixture.py'))


def packed(row):
    meta,data=row
    assert meta['format'] in (10,24)
    width=meta['width']*(8 if meta['format']==10 else 4)
    return b''.join(data[y*meta['stride']:y*meta['stride']+width] for y in range(meta['height']))


def main():
    fixtures={matrix:f['fixture'](matrix=matrix) for matrix in (1,9)};results=[]
    for matrix,mode in ((1,'sdr'),(1,'wcg'),(9,'wcg')):
        fixture=fixtures[matrix]
        for backend in ('d3d11','vulkan'):
            captures=[]
            for variant,options in (('baseline',['--libplacebo-opts=lut3d_size_I=48,lut3d_size_C=32,lut3d_size_h=256']),('production',[])):
                rows,status=t['capture'](fixture['path'],f'unaffected-{matrix}-{mode}-{variant}',backend,
                    size=f"{fixture['width']}x{fixture['height']}",mode=mode,extra_args=options,
                    post_configure=lambda p:p.command('set_property','target-contrast','inf'))
                assert rows[-1][0]['format']==(24 if mode=='sdr' else 10)
                captures.append(packed(rows[-1]))
            assert captures[0]==captures[1],('非色域压缩路线被改变',matrix,mode,backend)
            results.append(dict(matrix=matrix,mode=mode,backend=backend,pixels=fixture['width']*fixture['height'],
                all_rgba_bytes_exact=True,sha256=hashlib.sha256(captures[1]).hexdigest()))
            print('PASS',matrix,mode,backend,'全部RGBA字节相同',flush=True)
    (OUT/'unaffected-routes-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
