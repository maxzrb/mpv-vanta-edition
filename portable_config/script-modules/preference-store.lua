-- 只保存明确的用户选择，运行时回退和文件局部设置不进入偏好文件。
-- License: MIT
local mp = require 'mp'
local utils = require 'mp.utils'
local safe_file = dofile(mp.find_config_file('script-modules/safe-file.lua'))
local M = {}
local path = mp.command_native({'expand-path', '~~/files/playback-preferences.json'})
local hardware = {
    ['auto-safe'] = true, ['auto'] = true, ['no'] = true,
    ['auto-copy-safe'] = true, ['auto-copy'] = true,
    ['d3d11va'] = true, ['nvdec'] = true, ['d3d12va-copy'] = true,
    ['d3d11va-copy'] = true, ['nvdec-copy'] = true,
    ['vulkan'] = true, ['vulkan-copy'] = true, ['d3d12va'] = true,
    ['qsv'] = true, ['qsv-copy'] = true, ['amf'] = true, ['amf-copy'] = true,
    ['dxva2'] = true, ['dxva2-copy'] = true, ['cuda'] = true, ['cuda-copy'] = true,
    ['vaapi-copy'] = true, ['auto-unsafe'] = true, ['auto-copy-unsafe'] = true,
}
local sync = {audio = true, ['display-resample'] = true, ['display-tempo'] = true,
    ['display-vdrop'] = true, ['display-resample-vdrop'] = true}

function M.valid(name, value)
    if name == 'hwdec' then return type(value) == 'string' and hardware[value] == true end
    if name == 'video-sync' then return type(value) == 'string' and sync[value] == true end
    if name == 'hr-seek-framedrop' or name == 'd3d11va-zero-copy' or name == 'overload-catchup' then return type(value) == 'boolean' end
    return false
end

local function parse(bytes)
    local bom = bytes:sub(1, 3) == '\239\187\191' and '\239\187\191' or ''
    local text = bom ~= '' and bytes:sub(4) or bytes
    if text == '' then return {}, nil, bom end
    if not text:match('^%s*{') then return nil, '播放偏好不是 JSON 对象' end
    local data, err = utils.parse_json(text)
    if type(data) ~= 'table' then return nil, '播放偏好无法读取：' .. tostring(err) end
    return data, nil, bom
end

function M.read()
    local bytes, err = safe_file.read(path)
    if bytes == nil then return nil, err end
    return parse(bytes)
end

function M.set(name, value)
    if not M.valid(name, value) then return nil, '无效的播放偏好：' .. tostring(name) end
    local directory = utils.split_path(path)
    local ready, err = safe_file.ensure_directory(directory)
    if not ready then return nil, err end
    return safe_file.update(path, function(bytes)
        local data, err, bom = parse(bytes)
        if not data then return nil, err end
        data[name] = value
        return bom .. utils.format_json(data) .. '\n'
    end)
end

function M.restore(name)
    local data, err = M.read()
    if not data then return nil, err end
    local value = data[name]
    if value == nil then return end
    if not M.valid(name, value) then return nil, '忽略无效播放偏好：' .. name end
    -- 过载开关属于脚本策略，没有同名核心选项；临时解码模式不保存。
    if name == 'overload-catchup' then return value end
    -- 命令行与文件专用配置优先；一次性的启动参数不改写已保存的用户选择。
    if mp.get_property_bool('option-info/' .. name .. '/set-from-commandline', false)
        or mp.get_property_bool('option-info/' .. name .. '/set-locally', false) then return end
    local ok, set_err = mp.set_property_native(name, value)
    if not ok then return nil, '恢复播放偏好失败：' .. name .. '：' .. tostring(set_err) end
    return value
end

return M
