--[[
    This file is an internal file-browser addon.
    It should not be imported like a normal module.

    Automatically populates the root with windows drives on startup.
    Ctrl+r will add new drives mounted since startup.

    Drives will only be added if they are not already present in the root.
]]

local mp = require 'mp'
local msg = require 'mp.msg'
local fb = require 'file-browser'

local PLATFORM = fb.get_platform()

-- Windows + LuaJIT 直接读取盘符，省去起播时同步创建 fsutil 子进程。
local native_drives
if PLATFORM == 'windows' then
    local ok, ffi = pcall(require, 'ffi')
    if ok then
        local loaded, kernel = pcall(function()
            ffi.cdef[[unsigned long __stdcall GetLogicalDrives(void);]]
            return ffi.load('kernel32')
        end)
        if loaded then
            native_drives = function()
                local mask = tonumber(kernel.GetLogicalDrives())
                if mask == 0 then return nil end
                local root = {}
                for index = 0, 25 do
                    if math.floor(mask / 2^index) % 2 == 1 then
                        root[#root + 1] = string.char(65 + index) .. ':/'
                    end
                end
                return root
            end
        end
    end
end

---returns a list of windows drives
---@return string[]?
local function get_drives()
    if native_drives then
        local drives = native_drives()
        if drives then return drives end
    end
    -- 非 LuaJIT 环境或原生查询失败时，继续沿用插件原有行为。
    ---@type MPVSubprocessResult?, string?
    local result, err = mp.command_native({
        name = 'subprocess',
        playback_only = false,
        capture_stdout = true,
        args = {'fsutil', 'fsinfo', 'drives'}
    })
    if not result then return msg.error(err) end
    if result.status ~= 0 then return msg.error('could not read windows root') end

    local root = {}
    for drive in result.stdout:gmatch("(%a:)\\") do
        table.insert(root, drive..'/')
    end
    return root
end

-- adds windows drives to the root if they are not already present
local function import_drives()
    if fb.get_opt('auto_detect_windows_drives') and PLATFORM ~= 'windows' then return end

    local drives = get_drives()
    if not drives then return end

    for _, drive in ipairs(drives) do
        fb.register_root_item(drive)
    end
end

local keybind = {
    key = 'Ctrl+r',
    name = 'import_root_drives',
    command = import_drives,
    parser = 'root',
    passthrough = true
}

---@type ParserConfig
return {
    api_version = '1.9.0',
    setup = import_drives,
    keybinds = { keybind }
}
