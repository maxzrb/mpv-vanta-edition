"""HDR 峰值分析和长 GOP 跳转的独立候选比较；没有稳定收益时保留现状。"""
import json,time,runpy,re,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tmp/modernization/optimization-20261005'
helper=runpy.run_path(str(ROOT/'tools/validate-modernization.py'));Player=helper['Player'];cpu=helper['process_cpu_seconds']
def main():
    rows=[]
    for trial in range(1,4):
        for name,value in [('peak-auto','auto'),('peak-off','no')]:
            p=Player(['--no-config','--vo=gpu-next','--gpu-api=d3d11','--hwdec=auto-safe','--ao=null',
                '--geometry=1920x1080','--loop-file=inf','--target-trc=srgb','--target-prim=bt.709',
                '--hdr-contrast-recovery=0','--hdr-compute-peak='+value,
                str(ROOT/'tmp/modernization/validation/hdr10.mkv')],f'{name}-{trial}')
            try:
                p.wait_video();time.sleep(3)
                wall=time.monotonic();c0=cpu(p.process);last=p.get('time-pos');duration=p.get('duration');advance=0
                keys=['frame-drop-count','decoder-frame-drop-count'];before={k:p.get(k) or 0 for k in keys}
                while time.monotonic()-wall<20:
                    time.sleep(.5);position=p.get('time-pos');delta=position-last
                    if delta<-.5:delta+=duration
                    advance+=max(0,delta);last=position
                elapsed=time.monotonic()-wall
                row={'case':name,'trial':trial,'seconds':elapsed,'clock_ratio':advance/elapsed,
                    'cpu_core_percent':100*(cpu(p.process)-c0)/elapsed,
                    'counters':{k:(p.get(k) or 0)-before[k] for k in keys},'passes':p.get('vo-passes')}
                rows.append(row);print(name,trial,round(row['cpu_core_percent'],2),row['counters'],flush=True)
            finally:p.close()
    for trial in range(1,4):
        for drop in ['no','yes']:
            p=Player(['--no-config','--vo=gpu-next','--gpu-api=d3d11','--hwdec=auto-safe','--ao=null',
                '--pause=yes','--geometry=640x360','--hr-seek-framedrop='+drop,str(OUT/'long-gop.mkv')],f'seek-{drop}-{trial}')
            try:
                p.wait_video();timings=[]
                for position in [2.3,8.4,14.6,3.2,21.7]:
                    start=time.monotonic();result=p.command('seek',position,'absolute+exact')
                    assert result['error']=='success'
                    limit=time.monotonic()+8
                    while time.monotonic()<limit:
                        media=p.get('time-pos')
                        if media is not None and abs(media-position)<.1 and p.get('seeking') is False:break
                        time.sleep(.01)
                    assert abs(p.get('time-pos')-position)<.1
                    timings.append(time.monotonic()-start)
                rows.append({'case':'seek-'+drop,'trial':trial,'seek_seconds':timings})
                print('seek',drop,trial,round(statistics.median(timings),3),flush=True)
            finally:p.close()
    (OUT/'peak-seek-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS 独立峰值检测与长 GOP 跳转比较；不自动推广关闭峰值分析')
if __name__=='__main__':main()
