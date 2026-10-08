"""维护者手动观察滤镜启停的进程GPU内存；缓存保留不直接判作泄漏。"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import runpy
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/filter-handoff'
helpers=runpy.run_path(str(ROOT/'tools/benchmark-filter-handoff.py'))
Player,enable,memory=helpers['Player'],helpers['enable'],helpers['memory']
create_config=helpers['create_config']


class GPUProcessMemory:
    class Value(ctypes.Structure):
        _fields_=[('status',wintypes.DWORD),('value',ctypes.c_double)]
    class Item(ctypes.Structure):
        pass

    def __init__(self,pid):
        if not hasattr(self.Item,'_fields_'):
            self.Item._fields_=[('name',ctypes.c_char_p),('value',self.Value)]
        self.pid=pid
        self.pdh=ctypes.WinDLL('pdh')
        self.pdh.PdhOpenQueryA.argtypes=[ctypes.c_char_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)]
        self.pdh.PdhAddEnglishCounterA.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)]
        self.pdh.PdhGetFormattedCounterArrayA.argtypes=[ctypes.c_void_p,wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]
        self.pdh.PdhCollectQueryData.argtypes=[ctypes.c_void_p]
        self.pdh.PdhCloseQuery.argtypes=[ctypes.c_void_p]
        self.query=ctypes.c_void_p()
        assert self.pdh.PdhOpenQueryA(None,0,ctypes.byref(self.query))==0
        self.counters={}
        for label,metric in [('dedicated_mb','Dedicated Usage'),('shared_mb','Shared Usage')]:
            counter=ctypes.c_void_p()
            path=('\\GPU Process Memory(*)\\'+metric).encode('ascii')
            if self.pdh.PdhAddEnglishCounterA(self.query,path,0,ctypes.byref(counter))==0:
                self.counters[label]=counter
        self.pdh.PdhCollectQueryData(self.query)

    def sample(self):
        self.pdh.PdhCollectQueryData(self.query)
        result={}
        for label,counter in self.counters.items():
            size,count=wintypes.DWORD(),wintypes.DWORD()
            self.pdh.PdhGetFormattedCounterArrayA(counter,0x200,ctypes.byref(size),ctypes.byref(count),None)
            if not size.value:continue
            buffer=ctypes.create_string_buffer(size.value)
            if self.pdh.PdhGetFormattedCounterArrayA(counter,0x200,ctypes.byref(size),ctypes.byref(count),buffer):continue
            items=ctypes.cast(buffer,ctypes.POINTER(self.Item))
            values=[items[i].value.value for i in range(count.value)
                    if (items[i].name or b'').startswith(('pid_'+str(self.pid)+'_').encode('ascii'))
                    and items[i].value.status<=1]
            if values:result[label]=sum(values)/1048576
        return result

    def close(self):
        self.pdh.PdhCloseQuery(self.query)


def main():
    rows=[]
    for preset,group in [('svp','memc'),('rife-dml-426','memc'),('ccd','denoise')]:
        p=Player(['--config-dir='+str(create_config('filter-memory')),
            '--hwdec=d3d11va','--ao=null','--geometry=1920x1080',
            '--input-cursor=no','--input-vo-keyboard=no','--input-media-keys=no',
            str(OUT/(preset+'.mkv'))],'filter-memory-'+preset)
        counter=GPUProcessMemory(p.process.pid)
        def capture(phase,cycle):
            time.sleep(1)
            rows.append(dict(preset=preset,phase=phase,cycle=cycle,
                             gpu_process_memory=counter.sample(),process_memory=memory(p.process)))
        try:
            p.wait_video();capture('before',0)
            for cycle in range(1,4):
                enable(p,preset,group);capture('on',cycle)
                p.command('script-message','quality-disable',group)
                helpers['wait'](p,lambda: not p.get('vf'))
                capture('off',cycle)
            assert p.get('hwdec-current')=='d3d11va'
        finally:
            p.close();time.sleep(1)
            rows.append(dict(preset=preset,phase='exit',gpu_process_memory=counter.sample()))
            counter.close()
        print('PASS',preset,'三次实际启停GPU内存采样',flush=True)
    (OUT/'gpu-memory.json').write_text(json.dumps(dict(
        scope='进程PDH GPU内存计数，未采样或不存在实例时为空；缓存保留不等同泄漏',
        observations=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
