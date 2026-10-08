-- 自动匹配显示目标；手动覆盖在本次会话有效，恢复失败保留重试基线。
-- License: MIT
local mp = require 'mp'
local msg = require 'mp.msg'
local utils = require 'mp.utils'
local options = require 'mp.options'
local o = {verify_timeout=3, hdr_backend='scrgb', hdr_peak=0, hdr_contrast='auto'}
options.read_options(o,'color-target')
local keys={'icc-profile','icc-profile-auto','icc-intent','target-prim','target-trc','target-gamut',
    'target-peak','target-contrast','target-colorspace-hint','target-colorspace-hint-mode',
    'target-colorspace-hint-strict','d3d11-output-format','d3d11-output-csp',
    'hdr-reference-white','inverse-tone-mapping','hdr-contrast-recovery','treat-srgb-as-power22','dither-depth'}
local baseline, owned, drift, observed = {},{},{},{}
local playback_retry
local mode, requested, reason, status_text = '配置目标','auto','','可用'
local manual, writing, generation, timer = false,false,0,nil
local Select, Publish
local preferences, legacy_peak_display = {},nil
local preference_path=mp.command_native({'expand-path','~~/files/color-target-preferences.json'})
local f=io.open(preference_path,'r')
if f then
    local saved=utils.parse_json(f:read('*a'));f:close()
    if type(saved)=='table' then preferences=saved else msg.error('显示器偏好文件格式错误，使用当前会话基线') end
end
local function Display()
    local d=mp.get_property_native('user-data/display-info',{}) or {}
    return d,d['hdr-status']=='on',d['hdr-supported']==true or d['hdr-supported']=='true'
end
local function SystemColor()
    return mp.get_property_native('user-data/display-color',{}) or {}
end
local function IccContext()
    local c=SystemColor()
    if not c.identity then return nil end
    return c.identity..'|'..tostring(c.mode)..'|'..tostring(c.system_icc or '')
end
local function DisplayKey()
    local d=Display()
    if not d.uid or d.uid=='' then return nil end
    local suffix=SystemColor().mode=='wcg' and '|wcg' or ''
    return tostring(d.uid)..'|'..tostring(d['hdr-status'] or 'unknown')..suffix
end
local function Preference()
    local p=preferences[DisplayKey()]
    return type(p)=='table' and p or {}
end
local function SavePreference(key,value)
    local id=DisplayKey()
    if not id then return false,'显示器身份未知，不能保存此显示器偏好' end
    local previous=preferences[id]
    local updated={}
    for k,v in pairs(Preference()) do updated[k]=v end
    updated[key]=value;preferences[id]=updated
    if key=='icc' then updated.icc_context=value and IccContext() or nil end
    local file,err=io.open(preference_path,'w')
    if not file then preferences[id]=previous;return false,'保存显示器偏好失败：'..tostring(err) end
    local ok,write_err=file:write(utils.format_json(preferences)); file:close()
    if not ok then preferences[id]=previous end
    return ok~=nil,write_err
end
local function Peak()
    local d=Display(); local p=Preference()
    if tonumber(p.peak) and tonumber(p.peak)>0 then return tonumber(p.peak),'用户指定（按显示器及桌面模式保存，需测量确认）' end
    local id=DisplayKey()
    if not legacy_peak_display and id and tonumber(o.hdr_peak)>0 then legacy_peak_display=id end
    if id and id==legacy_peak_display and tonumber(o.hdr_peak)>0 then return tonumber(o.hdr_peak),'配置指定（仅绑定首次识别的显示器及模式）' end
    return tonumber(d['max-luminance']),'驱动／系统报告，非实测'
end
local function Cancel()
    generation=generation+1
    if timer then timer:kill();timer=nil end
end
local function Same(a,b)
    if a==b then return true end
    if (a==false and b=='no') or (a=='no' and b==false)
        or (a==true and b=='yes') or (a=='yes' and b==true) then return true end
    -- mpv 数字选项有时以字符串返回。
    return tonumber(a)~=nil and tonumber(a)==tonumber(b)
end
local function SameNative(a,b)
    -- 未知像素比例等字段可能为 NaN；两个未知值相同，不应每帧重复发布状态。
    if type(a)=='number' and type(b)=='number' and a~=a and b~=b then return true end
    if type(a)~='table' or type(b)~='table' then return a==b end
    for key,value in pairs(a) do if not SameNative(value,b[key]) then return false end end
    for key in pairs(b) do if a[key]==nil then return false end end
    return true
end
local function Write(key,value)
    writing=true
    local ok,err=mp.set_property_native(key,value)
    writing=false
    return ok,err
end
local function Read(key)
    local value=mp.get_property_native(key)
    -- 自定义色域未指定时核心返回空串；空串不能写回该选项，auto 才是等价基线。
    if key=='target-gamut' and value=='' then return 'auto' end
    return value
end
local function OutputProfile(format,csp)
    local names={['auto|srgb']='Color-Output-SDR',['rgba16f|linear']='Color-Output-scRGB',
        ['rgb10_a2|pq']='Color-Output-PQ'}
    local name=names[tostring(format)..'|'..tostring(csp)]
    if not name then return nil end
    for _,profile in ipairs(mp.get_property_native('profile-list',{}) or {}) do
        if profile.name==name then return name end
    end
end
local function WriteOutput(format,csp)
    local profile=OutputProfile(format,csp)
    if not profile then return nil end
    writing=true
    local _,err=mp.command_native({'apply-profile',profile})
    writing=false
    local accepted=err==nil and Same(Read('d3d11-output-format'),format) and Same(Read('d3d11-output-csp'),csp)
    return accepted,err or (not accepted and '输出配置组未应用完整配对' or nil)
end
local function RestorePlayback(snapshot)
    local errors={}
    local ok,err=Write('vid',snapshot.vid)
    if not ok then errors[#errors+1]='恢复视频轨：'..tostring(err) end
    if snapshot.position and mp.get_property_native('seekable')~=false then
        local _,seek_err=mp.command_native({'seek',snapshot.position,'absolute+exact'})
        if seek_err then errors[#errors+1]='恢复播放位置：'..tostring(seek_err) end
    end
    ok,err=Write('pause',snapshot.paused)
    if not ok then errors[#errors+1]='恢复暂停：'..tostring(err) end
    return #errors==0,table.concat(errors,'\n')
end
local function Update(values)
    if playback_retry then
        local resumed,resume_err=RestorePlayback(playback_retry)
        if not resumed then return false,resume_err end
        playback_retry=nil
    end
    local changes,previous,restored={},{},{}
    for _,key in ipairs(keys) do
        local current=Read(key)
        if values and values[key]~=nil then
            if not Same(current,values[key]) then changes[key]=values[key]; previous[key]=current end
        elseif owned[key]~=nil then
            if Same(current,owned[key]) then
                if not Same(current,baseline[key]) then changes[key]=baseline[key];previous[key]=current end
                restored[key]=true
            else baseline[key],owned[key]=nil,nil end
        end
    end
    local rebuild=changes['d3d11-output-format']~=nil or changes['d3d11-output-csp']~=nil
    local vid=mp.get_property_native('vid');local paused=mp.get_property_native('pause')
    local position=mp.get_property_native('time-pos')
    local suspend=rebuild and vid and vid~='no' and mp.get_property_native('video-params')
    if suspend and mp.get_property_native('seekable')==false then return false,'不可定位流无法安全重建输出；保留当前有效目标' end
    if suspend then
        local ok,err=Write('pause',true)
        if not ok then return false,'保留暂停状态失败：'..tostring(err) end
        ok,err=Write('vid','no')
        if not ok then Write('pause',paused);return false,'暂存视频轨失败：'..tostring(err) end
    end
    local applied,errors={},{}
    local paired=changes['d3d11-output-format']~=nil and changes['d3d11-output-csp']~=nil
        and OutputProfile(changes['d3d11-output-format'],changes['d3d11-output-csp'])~=nil
    if paired then
        -- 一个原生命令内设置完整配对，核心只重建一次 VO。
        local ok,err=WriteOutput(changes['d3d11-output-format'],changes['d3d11-output-csp'])
        if not ok then
            -- 配置组也可能部分应用失败，先回滚输出再恢复播放，不能丢掉恢复基线。
            local reverted=WriteOutput(previous['d3d11-output-format'],previous['d3d11-output-csp'])
            if not reverted then
                for _,key in ipairs({'d3d11-output-format','d3d11-output-csp'}) do
                    local restored,restore_err=Write(key,previous[key])
                    if not restored then
                        if baseline[key]==nil then baseline[key]=previous[key] end
                        owned[key]=Read(key)
                        err=tostring(err)..'\n回滚 '..key..'：'..tostring(restore_err)
                    end
                end
            end
            if suspend then
                playback_retry={vid=vid,paused=paused,position=position}
                local resumed,resume_err=RestorePlayback(playback_retry)
                if resumed then playback_retry=nil else err=tostring(err)..'\n'..resume_err end
            end
            return false,'输出过渡失败：'..tostring(err)
        end
        applied[#applied+1]='d3d11-output-format';applied[#applied+1]='d3d11-output-csp'
        if not values then
            for _,key in ipairs({'d3d11-output-format','d3d11-output-csp'}) do
                baseline[key],owned[key],restored[key]=nil,nil,nil
            end
        end
    end
    local function Rollback()
        local output_changed=false
        for _,item in ipairs(applied) do
            if item=='d3d11-output-format' or item=='d3d11-output-csp' then output_changed=true end
        end
        local restored_pair
        if output_changed and previous['d3d11-output-format'] and previous['d3d11-output-csp'] then
            restored_pair=WriteOutput(previous['d3d11-output-format'],previous['d3d11-output-csp'])
        end
        local function Revert(item)
            local reverted,revert_err=Write(item,previous[item])
            if not reverted then
                if baseline[item]==nil then baseline[item]=previous[item] end
                owned[item]=Read(item)
                errors[#errors+1]='回滚 '..item..'：'..tostring(revert_err)
            end
        end
        local defer_csp=false
        for index=#applied,1,-1 do
            local item=applied[index]
            if restored_pair and (item=='d3d11-output-format' or item=='d3d11-output-csp') then
                -- 完整配对已恢复。
            elseif item=='d3d11-output-csp' then defer_csp=true else Revert(item) end
        end
        if defer_csp then Revert('d3d11-output-csp') end
    end
    for _,key in ipairs(keys) do
        if changes[key]~=nil and not (paired and (key=='d3d11-output-format' or key=='d3d11-output-csp')) then
            local ok,err=Write(key,changes[key])
            if not ok then
                errors[#errors+1]=key..'：'..tostring(err)
                if values then
                    -- 应用是事务；恢复失败的字段仍保留原始基线，允许之后重试。
                    Rollback()
                    break
                end
            else
                applied[#applied+1]=key
                if not values then baseline[key],owned[key],restored[key]=nil,nil,nil end
            end
        end
    end
    if not values then
        for key in pairs(restored) do
            if changes[key]==nil then baseline[key],owned[key]=nil,nil end
        end
    end
    if suspend then
        local apply_failed=#errors>0
        playback_retry={vid=vid,paused=paused,position=position}
        local snapshot=playback_retry
        local function Resume()
            local ok,err=RestorePlayback(snapshot)
            if ok then playback_retry=nil else errors[#errors+1]=err end
        end
        Resume()
        if values and not apply_failed and #errors>0 then
            -- 重建、定位或暂停恢复失败都回滚整次目标切换，再恢复原播放链。
            Rollback()
            Resume()
        end
    end
    if values and #errors==0 then
        for _,key in ipairs(keys) do
            if values[key]~=nil then
                if baseline[key]==nil then
                    if previous[key]~=nil then baseline[key]=previous[key] else baseline[key]=Read(key) end
                end
                owned[key]=Read(key); drift[key]=nil
            end
        end
    end
    return #errors==0,table.concat(errors,'\n')
end
local last_published
Publish=function(status)
    if status then status_text=status end
    local d,active,supported=Display();local peak,source=Peak()
    local actual,pending={},{}
    for _,key in ipairs(keys) do
        actual[key]=Read(key)
        if owned[key]~=nil then
            pending[#pending+1]=key
            if not Same(actual[key],owned[key]) then drift[key]=actual[key] end
        end
    end
    if playback_retry then pending[#pending+1]='视频轨／播放位置／暂停' end
    local payload={
        mode=mode,requested=requested,status=status_text,reason=reason,manual=manual,
        display=d.name or '未知',display_id=d.uid or '未知',hdr_active=active,hdr_supported=supported,
        hdr_status=d['hdr-status'] or '未知',reported_bits=d['bit-depth'] or '未知',
        peak=peak,peak_source=peak and source or '未知',reference_white=actual['hdr-reference-white'],
        system_color=SystemColor(),
        display_color_owner=SystemColor().mode=='wcg' and 'Windows ACM（不叠加显示 ICC）' or '播放器目标／显式 ICC',
        actual_settings=actual,external_overrides=drift,restore_pending=pending,
        actual_target=mp.get_property_native('video-target-params',{}) or {},
        swapchain=mp.get_property_native('display-swapchain') or '未知',
        intermediate='gpu-next 自动选择；实际纹理格式见日志',
    }
    -- user-data 写入会通知父节点观察者；相同状态不再次广播，避免反馈循环。
    if SameNative(payload,last_published) then return end
    local ok,err=mp.set_property_native('user-data/color-target',payload)
    if ok then last_published=payload else msg.error('发布色彩状态失败：'..tostring(err)) end
end
local function SdrValues(icc)
    return {['icc-profile']='',['icc-profile-auto']=icc==true,['icc-intent']=1,
        ['target-prim']='bt.709',['target-trc']='srgb',['target-gamut']='auto',['target-peak']='auto',['target-contrast']='auto',
        ['target-colorspace-hint']=false,['target-colorspace-hint-mode']='target',['target-colorspace-hint-strict']=true,
        ['d3d11-output-format']='auto',['d3d11-output-csp']='srgb',['hdr-reference-white']='auto',
        ['inverse-tone-mapping']=false,['hdr-contrast-recovery']=0,['treat-srgb-as-power22']='no',
        ['dither-depth']='auto'}
end
local function HdrValues(backend,peak,contrast)
    local v=SdrValues(false)
    v['target-prim']=backend=='scrgb' and 'bt.709' or 'bt.2020'
    v['target-trc']=backend=='scrgb' and 'scrgb' or 'pq'
    v['target-peak'],v['target-contrast']=peak,contrast
    v['target-colorspace-hint']=true
    v['d3d11-output-format']=backend=='scrgb' and 'rgba16f' or 'rgb10_a2'
    v['d3d11-output-csp']=backend=='scrgb' and 'linear' or 'pq'
    if backend=='scrgb' then
        -- 浮点输出不提前量化到物理连接位深；最终量化由 Windows／驱动处理。
        v['dither-depth']='no'
        local source=mp.get_property_native('video-params',{}) or {}
        if source.primaries=='bt.2020' or source.primaries=='display-p3' or source.primaries=='dci-p3' then
            v['target-gamut']=source.primaries
        end
    end
    return v
end
local function Sdr(failure,icc)
    local v=SdrValues(icc==true)
    if type(icc)=='string' then v['icc-profile']=icc end
    local ok,err=Update(v)
    reason=failure or ''
    if ok then mode=icc and 'icc' or 'sdr';Publish('可用')
    else reason=(reason~='' and reason..'\n' or '')..err;Publish('失败');msg.error(reason) end
    return ok
end
local function SdrManaged(failure,icc)
    if SystemColor().mode~='wcg' or mp.get_property('gpu-api')~='d3d11' then return Sdr(failure,icc) end
    -- SDR ACM 的线性 1.0 是显示参考白，不使用 HDR 桌面的绝对亮度比例。
    local v=SdrValues(false)
    v['target-prim'],v['target-trc']='bt.709','scrgb'
    v['target-peak'],v['hdr-reference-white']=80,80
    -- 此处是交给系统的标准工作色彩空间，不再次做物理面板黑位补偿。
    v['target-contrast']='inf'
    v['d3d11-output-format'],v['d3d11-output-csp']='rgba16f','linear'
    v['target-colorspace-hint']=true
    v['dither-depth']='no'
    local source=mp.get_property_native('video-params',{}) or {}
    local primaries=source.primaries
    if primaries=='bt.2020' or primaries=='display-p3' or primaries=='dci-p3' then
        -- 广色域在线性 scRGB 中保留负分量，终端校色交给 Windows。
        v['target-gamut']=primaries
    end
    local ok,err=Update(v)
    reason=failure or ''
    if icc then reason='Windows ACM 已启用，显示校色由系统处理，不叠加显示 ICC' end
    if not ok then reason=err;Publish('失败');msg.error(err);return false end
    mode='准备 SDR ACM 输出';Publish('准备中')
    local token,started=generation,mp.get_time()
    local function Check()
        if token~=generation then return end
        if SystemColor().mode~='wcg' then timer=nil;Sdr('SDR ACM 状态已改变，恢复 SDR 基线',icc);return end
        local p=mp.get_property_native('video-target-params',{}) or {}
        if p.gamma=='scrgb' and p.pixelformat=='rgba16hf' and p.primaries=='bt.709' then
            timer=nil;mode='sdr-acm';Publish('可用')
        elseif mp.get_time()-started>=math.max(1,tonumber(o.verify_timeout) or 3) then
            timer=nil;Sdr('SDR ACM 浮点输出未协商成功，使用 SDR sRGB 兼容输出')
        else timer=mp.add_timeout(.2,Check) end
    end
    timer=mp.add_timeout(.2,Check)
    return true
end
local function TrustedICC()
    local p=Preference()
    if p.icc_context and IccContext() and p.icc_context~=IccContext() then
        return nil,'系统显示模式或 ICC 关联已改变；请重新选择可信 ICC'
    end
    return p.icc
end
local function Verify(backend,peak,contrast)
    local token,started=generation,mp.get_time()
    local function Check()
        if token~=generation then return end
        local _,active,supported=Display()
        if not active or not supported then timer=nil;Sdr('HDR 能力或桌面状态已改变，使用 SDR 基线');return end
        local p=mp.get_property_native('video-target-params',{}) or {}
        local accepted=backend=='scrgb' and p.gamma=='scrgb' and p.pixelformat=='rgba16hf' and p.primaries=='bt.709'
            or backend=='pq' and p.gamma=='pq' and p.pixelformat=='rgb10a2' and p.primaries=='bt.2020'
        if accepted then timer=nil;mode='hdr-'..backend;Publish('可用（HDR 实机色准待测）')
        elseif mp.get_time()-started>=math.max(1,tonumber(o.verify_timeout) or 3) then
            if backend=='scrgb' then
                reason='FP16 未协商成功，尝试 PQ 兼容输出'
                local ok,err=Update(HdrValues('pq',peak,contrast))
                if ok then Verify('pq',peak,contrast) else timer=nil;Sdr('PQ 应用失败：'..err) end
            else timer=nil;Sdr('HDR 输出验证超时，使用 SDR 基线') end
        else timer=mp.add_timeout(.2,Check) end
    end
    timer=mp.add_timeout(.2,Check)
end
Select=function(choice,origin)
    if choice~='auto' and choice~='sdr' and choice~='icc' and choice~='hdr' and choice~='restore' then return end
    if (origin=='internal' or origin=='legacy') and manual or origin=='display' and next(drift) then Publish();return end
    if origin~='internal' and origin~='legacy' and origin~='display' then
        manual=choice~='auto';requested=choice;drift={}
    end
    Cancel();reason=''
    if choice=='restore' then
        local ok,err=Update()
        if ok then mode='原目标';drift={} else reason=err;msg.error(err) end
        Publish(ok and '可用' or '失败');return
    end
    local d,active,supported=Display();local peak=Peak()
    if choice=='auto' then
        if active and supported then choice='hdr'
        else
            choice='sdr'
            if not d.uid or d['hdr-status']==nil or d['hdr-supported']==nil then reason='显示器身份／HDR 能力或状态未知，使用 SDR sRGB 基线' end
        end
    end
    if choice=='hdr' then
        if not active or not supported or not peak or peak<=203 or mp.get_property('gpu-api')~='d3d11' then
            local why=not active and 'Windows HDR 未开启或状态未知' or not supported and '显示器 HDR 能力未知'
                or (not peak or peak<=203) and 'HDR 峰值未知或不足；可按此显示器保存可信峰值'
                or '当前 HDR 输出路线需要 D3D11'
            SdrManaged(why..'，使用 SDR 基线');return
        end
        local backend=o.hdr_backend=='pq' and 'pq' or 'scrgb'
        local contrast=o.hdr_contrast;local minimum=tonumber(d['min-luminance'])
        if contrast=='auto' and backend=='scrgb' then
            -- scRGB 是交给系统的工作空间；保留绝对亮度，不按未实测面板黑位抬黑。
            contrast='inf'
        elseif contrast=='auto' and minimum and minimum>0 then
            local ratio=peak/minimum
            if ratio>=10 and ratio<=1000000 then contrast=tostring(ratio) end
        end
        -- 同一有效目标只更新发生变化的选项，不撤轨重建。
        if mode=='hdr-pq' and origin=='internal' then backend='pq' end
        local ok,err=Update(HdrValues(backend,peak,contrast))
        if not ok then reason='应用失败：'..err;Publish('失败');msg.error(reason);return end
        mode='准备 HDR 输出';Publish('准备中');Verify(backend,peak,contrast)
    else
        local icc
        if choice=='icc' then
            icc=Preference().icc or true
            local ok,err=SavePreference('icc',icc)
            if not ok then reason=err end
        elseif requested=='auto' then
            local why;icc,why=TrustedICC();reason=why or reason
        end
        SdrManaged(reason,icc)
    end
end
mp.register_script_message('color-select',Select)
mp.register_script_message('color-status',function() Publish();mp.commandv('script-message','show-color-status') end)
mp.register_script_message('color-peak',function(value)
    local peak=tonumber(value)
    if not peak or peak<0 or peak>10000 then mp.osd_message('请输入 0～10000 nits 的可信峰值，0 使用系统报告',4);return end
    local ok,err=SavePreference('peak',peak>0 and peak or nil)
    if not ok then msg.error(err);mp.osd_message(err,4);return end
    Select(requested=='auto' and 'auto' or 'hdr');Publish()
end)
mp.register_script_message('color-icc',function(path)
    if not path or path=='' then return end
    local ok,err=SavePreference('icc',mp.command_native({'expand-path',path}))
    if not ok then msg.error(err);mp.osd_message(err,4);return end
    Select('icc')
end)
for _,key in ipairs(keys) do
    mp.observe_property(key,'native',function(_,value)
        if key=='target-gamut' and value=='' then value='auto' end
        if writing then observed[key]=value;return end
        if observed[key]==nil then observed[key]=value;return end
        observed[key]=value
        if owned[key]~=nil and not Same(value,owned[key]) then
            Cancel();drift[key]=value;manual=true;reason='用户或其他脚本覆盖了 '..key..'；自动匹配暂缓'
            Publish('外部覆盖')
        end
    end)
end
local last_display_info
local function DisplayChanged()
    local d=Display()
    -- JSON 对象键序不具有语义，不能用序列化顺序判断同一显示器信息变化。
    local signature={display=d,system=SystemColor()}
    if SameNative(signature,last_display_info) then return end
    last_display_info=signature
    if not manual and requested=='auto' then Select('auto','internal')
    elseif requested=='hdr' and not next(drift) then Select('hdr','display')
    elseif requested=='sdr' and not next(drift) then
        -- 手动 SDR 选择保持；桌面 ACM 状态改变时仍需切换相应的输出编码。
        Cancel();SdrManaged('',false)
    elseif requested=='icc' and not next(drift) then
        -- 手动信任只属于保存时的显示身份／桌面模式，不自动信任另一个屏幕。
        Cancel()
        local icc,why=TrustedICC()
        SdrManaged(why or (icc and '' or '当前显示器没有用户明确选择的可信 ICC，使用 SDR 基线'),icc)
    else Publish() end
end
mp.observe_property('user-data/display-info','native',DisplayChanged)
mp.observe_property('user-data/display-color','native',DisplayChanged)
local last_source_primaries
mp.observe_property('video-params/primaries','string',function(_,value)
    if value==last_source_primaries then return end
    last_source_primaries=value
    -- 起播显示信息可能先于第一帧到达；在源原色就绪后补齐 scRGB 色域。
    if value and not next(drift) and requested~='restore' then
        Select(requested,requested=='auto' and 'internal' or 'display')
    end
end)
local last_target_params
mp.observe_property('video-target-params','native',function(_,value)
    -- 核心可能每帧通知同一目标；只在实际内容变化时重读选项并发布状态。
    if SameNative(value,last_target_params) then return end
    last_target_params=value
    Publish()
end)
mp.register_event('start-file',function() Cancel();playback_retry=nil end)
mp.register_event('file-loaded',function()
    if not manual and requested=='auto' then Select('auto','internal')
    elseif requested=='hdr' and mode=='准备 HDR 输出' then
        local peak=Peak();if peak then Verify(o.hdr_backend=='pq' and 'pq' or 'scrgb',peak,o.hdr_contrast) end
    else Publish() end
end)
mp.register_event('end-file',Cancel)
mp.register_event('shutdown',function() Cancel();local ok,err=Update();if not ok then msg.error(err) end end)
Publish()
