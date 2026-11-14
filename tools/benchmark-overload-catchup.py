"""同片同设置对照过载追赶；降速段验证保持或可选恢复，不混入性能统计。"""
import argparse
import json
from pathlib import Path
import runpy
import time

ROOT = Path(__file__).resolve().parents[1]
helper = runpy.run_path(str(ROOT / 'tools/test-overload-fate.py'))
Player, wait = helper['Player'], helper['wait']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('media', type=Path)
    parser.add_argument('--backend', choices=['d3d11', 'vulkan'], default='d3d11')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--full-config', action='store_true')
    parser.add_argument('--native-budget', action='store_true')
    parser.add_argument('--auto-recover', action='store_true')
    parser.add_argument('--enabled-only', action='store_true', help='复核源码修订时仅重跑开启组，原关闭组另存')
    args = parser.parse_args()
    rows = []
    modes = [True] if args.enabled_only else [False, True]
    for enabled in modes:
        if args.full_config:
            create = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']
            config = create('overload-real-' + args.backend)
        else:
            config = helper['configuration']()
        decoder = [] if args.native_budget else ['--vd-lavc-threads=32', '--vd-lavc-o=max_frame_delay=32']
        p = Player(['--config-dir=' + str(config), '--gpu-api=' + args.backend, '--hwdec=no',
                    *decoder, '--volume=0',
                    '--script-opts-append=color-target-pipeline=hq',
                    '--script-opts-append=decode-performance-catchup=' + ('yes' if enabled else 'no'),
                    '--script-opts-append=decode-performance-catchup_recover=' + ('yes' if args.auto_recover else 'no'),
                    '--geometry=640x360', '--start=10', str(args.media.resolve())],
                   'overload-real-' + args.backend + '-' + str(enabled))
        samples, output_states = [], []
        try:
            p.wait_video()
            start = time.monotonic()
            slow = False
            while time.monotonic() - start < (70 if enabled else 30):
                wall = time.monotonic() - start
                if enabled and not slow and wall >= 30:
                    p.command('set_property', 'speed', .25)
                    slow = True
                data = {k: p.get(k) for k in ['time-pos', 'avsync', 'frame-drop-count',
                        'decoder-frame-drop-count', 'vd-lavc-skipframe', 'hwdec-current',
                        'speed', 'pause', 'seeking', 'user-data/decode-performance']}
                data['wall'] = wall
                samples.append(data)
                if not data['seeking'] and not data['user-data/decode-performance']['reload-active']:
                    mode = data['vd-lavc-skipframe']
                    if not output_states or output_states[-1]['skipframe'] != mode:
                        target = p.get('video-target-params')
                        if target:
                            output_states.append(dict(skipframe=mode, target=target, source=p.get('video-params'),
                                color=p.get('user-data/color-target'), threads=p.get('vd-lavc-threads'),
                                avopts=p.get('vd-lavc-o')))
                time.sleep(.25)
            if enabled:
                assert any(s['vd-lavc-skipframe'] == 'nonref' for s in samples), '未触发真实过载追赶'
                if args.auto_recover:
                    assert any(s['wall'] > 40 and s['vd-lavc-skipframe'] == 'default'
                               and s['user-data/decode-performance']['catchup-switches'] >= 2 for s in samples), '降速后未恢复完整解码'
                else:
                    stable = [s for s in samples if s['wall'] > 40]
                    assert stable and all(s['vd-lavc-skipframe'] == 'nonref' for s in stable), '默认应保持参考帧模式'
        finally:
            p.close()
        log = p.log.read_text(encoding='utf-8', errors='replace')
        errors = [line for line in log.splitlines() if '[e]' in line or '[f]' in line or 'Lua error:' in line]
        assert not errors, errors[:10]
        normal = [s for s in samples if s['wall'] >= 8 and s['wall'] < 30 and s['speed'] == 1]
        row = dict(enabled=enabled, samples=samples, errors=errors, log=str(p.log),
                   output_states=output_states,
                   normal_speed_last_avsync=normal[-1]['avsync'],
                   normal_speed_max_abs_avsync=max(abs(s['avsync']) for s in normal if s['avsync'] is not None),
                   audio_underrun_log_lines=sum('underrun' in line.lower() for line in log.splitlines()),
                   audio_underruns=sum('Audio device underrun detected.' in line for line in log.splitlines()),
                   recovery_test=('30秒后以0.25倍速降低解码需求，验证可选恢复' if args.auto_recover
                                  else '30秒后以0.25倍速降低解码需求，验证默认保持参考帧模式') if enabled else None)
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k not in ['samples', 'output_states']}, ensure_ascii=False), flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(dict(passed=len(rows) == len(modes), backend=args.backend, rows=rows),
                                         ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
