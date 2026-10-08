"""顺序对照 mpv 与 VS 1.0.5 原生播放；保留逐秒数据。"""
import argparse
import json
from pathlib import Path
import runpy
import subprocess
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))
native_api = runpy.run_path(str(ROOT / 'tools/benchmark-vs105-native.py'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    parser.add_argument('media', type=Path)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--output', type=Path, default=ROOT / 'tmp/modernization/vs105-results')
    parser.add_argument('--cases', nargs='+', default=['mpv-current', 'vs-jinc', 'mpv-basic', 'vs-native', 'mpv-bilinear', 'vs-bilinear'])
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    props = ['time-pos', 'hwdec-current', 'video-params', 'video-target-params',
             'display-fps', 'video-sync', 'frame-drop-count', 'decoder-frame-drop-count',
             'mistimed-frame-count', 'vo-delayed-frame-count', 'avsync', 'speed',
             'estimated-vf-fps', 'vo-passes', 'vf', 'glsl-shaders', 'interpolation',
             'deband', 'options/dscale', 'options/cscale', 'options/correct-downscaling',
             'osd-dimensions']
    for trial in range(1, args.repeats + 1):
        for name in args.cases:
            destination = out / f'{name}-{trial}.json'
            print('START', name, trial, flush=True)
            if name.startswith('vs-'):
                algorithms = {'vs-jinc': 1284, 'vs-native': 7, 'vs-bilinear': 513, 'vs-soft': 513,
                              'vs-jinc-tearing': 1284, 'vs-bilinear-tearing': 513}
                command = [sys.executable, str(ROOT / 'tools/benchmark-vs105-native.py'),
                           str(args.package), str(args.media), str(destination),
                           '--seconds', str(args.seconds), '--algorithm', str(algorithms[name]),
                           '--mode', '1' if name == 'vs-soft' else '2']
                if name.endswith('-tearing'):
                    command += ['--tearing', '--pacing']
                subprocess.run(command, check=True, timeout=120)
                continue
            base = ['--geometry=1280x720+0+0', '--border=no', '--volume=0', '--sid=no',
                    '--secondary-sid=no', '--start=10', '--pause=yes']
            if name != 'mpv-current':
                base += ['--no-config', '--vo=gpu-next', '--gpu-api=d3d11',
                         '--hwdec=d3d11va', '--target-prim=bt.709', '--target-trc=srgb',
                         '--d3d11-output-csp=srgb', '--deband=no', '--interpolation=no',
                         '--cscale=bilinear', '--dscale=catmull_rom']
            if name in ['mpv-bilinear', 'mpv-soft']:
                base += ['--dscale=bilinear', '--correct-downscaling=no']
            if name == 'mpv-soft':
                base += ['--hwdec=no', '--vd-lavc-threads=16']
            if name == 'mpv-color-matched':
                base += ['--treat-srgb-as-power22=no', '--target-colorspace-hint=no']
            player = api['Player'](base + [str(args.media)], f'perf-{name}-{trial}')
            try:
                player.wait_video()
                player.command('set_property', 'ontop', True)
                player.command('set_property', 'pause', False)
                deadline = time.monotonic() + 60
                while (player.get('time-pos') or 0) < 15:
                    if time.monotonic() > deadline:
                        raise TimeoutError('mpv 预热超时')
                    time.sleep(.05)
                started = time.monotonic()
                rows = []
                try:
                    gpu = api['GPUCounter']()
                except Exception:
                    gpu = None
                while True:
                    row = {prop: player.get(prop) for prop in props}
                    row['wall'] = time.monotonic() - started
                    row['cpu_s'] = api['process_cpu_seconds'](player.process)
                    row['gpu_engines'] = native_api['gpu_engines'](gpu, player.process.pid) if gpu else None
                    rows.append(row)
                    if row['wall'] >= args.seconds:
                        break
                    time.sleep(max(0, 1 - (time.monotonic() - started - row['wall'])))
                destination.write_text(json.dumps({'args': base, 'rows': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
                print('DONE', name, trial, flush=True)
                if gpu:
                    gpu.close()
            finally:
                player.close()


if __name__ == '__main__':
    main()
