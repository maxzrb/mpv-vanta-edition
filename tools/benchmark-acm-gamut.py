"""固定线程与画面设置，测量移除重复色域映射前后的 GPU 分段耗时。"""
import argparse,json,os,runpy,statistics,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/pipeline-validation-20261011'
SOURCES={'av1':Path(r'C:\Users\maxzr\Downloads\OP-yuv444p12-SWTest.mkv'),
         'hevc':ROOT/'tmp/modernization/validation/compat-hevc10.mkv'}


def trial(backend,source,baseline,number):
    if baseline:os.environ['MPV_PIPELINE_BASELINE']='1'
    else:os.environ.pop('MPV_PIPELINE_BASELINE',None)
    t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'))
    cfg=t['output']['create_config']('gamut-time',exclude_scripts=t['EXCLUDED'])
    if baseline:
        import shutil
        shutil.copyfile(OUT/'color-target-before-closed-loop.lua',cfg/'scripts/color-target.lua')
    threads=32 if source=='av1' else 16
    p=t['pipeline']['api']['Player'](['--config-dir='+str(cfg),'--gpu-api='+backend,'--hwdec=no','--vd-lavc-threads='+str(threads),
        '--audio=no','--sid=no','--osd-level=0','--osd-on-seek=no','--loop-file=inf',
        '--geometry=1024x576','--autofit=1024x576','--autofit-smaller=1024x576',str(SOURCES[source])],
        'gamut-time-'+source+'-'+backend+'-'+str(number))
    try:
        p.wait_video()
        p.command('set_property','user-data/display-info',{'uid':'pipeline-software','hdr-status':'off','hdr-supported':False,'max-luminance':80})
        p.command('set_property','user-data/display-color',{'mode':'wcg','identity':'pipeline-software'})
        t['output']['wait'](p,lambda s:s['mode']=='sdr-acm')
        time.sleep(5)
        passes=p.get('vo-passes')['fresh']
        mapping=next(item for item in passes if 'color encoding' in item['desc'])
        assert mapping['count']>10 and p.get('vd-lavc-threads')==threads
        return dict(backend=backend,source=source,baseline=baseline,round=number,
                    color_end_median_ns=statistics.median(mapping['samples']),passes=passes,
                    settings={key:p.get(key) for key in ('target-gamut','target-trc','scale','dscale','linear-downscaling','vd-lavc-threads')})
    finally:p.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',choices=list(SOURCES));args=parser.parse_args()
    path=OUT/'gamut-timings.json'
    results=[r for r in json.loads(path.read_text(encoding='utf-8')) if r['source']!=args.source] if args.source and path.exists() else []
    for source in ([args.source] if args.source else SOURCES):
        for backend in ('d3d11','vulkan'):
            for number,baseline in enumerate((True,False,False,True)):
                row=trial(backend,source,baseline,number);results.append(row)
                print(source,backend,'BEFORE' if baseline else 'AFTER',row['color_end_median_ns']/1e6,'ms',flush=True)
    os.environ.pop('MPV_PIPELINE_BASELINE',None)
    path.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
