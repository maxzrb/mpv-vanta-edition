-- Copyright (c) 2025 dyphire <qimoge@gmail.com>
-- License: MIT
-- 本地改写：旧入口只管理用户启用的系统 HDR 切换，色彩目标交给统一管理器。
local mp = require 'mp'
local msg = require 'mp.msg'
local options = require 'mp.options'
local o = {hdr_mode='noth', fullscreen_only=false, target_peak='0', target_contrast='auto'}
options.read_options(o, 'hdr_mode')
local generation, timer, original_hdr, changed_system = 0, nil, nil, false
local paused_by_script = false
local function Resume()
    if paused_by_script then mp.set_property_native('pause', false); paused_by_script = false end
end
local function Cancel()
    generation = generation + 1
    if timer then timer:kill(); timer = nil end
    Resume()
end
local function State()
    return mp.get_property_native('user-data/display-info/hdr-status')
end
local function Manual()
    local s = mp.get_property_native('user-data/color-target', {}) or {}
    return s.manual == true
end
local function Evaluate()
    if o.hdr_mode == 'noth' or Manual() then return end
    local p = mp.get_property_native('video-params', {}) or {}
    if not p.gamma then return end
    local hdr = p.gamma == 'pq' or p.gamma == 'hlg' or p['dolby-vision-profile'] ~= nil
    local status = State()
    if status ~= 'on' and status ~= 'off' then return end
    if original_hdr == nil then original_hdr = status == 'on' end
    local fullscreen = mp.get_property_bool('fullscreen') or mp.get_property_bool('window-maximized')
    local expected = hdr and (not o.fullscreen_only or fullscreen)
    if o.hdr_mode == 'pass' then
        mp.commandv('script-message', 'color-select', hdr and status == 'on' and 'hdr' or 'sdr', 'legacy')
        return
    end
    if o.hdr_mode ~= 'switch' then return end
    if (status == 'on') == expected then
        mp.commandv('script-message', 'color-select', expected and 'hdr' or 'sdr', 'legacy')
        return
    end
    Cancel()
    local token, started = generation, mp.get_time()
    if not mp.get_property_bool('pause') then paused_by_script = true; mp.set_property_native('pause', true) end
    changed_system = true
    mp.commandv('script-message', 'toggle-hdr-display', expected and 'on' or 'off')
    local function Wait()
        if token ~= generation then return end
        if Manual() then Cancel(); return end
        if (State() == 'on') == expected or mp.get_time() - started >= 10 then
            timer = nil
            if (State() == 'on') ~= expected then msg.warn('Windows HDR 切换超时，按实际状态恢复播放') end
            mp.commandv('script-message', 'color-select', hdr and State() == 'on' and 'hdr' or 'sdr', 'legacy')
            Resume()
        else timer = mp.add_timeout(0.2, Wait) end
    end
    timer = mp.add_timeout(0.2, Wait)
end
if o.hdr_mode ~= 'noth' then
    mp.register_event('start-file', Cancel)
    mp.register_event('file-loaded', Evaluate)
    mp.register_event('end-file', Cancel)
    mp.observe_property('fullscreen', 'bool', function() if not timer then Evaluate() end end)
    mp.observe_property('window-maximized', 'bool', function() if not timer then Evaluate() end end)
    mp.observe_property('user-data/color-target', 'native', function() if Manual() then Cancel() end end)
    mp.register_event('shutdown', function()
        Cancel()
        -- 只恢复脚本实际改动前的状态，不把原本开启 HDR 的桌面强制关闭。
        if changed_system and original_hdr ~= nil then
            mp.commandv('script-message', 'toggle-hdr-display', original_hdr and 'on' or 'off')
        end
    end)
end
