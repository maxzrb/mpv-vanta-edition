-- 验证资源不足、手动参数、硬解隔离和解码切换的所有权，不依赖视频文件。
local props, hooks, events, messages, writes, commands = {}, {}, {}, {}, {}, {}
local total, available = 32 * 1024^3, 20 * 1024^3
local function Copy(t)
    if type(t) ~= 'table' then return t end
    local result = {}
    for k, v in pairs(t) do result[k] = Copy(v) end
    return result
end
local mp = {}
function mp.get_property_native(k, default) local v = props[k]; if v == nil then return default end; return Copy(v) end
function mp.get_property(k, default) local v = props[k]; if v == nil then return default end; return tostring(v) end
function mp.get_property_number(k, default) return tonumber(props[k]) or default end
function mp.get_property_bool(k, default) if props[k] == nil then return default end; return props[k] end
function mp.set_property_native(k, v)
    writes[k] = Copy(v)
    if k:match('^file%-local%-options/') then props[k:sub(20)] = Copy(v) end
    return true
end
function mp.set_property(k, v)
    if k == 'file-local-options/vd-lavc-o' and v == '' then
        writes[k], props['vd-lavc-o'] = '', {}
    elseif k:match('^file%-local%-options/') then props[k:sub(20)] = v
    else props[k] = v end
    return true
end
function mp.add_hook(name, priority, callback)
    hooks[name] = hooks[name] or {}
    hooks[name][#hooks[name] + 1] = {priority = priority, callback = callback}
end
function mp.register_event(name, callback) events[name] = callback end
function mp.observe_property(_, _, callback) events.observe = callback end
function mp.register_script_message(name, callback) messages[name] = callback end
function mp.add_key_binding(_, _, callback) events.toggle = callback end
function mp.command_native(command) commands[#commands + 1] = Copy(command) end
function mp.add_timeout(_, callback) events.timeout = callback end
function mp.find_config_file() return 'tools/test-preference-store-stub.lua' end
function mp.osd_message() end
package.loaded.mp = mp
package.loaded['mp.msg'] = {info = function() end, warn = function() end, error = function(e) error(e) end}
package.loaded['mp.options'] = {read_options = function() end}
package.loaded['mp.utils'] = {file_info = function(path) return path == 'local.mkv' and {} or nil end}
package.loaded.ffi = {os = 'Windows', cdef = function() end, sizeof = function() return 64 end,
    new = function() return {} end, load = function() return {GlobalMemoryStatusEx = function(data)
        data.total_phys, data.avail_phys = total, available; return 1
    end} end}
dofile('portable_config/scripts/decode-performance.lua')

local function RunHook(name)
    local list = hooks[name] or {}
    table.sort(list, function(a, b) return a.priority < b.priority end)
    for _, item in ipairs(list) do item.callback() end
end

local function Start(codec, policy, threads, avopts)
    props = {['current-tracks/video'] = {codec = codec, ['demux-w'] = 3840, ['demux-h'] = 2160},
        ['vd-lavc-threads'] = threads or 0, ['vd-lavc-o'] = avopts or {}, hwdec = policy,
        path = 'local.mkv', ['time-pos'] = 12.5, pause = true, seekable = true,
        vid = 1, aid = 2, sid = 3, ['secondary-sid'] = 'no'}
    writes, commands = {}, {}
    RunHook('on_loaded')
end
Start('hevc', 'no')
assert(not writes['file-local-options/vd-lavc-o'] and not writes['file-local-options/vd-lavc-threads'])
Start('av1', 'no', 8)
assert(props['vd-lavc-threads'] == 8 and props['vd-lavc-o'].max_frame_delay == nil)
Start('av1', 'no', 0, {max_frame_delay = '12'})
assert(props['vd-lavc-threads'] == 0 and props['vd-lavc-o'].max_frame_delay == '12')
available = 512 * 1024^2
Start('av1', 'no')
assert(props['vd-lavc-threads'] == 0 and props['vd-lavc-o'].max_frame_delay == nil)
available = 20 * 1024^3
Start('av1', 'd3d11va')
assert(props['vd-lavc-threads'] == 0 and props['vd-lavc-o'].max_frame_delay == nil)
Start('av1', 'no', 8)
props['vd-lavc-threads'], props.vd = 0, 'libaom-av1'
RunHook('on_loaded')
assert(props['vd-lavc-threads'] == 0 and props['vd-lavc-o'].max_frame_delay == nil)
Start('av1', 'auto-safe')
props['current-tracks/video']['decoder-desc'] = 'Alliance for Open Media AV1'
props['hwdec-current'] = 'd3d11va'
props['video-params'] = {w = 3840, h = 2160, pixelformat = 'd3d11'}
events.observe()
assert(props['vd-lavc-o'].max_frame_delay == nil and #commands == 0)
Start('av1', 'no', 0, {skip_loop_filter = 'default'})
assert(tonumber(props['vd-lavc-o'].max_frame_delay) > 4)
assert(props['vd-lavc-o'].skip_loop_filter == 'default')
props['vd-lavc-o'].other_user_option = 'a,b=c'
props['file-local-options'] = {'target-trc', 'vf'}
props['option-info/target-trc/set-locally'], props['option-info/vf/set-locally'] = true, true
props['file-local-options/target-trc'], props['file-local-options/vf'] = 'scrgb', 'format=yuv444p12'
messages['decode-performance-hwdec']('auto-safe')
assert(#commands == 1 and commands[1][1] == 'playlist-play-index')
assert(commands[1][2] == 'current' and commands[1][3] == true)
assert(props.hwdec == 'no')
RunHook('on_load')
assert(props.start == '12.5' and props.pause == true)
assert(props['vd-lavc-o'].max_frame_delay == nil)
assert(props['vd-lavc-o'].other_user_option == 'a,b=c')
assert(props['vd-lavc-threads'] == 0)
assert(props['file-local-options/target-trc'] == 'scrgb' and props['file-local-options/vf'] == 'format=yuv444p12')
assert(props.vid == 1 and props.aid == 2 and props.sid == 3 and props['secondary-sid'] == 'no')
RunHook('on_loaded')
Start('av1', 'no')
messages['decode-performance-hwdec']('auto-safe')
RunHook('on_load')
assert(writes['file-local-options/vd-lavc-o'] == '' and next(props['vd-lavc-o']) == nil)
RunHook('on_loaded')

-- 普通视频必须在可定位位置上重建，不能直接 set 当前 hwdec。
Start('hevc', 'auto-safe')
props['hwdec-current'] = 'd3d11va'
messages['decode-performance-hwdec']('no')
assert(#commands == 1 and commands[1][1] == 'playlist-play-index' and props.hwdec == 'auto-safe')
RunHook('on_load')
assert(props.hwdec == 'no' and props.start == '12.5' and props.pause == true)
RunHook('on_loaded')

-- 重载期间再次选择只排队，当前事务完成后再重建一次。
Start('hevc', 'auto-safe')
messages['decode-performance-hwdec']('no')
assert(#commands == 1)
messages['decode-performance-hwdec']('auto-safe')
assert(#commands == 1)
RunHook('on_load')
assert(props.hwdec == 'no')
RunHook('on_loaded')
assert(events.timeout)
events.timeout()
assert(#commands == 2 and commands[2][1] == 'playlist-play-index')
RunHook('on_load')
RunHook('on_loaded')

-- 不可定位的直播流不能中途破坏解码器；保留当前播放并让选择下次生效。
Start('hevc', 'd3d11va')
props.seekable = false
messages['decode-performance-hwdec']('no')
assert(#commands == 0 and props.hwdec == 'd3d11va')

-- 没有活动视频时不需要重建，可直接设置全局解码策略。
props = {hwdec = 'auto-safe'}
commands = {}
messages['decode-performance-hwdec']('no')
assert(props.hwdec == 'no' and #commands == 0)
messages['decode-performance-hwdec']('auto-safe')
assert(props.hwdec == 'auto-safe')

props = {hwdec = 'no'}
RunHook('on_load')
assert(props.hwdec == 'auto-safe')
props = {hwdec = 'd3d11va', ['option-info/hwdec/set-locally'] = true}
RunHook('on_load')
assert(props.hwdec == 'd3d11va')
io.write('PASS 编码隔离／手动参数／低内存／安全重建／不可定位保护／空闲直设\n')
