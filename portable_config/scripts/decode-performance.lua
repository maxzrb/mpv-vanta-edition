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
local user_policy
local function Copy(value)
    local result = {}
    for k, v in pairs(value or {}) do result[k] = v end
    return result
end

local function Status(phase, delay)
    mp.set_property_native('user-data/decode-performance', {
        state = phase, threads = state.threads, frame_delay = delay,
    })
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
        position = position, pause = mp.get_property_native('pause', false)}
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
    end
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
    if pending and pending.path == mp.get_property('path') and pending.overrides then
        local values = pending.overrides
        Local('hwdec', values.policy)
        Local('vd-lavc-threads', values.threads)
        Local('vd-lavc-o', values.avopts)
        Local('start', tostring(values.position))
        Local('resume-playback', false)
        Local('pause', values.pause)
        for key, files in pairs(values.extra) do Local(key, files) end
        pending.overrides = nil
    end
    -- 菜单选择跨文件保留；显式文件配置仍优先，CPU 滤镜的预加载选择随后运行。
    if user_policy and not mp.get_property_bool('option-info/hwdec/set-locally', false) then
        Local('hwdec', user_policy)
    end
end)
mp.add_hook('on_loaded', 55, Prepare)
mp.register_event('playback-restart', Tune)
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

local function Hardware(policy)
    -- 先撤销本脚本的 dav1d 专用参数，再切硬解，避免传给其它解码器。
    if not policy or policy == '' then return end
    user_policy = policy
    if state.prepared then
        local threads, avopts = OriginalOptions()
        pending = nil
        Reload(policy, threads, avopts)
    else
        mp.set_property('hwdec', policy)
        Prepare()
        Tune()
    end
end
mp.register_script_message('decode-performance-hwdec', Hardware)
mp.add_key_binding(nil, 'decode-performance-toggle-hwdec', function()
    Hardware(mp.get_property('hwdec') == 'no' and 'auto-safe' or 'no')
end)
