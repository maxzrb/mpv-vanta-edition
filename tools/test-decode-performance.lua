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
function mp.add_hook(name, _, callback) hooks[name] = callback end
function mp.register_event(name, callback) events[name] = callback end
function mp.observe_property(_, _, callback) events.observe = callback end
function mp.register_script_message(name, callback) messages[name] = callback end
function mp.add_key_binding(_, _, callback) events.toggle = callback end
function mp.command_native(command) commands[#commands + 1] = Copy(command) end
package.loaded.mp = mp
package.loaded['mp.msg'] = {info = function() end, warn = function() end, error = function(e) error(e) end}
package.loaded['mp.options'] = {read_options = function() end}
package.loaded['mp.utils'] = {file_info = function(path) return path == 'local.mkv' and {} or nil end}
package.loaded.ffi = {os = 'Windows', cdef = function() end, sizeof = function() return 64 end,
    new = function() return {} end, load = function() return {GlobalMemoryStatusEx = function(data)
        data.total_phys, data.avail_phys = total, available; return 1
    end} end}
dofile('portable_config/scripts/decode-performance.lua')

local function Start(codec, policy, threads, avopts)
    props = {['current-tracks/video'] = {codec = codec, ['demux-w'] = 3840, ['demux-h'] = 2160},
        ['vd-lavc-threads'] = threads or 0, ['vd-lavc-o'] = avopts or {}, hwdec = policy,
        path = 'local.mkv', ['time-pos'] = 12.5, pause = true}
    writes, commands = {}, {}
    hooks.on_loaded()
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
hooks.on_loaded()
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
hooks.on_load()
assert(props.start == '12.5' and props.pause == true)
assert(props['vd-lavc-o'].max_frame_delay == nil)
assert(props['vd-lavc-o'].other_user_option == 'a,b=c')
assert(props['vd-lavc-threads'] == 0)
assert(props['file-local-options/target-trc'] == 'scrgb' and props['file-local-options/vf'] == 'format=yuv444p12')
Start('av1', 'no')
messages['decode-performance-hwdec']('auto-safe')
hooks.on_load()
assert(writes['file-local-options/vd-lavc-o'] == '' and next(props['vd-lavc-o']) == nil)
props = {hwdec = 'no'}
hooks.on_load()
assert(props.hwdec == 'auto-safe')
props = {hwdec = 'd3d11va', ['option-info/hwdec/set-locally'] = true}
hooks.on_load()
assert(props.hwdec == 'd3d11va')
io.write('PASS 编码隔离／手动参数／低内存／硬解隔离／切换所有权与空表清除\n')
