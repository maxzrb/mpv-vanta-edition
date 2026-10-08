"""HQ 线性缩小的三轮真实播放对照；不使用 GPU 读回探针。"""
import json
import runpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/color-output-20261008'
helper = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']
config = create_config('linear-downscale-benchmark',exclude_scripts=['window-size-position.lua'])
media = ROOT / 'tmp/modernization/optimization-20261005/performance-2160.mkv'
rows = []
verify = '--verify' in sys.argv
for trial in range(1, 4):
    for linear in ([True] if verify else [False, True] if trial % 2 else [True, False]):
        p = helper['Player'](['--config-dir=' + str(config), '--geometry=1280x720',
            '--autofit=1280x720', '--autofit-smaller=1280x720', '--loop-file=inf',
            '--border=no','--title-bar=no',
            '--volume=0', '--input-cursor=no', '--input-default-bindings=no',
            '--input-vo-keyboard=no', '--input-media-keys=no', str(media)],
            f'linear-downscale-{trial}-{linear}')
        try:
            p.wait_video()
            p.command('set_property', 'linear-downscaling', linear)
            time.sleep(5)
            assert p.get('hwdec-current') == 'd3d11va'
            assert p.get('linear-downscaling') == linear
            target=p.get('video-target-params')
            assert (target['w'],target['h'])==(1280,720),target
            keys = ['frame-drop-count', 'decoder-frame-drop-count', 'mistimed-frame-count', 'vo-delayed-frame-count']
            before = {k: p.get(k) or 0 for k in keys}
            started = time.monotonic()
            cpu = helper['process_cpu_seconds'](p.process)
            last, advance = p.get('time-pos'), 0
            duration = p.get('duration')
            while time.monotonic() - started < 20:
                time.sleep(.5)
                now = p.get('time-pos')
                delta = now - last
                if delta < -.5:
                    delta += duration
                advance += max(0, delta)
                last = now
            elapsed = time.monotonic() - started
            row = dict(trial=trial, linear=linear, seconds=elapsed, clock_ratio=advance/elapsed,
                cpu_core_percent=100*(helper['process_cpu_seconds'](p.process)-cpu)/elapsed,
                counters={k: (p.get(k) or 0)-before[k] for k in keys}, passes=p.get('vo-passes'),target=target)
            assert .98 < row['clock_ratio'] < 1.02, row
        finally:
            p.close()
        log = p.log.read_text(encoding='utf-8', errors='replace')
        row['errors'] = [line for line in log.splitlines() if '[e]' in line or '[f]' in line]
        row['underruns'] = [line for line in log.splitlines() if 'underrun' in line.lower() or 'underflow' in line.lower()]
        assert not row['errors'] and not row['underruns'], row
        rows.append(row)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT/('linear-performance-final.json' if verify else 'linear-performance.json')).write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n',
            encoding='utf-8', newline='\n')
        print('PASS', trial, linear, row['clock_ratio'], row['counters'], flush=True)
