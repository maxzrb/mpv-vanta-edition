-- 用户主动选择的播放偏好即时保存；脚本临时调整不写回。
-- License: MIT
local mp = require 'mp'
local msg = require 'mp.msg'
local loaded, store = pcall(function()
    return dofile(mp.find_config_file('script-modules/preference-store.lua'))
end)
if not loaded then msg.error('播放偏好保存模块无法加载：' .. tostring(store)) end
local labels = {['video-sync'] = '帧同步', ['hr-seek-framedrop'] = '跳转时跳过中间帧',
    ['d3d11va-zero-copy'] = 'D3D11VA 零复制'}
local modes = {'display-resample', 'display-tempo', 'audio', 'display-vdrop', 'display-resample-vdrop'}
local names = {audio = '音频同步', ['display-resample'] = '显示器同步 · 重采样',
    ['display-tempo'] = '显示器同步 · 变速', ['display-vdrop'] = '显示器同步 · 丢帧',
    ['display-resample-vdrop'] = '显示器同步 · 重采样与丢帧'}
local session = {}

for name in pairs(labels) do
    if loaded then
        local value, err = store.restore(name)
        session[name] = value
        if err then msg.error(err) end
    end
end

local function set(name, value)
    if not labels[name] or loaded and not store.valid(name, value) then msg.error('无效的播放设置：' .. tostring(name)); return end
    local ok, err = mp.set_property_native(name, value)
    if not ok then msg.error('设置失败：' .. name .. '：' .. tostring(err)); return end
    session[name] = value
    local saved, save_err
    if loaded then saved, save_err = store.set(name, value) else save_err = store end
    if not saved then
        msg.error('播放偏好保存失败，原文件保留：' .. tostring(save_err))
        mp.osd_message('设置已生效，但未能保存', 3)
        return
    end
    mp.osd_message(labels[name] .. '：' .. (type(value) == 'boolean' and (value and '开' or '关') or names[value]), 2)
end

mp.add_hook('on_load', 55, function()
    for name, value in pairs(session) do
        if not mp.get_property_bool('option-info/' .. name .. '/set-locally', false) then
            local ok, err = mp.set_property_native('file-local-options/' .. name, value)
            if not ok then msg.error('应用播放偏好失败：' .. name .. '：' .. tostring(err)) end
        end
    end
end)

mp.register_script_message('set', set)
mp.register_script_message('toggle', function(name)
    if name ~= 'hr-seek-framedrop' and name ~= 'd3d11va-zero-copy' then msg.error('此设置不能切换：' .. tostring(name)); return end
    set(name, not mp.get_property_bool(name, false))
end)
mp.register_script_message('cycle-video-sync', function()
    local current = mp.get_property('video-sync')
    for index, value in ipairs(modes) do
        if value == current then set('video-sync', modes[index % #modes + 1]); return end
    end
    set('video-sync', modes[1])
end)
