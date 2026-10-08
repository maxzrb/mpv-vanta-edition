-- 真实调用流程回归：一次启用、后端独立、失败回退、组合及用户设置所有权。
local props={vf={{name='lavfi',label='external'}},['glsl-shaders']={},
    ['video-params']={w=320,h=180,primaries='bt.709',gamma='bt.1886'},
    interpolation=true,deband=false,['video-sync']='audio'}
local messages,events,timers={}, {}, {}
local fail=false
local fail_restore=false
local mp={}
function mp.get_property_native(k,d) if props[k]==nil then return d,'property unavailable' end;return props[k] end
function mp.get_property_bool(k,d) return mp.get_property_native(k,d) end
function mp.set_property_native(k,v)
    if fail_restore and k=='interpolation' and v==true then return nil,'故障注入恢复插值' end
    if fail and k=='vf' then fail=false;return nil,'实际加载失败' end
    props[k]=v;return true
end
function mp.command_native(a) return a[2]:gsub('~~/','C:/fixture/') end
function mp.commandv() end
function mp.command() end
function mp.osd_message() end
function mp.enable_messages() end
function mp.command_native_async() error('普通流程不得启动子进程') end
function mp.add_timeout(_,fn) local t={fn=fn};function t:kill() self.stopped=true end;timers[#timers+1]=t;return t end
function mp.register_script_message(k,f) messages[k]=f end
function mp.register_event(k,f) events[k]=f end
function mp.observe_property() end
package.loaded.mp=mp;package.loaded['mp.msg']={error=function() end}
package.loaded['mp.utils']={format_json=function() return '{}' end}
dofile('portable_config/scripts/quality.lua')
local function status() return props['user-data/quality'] end
local function initialized(n)
    for _=1,n or 1 do events['log-message']({prefix='vapoursynth',level='debug',text='initialized.\n'}) end
    events['playback-restart']()
end
local function error_frame(text)
    events['log-message']({prefix='vapoursynth',level='fatal',text=text})
    timers[#timers].fn()
end
events['start-file']();messages['quality-select']('ccd')
events['log-message']({prefix='vapoursynth',level='debug',text='initialized.\n'})
assert(status().state=='启用中')
events['video-reconfig']()
assert(status().state=='已添加','同帧率滤镜仅重配置输出也须更新状态')
events['start-file']();messages['quality-menu']('vs-memc')
messages['quality-select']('rife')
assert(#props.vf==2 and props.vf[2].params.file:find('RIFE_DML'), '通用入口一次调用 DML')
assert(status().state=='启用中');initialized();assert(status().state=='已添加')
assert(props.interpolation==false)
local chain=props.vf;messages['quality-select']('rife-dml');assert(props.vf==chain)
messages['quality-select']('rife-std')
events['log-message']({prefix='vapoursynth',level='fatal',text='Script evaluation failed:'})
events['log-message']({prefix='vapoursynth',level='fatal',text='ModuleNotFoundError: core.rife'})
timers[#timers].fn()
assert(status().state=='失败' and status().error:find('core.rife') and status().active.memc=='rife-dml')
assert(props.vf[1].label=='external' and props.vf[2].params.file:find('RIFE_DML'))
for _,id in ipairs({'drba-dml','drba-nv','svp','artcnn-nv'}) do
    messages['quality-reset']();messages['quality-select'](id)
    assert(#props.vf==2 and status().state=='启用中',id..' 被人为拦截')
    initialized()
end
messages['quality-reset']();messages['quality-select']('rife-dml');initialized()
messages['quality-select']('uai-dml');initialized(2)
assert(status().active.memc=='rife-dml' and #props.vf==3,'上游变化须自动保留补帧')
messages['quality-select']('artcnn')
assert(#props.vf==3 and #props['glsl-shaders']==1,'Shader 与 VF 组合')
messages['quality-select']('ccd');initialized(3)
assert(#props.vf==4 and props.vf[2].label=='quality-denoise' and props.vf[4].label=='quality-memc')
messages['quality-disable']('shader-upscale');assert(#props.vf==4)
messages['quality-select']('rife-dml-426');messages['quality-cancel']()
assert(status().active.memc=='rife-dml','取消恢复上次有效链')
messages['quality-select']('rife-dml-426');error_frame('真实模型加载失败')
assert(status().active.memc=='rife-dml' and status().error:find('真实模型加载失败'))
fail=true;messages['quality-select']('svp');assert(status().active.memc=='rife-dml')
props.interpolation=true
messages['quality-reset']()
assert(props.interpolation==true and #props.vf==1,'恢复不能覆盖后来改变的用户选项')
messages['quality-interpolation']();messages['quality-interpolation']()
props['video-sync']='display-vdrop';props.interpolation=false;props.deband=true
messages['quality-reset']()
assert(props['video-sync']=='display-vdrop' and props.interpolation==false and props.deband==true)
props['video-params'].gamma='pq'
messages['quality-select']('rife-dml');initialized()
assert(#props.vf==2 and status().warning~='','HDR 只提示，不拦截')
messages['quality-select']('rife-dml-heavy')
events['log-message']({prefix='vapoursynth',level='fatal',text='迟到错误'})
local stale=timers[#timers]
events['start-file']();stale.fn()
assert(status().state=='未启用' and #props.vf==1,'切集使旧回调失效')
props.interpolation=true
messages['quality-select']('rife-dml');initialized()
fail_restore=true;messages['quality-reset']()
assert(status().state=='失败' and status().error:find('恢复插值') and #status().restore_pending>0)
fail_restore=false;messages['quality-reset']()
assert(status().state=='未启用' and props.interpolation==true and #status().restore_pending==0,'恢复失败须可重试')
-- 达到目标时保留原帧，不添加 VS；仍可组合、替换其他补帧及切片清理。
props['container-fps']=59.925
messages['quality-select']('svp')
assert(status().state=='已添加' and status().active.memc=='svp' and status().note~='')
assert(#props.vf==1 and props.vf[1].label=='external','约 60fps 不应运行运动估计')
props.vf[2]={name='fps',label='external-fps',params={fps='24'}}
messages['quality-select']('svp');initialized()
assert(#props.vf==3 and status().note=='','外部帧率改写须以实际 VS 输入为准')
table.remove(props.vf,2)
messages['quality-select']('svp')
assert(#props.vf==1 and status().note~='')
messages['quality-select']('rife-dml');initialized()
messages['quality-select']('svp')
assert(#props.vf==1 and status().active.memc=='svp','直通替换旧补帧链')
props['container-fps']=120
messages['quality-select']('svp');assert(#props.vf==1,'高帧率不能降成 59.94')
props['container-fps']=24000/1001
messages['quality-select']('svp');initialized()
assert(#props.vf==2 and props.vf[2].params.file:find('SVP'),'低帧率仍须实际启用 SVP')
events['start-file']()
assert(status().state=='未启用' and status().note=='' and #props.vf==1)
io.write('滤镜一次启用／无预检／回退／组合／所有权／SVP 原帧直通 PASS\n')
