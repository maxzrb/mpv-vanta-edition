-- License: MIT
-- 高分辨率 AV1 软解只优化任务并行；不改变像素、滤镜、色彩或同步策略。
local mp = require 'mp'
local msg = require 'mp.msg'
local options = require 'mp.options'
local utils = require 'mp.utils'

local o = { enabled = true, max_threads = 32, max_frame_delay = 32,
    max_memory_mib = 8192, min_pixels = 3840 * 2160 }
options.read_options(o, 'decode-performance')

local memory_status
local ffi_ok, ffi = pcall(require, 'ffi')
if ffi_ok and ffi.os == 'Windows' then
    local ok, kernel = pcall(function()
        ffi.cdef[[
            typedef struct {
                unsigned long length, load;
                unsigned long long total_phys, avail_phys, total_page, avail_page;
                unsigned long long total_virtual, avail_virtual, avail_extended;
            } DecodePerformanceMemory;
            int __stdcall GlobalMemoryStatusEx(DecodePerformanceMemory *);
        ]]
        return ffi.load('kernel32')
    end)
    if ok then
        memory_status = function()
            local data = ffi.new('DecodePerformanceMemory')
            data.length = ffi.sizeof(data)
            if kernel.GlobalMemoryStatusEx(data) == 0 then return end
            return tonumber(data.total_phys), tonumber(data.avail_phys)
        end
    else
        msg.warn('无法读取内存状态，AV1 并行优化采用保守预算')
    end
end

local state = {}
local pending
local reload_state = {active = false, path = nil, queued = nil, started = false}
local reload_serial, file_generation = 0, 0
local seek_restore
local RestoreSeek
local user_policy
local requested_policy = mp.get_property('hwdec', 'no')
local preferences_loaded, preferences = pcall(function()
    return dofile(mp.find_config_file('script-modules/preference-store.lua'))
end)
if preferences_loaded then
    local err
    user_policy, err = preferences.restore('hwdec')
    if user_policy then requested_policy = user_policy end
    if err then msg.error(err) end
else
    msg.error('解码偏好保存模块无法加载：' .. tostring(preferences))
end
local function Copy(value)
    local result = {}
    for k, v in pairs(value or {}) do result[k] = v end
    return result
end

local function TrackSelection()
    local selection = {}
    for _, name in ipairs({'vid', 'aid', 'sid', 'secondary-sid'}) do
        local value = mp.get_property_native(name)
        if value ~= nil and value ~= '' then selection[name] = value end
    end
    return selection
end

local function Status(phase, delay)
    local policy = requested_policy
    if policy == 'auto' then policy = 'auto-safe'
    elseif policy == 'auto-copy' then policy = 'auto-copy-safe' end
    mp.set_property_native('user-data/decode-performance', {
        state = phase, threads = state.threads, frame_delay = delay,
        ['hwdec-policy'] = policy,
    })
end
Status('标准解码')

local function CancelReload(reason)
    if RestoreSeek then RestoreSeek() end
    reload_serial = reload_serial + 1
    reload_state = {active = false, path = nil, queued = nil, started = false}
    pending = nil
    Status('解码切换已取消')
    msg.warn('取消解码器重载：' .. reason .. '；已保存的用户选择保留')
end

local function Local(name, value)
    -- Lua 空表会被 native 接口编码为数组；键值选项用空字符串显式清空。
    local ok, err
    if name == 'vd-lavc-o' and next(value) == nil then
        ok, err = mp.set_property('file-local-options/' .. name, '')
    else
        ok, err = mp.set_property_native('file-local-options/' .. name, value)
    end
    if not ok then msg.error('设置解码并行参数失败：' .. name .. '：' .. tostring(err)) end
    return ok
end

RestoreSeek = function()
    local saved = seek_restore
    seek_restore = nil
    if saved and saved.path == mp.get_property('path')
        and mp.get_property('hr-seek') == 'yes' then
        Local('hr-seek', saved.value)
    end
end

local function Plan(w, h, params, initial_budget)
    local cores = tonumber(os.getenv('NUMBER_OF_PROCESSORS')) or 8
    local threads = math.max(1, math.min(math.floor(o.max_threads), cores * 2))
    -- 用实际平面存储估算；格式未知时按 16-bit 4:4:4 的最坏情况计算。
    local format = params and params.pixelformat or ''
    local bytes = 6
    if format:match('^yuv420p') then bytes = format:match('p%d') and 3 or 1.5
    elseif format:match('^yuv422p') then bytes = format:match('p%d') and 4 or 2
    elseif format == 'yuv444p' or format == 'gbrp' then bytes = 3 end
    local budget = initial_budget or math.max(0, o.max_memory_mib) * 1024 * 1024
    local total, available
    if memory_status then total, available = memory_status() end
    if initial_budget then
        -- 使用加载前的预算，避免把自己已分配的解码缓冲重复扣除。
    elseif total and available then
        budget = math.min(budget, total / 3, available / 2)
    else
        budget = math.min(budget, 1024 * 1024 * 1024)
    end
    -- 为参考帧、临时缓冲和渲染留余量；这是估算，非分配器硬上限。
    local depth = math.floor(budget / (w * h * bytes * 4)) - 8
    depth = math.min(threads, math.floor(o.max_frame_delay), depth)
    if depth <= math.min(8, math.ceil(math.sqrt(threads))) then return end
    return threads, depth, budget
end

local function Reload(policy, threads, avopts)
    local path = mp.get_property('path')
    local position = mp.get_property_number('time-pos', 0)
    if not pending then pending = {path = path, reprepare = true} end
    pending.overrides = {policy = policy, threads = threads, avopts = Copy(avopts),
        position = position, pause = mp.get_property_native('pause', false),
        selection = TrackSelection()}
    -- 将运行时添加的字幕／音轨纳入本文件选项，重播时保留内容与选择。
    local extra = {}
    for _, track in ipairs(mp.get_property_native('track-list', {})) do
        local filename = track['external-filename']
        local key = track.type == 'sub' and 'sub-files' or track.type == 'audio' and 'audio-files'
        if track.external and key and filename then
            local files = extra[key] or Copy(mp.get_property_native(key, {}))
            local found = false
            for _, file in ipairs(files) do if file == filename then found = true end end
            if not found then files[#files + 1] = filename end
            extra[key] = files
        end
    end
    pending.overrides.extra = extra
    -- 一次加载事务先设置全部参数再创建解码器，避免带旧码流状态的逐项重建。
    -- 重播当前条目，保留播放列表及文件局部选项，不替换或清空播放列表。
    local ok, result, err = pcall(mp.command_native,
        {'playlist-play-index', 'current', true})
    if not ok or err then
        pending = nil
        msg.error('切换解码并行失败：' .. tostring(err or result))
        return false, err or result
    end
    return true
end

local function Tune()
    if not state.prepared or state.applied then return end
    local track = mp.get_property_native('current-tracks/video', {})
    local decoder = tostring(track['decoder-desc'] or ''):lower()
    if track.codec ~= 'av1' or not decoder:find('dav1d', 1, true)
        or mp.get_property('hwdec-current') ~= 'no' then return end
    local current = mp.get_property_native('vd-lavc-o', {})
    if current.max_frame_delay ~= nil then
        state.applied = true
        Status('手动帧并行', current.max_frame_delay)
        return
    end
    local params = mp.get_property_native('video-params', {})
    if not params.pixelformat then return end
    if not params.pixelformat:match('^yuv') and not params.pixelformat:match('^gbr')
        and not params.pixelformat:match('^gray') then return end
    local _, depth = Plan(params.w, params.h, params, state.budget)
    if not depth then return end
    depth = math.min(depth, state.threads)
    local path = mp.get_property('path')
    -- 自动回退的本地文件重载一次；不为网络流额外打开连接。
    if not path or not utils.file_info(path) then return end
    state.applied = true
    state.original_avopts = Copy(current)
    current.max_frame_delay = tostring(depth)
    state.delay = depth
    pending = Copy(state)
    pending.path = path
    -- 已确认该文件无法走硬解；文件局部固定软解，下一文件恢复原硬解策略。
    Reload('no', state.threads, current)
end

local function Prepare()
    if pending and pending.path == mp.get_property('path') and not pending.reprepare then
        state, pending = pending, nil
        Status('AV1 软解并行', state.delay)
        msg.info('AV1 软解并行：' .. state.threads .. ' 工作线程／' .. state.delay .. ' 帧；像素处理不变')
        return
    end
    pending = nil
    state = {}
    Status(o.enabled and '标准解码' or '已关闭')
    if not o.enabled then return end
    local policy = mp.get_property('hwdec', 'no')
    if policy ~= 'no' and policy ~= 'auto-safe' and policy ~= 'auto'
        and policy ~= 'auto-copy' and policy ~= 'auto-copy-safe' then return end
    local decoder = mp.get_property('vd', '')
    if decoder ~= '' and decoder ~= 'auto' and decoder ~= 'libdav1d' then return end
    local track = mp.get_property_native('current-tracks/video', {})
    local w, h = tonumber(track['demux-w']), tonumber(track['demux-h'])
    if track.codec ~= 'av1' or track.image or track.external or not w or not h or w * h < o.min_pixels then return end
    local videos = 0
    for _, item in ipairs(mp.get_property_native('track-list', {})) do
        if item.type == 'video' and not item.image and not item.albumart and not item.dependent then
            videos = videos + 1
        end
    end
    if videos > 1 then return end
    local old_threads = mp.get_property_native('vd-lavc-threads', 0)
    local avopts = mp.get_property_native('vd-lavc-o', {})
    -- 明确指定的工作线程或帧并行视为用户所有，不覆盖。
    if old_threads ~= 0 or avopts.threads ~= nil or avopts.max_frame_delay ~= nil then return end
    local threads, depth, budget = Plan(w, h)
    if not threads then return end
    state.threads, state.original_threads = threads, old_threads
    state.budget = budget
    state.prepared = Local('vd-lavc-threads', threads)
    if not state.prepared then return end
    Status('硬解优先／软解预备')
    if mp.get_property('hwdec') == 'no' then
        -- 明确软解时，在创建解码器之前一次设好，避免首帧后的重建。
        state.original_avopts = Copy(avopts)
        avopts.max_frame_delay = tostring(depth)
        state.applied = Local('vd-lavc-o', avopts)
        if state.applied then state.delay = depth; Status('AV1 软解并行', depth) end
    end
end
mp.add_hook('on_load', 55, function()
    if reload_state.active then
        if reload_state.path ~= mp.get_property('path') then
            CancelReload('已切换到其他文件')
        else
            reload_state.started = true
        end
    end
    local loaded_override = false
    if pending and pending.path == mp.get_property('path') and pending.overrides then
        local values = pending.overrides
        Local('hwdec', values.policy)
        Local('vd-lavc-threads', values.threads)
        Local('vd-lavc-o', values.avopts)
        -- 恢复位置必须精确，不能受用户日常关键帧跳转偏好影响；首帧恢复后还原。
        RestoreSeek()
        local seek_mode = mp.get_property('hr-seek', 'yes')
        if seek_mode ~= 'yes' and seek_mode ~= 'always' then
            seek_restore = {path = mp.get_property('path'), value = seek_mode}
            Local('hr-seek', 'yes')
        end
        Local('start', tostring(values.position))
        Local('resume-playback', false)
        Local('pause', values.pause)
        for key, files in pairs(values.extra) do Local(key, files) end
        for name, value in pairs(values.selection) do Local(name, value) end
        pending.overrides = nil
        loaded_override = true
    end
    -- 菜单选择跨文件保留；显式文件配置仍优先，CPU 滤镜的预加载选择随后运行。
    if not loaded_override and user_policy
        and not mp.get_property_bool('option-info/hwdec/set-locally', false) then
        Local('hwdec', user_policy)
    end
end)
mp.add_hook('on_loaded', 55, Prepare)
mp.register_event('playback-restart', function() RestoreSeek(); Tune() end)
mp.add_hook('on_unload', 55, RestoreSeek)
mp.observe_property('current-tracks/video/decoder-desc', 'string', Tune)

local function OriginalOptions()
    local current = mp.get_property_native('vd-lavc-o', {})
    if state.delay then
        if tostring(current.max_frame_delay) == tostring(state.delay) then
            current.max_frame_delay = state.original_avopts.max_frame_delay
        end
    end
    local threads = mp.get_property_native('vd-lavc-threads', 0)
    if state.prepared and threads == state.threads then threads = state.original_threads end
    return threads, current
end

local function ActiveVideo()
    local track = mp.get_property_native('current-tracks/video')
    if not track or not track.codec or track.image or track.albumart then return end
    return track
end

local function CanReposition()
    local path = mp.get_property('path', '')
    if not path or path == '' then return false, '文件路径不可用' end
    if not mp.get_property_bool('seekable', false) then return false, '当前流不可定位' end
    if mp.get_property_number('time-pos') == nil then return false, '当前位置未知' end
    return true
end

local function SavePolicy(policy)
    local saved, err
    if preferences_loaded then saved, err = preferences.set('hwdec', policy) end
    if not saved then
        msg.error('解码偏好保存失败，原文件保留：' .. tostring(err or preferences))
        mp.osd_message('解码选择未能保存，仅在本次会话保留', 3)
    end
end

local ApplyHardware
ApplyHardware = function(policy)
    -- 新请求使上一事务遗留的延迟回调失效，防止旧选择覆盖新选择。
    reload_serial = reload_serial + 1
    local threads, avopts = OriginalOptions()
    if ActiveVideo() then
        local safe, reason = CanReposition()
        if not safe then
            msg.warn('未重建解码器：' .. reason .. '；选择将在下个可定位文件生效')
            Status('等待下次文件安全切换')
            mp.osd_message(reason .. '，已保留当前解码器；选择将在下次打开文件时生效', 5)
            return false
        end
        local position = mp.get_property_number('time-pos')
        reload_state.active, reload_state.path = true, mp.get_property('path')
        reload_state.queued, reload_state.started = nil, false
        pending = nil
        local ok, err = Reload(policy, threads, avopts)
        if not ok then
            CancelReload('重载命令执行失败')
            msg.error('安全重建解码器失败：' .. tostring(err))
            mp.osd_message('解码方式切换失败，当前播放未改变', 4)
            return false
        end
        msg.info(('安全重建解码器：%s -> %s，位置 %.3f 秒')
            :format(mp.get_property('hwdec-current', '?'), policy, position))
        mp.osd_message('正在安全切换解码器并恢复播放位置', 3)
        return true
    end
    local ok, err = mp.set_property('hwdec', policy)
    if not ok then
        msg.error('设置解码方式失败：' .. tostring(err))
        return false
    end
    Prepare()
    Tune()
    return true
end

local function Hardware(policy)
    if not policy or policy == '' then return end
    if preferences_loaded and not preferences.valid('hwdec', policy) then
        msg.error('无效的解码方式：' .. tostring(policy))
        return
    end
    user_policy = policy
    requested_policy = policy
    if reload_state.active then
        reload_state.queued = policy
        SavePolicy(policy)
        mp.osd_message('解码器正在重建，完成后应用最新选择', 3)
        return
    end
    ApplyHardware(policy)
    -- 仅菜单／绑定调用保存用户策略；hwdec-current 和局部软解／复制回退不保存。
    SavePolicy(policy)
end

local function FinishReload()
    if not reload_state.active then return end
    local path = mp.get_property('path')
    if path ~= reload_state.path then
        CancelReload('已切换到其他文件')
        return
    end
    reload_state.active, reload_state.path, reload_state.started = false, nil, false
    local queued = reload_state.queued
    reload_state.queued = nil
    msg.info('解码器重载参数已应用：' .. tostring(mp.get_property('hwdec')))
    if queued and queued ~= mp.get_property('hwdec') then
        local serial, generation = reload_serial, file_generation
        mp.add_timeout(0, function()
            if serial ~= reload_serial or generation ~= file_generation
                or path ~= mp.get_property('path')
                or mp.get_property_bool('idle-active', false) then return end
            ApplyHardware(queued)
        end)
    end
end

mp.register_event('start-file', function()
    file_generation = file_generation + 1
    if not reload_state.active then return end
    if reload_state.started then
        CancelReload('加载过程已被另一轮打开替换')
    else
        reload_state.started = true
    end
end)
mp.register_event('end-file', function(event)
    file_generation = file_generation + 1
    if not reload_state.active then return end
    -- 重播当前项会先结束旧文件；只有这一次正常卸载不能提前解锁。
    if not reload_state.started and event.reason == 'stop' then return end
    CancelReload('加载结束（' .. tostring(event.reason) .. '）')
end)
mp.observe_property('idle-active', 'bool', function(_, idle)
    if not idle or not mp.get_property_bool('idle-active', false) then return end
    file_generation = file_generation + 1
    if reload_state.active then CancelReload('播放器已停止或返回空闲') end
end)
mp.add_hook('on_loaded', 56, FinishReload)
mp.register_script_message('decode-performance-hwdec', Hardware)
mp.add_key_binding(nil, 'decode-performance-toggle-hwdec', function()
    -- 快速连按时以最近一次用户请求为准，避免重载尚未生效时两次都得到同一策略。
    Hardware(requested_policy == 'no' and 'auto-safe' or 'no')
end)
