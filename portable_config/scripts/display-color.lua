-- 原生只读显示检测，低频更新；只发布实际变化，不阻塞播放准备。
local mp = require 'mp'
local msg = require 'mp.msg'
local utils = require 'mp.utils'
local directory = mp.get_script_directory() or utils.split_path(debug.getinfo(1, 'S').source:gsub('^@', ''))
local path = mp.find_config_file('script-modules/display-color-native.lua')
    or utils.join_path(directory, '../script-modules/display-color-native.lua')
local ok, native = pcall(dofile, path or '')
if not ok then msg.warn('高级色彩原生检测不可用：' .. tostring(native)); return end
local last, timer, reported_error
local function same(a, b)
    if not a or not b then return a == b end
    for k, v in pairs(a) do if b[k] ~= v then return false end end
    for k in pairs(b) do if a[k] == nil then return false end end
    return true
end
local function refresh()
    local success, value, err = pcall(native.read, mp.get_property_number('window-id'))
    if not success then err, value = value, nil end
    value = value or {mode = 'unknown', source = err or '未知'}
    if not success and not reported_error then msg.warn(tostring(err)); reported_error = true end
    if not same(last, value) then
        local written, write_err = mp.set_property_native('user-data/display-color', value)
        if written then last = value else msg.error('发布显示色彩状态失败：' .. tostring(write_err)) end
    end
end
mp.observe_property('window-id', 'number', function(_, id)
    if timer then timer:kill(); timer = nil end
    refresh()
    if id and id ~= 0 then timer = mp.add_periodic_timer(2, refresh) end
end)
mp.register_event('file-loaded', refresh)
mp.register_event('shutdown', function() if timer then timer:kill() end end)
