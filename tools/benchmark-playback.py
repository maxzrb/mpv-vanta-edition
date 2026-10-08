"""同素材、同窗口与显示条件的三轮实际播放对比；每轮预热后采样至少 20 秒。"""
import json, time, runpy, re, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/optimization-20261005'
helper=runpy.run_path(str(ROOT/'tools/validate-modernization.py'))
Player, cpu_seconds=helper['Player'],helper['process_cpu_seconds']
def run(verify_direct=False):
    rows=[]
    cases=[('direct','d3d11va','Performance-Balanced',[]),
           ('copy','d3d11va-copy','Performance-Balanced',[]),
           ('high-quality','d3d11va','Performance-HighQuality',[])]
    if verify_direct: cases=cases[:1]
    for trial in range(1,4):
        # 交替次序，减小温度及缓存对单一候选的偏差。
        for name,hwdec,profile,extra in cases if trial%2 else list(reversed(cases)):
            p=Player(['--no-config','--include='+str(ROOT/'portable_config/profiles.conf'),'--profile='+profile,
                '--vo=gpu-next','--gpu-api=d3d11','--hwdec='+hwdec,'--d3d11va-zero-copy=no',
                '--ao=wasapi','--mute=yes','--geometry=1920x1080','--autofit=1920x1080',
                '--osc=no','--osd-level=0','--target-prim=bt.709','--target-trc=srgb',
                '--treat-srgb-as-power22=no','--hdr-contrast-recovery=0','--loop-file=inf',
                *extra,str(OUT/'performance-2160.mkv')],f'{"verify" if verify_direct else "performance"}-{name}-{trial}')
            try:
                p.wait_video();time.sleep(5)
                keys=['frame-drop-count','decoder-frame-drop-count','mistimed-frame-count','vo-delayed-frame-count']
                before={k:p.get(k) for k in keys}; wall=time.monotonic(); c0=cpu_seconds(p.process)
                start=p.get('time-pos');last=start;advance=0;samples=[];duration=p.get('duration')
                while time.monotonic()-wall<20:
                    time.sleep(.5);now=p.get('time-pos')
                    if now is not None and last is not None:
                        delta=now-last
                        if delta<-.5:delta+=duration
                        advance+=max(0,delta)
                    last=now
                    sample={'wall':time.monotonic()-wall,'media':now}
                    if verify_direct: sample['drops']=p.get('frame-drop-count') or 0
                    samples.append(sample)
                elapsed=time.monotonic()-wall
                row={'case':name,'trial':trial,'hwdec':hwdec,'actual_hwdec':p.get('hwdec-current'),
                     'profile':profile,'sample_seconds':elapsed,'media_advance':advance,
                     'clock_ratio':advance/elapsed,'cpu_core_percent':100*(cpu_seconds(p.process)-c0)/elapsed,
                     'counters':{k:(p.get(k) or 0)-(before[k] or 0) for k in keys},
                     'vo_passes':p.get('vo-passes'),'output':p.get('video-target-params'),
                     'video_output':p.get('video-out-params'),'audio':p.get('audio-out-params'),
                     'samples':samples}
                rows.append(row); print(json.dumps({k:row[k] for k in ['case','trial','clock_ratio','cpu_core_percent','counters']},ensure_ascii=False),flush=True)
            finally:p.close()
            log=p.log.read_text(encoding='utf-8',errors='replace')
            rows[-1]['errors']=[line for line in log.splitlines() if '[e]' in line or '[f]' in line]
            rows[-1]['audio_underruns']=[line for line in log.splitlines() if re.search(r'underrun|underflow',line,re.I)]
            if verify_direct:
                row=rows[-1]
                assert .98<row['clock_ratio']<1.02 and not row['errors'] and not row['audio_underruns'],row
                counts=[before['frame-drop-count'] or 0]+[s['drops'] for s in row['samples']]
                streak=0
                for a,b in zip(counts,counts[1:]):
                    streak=streak+1 if b>a else 0
                    assert streak<4,'连续两秒仍增加掉帧，不推广默认'
            filename='direct-stability-results.json' if verify_direct else 'performance-results.json'
            (OUT/filename).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DONE',len(rows),flush=True)
if __name__=='__main__':
    import sys
    run('--verify-direct' in sys.argv)
