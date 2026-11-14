-- License: MIT
-- 解码并行与可选过载追赶共用安全重载；临时参考帧模式不写入用户解码偏好。
local mp = require 'mp'
local msg = require 'mp.msg'
local options = require 'mp.options'
local utils = require 'mp.utils'

local o = { enabled = true, max_threads = 32, max_frame_delay = 32,
    max_memory_mib = 8192, min_pixels = 3840 * 2160, catchup = false,
    catchup_enter_lag = 0.35, catchup_enter_hold = 1.5, catchup_leave_lag = 0.06,
    catchup_leave_hold = 8, catchup_minimum = 12, catchup_retry = 30, catchup_settle = 2,
    catchup_recover = false, catchup_drop_window = 2, catchup_drop_ratio = .05,
    catchup_sync_lag = .75, catchup_sync_hold = 2, catchup_sync_interval = 10 }
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
local FinishReload
local catchup = {enabled = o.catchup, reference = false, phase = '关闭', switches = 0, resyncs = 0}
local CatchupReset, CatchupComplete, CatchupInterrupt, CatchupPublish
local user_policy
local requested_policy = mp.get_property('hwdec', 'no')
local preferences_loaded, preferences = pcall(function()
    local path = mp.find_config_file('script-modules/preference-store.lua')
    if not path then error('找不到播放偏好保存模块') end
    return dofile(path)
end)
if preferences_loaded then
    local err
    user_policy, err = preferences.restore('hwdec')
    if user_policy then requested_policy = user_policy end
    if err then msg.error(err) end
    local saved, save_err = preferences.restore('overload-catchup')
    local explicit = mp.get_property_native('script-opts', {}) or {}
    if saved ~= nil and explicit['decode-performance-catchup'] == nil then catchup.enabled = saved end
    if save_err then msg.error(save_err) end
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

local last_status
local function Status(phase, delay)
    state.phase = phase
    local policy = requested_policy
    if policy == 'auto' then policy = 'auto-safe'
    elseif policy == 'auto-copy' then policy = 'auto-copy-safe' end
    local payload = {
        state = phase, threads = state.threads, frame_delay = delay,
        ['hwdec-policy'] = policy,
        ['catchup-enabled'] = catchup.enabled, ['catchup-active'] = catchup.reference,
        ['catchup-state'] = catchup.phase, ['catchup-switches'] = catchup.switches,
        ['catchup-resyncs'] = catchup.resyncs, ['catchup-auto-recover'] = o.catchup_recover,
        ['catchup-reason'] = catchup.reason, ['reload-active'] = reload_state.active,
    }
    -- 采样不等于界面刷新；只在状态变化时通知菜单，避免高负载下反复重建。
    local changed = not last_status
    for key, value in pairs(payload) do if not last_status or last_status[key] ~= value then changed = true end end
    for key in pairs(last_status or {}) do if payload[key] == nil then changed = true end end
    if changed then
        last_status = payload
        mp.set_property_native('user-data/decode-performance', payload)
    end
end
Status('标准解码')

local function CancelReload(reason)
    if RestoreSeek then RestoreSeek() end
    reload_serial = reload_serial + 1
    reload_state = {active = false, path = nil, queued = nil, started = false}
    pending = nil
    if CatchupReset then CatchupReset('重载取消：' .. reason) end
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

local function Reload(policy, threads, avopts, change)
    change = change or {}
    local path = mp.get_property('path')
    local position = change.position or mp.get_property_number('time-pos', 0)
    if not pending then pending = {path = path, reprepare = true} end
    pending.overrides = {policy = policy, threads = threads, avopts = Copy(avopts),
        position = position, pause = mp.get_property_native('pause', false),
        selection = TrackSelection(), skipframe = change.skipframe}
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
        Status(state.delay and 'AV1 软解并行' or '标准解码', state.delay)
        if state.threads and state.delay then
            msg.info('AV1 软解并行：' .. state.threads .. ' 工作线程／' .. state.delay .. ' 帧；像素处理不变')
        end
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
        if values.skipframe ~= nil then Local('vd-lavc-skipframe', values.skipframe) end
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
mp.register_event('playback-restart', function()
    RestoreSeek()
    Tune()
    if reload_state.kind == 'catchup-video' and FinishReload then
        -- 原地视频重建没有文件加载事件，以第一帧恢复作为事务完成边界。
        FinishReload()
    end
end)
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
    local restore_skip = (catchup.reference or catchup.transition) and catchup.baseline or nil
    local managed_skip = catchup.managed or restore_skip ~= nil
    if CatchupReset then CatchupReset('用户选择解码方式') end
    catchup.managed = managed_skip
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
        reload_state.kind = 'hardware'
        reload_state.queued, reload_state.started = nil, false
        pending = nil
        local ok, err = Reload(policy, threads, avopts, {skipframe = restore_skip})
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
    if reload_state.kind == 'catchup-video' then
        -- 用户明确选择优先于自动追赶，不等待自动事务的后续回调。
        reload_state.active = false
    end
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

FinishReload = function()
    if not reload_state.active then return end
    local path = mp.get_property('path')
    if path ~= reload_state.path then
        CancelReload('已切换到其他文件')
        return
    end
    local kind = reload_state.kind
    reload_state.active, reload_state.path, reload_state.started, reload_state.kind = false, nil, false, nil
    if (kind == 'catchup' or kind == 'catchup-video') and CatchupComplete then CatchupComplete() end
    local queued = reload_state.queued
    reload_state.queued = nil
    msg.info('解码器重载参数已应用：' .. tostring(mp.get_property('hwdec')))
    Status(state.phase or '标准解码', state.delay)
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
    if not reload_state.active and CatchupReset then CatchupReset('新文件') end
    if not reload_state.active then return end
    if reload_state.started then
        CancelReload('加载过程已被另一轮打开替换')
    else
        reload_state.started = true
    end
end)
mp.register_event('end-file', function(event)
    file_generation = file_generation + 1
    local internal = reload_state.active and not reload_state.started and event.reason == 'stop'
    if not internal and CatchupReset then CatchupReset('文件结束') end
    if not reload_state.active then return end
    -- 重播当前项会先结束旧文件；只有这一次正常卸载不能提前解锁。
    if not reload_state.started and event.reason == 'stop' then return end
    CancelReload('加载结束（' .. tostring(event.reason) .. '）')
end)
mp.observe_property('idle-active', 'bool', function(_, idle)
    if not idle or not mp.get_property_bool('idle-active', false) then return end
    file_generation = file_generation + 1
    if CatchupReset then CatchupReset('空闲') end
    if reload_state.active then CancelReload('播放器已停止或返回空闲') end
end)
mp.add_hook('on_loaded', 56, FinishReload)
mp.register_script_message('decode-performance-hwdec', Hardware)
mp.add_key_binding(nil, 'decode-performance-toggle-hwdec', function()
    -- 快速连按时以最近一次用户请求为准，避免重载尚未生效时两次都得到同一策略。
    Hardware(requested_policy == 'no' and 'auto-safe' or 'no')
end)

-- 追赶判定与解码器操作分离；所有模式切换仍经过上面的单一重载事务。
local policy_ok, policy_module = pcall(function()
    local path = mp.find_config_file('script-modules/overload-policy.lua')
    if not path then error('找不到过载追赶判定模块') end
    return dofile(path)
end)
local function Bounded(value, fallback, minimum, maximum)
    value = tonumber(value)
    if not value or value ~= value then value = fallback end
    return math.max(minimum, math.min(maximum, value))
end
local policy
if policy_ok and type(policy_module) == 'table' and type(policy_module.new) == 'function' then
    policy = policy_module.new({
        enter_lag = Bounded(o.catchup_enter_lag, .35, .1, 10),
        enter_hold = Bounded(o.catchup_enter_hold, 1.5, .5, 30),
        leave_lag = Bounded(o.catchup_leave_lag, .06, .01, .1),
        leave_hold = Bounded(o.catchup_leave_hold, 8, 2, 60),
        minimum = Bounded(o.catchup_minimum, 12, 5, 120),
        retry = Bounded(o.catchup_retry, 30, 10, 120),
        settle = Bounded(o.catchup_settle, 2, .5, 15),
        recover = o.catchup_recover,
        drop_window = Bounded(o.catchup_drop_window, 2, 1, 10),
        drop_ratio = Bounded(o.catchup_drop_ratio, .05, .01, .5),
        sync_lag = Bounded(o.catchup_sync_lag, .75, .35, 10),
        sync_hold = Bounded(o.catchup_sync_hold, 2, 1, 30),
        sync_interval = Bounded(o.catchup_sync_interval, 10, 5, 60),
    })
else
    msg.warn('过载追赶判定模块不可用，保留完整解码')
end

CatchupPublish = function()
    Status(state.phase or '标准解码', state.delay)
end

CatchupInterrupt = function()
    if policy then policy:interrupt(mp.get_time()) end
    catchup.clock = nil
end

CatchupReset = function(reason)
    catchup.reference, catchup.baseline, catchup.transition = false, nil, nil
    catchup.reason, catchup.suspended = reason, false
    catchup.managed = false
    catchup.phase = catchup.enabled and '等待稳定播放' or '关闭'
    catchup.clock = nil
    if policy then policy:reset(mp.get_time()) end
    CatchupPublish()
end

local function Eligible()
    if not policy then return false, '判定模块不可用' end
    if catchup.suspended then return false, '当前文件尊重外部解码设置' end
    if not ActiveVideo() then return false, '没有活动视频' end
    if mp.get_property('hwdec-current', 'no') ~= 'no' then return false, '硬解保持完整解码' end
    local safe, reason = CanReposition()
    if not safe then return false, reason end
    if mp.get_property_bool('untimed', false) or mp.get_property('video-sync') == 'desync' then
        return false, '非实时播放不介入'
    end
    local track = ActiveVideo()
    local intra = {rawvideo = true, ffv1 = true, mjpeg = true, png = true, bmp = true}
    if intra[track.codec] then return false, '帧内编码保持完整解码' end
    for _, filter in ipairs(mp.get_property_native('vf', {}) or {}) do
        local name = tostring(filter.name or ''):lower()
        if name:find('vapoursynth', 1, true) or name:find('rife', 1, true)
            or name == 'lavfi' and tostring(filter.params and filter.params.graph or ''):find('minterpolate', 1, true) then
            return false, '时域滤镜需要完整输入帧'
        end
    end
    local current = mp.get_property('vd-lavc-skipframe', 'default')
    if not catchup.reference and current ~= 'default' then return false, '保留用户指定的解码跳帧' end
    if not catchup.reference and mp.get_property_bool('option-info/vd-lavc-skipframe/set-from-commandline', false) then
        return false, '命令行解码跳帧优先'
    end
    if not catchup.reference and not catchup.managed
        and mp.get_property_bool('option-info/vd-lavc-skipframe/set-locally', false) then
        return false, '文件专用解码跳帧优先'
    end
    return true
end

local function Lag(now)
    local position = mp.get_property_number('time-pos')
    if not position then return end
    local lag = mp.get_property_number('avsync')
    if mp.get_property_native('current-tracks/audio') and lag then return lag end
    -- 没有音轨时使用媒体位置与墙钟的差，暂停／跳转／变速后重新建立锚点。
    local speed = mp.get_property_number('speed', 1)
    catchup.clock = catchup.clock or {now = now, position = position}
    return catchup.clock.position + (now - catchup.clock.now) * speed - position
end

local function Reference(reference, automatic, resync)
    if reload_state.active or catchup.transition then return false, '解码器事务忙' end
    if reference == catchup.reference and not resync then return true end
    if resync and not catchup.reference then return false, '完整解码不执行参考帧重新同步' end
    if reference then
        if not catchup.enabled then return false, '过载追赶未开启' end
        local ready, reason = Eligible()
        if not ready then return false, reason end
    elseif not ActiveVideo() or not CanReposition() then
        if mp.get_property_bool('idle-active', false) or mp.get_property('path', '') == '' then
            CatchupReset('播放已结束')
            return true
        end
        -- 色彩／画质事务可能暂时撤下视频轨；保留所有权，等其恢复后再退出追赶。
        return false, '等待视频轨和可定位位置恢复'
    end
    local skip = reference and 'nonref' or catchup.baseline or 'default'
    if reference and not resync then catchup.baseline = mp.get_property('vd-lavc-skipframe', 'default') end
    local position = mp.get_property_number('time-pos', 0)
    if automatic and reference then
        position = position + math.max(0, Lag(mp.get_time()) or 0)
        local duration = mp.get_property_number('duration')
        if duration then position = math.min(position, math.max(0, duration - .1)) end
    end
    reload_serial = reload_serial + 1
    reload_state.active, reload_state.path = true, mp.get_property('path')
    reload_state.queued, reload_state.started, reload_state.kind = nil, true, 'catchup-video'
    catchup.transition = {reference = reference, skip = skip, path = reload_state.path,
        deadline = mp.get_time() + 20, position = position, resync = resync}
    catchup.phase = resync and '参考帧重新同步' or reference and '进入参考帧追赶' or '恢复完整解码'
    CatchupPublish()
    local vid = mp.get_property('vid', 'auto')
    if vid ~= 'auto' and not vid:match('^%d+$') then vid = 'auto' end
    local paused = mp.get_property_bool('pause', false)
    -- 同一核心命令批次先撤下视频、清空旧码流，再设置模式和恢复轨道。
    -- 显式两次定位保证新解码器从安全位置取流，保留音轨、字幕、线程及文件选项。
    local command = ('no-osd set pause yes; no-osd set file-local-options/vid no; '
        .. 'no-osd seek %.6f absolute+keyframes; '
        .. 'no-osd set file-local-options/vd-lavc-skipframe %s; '
        .. 'no-osd set file-local-options/vid %s; '
        .. 'no-osd seek %.6f absolute+exact; no-osd set pause %s')
        :format(position, skip, vid, position, paused and 'yes' or 'no')
    if resync then
        -- 模式不变时只刷新定位，不撤轨／改参数／重建解码器；仍走同一事务锁。
        command = ('no-osd seek %.6f absolute+exact'):format(position)
    end
    local called, ok, err = pcall(mp.command, command)
    if not called or not ok then
        CancelReload('追赶切换失败')
        return false, err or ok
    end
    CatchupPublish()
    msg.info(('%s：%s，位置 %.3f 秒')
        :format(resync and '参考帧重新同步' or '过载追赶原地视频重建', skip, position))
    return true
end

CatchupComplete = function()
    local transition = catchup.transition
    if not transition then return end
    catchup.transition = nil
    local actual = mp.get_property('vd-lavc-skipframe', 'default')
    if actual ~= transition.skip or mp.get_property('path') ~= transition.path then
        catchup.suspended, catchup.phase = true, '切换未应用，当前文件停止自动追赶'
        msg.error('过载追赶解码参数未按请求生效')
        return
    end
    catchup.reference = transition.reference
    catchup.managed = true
    if transition.resync then catchup.resyncs = catchup.resyncs + 1
    else catchup.switches = catchup.switches + 1 end
    catchup.phase = catchup.reference and '参考帧追赶' or '完整解码'
    if not catchup.reference then catchup.baseline = nil end
    catchup.clock = nil
    if transition.resync then policy:resynced(mp.get_time())
    else policy:commit(catchup.reference, mp.get_time()) end
    msg.info((transition.resync and '参考帧重新同步完成：' or '过载追赶切换完成：') .. actual)
    mp.osd_message(transition.resync and '过载追赶：保持参考帧模式并重新同步'
        or catchup.reference and '过载追赶：跳过部分非参考画面' or '过载追赶：恢复完整解码', 2)
end

local function CatchupToggle(action)
    local enabled
    if action == 'toggle' then enabled = not catchup.enabled
    elseif action == 'on' then enabled = true
    elseif action == 'off' then enabled = false
    else msg.error('无效的过载追赶操作：' .. tostring(action)); return end
    catchup.enabled = enabled
    CatchupInterrupt()
    local saved, err
    if preferences_loaded then saved, err = preferences.set('overload-catchup', enabled) end
    if not saved then msg.error('过载追赶开关未能保存：' .. tostring(err or preferences)) end
    catchup.phase = enabled and '等待稳定播放' or catchup.reference and '等待恢复完整解码' or '关闭'
    CatchupPublish()
    mp.osd_message(enabled and '过载追赶已开启，过载时会省略部分画面' or '过载追赶已关闭', 3)
end

mp.register_script_message('decode-performance-catchup', CatchupToggle)
mp.register_script_message('decode-performance-reference', function(value)
    -- 手动控制与自动判定复用同一事务，便于明确选择和固定样本回归。
    if value ~= 'yes' and value ~= 'no' then msg.error('参考帧模式只接受 yes/no'); return end
    local ok, err = Reference(value == 'yes', false)
    if not ok then msg.warn('参考帧模式未切换：' .. tostring(err)) end
end)

for _, property in ipairs({'pause', 'seeking', 'speed'}) do
    local observed_property = property
    mp.observe_property(property, 'native', function(_, value)
        if observed_property == 'pause' and pending and pending.overrides and type(value) == 'boolean' then
            pending.overrides.pause = value
        end
        CatchupInterrupt()
    end)
end
mp.register_event('seek', CatchupInterrupt)

if policy then
    policy:reset(mp.get_time())
    mp.add_periodic_timer(.25, function()
        if reload_state.active or catchup.transition then
            local transition = catchup.transition
            if reload_state.kind == 'catchup-video' and transition and transition.deadline
                and mp.get_time() >= transition.deadline then
                -- 坏流／极长预热未恢复时只回退一次整文件事务，避免悬挂重载锁。
                transition.deadline = nil
                reload_state.kind, reload_state.started = 'catchup', false
                pending = Copy(state)
                pending.path, pending.reprepare = transition.path, false
                local ok = Reload(mp.get_property('hwdec', 'no'),
                    mp.get_property_native('vd-lavc-threads', 0), mp.get_property_native('vd-lavc-o', {}),
                    {skipframe = transition.skip, position = transition.position})
                if not ok then CancelReload('原地重建和安全回退均失败') end
                msg.warn('过载追赶原地重建等待超时，已采用安全文件重载回退')
            end
            return
        end
        if catchup.reference and mp.get_property('vd-lavc-skipframe', 'default') ~= 'nonref' then
            catchup.reference, catchup.baseline, catchup.suspended = false, nil, true
            catchup.phase, catchup.reason = '尊重外部覆盖', '跳帧参数已被外部修改'
            CatchupPublish()
            return
        end
        if not catchup.enabled then
            if catchup.reference then Reference(false, false) end
            return
        end
        local ready, reason = Eligible()
        if not ready then
            if catchup.reference then Reference(false, false) end
            catchup.phase, catchup.reason = '等待', reason
            policy:interrupt(mp.get_time())
            CatchupPublish()
            return
        end
        local now = mp.get_time()
        local blocked = mp.get_property_bool('pause', false) or mp.get_property_bool('seeking', false)
            or mp.get_property_bool('paused-for-cache', false)
            or mp.get_property_bool('user-data/color-output-rebuilding', false)
        if blocked then catchup.clock = nil end
        local action = policy:step({now = now, blocked = blocked,
            reference = catchup.reference, lag = not blocked and Lag(now) or nil,
            dropped = mp.get_property_number('frame-drop-count'),
            fps = mp.get_property_number('container-fps', mp.get_property_number('estimated-vf-fps', 30)),
            speed = mp.get_property_number('speed', 1)})
        catchup.phase = catchup.reference and '参考帧追赶' or '完整解码'
        catchup.reason = blocked and '暂停／跳转／缓存期间不触发' or nil
        if catchup.reference and not blocked and not o.catchup_recover then
            catchup.reason = '本片保持参考帧模式；关闭追赶可恢复完整解码'
        end
        if action then Reference(action ~= 'full', true, action == 'resync') end
        CatchupPublish()
    end)
end
CatchupPublish()
