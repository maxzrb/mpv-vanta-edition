"""色域表密度的独立无插桩ABBA：生成/缓存、GPU分段、CPU、呈现丢帧。"""
import argparse, ctypes, json, os, re, runpy, statistics, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/gamut-general-20261012';OUT.mkdir(parents=True,exist_ok=True)
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));t['EXCLUDED'].remove('color-range-fix.lua')
api=t['pipeline']['api'];Player=api['Player']
process_cpu_seconds=runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['process_cpu_seconds']
CONFIGS={}


def memory(process):
    class Counters(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(key,ctypes.c_size_t) for key in
            ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
             'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
    value=Counters();value.cb=ctypes.sizeof(value)
    get=ctypes.WinDLL('psapi',use_last_error=True).GetProcessMemoryInfo
    get.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong];get.restype=ctypes.c_int
    assert get(int(process._handle),ctypes.byref(value),value.cb),ctypes.get_last_error()
    return {key:getattr(value,key) for key in ('WorkingSetSize','PeakWorkingSetSize','PrivateUsage')}


def prepare_4k():
    target=OUT/'gamut-hevc4k10.mkv'
    if target.exists():return target
    source=OUT/'grid-9-iec61966-2-1.mkv';assert source.exists()
    print('生成4K HEVC10固定图案，编码单线程',flush=True)
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y','-stream_loop','-1',
        '-threads','1','-i',str(source),'-vf','scale=3840:2160:flags=neighbor:in_range=pc:out_range=tv,format=yuv420p10le',
        '-frames:v','720','-c:v','libx265','-preset','ultrafast','-crf','16','-threads','1',
        '-x265-params','pools=none:frame-threads=1:wpp=0:log-level=error',
        '-color_range','tv','-colorspace','bt2020nc','-color_primaries','bt2020','-color_trc','iec61966-2-1',str(target)],
        check=True,timeout=180)
    return target


def prepare_grid():
    source=OUT/'grid-9-iec61966-2-1.mkv';target=OUT/'gamut-grid-long.mkv'
    if not target.exists():
        subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y','-stream_loop','-1',
            '-i',str(source),'-t','30','-map','0:v:0','-c','copy',str(target)],check=True,timeout=30)
    return target


def real_media(case):
    needles={'real-hlg':'Sayuri','real-vvc':'libvvenc','real-hevc60':'VID_20260928_093322'}
    matches=[v for v in Path(r'C:\Users\maxzr\Downloads').iterdir() if v.is_file() and needles[case] in v.name]
    assert len(matches)==1,matches
    if case!='real-hevc60':return matches[0]
    # 原片20秒；流拷贝延长测试副本，保留编码整数值，避免测量窗口跨播放器EOF。
    target=OUT/'independent-hevc60-long.mkv'
    if not target.exists():
        subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y','-stream_loop','2',
            '-i',str(matches[0]),'-t','60','-map','0:v:0','-c','copy',str(target)],check=True,timeout=45)
    return target


def config(backend,variant,cache_tag):
    key=(backend,variant,cache_tag)
    if key not in CONFIGS:CONFIGS[key]=t['output']['create_config']('density-'+ '-'.join(key),exclude_scripts=t['EXCLUDED'])
    return CONFIGS[key]


def trial(media,backend,variant,number,hardware=False,cache_tag='shared',window_seconds=12):
    cfg=config(backend,variant,cache_tag)
    args=['--config-dir='+str(cfg),'--gpu-api='+backend,'--hwdec='+('d3d11va' if hardware and backend=='d3d11' else 'd3d11va-copy' if hardware else 'no'),
        '--vd-lavc-threads=16','--script-opts-append=decode-performance-enabled=no',
        '--script-opts-append=color-target-pipeline=hq',
        '--pause=yes','--audio=no','--sid=no','--osd-level=0','--osd-on-seek=no','--osd-bar=no','--osc=no',
        '--geometry=1280x720','--autofit=1280x720','--autofit-smaller=1280x720','--loop-file=inf',
        '--msg-level=vo/gpu-next=debug',str(media)]
    dims=(96,64,256) if variant=='dense' else (48,32,256)
    args+=['--libplacebo-opts=lut3d_size_I=%d,lut3d_size_C=%d,lut3d_size_h=%d'%dims]
    start=time.monotonic();p=Player(args,f'density-{media.stem}-{backend}-{variant}-{number}')
    try:
        p.wait_video()
        p.command('set_property','user-data/display-info',{'uid':'density-software','hdr-status':'off','hdr-supported':False,'max-luminance':80,'min-luminance':0})
        p.command('set_property','user-data/display-color',{'mode':'sdr','identity':'density-software'})
        t['output']['wait'](p,lambda s:s['mode']=='sdr')
        p.command('set_property','target-contrast','inf');p.command('set_property','pause',False)
        deadline=time.monotonic()+15
        while True:
            passes=p.get('vo-passes') or {};fresh=passes.get('fresh') or []
            if fresh and max(v['count'] for v in fresh)>=5 and p.get('video-target-params').get('min-luma')==0:break
            assert time.monotonic()<deadline;time.sleep(.02)
        ready=time.monotonic()-start
        settings={key:p.get(key) for key in ('video-params','video-target-params','hwdec-current','vf','target-gamut','target-trc','scale','dscale','cscale','linear-downscaling','vd-lavc-threads','libplacebo-opts','container-fps','dither-depth')}
        assert settings['vd-lavc-threads']==16
        if hardware:assert settings['hwdec-current'] in ('d3d11va','d3d11va-copy'),settings
        time.sleep(1.5)
        before={k:p.get(k) or 0 for k in ('frame-drop-count','decoder-frame-drop-count','mistimed-frame-count')}
        pass_counts={v['desc']:v['count'] for v in (p.get('vo-passes') or {}).get('fresh',[])}
        pos=p.get('time-pos');c=process_cpu_seconds(p.process);wall=time.monotonic()
        # 软件上传计时环最多256条；24fps下12秒覆盖整个环，排除启动样本。
        time.sleep(window_seconds)
        elapsed=time.monotonic()-wall;cpu=process_cpu_seconds(p.process)-c
        after=p.get('time-pos');advance=after-pos
        dropped={k:(p.get(k) or 0)-v for k,v in before.items()}
        assert advance>0 and all(v>=0 for v in dropped.values()),('窗口内发生时钟/计数重置，数据不可用',advance,dropped)
        passes=p.get('vo-passes')
        result=dict(media=str(media),backend=backend,variant=variant,round=number,hardware=hardware,cache_tag=cache_tag,
            startup_ready_seconds=ready,window_seconds=elapsed,cpu_seconds=cpu,cpu_cores_used=cpu/elapsed,
            raw_media_clock_advance=advance,window_start_media_pos=pos,window_end_media_pos=after,
            drop_counters=dropped,passes=passes,settings=settings,
            no_gpu_readback_instrumentation=True,config=str(cfg),before_pass_counts=pass_counts,
            startup_readiness_condition='黑位0目标已协商，fresh至少5次；非纯首帧耗时',memory=memory(p.process))
        result['minimum_fresh_frames_estimate']=advance*settings['container-fps']-dropped['frame-drop-count']-dropped['decoder-frame-drop-count']-2
        p.command('set_property','pause',True)
        seek_start=time.monotonic();p.command('seek',1,'absolute+exact')
        deadline=seek_start+10
        while p.get('seeking') or abs((p.get('time-pos') or 0)-1)>.05:
            assert time.monotonic()<deadline;time.sleep(.01)
        result['seek_completion_ms']=(time.monotonic()-seek_start)*1000
    finally:p.close()
    log=p.log.read_text(encoding='utf-8',errors='replace')
    result['generated_lut_ms']=[float(v) for v in re.findall(r'Spent ([0-9.]+) ms generating shader LUT',log)]
    result['cached_lut_sizes']=[int(v) for v in re.findall(r'Re-using cached LUT .* with size (\d+)',log)]
    result['cache_load_ms']=[float(v) for v in re.findall(r'cache_load_obj:.*load time\(([0-9.]+) ms\)',log)]
    result['cached_files']=[dict(name=v.name,bytes=v.stat().st_size) for v in (cfg/'cache').rglob('*') if v.is_file()]
    assert not any(message in log for message in ('Lua error:','Script evaluation failed','Failed generating tone-mapping LUT','Failed generating gamut-mapping LUT'))
    result['gpu_fresh_segments']=[]
    for v in result['passes']['fresh']:
        # count是定长采样环内数量，并非累计绘制次数；窗口媒体推进须覆盖整个环。
        samples=v['samples']
        assert result['minimum_fresh_frames_estimate']>=len(samples)+2,('窗口未覆盖全部GPU采样环',v['desc'],result['minimum_fresh_frames_estimate'])
        result['gpu_fresh_segments'].append(dict(desc=v['desc'],count=v['count'],window_sample_count=len(samples),
            median_ns=statistics.median(samples) if samples else None,mean_ns=statistics.mean(samples) if samples else None))
    print(backend,media.stem,'硬解' if hardware else '软解',variant,number,'ready',round(ready,3),'CPU',round(cpu/elapsed,3),
        'LUT ms',result['generated_lut_ms'],'cached',result['cached_lut_sizes'],'drops',dropped,flush=True)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',choices=['grid','4k-soft','4k-hard','real-hlg','real-vvc','real-hevc60'],default='grid');args=parser.parse_args()
    media=real_media(args.case) if args.case.startswith('real-') else prepare_grid() if args.case=='grid' else prepare_4k();results=[]
    for backend in ('d3d11','vulkan'):
        # 各变体第一次独立冷缓存，后续复用相同隔离目录验证真实磁盘命中。
        for number,variant in enumerate(('default','dense','dense','default')):
            results.append(trial(media,backend,variant,number,hardware=args.case=='4k-hard',cache_tag=args.case,
                window_seconds=24 if args.case=='real-hevc60' else 12))
            (OUT/f'performance-{args.case}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
