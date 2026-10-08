"""先等待ETW就绪再加载视频，记录准确SDR基础配置的QPC稳定段。"""
import argparse
import ctypes as C
import json
from pathlib import Path
import runpy
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('media', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--start-gate', type=Path, required=True)
    parser.add_argument('--amd-metrics', action='store_true')
    parser.add_argument('--warm-position', type=int, choices=[15,20], default=15)
    args = parser.parse_args()
    api = runpy.run_path(str(Path(__file__).with_name('validate-modernization.py')))
    options = ['--no-config', '--idle=yes', '--pause=yes', '--geometry=1280x720+0+0',
        '--border=no', '--volume=0', '--sid=no', '--secondary-sid=no', '--start=10',
        '--vo=gpu-next', '--gpu-api=d3d11', '--hwdec=d3d11va', '--target-prim=bt.709',
        '--target-trc=srgb', '--d3d11-output-csp=srgb', '--treat-srgb-as-power22=no',
        '--target-colorspace-hint=no', '--deband=no', '--interpolation=no',
        '--cscale=bilinear', '--dscale=catmull_rom']
    player = api['Player'](options, 'mpv-presentmon')
    amd = None
    try:
        if args.amd_metrics:
            amd = runpy.run_path(str(Path(__file__).with_name('query-amd-metrics.py')))['AMDReader']()
        args.start_gate.with_suffix('.ready.json').write_text(
            json.dumps({'pid': player.process.pid}), encoding='utf-8')
        deadline = time.monotonic() + 60
        while not args.start_gate.exists():
            if time.monotonic() > deadline or player.process.poll() is not None:
                raise TimeoutError('ETW就绪等待失败')
            time.sleep(.05)
        player.command('loadfile', str(args.media.resolve()))
        player.wait_video()
        player.command('set_property', 'ontop', True)
        player.command('set_property', 'pause', False)
        deadline = time.monotonic() + 60
        while (player.get('time-pos') or 0) < args.warm_position:
            if time.monotonic() > deadline:
                raise TimeoutError('播放预热超时')
            time.sleep(.05)
        kernel = C.WinDLL('kernel32')
        frequency = C.c_int64()
        kernel.QueryPerformanceFrequency(C.byref(frequency))
        props = ['time-pos', 'hwdec-current', 'video-target-params', 'osd-dimensions',
                 'frame-drop-count', 'decoder-frame-drop-count', 'avsync', 'vo-passes']
        rows = []
        started = time.monotonic()
        while True:
            row = {name: player.get(name) for name in props}
            qpc = C.c_int64()
            kernel.QueryPerformanceCounter(C.byref(qpc))
            row.update(qpc=qpc.value, wall=time.monotonic() - started)
            if amd:
                row['amd_metrics'] = amd.read()
            rows.append(row)
            if row['wall'] >= args.seconds:
                break
            time.sleep(1)
        args.output.write_text(json.dumps({'args': options, 'pid': player.process.pid,
            'warm_position': args.warm_position,
            'qpc_frequency': frequency.value, 'rows': rows}, ensure_ascii=False, indent=2),
            encoding='utf-8')
        print(args.output)
    finally:
        if amd:
            amd.close()
        player.close()


if __name__ == '__main__':
    main()
