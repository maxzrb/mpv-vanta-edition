-- 固定输入事件和参考输出：检查恢复、动态元数据边界、滤镜所有权及失败回退。
local props={path='fixture.mkv',['current-vo']='gpu-next',vf={},['track-list']={}}
local observers,events,messages,timers,queue={},{},{},{},{}
local writes,fail_once=0,false
local mp={}
function mp.get_property(k,d) if props[k]==nil then return d end;return props[k] end
mp.get_property_native=mp.get_property
function mp.set_property_native(k,v)
    if k=='vf' and fail_once then fail_once=false;return nil,'故障注入' end
    props[k]=v
    if k=='vf' then writes=writes+1 end
    if observers[k] then queue[#queue+1]=function() observers[k](k,v) end end
    return true
end
function mp.observe_property(k,_,f) observers[k]=f end
function mp.register_event(k,f) events[k]=f end
function mp.register_script_message(k,f) messages[k]=f end
function mp.add_timeout(_,f)
    local t={fn=f};function t:kill() self.dead=true end
    timers[#timers+1]=t;return t
end
package.loaded.mp=mp
package.loaded['mp.msg']={error=function() end}
package.loaded['mp.options']={read_options=function(_,name) assert(name=='hdr-content-peak') end}
dofile('portable_config/scripts/hdr-content-peak.lua')
local function Flush()
    for _=1,30 do
        local q=queue;queue={};for _,f in ipairs(q) do f() end
        local ts=timers;timers={};for _,t in ipairs(ts) do if not t.dead then t.fn() end end
        if #queue==0 and #timers==0 then return end
    end
    error('内容峰值回调未收敛')
end
local function Source(extra)
    local p={gamma='pq',pixelformat='yuv420p10',primaries='bt.2020',
        ['max-luma']=1000,['min-luma']=.001,['max-cll']=97,['max-fall']=55}
    for k,v in pairs(extra or {}) do p[k]=v end
    mp.set_property_native('video-params',p);Flush()
end
local function Mode(pipeline,mode,overrides)
    mp.set_property_native('user-data/color-target',{pipeline=pipeline,mode=mode,external_overrides=overrides});Flush()
end
local function Peak()
    for _,f in ipairs(props.vf) do if f.label=='hdr-content-peak' then return tonumber(f.params['max-luma']) end end
end
local function Pass(name) io.write(name,' PASS\n') end
local user={name='crop',label='user',params={w='256',h='256'}}
props.vf={user};Mode('hq','sdr-acm');Source()
assert(Peak()==97 and props['video-params']['max-luma']==1000 and props.vf[1]==user)
local before=writes;Source();assert(writes==before,'重复元数据不能改写滤镜链')
Source({['max-cll']=400});assert(Peak()==400)
Pass('metadata-update-and-no-redundant-rebuild')
for _,value in ipairs({0,-1,10001,0/0,math.huge}) do
    Source({['max-cll']=value});assert(not Peak() and props.vf[1]==user)
end
Source({['max-cll']=50,['max-fall']=55});assert(not Peak())
Source({['max-cll']=false});assert(not Peak())
Source();assert(Peak()==97)
Pass('invalid-and-missing-maxcll-fallback')
for _,field in ipairs({'scene-max-r','scene-max-g','scene-max-b','scene-avg','max-pq-y','avg-pq-y','dolby-vision-profile'}) do
    Source({[field]=1});assert(not Peak(),field)
end
Source({gamma='hlg'});assert(not Peak())
Source({gamma='srgb'});assert(not Peak())
Source();mp.set_property_native('track-list',{{type='video',selected=true,['dolby-vision-profile']=8}});Flush()
assert(not Peak());mp.set_property_native('track-list',{});Flush();assert(Peak()==97)
Pass('dynamic-hdr-hlg-and-sdr-preservation')
Mode('standard','standard');assert(not Peak())
Mode('hq','hdr-scrgb');assert(not Peak())
Mode('hq','hdr-pq');assert(not Peak())
Mode('hq','sdr-acm',{['target-peak']=100});assert(not Peak())
Mode('hq','sdr-acm');assert(Peak()==97)
mp.set_property_native('video-out-params',{gamma='srgb'});Flush();assert(not Peak())
mp.set_property_native('video-out-params',{gamma='pq'});Flush();assert(Peak()==97)
Pass('output-route-switch-and-external-target')
local custom={name='format',label='custom-peak',params={['max-luma']='300'}}
mp.set_property_native('vf',{user,custom,props.vf[2]});Flush();assert(not Peak() and props.vf[2]==custom)
mp.set_property_native('vf',{user});Flush();assert(Peak()==97)
mp.set_property_native('vf',{user});Flush();Source({['max-cll']=400});assert(not Peak())
messages.refresh();Flush();assert(Peak()==400)
mp.set_property_native('vf',{user,{name='format',label='hdr-content-peak',params={['max-luma']='250'}}});Flush()
events['end-file']();Flush();assert(Peak()==250,'不能删除用户接管的同名滤镜')
Pass('user-filter-ownership-and-explicit-refresh')
props.vf={user};events['start-file']();events['file-loaded']();Source();assert(Peak()==97)
fail_once=true;Source({['max-cll']=400});assert(not Peak() and props.vf[1]==user)
assert(props['user-data/hdr-content-peak'].state=='失败')
messages.refresh();Flush();assert(Peak()==400)
events['end-file']();Flush();assert(not Peak() and props.vf[1]==user)
events['start-file']();events['file-loaded']();Source();assert(Peak()==97)
Pass('failed-update-rollback-and-next-file')
