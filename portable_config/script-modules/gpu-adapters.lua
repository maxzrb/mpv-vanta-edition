-- 通过 DXGI 的 LUID 匹配显卡名称，并查询驱动报告的显卡类型。
local ffi = require 'ffi'
local bit = require 'bit'
ffi.cdef[[
typedef struct { uint32_t low; int32_t high; } stats_gpu_luid;
typedef struct { uint32_t a; uint16_t b, c; uint8_t d[8]; } stats_gpu_guid;
typedef struct {
    uint16_t description[128]; uint32_t vendor, device, subsystem, revision;
    size_t video_memory, system_memory, shared_memory;
    stats_gpu_luid luid; uint32_t flags;
} stats_gpu_desc;
typedef struct { stats_gpu_luid luid; uint32_t adapter; } stats_gpu_open;
typedef struct { uint32_t adapter, type; void *data; uint32_t size; } stats_gpu_query;
typedef struct { uint32_t adapter; } stats_gpu_close;
int32_t __stdcall CreateDXGIFactory1(const stats_gpu_guid *, void **);
int32_t __stdcall D3DKMTOpenAdapterFromLuid(stats_gpu_open *);
int32_t __stdcall D3DKMTQueryAdapterInfo(stats_gpu_query *);
int32_t __stdcall D3DKMTCloseAdapter(const stats_gpu_close *);
int __stdcall WideCharToMultiByte(uint32_t, uint32_t, const uint16_t *, int, char *, int, const char *, int *);
]]
local dxgi, gdi, kernel = ffi.load('dxgi'), ffi.load('gdi32'), ffi.load('kernel32')
local M = {}
local function method(object, index, signature)
    return ffi.cast(signature, ffi.cast('void ***', object)[0][index])
end
local function release(object)
    method(object, 2, 'uint32_t (__stdcall *)(void *)')(object)
end
local function description(wide)
    local size = kernel.WideCharToMultiByte(65001, 0, wide, -1, nil, 0, nil, nil)
    if size <= 1 then return '未命名显卡' end
    local text = ffi.new('char[?]', size)
    kernel.WideCharToMultiByte(65001, 0, wide, -1, text, size, nil, nil)
    return ffi.string(text)
end
local function adapter_type(luid)
    local opened = ffi.new('stats_gpu_open')
    opened.luid = luid
    if gdi.D3DKMTOpenAdapterFromLuid(opened) ~= 0 then return nil end
    local value = ffi.new('uint32_t[1]')
    -- KMTQAITYPE_ADAPTERTYPE = 15，类型标志由 Windows 驱动提供。
    local query = ffi.new('stats_gpu_query', {opened.adapter, 15, value, ffi.sizeof(value)})
    local result = gdi.D3DKMTQueryAdapterInfo(query)
    gdi.D3DKMTCloseAdapter(ffi.new('stats_gpu_close', {opened.adapter}))
    return result == 0 and tonumber(value[0]) or nil
end
function M.read()
    local iid = ffi.new('stats_gpu_guid', {0x770aae78, 0xf26f, 0x4dba,
        {0xa8,0x29,0x25,0x3c,0x83,0xd1,0xb3,0x87}})
    local output = ffi.new('void *[1]')
    if dxgi.CreateDXGIFactory1(iid, output) ~= 0 then return nil end
    local factory, adapters = output[0], {}
    local enumerate = method(factory, 12, 'int32_t (__stdcall *)(void *, uint32_t, void **)')
    local index = 0
    while enumerate(factory, index, output) == 0 do
        local adapter, desc = output[0], ffi.new('stats_gpu_desc')
        local result = method(adapter, 10, 'int32_t (__stdcall *)(void *, stats_gpu_desc *)')(adapter, desc)
        if result == 0 then
            local flags = adapter_type(desc.luid)
            local luid = string.format('0x%08x_0x%08x', tonumber(ffi.cast('uint32_t', desc.luid.high)), tonumber(desc.luid.low))
            -- 排除软件、间接显示和半虚拟化设备；DXGI 的 REMOTE 标志是保留位，不能据此判断远控显卡。
            local excluded = bit.band(tonumber(desc.flags), 2) ~= 0
                or flags ~= nil and bit.band(flags, 0x4 + 0x40 + 0x80) ~= 0
            adapters[luid] = {name=description(desc.description),
                excluded=excluded, order=index, flags=flags, dxgi_flags=tonumber(desc.flags)}
        end
        release(adapter)
        index = index + 1
    end
    release(factory)
    return adapters
end
return M
