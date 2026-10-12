-- 验证校正滤镜所有权、外部改链、用户删除、切片与错误回滚。
local props={['current-vo']='gpu-next',['mpv-version']='mpv v0.41-36bf3d529',vf={}}
local observers,events,queue,timers={},{},{},{}
local fail=false
local mp={}
function mp.get_property(k,d) return props[k] or d end
function mp.get_property_native(k,d) return props[k] or d end
function mp.set_property_native(k,v)
    if fail and k=='vf' then return nil,'故障注入' end
    props[k]=v
    if observers[k] then queue[#queue+1]=function() observers[k](k,v) end end
    return true
end
function mp.observe_property(k,_,fn) observers[k]=fn end
function mp.register_event(k,fn) events[k]=fn end
function mp.add_timeout(_,fn) local t={fn=fn};function t:kill() self.dead=true end;timers[#timers+1]=t;return t end
package.loaded.mp=mp
package.loaded['mp.msg']={error=function() end}
package.loaded['mp.options']={read_options=function() end}
dofile('portable_config/scripts/color-range-fix.lua')
local function Flush()
    for _=1,20 do
        local q=queue;queue={};for _,f in ipairs(q) do f() end
        local ts=timers;timers={};for _,t in ipairs(ts) do if not t.dead then t.fn() end end
        if #queue==0 and #timers==0 then return end
    end
    error('校正回调形成循环')
end
local function Image(fmt,range)
    local p={pixelformat=fmt,colorlevels=range,colormatrix='bt.709',primaries='bt.709',gamma='srgb',w=256,h=256,alpha='none'}
    mp.set_property_native('video-out-params',p);Flush()
end
local user={name='crop',label='user-crop',params={w='256',h='256'}}
local function Start()
    props['video-out-params']=nil
    events['start-file']();events['file-loaded']();Flush()
end
events['file-loaded']();Flush()
props.vf={user};Image('yuv420p10','full')
assert(#props.vf==2 and props.vf[1]==user and props.vf[2].params.graph:find('yuv420p16le',1,true))
assert(props.vf[2].params.o=='threads=1')
Image('yuv420p16','limited');assert(props['user-data/color-range-fix'].state=='已校正')
local new={name='lavfi',label='user-rgb',params={graph='format=rgb48le'}}
mp.set_property_native('vf',{new,props.vf[2]});Flush()
Image('rgb48','full');assert(#props.vf==1 and props.vf[1]==new)
Image('yuv444p12','full');assert(#props.vf==2)
mp.set_property_native('vf',{new});Flush();Image('yuv444p12','full')
assert(#props.vf==1 and props['user-data/color-range-fix'].state=='外部已接管')
Start();Image('yuv444p12','full');assert(#props.vf==2)
local own=props.vf[2]
mp.set_property_native('vf',{new,{name='lavfi',label=own.label,params={graph='null'}}});Flush()
events['end-file']();Flush();assert(#props.vf==2,'外部接管的同名滤镜不能删除')
props.vf={user};Start();fail=true;Image('yuv444p10','full')
assert(#props.vf==1 and props.vf[1]==user and props['user-data/color-range-fix'].state=='失败')
fail=false;Start();Image('yuv444p10','full');assert(#props.vf==2)
events['end-file']();Flush();assert(#props.vf==1 and props.vf[1]==user)
for _,case in ipairs({{'yuv444p','full'},{'yuv444p16','full'},{'yuv444p12','limited'},{'rgb48','full'}}) do
    Start();Image(case[1],case[2]);assert(#props.vf==1)
end
io.write('范围校正所有权／改链／删除／切片／错误回滚 PASS\n')
