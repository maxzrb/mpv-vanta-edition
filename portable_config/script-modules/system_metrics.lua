-- Windows 原生采样：CPU 使用系统时间，GPU 使用按物理引擎汇总的 PDH。
-- 数据表示整机占用率；不冒充播放器进程占用率，也不按数值猜测显卡名称。
local ffi = require 'ffi'
assert(ffi.os == 'Windows', '仅支持 Windows')
ffi.cdef[[
typedef struct { uint32_t low, high; } vanta_filetime;
int __stdcall GetSystemTimes(vanta_filetime *, vanta_filetime *, vanta_filetime *);
uint32_t __stdcall GetActiveProcessorCount(uint16_t);
long __stdcall PdhOpenQueryA(const char *, uintptr_t, void **);
long __stdcall PdhAddEnglishCounterA(void *, const char *, uintptr_t, void **);
long __stdcall PdhCollectQueryData(void *);
long __stdcall PdhCloseQuery(void *);
typedef struct { uint32_t status; union { long long integer; double number; const char *text; }; } vanta_pdh_value;
typedef struct { const char *name; vanta_pdh_value value; } vanta_pdh_item;
long __stdcall PdhGetFormattedCounterArrayA(void *, uint32_t, uint32_t *, uint32_t *, vanta_pdh_item *);
]]
local kernel = ffi.load('kernel32')
local pdh = ffi.load('pdh')
local M = {}
local previous, query, counter, warm
local function ticks(t) return tonumber(t.high) * 4294967296 + tonumber(t.low) end
function M.cpu()
    if kernel.GetActiveProcessorCount(0xffff) > 64 then return nil end
    local t = ffi.new('vanta_filetime[3]')
    if kernel.GetSystemTimes(t, t + 1, t + 2) == 0 then return nil end
    local idle, total = ticks(t[0]), ticks(t[1]) + ticks(t[2])
    local old = previous
    previous = {idle, total}
    if not old or total <= old[2] then return nil, 'warming' end
    return math.max(0, math.min(100, 100 * (1 - (idle - old[1]) / (total - old[2]))))
end
function M.close()
    if query then pdh.PdhCloseQuery(query) end
    previous, query, counter, warm = nil, nil, nil, false
end
function M.gpu()
    if not query then
        local q, c = ffi.new('void *[1]'), ffi.new('void *[1]')
        if pdh.PdhOpenQueryA(nil, 0, q) ~= 0 then return nil end
        query = q[0]
        if pdh.PdhAddEnglishCounterA(query, '\\GPU Engine(*)\\Utilization Percentage', 0, c) ~= 0 then
            M.close(); return nil
        end
        counter = c[0]
    end
    if pdh.PdhCollectQueryData(query) ~= 0 then M.close(); return nil end
    if not warm then warm = true; return nil, 'warming' end
    local size, count = ffi.new('uint32_t[1]'), ffi.new('uint32_t[1]')
    local result = pdh.PdhGetFormattedCounterArrayA(counter, 0x200, size, count, nil)
    if result ~= -2147481646 or size[0] == 0 or size[0] > 16777216 then return nil end
    local buffer = ffi.new('uint8_t[?]', size[0])
    local items = ffi.cast('vanta_pdh_item *', buffer)
    if pdh.PdhGetFormattedCounterArrayA(counter, 0x200, size, count, items) ~= 0 then return nil end
    local engines, adapters = {}, {}
    for i = 0, tonumber(count[0]) - 1 do
        local item = items[i]
        if item.name ~= nil and item.value.status <= 1 then
            local name, value = ffi.string(item.name), tonumber(item.value.number)
            local luid, physical, engine = name:match('luid_(.-)_phys_(%d+)_eng_(%d+)')
            if luid and value == value and value >= 0 then
                local adapter = luid .. '/' .. physical
                local key = adapter .. '/' .. engine
                engines[key] = math.min(100, (engines[key] or 0) + value)
                adapters[adapter] = math.max(adapters[adapter] or 0, engines[key])
            end
        end
    end
    return next(adapters) and adapters or nil
end
return M
