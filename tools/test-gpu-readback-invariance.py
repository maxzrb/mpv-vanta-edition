"""比较逐阶段诊断与仅交换链读回，防止探针改变被测输出。"""
import json,runpy,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'))
OUT=t['OUT']


def packed(metadata,data):
    return b''.join(data[y*metadata['stride']:y*metadata['stride']+metadata['width']*8] for y in range(metadata['height']))


def main():
    results=[]
    media,_=t['fixtures']['fixture']('probe-invariance',12,9,False,True)
    for backend in ('d3d11','vulkan'):
        rows,status=t['capture'](media,'probe-invariance',backend)
        stage=next(r for r in rows if r[0]['phase']=='present')
        cfg=t['capture'].__globals__['CONFIGS'][backend]
        api=runpy.run_path(str(ROOT/('tools/gpu-readback-vulkan.py' if backend=='vulkan' else 'tools/gpu-readback.py')))
        p,probe=api['create_player'](['--config-dir='+str(cfg),'--gpu-api='+backend,'--hwdec=no','--ao=null','--pause=yes',
            '--sid=no','--osd-level=0','--osd-bar=no','--osd-on-seek=no','--osc=no','--gpu-shader-cache=no',
            '--geometry=256x256','--autofit=256x256','--autofit-smaller=256x256','--loop-file=inf',str(media)],'probe-baseline-'+backend)
        try:
            p.wait_video()
            p.command('set_property','user-data/display-info',{'uid':'pipeline-software','hdr-status':'off','hdr-supported':False,'max-luminance':80,'min-luminance':0})
            p.command('set_property','user-data/display-color',{'mode':'wcg','identity':'pipeline-software','sdr_white_nits':80})
            p.command('set_property','pause',False)
            t['output']['wait'](p,lambda s:s['mode']=='sdr-acm')
            time.sleep(.5)
            frame=probe.read(p)
            assert frame.meta['format']==10
            assert packed(*stage)==packed(frame.meta,frame.data),'逐阶段诊断改变实际输出'
            results.append(dict(backend=backend,all_rgba_pixels_exact=True,pixels=65536))
            print('PASS',backend,'诊断前后全部 RGBA 像素逐字节相等',flush=True)
        finally:p.close();probe.close()
    (OUT/'readback-invariance.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
