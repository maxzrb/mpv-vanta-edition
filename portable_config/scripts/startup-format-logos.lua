-- Professional startup format logos for mpv.
-- Shows at most one picture-standard logo and one audio-standard logo.

local msg = require 'mp.msg'
local options = require 'mp.options'
local utils = require 'mp.utils'
local logo_bounds = dofile(mp.command_native({
    'expand-path', '~~/script-modules/startup-logo-bounds.lua',
}))

local o = {
    enabled = true,
    -- 黑边检测模式：current=后瞻单路 / parallel=后瞻双路并发 /
    -- yaozhi=杳知视觉方案(纯视觉，显示后复检可重定位) / none=不检测(右上角直接显示)
    mode = 'current',
    show_video = true,
    show_audio = true,
    show_sdr = true,
    show_common_audio = true,
    require_video = false,
    filename_fallback = true,
    show_on_audio_change = true,
    position = 'top-right',
    anchor_to_video = true,
    detect_encoded_bars = true,
    encoded_bar_threshold = 16,
    encoded_bar_delay = 0.18,
    encoded_bar_samples = 3,
    encoded_bar_sample_interval = 0.22,
    -- 偏黑/稀疏画面（内容覆盖率低于该值）不采用黑边锚点，避免暗部被误判成黑边
    encoded_bar_min_coverage = 0.3,
    -- 后瞻：起播黑屏/稀疏画面时，在 encoded_bar_lookahead_min ~ encoded_bar_lookahead 秒
    -- 窗口内随机采样 encoded_bar_lookahead_samples 处（第一处落在下限~下限+1s，
    -- 任意两处间隔 >= encoded_bar_lookahead_gap 秒），并行解码对应帧，任一帧可信即用；
    -- 0=关闭，找不到 ffmpeg 自动回退复检
    encoded_bar_lookahead = 10,
    encoded_bar_lookahead_min = 3,
    encoded_bar_lookahead_samples = 3,
    encoded_bar_lookahead_gap = 2,
    -- 首窗只得到“无黑边”时，扩大到该时间点做第二窗确认；避免片头全幅 Logo
    -- 先于正片窄黑边出现时，过早把徽章锁到右上角。<= lookahead 可关闭确认窗。
    encoded_bar_confirm_min = 30,
    encoded_bar_confirm_lookahead = 75,
    encoded_bar_confirm_samples = 3,
    -- 双路模式首个快速深探针；优先跨过发行方片头，并避免随机落到 AV1 慢 GOP。
    encoded_bar_fast_probe = 40,
    -- 旧键兼容：>= 0 时覆盖 encoded_bar_fast_probe；新配置不要再使用。
    encoded_bar_parallel_fast_probe = -1,
    -- 后瞻 ffmpeg 解码线程数。4 在 4K HEVC 上能明显降低起播 CPU 峰值，
    -- 同时只比自动线程略慢；设为 0 交给 ffmpeg 自动决定。
    encoded_bar_ffmpeg_threads = 4,
    encoded_bar_followup_delay = 2.5,
    encoded_bar_followup_interval = 1.5,
    encoded_bar_followup_samples = 3,
    scale = 1.0,
    portrait_scale = 1.18,
    margin_x = 60,
    margin_y = 38,
    delay = 0.45,
    hold = 4.0,
    frame_wait_timeout = 5.0,
    fade_in = 0.12,
    fade_out = 0.18,
    retry_interval = 0.25,
    retry_count = 8,
    style = 'color',
    video_priority = 'dolby-vision,hdr-vivid,hdr10-plus,hdr10,hlg,sdr',
    audio_priority = 'dolby-atmos,dts-x,audio-vivid,dolby-truehd,dts-hd-ma,dts-hd-hra,dolby-digital-plus,dolby-digital,dts,ac4,mpeg-h,flac,alac,pcm,mlp,wavpack,ape,wma,opus,aac,vorbis,mp3',
    asset_dir = '~~/script-assets/startup-format-logos/runtime',
    overlay_id = 50,
}

options.read_options(o, 'startup_format_logos')

local function normalize_style(value)
    return tostring(value or ''):lower() == 'white' and 'white' or 'color'
end

local function normalize_mode(value)
    local mode = tostring(value or ''):lower()
    if mode == 'parallel' then return 'parallel' end
    if mode == 'yaozhi' then return 'yaozhi' end
    if mode == 'none' or mode == 'off' or mode == 'no' then return 'none' end
    return 'current'
end

o.style = normalize_style(o.style)
o.mode = normalize_mode(o.mode)

-- none 模式：不检测编码黑边，等效 detect_encoded_bars=no
local function effective_detect_encoded_bars()
    if o.mode == 'none' then return false end
    return o.detect_encoded_bars == true
end

local state = {
    loaded = false,
    file_generation = 0,
    display_generation = 0,
    timers = {},
    visible = false,
    overlays_present = false,
    opacity_index = 0,
    current = nil,
    last_aid = nil,
    frame_ready = false,
    waiting_for_frame = false,
    content_insets = nil,
    -- 当前 content_insets 是否命中画幅白名单；false=纯视觉兜底，nil=无结果
    content_insets_matched = nil,
    -- 徽标是否已显示；一旦显示，锚点冻结不再移动（避免黑屏→亮屏时徽标跳位）
    badge_displayed = false,
    -- 后瞻 ffmpeg 解码是否进行中（防重入）
    lookahead_busy = false,
    lookahead_requests = {},
    bar_request = nil,
    overlay_error_logged = false,
}

local asset_root = nil
local manifest = nil
local levels = nil
local overlay_base = math.floor(tonumber(o.overlay_id) or 50)
local config_path = mp.command_native({
    'expand-path', '~~/script-opts/startup_format_logos.conf',
})


local function clamp(value, low, high)
    return math.max(low, math.min(high, value))
end


local function cancel_lookahead_requests()
    for request in pairs(state.lookahead_requests) do
        pcall(mp.abort_async_command, request)
    end
    state.lookahead_requests = {}
    state.lookahead_busy = false
end


local function round(value)
    return math.floor(value + 0.5)
end


local function number_option(value, fallback)
    local number = tonumber(value)
    if number == nil then return fallback end
    return number
end


local function stop_timer(name)
    local timer = state.timers[name]
    if timer then
        timer:kill()
        state.timers[name] = nil
    end
end


local function schedule(name, delay, callback)
    stop_timer(name)
    local timer
    timer = mp.add_timeout(math.max(0, tonumber(delay) or 0), function()
        if state.timers[name] == timer then
            state.timers[name] = nil
        end
        callback()
    end)
    state.timers[name] = timer
end


local function join_path(root, child)
    return utils.join_path(root, child)
end


local function read_text_file(path)
    local handle, err = io.open(path, 'rb')
    if not handle then return nil, err end
    local content = handle:read('*a')
    handle:close()
    return content
end


local function persist_option(name, value)
    local handle = io.open(config_path, 'rb')
    local content = handle and handle:read('*a') or ''
    if handle then handle:close() end

    local escaped_name = tostring(name):gsub('([^%w])', '%%%1')
    local serialized = tostring(value)
    local replaced
    content, replaced = content:gsub(
        '^([ \t]*' .. escaped_name .. '[ \t]*=)[^\r\n]*',
        '%1' .. serialized,
        1
    )
    if replaced == 0 then
        content, replaced = content:gsub(
            '(\r?\n)([ \t]*' .. escaped_name .. '[ \t]*=)[^\r\n]*',
            '%1%2' .. serialized,
            1
        )
    end
    if replaced == 0 then
        content = tostring(name) .. '=' .. serialized .. '\n' .. content
    end

    handle = io.open(config_path, 'wb')
    if not handle then
        msg.error('Unable to persist startup logo setting: ' .. tostring(config_path))
        return false
    end
    handle:write(content)
    handle:close()
    return true
end


local function load_assets()
    asset_root = mp.command_native({'expand-path', o.asset_dir})
    if not asset_root or asset_root == '' then
        msg.error('Unable to expand startup logo asset directory')
        return false
    end

    local raw, read_err = read_text_file(join_path(asset_root, 'manifest.json'))
    if not raw then
        msg.error('Unable to read startup logo manifest: ' .. tostring(read_err))
        return false
    end

    local parsed, parse_err = utils.parse_json(raw)
    if type(parsed) ~= 'table' then
        msg.error('Unable to parse startup logo manifest: ' .. tostring(parse_err))
        return false
    end
    if type(parsed.opacity_levels) ~= 'table'
        or type(parsed.backgrounds) ~= 'table'
        or type(parsed.logos) ~= 'table'
        or type(parsed.base_layout) ~= 'table' then
        msg.error('Startup logo manifest is incomplete')
        return false
    end

    manifest = parsed
    levels = parsed.opacity_levels
    table.sort(levels, function(a, b) return tonumber(a) < tonumber(b) end)
    msg.info(string.format(
        'assets loaded: %d logos, %d opacity levels',
        (function()
            local count = 0
            for _ in pairs(parsed.logos) do count = count + 1 end
            return count
        end)(),
        #levels
    ))
    return true
end


local function publish_state()
    local current = state.current or {}
    mp.set_property_bool('user-data/startup-format-logos/enabled', o.enabled == true)
    mp.set_property('user-data/startup-format-logos/mode', o.mode)
    mp.set_property('user-data/startup-format-logos/style', o.style)
    mp.set_property('user-data/startup-format-logos/video', current.video or '')
    mp.set_property('user-data/startup-format-logos/audio', current.audio or '')
    mp.set_property('user-data/startup-format-logos/visible', state.visible and 'yes' or 'no')
end


local function remove_overlay(id)
    pcall(mp.command_native, {'overlay-remove', id})
end


local function remove_overlays()
    if state.overlays_present then
        remove_overlay(overlay_base)
        remove_overlay(overlay_base + 1)
        remove_overlay(overlay_base + 2)
    end
    state.overlays_present = false
    state.visible = false
    state.opacity_index = 0
    publish_state()
end


local function cancel_display(clear_current)
    state.display_generation = state.display_generation + 1
    stop_timer('animation')
    stop_timer('hold')
    remove_overlays()
    if clear_current then
        state.current = nil
        publish_state()
    end
end


local function split_priority(value)
    local result = {}
    for token in tostring(value or ''):gmatch('[^,%s]+') do
        result[#result + 1] = token:lower()
    end
    return result
end


local function choose_candidate(candidates, priority)
    if not manifest then return nil end
    for _, slug in ipairs(split_priority(priority)) do
        if candidates[slug] and manifest.logos[slug] then
            return slug
        end
    end
    return nil
end


local function read_selected_track(kind)
    local selector = kind == 'audio' and 'aid' or (kind == 'video' and 'vid' or nil)
    if selector then
        local selected_id = mp.get_property_native(selector)
        if selected_id == false or tostring(selected_id or '') == 'no' then
            return nil
        end
    end

    local current = mp.get_property_native('current-tracks/' .. kind, {})
    if type(current) == 'table' and current.type == kind then
        return current
    end

    local tracks = mp.get_property_native('track-list', {})
    if type(tracks) == 'table' then
        local fallback = nil
        local count = 0
        for _, track in ipairs(tracks) do
            if type(track) == 'table' and track.type == kind then
                if track.selected == true then return track end
                count = count + 1
                fallback = fallback or track
            end
        end
        -- A lone track is safe during the short interval before mpv marks it
        -- selected. With multiple tracks, guessing the first one can display
        -- the wrong family before aid/vid settles.
        if count == 1 then return fallback end
    end
    return nil
end


local function count_tracks(kind)
    local count = 0
    local tracks = mp.get_property_native('track-list', {})
    if type(tracks) == 'table' then
        for _, track in ipairs(tracks) do
            if type(track) == 'table' and track.type == kind then
                count = count + 1
            end
        end
    end
    return count
end


local function has_real_video_track()
    local track = read_selected_track('video')
    return type(track) == 'table'
        and track.type == 'video'
        and track.albumart ~= true
end


local function append_context(parts, value)
    if type(value) == 'string' or type(value) == 'number' then
        parts[#parts + 1] = tostring(value)
    end
end


local TRACK_TEXT_FIELDS = {
    'codec', 'codec-desc', 'codec-profile', 'decoder-desc',
    'demux-codec', 'title', 'lang', 'format',
}


local function build_context(track, include_filename, extra)
    local parts = {}
    append_context(parts, extra)
    if type(track) == 'table' then
        for _, field in ipairs(TRACK_TEXT_FIELDS) do
            append_context(parts, track[field])
        end
        if type(track.metadata) == 'table' then
            for key, value in pairs(track.metadata) do
                append_context(parts, key)
                append_context(parts, value)
            end
        end
    end
    if include_filename then
        append_context(parts, mp.get_property('filename', ''))
        append_context(parts, mp.get_property('media-title', ''))
        append_context(parts, mp.get_property('path', ''))
    end
    local raw = table.concat(parts, ' '):lower()
    -- Keep the meaning of literal "+" markers before stripping punctuation.
    -- This makes filenames such as HDR10+ and DD+ match the same rules as
    -- their spelled-out forms without weakening the brand checks.
    local compact = raw:gsub('%+', 'plus')
        :gsub('[%s%._%-:/\\%[%]%(%)]+', '')
    return raw, compact
end


local function contains_plain(text, needle)
    return text:find(needle, 1, true) ~= nil
end


local function positive(value)
    local number = tonumber(value)
    return number ~= nil and number > 0
end


local function has_dolby_vision(track, params, compact)
    if type(track) == 'table' then
        if positive(track['dolby-vision-profile']) or track['dolby-vision-level'] ~= nil then
            return true
        end
    end
    if type(params) == 'table' then
        if positive(params['dolby-vision-profile']) or params['dolby-vision-level'] ~= nil then
            return true
        end
    end
    return contains_plain(compact, 'dolbyvision')
        or contains_plain(compact, 'dovi')
        or contains_plain(compact, 'dvhe')
        or contains_plain(compact, 'dvh1')
end


local function has_hdr10_plus(track, params, compact)
    if type(track) == 'table' then
        if track.hdr10plus == true
            or positive(track['scene-max-r'])
            or positive(track['scene-max-g'])
            or positive(track['scene-max-b']) then
            return true
        end
    end
    if type(params) == 'table' then
        if params.hdr10plus == true
            or positive(params['scene-max-r'])
            or positive(params['scene-max-g'])
            or positive(params['scene-max-b']) then
            return true
        end
    end
    return contains_plain(compact, 'hdr10plus')
        or contains_plain(compact, 'hdr10p')
end


local function detect_video_candidates(track)
    local candidates = {}
    if type(track) ~= 'table' or track.type ~= 'video' or track.albumart == true then
        return candidates
    end

    local params = mp.get_property_native('video-params', {})
    local _, compact = build_context(track, o.filename_fallback, nil)
    if has_dolby_vision(track, params, compact) then
        candidates['dolby-vision'] = true
    end
    if (type(params) == 'table' and params['hdr-vivid'] == true)
        or (o.filename_fallback
            and (contains_plain(compact, 'hdrvivid')
                or contains_plain(compact, 'cuvahdr'))) then
        candidates['hdr-vivid'] = true
    end
    if has_hdr10_plus(track, params, compact) then
        candidates['hdr10-plus'] = true
    end

    local gamma = type(params) == 'table'
        and tostring(params.gamma or params.transfer or ''):lower()
        or ''
    if gamma == 'pq' or gamma == 'smpte2084'
        or (o.filename_fallback and contains_plain(compact, 'hdr10')) then
        candidates.hdr10 = true
    end
    if gamma == 'hlg'
        or gamma == 'arib-std-b67'
        or gamma == 'aribstdb67'
        or (o.filename_fallback and contains_plain(compact, 'hlg')) then
        candidates.hlg = true
    end
    if o.show_sdr then
        candidates.sdr = true
    end
    return candidates
end


local function detect_audio_candidates(track, include_filename)
    local candidates = {}
    if type(track) ~= 'table' or track.type ~= 'audio' then
        return candidates
    end

    local codec = mp.get_property('audio-codec', '')
    local raw, compact = build_context(track, include_filename == true, codec)
    local _, codec_compact = build_context(track, false, codec)

    if contains_plain(compact, 'atmos')
        or contains_plain(compact, 'dolbyatmos')
        or raw:match('%f[%w]joc%f[%W]') then
        candidates['dolby-atmos'] = true
    end
    if contains_plain(compact, 'dtsx') then
        candidates['dts-x'] = true
    end
    if contains_plain(codec_compact, 'av3a')
        or contains_plain(compact, 'audiovivid')
        or contains_plain(compact, 'avs3audio') then
        candidates['audio-vivid'] = true
    end
    if contains_plain(compact, 'truehd')
        or contains_plain(compact, 'mlpfba') then
        candidates['dolby-truehd'] = true
    end
    if contains_plain(compact, 'dtshdmasteraudio')
        or contains_plain(compact, 'dtshdmaster')
        or contains_plain(compact, 'dtshdma')
        or contains_plain(compact, 'dtsma') then
        candidates['dts-hd-ma'] = true
    end
    if contains_plain(compact, 'dtshdhighresolutionaudio')
        or contains_plain(compact, 'dtshdhighresolution')
        or contains_plain(compact, 'dtshdhra')
        or contains_plain(compact, 'dtshighres') then
        candidates['dts-hd-hra'] = true
    end
    if contains_plain(compact, 'dolbydigitalplus')
        or contains_plain(compact, 'eac3')
        or contains_plain(compact, 'ddplus')
        or contains_plain(compact, 'ddp') then
        candidates['dolby-digital-plus'] = true
    end
    if contains_plain(codec_compact, 'ac3')
        or contains_plain(compact, 'dolbydigital') then
        candidates['dolby-digital'] = true
    end
    if contains_plain(codec_compact, 'dca')
        or contains_plain(codec_compact, 'dts')
        or raw:match('%f[%w]dts%f[%W]') then
        candidates.dts = true
    end

    -- AC-4 and MPEG-H are immersive delivery formats, not ordinary fallback
    -- codecs. They remain available when common FLAC/AAC/PCM badges are off.
    if contains_plain(codec_compact, 'ac4') then
        candidates.ac4 = true
    end
    if contains_plain(codec_compact, 'mpegh')
        or contains_plain(codec_compact, 'mhm1')
        or contains_plain(codec_compact, 'mha1') then
        candidates['mpeg-h'] = true
    end

    if o.show_common_audio then
        if contains_plain(codec_compact, 'flac') then
            candidates.flac = true
        end
        if contains_plain(codec_compact, 'alac') then
            candidates.alac = true
        end
        if contains_plain(codec_compact, 'pcm')
            or contains_plain(codec_compact, 'lpcm') then
            candidates.pcm = true
        end
        if contains_plain(codec_compact, 'mlp')
            and not candidates['dolby-truehd'] then
            candidates.mlp = true
        end
        if contains_plain(codec_compact, 'wavpack')
            or codec_compact == 'wv' then
            candidates.wavpack = true
        end
        if codec_compact == 'ape'
            or contains_plain(codec_compact, 'monkeysaudio') then
            candidates.ape = true
        end
        if codec_compact == 'wma'
            or contains_plain(codec_compact, 'wmav1')
            or contains_plain(codec_compact, 'wmav2')
            or contains_plain(codec_compact, 'wmapro')
            or contains_plain(codec_compact, 'wmavoice')
            or contains_plain(codec_compact, 'wmalossless')
            or contains_plain(codec_compact, 'windowsmediaaudio') then
            candidates.wma = true
        end
        if contains_plain(codec_compact, 'opus') then
            candidates.opus = true
        end
        if contains_plain(codec_compact, 'aac') then
            candidates.aac = true
        end
        if contains_plain(codec_compact, 'vorbis') then
            candidates.vorbis = true
        end
        if contains_plain(codec_compact, 'mp3') then
            candidates.mp3 = true
        end
    end
    return candidates
end


local DOLBY_AUDIO_CANDIDATES = {
    ['dolby-atmos'] = true,
    ['dolby-truehd'] = true,
    ['dolby-digital-plus'] = true,
    ['dolby-digital'] = true,
}


local DTS_AUDIO_CANDIDATES = {
    ['dts-x'] = true,
    ['dts-hd-ma'] = true,
    ['dts-hd-hra'] = true,
    dts = true,
}


local AUDIO_CODEC_FIELDS = {
    'codec', 'codec-desc', 'codec-profile', 'decoder-desc',
    'demux-codec', 'format',
}


local function selected_audio_profile(track)
    local codec_track = {type = 'audio'}
    if type(track) == 'table' then
        for _, field in ipairs(AUDIO_CODEC_FIELDS) do
            codec_track[field] = track[field]
        end
    end

    local codec = mp.get_property('audio-codec', '')
    local _, compact = build_context(codec_track, false, codec)
    local dts_family = contains_plain(compact, 'dca')
        or contains_plain(compact, 'dts')
    local atmos_carrier = contains_plain(compact, 'truehd')
        or contains_plain(compact, 'mlpfba')
        or contains_plain(compact, 'eac3')
        or contains_plain(compact, 'ec3')
        or contains_plain(compact, 'ac4')
    local dolby_family = atmos_carrier
        or contains_plain(compact, 'ac3')
        or contains_plain(compact, 'mlp')
        or contains_plain(compact, 'dolbydigital')
        or contains_plain(compact, 'dolbytruehd')

    if dts_family then return 'dts', false end
    if dolby_family then return 'dolby', atmos_carrier end
    if compact ~= '' then return 'other', false end
    return 'unknown', false
end


local function remove_candidate_family(candidates, family)
    for slug in pairs(family) do
        candidates[slug] = nil
    end
end


local function filter_audio_candidates(candidates, family, atmos_carrier)
    if family == 'dts' then
        remove_candidate_family(candidates, DOLBY_AUDIO_CANDIDATES)
    elseif family == 'dolby' then
        remove_candidate_family(candidates, DTS_AUDIO_CANDIDATES)
        if not atmos_carrier then
            candidates['dolby-atmos'] = nil
        end
    elseif family == 'other' then
        remove_candidate_family(candidates, DOLBY_AUDIO_CANDIDATES)
        remove_candidate_family(candidates, DTS_AUDIO_CANDIDATES)
    end
    return candidates
end


local function merge_candidate_family(target, source, family)
    for slug in pairs(family) do
        if source[slug] then target[slug] = true end
    end
end


local function detect_selected_audio(track)
    if type(track) ~= 'table' or track.type ~= 'audio' then return nil end

    local family, atmos_carrier = selected_audio_profile(track)
    local candidates = filter_audio_candidates(
        detect_audio_candidates(track, false),
        family,
        atmos_carrier
    )

    -- File names describe the whole container, not the selected audio track.
    -- They are therefore unsafe in multi-audio files. For a single track they
    -- may only refine a compatible codec family, never replace it with Dolby
    -- or DTS from another family.
    if o.filename_fallback and count_tracks('audio') == 1 then
        local fallback = filter_audio_candidates(
            detect_audio_candidates(track, true),
            family,
            atmos_carrier
        )
        if family == 'dts' then
            merge_candidate_family(candidates, fallback, DTS_AUDIO_CANDIDATES)
        elseif family == 'dolby' and atmos_carrier and fallback['dolby-atmos'] then
            candidates['dolby-atmos'] = true
        end
    end

    return choose_candidate(candidates, o.audio_priority)
end


local function detect_pair()
    local video_track = read_selected_track('video')
    if o.require_video and not has_real_video_track() then
        return nil, nil
    end

    local audio_track = read_selected_track('audio')
    local video = o.show_video
        and choose_candidate(detect_video_candidates(video_track), o.video_priority)
        or nil
    local audio = o.show_audio
        and detect_selected_audio(audio_track)
        or nil
    local audio_pending = false
    if o.show_audio and not audio then
        if type(audio_track) == 'table' and audio_track.type == 'audio' then
            audio_pending = true
        else
            local aid = mp.get_property_native('aid')
            if aid ~= false and tostring(aid or '') ~= 'no'
                and count_tracks('audio') > 0 then
                audio_pending = true
            end
        end
    end
    return video, audio, audio_pending
end


local function get_osd_size()
    local width = mp.get_property_number('osd-width', 0)
    local height = mp.get_property_number('osd-height', 0)
    if width <= 0 or height <= 0 then return nil, nil end
    return width, height
end


local function get_viewport_scale(osd_width, osd_height)
    -- Keep the same physical hierarchy when the player window follows a
    -- portrait video instead of treating its short width as a landscape view.
    if osd_height > osd_width then
        return math.min(osd_width / 1080, osd_height / 1920)
    end
    return math.min(osd_width / 1920, osd_height / 1080)
end


local function get_video_bounds(osd_width, osd_height)
    local bounds = {
        left = 0,
        top = 0,
        right = osd_width,
        bottom = osd_height,
    }
    if not o.anchor_to_video then return bounds end

    local dimensions = mp.get_property_native('osd-dimensions', {})
    if type(dimensions) ~= 'table' then return bounds end

    local left = clamp(tonumber(dimensions.ml) or 0, 0, osd_width)
    local top = clamp(tonumber(dimensions.mt) or 0, 0, osd_height)
    local right = clamp(osd_width - (tonumber(dimensions.mr) or 0), 0, osd_width)
    local bottom = clamp(osd_height - (tonumber(dimensions.mb) or 0), 0, osd_height)
    if right <= left or bottom <= top then return bounds end

    bounds.left = left
    bounds.top = top
    bounds.right = right
    bounds.bottom = bottom

    -- osd-dimensions only describes bars added by mpv. Blu-ray/ISO video often
    -- carries black bars inside the decoded 16:9 frame, so apply the normalized
    -- pixel probe as an additional safe area. Sparse opening frames receive a
    -- few follow-up probes, so a later stable letterbox can safely re-anchor
    -- the badge without seeking or delaying playback. If another script has
    -- already cropped the video, ignore these insets to avoid double-cropping.
    local insets = state.content_insets
    local video_crop = mp.get_property('video-crop', '')
    if type(insets) == 'table' and (not video_crop or video_crop == '') then
        local video_width = bounds.right - bounds.left
        local video_height = bounds.bottom - bounds.top
        bounds.left = bounds.left + video_width * (tonumber(insets.left) or 0)
        bounds.right = bounds.right - video_width * (tonumber(insets.right) or 0)
        bounds.top = bounds.top + video_height * (tonumber(insets.top) or 0)
        bounds.bottom = bounds.bottom - video_height * (tonumber(insets.bottom) or 0)
    end
    return bounds
end




local function compute_layout(kind)
    local osd_width, osd_height = get_osd_size()
    if not osd_width then return nil end

    local base = manifest.base_layout[kind]
    local bounds = get_video_bounds(osd_width, osd_height)
    local available_width = bounds.right - bounds.left
    local available_height = bounds.bottom - bounds.top
    local viewport_scale = get_viewport_scale(osd_width, osd_height)
    local orientation_scale = osd_height > osd_width
        and number_option(o.portrait_scale, 1.18)
        or 1.0
    local display_scale = clamp(
        viewport_scale * number_option(o.scale, 1.0) * orientation_scale,
        0.25,
        2.0
    )
    local fit_scale = math.min(
        (available_width - 24) / tonumber(base.w),
        (available_height - 24) / tonumber(base.h)
    )
    display_scale = math.min(display_scale, fit_scale)
    if display_scale <= 0 then return nil end

    local width = round(tonumber(base.w) * display_scale)
    local height = round(tonumber(base.h) * display_scale)
    local margin_x = round(number_option(o.margin_x, 60) * viewport_scale)
    local margin_y = round(number_option(o.margin_y, 38) * viewport_scale)
    local position = tostring(o.position):lower():gsub('_', '-')
    local left = position:find('left', 1, true) ~= nil
    local bottom = position:find('bottom', 1, true) ~= nil
    local x = left
        and bounds.left + margin_x
        or bounds.right - width - margin_x
    local y = bottom
        and bounds.bottom - height - margin_y
        or bounds.top + margin_y

    return {
        x = round(clamp(x, bounds.left, bounds.right - width)),
        y = round(clamp(y, bounds.top, bounds.bottom - height)),
        w = width,
        h = height,
        scale = display_scale,
        base = base,
    }
end


local function overlay_add(id, x, y, file, width, height, display_width, display_height)
    local ok, err = pcall(mp.command_native, {
        'overlay-add', id, x, y, file, 0, 'bgra',
        width, height, width * 4, display_width, display_height,
    })
    if not ok then
        if not state.overlay_error_logged then
            msg.error('Unable to render startup logo overlay: ' .. tostring(err))
            state.overlay_error_logged = true
        end
        return false
    end
    return true
end


local function render_logo(id, slug, level_key, layout, center_y)
    local asset = manifest.logos[slug]
    if not asset then return false end
    local source_scale = tonumber(manifest.source_scale) or 2
    local base_logo_width = tonumber(manifest.base_layout.logo_max_w)
        or asset.w / source_scale
    local base_logo_height = tonumber(manifest.base_layout.logo_max_h)
        or asset.h / source_scale
    local display_width = math.max(1, round(base_logo_width * layout.scale))
    local display_height = math.max(1, round(base_logo_height * layout.scale))
    local white = o.style == 'white'
    local variants = white and asset.white_variants or asset.variants
    local source = {
        w = asset.w,
        h = asset.h,
        files = white and asset.white_files or asset.files,
    }
    if type(variants) == 'table' then
        -- Use the smallest source that is at least as large as the target.
        -- 1080p therefore renders the 156x64 tier 1:1, while 1440p/4K use
        -- the 312x128 tier and avoid unnecessary double filtering.
        local one_x = variants['1']
        local two_x = variants['2']
        if type(one_x) == 'table'
            and display_width <= (tonumber(one_x.w) or 0)
            and display_height <= (tonumber(one_x.h) or 0) then
            source = one_x
        elseif type(two_x) == 'table' then
            source = two_x
        end
    end
    local filename = type(source.files) == 'table' and source.files[level_key]
    if not filename then return false end
    local x = round(layout.x + layout.w / 2 - display_width / 2)
    local y = round(layout.y + center_y * layout.scale - display_height / 2)
    return overlay_add(
        id, x, y, join_path(asset_root, filename),
        source.w, source.h, display_width, display_height
    )
end


local function render_level(index)
    if not manifest or not state.current then return false end
    local level = levels[index]
    if not level then return false end
    local level_key = tostring(level)
    local double = state.current.video ~= nil and state.current.audio ~= nil
    local kind = double and 'double' or 'single'
    local layout = compute_layout(kind)
    if not layout then return false end
    local background = manifest.backgrounds[kind]
    local background_file = background
        and type(background.files) == 'table'
        and background.files[level_key]
        or nil
    if background_file then
        local background_ok = overlay_add(
            overlay_base,
            layout.x,
            layout.y,
            join_path(asset_root, background_file),
            background.w,
            background.h,
            layout.w,
            layout.h
        )
        if not background_ok then return false end
    else
        -- Color-badge assets carry their own dark surface and accent rim.
        -- The shared background remains optional for other asset themes.
        remove_overlay(overlay_base)
    end

    if double then
        render_logo(
            overlay_base + 1,
            state.current.video,
            level_key,
            layout,
            tonumber(layout.base.top_center_y)
        )
        render_logo(
            overlay_base + 2,
            state.current.audio,
            level_key,
            layout,
            tonumber(layout.base.bottom_center_y)
        )
    else
        local slug = state.current.video or state.current.audio
        render_logo(
            overlay_base + 1,
            slug,
            level_key,
            layout,
            tonumber(layout.base.center_y)
        )
        remove_overlay(overlay_base + 2)
    end

    state.overlays_present = true
    state.visible = true
    state.opacity_index = index
    publish_state()
    return true
end


local function start_fade_out(generation)
    if generation ~= state.display_generation then return end
    local count = #levels
    local duration = math.max(0, tonumber(o.fade_out) or 0)
    if duration <= 0 or count <= 1 then
        remove_overlays()
        return
    end

    local interval = duration / count
    local index = count - 1
    local function step()
        if generation ~= state.display_generation then return end
        if index < 1 then
            remove_overlays()
            return
        end
        render_level(index)
        index = index - 1
        schedule('animation', interval, step)
    end
    schedule('animation', interval, step)
end


local function finish_fade_in(generation)
    if generation ~= state.display_generation then return end
    local hold = math.max(0, tonumber(o.hold) or 0)
    schedule('hold', hold, function() start_fade_out(generation) end)
end


local function start_fade_in(generation)
    local count = #levels
    local duration = math.max(0, tonumber(o.fade_in) or 0)
    if duration <= 0 or count <= 1 then
        render_level(count)
        finish_fade_in(generation)
        return
    end

    local interval = duration / (count - 1)
    local index = 1
    local function step()
        if generation ~= state.display_generation then return end
        render_level(index)
        if index >= count then
            finish_fade_in(generation)
            return
        end
        index = index + 1
        schedule('animation', interval, step)
    end
    step()
end


local function show_pair(video, audio, reason)
    if not o.enabled or not manifest then return false end
    if not video and not audio then return false end
    if video and not manifest.logos[video] then video = nil end
    if audio and not manifest.logos[audio] then audio = nil end
    if not video and not audio then return false end

    cancel_display(false)
    state.current = {video = video, audio = audio}
    local generation = state.display_generation
    publish_state()
    msg.debug(string.format(
        'show (%s): video=%s audio=%s style=%s',
        tostring(reason or 'unknown'),
        tostring(video or 'none'),
        tostring(audio or 'none'),
        o.style
    ))
    start_fade_in(generation)
    return true
end


local function detect_and_show(file_generation, attempt, reason)
    if file_generation ~= state.file_generation or not state.loaded or not o.enabled then
        return
    end
    local video, audio, audio_pending = detect_pair()
    local max_attempts = math.max(1, math.floor(tonumber(o.retry_count) or 1))
    if (video or audio) and not (audio_pending and attempt < max_attempts) then
        show_pair(video, audio, reason)
        return
    end

    if attempt < max_attempts then
        schedule('retry', tonumber(o.retry_interval) or 0.25, function()
            detect_and_show(file_generation, attempt + 1, reason)
        end)
    else
        state.current = nil
        publish_state()
        msg.debug('no premium startup logo detected')
    end
end


local function schedule_detection(reason, delay)
    local file_generation = state.file_generation
    stop_timer('retry')
    schedule('retry', delay or 0, function()
        detect_and_show(file_generation, 1, reason)
    end)
end


local function has_video_geometry()
    local params = mp.get_property_native('video-out-params', {})
    if type(params) ~= 'table' then return false end
    local width = tonumber(params.dw) or tonumber(params.w)
    local height = tonumber(params.dh) or tonumber(params.h)
    if not width or width <= 0 or not height or height <= 0 then return false end

    local dimensions = mp.get_property_native('osd-dimensions', {})
    return type(dimensions) == 'table'
        and tonumber(dimensions.w) ~= nil
        and tonumber(dimensions.h) ~= nil
        and tonumber(dimensions.w) > 0
        and tonumber(dimensions.h) > 0
end

-- 杳知 8.12 视觉方案复检：稀疏开场先显示默认位，随后复检出现黑边时
-- 直接更新锚点并重渲染（显示后可移动），不等待、不延迟起播。
local function start_yaozhi_bar_followup(file_generation)
    local remaining = clamp(
        math.floor(tonumber(o.encoded_bar_followup_samples) or 3),
        0,
        5
    )
    if remaining <= 0 then return end
    local interval = clamp(
        tonumber(o.encoded_bar_followup_interval) or 1.5,
        0.5,
        4.0
    )

    local function request_sample()
        -- 已有黑边结果即停止（杳知原版）
        if file_generation ~= state.file_generation or not state.loaded
            or state.content_insets ~= nil or remaining <= 0 then
            return
        end
        remaining = remaining - 1
        local ok, request = pcall(mp.command_native_async, {
            name = 'screenshot-raw', flags = 'video', format = 'bgr0',
        }, function(success, frame)
            state.bar_request = nil
            if file_generation ~= state.file_generation or not state.loaded then return end
            if success then
                -- 杳知视觉方案：纯像素检测，不做画幅白名单与偏黑门槛
                local insets = logo_bounds.detect(
                    frame, o.encoded_bar_threshold, 0
                )
                if insets then
                    state.content_insets = insets
                    msg.debug(string.format(
                        'yaozhi followup: left=%.4f top=%.4f right=%.4f bottom=%.4f',
                        tonumber(insets.left) or 0,
                        tonumber(insets.top) or 0,
                        tonumber(insets.right) or 0,
                        tonumber(insets.bottom) or 0
                    ))
                    -- 已显示则重定位，未显示则正常显示
                    if state.visible and state.opacity_index > 0 then
                        render_level(state.opacity_index)
                    else
                        schedule_detection('yaozhi-followup', tonumber(o.delay) or 0.45)
                    end
                    return
                end
            end
            if remaining > 0 then schedule('bar-followup', interval, request_sample) end
        end)
        if ok then
            state.bar_request = request
        elseif remaining > 0 then
            schedule('bar-followup', interval, request_sample)
        end
    end

    schedule(
        'bar-followup',
        clamp(tonumber(o.encoded_bar_followup_delay) or 2.5, 0.5, 8.0),
        request_sample
    )
end


-- 全黑开场、片头 Logo 等稀疏画面无法可靠锁定徽章锚点：徽标暂不显示，
-- 在正常播放中安排少量廉价复检（不 seek、不延迟起播），一旦出现可信内容
-- 画面（检测到黑边，或覆盖率足够且确认无黑边）就一次性显示到位并冻结锚点；
-- 复检次数耗尽仍未出现可信画面时兜底显示，避免徽标缺失。
local function start_ambiguous_bar_followup(file_generation)
    local remaining = clamp(
        math.floor(tonumber(o.encoded_bar_followup_samples) or 3),
        0,
        5
    )
    if remaining <= 0 then return end
    local interval = clamp(
        tonumber(o.encoded_bar_followup_interval) or 1.5,
        0.5,
        4.0
    )

    -- 复检耗尽仍未出现可信内容画面：兜底显示（避免中心文字、长时间黑屏等
    -- 低覆盖开场导致徽标永久缺失）。所有剩余次数用尽后必然走到这里。
    local function fallback_show()
        if file_generation ~= state.file_generation or not state.loaded
            or state.badge_displayed then
            return
        end
        state.badge_displayed = true
        schedule_detection('sparse-timeout', tonumber(o.delay) or 0.45)
    end

    local function request_sample()
        -- 徽标已显示或文件已切换：停止（已显示的徽标绝不移动）
        if file_generation ~= state.file_generation or not state.loaded
            or state.badge_displayed then
            return
        end
        if remaining <= 0 then
            fallback_show()
            return
        end
        remaining = remaining - 1
        local ok, request = pcall(mp.command_native_async, {
            name = 'screenshot-raw', flags = 'video', format = 'bgr0',
        }, function(success, frame)
            state.bar_request = nil
            if file_generation ~= state.file_generation or not state.loaded
                or state.badge_displayed then
                return
            end
            if success then
                local insets, _, coverage, matched = logo_bounds.detect(
                    frame, o.encoded_bar_threshold, o.encoded_bar_min_coverage
                )
                -- 出现可信结果（黑边，或内容画面且确认无黑边）→ 一次性显示并冻结
                local displayable = insets ~= nil or (coverage or 0) >= 0.28
                if displayable then
                    state.content_insets = insets
                    state.content_insets_matched = type(insets) == 'table' and matched == true or nil
                    if type(insets) == 'table' then
                        msg.debug(string.format(
                            'encoded bars confirmed after sparse opening: left=%.4f top=%.4f right=%.4f bottom=%.4f',
                            tonumber(insets.left) or 0,
                            tonumber(insets.top) or 0,
                            tonumber(insets.right) or 0,
                            tonumber(insets.bottom) or 0
                        ))
                    end
                    state.badge_displayed = true
                    schedule_detection('sparse-resolved', tonumber(o.delay) or 0.45)
                    return
                end
            end
            -- 次数用尽仍未等到可信内容：兜底显示；否则继续复检
            if remaining > 0 then
                schedule('bar-followup', interval, request_sample)
            else
                fallback_show()
            end
        end)
        if ok then
            state.bar_request = request
        elseif remaining > 0 then
            schedule('bar-followup', interval, request_sample)
        else
            fallback_show()
        end
    end

    schedule(
        'bar-followup',
        clamp(tonumber(o.encoded_bar_followup_delay) or 2.5, 0.5, 8.0),
        request_sample
    )
end


-- ffmpeg 可执行文件探测（PATH + 常见安装路径），结果缓存。
local ffmpeg_path = nil
local function find_ffmpeg()
    if ffmpeg_path ~= nil then return ffmpeg_path end
    local names = { 'ffmpeg.exe', 'ffmpeg' }
    local candidates = {}
    -- 优先随包自带的检测专用 ffmpeg：mpv 根目录 ffmpeg/ffmpeg.exe
    -- （01 Base 随包分发，解压即用，不依赖 PATH 或系统安装）。
    -- 本脚本位于 portable_config/scripts/，向上两级即 mpv 根目录。
    -- 用脚本自身绝对路径定位 mpv 根目录（mp.get_script_directory 在此构建可能为空）。
    -- 本脚本位于 portable_config/scripts/，剥掉该尾部即 mpv 根目录。
    local source = debug.getinfo(1, 'S').source:gsub('^@', '')
    if source ~= '' then
        local script_dir = select(1, utils.split_path(source))
        local mpv_root = (script_dir:gsub('[/\\]$', ''))
            :gsub('[/\\][Pp]ortable_config[/\\][Ss]cripts$', '')
        candidates[#candidates + 1] = join_path(join_path(mpv_root, 'ffmpeg'), 'ffmpeg.exe')
        candidates[#candidates + 1] = join_path(join_path(mpv_root, 'tools'), 'ffmpeg')
        candidates[#candidates + 1] = join_path(mpv_root, 'ffmpeg')
    end
    for dir in (os.getenv('PATH') or ''):gmatch('[^;]+') do
        for _, name in ipairs(names) do
            candidates[#candidates + 1] = join_path(dir, name)
        end
    end
    for _, extra in ipairs({
        'C:\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
    }) do
        candidates[#candidates + 1] = extra
    end
    for _, candidate in ipairs(candidates) do
        local handle = io.open(candidate, 'r')
        if handle then
            handle:close()
            ffmpeg_path = candidate
            return candidate
        end
    end
    ffmpeg_path = false
    return false
end

-- 后瞻检测用的首窗随机采样：在指定时间窗取多个偏移，随后由第二确认窗
-- 处理“全幅片头先于正片黑边出现”的歧义。
local random_seeded = false
-- 在 [min_first, window] 秒窗口内随机采样 count 个偏移：
--   第一处落在 [min_first, min_first+1]；其余在第一处之后，任意两处间隔 >= gap 且不超窗口。
local function random_lookahead_offsets(window, count, gap, min_first)
    local result = {}
    window = clamp(math.floor(tonumber(window) or 0), 0, 120)
    count = clamp(math.floor(tonumber(count) or 3), 1, 6)
    gap = clamp(math.floor(tonumber(gap) or 2), 0, math.max(1, window))
    min_first = clamp(math.floor(tonumber(min_first) or 0), 0, math.max(0, window - 1))
    if window <= 0 then return result end
    if not random_seeded then
        math.randomseed(math.floor(os.time() + mp.get_time() * 1000))
        random_seeded = true
    end

    -- 第一处落在 [min_first, min_first+1]
    local first = min_first + math.random()
    result[1] = first

    -- 其余 count-1 处：first 之后，间隔 >= gap，且 <= window
    local remaining = count - 1
    if remaining > 0 then
        local tail = window - first - gap * remaining
        if tail < 0 then
            -- 放不下：从 first 起按最小间隔铺开，超出窗口截断
            for i = 2, count do result[i] = math.min(window, first + (i - 1) * gap) end
        else
            local points = {}
            for i = 1, remaining do points[i] = math.random() * tail end
            table.sort(points)
            for i = 1, remaining do
                result[i + 1] = first + i * gap + points[i]
            end
        end
    end

    table.sort(result)
    return result
end

-- 在 [start_time, end_time] 内分层随机采样：每个等分时间段取一处，避免普通随机
-- 点全挤在片头同一段转场。采样限制在各段中部 60%，相邻点天然保持一定距离。
local function stratified_lookahead_offsets(start_time, end_time, count)
    local result = {}
    start_time = math.max(0, tonumber(start_time) or 0)
    end_time = math.max(start_time, tonumber(end_time) or start_time)
    count = clamp(math.floor(tonumber(count) or 3), 1, 6)
    local span = end_time - start_time
    if span < 0.5 then return result end
    if not random_seeded then
        math.randomseed(math.floor(os.time() + mp.get_time() * 1000))
        random_seeded = true
    end
    local segment = span / count
    for index = 0, count - 1 do
        local segment_start = start_time + index * segment
        result[#result + 1] = segment_start + segment * (0.20 + math.random() * 0.60)
    end
    return result
end

-- 后瞻检测：起播黑屏/稀疏画面时，并行解码「当前时间 + 各偏移」处的一帧
-- （640×360 BGR0，flags=neighbor 不做插值，黑边保持纯黑，避免缩小混叠漏掉小黑边），
-- 复用黑边检测。首窗与后续确认窗交错串行采样：先看 3~4 秒，再立即看确认窗
-- 前段，避免必须耗尽三个近端黑屏样本后才寻找正片。任一可信黑边立即采用；
-- 确认窗仍无黑边才确认右上角；全部不可信则回退常规复检。
local function start_bar_lookahead(file_generation)
    -- 后瞻仅两种后瞻模式启用；杳知视觉方案与不检测模式不依赖 ffmpeg
    if o.mode ~= 'current' and o.mode ~= 'parallel' then return false end
    local offsets = random_lookahead_offsets(
        o.encoded_bar_lookahead, o.encoded_bar_lookahead_samples,
        o.encoded_bar_lookahead_gap, o.encoded_bar_lookahead_min
    )
    if #offsets == 0 then return false end
    if state.badge_displayed or state.lookahead_busy then return false end
    local ffmpeg = find_ffmpeg()
    if not ffmpeg then
        msg.debug('bar lookahead disabled: ffmpeg not found')
        return false
    end
    local path = mp.get_property('path', '')
    if not path or path == '' then return false end

    state.lookahead_busy = true
    local now = math.max(0, tonumber(mp.get_property_number('time-pos', 0)) or 0)
    local tmp_dir = os.getenv('TEMP') or os.getenv('TMP') or '/tmp'
    local stamp = tostring(mp.get_time())
    local initial_results = {}
    local confirm_results = {}
    local tmp_files = {}  -- 所有临时文件，结算后统一清理
    local settled = false

    local function pick_bars(results)
        for _, r in ipairs(results) do
            if r and r.insets and r.matched then return r end
        end
        for _, r in ipairs(results) do
            if r and r.insets then return r end
        end
    end

    local function pick_no_bars(results, minimum_count)
        local first
        local count = 0
        for _, r in ipairs(results) do
            if r and not r.insets and (r.coverage or 0) >= 0.28 then
                first = first or r
                count = count + 1
            end
        end
        return count >= (minimum_count or 1) and first or nil
    end

    local function settle(pick)
        if settled then return end
        settled = true
        cancel_lookahead_requests()
        for _, f in ipairs(tmp_files) do pcall(os.remove, f) end
        if file_generation ~= state.file_generation or not state.loaded
            or state.badge_displayed then
            return
        end
        if pick then
            local insets = pick.insets
            state.content_insets = insets
            state.content_insets_matched = type(insets) == 'table' and pick.matched == true or nil
            state.badge_displayed = true
            msg.debug(string.format(
                'bar lookahead resolved (t+%.1fs): left=%.4f top=%.4f right=%.4f bottom=%.4f cov=%.3f',
                pick.offset or 0,
                type(insets) == 'table' and (tonumber(insets.left) or 0) or 0,
                type(insets) == 'table' and (tonumber(insets.top) or 0) or 0,
                type(insets) == 'table' and (tonumber(insets.right) or 0) or 0,
                type(insets) == 'table' and (tonumber(insets.bottom) or 0) or 0,
                pick.coverage or 0
            ))
            schedule_detection('lookahead', tonumber(o.delay) or 0.45)
            return
        end
        -- 所有偏移都不可信（黑屏/稀疏）：回退常规复检
        start_ambiguous_bar_followup(file_generation)
    end

    local first_window_end = tonumber(o.encoded_bar_lookahead) or 10
    local confirm_start = math.max(
        first_window_end, tonumber(o.encoded_bar_confirm_min) or 30
    )
    local confirm_end = tonumber(o.encoded_bar_confirm_lookahead) or 75
    local duration = tonumber(mp.get_property_number('duration', 0)) or 0
    if duration > 0 then
        confirm_end = math.min(confirm_end, math.max(0, duration - now - 0.1))
    end
    local confirm_offsets = stratified_lookahead_offsets(
        confirm_start, confirm_end, o.encoded_bar_confirm_samples
    )

    -- 近端与远端交错：I1,C1,I2,C2,I3,C3。复杂黑屏片头通常在 C1
    -- 就能命中正片黑边，同时仍保留近端样本对短片头的快速响应。
    local plan = {}
    local plan_size = math.max(#offsets, #confirm_offsets)
    for index = 1, plan_size do
        if offsets[index] then
            plan[#plan + 1] = {offset = offsets[index], results = initial_results, index = index}
        end
        if confirm_offsets[index] then
            plan[#plan + 1] = {offset = confirm_offsets[index], results = confirm_results, index = index}
        end
    end
    if #confirm_offsets > 0 then
        msg.debug(string.format(
            'bar lookahead: interleaving %.1f-%.1fs confirmation window (%d+%d samples)',
            confirm_start, confirm_end, #offsets, #confirm_offsets
        ))
    end

    local function launch_probe(item, serial, completed)
            if settled then return end
            local offset = item.offset
            local target = now + offset
            local tmp_file = join_path(tmp_dir, string.format(
                'vanta-la-%s-%d.raw', stamp, serial
            ))
            tmp_files[#tmp_files + 1] = tmp_file
            -- args[0] 必须是可执行文件路径（mpv subprocess 按此启动进程）
            local args = {
                ffmpeg,
                '-hide_banner', '-loglevel', 'error',
                '-threads', tostring(clamp(
                    math.floor(tonumber(o.encoded_bar_ffmpeg_threads) or 4), 0, 16
                )),
                '-ss', string.format('%.3f', target),
                '-i', path,
                '-map', '0:v:0',
                '-frames:v', '1',
                '-vf', 'scale=640:360:flags=neighbor',
                '-f', 'rawvideo',
                '-pix_fmt', 'bgr0',
                '-y', tmp_file,
            }
            local request
            local ok
            ok, request = pcall(mp.command_native_async, {
                name = 'subprocess',
                args = args,
                capture_stderr = true,
            }, function(success, result)
                if request then state.lookahead_requests[request] = nil end
                if settled then
                    pcall(os.remove, tmp_file)
                    return
                end
                local content = nil
                if success and result and result.status == 0 then
                    content = read_text_file(tmp_file)
                end
                if content and #content == 640 * 360 * 4 then
                    local frame = {
                        format = 'bgr0',
                        w = 640,
                        h = 360,
                        stride = 640 * 4,
                        data = content,
                    }
                    local insets, _, coverage, matched = logo_bounds.detect(
                        frame, o.encoded_bar_threshold, o.encoded_bar_min_coverage
                    )
                    item.results[item.index] = {
                        offset = offset,
                        insets = insets,
                        coverage = coverage or 0,
                        matched = matched == true,
                    }
                else
                    item.results[item.index] = {
                        offset = offset, insets = nil, coverage = 0, matched = false,
                    }
                end
                local probe = item.results[item.index]
                msg.debug(string.format(
                    'bar lookahead sample (t+%.1fs): %s cov=%.3f matched=%s',
                    offset,
                    probe.insets and 'bars' or ((probe.coverage or 0) >= 0.28 and 'no-bars' or 'uncertain'),
                    probe.coverage or 0,
                    tostring(probe.matched == true)
                ))
                -- 可信黑边的置信度高于无黑边，命中后无需继续剩余采样。
                completed(probe)
            end)
            if ok and request then
                state.lookahead_requests[request] = true
            else
                item.results[item.index] = {
                    offset = offset, insets = nil, coverage = 0, matched = false,
                }
                completed(item.results[item.index])
            end
    end

    local function finish_plan()
        if settled then return end
        local bars = pick_bars(initial_results) or pick_bars(confirm_results)
        if bars then settle(bars) return end
        if #confirm_offsets == 0 then
            settle(pick_no_bars(initial_results))
            return
        end
        -- “有黑边”任一可信样本即可成立；“无黑边”至少需要两帧远端共识。
        settle(pick_no_bars(confirm_results, 2))
    end

    local function pick_early_no_bars()
        -- 一帧近端亮画面 + 一帧深后瞻亮画面即可确认无黑边；深后瞻已跨过
        -- 常见发行方片头。若任一帧有黑边，外层仍优先立即采用黑边。
        return pick_no_bars(initial_results, 1) and pick_no_bars(confirm_results, 1)
            and pick_no_bars(confirm_results, 1) or nil
    end

    local function get_fast_probe()
        local legacy = tonumber(o.encoded_bar_parallel_fast_probe) or -1
        local fast_probe = clamp(
            legacy >= 0 and legacy or (tonumber(o.encoded_bar_fast_probe) or 40),
            confirm_start, confirm_end
        )
        if duration > 0 then
            fast_probe = math.min(fast_probe, math.max(0, duration - now - 0.1))
        end
        return fast_probe > first_window_end and fast_probe or confirm_offsets[1]
    end

    local function run_common_plan(concurrency)
        -- 单路/双路共用完全相同的采样顺序、判定门槛与回退；唯一差异是
        -- 困难场景每批启动 1 个还是 2 个 ffmpeg。
        local first_deep = get_fast_probe()
        local function evaluate_results()
            local bars = pick_bars(initial_results) or pick_bars(confirm_results)
            if bars then return bars end
            return pick_early_no_bars() or pick_no_bars(confirm_results, 2)
        end

        local function run_fallback()
            local next_index = 1
            local serial = 10
            local function run_batch()
                if settled then return end
                local batch = {}
                for _ = 1, concurrency do
                    if plan[next_index] then
                        batch[#batch + 1] = plan[next_index]
                        next_index = next_index + 1
                    end
                end
                if #batch == 0 then finish_plan() return end
                local pending = #batch
                local function on_probe(probe)
                    if settled then return end
                    if probe.insets then settle(probe) return end
                    pending = pending - 1
                    local decision = evaluate_results()
                    if decision then
                        settle(decision)
                    elseif pending <= 0 then
                        run_batch()
                    end
                end
                for _, item in ipairs(batch) do
                    serial = serial + 1
                    launch_probe(item, serial, on_probe)
                end
            end
            run_batch()
        end

        if not first_deep then run_fallback() return end
        launch_probe({
            offset = first_deep, results = confirm_results, index = 1,
        }, 1, function(probe)
            if probe.insets or (probe.coverage or 0) >= 0.28 then
                settle(probe)
            else
                run_fallback()
            end
        end)
    end

    run_common_plan(o.mode == 'parallel' and 2 or 1)
    return true
end

local function prepare_display_after_frame(reason)
    local file_generation = state.file_generation
    local function continue_detection(insets, suffix, followup, matched, show_now)
        if file_generation ~= state.file_generation or not state.loaded then return end
        local yz_mode = o.mode == 'yaozhi'
        -- 锚点：两种后瞻模式显示后冻结；yaozhi 模式始终允许更新（可重定位）
        if yz_mode or not state.badge_displayed then
            state.content_insets = insets
            state.content_insets_matched = type(insets) == 'table' and matched == true or nil
            if type(insets) == 'table' then
                msg.debug(string.format(
                    'encoded bars: left=%.4f top=%.4f right=%.4f bottom=%.4f',
                    tonumber(insets.left) or 0,
                    tonumber(insets.top) or 0,
                    tonumber(insets.right) or 0,
                    tonumber(insets.bottom) or 0
                ))
            end
        end
        state.bar_request = nil
        stop_timer('bar-detect-timeout')
        if yz_mode then
            -- 杳知视觉方案：无论有无黑边都显示（默认位或黑边锚点），复检另行重定位
            state.badge_displayed = true
            schedule_detection(reason .. (suffix or ''), tonumber(o.delay) or 0.45)
        elseif not state.badge_displayed and show_now then
            -- 两种后瞻模式：仅在未显示且本次结果可展示时显示。
            state.badge_displayed = true
            cancel_lookahead_requests()
            schedule_detection(reason .. (suffix or ''), tonumber(o.delay) or 0.45)
        end
        if followup then
            if start_bar_lookahead(file_generation) then
                return
            end
            -- 双路模式可能已在当前帧检测前预启动后瞻，不重复进入视觉复检。
            if state.lookahead_busy then return end
            -- 杳知视觉方案用可重定位复检，current 用冻结+兜底复检
            if yz_mode then
                start_yaozhi_bar_followup(file_generation)
            else
                start_ambiguous_bar_followup(file_generation)
            end
        end
    end

    if not has_real_video_track() or not o.anchor_to_video or not effective_detect_encoded_bars() then
        continue_detection(nil, '', false, false, true)
        return
    end

    -- 两种后瞻模式都在首帧稳定后立即预启动固定深探针，不再等待三次
    -- screenshot-raw 判断片头是否稀疏。困难场景的补测并发度仍由模式决定。
    if o.mode == 'current' or o.mode == 'parallel' then
        start_bar_lookahead(file_generation)
    end

    schedule('bar-detect', math.max(0, tonumber(o.encoded_bar_delay) or 0.18), function()
        if file_generation ~= state.file_generation or not state.loaded then return end
        local completed = false
        local probes = {}
        local probes_matched = {}
        local matched_count = 0
        local max_coverage = 0
        local sample_count = clamp(math.floor(tonumber(o.encoded_bar_samples) or 3), 1, 5)
        local sample_interval = clamp(tonumber(o.encoded_bar_sample_interval) or 0.22, 0.05, 0.75)

        -- 画幅匹配优先（current）：命中白名单的样本合并；白名单外退化为纯视觉兜底。
        -- 杳知视觉方案（yaozhi）：全部样本合并，不做画幅白名单。
        local function merge_probes()
            if o.mode ~= 'yaozhi' and matched_count > 0 then
                local matched_probes = {}
                for index, probe in ipairs(probes) do
                    if probes_matched[index] then matched_probes[#matched_probes + 1] = probe end
                end
                return logo_bounds.merge(matched_probes), true
            end
            return logo_bounds.merge(probes), false
        end

        local function finish(insets, suffix, used_matched)
            if completed then return end
            completed = true
            local yz_mode = o.mode == 'yaozhi'
            -- 可展示：检测到黑边，或画面内容充分（覆盖率达标）
            local displayable = insets ~= nil or max_coverage >= 0.28
            -- 杳知视觉方案：仅"无黑边且覆盖率低"时复检；始终显示（默认位/黑边锚点）
            -- current：黑屏/稀疏开场（无黑边且覆盖率低）暂不显示，交给复检
            local followup = yz_mode
                and (insets == nil and max_coverage < 0.28)
                or (not displayable)
            local wait_for_lookahead = (o.mode == 'current' or o.mode == 'parallel')
                and state.lookahead_busy and insets == nil
            continue_detection(
                insets, suffix, followup, used_matched,
                yz_mode or (displayable and not wait_for_lookahead)
            )
        end
        schedule('bar-detect-timeout', 1.4 + sample_count * sample_interval, function()
            local insets, used_matched = merge_probes()
            finish(insets, insets and '-encoded-bars-timeout' or '-bar-timeout', used_matched)
        end)

        local function request_sample(index)
            if completed or file_generation ~= state.file_generation or not state.loaded then return end
            local ok, request = pcall(mp.command_native_async, {
                name = 'screenshot-raw', flags = 'video', format = 'bgr0',
            }, function(success, frame)
                if completed then return end
                if success then
                    local insets, _, coverage, matched = logo_bounds.detect(
                        frame,
                        o.encoded_bar_threshold,
                        o.mode == 'yaozhi' and 0 or o.encoded_bar_min_coverage
                    )
                    max_coverage = math.max(max_coverage, tonumber(coverage) or 0)
                    if insets then
                        probes[#probes + 1] = insets
                        probes_matched[#probes_matched + 1] = matched == true
                        if matched == true then matched_count = matched_count + 1 end
                    end
                end
                if index >= sample_count then
                    local insets, used_matched = merge_probes()
                    finish(insets, insets and '-encoded-bars' or '-frame-bounds', used_matched)
                else
                    schedule('bar-detect-sample', sample_interval, function()
                        request_sample(index + 1)
                    end)
                end
            end)
            if not ok then
                if index >= sample_count then
                    local insets, used_matched = merge_probes()
                    finish(insets, insets and '-encoded-bars' or '-bar-unavailable', used_matched)
                else
                    schedule('bar-detect-sample', sample_interval, function()
                        request_sample(index + 1)
                    end)
                end
            else
                state.bar_request = request
            end
        end
        request_sample(1)
    end)
end


local function mark_frame_ready(reason)
    if not state.loaded or state.frame_ready then return end
    state.frame_ready = true
    state.waiting_for_frame = false
    stop_timer('frame-wait')
    if o.enabled and manifest then prepare_display_after_frame(reason) end
end


local function on_playback_restart()
    -- The first playback-restart arrives only after mpv has a presentable
    -- video frame. Waiting for it prevents the badges from appearing against
    -- the empty window and then jumping when letterbox/pillarbox bounds land.
    if state.loaded and not state.frame_ready then
        mark_frame_ready('first-frame')
    end
end


local function on_file_loaded()
    state.file_generation = state.file_generation + 1
    state.loaded = true
    state.frame_ready = false
    state.waiting_for_frame = true
    state.content_insets = nil
    state.content_insets_matched = nil
    state.badge_displayed = false
    cancel_lookahead_requests()
    state.last_aid = mp.get_property_native('aid')
    state.overlay_error_logged = false
    cancel_display(true)
    stop_timer('frame-wait')
    stop_timer('bar-followup')

    if not has_real_video_track() then
        if o.require_video then
            state.waiting_for_frame = false
            msg.debug('startup logo skipped: a real video track is required')
            return
        end

        -- Audio-only playback has no video frame or video-out geometry to wait
        -- for. Wait briefly for the window OSD instead, then use the full OSD
        -- bounds and skip video-only encoded-bar probing.
        local file_generation = state.file_generation
        local function wait_for_audio_osd(attempt)
            schedule('frame-wait', attempt == 1 and 0.05 or 0.10, function()
                if file_generation ~= state.file_generation
                    or not state.loaded or state.frame_ready then
                    return
                end
                local width, height = get_osd_size()
                if width and height then
                    mark_frame_ready('audio-only-osd')
                elseif attempt < 15 then
                    wait_for_audio_osd(attempt + 1)
                else
                    state.waiting_for_frame = false
                    msg.debug('startup logo skipped: no OSD geometry for audio-only playback')
                end
            end)
        end
        wait_for_audio_osd(1)
        return
    end

    schedule('frame-wait', math.max(0.5, tonumber(o.frame_wait_timeout) or 5.0), function()
        if not state.loaded or state.frame_ready then return end
        if has_video_geometry() then
            mark_frame_ready('video-geometry-timeout')
        else
            state.waiting_for_frame = false
            msg.debug('startup logo skipped: no stable video frame or geometry')
        end
    end)
end


local function on_end_file()
    state.file_generation = state.file_generation + 1
    state.loaded = false
    state.frame_ready = false
    state.waiting_for_frame = false
    state.content_insets = nil
    state.content_insets_matched = nil
    state.badge_displayed = false
    state.last_aid = nil
    stop_timer('frame-wait')
    stop_timer('bar-detect')
    stop_timer('bar-detect-timeout')
    stop_timer('bar-followup')
    if state.bar_request then
        pcall(mp.abort_async_command, state.bar_request)
        state.bar_request = nil
    end
    cancel_lookahead_requests()
    stop_timer('retry')
    stop_timer('audio-change')
    cancel_display(true)
end


local function on_audio_track_change(_, value)
    if not state.loaded then
        state.last_aid = value
        return
    end
    if value == state.last_aid then return end
    state.last_aid = value
    if not state.frame_ready then return end
    if o.enabled and o.show_on_audio_change then
        schedule('audio-change', 0.18, function()
            if not state.loaded then return end
            local video, audio = detect_pair()
            if video or audio then
                show_pair(video, audio, 'audio-track-change')
            else
                cancel_display(true)
            end
        end)
    end
end


local function preview_message(video, audio)
    local function normalize(value)
        value = tostring(value or ''):lower()
        if value == '' or value == 'none' or value == 'no' then return nil end
        return value
    end
    video = normalize(video)
    audio = normalize(audio)
    if not show_pair(video, audio, 'manual-preview') then
        mp.osd_message('起播 Logo 预览参数无效', 2)
    end
end


local function toggle_message()
    o.enabled = not o.enabled
    persist_option('enabled', o.enabled and 'yes' or 'no')
    if not o.enabled then
        cancel_display(true)
    elseif state.loaded then
        if state.frame_ready then
            schedule_detection('runtime-toggle', 0)
        else
            state.waiting_for_frame = true
        end
    end
    publish_state()
    mp.osd_message('起播格式 Logo：' .. (o.enabled and '开启' or '关闭'), 2)
end


local function set_style_message(value)
    local style = normalize_style(value)
    o.style = style
    persist_option('style', style)
    if state.visible and state.opacity_index > 0 then
        render_level(state.opacity_index)
    end
    publish_state()
    mp.osd_message(
        '起播格式图标：' .. (style == 'white' and '透明白图标' or '彩色徽章'),
        2
    )
end


local function set_mode_message(value)
    local mode = normalize_mode(value)
    if mode == o.mode then return end
    o.mode = mode
    persist_option('mode', mode)
    -- 切换模式后重新走一遍黑边检测与显示（prepare 会按新 mode 决定检测方式）
    cancel_display(true)
    state.badge_displayed = false
    cancel_lookahead_requests()
    if state.loaded and state.frame_ready then
        prepare_display_after_frame('mode-change')
    else
        state.waiting_for_frame = true
    end
    publish_state()
    local label = mode == 'current' and '后瞻方案·单路检测（实验性）'
        or (mode == 'parallel' and '后瞻方案·双路检测（实验性）')
        or (mode == 'yaozhi' and '杳知视觉方案' or '不检测（右上角直接显示）')
    mp.osd_message('起播 Logo 检测模式：' .. label, 2)
end


if overlay_base < 0 or overlay_base > 61 then
    msg.warn('overlay_id must leave room for three IDs; falling back to 50')
    overlay_base = 50
end
if overlay_base <= 42 and overlay_base + 2 >= 42 then
    msg.warn('overlay_id range collides with thumbfast overlay 42')
end

if not load_assets() then
    o.enabled = false
end

mp.register_event('file-loaded', on_file_loaded)
mp.register_event('playback-restart', on_playback_restart)
mp.register_event('end-file', on_end_file)
mp.observe_property('aid', 'native', on_audio_track_change)
mp.observe_property('osd-dimensions', 'native', function()
    if state.visible and state.opacity_index > 0 then
        render_level(state.opacity_index)
    end
end)

mp.register_script_message('startup-format-logos-show', function()
    if state.loaded then schedule_detection('manual-detect', 0) end
end)
mp.register_script_message('startup-format-logos-preview', preview_message)
mp.register_script_message('startup-format-logos-hide', function() cancel_display(true) end)
mp.register_script_message('startup-format-logos-toggle', toggle_message)
mp.register_script_message('startup-format-logos-set-style', set_style_message)
mp.register_script_message('startup-format-logos-set-mode', set_mode_message)

publish_state()
msg.info('script loaded')
