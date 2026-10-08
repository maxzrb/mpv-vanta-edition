"""只对本工具启动的诊断 mpv 读取原始交换链像素，不参与日常播放。"""
import ctypes
import queue
import runpy
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']


class Probe:
    def __init__(self):
        self.session = self.script = None
        self.results = queue.Queue()
        self.counter = 0

    def attach(self, process):
        # 复用忽略目录中的维护依赖，不改播放器 Python 组件。
        sys.path.insert(0, str(ROOT / 'tmp/modernization/vs105-instrument/deps'))
        import frida
        self.session = frida.attach(process.pid)
        self.script = self.session.create_script(Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))
        self.script.on('message', self.message)
        self.script.load()

    def message(self, message, data):
        if message['type'] == 'error':
            self.results.put(({'error': message.get('stack', str(message))}, None))
        elif message['type'] == 'send' and 'capture' in message['payload']:
            self.results.put((message['payload'], data))

    def read(self, player, timeout=10):
        self.counter += 1
        self.script.exports_sync.arm(self.counter)
        paused = player.get('pause')
        player.command('set_property', 'pause', False)
        # 静态图片可能停止呈现；同位置重解码只用于触发诊断帧，像素内容保持原样。
        if any(t.get('image') and t.get('selected') for t in player.get('track-list') or []):
            player.command('seek', player.get('time-pos') or 0, 'absolute+exact')
        try:
            try:
                meta, data = self.results.get(timeout=timeout)
            except queue.Empty:
                raise RuntimeError('GPU 读回未收到呈现：' + str(self.script.exports_sync.status())) from None
            if 'error' in meta:
                raise RuntimeError(meta['error'])
            assert meta['capture'] == self.counter
            return Frame(meta, data)
        finally:
            player.command('set_property', 'pause', paused)

    def close(self):
        if self.session:
            try:
                self.session.detach()
            except Exception:
                pass


class Frame:
    def __init__(self, metadata, data):
        self.meta, self.data = metadata, data

    def pixel(self, x, y):
        m = self.meta
        assert 0 <= x < m['width'] and 0 <= y < m['height']
        offset = y * m['stride'] + x * (8 if m['format'] == 10 else 4)
        if m['format'] == 10:
            return struct.unpack_from('<4e', self.data, offset)
        if m['format'] == 24:
            code = struct.unpack_from('<I', self.data, offset)[0]
            return tuple(((code >> shift) & 1023) / 1023 for shift in (0, 10, 20)) + ((code >> 30) / 3,)
        rgba = tuple(v / 255 for v in self.data[offset:offset + 4])
        return (rgba[2], rgba[1], rgba[0], rgba[3]) if m['format'] == 87 else rgba


def create_player(args, name, executable=None):
    probe = Probe()
    try:
        player = Player(args, name, before_resume=probe.attach, executable=executable)
        return player, probe
    except BaseException:
        probe.close()
        raise
