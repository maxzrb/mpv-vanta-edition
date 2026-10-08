"""8K AV1 无降质软解定位：纯解码控制与完整可见播放分开，串行测量。"""
import argparse
import json
import re
import runpy
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
helper = runpy.run_path(str(ROOT/'tools/validate-modernization.py'))
create_config = runpy.run_path(str(ROOT/'tools/isolated-config.py'))['create_config']
COUNTERS = ['frame-drop-count','decoder-frame-drop-count','mistimed-frame-count','vo-delayed-frame-count']


def errors(log):
    return [line for line in log.splitlines() if '[e]' in line or '[f]' in line]


def decode(args, threads, delay):
    name=f'av1-null-t{threads}-d{delay}'
    options=['--no-config','--vo=null','--audio=no','--sid=no','--hwdec=no','--vd=libdav1d',
        '--vd-lavc-threads='+str(threads),'--vd-lavc-o=max_frame_delay='+str(delay),
        '--untimed','--video-sync=desync','--framedrop=no','--start=10',
        '--frames='+str(args.frames),'--pause=yes',str(args.media)]
    p=helper['Player'](options,name)
    try:
        p.wait_video()
        p.command('set_property','pause',False)
        deadline=time.monotonic()+60
        while (p.get('time-pos') or 0)<10.3:
            if time.monotonic()>deadline:raise TimeoutError('纯解码控制预热超时')
            time.sleep(.1)
        before_pos=p.get('time-pos')
        cpu=helper['process_cpu_seconds'](p.process)
        started=time.monotonic()
        last_pos=before_pos
        while True:
            pos=p.get('time-pos')
            if pos is not None:last_pos=pos
            # 帧数上限触发文件结束后进入 idle，eof-reached 可能随文件卸载清零。
            if p.get('idle-active') or p.get('eof-reached'):break
            if time.monotonic()-started>120:raise TimeoutError(name)
            time.sleep(.1)
        elapsed=time.monotonic()-started
        row=dict(kind='null-decode-control',threads=threads,max_frame_delay=delay,
            seconds=elapsed,media_advance=last_pos-before_pos,
            clock_ratio=(last_pos-before_pos)/elapsed,
            cpu_cores=(helper['process_cpu_seconds'](p.process)-cpu)/elapsed,
            decoder='libdav1d',
            options=options,scope='无GPU上传／呈现／音频；不能视为实际播放')
    finally:p.close()
    log=p.log.read_text(encoding='utf-8',errors='replace')
    row['errors']=errors(log)
    row['decoder_details']=[line for line in log.splitlines() if 'libdav1d' in line or 'max_frame_delay' in line or 'Using ' in line and 'threads' in line]
    assert not row['errors'],row['errors']
    return row


def play(args, config, case, trial):
    names={
        'baseline':[],
        'dr-no':['--vd-lavc-dr=no'],
        'dr-yes':['--vd-lavc-dr=yes'],
        'queue':['--vd-queue-enable=yes'],
        'queue-dr-no':['--vd-queue-enable=yes','--vd-lavc-dr=no'],
        'queue-large':['--vd-queue-enable=yes','--vd-queue-max-bytes=512MiB','--vd-queue-max-samples=16'],
        't32':['--vd-lavc-threads=32'],
        't32-dr-no':['--vd-lavc-threads=32','--vd-lavc-dr=no'],
        'd8':['--vd-lavc-o=max_frame_delay=8'],
    }
    extra=names.get(case)
    if extra is None:
        match=re.fullmatch(r't(\d+)-d(\d+)',case)
        if not match:raise ValueError(case)
        extra=['--vd-lavc-threads='+match[1],'--vd-lavc-o=max_frame_delay='+match[2]]
    options=['--config-dir='+str(config),'--hwdec=no','--vd=libdav1d',
        '--geometry=1280x720+0+0','--autofit=1280x720','--autofit-smaller=1280x720',
        '--border=no','--title-bar=no','--volume=0','--sid=no','--secondary-sid=no',
        '--start=10','--pause=yes','--input-cursor=no','--input-vo-keyboard=no',
        '--input-media-keys=no',*extra,str(args.media)]
    p=helper['Player'](options,f'av1-play-{case}-{trial}')
    p.ipc_timeout=30
    try:
        p.wait_video()
        p.command('set_property','ontop',True)
        p.command('set_property','pause',False)
        deadline=time.monotonic()+60
        while (p.get('time-pos') or 0)<15:
            if time.monotonic()>deadline:raise TimeoutError('预热超时')
            time.sleep(.2)
        assert p.get('hwdec-current') in ('no',None)
        assert not p.get('vf') and not p.get('glsl-shaders') and not p.get('interpolation')
        assert p.get('linear-downscaling') is True
        settings={k:p.get(k) for k in ['video-params','video-target-params','video-codec',
            'video-sync','display-fps','current-ao','vd-lavc-threads','vd-lavc-dr',
            'vd-lavc-o','vd-queue-enable','vd-queue-max-bytes','vd-queue-max-samples',
            'deband','dscale','cscale','linear-downscaling','hwdec-current','framedrop']}
        color=p.get('user-data/color-target')
        assert color['mode']=='sdr-acm' and not color['external_overrides'],color
        first=p.get('time-pos')
        counts={k:p.get(k) or 0 for k in COUNTERS}
        log_offset=p.log.stat().st_size
        cpu=helper['process_cpu_seconds'](p.process)
        started=time.monotonic()
        samples=[]
        while time.monotonic()-started<args.seconds:
            time.sleep(.5)
            sample={k:p.get(k) for k in ['time-pos','frame-drop-count','decoder-frame-drop-count','avsync','pause','window-minimized']}
            sample['wall']=time.monotonic()-started
            assert not sample['pause'] and not sample['window-minimized'],sample
            samples.append(sample)
        elapsed=time.monotonic()-started
        advance=samples[-1]['time-pos']-first
        row=dict(kind='visible-full-config',case=case,trial=trial,seconds=elapsed,
            media_advance=advance,clock_ratio=advance/elapsed,
            cpu_cores=(helper['process_cpu_seconds'](p.process)-cpu)/elapsed,
            counters={k:(p.get(k) or 0)-counts[k] for k in COUNTERS},
            samples=samples,settings=settings,color=color,passes=p.get('vo-passes'),options=options)
        row['max_abs_avsync']=max(abs(s['avsync'] or 0) for s in samples)
        row['steady_audio_events']=[line for line in p.log.read_bytes()[log_offset:].decode('utf-8',errors='replace').splitlines()
            if re.search(r'underrun|underflow',line,re.I) and ('[ao/' in line or 'audio' in line.lower())]
        row['realtime_no_drop']=(.98<row['clock_ratio']<1.02 and not any(row['counters'].values())
            and not row['steady_audio_events'] and row['max_abs_avsync']<.1)
    finally:p.close()
    log=p.log.read_text(encoding='utf-8',errors='replace')
    row['errors']=errors(log)
    row['startup_errors']=errors(p.log.read_bytes()[:log_offset].decode('utf-8',errors='replace'))
    row['steady_errors']=errors(p.log.read_bytes()[log_offset:].decode('utf-8',errors='replace'))
    if row['steady_errors']:row['realtime_no_drop']=False
    row['dr_details']=[line for line in log.splitlines() if re.search(r'direct.render|max_frame_delay|Using .*threads|libdav1d [0-9]',line,re.I)]
    assert not row['steady_errors'] and 'Lua error:' not in log,row['steady_errors']
    return row


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('media',type=Path)
    parser.add_argument('--mode',choices=['decode','play'],default='play')
    parser.add_argument('--cases',nargs='+',default=['baseline','dr-no','queue','t32'])
    parser.add_argument('--threads',type=int,nargs='+',default=[8,12,16,24,32])
    parser.add_argument('--delay',type=int,default=0)
    parser.add_argument('--frames',type=int,default=288)
    parser.add_argument('--seconds',type=float,default=20)
    parser.add_argument('--rounds',type=int,default=1)
    parser.add_argument('--output',type=Path,default=ROOT/'tmp/modernization/kaguya-softdecode-20261008')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    rows=[]
    if args.mode=='decode':
        cases=args.threads
        config=None
    else:
        cases=args.cases
        config=create_config('av1-software',exclude_scripts=['window-size-position.lua'])
    path=args.output/(args.mode+'-results.json')
    for trial in range(1,args.rounds+1):
        for case in (cases if trial%2 else list(reversed(cases))):
            print('RUN',args.mode,case,trial,flush=True)
            row=decode(args,case,args.delay) if args.mode=='decode' else play(args,config,case,trial)
            row['trial']=trial
            rows.append(row)
            path.write_text(json.dumps(dict(media=args.media.name,rows=rows,
                scope='强制CPU解码；不启用解码跳帧或降低位深／处理精度；输出丢帧据实记录；null只是控制组'),
                ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
            print('RESULT',json.dumps({k:row.get(k) for k in ['threads','case','clock_ratio','cpu_cores','counters','realtime_no_drop']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
