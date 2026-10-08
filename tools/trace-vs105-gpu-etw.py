"""用独立DxgKrnl用户ETW会话记录GPU队列；不占用或取消系统WPR会话。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
import runpy
import ctypes as C
import hashlib


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    parser.add_argument('media', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--algorithm', type=int, default=513)
    parser.add_argument('--mpv', action='store_true')
    parser.add_argument('--lean', action='store_true')
    parser.add_argument('--video-queue-limit', type=int, choices=[0,4,8], default=0)
    args = parser.parse_args()
    if args.video_queue_limit and args.mpv:
        raise ValueError('mpv对照不改写队列')
    if args.video_queue_limit and hashlib.sha256((args.package/'FFF.Native.dll').read_bytes()).hexdigest() != '094c19e0658235dafa0c5b5d46e59c211c9390632c71794aad45e4dcfe95de50':
        raise RuntimeError('预算探针仅支持已核验DLL')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    session = 'VantaGPU-' + uuid.uuid4().hex
    gate = args.output.with_suffix('.gate')
    if gate.exists():
        raise RuntimeError('请用新输出文件名，避免复用启动门')
    environment = os.environ.copy()
    environment['VSR_3FP_PROFILE'] = '1'
    command = [sys.executable, str(Path(__file__).with_name('benchmark-vs105-native.py')),
               str(args.package), str(args.media), str(args.output), '--algorithm',
               str(args.algorithm), '--seconds', '20', '--start-gate', str(gate)]
    if args.video_queue_limit:
        command += ['--video-queue-limit',str(args.video_queue_limit)]
    if args.mpv:
        command = [sys.executable, str(Path(__file__).with_name('benchmark-mpv-presentmon.py')),
            str(args.media), str(args.output), '--seconds', '20', '--start-gate', str(gate)]
    if args.lean:
        environment.pop('VSR_3FP_PROFILE', None)
        command += ['--warm-position', '20']
    filter_api = runpy.run_path(str(Path(__file__).with_name('configure-gpu-etw-filter.py')))
    configure = filter_api['configure']
    filter_info = []
    marker = runpy.run_path(str(Path(__file__).with_name('etw-qpc-marker.py')))['Marker']()
    markers = []
    host = None

    started = False
    with args.output.with_suffix('.etw.log').open('w', encoding='utf-8') as log:
        try:
            start = subprocess.run(['logman', 'start', session, '-ets', '-o',
                str(args.output.with_suffix('.etl').resolve()), '-p',
                'Microsoft-Windows-DxgKrnl', '0x841' if args.lean else '0xffffffffffffffff', '5', '-bs', '1024',
                '-nb', '8', '64', '-f', 'bincirc', '-max', '256'],
                stdout=log, stderr=subprocess.STDOUT)
            if start.returncode:
                raise RuntimeError('独立GPU ETW启动失败，详见etw日志')
            started = True
            marker.enable(filter_api['session_handle'](session))
            if args.lean:
                filter_info.append(configure(session, 0x841))
            markers.append(marker.emit())
            host = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 15
            while not gate.with_suffix('.ready.json').exists():
                if time.monotonic() > deadline or host.poll() is not None:
                    raise TimeoutError('原生探针未就绪')
                time.sleep(.05)
            gate.write_text('start', encoding='utf-8')
            host.wait(timeout=110)
            if host.returncode:
                raise RuntimeError('原生播放失败')
            if args.video_queue_limit and json.loads(args.output.read_text(encoding='utf-8')).get('budget_patch',{}).get('queue_limit')!=args.video_queue_limit:
                raise RuntimeError('预算实验未核验，拒绝采用ETW结果')
            markers.append(marker.emit())
        finally:
            if host and host.poll() is None:
                host.kill()
                host.wait()
            if started:
                subprocess.run(['logman', 'stop', session, '-ets'], stdout=log,
                               stderr=subprocess.STDOUT, check=True)
            marker.close()
    args.output.with_suffix('.etw.json').write_text(json.dumps({
        'session': session, 'host_pid': host.pid, 'host_exit': host.returncode,
        'target_pid': json.loads(gate.with_suffix('.ready.json').read_text(encoding='utf-8'))['pid'],
        'filters': filter_info, 'video_queue_limit':args.video_queue_limit,
        'marker_provider': marker.guid, 'qpc_markers': markers,
        'command': command, 'provider': 'Microsoft-Windows-DxgKrnl'},
        ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
