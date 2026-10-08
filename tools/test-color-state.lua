-- 故障注入验证恢复重试、免重建、外部覆盖、能力变化与 HDR 软件协商。
local props={['gpu-api']='d3d11',vid=1,pause=false,seekable=true,['time-pos']=12,
    ['video-params']={gamma='pq'},['target-trc']='gamma2.2',['target-prim']='bt.709',
    ['target-peak']='auto',['target-contrast']='auto',['target-gamut']='',['dither-depth']='auto',['icc-profile']='',['icc-profile-auto']=false,
    ['icc-intent']=1,['target-colorspace-hint']=false,['target-colorspace-hint-mode']='target',
    ['target-colorspace-hint-strict']=true,['d3d11-output-format']='auto',['d3d11-output-csp']='srgb',
    ['hdr-reference-white']='auto',['inverse-tone-mapping']=false,['hdr-contrast-recovery']=0,
    ['treat-srgb-as-power22']='no',['video-target-params']={gamma='srgb',pixelformat='rgb10a2'}}
local messages,events,observers,timers,writes={},{},{},{},{}
local now,fail_key,fail_value,fail_once=0,nil,nil,false
local mp={}
function mp.get_property_native(k,d) if props[k]==nil then return d end;return props[k] end
function mp.get_property(k) return props[k] end
function mp.get_time() return now end
function mp.set_property_native(k,v)
    if k==fail_key and v==fail_value then
        if fail_once then fail_key=nil;fail_once=false end
        return nil,'故障注入 '..k
    end
    props[k]=v;writes[#writes+1]={k,v}
    if observers[k] then observers[k](k,v) end
    return true
end
function mp.command_native(a) if a[1]=='expand-path' then return 'tmp/modernization/optimization-20261005/color-test-prefs.json' end;return true end
function mp.commandv() end
function mp.osd_message() end
function mp.add_timeout(_,fn) local t={fn=fn};function t:kill() self.stopped=true end;timers[#timers+1]=t;return t end
function mp.observe_property(k,_,f) observers[k]=f end
function mp.register_event(k,f) events[k]=f end
function mp.register_script_message(k,f) messages[k]=f end
package.loaded.mp=mp;package.loaded['mp.msg']={error=function() end}
package.loaded['mp.options']={read_options=function() end}
package.loaded['mp.utils']={parse_json=function() return {} end,format_json=function(t)
    local r={};for k,v in pairs(t) do r[#r+1]=tostring(k)..'='..tostring(v) end;table.sort(r);return table.concat(r,'|')
end}
dofile('portable_config/scripts/color-target.lua')
for k,f in pairs(observers) do if k~='user-data/display-info' then f(k,props[k]) end end
local status_writes=#writes
observers['video-target-params']('video-target-params',{gamma='srgb',pixelformat='rgb10a2'})
assert(#writes==status_writes,'相同目标的新对象不能重复发布')
props['video-target-params']={gamma='srgb',pixelformat='rgb10a2',['max-luma']=100,hdr={peak=100}}
observers['video-target-params']('video-target-params',props['video-target-params'])
assert(#writes==status_writes+1,'真实亮度／嵌套元数据变化须发布')
status_writes=#writes
observers['video-target-params']('video-target-params',{gamma='srgb',pixelformat='rgb10a2',['max-luma']=100,hdr={peak=100}})
assert(#writes==status_writes)
props['video-target-params']={gamma='srgb',pixelformat='rgb10a2',par=0/0,hdr={peak=100}}
observers['video-target-params']('video-target-params',props['video-target-params'])
status_writes=#writes
observers['video-target-params']('video-target-params',{gamma='srgb',pixelformat='rgb10a2',par=0/0,hdr={peak=100}})
assert(#writes==status_writes,'两个未知 NaN 值不能触发逐帧重复发布')
props['video-target-params']={gamma='srgb',pixelformat='rgb10a2',par=1,hdr={peak=100}}
observers['video-target-params']('video-target-params',props['video-target-params'])
assert(#writes==status_writes+1,'NaN 变为已知值须发布')
local function status() return props['user-data/color-target'] end
local function tick(dt) now=now+dt;local t=timers[#timers];assert(t and not t.stopped);t.fn() end
local function display(supported,on,uid,peak)
    props['user-data/display-info']={uid=uid or 'A',['hdr-supported']=supported,['hdr-status']=on and 'on' or 'off',['max-luminance']=peak or 1000,['min-luminance']=.01,['bit-depth']=10}
    observers['user-data/display-info']()
end
messages['color-select']('auto')
assert(status().mode=='sdr' and status().reason:find('未知') and props['target-trc']=='srgb')
messages['color-select']('restore')
fail_key,fail_value='target-trc','gamma2.2'
messages['color-select']('sdr')
messages['color-select']('restore')
assert(status().status=='失败' and status().reason:find('target%-trc') and #status().restore_pending>0,'恢复失败须保留基线')
fail_key=nil;messages['color-select']('restore')
assert(props['target-trc']=='gamma2.2' and #status().restore_pending==0,'恢复重试成功')
messages['color-select']('auto');display(true,true)
assert(props['target-trc']=='scrgb' and status().status=='准备中')
props['video-target-params']={gamma='scrgb',primaries='bt.709',pixelformat='rgba16hf'}
tick(.2);assert(status().mode=='hdr-scrgb')
local before=#writes
events['start-file']();events['file-loaded']()
for i=before+1,#writes do assert(writes[i][1]~='vid','同输出切集不撤轨') end
tick(.2)
mp.set_property_native('target-trc','gamma2.4')
assert(status().manual and status().external_overrides['target-trc']=='gamma2.4')
events['file-loaded']();assert(props['target-trc']=='gamma2.4','自动管理尊重外部覆盖')
messages['color-select']('hdr')
assert(props['target-trc']=='scrgb' and not next(status().external_overrides),'主动重选重新应用')
tick(.2)
messages['color-select']('auto');tick(.2)
assert(not status().manual and status().requested=='auto')
display(false,true)
assert(props['target-trc']=='srgb','HDR 支持信息变化必须重判')
display(true,true)
props['video-target-params']={gamma='srgb',pixelformat='rgb10a2'}
tick(4);assert(props['target-trc']=='pq')
props['video-target-params']={gamma='pq',primaries='bt.2020',pixelformat='rgb10a2'}
tick(.2);assert(status().mode=='hdr-pq')
local old=timers[#timers]
messages['color-select']('sdr');old.fn();assert(status().mode=='sdr')
messages['color-select']('hdr')
props['video-target-params']={gamma='srgb',pixelformat='rgb10a2'}
tick(4);tick(4);assert(status().mode=='sdr' and status().reason:find('超时'))
fail_key,fail_value='vid',1
messages['color-select']('hdr')
assert(status().status=='失败' and props.vid=='no' and #status().restore_pending>0,'持续重建失败保留原轨基线')
fail_key=nil;messages['color-select']('restore')
assert(status().status=='可用' and props.vid==1 and props.pause==false and props['time-pos']==12,'恢复轨道也必须能重试')
messages['color-select']('sdr')
fail_key,fail_value,fail_once='vid',1,true
messages['color-select']('hdr')
assert(status().status=='失败' and props['target-trc']=='srgb' and props.vid==1 and props.pause==false,'输出重建失败回退原目标与播放状态')
fail_key,fail_value='target-trc','scrgb'
messages['color-select']('hdr')
assert(status().status=='失败' and props['target-trc']=='srgb' and props['icc-profile-auto']==false,'部分写入失败事务回滚')
fail_key=nil;messages['color-select']('hdr')
props['video-target-params']={gamma='scrgb',primaries='bt.709',pixelformat='rgba16hf'};tick(.2)
mp.set_property_native('target-contrast','1234')
messages['color-select']('restore');assert(props['target-contrast']=='1234','保留外部改写')
messages['color-select']('sdr')
assert(props.pause==false and props.vid==1 and props['time-pos']==12)
messages['color-select']('hdr')
local stale=timers[#timers];events['start-file']();stale.fn()
assert(status().status=='准备中','文件切换使旧回调失效')
events['file-loaded']();tick(.2)
messages['color-select']('auto')
display(true,false)
props['user-data/display-color']={mode='wcg',identity='native-A',system_icc='A.icc'}
observers['user-data/display-color']()
props['video-target-params']={gamma='scrgb',primaries='bt.709',pixelformat='rgba16hf'};tick(.2)
assert(status().mode=='sdr-acm' and props['target-peak']==80 and props['hdr-reference-white']==80)
assert(props['dither-depth']=='no','浮点输出不能提前量化')
messages['color-select']('icc');tick(.2)
assert(status().mode=='sdr-acm' and props['icc-profile-auto']==false,'ACM 不叠加显示 ICC')
local acm_before=#writes
events['start-file']();events['file-loaded']()
for i=acm_before+1,#writes do assert(writes[i][1]~='vid','同 ACM 输出切集不能重建') end
-- 关闭 ACM 恢复经典 SDR；不得自动继承 ACM 模式中的显示 ICC。
props['user-data/display-color']={mode='sdr',identity='native-A',system_icc='A.icc'}
observers['user-data/display-color']()
assert(props['target-trc']=='srgb' and props['dither-depth']=='auto' and not props['icc-profile-auto'])
messages['color-select']('sdr')
props['user-data/display-color']={mode='wcg',identity='native-A',system_icc='A.icc'}
observers['user-data/display-color']();tick(.2)
assert(status().mode=='sdr-acm' and status().requested=='sdr' and status().manual)
props['user-data/display-color']={mode='hdr',identity='native-A',system_icc='A.icc'}
observers['user-data/display-color']()
assert(status().mode=='sdr' and props['target-trc']=='srgb','手动 SDR 在桌面切换后须恢复合适输出')

-- 原生配置组部分应用失败也须恢复原输出；不能依赖单属性回滚测试覆盖。
props['profile-list']={{name='Color-Output-SDR'},{name='Color-Output-scRGB'}}
local command_original=mp.command_native
local partial_profile=true
function mp.command_native(a)
    if a[1]=='apply-profile' then
        local scrgb=a[2]=='Color-Output-scRGB'
        mp.set_property_native('d3d11-output-format',scrgb and 'rgba16f' or 'auto')
        if scrgb and partial_profile then return nil,'配置组部分故障' end
        mp.set_property_native('d3d11-output-csp',scrgb and 'linear' or 'srgb')
        return true
    end
    return command_original(a)
end
props['user-data/display-color']={mode='wcg',identity='native-A',system_icc='A.icc'}
observers['user-data/display-color']()
assert(status().status=='失败' and props['d3d11-output-format']=='auto' and props['d3d11-output-csp']=='srgb')
assert(props.vid==1 and props.pause==false,'配对失败不能丢掉播放状态')
partial_profile=false
messages['color-select']('sdr');tick(.2)
assert(status().mode=='sdr-acm' and props['d3d11-output-format']=='rgba16f' and props['d3d11-output-csp']=='linear')
events['shutdown']()
io.write('色彩恢复重试／事务／免重建／覆盖／HDR 软件协商 PASS\n')
