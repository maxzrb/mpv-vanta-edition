-- 一次选择直接启用；只处理实际加载错误，不扫描组件、不模拟试跑。
-- License: MIT
local mp = require 'mp'
local utils = require 'mp.utils'
local msg = require 'mp.msg'
local presets = {
    {id='fsrcnnx', group='upscale', title='通用 Shader · FSRCNNX', shader='FSRCNNX/FSRCNNX_x2_8_0_4_1.glsl'},
    {id='artcnn', group='upscale', title='动画 Shader · ArtCNN C4F16', shader='ArtCNN/ArtCNN_C4F16.glsl'},
    {id='uai-dml', group='upscale', title='AI 超分 · DirectML', script='MIX_UAI_DML.vpy'},
    {id='uai-migx', group='upscale', title='AI 超分 · AMD MIGraphX', script='MIX_UAI_MIGX.vpy'},
    {id='uai-trt', group='upscale', title='AI 超分 · NVIDIA TensorRT', script='MIX_UAI_NV_TRT.vpy'},
    {id='artcnn-nv', group='upscale', title='ArtCNN · NVIDIA TensorRT', script='SR_ARTCNN_NV.vpy'},
    {id='mvt', group='memc', title='MVTools 二倍帧', script='MEMC_MVT_LQ.vpy'},
    {id='rife-dml', group='memc', title='RIFE 4.25 Lite · DirectML 二倍帧', script='MEMC_RIFE_DML.vpy'},
    {id='rife-dml-426', group='memc', title='RIFE 4.26 · DirectML 二倍帧', script='MEMC_RIFE_DML_426.vpy'},
    {id='rife-dml-heavy', group='memc', title='RIFE 4.26 Heavy · DirectML 二倍帧', script='MEMC_RIFE_DML_426_HEAVY.vpy'},
    {id='rife-dml-720', group='memc', title='RIFE DirectML · 720p 性能模式', script='MEMC_RIFE_DML_PERF_720.vpy'},
    {id='rife-std', group='memc', title='RIFE-STD · NCNN（独立后端）', script='MEMC_RIFE_STD.vpy'},
    {id='rife-trt', group='memc', title='RIFE 4.25 Lite · NVIDIA TensorRT', script='MEMC_RIFE_NV.vpy'},
    {id='rife-trt-426', group='memc', title='RIFE 4.26 · NVIDIA TensorRT', script='MEMC_RIFE_NV_426.vpy'},
    {id='rife-trt-heavy', group='memc', title='RIFE 4.26 Heavy · NVIDIA TensorRT', script='MEMC_RIFE_NV_426_HEAVY.vpy'},
    {id='drba-dml', group='memc', title='DRBA · DirectML', script='MEMC_DRBA_DML.vpy'},
    {id='drba-nv', group='memc', title='DRBA · NVIDIA TensorRT', script='MEMC_DRBA_NV.vpy'},
    {id='svp', group='memc', title='SVP', script='MEMC_SVP_PRO.vpy'},
    {id='ccd', group='denoise', title='CCD 彩噪降低', script='NR_CCD_STD.vpy'},
    {id='bm3d', group='denoise', title='BM3D · NVIDIA CUDA', script='NR_BM3D_NV.vpy'},
}
local by_id = {}
for _,p in ipairs(presets) do by_id[p.id]=p end
local active, stable_active, owned_shaders, baseline, written = {}, {}, {}, {}, {}
local labels = {['quality-denoise']=true,['quality-upscale']=true,['quality-memc']=true}
local function managed(filter)
    return labels[filter.label]
end
local state, last_error, warning, generation, attempt = '未启用','','',0,nil
local performance = 'balanced'
local function expand(path)
    local result=mp.command_native({'expand-path',path})
    -- 隔离脚本测试也使用脚本所在配置根；不依赖进程的工作目录。
    if path:sub(1,3)=='~~/' and result==path:sub(4) then
        local directory=mp.get_script_directory() or utils.split_path(debug.getinfo(1,'S').source:gsub('^@',''))
        return utils.join_path(directory,'../'..path:sub(4))
    end
    return result
end
local performance_profiles={balanced='Performance-Balanced',['high-quality']='Performance-HighQuality'}
local preferences_path=expand('~~/files/quality-preferences.json')
local preferences_file=io.open(preferences_path,'r')
if preferences_file then
    local preferences=utils.parse_json(preferences_file:read('*a')) or {};preferences_file:close()
    if type(preferences)=='table' and performance_profiles[preferences.performance] then performance=preferences.performance end
end
local function list(name) return mp.get_property_native(name,{}) or {} end
local function copy(t) local r={}; for k,v in pairs(t) do r[k]=v end; return r end
local function svp_passthrough(selection)
    -- 用户确认固定 59.94 目标；约 60fps 的计时偏差不值得重算整幅运动场。
    local value=mp.get_property_native('container-fps')
    local fps=tonumber(value)
    if selection.memc~='svp' or not fps or fps<60000/1001*0.999 then return false end
    -- 外部帧率改写／VS 的实际输入须由 vpy 判断，不能用容器帧率跳过真实补帧。
    for _,filter in ipairs(list('vf')) do
        if not managed(filter) and filter.enabled~=false then
            local graph=tostring(type(filter.params)=='table' and filter.params.graph or '')
            if filter.name=='fps' or filter.name=='framerate' or filter.name=='vapoursynth'
                or graph:find('%f[%a]fps%f[%A]') or graph:find('framerate')
                or graph:find('minterpolate') or graph:find('setpts') then return false end
        end
    end
    return true
end
local function publish()
    local chain={}
    local pending={}
    local note=svp_passthrough(active) and 'SVP：原片已达到 59.94fps 目标，保留原帧；未运行运动估计' or ''
    for key in pairs(written) do pending[#pending+1]=key end
    for _,group in ipairs({'denoise','upscale','memc'}) do
        local p=by_id[active[group]]
        if p then chain[#chain+1]={group=group,id=p.id,title=p.title} end
    end
    mp.set_property_native('user-data/quality',{active=copy(active),state=state,error=last_error,chain=chain,
        warning=warning,note=note,performance=performance,restore_pending=pending,preparing='',capabilities={}})
end
local function warn_color()
    local p=mp.get_property_native('video-params',{}) or {}
    warning=(p.gamma=='pq' or p.gamma=='hlg' or p['dolby-vision-profile']~=nil
        or p.primaries and p.primaries~='bt.709' and p.primaries~='bt.601-525' and p.primaries~='bt.601-625')
        and '本增强的 HDR／广色域色彩保真尚未验证' or ''
end
local function write_option(key,value)
    if baseline[key]==nil then baseline[key]=mp.get_property_native(key) end
    local ok,err=mp.set_property_native(key,value)
    if ok then written[key]=mp.get_property_native(key) end
    return ok,err
end
local function restore_options(keys)
    local errors={}
    for _,key in ipairs(keys) do
        if written[key]~=nil then
            if mp.get_property_native(key)==written[key] then
                local ok,err=mp.set_property_native(key,baseline[key])
                if not ok then
                    errors[#errors+1]='恢复增强选项失败：'..key..' '..tostring(err)
                    msg.error(errors[#errors])
                else baseline[key],written[key]=nil,nil end
            else baseline[key],written[key]=nil,nil end
        end
    end
    return #errors==0,table.concat(errors,'\n')
end
local function shaders_without_owned()
    local r={}
    for _,path in ipairs(list('glsl-shaders')) do if not owned_shaders[path] then r[#r+1]=path end end
    return r
end
local function filters_for(selection,before)
    local r={}
    for _,f in ipairs(before or list('vf')) do if not managed(f) then r[#r+1]=f end end
    for _,group in ipairs({'denoise','upscale','memc'}) do
        local p=by_id[selection[group]]
        if p and p.script and not (group=='memc' and svp_passthrough(selection)) then
            r[#r+1]={name='vapoursynth',label='quality-'..group,
                params={file=expand('~~/vs/'..p.script),['concurrent-frames']='4'}}
        end
    end
    return r
end
local function cancel_attempt() generation=generation+1; attempt=nil; mp.enable_messages('error') end
local function fail_attempt(error_text)
    local op=attempt
    if not op or op.generation~=generation then return end
    attempt=nil; mp.enable_messages('error')
    -- 只替换本管理链，保留当前外部滤镜。
    local ok,err=mp.set_property_native('vf',filters_for(op.before_active))
    local shader=active.shader
    active=copy(op.before_active);active.shader=shader;stable_active=copy(active)
    local restore_error=''
    if not active.memc then local _;_,restore_error=restore_options({'interpolation'}) end
    state,last_error='失败',op.title..'：'..tostring(error_text)
    if not ok then last_error=last_error..'\n原链恢复失败：'..tostring(err) end
    if restore_error~='' then last_error=last_error..'\n'..restore_error end
    msg.error(last_error); publish(); mp.osd_message(last_error,6)
end
local function apply_filters(selection,title)
    cancel_attempt()
    local filters=filters_for(selection)
    local expected=0
    for _,filter in ipairs(filters) do if managed(filter) then expected=expected+1 end end
    attempt={generation=generation,before_active=copy(stable_active),title=title,expected=expected,initialized=0}
    mp.enable_messages('debug')
    state,last_error='启用中',''; publish()
    mp.osd_message('正在启用：'..title..'\n首次模型／引擎初始化请等待',4)
    local had_managed=false
    for _,filter in ipairs(list('vf')) do if managed(filter) then had_managed=true;break end end
    local paused=mp.get_property_native('pause')
    if had_managed then
        -- 明确销毁旧管理链，避免上游尺寸／顺序变化时复用带旧时间戳的 VS 实例。
        mp.set_property_native('pause',true)
        local cleared,clear_err=mp.set_property_native('vf',filters_for({}))
        if not cleared then mp.set_property_native('pause',paused);fail_attempt(clear_err);return false end
    end
    local ok,err=mp.set_property_native('vf',filters)
    if had_managed then mp.set_property_native('pause',paused) end
    if not ok then fail_attempt(err or '实际滤镜加载失败'); return false end
    active=selection
    if active.memc then
        local changed,change_err=write_option('interpolation',false)
        if not changed then fail_attempt('关闭播放器插值失败：'..tostring(change_err));return false end
    else
        local restored,restore_err=restore_options({'interpolation'})
        if not restored then attempt.restore_error=restore_err end
    end
    publish()
    if expected==0 then
        stable_active=copy(active);last_error=attempt.restore_error or ''
        state=last_error=='' and '已添加' or '失败'
        attempt=nil;mp.enable_messages('error');publish()
        if svp_passthrough(active) then mp.osd_message('SVP：已达到 59.94fps 目标，保留原帧，无需运动估计',4) end
    end
    return true
end
local function reset()
    cancel_attempt()
    mp.set_property_native('vf',filters_for({}))
    mp.set_property_native('glsl-shaders',shaders_without_owned())
    active,stable_active,owned_shaders={},{},{}
    local restored,restore_err=restore_options({'interpolation','video-sync','deband'})
    state,last_error,warning=restored and '未启用' or '失败',restore_err,''; publish()
end
local function select_preset(id)
    if id=='rife' then id='rife-dml' end
    local p=by_id[id]
    if not p then return end
    if not mp.get_property_native('video-params') then mp.osd_message('请先打开视频',3); return end
    warn_color()
    if p.shader then
        local path=expand('~~/shaders/'..p.shader)
        local r,present=shaders_without_owned(),false
        for _,item in ipairs(r) do if item==path then present=true end end
        if not present then r[#r+1]=path end
        local ok,err=mp.set_property_native('glsl-shaders',r)
        if not ok then state,last_error='失败',tostring(err); publish(); return end
        owned_shaders,active.shader={[path]=not present},id
        stable_active.shader=id
        state,last_error='已添加',''; publish()
        mp.osd_message('已添加：'..p.title..(warning~='' and '\n'..warning or ''),4); return
    end
    -- 同一方案保持幂等；上游变化时保留补帧并一次重建管理链。
    if active[p.group]==id and not (id=='svp' and svp_passthrough(active)) then
        for _,f in ipairs(list('vf')) do
            if f.enabled~=false and f.label=='quality-'..p.group then publish();return end
        end
    end
    local selection=copy(active); selection[p.group]=id
    apply_filters(selection,p.title)
end
local function disable_group(group)
    if group:match('^shader%-') then
        mp.set_property_native('glsl-shaders',shaders_without_owned()); owned_shaders={}; active.shader=nil;stable_active.shader=nil; publish(); return
    end
    group=group:gsub('^vs%-',''):gsub('^nv%-','')
    local selection=copy(active); selection[group]=nil
    apply_filters(selection,'关闭此类增强')
end
mp.register_script_message('quality-select',select_preset)
mp.register_script_message('quality-menu',function(group)
    group=group or 'upscale'
    local category=group:gsub('^nv%-',''):gsub('^vs%-',''):gsub('^shader%-','')
    local items={{title='关闭此类增强',value={'script-message','quality-disable',group=='upscale' and 'shader-upscale' or group}}}
    if category=='memc' then
        items[#items+1]={title='mpv 轻量插值',value={'script-message','quality-interpolation'},selectable=true,
            active=mp.get_property_bool('interpolation',false)}
    elseif category=='denoise' then
        items[#items+1]={title='去色带',value={'script-message','quality-deband'},selectable=true,
            active=mp.get_property_bool('deband',false)}
    end
    for _,p in ipairs(presets) do
        local belongs=p.group==category
        if group:match('^nv%-') then belongs=belongs and p.title:find('NVIDIA',1,true)~=nil end
        if group:match('^vs%-') then belongs=belongs and p.script~=nil end
        if group:match('^shader%-') or group=='upscale' then belongs=belongs and p.shader~=nil end
        if belongs then items[#items+1]={title=p.title,value={'script-message','quality-select',p.id},
            hint='点击直接启用',selectable=true,active=active[p.shader and 'shader' or category]==p.id} end
    end
    mp.commandv('script-message-to','uosc','open-menu',utils.format_json({type='quality-'..group,title='画质处理',items=items}))
end)
mp.register_script_message('quality-shader-preset',function(profile)
    if not profile or not (profile:match('^Preset%-') or profile:match('^Anime4K%-')) then return end
    if not mp.get_property_native('video-params') then mp.osd_message('请先打开视频',3); return end
    warn_color()
    local _,err=mp.command_native({'apply-profile',profile})
    if err then state,last_error='失败',tostring(err); publish(); return end
    owned_shaders={}; for _,path in ipairs(list('glsl-shaders')) do owned_shaders[path]=true end
    active.shader=profile;stable_active.shader=profile; state,last_error='已添加',''; publish()
    mp.osd_message('已添加：'..profile..(warning~='' and '\n'..warning or ''),4)
end)
mp.register_script_message('quality-shader-command',function(command)
    if type(command)~='string' then return end
    warn_color()
    local external={};for _,path in ipairs(shaders_without_owned()) do external[path]=true end
    local ok,result,err=pcall(mp.command,command)
    if not ok or err then state,last_error='失败',tostring(err or result);msg.error(last_error)
    else
        owned_shaders={}
        for _,path in ipairs(list('glsl-shaders')) do if not external[path] then owned_shaders[path]=true end end
        active.shader=next(owned_shaders) and (command:match('apply%-profile%s+([^;%s]+)') or '手动 Shader') or nil
        stable_active.shader=active.shader
        if state~='启用中' then state,last_error='已添加','' end
    end
    publish(); if warning~='' then mp.osd_message(warning,4) end
end)
mp.register_script_message('quality-clear-shaders',function()
    mp.set_property_native('glsl-shaders',{}); owned_shaders={}; active.shader=nil;stable_active.shader=nil; publish()
end)
mp.register_script_message('quality-clear-filters',function()
    cancel_attempt(); mp.set_property_native('vf',{})
    active.denoise,active.upscale,active.memc=nil,nil,nil
    stable_active=copy(active)
    local restored,restore_err=restore_options({'interpolation'})
    state,last_error=restored and '未启用' or '失败',restore_err;publish()
end)
mp.register_script_message('quality-disable',disable_group)
mp.register_script_message('quality-reset',reset)
mp.register_script_message('quality-cancel',function() if attempt then fail_attempt('用户取消启用') end; cancel_attempt() end)
mp.register_script_message('quality-interpolation',function()
    if active.memc then disable_group('memc') end
    local enabled=not mp.get_property_bool('interpolation',false)
    write_option('interpolation',enabled)
    if enabled then write_option('video-sync','display-resample') else restore_options({'video-sync'}) end
    publish()
end)
mp.register_script_message('quality-deband',function() write_option('deband',not mp.get_property_bool('deband',false)); publish() end)
mp.register_script_message('quality-performance',function(value)
    if not performance_profiles[value] then return end
    local _,err=mp.command_native({'apply-profile',performance_profiles[value]})
    if err then msg.error('性能档位应用失败：'..tostring(err)); return end
    performance=value
    local file,save_err=io.open(preferences_path,'w')
    if file then file:write(utils.format_json({performance=value}));file:close()
    else msg.error('保存性能偏好失败：'..tostring(save_err)) end
    publish();mp.osd_message('性能档位：'..performance_profiles[value],3)
end)
-- 只订阅实际加载错误；不会为菜单启动子进程。
mp.enable_messages('error')
mp.register_event('log-message',function(event)
    if not attempt or attempt.generation~=generation then return end
    local prefix=event.prefix or ''
    if prefix:find('vapoursynth',1,true) and (event.text or ''):match('^initialized%.%s*$') then
        attempt.initialized=attempt.initialized+1
        if attempt.initialized>=attempt.expected and not attempt.errors then
            attempt.ready=true
        end
        return
    end
    if event.level~='error' and event.level~='fatal' then return end
    if prefix:find('vapoursynth',1,true) or prefix:find('ffmpeg',1,true) and (event.text or ''):find('vapoursynth',1,true) then
        local op=attempt
        op.errors=op.errors or {}
        op.errors[#op.errors+1]=(event.text or '实际滤镜加载失败'):gsub('%s+$','')
        if not op.error_timer then
            -- 收齐实际初始化的 traceback，避免只显示通用的第一行。
            op.error_timer=mp.add_timeout(0.05,function()
                if attempt==op then fail_attempt(table.concat(op.errors,'\n')) end
            end)
        end
    end
end)
local function complete_attempt()
    if attempt and attempt.ready and not attempt.errors and not attempt.completed then
        attempt.completed=true
        stable_active=copy(active);last_error=attempt.restore_error or ''
        state=last_error=='' and '已添加' or '失败';publish();mp.enable_messages('error')
        mp.osd_message('已添加：'..attempt.title..(warning~='' and '\n'..warning or ''),4)
    end
end
mp.register_event('playback-restart',complete_attempt)
-- 同帧率滤镜可能只重配置输出，不触发帧率变化或再次播放启动。
mp.register_event('video-reconfig',complete_attempt)
mp.observe_property('estimated-vf-fps','number',function(_,value)
    if value and value>0 and state=='启用中' then complete_attempt() end
end)
mp.register_event('start-file',reset)
mp.register_event('end-file',reset)
mp.register_event('shutdown',cancel_attempt)
-- 默认明确应用 HQ；退役低功耗偏好自动回到默认档。
do
    local _,err=mp.command_native({'apply-profile',performance_profiles[performance]})
    if err then msg.error('恢复性能档位失败：'..tostring(err)) end
end
publish()
