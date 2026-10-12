"""逐绘制源／中间／输出读回，只附加本工具创建的隔离诊断进程。"""
import queue
import runpy
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
api=runpy.run_path(str(ROOT/'tools/gpu-readback.py'))


class Probe(api['Probe']):
    def __init__(self,backend='d3d11'):
        super().__init__();self.backend=backend

    def attach(self,process):
        sys.path.insert(0,str(ROOT/'tmp/modernization/vs105-instrument/deps'))
        import frida
        self.session=frida.attach(process.pid)
        if self.backend=='d3d11':source=(ROOT/'tools/gpu-pipeline-d3d11.js').read_text(encoding='utf-8')
        else:
            source=(ROOT/'tools/gpu-readback-vulkan.js').read_text(encoding='utf-8')
            source=source.replace('function watch(name,address)', 'function watchFinal(name,address)')
            source=source.replace('requested=null;capture(a[0],a[1],id);', 'requested=null;flushStages(a[0]);capture(a[0],a[1],id);')
            source+=(ROOT/'tools/gpu-pipeline-vulkan.js').read_text(encoding='utf-8')
        self.script=self.session.create_script(source)
        self.script.on('message',self.message);self.script.load()

    def read(self,player,timeout=20,force_redraw=False,advance_frame=False):
        assert not (advance_frame and force_redraw)
        brightness=player.get('brightness') if force_redraw else None
        if force_redraw:
            # 恒定硬解夹具的精确跳转可能命中渲染缓存；恢复原值时强制一次真正绘制。
            player.command('set_property','brightness',brightness+1 if brightness<100 else brightness-1)
            time.sleep(.1)
        self.counter+=1;self.script.exports_sync.arm(self.counter)
        if force_redraw:player.command('set_property','brightness',brightness)
        if advance_frame:
            # 动态峰值验收逐帧推进，避免精确跳转重置峰值IIR历史。
            player.command('frame-step')
        else:
            player.command('seek',player.get('time-pos') or 0,'absolute+exact')
        entries=[]
        deadline=time.monotonic()+timeout
        while True:
            try:meta,data=self.results.get(timeout=max(.001,deadline-time.monotonic()))
            except queue.Empty:raise RuntimeError(self.script.exports_sync.status()) from None
            if 'error' in meta:raise RuntimeError(meta)
            assert meta['capture']==self.counter
            if meta.get('done'):break
            if self.backend=='vulkan' and 'phase' not in meta:
                meta['phase']='present';entries.append((meta,bytes(data)));break
            entries.append((meta,bytes(data)))
        assert any(m['phase']=='output' for m,_ in entries),str([(m['phase'],m.get('format')) for m,_ in entries])+str(self.script.exports_sync.status())
        return entries


def create_player(args,name,backend='d3d11'):
    probe=Probe(backend)
    try:return api['Player'](args,name,before_resume=probe.attach),probe
    except BaseException:probe.close();raise
