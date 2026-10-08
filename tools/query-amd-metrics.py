"""读取本机AMD驱动ADL传感器；不调用任何调频、调压或设置接口。"""
import ctypes as C
import json


class Adapter(C.Structure):
    _fields_ = [('size', C.c_int), ('index', C.c_int), ('udid', C.c_char * 256),
        ('bus', C.c_int), ('device', C.c_int), ('function', C.c_int), ('vendor', C.c_int),
        ('name', C.c_char * 256), ('display', C.c_char * 256), ('present', C.c_int),
        ('exists', C.c_int), ('path', C.c_char * 256), ('path_ext', C.c_char * 256),
        ('pnp', C.c_char * 256), ('display_index', C.c_int)]


class Sensor(C.Structure):
    _fields_ = [('supported', C.c_int), ('value', C.c_int)]


class PMLog(C.Structure):
    _fields_ = [('size', C.c_int), ('sensors', Sensor * 256)]


class PerformanceStatus(C.Structure):
    _fields_ = [(name, C.c_int) for name in ['core_clock', 'memory_clock', 'dcef_clock',
        'gfx_clock', 'uvd_clock', 'vce_clock', 'gpu_activity', 'core_level', 'memory_level',
        'dcef_level', 'gfx_level', 'uvd_level', 'vce_level', 'bus_speed', 'bus_lanes',
        'max_bus_lanes', 'vddc', 'vddci']]


class SensorSupport(C.Structure):
    _fields_ = [('sensors', C.c_ushort * 256), ('reserved', C.c_int * 16)]


SENSOR_NAMES = {1: 'gfx_mhz', 2: 'memory_mhz', 3: 'soc_mhz', 4: 'uvd1_mhz',
    5: 'uvd2_mhz', 6: 'vce_mhz', 7: 'vcn_mhz', 8: 'edge_c', 19: 'gfx_activity_percent',
    20: 'memory_activity_percent', 23: 'asic_power', 27: 'hotspot_c', 35: 'throttler_status',
    36: 'vcn1_mhz', 37: 'vcn2_mhz', 40: 'bus_speed', 41: 'bus_lanes', 44: 'fclk_mhz'}


class AMDReader:
    def __init__(self):
        # ABI字段和传感器编号依据AMD官方ADL 18.1公开接口，非复制SDK源码。
        self.context = C.c_void_p()
        self.dll = C.CDLL('C:/Windows/System32/atiadlxx.dll')
        self.crt = C.CDLL('msvcrt')
        self.crt.malloc.argtypes, self.crt.malloc.restype = [C.c_size_t], C.c_void_p
        self.callback_type = C.CFUNCTYPE(C.c_void_p, C.c_int)
        self.callback = self.callback_type(lambda size: self.crt.malloc(size))
        create = self.bind('ADL2_Main_Control_Create', [self.callback_type, C.c_int, C.POINTER(C.c_void_p)])
        status = create(self.callback, 1, C.byref(self.context))
        if status != 0:
            raise RuntimeError(f'ADL初始化失败：{status}')
        try:
            count = C.c_int()
            status = self.bind('ADL2_Adapter_NumberOfAdapters_Get', [C.c_void_p, C.POINTER(C.c_int)])(
                self.context, C.byref(count))
            if status != 0 or not 0 < count.value < 128:
                raise RuntimeError(f'ADL适配器枚举失败：{status}')
            adapters = (Adapter * count.value)()
            for adapter in adapters:
                adapter.size = C.sizeof(Adapter)
            status = self.bind('ADL2_Adapter_AdapterInfo_Get', [C.c_void_p, C.POINTER(Adapter), C.c_int])(
                self.context, adapters, C.sizeof(adapters))
            if status != 0:
                raise RuntimeError(f'ADL适配器信息失败：{status}')
            self.adapters = []
            seen = set()
            for adapter in adapters:
                key = (adapter.bus, adapter.device, adapter.function)
                if adapter.present and 'RX 6600' in adapter.name.decode('ascii', errors='replace') and key not in seen:
                    seen.add(key)
                    self.adapters.append({'index': adapter.index, 'name': adapter.name.decode('ascii'),
                        'pci': key})
            if not self.adapters:
                raise RuntimeError('未找到本次验证的RX6600适配器')
            self.query = self.bind('ADL2_New_QueryPMLogData_Get', [C.c_void_p, C.c_int, C.POINTER(PMLog)])
            self.performance = self.bind('ADL2_OverdriveN_PerformanceStatus_Get',
                [C.c_void_p, C.c_int, C.POINTER(PerformanceStatus)])
            self.support = self.bind('ADL2_Adapter_PMLog_Support_Get',
                [C.c_void_p, C.c_int, C.POINTER(SensorSupport)])
            for adapter in self.adapters:
                support = SensorSupport()
                adapter['support_status'] = self.support(self.context, adapter['index'], C.byref(support))
                adapter['supported_sensor_ids'] = [i for i in support.sensors if i] if adapter['support_status'] == 0 else None
        except Exception:
            self.close()
            raise

    def bind(self, name, types):
        function = getattr(self.dll, name)
        function.argtypes, function.restype = types, C.c_int
        return function

    def read(self):
        result = []
        for adapter in self.adapters:
            data = PMLog()
            data.size = C.sizeof(data)
            status = self.query(self.context, adapter['index'], C.byref(data))
            performance = PerformanceStatus()
            performance_status = self.performance(self.context, adapter['index'], C.byref(performance))
            result.append({**adapter, 'status': status, 'values': {
                SENSOR_NAMES.get(i, f'sensor_{i}'): sensor.value
                for i, sensor in enumerate(data.sensors) if status == 0 and sensor.supported},
                'odn_status': performance_status,
                # 旧接口无逐传感器支持位，保留原始单位；0不能作为媒体时钟已读取的证据。
                'odn_raw': {name: getattr(performance, name) for name, _ in performance._fields_}
                    if performance_status == 0 else None})
        return result

    def close(self):
        if self.context:
            self.bind('ADL2_Main_Control_Destroy', [C.c_void_p])(self.context)
            self.context = C.c_void_p()


if __name__ == '__main__':
    reader = AMDReader()
    try:
        print(json.dumps(reader.read(), ensure_ascii=False, indent=2))
    finally:
        reader.close()
