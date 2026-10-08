"""同完整配置比较新增管理任务的起播附加耗时，不把起播短测当稳态性能收益。"""
import json
import re
import runpy
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/optimization-20261005'
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']
configs = {name: create_config('startup-' + name) for name in ['managed', 'without-managers']}
for name in ['quality.lua', 'color-target.lua', 'quality_status.lua', 'hwdec-select.lua', 'hdr-mode.lua']:
    # 只修改自建隔离配置；对照基线仍使用相同 HQ／直接硬解／SDR 目标。
    (configs['without-managers'] / 'scripts' / name).unlink()
rows = []
for trial in range(1, 4):
    for name in (['managed', 'without-managers'] if trial % 2 else ['without-managers', 'managed']):
        start = time.monotonic()
        p = Player(['--config-dir=' + str(configs[name]), '--ao=null', '--pause=no', '--geometry=1280x720',
                    str(ROOT / 'tmp/modernization/validation/compat-hevc10.mkv')], f'startup-{name}-{trial}')
        try:
            p.wait_video()
            ready = time.monotonic() - start
            limit = time.monotonic() + 6
            while time.monotonic() < limit and (p.get('time-pos') or 0) <= 0:
                time.sleep(.1)
            assert p.get('time-pos') > 0 and not p.get('vf') and not p.get('glsl-shaders')
        finally:
            p.close()
        log = p.log.read_text(encoding='utf-8')
        assert 'probe.py' not in log and 'prepare_filter' not in log and 'Lua error:' not in log
        first = re.search(r'\[\s*([0-9.]+)\].*first video frame', log, re.I)
        rows.append({'case': name, 'trial': trial, 'ipc_video_ready_seconds': ready,
                     'first_video_frame_log_seconds': float(first[1]) if first else None})
        print(name, trial, round(ready, 3), flush=True)
(OUT / 'startup-results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                                        encoding='utf-8', newline='\n')
print('PASS 同完整配置三轮起播对照；非稳态性能推广依据')
