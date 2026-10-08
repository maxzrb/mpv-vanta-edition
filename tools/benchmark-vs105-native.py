"""用独立可见窗口测试用户提供的 VS 1.0.5 内核；不操作播放器界面。"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import importlib.util
import json
import os
from pathlib import Path
import time
import re
import runpy
import hashlib


def gpu_engines(counter, pid):
    """按进程与引擎名称读取 PDH，避免混入桌面和其它程序。"""
    counter.pdh.PdhCollectQueryData(counter.query)
    size, count = W.DWORD(), W.DWORD()
    counter.pdh.PdhGetFormattedCounterArrayA(counter.counter, 0x200, C.byref(size), C.byref(count), None)
    if not size.value:
        return {}
    buffer = C.create_string_buffer(size.value)
    if counter.pdh.PdhGetFormattedCounterArrayA(counter.counter, 0x200, C.byref(size), C.byref(count), buffer):
        return {}
    items = C.cast(buffer, C.POINTER(counter.Item))
    result = {}
    for index in range(count.value):
        item = items[index]
        name = (item.name or b'').decode('ascii', errors='replace')
        match = re.search(r'engtype_(.*)', name)
        if name.startswith(f'pid_{pid}_') and match and item.value.status <= 1:
            key = match[1]
            result[key] = result.get(key, 0) + max(0, item.value.data.number)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    parser.add_argument('media', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--abi', type=Path, default=Path(__file__).with_name('benchmark-vs105-abi.py'))
    parser.add_argument('--mode', type=int, choices=[1, 2], default=2)
    parser.add_argument('--algorithm', type=int, default=1284)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--tearing', action='store_true')
    parser.add_argument('--pacing', action='store_true')
    parser.add_argument('--width', type=int, default=1280)
    parser.add_argument('--height', type=int, default=720)
    parser.add_argument('--quality', type=int, choices=[0, 1], default=1)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--start-gate', type=Path)
    parser.add_argument('--idle-copy-probe', action='store_true')
    parser.add_argument('--amd-metrics', action='store_true')
    parser.add_argument('--warm-position', type=int, choices=[15,20], default=15)
    parser.add_argument('--seek-cycle', action='store_true')
    parser.add_argument('--video-queue-limit', type=int, choices=[0,4,8], default=0)
    args = parser.parse_args()
    if args.seek_cycle and args.seconds < 20:
        raise ValueError('跳转回归至少观察20秒')
    if args.start_gate:
        # 外部采集器先建立独立会话，再允许创建D3D设备，保留完整事件关联。
        args.start_gate.parent.mkdir(parents=True, exist_ok=True)
        args.start_gate.with_suffix('.ready.json').write_text(
            json.dumps({'pid': os.getpid()}), encoding='utf-8')
        deadline = time.monotonic() + 60
        while not args.start_gate.exists():
            if time.monotonic() > deadline:
                raise TimeoutError('等待采集器启动超时')
            time.sleep(.02)
    spec = importlib.util.spec_from_file_location('vs_abi', args.abi)
    abi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(abi)
    user = C.WinDLL('user32', use_last_error=True)
    kernel = C.WinDLL('kernel32', use_last_error=True)
    user.SetProcessDpiAwarenessContext.argtypes = [C.c_void_p]
    user.SetProcessDpiAwarenessContext(C.c_void_p(-4))
    user.CreateWindowExW.restype = W.HWND
    user.CreateWindowExW.argtypes = [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD,
                                   C.c_int, C.c_int, C.c_int, C.c_int,
                                   W.HWND, W.HMENU, W.HINSTANCE, C.c_void_p]
    user.DestroyWindow.argtypes = [W.HWND]
    user.SetWindowPos.argtypes = [W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT]
    user.GetClientRect.argtypes = [W.HWND, C.POINTER(W.RECT)]
    kernel.GetModuleHandleW.restype = W.HMODULE
    window = user.CreateWindowExW(0, 'STATIC', 'VS 1.0.5 native performance test',
                                 0x80000000 if args.headless else 0x90000000,
                                 0, 0, args.width, args.height,
                                 None, None, kernel.GetModuleHandleW(None), None)
    if not window:
        raise C.WinError(C.get_last_error())
    # 测试窗口置顶，避免被聊天窗口遮挡后 DXGI 节流污染结果。
    if not args.headless:
        user.SetWindowPos(window, W.HWND(-1), 0, 0, 0, 0, 0x13)
    directories = [os.add_dll_directory(str(args.package.resolve()))]
    dll = C.CDLL(str((args.package / 'FFF.Native.dll').resolve()))
    budget_patch = None
    if args.video_queue_limit:
        # 仅限固定DLL的本进程实验；改变预算常量，磁盘文件和像素处理代码不变。
        expected = '094c19e0658235dafa0c5b5d46e59c211c9390632c71794aad45e4dcfe95de50'
        if hashlib.sha256((args.package/'FFF.Native.dll').read_bytes()).hexdigest()!=expected:
            raise RuntimeError('队列实验仅支持已核验DLL')
        address=dll._handle+0x93ba
        if C.string_at(address,5)!=bytes.fromhex('b800000008'):
            raise RuntimeError('队列预算指令不匹配')
        protect=kernel.VirtualProtect
        protect.argtypes=[C.c_void_p,C.c_size_t,W.DWORD,C.POINTER(W.DWORD)]
        protect.restype=W.BOOL
        previous=W.DWORD()
        if not protect(address+1,4,0x40,C.byref(previous)):
            raise C.WinError(C.get_last_error())
        budget=args.video_queue_limit*7680*4320*3
        try:
            C.memmove(address+1,budget.to_bytes(4,'little'),4)
        finally:
            restored=W.DWORD()
            if not protect(address+1,4,previous.value,C.byref(restored)):
                raise C.WinError(C.get_last_error())
        kernel.GetCurrentProcess.restype=W.HANDLE
        kernel.FlushInstructionCache.argtypes=[W.HANDLE,C.c_void_p,C.c_size_t]
        if not kernel.FlushInstructionCache(kernel.GetCurrentProcess(),address,5):
            raise C.WinError(C.get_last_error())
        budget_patch={'queue_limit':args.video_queue_limit,'budget_bytes':budget,'rva':0x93ba,
            'dll_sha256':expected,'original_budget_bytes':128*1024*1024}
    def bind(name, types, result=C.c_int32):
        function = getattr(dll, 'FFF3FP_' + name)
        function.argtypes, function.restype = types, result
        return function
    version = bind('GetApiVersion', [], C.c_uint32)()
    if version != 16:
        user.DestroyWindow(window)
        raise RuntimeError(f'本探针只核对了 1.0.5 的 API 16，实际为 {version}')
    create = bind('Create', [C.POINTER(abi.ThreeFpConfiguration), C.POINTER(C.c_void_p)])
    snapshot = bind('GetSnapshot', [C.c_void_p, C.POINTER(abi.ThreeFpSnapshot)])
    open_file = bind('Open', [C.c_void_p, C.c_char_p])
    play = bind('Play', [C.c_void_p])
    seek = bind('Seek', [C.c_void_p, C.c_int64])
    destroy = bind('Destroy', [C.c_void_p], None)
    volume = bind('SetVolume', [C.c_void_p, C.c_float, C.c_uint32])
    algorithms = bind('SetScalingAlgorithms', [C.c_void_p, C.c_uint32, C.c_uint32])
    log_callback = C.CFUNCTYPE(None, C.c_void_p, C.c_char_p)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    log = args.output.with_suffix('.log').open('w', encoding='utf-8')
    @log_callback
    def log_line(context, line):
        if line:
            log.write(line.decode('utf-8', errors='replace') + '\n')
            log.flush()
    bind('SetLogCallback', [log_callback, C.c_void_p], None)(log_line, None)
    config = abi.ThreeFpConfiguration()
    config.size, config.version = C.sizeof(config), version
    config.outputWindow, config.decodeMode = None if args.headless else window, args.mode
    config.sdrPeakNits, config.hdrPeakNits, config.sdrPaperWhiteNits = 100, 1000, 203
    config.videoScalingQuality, config.preferredAdapterIndex = args.quality, -1
    handle = C.c_void_p()
    def check(result):
        if result != 0:
            raise RuntimeError('3FP API returned ' + str(result))
    rows = []
    amd = None
    common = runpy.run_path(str(Path(__file__).with_name('validate-modernization.py')))
    try:
        gpu = common['GPUCounter']()
    except Exception:
        gpu = None
    started = time.monotonic()
    # 只处理探针自己的消息队列，不向其他窗口发送输入。
    def pump():
        message = W.MSG()
        while user.PeekMessageW(C.byref(message), None, 0, 0, 1):
            user.TranslateMessage(C.byref(message))
            user.DispatchMessageW(C.byref(message))
        rect = W.RECT()
        if not user.GetClientRect(window, C.byref(rect)) or (rect.right, rect.bottom) != (args.width, args.height):
            raise RuntimeError('测试窗口大小发生改变')
    def read():
        pump()
        s = abi.ThreeFpSnapshot()
        s.size, s.version = C.sizeof(s), 8
        check(snapshot(handle, C.byref(s)))
        if s.state == 6:
            raise RuntimeError('3FP 播放失败，详见日志')
        row = {name: getattr(s, name) for name, _ in s._fields_}
        return row
    try:
        if args.amd_metrics:
            amd = runpy.run_path(str(Path(__file__).with_name('query-amd-metrics.py')))['AMDReader']()
        check(create(C.byref(config), C.byref(handle)))
        check(volume(handle, 1, 1))
        if args.tearing:
            check(bind('SetPresentConfig', [C.c_void_p, C.c_uint32])(handle, 1))
        if args.pacing:
            check(bind('SetPacingConfig', [C.c_void_p, C.c_uint32])(handle, 1))
        check(algorithms(handle, args.algorithm, args.algorithm & 255))
        check(open_file(handle, str(args.media.resolve()).encode('utf-8')))
        while read()['state'] != 2:
            if time.monotonic() - started > 30:
                raise TimeoutError('等待打开超时')
            time.sleep(.01)
        check(seek(handle, 100000000))
        check(play(handle))
        while read()['position100ns'] < args.warm_position * 10000000:
            if time.monotonic() - started > 60:
                raise TimeoutError('等待预热超时')
            time.sleep(.01)
        measurement = time.monotonic()
        control_events = []
        seek_requested = False
        qpc_frequency = C.c_int64()
        kernel.QueryPerformanceFrequency(C.byref(qpc_frequency))
        kernel.GetCurrentProcess.restype = W.HANDLE
        kernel.GetProcessTimes.argtypes = [W.HANDLE, *([C.POINTER(W.FILETIME)] * 4)]
        while True:
            row = read()
            row['wall'] = time.monotonic() - measurement
            qpc = C.c_int64()
            kernel.QueryPerformanceCounter(C.byref(qpc))
            row['qpc'] = qpc.value
            if amd:
                row['amd_metrics'] = amd.read()
            times = [W.FILETIME() for _ in range(4)]
            kernel.GetProcessTimes(kernel.GetCurrentProcess(), *(C.byref(t) for t in times))
            row['cpu_s'] = sum((t.dwHighDateTime << 32) + t.dwLowDateTime for t in times[2:]) / 1e7
            row['gpu_engines'] = gpu_engines(gpu, os.getpid()) if gpu else None
            # 前缀 ABI 来自原生探针；版本 1 可读取交换链和实际目标尺寸。
            class Target(C.Structure):
                _fields_ = [(name, C.c_uint32) for name in ['size', 'version', 'swapWidth',
                    'swapHeight', 'clientWidth', 'clientHeight', 'destX', 'destY',
                    'destWidth', 'destHeight', 'outputBitDepth', 'hdr']]
            target = Target()
            target.size, target.version = C.sizeof(target), 1
            target_result = bind('GetRenderTargetInfo', [C.c_void_p, C.POINTER(Target)])(handle, C.byref(target))
            row['render_target'] = {name: getattr(target, name) for name, _ in target._fields_} if target_result == 0 else None
            row['seek_phase'] = 1 if seek_requested else 0
            rows.append(row)
            if args.seek_cycle and not seek_requested and row['wall'] >= 6:
                check(seek(handle,600000000))
                seek_requested=True
                control_events.append({'kind':'seek','target100ns':600000000,'qpc':row['qpc'],'wall':row['wall']})
            if row['wall'] >= args.seconds:
                break
            until = time.monotonic() + 1
            while time.monotonic() < until:
                pump()
                time.sleep(.005)
        args.output.write_text(json.dumps({'api_version': version, 'config_size': C.sizeof(config),
            'snapshot_size': C.sizeof(abi.ThreeFpSnapshot), 'mode': args.mode,
            'algorithm': args.algorithm, 'tearing': args.tearing, 'pacing': args.pacing,
            'quality': args.quality, 'headless': args.headless, 'qpc_frequency': qpc_frequency.value,
            'warm_position': args.warm_position, 'budget_patch':budget_patch, 'control_events':control_events,
            'window': [args.width, args.height], 'rows': rows}, indent=2), encoding='utf-8')
        print(args.output)
        if args.idle_copy_probe:
            # 稳定段之后暂停并等待独立复制探针，不混入播放性能统计。
            check(bind('Pause', [C.c_void_p])(handle))
            time.sleep(1)
            before = read()
            args.start_gate.with_suffix('.paused').write_text('ready', encoding='utf-8')
            deadline = time.monotonic() + 45
            while not args.start_gate.with_suffix('.copy-done').exists():
                if time.monotonic() > deadline:
                    raise TimeoutError('暂停复制探针未完成')
                pump()
                time.sleep(.02)
            after = read()
            args.output.with_suffix('.idle.json').write_text(json.dumps({
                'before': before, 'after': after}, indent=2), encoding='utf-8')
    finally:
        if amd:
            amd.close()
        if handle:
            destroy(handle)
        user.DestroyWindow(window)
        if gpu:
            gpu.close()
        log.close()
        for directory in directories:
            directory.close()


if __name__ == '__main__':
    main()
