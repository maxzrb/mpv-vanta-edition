-- Windows 起播／主动打开媒体时抬到前台，保留用户的持续置顶选择。
local msg = require 'mp.msg'
local options = require 'mp.options'
local o = { enabled = true }
options.read_options(o, 'window_foreground')
if not o.enabled then return end

local ffi_ok, ffi = pcall(require, 'ffi')
if not ffi_ok then return end
local bit = require 'bit'
local native_ok, user32 = pcall(function()
    ffi.cdef[[
        int IsWindow(void* hwnd);
        int IsIconic(void* hwnd);
        int ShowWindow(void* hwnd, int command);
        int SetWindowPos(void* hwnd, void* after, int x, int y, int cx, int cy, unsigned flags);
        int SetForegroundWindow(void* hwnd);
        void* GetForegroundWindow(void);
        long GetWindowLongA(void* hwnd, int index);
    ]]
    return ffi.load('user32')
end)
if not native_ok then return end

local pending = false
local first_window = true
local automatic_next = false
local retry_timer = nil
local deadline = 0

local function CancelRetry()
    if retry_timer then retry_timer:kill(); retry_timer = nil end
end

local function RaiseWindow()
    if not pending then return end
    local id = mp.get_property_number('window-id')
    if not id or id == 0 then return end
    local hwnd = ffi.cast('void*', id)
    if user32.IsWindow(hwnd) == 0 then return end
    pending = false
    first_window = false
    CancelRetry()
    if user32.IsIconic(hwnd) ~= 0 then
        -- 同步更新 mpv 的最小化状态，让自动暂停配置能够恢复。
        mp.set_property_bool('window-minimized', false)
        user32.ShowWindow(hwnd, 9)
    end
    local focused = user32.SetForegroundWindow(hwnd) ~= 0
        and user32.GetForegroundWindow() == hwnd
    local raised
    if focused or bit.band(user32.GetWindowLongA(hwnd, -20), 8) ~= 0 then
        raised = user32.SetWindowPos(hwnd, nil, 0, 0, 0, 0, 0x0013) ~= 0
    else
        -- 后台激活被拒绝时，普通 HWND_TOP 也可能留在原来的显示层级。
        -- 原生层短暂抬升后立即恢复普通层级，不修改 mpv 的 ontop／保存选项。
        raised = user32.SetWindowPos(hwnd, ffi.cast('void*', -1), 0, 0, 0, 0, 0x0013) ~= 0
        local restored = user32.SetWindowPos(hwnd, ffi.cast('void*', -2), 0, 0, 0, 0, 0x0013) ~= 0
        if not restored then msg.error('起播窗口普通层级恢复失败') end
        raised = raised and restored
    end
    if not raised then msg.warn('起播窗口抬升失败') end
    if not focused then
        -- 系统可能限制后台进程切换键盘焦点；保留已经抬升的显示顺序。
        msg.verbose('Windows 保留当前键盘焦点，已请求抬升播放器窗口')
    end
end

local function RequestRaise()
    pending = true
    deadline = mp.get_time() + 2
    CancelRetry()
    RaiseWindow()
    if pending then
        retry_timer = mp.add_periodic_timer(0.1, function()
            if mp.get_time() >= deadline then
                pending = false
                CancelRetry()
            else
                RaiseWindow()
            end
        end)
    end
end

mp.observe_property('window-id', 'number', function(_, id)
    if id and id ~= 0 then
        if first_window then RequestRaise() else RaiseWindow() end
    end
end)
mp.register_event('start-file', function()
    local skip = automatic_next
    automatic_next = false
    if not skip then RequestRaise() end
end)
mp.register_event('end-file', function(event)
    automatic_next = event.reason == 'eof' or event.reason == 'error'
    pending = false
    CancelRetry()
end)
mp.observe_property('idle-active', 'bool', function(_, idle)
    -- 播放列表已结束后，下一次打开媒体是主动请求。
    if idle then automatic_next = false end
end)
mp.register_event('shutdown', CancelRetry)
