"""只读查询活动显示适配器的WDDM引擎类型，供ETW节点编号解释。"""
import argparse
import ctypes as C
import json
from pathlib import Path
import re
import runpy
import time


class Luid(C.Structure):
    _fields_ = [('low', C.c_uint32), ('high', C.c_int32)]


class OpenAdapter(C.Structure):
    _fields_ = [('name', C.c_wchar * 32), ('handle', C.c_uint32),
                ('luid', Luid), ('source', C.c_uint32)]


class NodeData(C.Structure):
    _fields_ = [('engine', C.c_uint32), ('name', C.c_wchar * 32),
                ('flags', C.c_uint32), ('gpu_mmu', C.c_uint8), ('io_mmu', C.c_uint8)]


class Node(C.Structure):
    _fields_ = [('ordinal', C.c_uint32), ('data', NodeData)]


class Query(C.Structure):
    _fields_ = [('handle', C.c_uint32), ('kind', C.c_uint32),
                ('data', C.c_void_p), ('size', C.c_uint32)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--display', default=r'\\.\DISPLAY1')
    args = parser.parse_args()
    assert C.sizeof(OpenAdapter) == C.sizeof(Node) == 80
    dll = C.WinDLL('gdi32')
    opened = OpenAdapter()
    opened.name = args.display
    dll.D3DKMTOpenAdapterFromGdiDisplayName.argtypes = [C.POINTER(OpenAdapter)]
    dll.D3DKMTQueryAdapterInfo.argtypes = [C.POINTER(Query)]
    dll.D3DKMTCloseAdapter.argtypes = [C.POINTER(C.c_uint32)]
    result = dll.D3DKMTOpenAdapterFromGdiDisplayName(C.byref(opened))
    if result:
        raise RuntimeError(f'打开显示适配器失败：{result:#x}')
    names = ['Other', '3D', 'Video Decode', 'Video Encode', 'Video Processing',
             'Scene Assembly', 'Copy', 'Overlay', 'Crypto', 'Video Codec']
    nodes = []
    try:
        for index in range(32):
            node = Node()
            node.ordinal = index
            query = Query(opened.handle, 25, C.addressof(node), C.sizeof(node))
            result = dll.D3DKMTQueryAdapterInfo(C.byref(query))
            if result:
                break
            nodes.append({'node': index, 'engine': node.data.engine,
                'type': names[node.data.engine] if node.data.engine < len(names) else 'Unknown',
                'name': node.data.name, 'flags': node.data.flags})
    finally:
        dll.D3DKMTCloseAdapter(C.byref(C.c_uint32(opened.handle)))
    metadata_status = result
    if not nodes:
        # 驱动不接受NODEMETADATA查询时，用PDH实例中的引擎编号和标签作兼容回退。
        api = runpy.run_path(str(Path(__file__).with_name('validate-modernization.py')))
        counter = api['GPUCounter']()
        try:
            counter.pdh.PdhCollectQueryData(counter.query)
            time.sleep(.2)
            counter.pdh.PdhCollectQueryData(counter.query)
            size, count = C.c_uint32(), C.c_uint32()
            counter.pdh.PdhGetFormattedCounterArrayA(counter.counter, 0x200, C.byref(size), C.byref(count), None)
            buffer = C.create_string_buffer(size.value)
            if counter.pdh.PdhGetFormattedCounterArrayA(counter.counter, 0x200, C.byref(size), C.byref(count), buffer) == 0:
                items = C.cast(buffer, C.POINTER(counter.Item))
                values = {}
                for index in range(count.value):
                    name = (items[index].name or b'').decode('ascii', errors='replace')
                    match = re.search(r'luid_0x([0-9a-fA-F]+)_0x([0-9a-fA-F]+)_phys_0_eng_(\d+)_engtype_(.+)', name)
                    if match and int(match[1],16)==opened.luid.high and int(match[2],16)==opened.luid.low:
                        values[int(match[3])] = match[4]
                nodes = [{'node': index, 'type': name, 'source': 'PDH instance'} for index, name in sorted(values.items())]
        finally:
            counter.close()
    data = {'display': args.display, 'luid_low': opened.luid.low,
            'luid_high': opened.luid.high, 'metadata_status': hex(metadata_status & 0xffffffff), 'nodes': nodes}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
