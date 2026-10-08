-- 旧自动入口不写渲染选项，切片／手动选择取消等待，退出恢复原系统状态。
local function Fixture(mode, initial)
    local props={['video-params']={gamma='pq'}, ['user-data/display-info/hdr-status']=initial,
        pause=false, fullscreen=true, ['window-maximized']=false}
    local events, observers, timers, commands = {}, {}, {}, {}
    local clock=0
    local mp={}
    function mp.get_property_native(k,d) if props[k]==nil then return d end; return props[k] end
    function mp.get_property_bool(k) return props[k]==true end
    function mp.set_property_native(k,v) assert(k=='pause', '旧脚本不应直接写色彩选项'); props[k]=v end
    function mp.get_time() return clock end
    function mp.commandv(...) commands[#commands+1]={...} end
    function mp.add_timeout(_,fn)
        local t={fn=fn}; function t:kill() self.stopped=true end
        timers[#timers+1]=t;return t
    end
    function mp.register_event(k,f) events[k]=f end
    function mp.observe_property(k,_,f) observers[k]=f end
    package.loaded.mp=mp
    package.loaded['mp.msg']={warn=function() end}
    package.loaded['mp.options']={read_options=function(o) o.hdr_mode=mode end}
    dofile('portable_config/scripts/hdr-mode.lua')
    return {props=props,events=events,observers=observers,timers=timers,commands=commands,
        tick=function(dt) clock=clock+dt;timers[#timers].fn() end}
end
local f=Fixture('noth','off')
assert(next(f.events)==nil and next(f.observers)==nil, '默认关闭不启动自动管理')
f=Fixture('pass','on'); f.events['file-loaded']()
assert(f.commands[1][2]=='color-select' and f.commands[1][3]=='hdr')
f=Fixture('switch','off'); f.events['file-loaded']()
assert(f.props.pause==true and f.commands[1][2]=='toggle-hdr-display')
f.tick(11)
assert(f.props.pause==false and f.commands[#f.commands][3]=='sdr', '超时按实际状态恢复播放')
f=Fixture('switch','off');f.events['file-loaded']()
local old=f.timers[#f.timers]
f.events['start-file']();old.fn()
assert(f.props.pause==false and #f.commands==1, '切片取消旧等待')
f=Fixture('switch','off');f.events['file-loaded']()
f.props['user-data/color-target']={manual=true}
f.observers['user-data/color-target']()
assert(f.props.pause==false and f.timers[#f.timers].stopped)
f=Fixture('switch','on');f.props['video-params']={gamma='bt.1886', ['max-luma']=1000}
f.events['file-loaded']()
assert(f.commands[1][3]=='off', 'SDR 高亮标记不能被判为 PQ／HLG')
f.events['shutdown']()
assert(f.commands[#f.commands][3]=='on', '不能把原本开启 HDR 的桌面强制关掉')
io.write('HDR 自动入口生命周期回归 PASS\n')
