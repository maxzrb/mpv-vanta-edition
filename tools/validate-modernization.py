"""用独立 IPC 会话验证实际播放、增强生命周期和统计开销。"""
import argparse
import json
from pathlib import Path
import queue
import subprocess
import threading
import time
import uuid
import ctypes
import os
from ctypes import wintypes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/validation'
OUT.mkdir(parents=True, exist_ok=True)


def process_cpu_seconds(process):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
    times = [wintypes.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(int(process._handle), *(ctypes.byref(t) for t in times)):
        raise ctypes.WinError(ctypes.get_last_error())
    return sum((t.dwHighDateTime << 32) + t.dwLowDateTime for t in times[2:]) / 1e7


class GPUCounter:
    """独立于 stats 的整机 GPU 计数器；两组测试使用相同采样开销。"""
    class ValueUnion(ctypes.Union):
        _fields_ = [('number', ctypes.c_double), ('integer', ctypes.c_longlong)]
    class Value(ctypes.Structure):
        pass
    class Item(ctypes.Structure):
        pass

    def __init__(self):
        if not hasattr(self.Value, '_fields_'):
            self.Value._fields_ = [('status', wintypes.DWORD), ('data', self.ValueUnion)]
            self.Item._fields_ = [('name', ctypes.c_char_p), ('value', self.Value)]
        self.pdh = ctypes.WinDLL('pdh')
        self.query, self.counter = ctypes.c_void_p(), ctypes.c_void_p()
        self.pdh.PdhOpenQueryA.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
        self.pdh.PdhAddEnglishCounterA.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
        self.pdh.PdhCollectQueryData.argtypes = [ctypes.c_void_p]
        self.pdh.PdhCloseQuery.argtypes = [ctypes.c_void_p]
        self.pdh.PdhGetFormattedCounterArrayA.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        assert self.pdh.PdhOpenQueryA(None, 0, ctypes.byref(self.query)) == 0
        assert self.pdh.PdhAddEnglishCounterA(self.query, b'\\GPU Engine(*)\\Utilization Percentage', 0, ctypes.byref(self.counter)) == 0
        self.pdh.PdhCollectQueryData(self.query)

    def sample(self):
        import re
        self.pdh.PdhCollectQueryData(self.query)
        size, count = wintypes.DWORD(), wintypes.DWORD()
        self.pdh.PdhGetFormattedCounterArrayA(self.counter, 0x200, ctypes.byref(size), ctypes.byref(count), None)
        if not size.value:
            return {}
        buffer = ctypes.create_string_buffer(size.value)
        if self.pdh.PdhGetFormattedCounterArrayA(self.counter, 0x200, ctypes.byref(size), ctypes.byref(count), buffer):
            return {}
        items = ctypes.cast(buffer, ctypes.POINTER(self.Item))
        engines, adapters = {}, {}
        for index in range(count.value):
            item = items[index]
            match = re.search(rb'luid_(.*?)_phys_(\d+)_eng_(\d+)', item.name or b'')
            if match and item.value.status <= 1:
                adapter = b'/'.join(match.groups()[:2]).decode()
                engine = adapter + '/' + match[3].decode()
                engines[engine] = min(100, engines.get(engine, 0) + max(0, item.value.data.number))
                adapters[adapter] = max(adapters.get(adapter, 0), engines[engine])
        return adapters

    def close(self):
        self.pdh.PdhCloseQuery(self.query)


class Player:
    def __init__(self, args, name, before_resume=None, executable=None):
        self.pipe_name = r'\\.\pipe\vanta-test-' + uuid.uuid4().hex
        self.log = OUT / (name + '.log')
        self.process = subprocess.Popen([str(executable or ROOT / 'mpv.exe'), *args,
                                         '--input-ipc-server=' + self.pipe_name,
                                         '--log-file=' + str(self.log), '--idle=yes', '--keep-open=yes',
                                         '--ontop=no', '--save-position-on-quit=no', '--save-watch-history=no'],
                                        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        creationflags=4 if before_resume else 0)
        if before_resume:
            try:
                before_resume(self.process)
                native = ctypes.WinDLL('ntdll')
                native.NtResumeProcess.argtypes = [wintypes.HANDLE]
                native.NtResumeProcess.restype = ctypes.c_long
                if native.NtResumeProcess(int(self.process._handle)) != 0:
                    raise RuntimeError('诊断播放器恢复失败')
            except BaseException:
                self.process.kill()
                self.process.wait()
                raise
        started = time.monotonic()
        while True:
            try:
                self.pipe = open(self.pipe_name, 'r+b', buffering=0)
                break
            except OSError:
                if self.process.poll() is not None or time.monotonic() - started > 15:
                    raise RuntimeError('播放器 IPC 启动失败：' + name)
                time.sleep(.1)
        self.request_id = 0
        self.ipc_timeout = 10
        self.response_buffer = b''
        # 先查看管道可读字节，保证初始化卡住时测试的 IPC 超时仍有效。
        import msvcrt
        self.pipe_handle = msvcrt.get_osfhandle(self.pipe.fileno())
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.PeekNamedPipe.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
            ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]

    def command(self, *args):
        self.request_id += 1
        self.pipe.write((json.dumps({'command': args, 'request_id': self.request_id}) + '\n').encode('utf-8'))
        deadline = time.monotonic() + self.ipc_timeout
        while time.monotonic() < deadline:
            if b'\n' not in self.response_buffer:
                available = wintypes.DWORD()
                if not self.kernel.PeekNamedPipe(self.pipe_handle, None, 0, None, ctypes.byref(available), None):
                    raise RuntimeError('IPC 已关闭')
                if not available.value:
                    time.sleep(.01)
                    continue
                self.response_buffer += self.pipe.read(available.value)
                continue
            line, self.response_buffer = self.response_buffer.split(b'\n', 1)
            data = json.loads(line)
            if data.get('request_id') == self.request_id:
                return data
        raise TimeoutError(args)

    def get(self, prop):
        return self.command('get_property', prop).get('data')

    def wait_video(self):
        started = time.monotonic()
        while time.monotonic() - started < 20:
            if self.get('video-params') and self.get('time-pos') is not None:
                return
            time.sleep(.1)
        raise RuntimeError('视频没有开始播放')

    def close(self):
        try:
            self.command('quit')
        except (OSError, queue.Empty, TimeoutError, RuntimeError):
            pass
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.pipe.close()


def color_tests():
    cases = [('sdr8', 'yuv420p', 'bt709', 'bt709', 'bt709'),
             ('sdr10', 'yuv420p10le', 'bt709', 'bt709', 'bt709'),
             ('wide-sdr', 'yuv420p10le', 'bt2020', 'bt709', 'bt2020nc'),
             ('hdr10', 'yuv420p10le', 'bt2020', 'smpte2084', 'bt2020nc'),
             ('hlg', 'yuv420p10le', 'bt2020', 'arib-std-b67', 'bt2020nc')]
    results = []
    for name, fmt, prim, transfer, matrix in cases:
        media = OUT / (name + '.mkv')
        encoder_colors = {'bt709': 'bt709', 'bt2020': 'bt2020', 'smpte2084': 'smpte2084', 'arib-std-b67': 'arib-std-b67'}
        params = 'log-level=error:colorprim=' + encoder_colors[prim] + ':transfer=' + encoder_colors[transfer] + ':colormatrix=' + matrix
        if name == 'hdr10':
            params += ':master-display=G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,50):max-cll=1000,400'
        subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                        '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=24', '-t', '6',
                        '-pix_fmt', fmt, '-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '20', '-x265-params', params, '-color_primaries', prim, '-color_trc', transfer,
                        '-colorspace', matrix, '-color_range', 'tv', str(media)], check=True, timeout=60)
        player = Player(['--config-dir=' + str(ROOT / 'portable_config'), '--ao=null', '--hwdec=no', str(media)], name)
        try:
            player.wait_video()
            time.sleep(1)
            data = {prop: player.get(prop) for prop in ['video-dec-params', 'video-params', 'video-target-params',
                    'display-swapchain', 'interpolation', 'deband', 'vf', 'glsl-shaders']}
            assert data['interpolation'] is False, data
            assert data['deband'] is False, data
            assert data['video-params']['primaries'] == ('bt.709' if prim == 'bt709' else 'bt.2020'), data
            assert data['video-params']['gamma'] == {'bt709': 'bt.1886', 'smpte2084': 'pq', 'arib-std-b67': 'hlg'}[transfer], data
            assert data['video-target-params']['primaries'] == 'bt.709', data
            assert data['video-target-params']['gamma'] == 'srgb', data
            player.command('script-message', 'quality-select', 'artcnn')
            time.sleep(.2)
            shaders = player.get('glsl-shaders')
            assert bool(shaders) == (name in ['sdr8', 'sdr10']), shaders
            # 清空必须保留由其他脚本或用户添加的滤镜。
            player.command('vf', 'add', '@test-external:lavfi=[hflip]')
            player.command('script-message', 'quality-reset')
            time.sleep(.2)
            assert any(f.get('label') == 'test-external' for f in player.get('vf')), player.get('vf')
            assert not player.get('glsl-shaders')
            player.command('script-message', 'show-quality-status')
            data['passed'] = True
            results.append({'case': name, 'data': data})
        finally:
            player.close()
        errors = [line for line in player.log.read_text(encoding='utf-8').splitlines() if '[e]' in line or '[f]' in line]
        assert not errors, errors
    return results


def stats_tests(duration):
    results = []
    for implementation, script in [('before', ROOT / 'backup/modernization-20261004/portable_config/scripts/stats.lua'),
                                   ('after', ROOT / 'portable_config/scripts/stats.lua')]:
        for mode in ['closed', 'first-open', 'repeat', 'persistent']:
            for trial in range(3):
                player = Player(['--no-config', '--config-dir=' + str(ROOT / 'portable_config'), '--vo=gpu-next',
                                 '--gpu-api=d3d11', '--ao=null', '--load-scripts=no', '--script=' + str(script),
                                 '--load-stats-overlay=no',
                                 '--script-opts=stats-persistent_overlay=yes',
                                 'av://lavfi:testsrc2=size=1280x720:rate=24'], f'stats-{implementation}-{mode}-{trial}')
                try:
                    player.wait_video()
                    time.sleep(.5)
                    start = {p: player.get(p) or 0 for p in ['frame-drop-count', 'mistimed-frame-count', 'vo-delayed-frame-count']}
                    begin = time.monotonic()
                    cpu_start = process_cpu_seconds(player.process)
                    gpu = GPUCounter()
                    gpu_samples = []
                    if mode != 'closed':
                        player.command('script-binding', 'stats/display-stats-toggle')
                    next_toggle = begin + .6
                    next_sample = begin + 1
                    while time.monotonic() - begin < duration:
                        if mode == 'repeat' and time.monotonic() >= next_toggle:
                            player.command('script-binding', 'stats/display-stats-toggle')
                            next_toggle += .6
                        if time.monotonic() >= next_sample:
                            gpu_samples.append(gpu.sample())
                            next_sample += 1
                        time.sleep(.1)
                    counters = {p: (player.get(p) or 0) - start[p] for p in start}
                    cpu_percent = 100 * (process_cpu_seconds(player.process) - cpu_start) / (time.monotonic() - begin) / os.cpu_count()
                    gpu.close()
                    passes = player.get('vo-passes')
                    pending = player.get('user-data/stats/system-pending')
                    queries = player.get('user-data/stats/subprocess-count')
                    if mode != 'closed' and player.get('user-data/stats/toggled'):
                        player.command('script-binding', 'stats/display-stats-toggle')
                    time.sleep(.2)
                    results.append({'implementation': implementation, 'mode': mode, 'trial': trial,
                                    'duration': duration, 'counters': counters, 'vo_passes': passes,
                                    'pending': pending, 'fallback_queries': queries,
                                    'mpv_cpu_percent': cpu_percent, 'system_gpu_samples': gpu_samples})
                finally:
                    player.close()
                text = player.log.read_text(encoding='utf-8')
                results[-1]['logged_subprocesses'] = text.count('Run command: subprocess,')
                errors = [line for line in text.splitlines() if '[e]' in line or '[f]' in line]
                results[-1]['provider_errors'] = [line for line in errors if 'Subprocess failed:' in line]
                assert not [line for line in errors if 'Subprocess failed:' not in line], errors
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stats', action='store_true')
    parser.add_argument('--duration', type=float, default=6)
    args = parser.parse_args()
    results = stats_tests(args.duration) if args.stats else color_tests()
    path = OUT / ('stats-results.json' if args.stats else 'color-results.json')
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS', len(results), path)


if __name__ == '__main__':
    main()
