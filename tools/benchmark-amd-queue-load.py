"""用独立、限队列的计算工作量对照GPU频率；不调用调频或驱动设置接口。"""
import argparse
import ctypes as C
import json
from pathlib import Path
import subprocess
import sys
import time


def method(object, index, result, types):
    table = C.cast(object, C.POINTER(C.POINTER(C.c_void_p))).contents
    return C.WINFUNCTYPE(result, C.c_void_p, *types)(table[index])


def check(status):
    if status < 0:
        raise RuntimeError(f'D3D11探针失败：0x{status & 0xffffffff:08x}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('package', type=Path)
    parser.add_argument('media', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--groups', type=int, choices=[2048, 8192, 32768], default=8192)
    parser.add_argument('--algorithm', type=int, default=513)
    parser.add_argument('--iterations', type=int, choices=[256,1024,4096], default=256)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    d3d = C.WinDLL('d3d11')
    compiler = C.WinDLL('d3dcompiler_47')
    device, context, level = C.c_void_p(), C.c_void_p(), C.c_uint()
    create = d3d.D3D11CreateDevice
    create.argtypes = [C.c_void_p, C.c_uint, C.c_void_p, C.c_uint, C.c_void_p,
        C.c_uint, C.c_uint, C.POINTER(C.c_void_p), C.POINTER(C.c_uint), C.POINTER(C.c_void_p)]
    create.restype = C.c_int32
    objects = []
    host = None
    started = time.monotonic()
    dispatches = 0
    try:
        check(create(None, 1, None, 0, None, 0, 7, C.byref(device), C.byref(level), C.byref(context)))
        objects += [device, context]
        # 独立结构化缓冲区，不读取播放器解码表面，不参与其栅栏和像素输出。
        source = b'''RWStructuredBuffer<uint> dst : register(u0);
        [numthreads(64,1,1)] void main(uint3 id : SV_DispatchThreadID) {
            uint v=id.x+1; [loop] for(uint i=0;i<256;i++)
                v=(v*1664525u+1013904223u)^(v>>13);
            dst[id.x]=v;
        }'''
        source = source.replace(b'i<256', f'i<{args.iterations}'.encode('ascii'))
        blob, errors = C.c_void_p(), C.c_void_p()
        compile_shader = compiler.D3DCompile
        compile_shader.argtypes = [C.c_char_p, C.c_size_t, C.c_char_p, C.c_void_p,
            C.c_void_p, C.c_char_p, C.c_char_p, C.c_uint, C.c_uint,
            C.POINTER(C.c_void_p), C.POINTER(C.c_void_p)]
        compile_shader.restype = C.c_int32
        status = compile_shader(source, len(source), b'queue-load', None, None,
            b'main', b'cs_5_0', 0x8000, 0, C.byref(blob), C.byref(errors))
        if errors:
            objects.append(errors)
        if blob:
            objects.append(blob)
        check(status)
        pointer = method(blob, 3, C.c_void_p, [])(blob)
        size = method(blob, 4, C.c_size_t, [])(blob)
        shader, buffer, view, query = (C.c_void_p() for _ in range(4))
        check(method(device, 18, C.c_int32, [C.c_void_p, C.c_size_t, C.c_void_p,
            C.POINTER(C.c_void_p)])(device, pointer, size, None, C.byref(shader)))
        objects.append(shader)
        definition = (C.c_uint * 6)(args.groups * 64 * 4, 0, 128, 0, 64, 4)
        check(method(device, 3, C.c_int32, [C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)])(
            device, definition, None, C.byref(buffer)))
        objects.append(buffer)
        descriptor = (C.c_uint * 5)(0, 1, 0, args.groups * 64, 0)
        check(method(device, 8, C.c_int32, [C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)])(
            device, buffer, descriptor, C.byref(view)))
        objects.append(view)
        query_descriptor = (C.c_uint * 2)(0, 0)
        check(method(device, 24, C.c_int32, [C.c_void_p, C.POINTER(C.c_void_p)])(
            device, query_descriptor, C.byref(query)))
        objects.append(query)
        method(context, 69, None, [C.c_void_p, C.c_void_p, C.c_uint])(context, shader, None, 0)
        method(context, 68, None, [C.c_uint, C.c_uint, C.c_void_p, C.c_void_p])(
            context, 0, 1, C.byref(view), None)
        dispatch = method(context, 41, None, [C.c_uint, C.c_uint, C.c_uint])
        end = method(context, 28, None, [C.c_void_p])
        flush = method(context, 111, None, [])
        get_data = method(context, 29, C.c_int32, [C.c_void_p, C.c_void_p, C.c_uint, C.c_uint])
        command = [sys.executable, str(Path(__file__).with_name('benchmark-vs105-native.py')),
            str(args.package), str(args.media), str(args.output), '--algorithm', str(args.algorithm),
            '--seconds', '20', '--amd-metrics']
        with args.output.with_suffix('.load-host.log').open('w', encoding='utf-8') as log:
            host = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            pending = False
            next_dispatch = time.monotonic()
            while host.poll() is None:
                if time.monotonic() - started > 110:
                    raise TimeoutError('GPU对照探针超时')
                if pending:
                    status = get_data(context, query, None, 0, 1)
                    check(status)
                    pending = status != 0
                if not pending and time.monotonic() >= next_dispatch:
                    dispatch(context, args.groups, 1, 1)
                    end(context, query)
                    flush(context)
                    dispatches += 1
                    pending = True
                    next_dispatch = time.monotonic() + 1 / 60
                time.sleep(.001)
        if host.returncode:
            raise RuntimeError('播放器对照失败，查看load-host日志')
        args.output.with_suffix('.load.json').write_text(json.dumps({
            'groups': args.groups, 'dispatches': dispatches, 'feature_level': level.value,
            'iterations': args.iterations,
            'elapsed_s': time.monotonic() - started, 'command': command,
            'host_exit': host.returncode, 'max_pending_dispatches': 1}, indent=2), encoding='utf-8')
        print(args.output)
    finally:
        if host and host.poll() is None:
            host.kill()
            host.wait()
        for object in reversed(objects):
            method(object, 2, C.c_uint, [])(object)


if __name__ == '__main__':
    main()
