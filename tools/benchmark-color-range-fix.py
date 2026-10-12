"""真实 mpv 的 4K 全范围校正 ABBA 代价；固定线程，不附加 GPU 读回器。"""
import ctypes,json,os,runpy,subprocess,time
from ctypes import wintypes
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/color-range-fix-20261011'
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'))
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
kernel.GetProcessTimes.restype=wintypes.BOOL


def cpu(p):
    times=[wintypes.FILETIME() for _ in range(4)]
    assert kernel.GetProcessTimes(int(p.process._handle),*[ctypes.byref(v) for v in times])
    return sum((v.dwHighDateTime<<32)|v.dwLowDateTime for v in times[2:])/1e7


def fixture():
    target=OUT/'full4k-12.mkv'
    if target.exists():return target
    raw=ROOT/'tmp/modernization/pipeline-validation-20261011/range-time-4k-12.yuv'
    print('生成 4K 12bit 全范围 FFV1 夹具，编码线程固定1',flush=True)
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y','-stream_loop','-1',
        '-f','rawvideo','-pixel_format','yuv444p12le','-video_size','3840x2160','-framerate','24',
        '-color_range','pc','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1',
        '-i',str(raw),'-frames:v','144','-c:v','ffv1','-level','3','-slices','16','-slicecrc','0','-threads','1',
        '-color_range','pc','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1',str(target)],check=True,timeout=180)
    return target


def trial(media,backend,enabled,number):
    excludes=list(t['EXCLUDED'])
    if enabled:excludes.remove('color-range-fix.lua')
    cfg=t['output']['create_config']('range-time',exclude_scripts=excludes)
    p=t['pipeline']['api']['Player'](['--config-dir='+str(cfg),'--gpu-api='+backend,'--hwdec=no',
        '--vd-lavc-threads=16','--audio=no','--sid=no','--osd-level=0','--geometry=1024x576',
        '--autofit=1024x576','--autofit-smaller=1024x576',str(media)],f'range-time-{backend}-{number}')
    try:
        p.wait_video()
        p.command('set_property','user-data/display-info',{'uid':'pipeline-software','hdr-status':'off','hdr-supported':False,'max-luminance':80})
        p.command('set_property','user-data/display-color',{'mode':'wcg','identity':'pipeline-software'})
        t['output']['wait'](p,lambda s:s['mode']=='sdr-acm')
        if enabled:
            deadline=time.monotonic()+20
            while (p.get('user-data/color-range-fix') or {}).get('state')!='已校正':
                assert time.monotonic()<deadline;time.sleep(.05)
        time.sleep(1.5)
        before={k:p.get(k) or 0 for k in ('frame-drop-count','decoder-frame-drop-count')}
        pos=p.get('time-pos');started=time.monotonic();c=cpu(p)
        time.sleep(2)
        wall=time.monotonic()-started;used=cpu(p)-c;elapsed=p.get('time-pos')-pos
        dropped={k:(p.get(k) or 0)-v for k,v in before.items()}
        assert elapsed>0 and p.get('vd-lavc-threads')==16
        return dict(backend=backend,enabled=enabled,round=number,window_seconds=wall,media_seconds=elapsed,
                    media_clock_ratio=elapsed/wall,cpu_seconds=used,cpu_ms_per_media_frame=used/(elapsed*24)*1000,
                    drop_counters=dropped,decoder_threads=16,source=p.get('video-params'),
                    output=p.get('video-out-params'),filters=p.get('vf'))
    finally:p.close()


def main():
    media=fixture();rows=[]
    for backend in ('d3d11','vulkan'):
        for n,enabled in enumerate((False,True,True,False)):
            row=trial(media,backend,enabled,n);rows.append(row)
            print(backend,'校正' if enabled else '基线',row['cpu_ms_per_media_frame'],'CPU ms/frame',row['drop_counters'],flush=True)
    (OUT/'playback-timings.json').write_text(json.dumps(dict(scope='4K24 FFV1全范围12bit；1024×576；固定16解码线程、校正滤镜1线程；1.5秒预热＋2秒窗口、ABBA；非AV1零丢帧测试',
        trials=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
