-- 小型状态文件的可靠读改写；只在提交成功后替换原文件。
-- License: MIT
local M = {}
local available, ffi = pcall(require, 'ffi')
local windows = available and ffi.os == 'Windows'
local kernel
local sequence = 0

if windows then
    ffi.cdef[[
        void * __stdcall CreateFileW(const wchar_t *, unsigned long, unsigned long, void *, unsigned long, unsigned long, void *);
        int __stdcall ReadFile(void *, void *, unsigned long, unsigned long *, void *);
        int __stdcall WriteFile(void *, const void *, unsigned long, unsigned long *, void *);
        int __stdcall FlushFileBuffers(void *);
        int __stdcall CloseHandle(void *);
        int __stdcall MoveFileExW(const wchar_t *, const wchar_t *, unsigned long);
        int __stdcall DeleteFileW(const wchar_t *);
        int __stdcall GetFileSizeEx(void *, int64_t *);
        unsigned long __stdcall GetLastError(void);
        unsigned long __stdcall GetCurrentProcessId(void);
        void __stdcall Sleep(unsigned long);
        unsigned long __stdcall GetFullPathNameW(const wchar_t *, unsigned long, wchar_t *, wchar_t **);
        int __stdcall LCMapStringW(unsigned long, unsigned long, const wchar_t *, int, wchar_t *, int);
        void * __stdcall CreateMutexW(void *, int, const wchar_t *);
        unsigned long __stdcall WaitForSingleObject(void *, unsigned long);
        int __stdcall ReleaseMutex(void *);
        int __stdcall MultiByteToWideChar(unsigned int, unsigned long, const char *, int, wchar_t *, int);
    ]]
    kernel = ffi.load('kernel32')
end

local function wide(path)
    if type(path) ~= 'string' or path:find('\0', 1, true) then return nil end
    local count = kernel.MultiByteToWideChar(65001, 8, path, -1, nil, 0)
    if count == 0 then return nil end
    local buffer = ffi.new('wchar_t[?]', count)
    if kernel.MultiByteToWideChar(65001, 8, path, -1, buffer, count) == 0 then return nil end
    return buffer
end

local function invalid(handle)
    return handle == ffi.cast('void *', -1)
end

local function failure(action)
    return action .. '（Windows 错误 ' .. tonumber(kernel.GetLastError()) .. '）'
end

function M.read(path)
    if not windows then return nil, '可靠文件保存需要 Windows LuaJIT 接口' end
    local name = wide(path)
    if not name then return nil, '文件路径不是有效的 UTF-8' end
    local handle = kernel.CreateFileW(name, 0x80000000, 7, nil, 3, 0x80, nil)
    if invalid(handle) then
        local code = tonumber(kernel.GetLastError())
        if code == 2 then return '', nil, false end
        return nil, failure('读取文件失败')
    end
    local size = ffi.new('int64_t[1]')
    local ok = kernel.GetFileSizeEx(handle, size) ~= 0
    if not ok then
        local err = failure('读取状态文件大小失败')
        kernel.CloseHandle(handle)
        return nil, err
    end
    local count = tonumber(size[0])
    if count < 0 or count > 256 * 1024 * 1024 then
        kernel.CloseHandle(handle)
        return nil, '状态文件大小无效或超过 256 MiB'
    end
    local buffer = ffi.new('char[?]', math.max(count, 1))
    local read = ffi.new('unsigned long[1]')
    ok = kernel.ReadFile(handle, buffer, count, read, nil) ~= 0 and tonumber(read[0]) == count
    local err = not ok and failure('读取文件不完整') or nil
    kernel.CloseHandle(handle)
    if not ok then return nil, err end
    return ffi.string(buffer, count), nil, true
end

local function write_temporary(path, content)
    local handle = kernel.CreateFileW(wide(path), 0x40000000, 0, nil, 1, 0x80, nil)
    if invalid(handle) then return nil, failure('创建临时文件失败') end
    local written = ffi.new('unsigned long[1]')
    local ok = kernel.WriteFile(handle, content, #content, written, nil) ~= 0
        and tonumber(written[0]) == #content
    local err = not ok and failure('临时文件写入不完整') or nil
    if ok and kernel.FlushFileBuffers(handle) == 0 then
        ok, err = false, failure('临时文件落盘失败')
    end
    if kernel.CloseHandle(handle) == 0 and ok then ok, err = false, failure('关闭临时文件失败') end
    return ok, err
end

local function acquire(path)
    -- 内核互斥量覆盖完整读改写，不依赖可被删除后重新创建的锁文件。
    local full = ffi.new('wchar_t[32768]')
    local size = tonumber(kernel.GetFullPathNameW(wide(path), 32768, full, nil))
    if size == 0 or size >= 32768 then return nil, '无法规范化保存路径' end
    local lowered = ffi.new('wchar_t[32768]')
    size = kernel.LCMapStringW(0x7F, 0x100, full, -1, lowered, 32768)
    if size == 0 then return nil, failure('无法规范化路径大小写') end
    local bytes = ffi.string(lowered, (size - 1) * 2)
    local first, second = 5381, 0
    for index = 1, #bytes do
        local byte = bytes:byte(index)
        first = (first * 33 + byte) % 4294967296
        second = (second * 65599 + byte) % 4294967296
    end
    local handle = kernel.CreateMutexW(nil, 0, wide(string.format('Local\\mpv-safe-file-%08x%08x', first, second)))
    if handle == nil then return nil, failure('无法创建保存锁') end
    local result = tonumber(kernel.WaitForSingleObject(handle, 8))
    if result ~= 0 and result ~= 0x80 then
        local err = result == 0x102 and '其他播放器正在保存，请稍后重试' or failure('无法获取保存锁')
        kernel.CloseHandle(handle)
        return nil, err
    end
    return handle
end

function M.update(path, transform)
    if not windows then return nil, '可靠文件保存需要 Windows LuaJIT 接口' end
    local target = wide(path)
    if not target then return nil, '文件路径不是有效的 UTF-8' end
    local lock, lock_err = acquire(path)
    if not lock then return nil, lock_err end
    local temporary
    local success, result, err = pcall(function()
        local before, read_err, exists = M.read(path)
        if before == nil then return nil, read_err end
        local content, transform_err = transform(before)
        if type(content) ~= 'string' then return nil, transform_err or '保存内容无效' end
        if #content > 256 * 1024 * 1024 then return nil, '保存内容超过 256 MiB' end
        if content == before and exists then return true, content end
        sequence = sequence + 1
        temporary = path .. '.tmp-' .. tonumber(kernel.GetCurrentProcessId()) .. '-' .. sequence
        local wrote, write_err = write_temporary(temporary, content)
        if not wrote then return nil, write_err end
        local current, current_err, current_exists = M.read(path)
        if current == nil then return nil, current_err end
        if current ~= before or current_exists ~= exists then
            return nil, '保存期间文件被其他程序修改，已保留新内容，请刷新后重试'
        end
        -- 不先删除目标；同目录替换失败时原始数据保持不变。
        if kernel.MoveFileExW(wide(temporary), target, 9) == 0 then return nil, failure('替换原文件失败') end
        temporary = nil
        return true, content
    end)
    if temporary then kernel.DeleteFileW(wide(temporary)) end
    kernel.ReleaseMutex(lock)
    kernel.CloseHandle(lock)
    if not success then return nil, '保存处理失败：' .. tostring(result) end
    return result, err
end

function M.write(path, content)
    return M.update(path, function() return content end)
end

function M.update_options(path, values)
    return M.update(path, function(content)
        local bom = content:sub(1, 3) == '\239\187\191' and '\239\187\191' or ''
        if bom ~= '' then content = content:sub(4) end
        local newline = content:find('\r\n', 1, true) and '\r\n' or '\n'
        for name, value in pairs(values) do
            if not name:match('^[%w_%-]+$') then return nil, '选项名称无效' end
            local serialized = type(value) == 'boolean' and (value and 'yes' or 'no') or tostring(value)
            if serialized:find('[\r\n]') then return nil, '选项值不能包含换行' end
            local pattern = name:gsub('([^%w])', '%%%1')
            local replaced = 0
            local function replace(prefix) replaced = replaced + 1; return prefix .. serialized end
            content = content:gsub('^([ \t]*' .. pattern .. '[ \t]*=)[^\r\n]*', replace)
            content = content:gsub('([\r\n][ \t]*' .. pattern .. '[ \t]*=)[^\r\n]*', replace)
            if replaced == 0 then
                if content ~= '' and not content:match('[\r\n]$') then content = content .. newline end
                content = content .. name .. '=' .. serialized .. newline
            end
        end
        return bom .. content
    end)
end

return M
