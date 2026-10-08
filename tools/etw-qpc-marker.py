"""在自己的ETW提供者写入QPC标记，并记录调用前后边界。"""
import ctypes as C
import uuid


class Marker:
    def __init__(self):
        self.guid = str(uuid.uuid4())
        self.provider = C.create_string_buffer(uuid.UUID(self.guid).bytes_le, 16)
        self.handle = C.c_ulonglong()
        self.api = C.WinDLL('advapi32')
        self.clock = C.WinDLL('kernel32').QueryPerformanceCounter
        self.clock.argtypes = [C.POINTER(C.c_longlong)]
        register = self.api.EventRegister
        register.argtypes, register.restype = [C.c_void_p, C.c_void_p, C.c_void_p,
            C.POINTER(C.c_ulonglong)], C.c_uint
        status = register(self.provider, None, None, C.byref(self.handle))
        if status:
            raise RuntimeError(f'自己的ETW提供者注册失败：{status}')
        self.write = self.api.EventWriteString
        self.write.argtypes, self.write.restype = [C.c_ulonglong, C.c_ubyte,
            C.c_ulonglong, C.c_wchar_p], C.c_uint

    def enable(self, session_handle):
        enable = self.api.EnableTraceEx2
        enable.argtypes, enable.restype = [C.c_ulonglong, C.c_void_p, C.c_uint, C.c_ubyte,
            C.c_ulonglong, C.c_ulonglong, C.c_uint, C.c_void_p], C.c_uint
        status = enable(session_handle, self.provider, 1, 5, 1, 0, 1000, None)
        if status:
            raise RuntimeError(f'自己的QPC提供者启用失败：{status}')

    def emit(self):
        nonce = 'VantaQpc-' + uuid.uuid4().hex
        before, after = C.c_longlong(), C.c_longlong()
        self.clock(C.byref(before))
        status = self.write(self.handle, 5, 1, nonce)
        self.clock(C.byref(after))
        if status:
            raise RuntimeError(f'QPC标记写入失败：{status}')
        if after.value - before.value > 10000:
            raise RuntimeError('QPC标记写入超过1ms，拒绝采用此时间锚')
        return {'nonce': nonce, 'qpc_before': before.value, 'qpc_after': after.value}

    def close(self):
        if self.handle.value:
            unregister = self.api.EventUnregister
            unregister.argtypes, unregister.restype = [C.c_ulonglong], C.c_uint
            unregister(self.handle)
            self.handle.value = 0
