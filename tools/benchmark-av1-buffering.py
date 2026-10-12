"""固定解码线程，比较完整可见播放的解码队列和启动预缓冲；只改隔离配置。"""
import argparse
import ctypes
import json
import runpy
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
h = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))
memory = runpy.run_path(str(ROOT / 'tools/benchmark-av1-scheduling.py'))['memory']
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']


def available_memory():
    class Status(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                    *[(k, ctypes.c_ulonglong) for k in ['total', 'available', 'total_page',
                       'available_page', 'total_virtual', 'available_virtual', 'extended']]]
    status = Status(); status.length = ctypes.sizeof(status)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.available


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('media', type=Path)
    parser.add_argument('--backend', choices=['d3d11', 'vulkan'], default='d3d11')
    parser.add_argument('--frames', type=int, default=16)
    parser.add_argument('--bytes', default='768MiB')
    parser.add_argument('--secs', type=float, default=2)
    parser.add_argument('--prefill', type=float, default=0)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float, default=92.09)
    parser.add_argument('--extra', action='append', default=[])
    parser.add_argument('--name', default='d3d11-q16')
    parser.add_argument('--output', type=Path, default=ROOT / 'tmp/modernization/zero-drop-study-20261011')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    cfg = create_config('buffering-' + args.name, exclude_scripts=['window-size-position.lua', 'autoload.lua'])
    options = ['--config-dir=' + str(cfg), '--gpu-api=' + args.backend, '--hwdec=no', '--vd-queue-enable=yes',
        '--vd-lavc-threads=32', '--vd-lavc-o=max_frame_delay=32',
        '--vd-queue-max-samples=' + str(args.frames), '--vd-queue-max-bytes=' + args.bytes,
        '--vd-queue-max-secs=' + str(args.secs), '--start=' + str(args.start), '--end=' + str(args.end),
        '--pause=yes', '--volume=0', '--sid=auto', '--geometry=1280x720', '--autofit=1280x720',
        '--autofit-smaller=1280x720', '--border=no', '--input-vo-keyboard=no',
        '--input-media-keys=no', '--input-cursor=no', *args.extra, str(args.media)]
    print('RUN', args.name, 'available GiB', round(available_memory() / 2**30, 2), flush=True)
    p = h['Player'](options, 'buffering-' + args.name); p.ipc_timeout = 30
    try:
        p.wait_video(); deadline = time.monotonic() + 20
        while (p.get('user-data/color-target') or {}).get('mode') != 'sdr-acm':
            assert time.monotonic() < deadline; time.sleep(.1)
        assert p.get('sid') == 1 and p.get('playlist-count') == 1
        assert not p.get('vf') and not p.get('glsl-shaders') and p.get('linear-downscaling') is True
        assert p.get('vd-lavc-threads') == 32 and p.get('speed') == 1
        settings = {k: p.get(k) for k in ['video-params', 'video-target-params', 'sid', 'framedrop',
            'video-sync', 'vd-lavc-threads', 'vd-lavc-o', 'vd-queue-max-samples', 'vd-queue-max-bytes',
            'vd-queue-max-secs', 'vulkan-async-transfer', 'vulkan-async-compute', 'vulkan-queue-count',
            'vulkan-swap-mode', 'swapchain-depth', 'dscale', 'linear-downscaling']}
        prefills = []; began = time.monotonic()
        while time.monotonic() - began < args.prefill:
            prefills.append({'wall': time.monotonic() - began, 'cpu': h['process_cpu_seconds'](p.process),
                             'memory': memory(p.process), 'available': available_memory()})
            assert available_memory() > 1.5 * 2**30, '剩余物理内存过低，终止本工具的播放器'
            time.sleep(.5)
        row = {'name': args.name, 'options': options, 'settings': settings, 'prefill_samples': prefills,
               'color': p.get('user-data/color-target')}
        counts = {k: p.get(k) or 0 for k in ['frame-drop-count', 'decoder-frame-drop-count',
                  'mistimed-frame-count', 'vo-delayed-frame-count']}
        log_offset = p.log.stat().st_size; began = time.monotonic(); samples = []; last_report = 0
        p.command('set_property', 'ontop', True); p.command('set_property', 'pause', False)
        while time.monotonic() - began < (args.end - args.start) * 2 + 30:
            assert p.get('path') == str(args.media)
            sample = {k: p.get(k) for k in ['time-pos', 'frame-drop-count', 'avsync', 'eof-reached', 'pause']}
            sample.update(wall=time.monotonic() - began, available=available_memory())
            samples.append(sample)
            assert sample['available'] > 1.5 * 2**30, '剩余物理内存过低，终止本工具的播放器'
            if sample['wall'] - last_report > 25:
                print('PROGRESS', args.name, sample, flush=True); last_report = sample['wall']
            if sample['eof-reached'] or p.get('idle-active'): break
            if sample['pause'] and p.get('eof-reached'): break
            assert not sample['pause'] and not p.get('window-minimized')
            time.sleep(.5)
        else: raise TimeoutError(args.name)
        elapsed = time.monotonic() - began
        log = p.log.read_bytes()[log_offset:].decode('utf-8')
        row.update(seconds=elapsed, samples=samples, memory=memory(p.process), initial_counters=counts,
            counters={k: (p.get(k) or 0) - v for k, v in counts.items()},
            max_abs_avsync=max(abs(s['avsync'] or 0) for s in samples),
            audio_underruns=sum('Audio device underrun detected.' in line for line in log.splitlines()),
            errors=[line for line in log.splitlines() if '[e]' in line or '[f]' in line])
        assert 'Lua error:' not in log
    finally: p.close()
    path = args.output / (args.name + '.json')
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('RESULT', json.dumps({k: row[k] for k in ['seconds', 'counters', 'max_abs_avsync',
                                                 'audio_underruns', 'memory', 'errors']}, ensure_ascii=False), flush=True)


if __name__ == '__main__': main()
