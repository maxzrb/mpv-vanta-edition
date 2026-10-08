-- 只读 Windows 显示色彩状态；不改系统 HDR，不启动外部进程。
local ffi = require 'ffi'
assert(ffi.os == 'Windows', '仅支持 Windows')
local bit = require 'bit'
ffi.cdef[[
typedef struct { uint32_t low; int32_t high; } vanta_color_luid;
typedef struct { int32_t left, top, right, bottom; } vanta_color_rect;
typedef struct { uint32_t size; vanta_color_rect monitor, work; uint32_t flags; uint16_t device[32]; } vanta_color_monitor;
typedef struct { vanta_color_luid adapter; uint32_t id, index, flags; } vanta_color_source;
typedef struct { vanta_color_luid adapter; uint32_t id, index, technology, rotation, scaling, numerator, denominator, scanline; int32_t available; uint32_t flags; } vanta_color_target;
typedef struct { vanta_color_source source; vanta_color_target target; uint32_t flags; } vanta_color_path;
typedef struct { uint32_t type, size; vanta_color_luid adapter; uint32_t id; } vanta_color_header;
typedef struct { vanta_color_header header; uint16_t device[32]; } vanta_color_source_name;
typedef struct { vanta_color_header header; uint32_t flags, encoding, bits, mode; } vanta_color_info;
typedef struct { vanta_color_header header; uint32_t level; } vanta_color_white;
void * __stdcall MonitorFromWindow(void *, uint32_t);
int __stdcall GetMonitorInfoW(void *, vanta_color_monitor *);
long __stdcall GetDisplayConfigBufferSizes(uint32_t, uint32_t *, uint32_t *);
long __stdcall QueryDisplayConfig(uint32_t, uint32_t *, vanta_color_path *, uint32_t *, void *, void *);
long __stdcall DisplayConfigGetDeviceInfo(vanta_color_header *);
void * __stdcall CreateDCW(const uint16_t *, const uint16_t *, const uint16_t *, const void *);
int __stdcall DeleteDC(void *);
int __stdcall GetICMProfileW(void *, uint32_t *, uint16_t *);
int __stdcall WideCharToMultiByte(uint32_t, uint32_t, const uint16_t *, int, char *, int, const char *, int *);
]]
local user = ffi.load('user32')
local gdi = ffi.load('gdi32')
local kernel = ffi.load('kernel32')
assert(ffi.sizeof('vanta_color_path') == 72 and ffi.sizeof('vanta_color_header') == 20,
    'Windows 显示结构布局不匹配')
local M = {}
local function utf8(wide)
    local size = kernel.WideCharToMultiByte(65001, 0, wide, -1, nil, 0, nil, nil)
    if size <= 1 then return '' end
    local buffer = ffi.new('char[?]', size)
    if kernel.WideCharToMultiByte(65001, 0, wide, -1, buffer, size, nil, nil) == 0 then return '' end
    return ffi.string(buffer)
end
local function header(packet, kind, adapter, id, size)
    packet.header.type, packet.header.size = kind, size or ffi.sizeof(packet)
    packet.header.adapter, packet.header.id = adapter, id
end
local function query(packet)
    return user.DisplayConfigGetDeviceInfo(ffi.cast('vanta_color_header *', packet)) == 0
end
function M.read(window_id)
    if not window_id or tonumber(window_id) == 0 then return nil, '窗口尚未建立' end
    local monitor = user.MonitorFromWindow(ffi.cast('void *', tonumber(window_id)), 2)
    local info = ffi.new('vanta_color_monitor')
    info.size = ffi.sizeof(info)
    if monitor == nil or user.GetMonitorInfoW(monitor, info) == 0 then return nil, '显示器查询失败' end
    local device = utf8(info.device)
    -- 热插拔可能改变数组大小，只进行有界重试。
    for _ = 1, 2 do
        local count, modes = ffi.new('uint32_t[1]'), ffi.new('uint32_t[1]')
        if user.GetDisplayConfigBufferSizes(2, count, modes) ~= 0 then break end
        if count[0] == 0 or count[0] > 128 or modes[0] > 512 then break end
        local paths = ffi.new('vanta_color_path[?]', count[0])
        local mode_buffer = ffi.new('uint64_t[?]', math.max(1, tonumber(modes[0]) * 8))
        local result = user.QueryDisplayConfig(2, count, paths, modes, mode_buffer, nil)
        if result == 0 then
            local matches = {}
            for i = 0, tonumber(count[0]) - 1 do
                local path = paths[i]
                local name = ffi.new('vanta_color_source_name')
                header(name, 1, path.source.adapter, path.source.id)
                if query(name) and utf8(name.device):lower() == device:lower() then matches[#matches + 1] = i end
            end
            -- 镜像输出的终端可能采用不同模式，不能把任意一个终端当作唯一目标。
            if #matches ~= 1 then return nil, '显示目标不唯一或尚未匹配' end
            local target = paths[matches[1]].target
            local color = ffi.new('vanta_color_info')
            header(color, 15, target.adapter, target.id)
            local modern = query(color)
            if not modern then
                header(color, 9, target.adapter, target.id, 32)
                if not query(color) then return nil, '系统未提供高级色彩状态' end
            end
            local active = bit.band(tonumber(color.flags), 2) ~= 0
            -- 旧接口不区分 HDR 与 WCG；保留未知，由现有 HDR 插件补充。
            local mode = modern and ({[0] = 'sdr', [1] = 'wcg', [2] = 'hdr'})[tonumber(color.mode)]
                or (not active and 'sdr' or 'advanced-unknown')
            local white = ffi.new('vanta_color_white')
            header(white, 11, target.adapter, target.id)
            local white_nits = query(white) and tonumber(white.level) / 1000 * 80 or nil
            if white_nits and (white_nits <= 0 or white_nits > 10000) then white_nits = nil end
            local profile = ''
            local dc = gdi.CreateDCW(nil, info.device, nil, nil)
            if dc ~= nil then
                local length = ffi.new('uint32_t[1]', 32768)
                local name = ffi.new('uint16_t[32768]')
                if gdi.GetICMProfileW(dc, length, name) ~= 0 then profile = utf8(name) end
                gdi.DeleteDC(dc)
            end
            return {mode = mode, advanced_active = active,
                source = modern and 'DisplayConfig v2' or 'DisplayConfig v1',
                device = device, target_id = tonumber(target.id), window_id = tonumber(window_id),
                bits = tonumber(color.bits), encoding = tonumber(color.encoding),
                sdr_white_nits = white_nits, system_icc = profile,
                identity = string.format('%08x:%08x:%d', tonumber(target.adapter.high),
                    tonumber(target.adapter.low), tonumber(target.id))}
        elseif result ~= 122 then break end
    end
    return nil, '显示拓扑暂不可用'
end
return M
