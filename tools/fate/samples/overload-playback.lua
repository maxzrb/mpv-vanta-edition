-- 固定快照只替换过载传感输入；解码、定位、轨道及事件使用真实 mpv。
local mp = require 'mp'
local original = mp.get_property_number
local sensors = {avsync = 'lag', ['frame-drop-count'] = 'dropped', ['container-fps'] = 'fps'}
mp.get_property_number = function(name, fallback)
    local sensor = sensors[name]
    if sensor then
        local value = mp.get_property_native('user-data/fate-overload/' .. sensor)
        if type(value) == 'number' then return value end
    end
    return original(name, fallback)
end
dofile(mp.find_config_file('scripts/decode-performance.lua'))
