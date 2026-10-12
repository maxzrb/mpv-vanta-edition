"""仅对自有诊断进程读取 Vulkan FP16／RGB10 交换链，非日常播放依赖。"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
api = runpy.run_path(str(ROOT / 'tools/gpu-readback.py'))


class Probe(api['Probe']):
    def attach(self, process):
        # 复用维护诊断依赖；不改播放器 Python 组件，不附加到用户播放进程。
        sys.path.insert(0, str(ROOT / 'tmp/modernization/vs105-instrument/deps'))
        import frida
        self.session = frida.attach(process.pid)
        source = Path(__file__).with_suffix('.js').read_text(encoding='utf-8')
        self.script = self.session.create_script(source)
        self.script.on('message', self.message)
        self.script.load()


def create_player(args, name, executable=None):
    probe = Probe()
    try:
        player = api['Player'](args, name, before_resume=probe.attach, executable=executable)
        return player, probe
    except BaseException:
        probe.close()
        raise
