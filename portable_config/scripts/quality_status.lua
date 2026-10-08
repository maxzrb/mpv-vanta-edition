-- 当前启用项使用简短、可滚动列表；详细色彩与故障信息独立显示。

local mp = require 'mp'
local msg = require 'mp.msg'
local utils = require 'mp.utils'
-- mpv 不会自动把 script-modules 加入 require 路径；兼容活动配置及独立脚本测试。
local precision_directory=mp.get_script_directory() or utils.split_path(debug.getinfo(1,'S').source:gsub('^@',''))
local precision_path=mp.find_config_file('script-modules/render-precision.lua')
    or utils.join_path(precision_directory,'../script-modules/render-precision.lua')
local precision_loaded, precision = pcall(dofile, precision_path)
if not precision_loaded then msg.error('加载精度说明模块失败：'..tostring(precision)) end

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

local fallback_timer, fallback_page, fallback_lines
local function ClearFallback()
    if fallback_timer then fallback_timer:kill();fallback_timer=nil end
    mp.remove_key_binding('quality-status-prev')
    mp.remove_key_binding('quality-status-next')
    fallback_lines=nil
end
local function Present(lines,title,kind,details)
    ClearFallback()
    local items={}
    for _,line in ipairs(lines) do
        if line~='' and line~=title then
            -- 只读项目仍允许键盘选中以滚动到屏外；点击不执行处理、不关闭页面。
            items[#items+1]={title=line,value={'ignore'},keep_open=true}
        end
    end
    if not details then
        items[#items+1]={title='查看详细色彩与播放状态',value={'script-message','show-color-status'}}
    end
    mp.set_property_native('user-data/quality-status',{view=kind,items=items})
    if type(mp.get_property_native('user-data/uosc'))=='table' then
        mp.commandv('script-message-to','uosc','open-menu',utils.format_json({
            type=kind,title=title,items=items,mouse_nav=true,search_style='disabled'}))
        return
    end
    -- 独立脚本环境没有 uosc 时分页显示，避免长列表超出窗口。
    fallback_lines,fallback_page=lines,1
    local size=math.max(5,math.min(12,math.floor(mp.get_property_number('osd-height',720)/45)-2))
    local function Draw()
        if not fallback_lines then return end
        local pages=math.max(1,math.ceil(#fallback_lines/size))
        fallback_page=math.max(1,math.min(fallback_page,pages))
        local text={}
        for i=(fallback_page-1)*size+1,math.min(#fallback_lines,fallback_page*size) do text[#text+1]=fallback_lines[i] end
        text[#text+1]=string.format('第 %d/%d 页 · PgUp/PgDn 翻页',fallback_page,pages)
        mp.osd_message(table.concat(text,'\n'),10)
    end
    mp.add_forced_key_binding('PGUP','quality-status-prev',function() fallback_page=fallback_page-1;Draw() end)
    mp.add_forced_key_binding('PGDWN','quality-status-next',function() fallback_page=fallback_page+1;Draw() end)
    fallback_timer=mp.add_timeout(10,ClearFallback)
    Draw()
end
local function show_color_status()
    local shaders = native_list('glsl-shaders')
    local filters = native_list('vf')
    local interpolation = mp.get_property_bool('interpolation', false)
    local lines = {'色彩与播放详情', ''}

    local function describe(params)
        if type(params) ~= 'table' then return '未知' end
        local function known(value, fallback)
            if not value or value == '' or value == 'auto' or value == 'unknown' then return fallback end
            return value
        end
        local format = params['hw-pixelformat'] or params.pixelformat or '未知'
        local storage = precision_loaded and precision.format(params) or '精度未知 [' .. format .. ']'
        return string.format('%s / %s / %s / %s / %s',
            known(params.primaries, '未知色域'), known(params.gamma, '未知传递函数'),
            known(params.colormatrix, '未知矩阵'), known(params['colorlevels'], '未知范围'),
            storage)
    end
    table.insert(lines, '解码源：' .. describe(mp.get_property_native('video-dec-params')))
    table.insert(lines, '有效输入（含自动推断）：' .. describe(mp.get_property_native('video-params')))
    table.insert(lines, '滤镜输出：' .. describe(mp.get_property_native('video-out-params')))
    table.insert(lines, '解码与滤镜交接：' .. (precision_loaded and precision.handoff(
        mp.get_property('hwdec-current','no'),mp.get_property_native('video-out-params'),filters) or '未知'))
    table.insert(lines, '渲染目标：' .. describe(mp.get_property_native('video-target-params')))
    local swap = mp.get_property_native('display-swapchain')
    table.insert(lines, '交换链：' .. (type(swap) == 'table' and require('mp.utils').format_json(swap) or tostring(swap or '未知')))
    local renderer = mp.get_property('current-vo','未知')
    table.insert(lines, 'GPU 中间精度：' .. (renderer=='gpu-next' and 'gpu-next 优先 FP16；' or renderer .. '；')
        .. '当前会话未逐阶段采集，不能由最终输出推断')
    table.insert(lines, '显示器实际输出位深／色准：未知，需驱动信息／测量确认')
    local target = mp.get_property_native('video-target-params', {}) or {}
    table.insert(lines, '目标亮度标尺：' .. (target['max-luma'] and tostring(target['max-luma']) .. ' cd/m²（配置／估计值，非实测）' or '未知'))
    local icc = mp.get_property('icc-profile', '')
    table.insert(lines, 'ICC：' .. (icc ~= '' and icc or mp.get_property_bool('icc-profile-auto', false) and '使用系统描述文件' or '未启用'))
    local color = mp.get_property_native('user-data/color-target', {}) or {}
    table.insert(lines, '色彩模式：' .. tostring(color.mode or '配置目标') .. ' / ' .. tostring(color.status or '未知'))
    table.insert(lines, '目标意图：' .. tostring(color.requested or '未知') .. (color.manual and '（本次会话手动覆盖）' or '（自动匹配）'))
    local actual = color.actual_settings or {}
    table.insert(lines, '实际设置：' .. tostring(actual['target-prim'] or '未知') .. ' / ' .. tostring(actual['target-trc'] or '未知')
        .. ' / ' .. tostring(actual['d3d11-output-format'] or '未知') .. ' / ' .. tostring(actual['d3d11-output-csp'] or '未知'))
    for key, value in pairs(color.external_overrides or {}) do
        table.insert(lines, '外部覆盖：' .. key .. '=' .. tostring(value))
    end
    if color.reason and color.reason ~= '' then table.insert(lines, '色彩提示：' .. color.reason) end
    table.insert(lines, 'Windows HDR：' .. tostring(color.hdr_status or '未知') .. ' / 显示器：' .. tostring(color.display or '未知'))
    local system_color=color.system_color or {}
    local mode_names={sdr='经典 SDR',wcg='SDR ACM',hdr='HDR',['advanced-unknown']='高级色彩（类型未知）'}
    table.insert(lines, 'Windows 显示模式：' .. tostring(mode_names[system_color.mode] or system_color.mode or '未知')
        .. ' / 校色责任：' .. tostring(color.display_color_owner or '未知'))
    if system_color.sdr_white_nits then
        table.insert(lines, '系统 SDR 白：' .. tostring(system_color.sdr_white_nits) .. ' nits（仅 HDR 桌面按绝对标尺使用）')
    end
    table.insert(lines, '显示链接报告位深：' .. tostring(color.reported_bits or '未知') .. '（不是面板实测）')
    table.insert(lines, 'HDR 峰值来源：' .. tostring(color.peak or '未知') .. ' / ' .. tostring(color.peak_source or '未知'))
    if system_color.mode=='wcg' then
        table.insert(lines, 'SDR ACM 工作白：线性 1.0；80 用于内部编码标尺，非屏幕亮度实测')
    else
        table.insert(lines, 'HDR 参考白：' .. tostring(color.reference_white or '未知') .. '（auto 查询系统，失败回退 203 nits）')
    end
    table.insert(lines, '场景峰值分析：' .. tostring(mp.get_property_native('hdr-compute-peak') or '未知'))
    table.insert(lines, '输出色彩空间标记：' .. tostring(mp.get_property_native('target-colorspace-hint')))
    table.insert(lines, '动态 HDR／DV 实际执行：无法从当前属性完整确认，未知；不等同于格式识别')
    local quality = mp.get_property_native('user-data/quality', {}) or {}
    table.insert(lines, '滤镜状态：' .. tostring(quality.state or '未启用'))
    local performance_names={balanced='HQ（默认）',['high-quality']='高质量'}
    table.insert(lines, '性能档位：' .. tostring(performance_names[quality.performance] or quality.performance or 'HQ（默认）'))
    for _, stage in ipairs(quality.chain or {}) do table.insert(lines, '处理步骤：' .. tostring(stage.title)) end
    if quality.note and quality.note ~= '' then table.insert(lines, quality.note) end
    if quality.warning and quality.warning ~= '' then table.insert(lines, '增强提示：' .. quality.warning) end
    if quality.error and quality.error ~= '' then table.insert(lines, '滤镜错误：' .. quality.error) end
    if quality.state=='失败' and #(quality.restore_pending or {})>0 then
        table.insert(lines,'增强选项恢复待重试：'..table.concat(quality.restore_pending,', '))
    end
    table.insert(lines, '')

    append_section(lines, '着色器', shaders, format_shader)
    table.insert(lines, '')
    append_section(lines, '视频滤镜', filters, format_filter)
    table.insert(lines, '')
    table.insert(lines, 'mpv 轻量插值')
    table.insert(lines, interpolation and '  已启用' or '  未启用')

    Present(lines,'色彩与播放详情','quality-details',true)
end

local function show_quality_status()
    local q=mp.get_property_native('user-data/quality',{}) or {}
    local names={balanced='HQ（默认）',['high-quality']='高质量'}
    local lines={'当前启用项','状态：'..tostring(q.state or '未启用'),
        '性能：'..tostring(names[q.performance] or q.performance or '稳健 HQ'),
        '解码：'..tostring(mp.get_property('hwdec-current','no'))}
    local source=mp.get_property_number('container-fps')
    local output=mp.get_property_number('estimated-vf-fps')
    -- 清空滤镜后估计值会滞留数帧；没有滤镜时显示原始帧率。
    if #native_list('vf')==0 then output=source end
    if source and output then lines[#lines+1]=string.format('帧率：%.3f → %.3f fps',source,output) end
    append_section(lines,'视频滤镜',native_list('vf'),format_filter)
    append_section(lines,'着色器',native_list('glsl-shaders'),format_shader)
    if mp.get_property_bool('interpolation',false) then lines[#lines+1]='mpv 轻量插值：已启用' end
    if q.note and q.note~='' then lines[#lines+1]=q.note end
    if q.warning and q.warning~='' then lines[#lines+1]='提示：'..q.warning end
    if q.error and q.error~='' then
        lines[#lines+1]='失败详情请查看控制台或详细状态'
    end
    Present(lines,'当前启用项','quality-active',false)
end
mp.register_script_message('show-quality-status',show_quality_status)
mp.register_script_message('show-color-status',show_color_status)
mp.register_event('start-file',ClearFallback)
mp.register_event('shutdown',ClearFallback)
