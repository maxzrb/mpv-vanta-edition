-- 只发现活动配置的脚本目录，避免 Windows 将根目录 Python Scripts 误当成 mpv 脚本。
local mp = require 'mp'
local msg = require 'mp.msg'
local utils = require 'mp.utils'
local directory = mp.command_native({'expand-path', '~~/scripts'})
local names, err = utils.readdir(directory)
if not names then msg.error('无法读取活动脚本目录：' .. tostring(err)); return end
table.sort(names, function(a, b) return a:lower() < b:lower() end)
local loaded = {}
for _, name in ipairs(names) do
    if name:sub(1, 1) ~= '.' and name:lower() ~= 'backup' then
        local path = utils.join_path(directory, name)
        local info = utils.file_info(path)
        local supported = info and info.is_file and name:lower():match('%.(lua)$')
            or info and info.is_file and (name:lower():match('%.js$') or name:lower():match('%.dll$') or name:lower():match('%.so$'))
        if info and info.is_dir then
            supported = utils.file_info(utils.join_path(path, 'main.lua'))
                or utils.file_info(utils.join_path(path, 'main.js'))
        end
        if supported then
            local _, load_err = mp.command_native({'load-script', path})
            if load_err then msg.error('加载活动脚本失败：' .. name .. '：' .. tostring(load_err))
            else loaded[#loaded + 1] = name end
        end
    end
end
mp.set_property_native('user-data/config-script-loader/loaded', loaded)
