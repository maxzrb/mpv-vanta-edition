-- License: MIT
-- 自动硬解在预加载时为 CPU 滤镜选择复制路径；用户明确指定的后端不覆盖。
local mp = require 'mp'
local msg = require 'mp.msg'
local function CpuFilters()
    for _,f in ipairs(mp.get_property_native('vf',{}) or {}) do
        if f.enabled~=false and (f.name=='vapoursynth' or f.name=='lavfi' or f.name=='scale'
            or f.name=='format' or f.name=='yadif' or f.name=='bwdif') then return true end
    end
    return false
end
mp.add_hook('on_preloaded',50,function()
    local policy=mp.get_property('hwdec')
    if (policy~='auto-safe' and policy~='auto') or mp.get_property('vid','auto')=='no' then return end
    if not CpuFilters() then return end
    local ok,err=mp.set_property('file-local-options/hwdec','auto-copy')
    if not ok then msg.error('软件滤镜兼容硬解选择失败：'..tostring(err));return end
    msg.info('CPU 滤镜在解码前选择复制硬解；仅当前文件生效')
end)
