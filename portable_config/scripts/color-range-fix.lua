-- License: MIT
-- 当前 gpu-next 核心的全范围 10/12bit 中点校正；仅转换命中格式，保留色度与元数据。
local mp = require 'mp'
local msg = require 'mp.msg'
local options = require 'mp.options'
local o = {enabled=true}
options.read_options(o)
local LABEL = 'color-full-range'
local owned, others, original, source_key, timer
local last_published
local generation=0
local suppressed = false
local file_active = mp.get_property('path')~=nil
local output_ready = file_active

local function Same(a,b)
    if a==b then return true end
    if type(a)~=type(b) then return false end
    if type(a)~='table' then return a==b end
    for k,v in pairs(a) do if not Same(v,b[k]) then return false end end
    for k in pairs(b) do if a[k]==nil then return false end end
    return true
end
local function Split(chain)
    local rest, mine = {}, nil
    for _,f in ipairs(chain or {}) do
        if f.label==LABEL then mine=f else rest[#rest+1]=f end
    end
    return rest,mine
end
local function Publish(state,reason)
    local payload={
        active=owned~=nil,state=state,reason=reason or '',input=original,
        output=owned and owned.params and owned.params.graph or '',threads=1,generation=generation}
    -- 相同状态不重复广播，避免 HDR 元数据回调带来额外后台开销。
    if Same(payload,last_published) then return end
    mp.set_property_native('user-data/color-range-fix',payload)
    last_published=payload
end
local function Remove()
    if not owned then return end
    local rest,mine=Split(mp.get_property_native('vf',{}) or {})
    if mine and Same(mine,owned) then
        local previous=owned
        owned=nil
        local ok,err=mp.set_property_native('vf',rest)
        if not ok then owned=previous;msg.error('撤销范围校正失败：'..tostring(err));return false end
    else owned=nil end
    others=nil
    return true
end
local function OutputFormat(p)
    if type(p)~='table' or p.colorlevels~='full' then return end
    if p.colormatrix~='bt.601' and p.colormatrix~='bt.709' and p.colormatrix~='bt.2020-ncl' then return end
    if p['dolby-vision-profile'] or p.alpha and p.alpha~='none' then return end
    local fmt=p['hw-pixelformat'] or p.pixelformat or ''
    local sampling,bits=fmt:match('^yuv(%d+)p(%d+)$')
    if fmt=='p010' or fmt=='p010le' then sampling,bits='420','10' end
    if fmt=='p012' or fmt=='p012le' then sampling,bits='420','12' end
    if (bits~='10' and bits~='12') or (sampling~='420' and sampling~='422' and sampling~='444') then return end
    return 'yuv'..sampling..'p16le'
end
local function Audit()
    timer=nil
    if not o.enabled or suppressed or not file_active or not output_ready then return end
    -- 固定已验证核心；更新核心后必须重新验证，不能盲目沿用绕过方案。
    if mp.get_property('current-vo')~='gpu-next'
        or not (mp.get_property('mpv-version',''):find('36bf3d529',1,true)) then
        Remove();Publish('未适用','当前后端／核心未经本校正验证');return
    end
    local p=mp.get_property_native('video-out-params')
    if owned then
        if p and p.colorlevels=='limited' and p.w==original.w and p.h==original.h
            and p.gamma==original.gamma and p.primaries==original.primaries then
            Publish('已校正')
        end
        return
    end
    local fmt=OutputFormat(p)
    if not fmt then Publish('无需校正');return end
    local rest,mine=Split(mp.get_property_native('vf',{}) or {})
    if mine then Publish('未校正','同名滤镜由外部持有');return end
    original=p
    local prefix=''
    if p['hw-pixelformat'] then
        -- 显式下载原硬解表面；不改硬解后端，也不让 FFmpeg 隐式猜测下载格式。
        local download=p['hw-pixelformat']
        if download:match('^yuv%d+p%d+$') or download=='p010' or download=='p012' then download=download..'le' end
        prefix='hwdownload,format=pix_fmts='..download..','
    end
    local filter={name='lavfi',label=LABEL,params={
        graph=prefix..'zscale=rangein=full:range=limited,format=pix_fmts='..fmt,o='threads=1'}}
    rest[#rest+1]=filter
    owned=filter
    local ok,err=mp.set_property_native('vf',rest)
    if not ok then
        owned=nil;suppressed=true
        Publish('失败',tostring(err));msg.error('全范围色度中点校正失败：'..tostring(err));return
    end
    local current=mp.get_property_native('vf',{}) or {}
    others,owned=Split(current)
    Publish('等待校正输出')
end
local function Schedule()
    if timer then timer:kill() end
    timer=mp.add_timeout(0,Audit)
end
mp.observe_property('video-out-params','native',function(_,p)
    -- file-loaded 发生时旧 VO 参数可能仍在；只依据新文件实际输出的通知启动校正。
    if file_active and p then output_ready=true end
    Schedule()
end)
mp.observe_property('vf','native',function(_,chain)
    if not owned then Schedule();return end
    local rest,mine=Split(chain)
    if not mine or not Same(mine,owned) then
        -- 用户删除／禁用／改写本滤镜后，本文件不再自动补回。
        owned=nil;others=nil;suppressed=true;Publish('外部已接管');return
    end
    if others and not Same(rest,others) then
        -- 外部链改变后重新检查实际渲染输入，避免对 RGB／16bit 结果重复转换。
        if Remove() then Schedule() end
    end
end)
mp.observe_property('video-params','native',function(_,p)
    if not p then return end
    local key={p.pixelformat,p['hw-pixelformat'],p.w,p.h,p.colorlevels,p.colormatrix,p.primaries,p.gamma}
    if source_key and not Same(key,source_key) and owned then Remove() end
    source_key=key;Schedule()
end)
local function Reset()
    generation=generation+1
    file_active=false
    output_ready=false
    if timer then timer:kill();timer=nil end
    Remove();original=nil;source_key=nil;suppressed=false
    Publish('等待图像参数')
end
mp.register_event('start-file',Reset)
mp.register_event('file-loaded',function() file_active=true end)
mp.register_event('end-file',Reset)
mp.register_event('shutdown',Reset)
