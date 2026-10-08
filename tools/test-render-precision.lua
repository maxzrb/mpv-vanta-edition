-- 检查状态说明不会把整数容器、浮点存储与主图像交接混为一谈。
package.path='portable_config/script-modules/?.lua;'..package.path
local precision=require 'render-precision'
for _,test in ipairs({
    {'nv12','整数 8bit'}, {'p010','整数 10bit'}, {'yuv444p16','整数 16bit'},
    {'yuv422p','整数 8bit'}, {'rgba16hf','浮点存储 16bit'},
    {'rgb10a2','整数 10bit'}, {'gbrpf32le','浮点存储 32bit'}, {'opaque','位深未知'},
}) do
    assert(precision.format({pixelformat=test[1]}):find(test[2],1,true),test[1])
end
assert(precision.format({pixelformat='d3d11',['hw-pixelformat']='p010'}):find('整数 10bit',1,true))
assert(precision.handoff('d3d11va',{pixelformat='d3d11'},{{name='lavfi'}}):find('保持 GPU',1,true))
assert(precision.handoff('d3d11va',{pixelformat='yuv420p10'},{{name='vapoursynth'}}):find('下载帧',1,true))
assert(precision.handoff('d3d11va-copy',{pixelformat='yuv420p10'},{}):find('复制到系统内存',1,true))
assert(precision.handoff('d3d11va',{pixelformat='yuv420p10'},{{name='vapoursynth',enabled=false}}):find('未完整确认',1,true))
assert(precision.handoff('no',{},{}):find('软件解码',1,true))
io.write('格式精度／交接说明 PASS\n')
