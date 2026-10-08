"""配置自己创建的VantaGPU会话事件过滤，保留校准、上下文、包和栅栏。"""
import ctypes as C
import uuid


class WNode(C.Structure):
    _fields_ = [('size', C.c_uint), ('provider', C.c_uint), ('handle', C.c_ulonglong),
        ('timestamp', C.c_ulonglong), ('guid', C.c_ubyte * 16), ('clock', C.c_uint), ('flags', C.c_uint)]


class Properties(C.Structure):
    _fields_ = [('wnode', WNode), ('values', C.c_uint * 14), ('thread', C.c_void_p),
        ('name_offset', C.c_uint), ('file_offset', C.c_uint)]


class FilterDescriptor(C.Structure):
    _fields_ = [('pointer', C.c_ulonglong), ('size', C.c_uint), ('type', C.c_uint)]


class Parameters(C.Structure):
    _fields_ = [('version', C.c_uint), ('properties', C.c_uint), ('flags', C.c_uint),
        ('source', C.c_ubyte * 16), ('filters', C.POINTER(FilterDescriptor)), ('count', C.c_uint)]


EVENT_IDS = [27,28,30,31,174,175,176,177,178,179,180,262,294,295,462]


def session_handle(session):
    if not session.startswith('VantaGPU-'):
        raise ValueError('仅允许配置自己创建的VantaGPU会话')
    api = C.WinDLL('advapi32')
    data = C.create_string_buffer(C.sizeof(Properties) + 4096)
    properties = Properties.from_buffer(data)
    properties.wnode.size = len(data)
    properties.name_offset = C.sizeof(Properties)
    properties.file_offset = properties.name_offset + 2048
    query = api.ControlTraceW
    query.argtypes, query.restype = [C.c_ulonglong, C.c_wchar_p, C.c_void_p, C.c_uint], C.c_uint
    status = query(0, session, data, 0)
    if status or not properties.wnode.handle:
        raise RuntimeError(f'查询自己的ETW会话失败：{status}')
    return properties.wnode.handle


def configure(session, keyword):
    handle = session_handle(session)
    api = C.WinDLL('advapi32')
    event_filter = C.create_string_buffer(4 + 2 * len(EVENT_IDS))
    C.c_ubyte.from_buffer(event_filter, 0).value = 1
    C.c_ushort.from_buffer(event_filter, 2).value = len(EVENT_IDS)
    ids = (C.c_ushort * len(EVENT_IDS)).from_buffer(event_filter, 4)
    ids[:] = EVENT_IDS
    descriptor = FilterDescriptor(C.addressof(event_filter), len(event_filter), 0x80000200)
    parameters = Parameters()
    parameters.version, parameters.count = 2, 1
    parameters.filters = C.pointer(descriptor)
    provider = C.create_string_buffer(uuid.UUID('802ec45a-1e99-4b83-9920-87c98277ba9d').bytes_le, 16)
    enable = api.EnableTraceEx2
    enable.argtypes, enable.restype = [C.c_ulonglong, C.c_void_p, C.c_uint, C.c_ubyte,
        C.c_ulonglong, C.c_ulonglong, C.c_uint, C.POINTER(Parameters)], C.c_uint
    status = enable(handle, provider, 1, 5, keyword, 0, 1000, C.byref(parameters))
    if status:
        raise RuntimeError(f'过滤自己的ETW会话失败：{status}')
    return {'event_ids': EVENT_IDS, 'keywords': hex(keyword), 'status': status}
