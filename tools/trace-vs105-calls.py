"""仅插桩本工具创建的原生测试进程，逐调用记录D3D11／DXGI时间。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    parser.add_argument('media', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--algorithm', type=int, default=519)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--skip-video-processor', action='store_true')
    parser.add_argument('--skip-draw', action='store_true')
    parser.add_argument('--skip-copy', action='store_true')
    parser.add_argument('--copy-box', type=int, choices=[0,64], default=0)
    parser.add_argument('--device-latency', type=int, choices=[0,1,2], default=0)
    parser.add_argument('--shader-texture-only', action='store_true')
    parser.add_argument('--decoder-only', action='store_true')
    parser.add_argument('--pool-size', type=int, choices=[0,12,14,16], default=0)
    parser.add_argument('--discard-copy', action='store_true')
    parser.add_argument('--separate-surfaces', action='store_true')
    parser.add_argument('--flush-copy', action='store_true')
    parser.add_argument('--flush-decode', action='store_true')
    parser.add_argument('--mpv', action='store_true')
    parser.add_argument('--wait-copy', action='store_true')
    parser.add_argument('--idle-copy-probe', action='store_true')
    parser.add_argument('--wait-decode', action='store_true')
    parser.add_argument('--early-copy', action='store_true')
    parser.add_argument('--no-profile', action='store_true')
    parser.add_argument('--device-flags', type=int, choices=[-1,0], default=-1)
    parser.add_argument('--amd-metrics', action='store_true')
    parser.add_argument('--gpu-priority', type=int, choices=[0,7], default=None)
    parser.add_argument('--decode-interval-ms', type=int, choices=[0,10,20], default=0)
    parser.add_argument('--release-after-copy', action='store_true')
    parser.add_argument('--video-queue-limit', type=int, choices=[0,4,8], default=0)
    args = parser.parse_args()
    if args.early_copy and (args.algorithm != 513 or args.mpv):
        raise ValueError('提前复制实验仅针对本版VS Shader双线性路径')
    if args.release_after_copy and (args.algorithm != 513 or args.mpv or args.early_copy):
        raise ValueError('复制后释放实验只验证原始Shader双线性路径')
    if not args.mpv and hashlib.sha256((args.package / 'FFF.Native.dll').read_bytes()).hexdigest() != \
            '094c19e0658235dafa0c5b5d46e59c211c9390632c71794aad45e4dcfe95de50':
        raise RuntimeError('固定调用位置探针仅支持已核验的094c19e版本DLL')
    # 探针依赖仅在忽略目录内，不改播放器Python组件。
    sys.path.insert(0, str(Path('tmp/modernization/vs105-instrument/deps').resolve()))
    import frida
    args.output.parent.mkdir(parents=True, exist_ok=True)
    gate = args.output.with_name(args.output.stem + '-' + uuid.uuid4().hex + '.gate')
    command = [sys.executable, str(Path(__file__).with_name('benchmark-vs105-native.py')),
               str(args.package), str(args.media), str(args.output), '--algorithm',
               str(args.algorithm), '--seconds', str(args.seconds), '--start-gate', str(gate)]
    if args.video_queue_limit:
        command += ['--video-queue-limit',str(args.video_queue_limit)]
    if args.idle_copy_probe:
        command += ['--idle-copy-probe']
    if args.mpv:
        if any([args.skip_video_processor, args.skip_draw, args.skip_copy, args.copy_box,
                args.device_latency, args.shader_texture_only, args.decoder_only, args.pool_size,
                args.discard_copy, args.separate_surfaces, args.flush_copy, args.flush_decode, args.wait_copy,
                args.idle_copy_probe, args.wait_decode, args.device_flags >= 0, args.gpu_priority is not None,
                args.decode_interval_ms, args.video_queue_limit]):
            raise ValueError('mpv仅支持只读探针，不允许应用VS实验改写')
        command = [sys.executable, str(Path(__file__).with_name('benchmark-mpv-presentmon.py')),
                   str(args.media), str(args.output), '--seconds', str(args.seconds),
                   '--start-gate', str(gate)]
    if args.amd_metrics:
        command += ['--amd-metrics']
    environment = os.environ.copy()
    environment['VSR_3FP_PROFILE'] = '1'
    if args.no_profile:
        environment.pop('VSR_3FP_PROFILE', None)
    with args.output.with_suffix('.host.log').open('w', encoding='utf-8') as log, \
         args.output.with_suffix('.calls.jsonl').open('w', encoding='utf-8') as events:
        host = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT)
        session = None
        try:
            deadline = time.monotonic() + 15
            while not gate.with_suffix('.ready.json').exists():
                if time.monotonic() > deadline or host.poll() is not None:
                    raise TimeoutError('原生探针未就绪')
                time.sleep(.05)
            target_pid = json.loads(gate.with_suffix('.ready.json').read_text(encoding='utf-8')).get('pid', host.pid)
            session = frida.attach(target_pid)
            source = 'const SKIP_VIDEO_PROCESSOR=' + str(args.skip_video_processor).lower() + ';\n'
            source += 'const SKIP_DRAW=' + str(args.skip_draw).lower() + ';\n'
            source += 'const SKIP_COPY=' + str(args.skip_copy).lower() + ';\n'
            source += f'const COPY_BOX={args.copy_box};const DEVICE_LATENCY={args.device_latency};\n'
            source += 'const SHADER_TEXTURE_ONLY=' + str(args.shader_texture_only).lower() + ';\n'
            source += 'const DECODER_ONLY=' + str(args.decoder_only).lower() + ';\n'
            source += f'const POOL_SIZE={args.pool_size};\n'
            source += 'const DISCARD_COPY=' + str(args.discard_copy).lower() + ';\n'
            source += 'const SEPARATE_SURFACES=' + str(args.separate_surfaces).lower() + ';\n'
            source += 'const FLUSH_COPY=' + str(args.flush_copy).lower() + ';\n'
            source += 'const FLUSH_DECODE=' + str(args.flush_decode).lower() + ';\n'
            source += 'const WAIT_COPY=' + str(args.wait_copy).lower() + ';\n'
            source += 'const WAIT_DECODE=' + str(args.wait_decode).lower() + ';\n'
            source += 'const IDLE_COPY_PROBE=' + str(args.idle_copy_probe).lower() + ';\n'
            source += 'const EARLY_COPY=' + str(args.early_copy).lower() + ';\n'
            source += f'const DEVICE_FLAGS={args.device_flags};\n'
            source += f'const GPU_PRIORITY={json.dumps(args.gpu_priority)};\n'
            source += f'const DECODE_INTERVAL_MS={args.decode_interval_ms};\n'
            source += 'const RELEASE_AFTER_COPY=' + str(args.release_after_copy).lower() + ';\n'
            source += Path(__file__).with_suffix('.js').read_text(encoding='utf-8')
            script = session.create_script(source)
            errors = []
            payloads = []
            def message(value, data):
                events.write(json.dumps(value, ensure_ascii=False) + '\n')
                events.flush()
                if value['type'] == 'error':
                    errors.append(value)
                elif value['type'] == 'send':
                    payloads.append(value['payload'])
            script.on('message', message)
            script.load()
            gate.write_text('start', encoding='utf-8')
            if args.idle_copy_probe:
                deadline = time.monotonic() + 100
                while not gate.with_suffix('.paused').exists():
                    if time.monotonic() > deadline or host.poll() is not None:
                        raise TimeoutError('暂停复制探针未就绪')
                    time.sleep(.05)
                replay = script.exports_sync.replaycopy()
                args.output.with_suffix('.copy-replay.json').write_text(
                    json.dumps(replay, ensure_ascii=False, indent=2), encoding='utf-8')
                gate.with_suffix('.copy-done').write_text('done', encoding='utf-8')
            host.wait(timeout=110)
            if host.returncode:
                raise RuntimeError('插桩播放失败，详见host日志')
            if errors:
                raise RuntimeError('插桩脚本报错，不能采用此次结果')
            if args.separate_surfaces and not any(x.get('separate_surface_count')==22 for x in payloads):
                raise RuntimeError('独立纹理实验没有生效，不能采用此次结果')
            if args.video_queue_limit and json.loads(args.output.read_text(encoding='utf-8')).get('budget_patch',{}).get('queue_limit') != args.video_queue_limit:
                raise RuntimeError('解码帧队列实验没有生效，不能采用此次结果')
            calls = [call for payload in payloads for call in payload.get('calls', [])]
            for enabled, name in [(args.early_copy, 'EarlyCopy'), (args.wait_copy, 'CopyCompletionWait'),
                                  (args.wait_decode, 'DecodeCompletionWait')]:
                if enabled and not any(call['name'] == name for call in calls):
                    raise RuntimeError(f'{name}实验没有生效，不能采用此次结果')
            args.output.with_suffix('.instrument.json').write_text(json.dumps({
                'frida_version': frida.__version__, 'command': command,
                'target_pid': target_pid, 'mpv': args.mpv,
                'skip_video_processor': args.skip_video_processor,
                'skip_draw': args.skip_draw, 'skip_copy': args.skip_copy,
                'copy_box': args.copy_box, 'device_latency': args.device_latency,
                'shader_texture_only': args.shader_texture_only, 'decoder_only': args.decoder_only,
                'pool_size': args.pool_size,
                'discard_copy': args.discard_copy,
                'separate_surfaces': args.separate_surfaces,
                'flush_copy': args.flush_copy, 'flush_decode': args.flush_decode,
                'wait_copy': args.wait_copy,
                'idle_copy_probe': args.idle_copy_probe,
                'wait_decode': args.wait_decode,
                'early_copy': args.early_copy,
                'no_profile': args.no_profile, 'device_flags': args.device_flags,
                'amd_metrics': args.amd_metrics,
                'gpu_priority': args.gpu_priority,
                'decode_interval_ms': args.decode_interval_ms,
                'release_after_copy': args.release_after_copy,
                'video_queue_limit': args.video_queue_limit,
                'script_sha256': hashlib.sha256(source.encode('utf-8')).hexdigest(),
                'host_exit': host.returncode}, ensure_ascii=False, indent=2), encoding='utf-8')
            print(args.output)
        finally:
            if session:
                try:
                    session.detach()
                except frida.InvalidOperationError:
                    pass
            if host.poll() is None:
                host.kill()
                host.wait()


if __name__ == '__main__':
    main()
