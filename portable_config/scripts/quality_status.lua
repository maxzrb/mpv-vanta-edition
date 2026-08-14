-- 以竖排列表显示当前启用的着色器、视频滤镜和轻量插值

local mp = require 'mp'

local VS_LABELS = {
    ['quality-memc'] = '补帧',
    ['quality-upscale'] = '超分',
    ['quality-denoise'] = '降噪',
    ['quality-deblock'] = '去色块',
}

local function basename(file)
    if not file or file == '' then
        return nil
    end
    return file:gsub('\\', '/'):match('([^/]+)$') or file
end

local function native_list(name)
    local value = mp.get_property_native(name)
    if type(value) == 'table' then
        return value
    end
    return {}
end

local function format_shader(shader)
    return basename(shader) or tostring(shader)
end

local function format_filter(filter)
    if type(filter) ~= 'table' then
        return tostring(filter)
    end

    local label = filter.label
    local name = filter.name or '未知滤镜'
    local params = type(filter.params) == 'table' and filter.params or {}
    local purpose = label and VS_LABELS[label]

    if purpose then
        local file = basename(params.file)
        return file and string.format('[%s] %s', purpose, file)
            or string.format('[%s] %s', purpose, name)
    end

    if label and label ~= '' then
        return string.format('%s [%s]', name, label)
    end
    return name
end

local function append_section(lines, title, items, formatter)
    table.insert(lines, string.format('%s（%d）', title, #items))
    if #items == 0 then
        table.insert(lines, '  无')
    else
        for index, item in ipairs(items) do
            table.insert(lines, string.format('  %d. %s', index, formatter(item)))
        end
    end
end

local function show_quality_status()
    local shaders = native_list('glsl-shaders')
    local filters = native_list('vf')
    local interpolation = mp.get_property_bool('interpolation', false)
    local lines = {'当前画质处理', ''}

    append_section(lines, '着色器', shaders, format_shader)
    table.insert(lines, '')
    append_section(lines, '视频滤镜', filters, format_filter)
    table.insert(lines, '')
    table.insert(lines, 'mpv 轻量插值')
    table.insert(lines, interpolation and '  已启用' or '  未启用')

    mp.osd_message(table.concat(lines, '\n'), 8)
end

mp.register_script_message('show-quality-status', show_quality_status)
