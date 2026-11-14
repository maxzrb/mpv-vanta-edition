--[[
  * dv-map.lua v1.0.0
  * 杜比视界映射：动态（RPU，默认） / 静态（忽略 RPU 动态亮度）
]]

local mp = require 'mp'
local msg = require 'mp.msg'
local utils = require 'mp.utils'

local LABEL = 'dv-static'
local preference_path = mp.command_native({'expand-path', '~~/files/dv-map-preferences.json'})
local preference = 'dynamic'
local last_mode, last_preference

local function ReadPreference()
    local file = io.open(preference_path, 'r')
    if not file then return end
    local data = utils.parse_json(file:read('*a'))
    file:close()
    if type(data) == 'table' and (data.mode == 'dynamic' or data.mode == 'static') then
        preference = data.mode
    elseif data ~= nil then
        msg.error('杜比视界映射偏好格式错误，使用动态映射')
    end
end

local function SavePreference()
    local directory = utils.split_path(preference_path)
    if directory and directory ~= '' then pcall(utils.mkdir, directory) end
    local file, err = io.open(preference_path, 'w')
    if not file then
        msg.error('保存杜比视界映射偏好失败：' .. tostring(err))
        return false
    end
    local ok, write_err = file:write(utils.format_json({mode = preference}))
    file:close()
    if not ok then
        msg.error('保存杜比视界映射偏好失败：' .. tostring(write_err))
        return false
    end
    return true
end

local function Video()
    local params = mp.get_property_native('video-params', {}) or {}
    local output = mp.get_property_native('video-out-params', {}) or {}
    local profile = tonumber(params['dolby-vision-profile'] or output['dolby-vision-profile'])
    if not profile then
        for _, track in ipairs(mp.get_property_native('track-list', {}) or {}) do
            if track.type == 'video' and track.selected then
                profile = tonumber(track['dolby-vision-profile'])
                if profile then break end
            end
        end
    end
    local is_dv = profile ~= nil or output.colormatrix == 'dolbyvision'
        or params['dolby-vision-profile'] ~= nil
    return is_dv, profile
end

local function HasStaticFilter()
    for _, filter in ipairs(mp.get_property_native('vf', {}) or {}) do
        if filter.label == LABEL then return true end
    end
    return false
end

local function RemoveStaticFilter()
    local chain = mp.get_property_native('vf', {}) or {}
    local kept, removed = {}, false
    for _, filter in ipairs(chain) do
        if filter.label == LABEL then
            removed = true
        else
            kept[#kept + 1] = filter
        end
    end
    if removed then
        local ok, err = mp.set_property_native('vf', kept)
        if not ok then msg.error('移除杜比视界静态映射失败：' .. tostring(err)) end
    end
end

local function AddStaticFilter()
    if HasStaticFilter() then return end
    local ok, err = mp.commandv('vf', 'add', '@' .. LABEL .. ':format=dolbyvision=no')
    if not ok then msg.error('添加杜比视界静态映射失败：' .. tostring(err)) end
end

local function Publish()
    local payload = {
        mode = HasStaticFilter() and 'static' or 'dynamic',
        preference = preference,
    }
    if payload.mode == last_mode and payload.preference == last_preference then return end
    last_mode, last_preference = payload.mode, payload.preference
    mp.set_property_native('user-data/dv-map', payload)
end

local function Apply(mode, announce, save)
    if mode ~= 'dynamic' and mode ~= 'static' then return end
    preference = mode
    if save ~= false then SavePreference() end
    local is_dv, profile = Video()
    if mode == 'static' and is_dv and profile ~= 5 then
        AddStaticFilter()
    else
        RemoveStaticFilter()
    end
    Publish()
    if not announce then return end
    if HasStaticFilter() then
        mp.osd_message('杜比视界映射：静态', 3)
    elseif mode == 'static' and not is_dv then
        mp.osd_message('杜比视界映射：静态', 4)
    elseif mode == 'static' and profile == 5 then
        mp.osd_message('杜比视界 P5 不支持静态映射，保持动态', 4)
    else
        mp.osd_message('杜比视界映射：动态', 3)
    end
end

ReadPreference()
Publish()

mp.register_script_message('toggle', function()
    Apply(HasStaticFilter() and 'dynamic' or 'static', true)
end)
mp.register_script_message('dynamic', function() Apply('dynamic', true) end)
mp.register_script_message('static', function() Apply('static', true) end)

mp.observe_property('vf', 'native', Publish)
mp.register_event('file-loaded', function()
    -- vf 会在换片时重置；等视频参数就绪后恢复已保存的映射偏好。
    mp.add_timeout(0.15, function()
        Apply(preference, false, false)
        if preference == 'static' then
            local mode = HasStaticFilter() and '静态' or '动态'
            mp.osd_message('杜比视界映射：' .. mode, 2)
        end
    end)
end)
