"""只读枚举DxgKrnl事件描述，选择必要关键字以减少GPU追踪开销。"""
import ctypes as C
import json
import uuid


class Descriptor(C.Structure):
    _fields_ = [('id', C.c_ushort), ('version', C.c_ubyte), ('channel', C.c_ubyte),
        ('level', C.c_ubyte), ('opcode', C.c_ubyte), ('task', C.c_ushort), ('keyword', C.c_ulonglong)]


if __name__ == '__main__':
    provider = C.create_string_buffer(uuid.UUID('802ec45a-1e99-4b83-9920-87c98277ba9d').bytes_le, 16)
    tdh = C.WinDLL('tdh')
    call = tdh.TdhEnumerateManifestProviderEvents
    call.argtypes, call.restype = [C.c_void_p, C.c_void_p, C.POINTER(C.c_uint)], C.c_uint
    size = C.c_uint()
    status = call(provider, None, C.byref(size))
    if status != 122 or size.value < 24:
        raise RuntimeError(f'事件描述大小查询失败：{status}')
    data = C.create_string_buffer(size.value)
    status = call(provider, data, C.byref(size))
    if status:
        raise RuntimeError(f'事件描述查询失败：{status}')
    count = C.c_uint.from_buffer(data, 0).value
    if 8 + count * C.sizeof(Descriptor) > size.value:
        raise RuntimeError('事件描述数组超出已分配缓冲区')
    values = (Descriptor * count).from_buffer(data, 8)
    selected = {27,30,174,175,176,177,178,180,262,294,295}
    print(json.dumps([{**{name: getattr(d, name) for name, _ in d._fields_},
        'keyword': hex(d.keyword)} for d in values if d.id in selected], indent=2))
