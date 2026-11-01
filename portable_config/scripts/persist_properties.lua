-- Script home: https://github.com/d87/mpv-persist-properties
-- 按实际变更合并保存；首次变更、快速退出及多实例均保留待提交状态。
local mp = require 'mp'
local utils = require 'mp.utils'
local msg = require 'mp.msg'
local options = require 'mp.options'
local o = {properties = 'volume,sub-scale', properties_path = 'persistent_config.json'}
options.read_options(o, 'persist_properties')
local loaded, safe_file = pcall(function()
    return dofile(mp.find_config_file('script-modules/safe-file.lua'))
end)
if not loaded then msg.error('设置保存模块无法加载：' .. tostring(safe_file)); return end
local root = mp.find_config_file('.') or mp.command_native({'expand-path', '~~/'})
local path = utils.join_path(root, o.properties_path)
local pending, observed = {}, {}
local names = {}
for name in o.properties:gmatch('[^,]+') do
    name = name:match('^%s*(.-)%s*$')
    if name ~= '' then names[#names + 1] = name end
end

local function parse(bytes)
    local bom = bytes:sub(1, 3) == '\239\187\191' and '\239\187\191' or ''
    local text = bom ~= '' and bytes:sub(4) or bytes
    if text == '' then return {}, nil, bom end
    if not text:match('^%s*{') then return nil, '设置文件不是 JSON 对象' end
    local data, err = utils.parse_json(text)
    if type(data) ~= 'table' then return nil, '设置文件无法读取：' .. tostring(err) end
    return data, nil, bom
end

local function save()
    if not next(pending) then return end
    local directory = utils.split_path(path)
    local ready, dir_err = safe_file.ensure_directory(directory)
    if not ready then msg.error(dir_err); return end
    local ok, err = safe_file.update(path, function(bytes)
        local data, parse_err, bom = parse(bytes)
        if not data then return nil, parse_err end
        for name, value in pairs(pending) do data[name] = value end
        return bom .. utils.format_json(data) .. '\n'
    end)
    if ok then pending = {}
    else msg.error('设置保存失败，原文件保留：' .. tostring(err)) end
end

local bytes, read_err = safe_file.read(path)
local saved, parse_err
if bytes ~= nil then saved, parse_err = parse(bytes) end
if read_err or parse_err then msg.error(read_err or parse_err) end
for _, name in ipairs(names) do
    if saved and saved[name] ~= nil
        and not mp.get_property_bool('option-info/' .. name .. '/set-from-commandline', false)
        and not mp.get_property_bool('option-info/' .. name .. '/set-locally', false) then
        local ok, err = mp.set_property_native(name, saved[name])
        if not ok then msg.error('恢复设置失败：' .. name .. '：' .. tostring(err)) end
    end
    -- 先记录初值，观察器的首次通知不视为用户改动。
    observed[name] = utils.format_json(mp.get_property_native(name))
end
local timer = mp.add_timeout(5, save)
timer:kill()
for _, name in ipairs(names) do
    mp.observe_property(name, 'native', function(property, value)
        local encoded = utils.format_json(value)
        if observed[property] == encoded then return end
        observed[property] = encoded
        if value == nil then return end
        pending[property] = value
        timer:kill()
        timer:resume()
    end)
end
mp.register_event('shutdown', save)
