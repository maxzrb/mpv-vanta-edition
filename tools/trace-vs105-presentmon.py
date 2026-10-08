"""用独立ETW会话捕获原生探针的DXGI呈现，保持其它追踪会话。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('presentmon', type=Path)
    parser.add_argument('package', type=Path)
    parser.add_argument('media', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--algorithm', type=int, default=519)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--tearing', action='store_true')
    parser.add_argument('--mpv', action='store_true')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    gate = args.output.with_name(args.output.stem + '-' + uuid.uuid4().hex + '.gate')
    environment = os.environ.copy()
    environment['VSR_3FP_PROFILE'] = '1'
    command = [sys.executable, str(Path(__file__).with_name('benchmark-vs105-native.py')),
               str(args.package), str(args.media), str(args.output),
               '--algorithm', str(args.algorithm), '--seconds', str(args.seconds),
               '--start-gate', str(gate)]
    if args.tearing:
        command += ['--tearing', '--pacing']
    if args.mpv:
        command = [sys.executable, str(Path(__file__).with_name('benchmark-mpv-presentmon.py')),
                   str(args.media), str(args.output), '--seconds', str(args.seconds),
                   '--start-gate', str(gate)]
    host_log = args.output.with_suffix('.host.log').open('w', encoding='utf-8')
    host = subprocess.Popen(command, env=environment, stdout=host_log, stderr=subprocess.STDOUT)
    collector = None
    collector_log = args.output.with_suffix('.presentmon.log').open('w', encoding='utf-8')
    session = 'VantaVSProbe-' + uuid.uuid4().hex
    try:
        deadline = time.monotonic() + 15
        while not gate.with_suffix('.ready.json').exists():
            if host.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('探针未就绪，详见host日志')
            time.sleep(.05)
        target_pid = json.loads(gate.with_suffix('.ready.json').read_text(encoding='utf-8'))['pid']
        collector_command = [str(args.presentmon.resolve()), '--process_id', str(target_pid),
            '--output_file', str(args.output.with_suffix('.presentmon.csv').resolve()),
            '--session_name', session, '--qpc_time', '--v2_metrics', '--track_gpu_video',
            '--track_hybrid_present', '--write_display_metadata', '--no_track_input',
            '--no_console_stats', '--terminate_on_proc_exit', '--timed', '100',
            '--terminate_after_timed']
        collector = subprocess.Popen(collector_command, stdout=collector_log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 15
        while True:
            if collector.poll() is not None:
                raise RuntimeError('PresentMon未能启动，详见presentmon日志')
            state = subprocess.run(['logman', 'query', session, '-ets'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if state.returncode == 0:
                break
            if time.monotonic() > deadline:
                raise TimeoutError('ETW会话未就绪')
            time.sleep(.1)
        gate.write_text('start', encoding='utf-8')
        host.wait(timeout=110)
        if host.returncode:
            raise RuntimeError('播放探针失败，详见host日志')
        # 非管理员捕获可能没有进程退出事件；用独立会话名主动结束并刷新CSV。
        try:
            collector.wait(timeout=3)
        except subprocess.TimeoutExpired:
            subprocess.run([str(args.presentmon.resolve()), '--session_name', session,
                            '--terminate_existing_session'], stdout=collector_log,
                           stderr=subprocess.STDOUT, check=True, timeout=10)
            collector.wait(timeout=10)
        if collector.returncode:
            raise RuntimeError('PresentMon异常退出')
        args.output.with_suffix('.capture.json').write_text(json.dumps({
            'session': session, 'pid': target_pid, 'host_pid': host.pid, 'collector_args': collector_command,
            'host_args': command, 'collector_exit': collector.returncode,
            'host_exit': host.returncode}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(args.output)
    finally:
        if host.poll() is None:
            host.kill()
            host.wait()
        if collector and collector.poll() is None:
            # 只终止本工具创建的会话，不使用stop_existing_session。
            subprocess.run([str(args.presentmon.resolve()), '--session_name', session,
                            '--terminate_existing_session'], stdout=collector_log,
                           stderr=subprocess.STDOUT, timeout=10)
            try:
                collector.wait(timeout=10)
            except subprocess.TimeoutExpired:
                collector.kill()
                collector.wait()
        host_log.close()
        collector_log.close()


if __name__ == '__main__':
    main()
