"""按Windows实际CPU拓扑比较AV1调度，只约束测试播放器。"""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import runpy
import time

ROOT=Path(__file__).resolve().parents[1]
bench=runpy.run_path(str(ROOT/'tools/benchmark-av1-software.py'))
Player=bench['helper']['Player']
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.GetSystemCpuSetInformation.argtypes=[ctypes.c_void_p,wintypes.ULONG,ctypes.POINTER(wintypes.ULONG),wintypes.HANDLE,wintypes.ULONG]
kernel.SetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.c_size_t]
kernel.GetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
kernel.GetSystemTimes.argtypes=[ctypes.POINTER(wintypes.FILETIME)]*3


def system_busy():
    idle,kernel_time,user=[wintypes.FILETIME() for _ in range(3)]
    assert kernel.GetSystemTimes(ctypes.byref(idle),ctypes.byref(kernel_time),ctypes.byref(user))
    def seconds(value):return ((value.dwHighDateTime<<32)+value.dwLowDateTime)/1e7
    return seconds(kernel_time)+seconds(user)-seconds(idle)


def memory(process):
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD),
                  *[(name,ctypes.c_size_t) for name in ['peak_working_set','working_set','peak_paged','paged',
                                                       'peak_nonpaged','nonpaged','pagefile','peak_pagefile','private']]]
    psapi=ctypes.WinDLL('psapi',use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    counters=Counters();counters.cb=ctypes.sizeof(counters)
    assert psapi.GetProcessMemoryInfo(int(process._handle),ctypes.byref(counters),counters.cb)
    return {key:getattr(counters,key) for key in ['peak_working_set','working_set','private']}


def topology():
    size=wintypes.ULONG()
    kernel.GetSystemCpuSetInformation(None,0,ctypes.byref(size),None,0)
    buffer=ctypes.create_string_buffer(size.value)
    if not kernel.GetSystemCpuSetInformation(buffer,size.value,ctypes.byref(size),None,0):
        raise ctypes.WinError(ctypes.get_last_error())
    rows=[];offset=0
    while offset<size.value:
        raw=buffer.raw[offset:]
        length=int.from_bytes(raw[:4],'little')
        assert length>=8
        if int.from_bytes(raw[4:8],'little')==0:
            assert length>=24
            rows.append(dict(group=int.from_bytes(raw[12:14],'little'),logical=raw[14],
                             core=raw[15],efficiency=raw[18],flags=raw[19]))
        offset+=length
    assert {row['group'] for row in rows}=={0},'此实验仅用于单处理器组'
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('media',type=Path)
    parser.add_argument('--mode',choices=['decode','play'],default='decode')
    parser.add_argument('--cases',nargs='+',default=['all-t16','all-t8','p-t12','p-one-t6','all-one-t10'])
    parser.add_argument('--frames',type=int,default=288)
    parser.add_argument('--seconds',type=float,default=20)
    parser.add_argument('--rounds',type=int,default=2)
    parser.add_argument('--logo-mode',choices=['current','parallel','yaozhi','none'])
    parser.add_argument('--output',type=Path,default=ROOT/'tmp/modernization/av1-scheduling-20261008')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    cpus=topology()
    fast=max(row['efficiency'] for row in cpus)
    p=[row for row in cpus if row['efficiency']==fast]
    def one_per_core(rows):
        selected={}
        for row in rows:selected.setdefault(row['core'],row)
        return list(selected.values())
    groups={'all':cpus,'p':p,'p-one':one_per_core(p),'all-one':one_per_core(cpus)}
    rows=[]
    config=bench['create_config']('av1-scheduling',exclude_scripts=['window-size-position.lua']) if args.mode=='play' else None
    for trial in range(1,args.rounds+1):
        for name in (args.cases if trial%2 else list(reversed(args.cases))):
            scheduling_name,_,case_logo_mode=name.partition('@')
            logo_mode=case_logo_mode or args.logo_mode
            assert logo_mode in (None,'current','parallel','yaozhi','none')
            group,threads=scheduling_name.rsplit('-t',1)
            mask=sum(1<<row['logical'] for row in groups[group])
            def before_resume(process):
                if not kernel.SetProcessAffinityMask(int(process._handle),mask):
                    raise ctypes.WinError(ctypes.get_last_error())
                actual,system=ctypes.c_size_t(),ctypes.c_size_t()
                assert kernel.GetProcessAffinityMask(int(process._handle),ctypes.byref(actual),ctypes.byref(system))
                assert actual.value==mask
            # 使用同样的挂起启动，保证线程创建之前调度边界就已设置。
            probe={}
            class MeasuredPlayer(Player):
                def close(self):
                    elapsed=time.monotonic()-probe['start']
                    probe['background_busy_cores']=max(0,(system_busy()-probe['system_cpu']-bench['helper']['process_cpu_seconds'](self.process))/elapsed)
                    probe['memory']=memory(self.process)
                    super().close()
            def factory(options,log_name):
                probe.update(start=time.monotonic(),system_cpu=system_busy())
                if logo_mode:
                    options=[*options,'--script-opts-append=startup_format_logos-mode='+logo_mode]
                return MeasuredPlayer(options,log_name+'-'+group+'-'+(logo_mode or 'configured'),before_resume=before_resume)
            bench['helper']['Player']=factory
            print('RUN',args.mode,name,trial,hex(mask),flush=True)
            row=bench['decode'](args,int(threads),0) if args.mode=='decode' else bench['play'](args,config,'t'+threads+'-d0',trial)
            row.update(scheduling_case=name,trial=trial,affinity_mask=hex(mask),logical_processors=[r['logical'] for r in groups[group]])
            row.update(background_busy_cores=probe['background_busy_cores'],memory=probe['memory'])
            row['logo_mode']=logo_mode or 'configured'
            rows.append(row)
            result=dict(media=args.media.name,topology=cpus,rows=rows,
                        scope='只改测试进程CPU调度及解码线程；保留源分辨率、位深、解码处理；可见播放保留完整HQ／ACM／音频')
            (args.output/(args.mode+'-results.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
            print('RESULT',name,round(row['clock_ratio']*47.952,2),'fps',row.get('counters'),flush=True)


if __name__=='__main__':main()
