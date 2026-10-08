-- 自动模式为软件滤镜选择兼容路径，明确指定的后端及普通播放保持原意图。
local props,hook,writes={},{},{}
local mp={}
function mp.get_property(k,d) return props[k] or d end
function mp.get_property_native(k,d) return props[k] or d end
function mp.set_property(k,v) writes[k]=v;return true end
function mp.add_hook(name,_,fn) assert(name=='on_preloaded');hook=fn end
package.loaded.mp=mp;package.loaded['mp.msg']={info=function() end,error=function(e) error(e) end}
dofile('portable_config/scripts/hwdec-select.lua')
for _,test in ipairs({
    {'auto-safe',{},nil},{'auto',{{name='vapoursynth'}},'auto-copy'},
    {'auto-safe',{{name='lavfi'}},'auto-copy'},
    {'auto-safe',{{name='vapoursynth',enabled=false}},nil},
    {'no',{{name='vapoursynth'}},nil},{'d3d11va',{{name='vapoursynth'}},nil},
    {'d3d11va-copy',{{name='vapoursynth'}},nil},
}) do
    props={hwdec=test[1],vf=test[2],vid='auto'};writes={};hook()
    assert(writes['file-local-options/hwdec']==test[3] and writes.hwdec==nil)
end
io.write('自动硬解／CPU 滤镜兼容／手动选择作用域 PASS\n')
