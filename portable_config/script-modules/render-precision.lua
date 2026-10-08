-- 格式与交接只描述可观察属性，不从最终输出推断整条管线精度。
-- License: MIT
local M = {}
local hardware_formats = {d3d11=true, cuda=true, vaapi=true, vulkan=true,
    videotoolbox=true, dxva2_vld=true, vdpau=true}
local known_bits = {nv12=8, nv21=8, p010=10, p010le=10, p010be=10,
    p016=16, p016le=16, p016be=16, rgb10a2=10, rgb10_a2=10,
    rgba16hf=16, rgb16hf=16, r16hf=16, rg16hf=16,
    rgba16f=16, rgba32f=32, rgb32f=32, rgba8=8, rgb8=8,
    bgra=8, rgba=8, rgb24=8, bgr24=8, rgb0=8, bgr0=8}

function M.format(params)
    if type(params) ~= 'table' then return '未知格式' end
    local format = params['hw-pixelformat'] or params.pixelformat or ''
    local bits = params['component-bits'] or known_bits[format]
        or tonumber(format:match('p(%d+)')) or tonumber(format:match('f(%d+)'))
    if not bits and (format:match('^yuvj?%d+p$') or format:match('^gbrp$')
        or format:match('^gray$')) then bits=8 end
    local floating = format:find('hf',1,true) or format:match('f%d+') or format:match('%df$')
    local precision = bits and string.format('%s %dbit',floating and '浮点存储' or '整数',bits)
        or '位深未知'
    return precision .. ' [' .. (format ~= '' and format or '未知') .. ']'
end

function M.handoff(decoder, output, filters)
    decoder = decoder or 'no'
    if decoder == 'no' or decoder == '' then return '软件解码，图像在系统内存' end
    if decoder:match('%-copy$') then return decoder .. '：硬解后复制到系统内存' end
    local format = type(output)=='table' and output.pixelformat or nil
    if hardware_formats[format] then return decoder .. '：主输出保持 GPU 表面' end
    for _,filter in ipairs(filters or {}) do
        if filter.enabled ~= false and filter.name == 'vapoursynth' and format then
            return decoder .. '：硬解后下载帧供 VS 处理，再上传渲染'
        end
    end
    return decoder .. '：交接方式未完整确认'
end

return M
