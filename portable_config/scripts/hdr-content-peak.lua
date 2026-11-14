-- License: MIT
-- HQ 静态 PQ 转 SDR 优先采用片源 MaxCLL；只覆盖渲染元数据，不改像素或原片。
local mp = require 'mp'
local msg = require 'mp.msg'
local options = require 'mp.options'
local o = {enabled=true}
options.read_options(o,'hdr-content-peak')
local LABEL = 'hdr-content-peak'
local owned, timer, last_published, failure
local writing, suppressed = false, false
local file_active = mp.get_property('path') ~= nil

local function Same(a,b)
    if a == b then return true end
    if type(a) ~= 'table' or type(b) ~= 'table' then return false end
    for k,v in pairs(a) do if not Same(v,b[k]) then return false end end
    for k in pairs(b) do if a[k] == nil then return false end end
    return true
end
local function Split(chain)
    local rest, mine = {}, nil
    for _,filter in ipairs(chain or {}) do
        if filter.label == LABEL then mine = filter else rest[#rest+1] = filter end
    end
    return rest, mine
end
local function Number(value)
    local n = tonumber(value)
    if n and n == n and n > 0 and n <= 10000 then return n end
end
local function Publish(state,reason,source)
    source = source or mp.get_property_native('video-params',{}) or {}
    local payload = {active=owned ~= nil,state=state,reason=reason or '',
        max_cll=Number(source['max-cll']),mastering_peak=Number(source['max-luma']),
        selected_peak=owned and tonumber(owned.params['max-luma']) or nil,
        origin=owned and 'MaxCLL' or '片源原有元数据'}
    if Same(payload,last_published) then return end
    mp.set_property_native('user-data/hdr-content-peak',payload)
    last_published = payload
end
local function Remove()
    if not owned then return true end
    local rest,mine = Split(mp.get_property_native('vf',{}) or {})
    if not mine or not Same(mine,owned) then owned = nil;return true end
    writing = true
    local ok,err = mp.set_property_native('vf',rest)
    writing = false
    if not ok then
        Publish('失败','撤销源峰值覆盖失败：'..tostring(err))
        msg.error('撤销 HDR 内容峰值失败：'..tostring(err))
        return false
    end
    owned = nil
    return true
end
local function Choice(source,color,chain)
    if not o.enabled then return nil,'已禁用' end
    if not file_active then return nil,'等待片源' end
    if mp.get_property('current-vo') ~= 'gpu-next' or color.pipeline ~= 'hq' then
        return nil,'当前路线不使用 HQ HDR→SDR'
    end
    if color.mode ~= 'sdr' and color.mode ~= 'sdr-acm' and color.mode ~= 'icc'
        and color.mode ~= '准备 SDR ACM 输出' then return nil,'当前不是 SDR 输出' end
    if next(color.external_overrides or {}) then return nil,'目标设置由外部接管' end
    if source.gamma ~= 'pq' then return nil,'当前不是 PQ 片源' end
    -- 动态亮度、杜比色彩重建和 HLG 的 OOTF 不在静态峰值覆盖范围内。
    if source['dolby-vision-profile'] or source.colormatrix == 'dolbyvision' then
        return nil,'保留杜比视界元数据'
    end
    for _,key in ipairs({'scene-max-r','scene-max-g','scene-max-b','scene-avg','max-pq-y','avg-pq-y'}) do
        if Number(source[key]) then return nil,'保留片源动态亮度元数据' end
    end
    for _,track in ipairs(mp.get_property_native('track-list',{}) or {}) do
        if track.type == 'video' and track.selected and track['dolby-vision-profile'] then
            return nil,'保留杜比视界元数据'
        end
    end
    for _,filter in ipairs(chain) do
        local params = filter.params or {}
        if filter.label ~= LABEL and filter.enabled ~= false and filter.name == 'format'
            and (params['max-luma'] or params['sig-peak']) then
            return nil,'源峰值已由其他滤镜指定'
        end
    end
    local output = mp.get_property_native('video-out-params')
    if output and output.gamma and output.gamma ~= 'pq' then return nil,'滤镜输出已转换传递函数' end
    local peak = Number(source['max-cll'])
    if not peak then return nil,'MaxCLL 缺失或无效，保留原有元数据' end
    if peak <= (Number(source['min-luma']) or 0)
        or (Number(source['max-fall']) or 0) > peak then
        return nil,'MaxCLL 与其他亮度元数据矛盾，保留原有元数据'
    end
    return peak
end
local function Audit()
    timer = nil
    if mp.get_property_native('user-data/color-output-rebuilding',false) then return end
    local source = mp.get_property_native('video-params',{}) or {}
    local color = mp.get_property_native('user-data/color-target',{}) or {}
    local chain = mp.get_property_native('vf',{}) or {}
    local rest,mine = Split(chain)
    if suppressed then
        Publish(failure and '失败' or '外部已接管',failure or '保留用户对滤镜的修改',source);return
    end
    if mine and not owned then Publish('外部已接管','保留用户对滤镜的修改',source);return end
    local peak,reason = Choice(source,color,chain)
    if not peak then
        if Remove() then Publish('未覆盖',reason,source) end
        return
    end
    if owned and tonumber(owned.params['max-luma']) == peak then
        Publish('已应用','',source);return
    end
    -- format 默认不转换像素；原始 video-params 保留母版、MaxCLL 及色彩标记。
    rest[#rest+1] = {name='format',label=LABEL,params={['max-luma']=tostring(peak)}}
    writing = true
    local ok,err = mp.set_property_native('vf',rest)
    writing = false
    if not ok then
        -- 元数据改变后的更新失败时，优先撤掉旧边界，避免把上一个内容峰值留给新场景。
        if owned then Remove() end
        suppressed = true
        failure = tostring(err)
        Publish('失败',failure,source)
        msg.error('应用 HDR 内容峰值失败：'..tostring(err))
        return
    end
    local current = mp.get_property_native('vf',{}) or {}
    local _,applied = Split(current)
    owned = applied
    Publish(applied and '已应用' or '失败',applied and '' or '核心未保留峰值滤镜',source)
end
local function Schedule()
    if timer then timer:kill() end
    timer = mp.add_timeout(0,Audit)
end
for _,property in ipairs({'video-params','video-out-params','track-list','current-vo',
        'user-data/color-target','user-data/color-output-rebuilding'}) do
    mp.observe_property(property,'native',Schedule)
end
mp.observe_property('vf','native',function(_,chain)
    if writing then return end
    if owned then
        local _,mine = Split(chain)
        if not Same(mine,owned) then
            owned = nil;suppressed = true
            Publish('外部已接管','用户删除或修改了源峰值滤镜');return
        end
    end
    Schedule()
end)
local function Reset()
    file_active = false
    if timer then timer:kill();timer = nil end
    Remove();suppressed = false;failure = nil
    Publish('等待片源')
end
mp.register_event('start-file',Reset)
mp.register_event('end-file',Reset)
mp.register_event('file-loaded',function() file_active = true;Schedule() end)
mp.register_event('playback-restart',Schedule)
mp.register_event('shutdown',function()
    if timer then timer:kill();timer = nil end
end)
mp.register_script_message('refresh',function() suppressed = false;failure = nil;Schedule() end)
