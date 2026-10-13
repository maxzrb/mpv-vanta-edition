-- Windows 原生采样：CPU 使用系统时间，GPU 使用按物理引擎汇总的 PDH。
-- 显卡身份由 DXGI／驱动标志识别，分别统计整机与指定进程的占用。
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
local adapter_reader, adapter_catalog
local module_source = debug.getinfo(1, 'S').source:gsub('^@', ''):gsub(string.char(92), '/')
local module_directory = module_source:match('^(.*/)') or ''
function M.adapters()
    -- 仅在统计面板开始采样后枚举，避免增加播放器起播时的设备初始化开销。
    if not adapter_reader then adapter_reader = dofile(module_directory .. 'gpu-adapters.lua') end
    if not adapter_catalog then adapter_catalog = adapter_reader.read() end
    return adapter_catalog
end
function M.aggregate(samples, pid)
    local catalog = M.adapters()
    if not catalog then return nil end
    local rows, engines, process_engines = {}, {}, {}
    for _, item in ipairs(samples) do
        local process, luid, physical, engine = (item.name or ''):match('^pid_(%d+)_luid_(.-)_phys_(%d+)_eng_(%d+)')
        local value = tonumber(item.value)
        local info = luid and catalog[luid:lower()]
        if info and not info.excluded and value and value == value and value >= 0 then
            local adapter = luid:lower() .. '/' .. physical
            local key = adapter .. '/' .. engine
            local row = rows[adapter]
            if not row then
                row = {name=info.name, order=info.order, physical=tonumber(physical),
                    total=0, process=pid and 0 or nil}
                rows[adapter] = row
            end
            -- 同一引擎汇总各进程，再取最忙引擎；不把不同引擎百分比相加。
            engines[key] = math.min(100, (engines[key] or 0) + value)
            row.total = math.max(row.total, engines[key])
            if pid and tonumber(process) == pid then
                process_engines[key] = math.min(100, (process_engines[key] or 0) + value)
                row.process = math.max(row.process, process_engines[key])
            end
        end
    end
    return next(rows) and rows or nil
end
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
    adapter_catalog = nil
end
function M.gpu(pid)
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
    local samples = {}
    for i = 0, tonumber(count[0]) - 1 do
        local item = items[i]
        if item.name ~= nil and item.value.status <= 1 then
            samples[#samples + 1] = {name=ffi.string(item.name), value=tonumber(item.value.number)}
        end
    end
    return M.aggregate(samples, pid)
end
return M
