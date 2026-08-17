-- 基于 mpv 官方属性的媒体格式检测，供界面元素复用。

local M = {}

local function lower(value)
    return tostring(value or ''):lower()
end

local function trim(value)
    return tostring(value or ''):match('^%s*(.-)%s*$')
end

local function compact(value)
    return lower(value):gsub('%+', 'plus'):gsub('[^%w]', '')
end

local function contains(text, needle)
    return tostring(text or ''):find(needle, 1, true) ~= nil
end

local function positive(value)
    local number = tonumber(value)
    return number ~= nil and number > 0
end

local CODEC_FIELDS = {
    'codec', 'demux-codec', 'format', 'codec-desc', 'decoder-desc',
    'codec-profile',
}

local STRUCTURED_METADATA_KEYS = {
    dolbyvisionprofile = true,
    dolbyvisionlevel = true,
    doviprofile = true,
    dovilevel = true,
    hdr10plus = true,
    hdrvivid = true,
    scenemaxr = true,
    scenemaxg = true,
    scenemaxb = true,
    maxcll = true,
    maxfall = true,
    minluma = true,
    maxluma = true,
    masteringdisplay = true,
    contentlightlevel = true,
    transfer = true,
    gamma = true,
    joc = true,
    dtsx = true,
    dtshdmaster = true,
    dtshdhighresolution = true,
}

-- 仅使用 mpv 当前轨道的真实 codec 字段构造主识别上下文。
-- 文件名和媒体标题不具备格式判定权；轨道标题由具体识别函数受限兜底。
local function build_codec_context(codec, track)
    local parts = {}
    if trim(codec) ~= '' then parts[#parts + 1] = tostring(codec) end
    if type(track) == 'table' then
        for _, field in ipairs(CODEC_FIELDS) do
            if trim(track[field]) ~= '' then
                parts[#parts + 1] = tostring(track[field])
            end
        end
        if type(track.metadata) == 'table' then
            for key, value in pairs(track.metadata) do
                if STRUCTURED_METADATA_KEYS[compact(key)] and trim(value) ~= '' then
                    parts[#parts + 1] = tostring(key)
                    parts[#parts + 1] = tostring(value)
                end
            end
        end
    end
    local raw = lower(table.concat(parts, ' '))
    return raw, compact(raw)
end

local function raw_codec_label(value)
    local text = trim(value)
    if text == '' then return nil end
    local token = text:match('^([^%s%(%)]+)') or text
    local normalized = token:lower()
    if normalized == 'unknown' or normalized == 'unrecognized'
        or normalized == 'none' or normalized == 'no' then
        return nil
    end
    return token:gsub('_', '-'):upper()
end

local function structured_metadata_value(track, wanted)
    if type(track) ~= 'table' or type(track.metadata) ~= 'table' then return nil end
    for key, value in pairs(track.metadata) do
        if compact(key) == wanted then return value end
    end
    return nil
end

local function track_title_context(track)
    local raw = type(track) == 'table' and lower(track.title) or ''
    return raw, compact(raw)
end

local function read_selected_track(kind)
    local selector = kind == 'audio' and 'aid' or (kind == 'video' and 'vid' or nil)
    if selector then
        local selected_id = mp.get_property_native(selector)
        if selected_id == false or tostring(selected_id or '') == 'no' then return {} end
    end

    local current = mp.get_property_native('current-tracks/' .. kind, {})
    if type(current) == 'table' and current.type == kind then return current end

    local selected
    local count = 0
    local tracks = mp.get_property_native('track-list', {})
    if type(tracks) == 'table' then
        for _, track in ipairs(tracks) do
            if type(track) == 'table' and track.type == kind then
                count = count + 1
                if track.selected == true then return track end
                selected = selected or track
            end
        end
    end
    return count == 1 and selected or {}
end

local function read_snapshot()
    return {
        video_params = mp.get_property_native('video-params', {}),
        video_frame_info = mp.get_property_native('video-frame-info', {}),
        audio_params = mp.get_property_native('audio-params', {}),
        video_track = read_selected_track('video'),
        audio_track = read_selected_track('audio'),
        video_codec = mp.get_property('video-codec', ''),
        audio_codec = mp.get_property('audio-codec', ''),
        hwdec = mp.get_property('hwdec-current', ''),
        fps = mp.get_property_number('estimated-vf-fps', 0),
        container_fps = mp.get_property_number('container-fps', 0),
        audio_channel_count = mp.get_property_number('audio-params/channel-count', 0),
        audio_channels = mp.get_property_number('audio-channels', 0),
    }
end

local function dolby_vision_label(snapshot, context)
    local track = snapshot.video_track or {}
    local params = snapshot.video_params or {}
    local profile = tonumber(track['dolby-vision-profile'])
        or tonumber(params['dolby-vision-profile'])
        or tonumber(structured_metadata_value(track, 'dolbyvisionprofile'))
        or tonumber(structured_metadata_value(track, 'doviprofile'))
    local detected = positive(profile)
        or track['dolby-vision-level'] ~= nil
        or params['dolby-vision-level'] ~= nil
        or structured_metadata_value(track, 'dolbyvisionlevel') ~= nil
        or structured_metadata_value(track, 'dovilevel') ~= nil
        or contains(context, 'dolbyvision')
        or contains(context, 'dovi')
        or contains(context, 'dvhe')
        or contains(context, 'dvh1')
    if not detected then return nil end
    return profile and profile > 0 and ('Dolby Vision P' .. tostring(profile)) or 'Dolby Vision'
end

local function has_hdr10_plus(track, params, context)
    return track.hdr10plus == true
        or params.hdr10plus == true
        or positive(track['scene-max-r'])
        or positive(track['scene-max-g'])
        or positive(track['scene-max-b'])
        or positive(params['scene-max-r'])
        or positive(params['scene-max-g'])
        or positive(params['scene-max-b'])
        or contains(context, 'scenemax')
        or contains(context, 'hdr10plus')
        or contains(context, 'hdr10p')
end

local function has_hdr10_static_metadata(track, params, context)
    return positive(track['max-cll'])
        or positive(track['max-fall'])
        or positive(track['min-luma'])
        or positive(track['max-luma'])
        or positive(params['max-cll'])
        or positive(params['max-fall'])
        or positive(params['min-luma'])
        or positive(params['max-luma'])
        or contains(context, 'maxcll')
        or contains(context, 'maxfall')
        or contains(context, 'minluma')
        or contains(context, 'maxluma')
        or contains(context, 'hdr10')
end

local SDR_GAMMAS = {
    ['bt.1886'] = true,
    ['bt709'] = true,
    ['bt.709'] = true,
    ['srgb'] = true,
    ['linear'] = true,
    ['gamma1.8'] = true,
    ['gamma2.0'] = true,
    ['gamma2.2'] = true,
    ['gamma2.4'] = true,
    ['gamma2.6'] = true,
    ['gamma2.8'] = true,
    ['prophoto'] = true,
    ['st428'] = true,
}

local function detect_dynamic_range_title(track)
    local raw, context = track_title_context(track)
    if context == '' then return nil end
    if contains(context, 'dolbyvision') or contains(context, 'dovi')
        or contains(context, 'dvhe') or contains(context, 'dvh1') then
        local profile = raw:match('dolby%s*vision%s*p?(%d+)')
            or raw:match('dovi%s*p?(%d+)')
        return profile and ('Dolby Vision P' .. profile) or 'Dolby Vision'
    end
    if contains(context, 'hdrvivid') or contains(context, 'cuvahdr') then
        return 'HDR Vivid'
    end
    if contains(context, 'hdr10plus') or contains(context, 'hdr10p') then
        return 'HDR10+'
    end
    if contains(context, 'hlg') then return 'HLG' end
    if contains(context, 'hdr10') then return 'HDR10' end
    if contains(context, 'hdr') then return 'HDR' end
    if contains(context, 'sdr') then return 'SDR' end
    return nil
end

local function detect_dynamic_range(snapshot, context)
    local track = type(snapshot.video_track) == 'table' and snapshot.video_track or {}
    local params = type(snapshot.video_params) == 'table' and snapshot.video_params or {}
    local dv = dolby_vision_label(snapshot, context)
    if dv then return dv end

    -- HDR Vivid（CUV-HDR）优先于普通 PQ/HLG 判断
    if params['hdr-vivid'] == true
        or track['hdr-vivid'] == true
        or contains(context, 'hdrvivid')
        or contains(context, 'cuvahdr') then
        return 'HDR Vivid'
    end

    local gamma = lower(params.gamma or params.transfer or track.gamma or track.transfer)
    local pq = gamma == 'pq' or gamma == 'smpte2084'
    if pq and has_hdr10_plus(track, params, context) then return 'HDR10+' end
    if gamma == 'hlg' or gamma == 'arib-std-b67' or gamma == 'aribstdb67'
        or contains(context, 'hlg') then
        return 'HLG'
    end
    if pq then
        return has_hdr10_static_metadata(track, params, context) and 'HDR10' or 'HDR'
    end
    if gamma == '' and has_hdr10_plus(track, params, context) then return 'HDR10+' end
    if gamma == '' and has_hdr10_static_metadata(track, params, context) then return 'HDR10' end
    if SDR_GAMMAS[gamma] then return 'SDR' end
    return detect_dynamic_range_title(track) or '动态范围未知'
end

local VIDEO_CODEC_RULES = {
    {'VVC', {'vvc', 'h266'}},
    {'AVS3', {'avs3'}},
    {'AVS2', {'avs2', 'davs2'}},
    {'AVS+', {'cavs'}},
    {'HEVC', {'hevc', 'h265', 'x265'}},
    {'EVC', {'evc'}},
    {'AVC', {'h264', 'x264', 'avc1', 'avc'}},
    {'AV1', {'av01', 'libaomav1', 'dav1d', 'av1'}},
    {'VP9', {'vp9'}},
    {'VP8', {'vp8'}},
    {'MPEG-2', {'mpeg2video', 'mpeg2'}},
    {'MPEG-1', {'mpeg1video', 'mpeg1'}},
    {'MS MPEG-4', {'msmpeg4'}},
    {'MPEG-4', {'mpeg4', 'xvid', 'divx'}},
    {'H.263', {'h263'}},
    {'VC-1', {'vc1', 'wmv3'}},
    {'WMV', {'wmv1', 'wmv2'}},
    {'ProRes', {'prores'}},
    {'DNxHD/DNxHR', {'dnxhd', 'dnxhr'}},
    {'CineForm', {'cineform', 'cfhd', 'vc5'}},
    {'FFV1', {'ffv1'}},
    {'HuffYUV', {'huffyuv'}},
    {'Dirac', {'dirac'}},
    {'APV', {'apv'}},
    {'HAP', {'hap'}},
    {'MJPEG', {'mjpeg'}},
    {'Theora', {'theora'}},
    {'JPEG 2000', {'jpeg2000', 'j2k'}},
    {'JPEG XL', {'jpegxl', 'jxl'}},
    {'WebP', {'webp'}},
    {'VP6', {'vp6'}},
    {'RealVideo', {'rv10', 'rv20', 'rv30', 'rv40', 'realvideo'}},
    {'RAW', {'rawvideo'}},
}

local function detect_video_codec_value(value)
    local context = compact(value)
    if context == '' then return '' end
    for _, rule in ipairs(VIDEO_CODEC_RULES) do
        for _, needle in ipairs(rule[2]) do
            if contains(context, needle) then return rule[1] end
        end
    end
    return ''
end

local function video_codec_candidates(snapshot)
    local track = type(snapshot.video_track) == 'table' and snapshot.video_track or {}
    return {
        snapshot.video_codec or '',
        track.codec or '',
        track['demux-codec'] or '',
        track.format or '',
        track['codec-desc'] or '',
        track['decoder-desc'] or '',
    }
end

-- 视频编码以真实轨道/解码器属性为准，轨道标题只在这些属性缺失时兜底。
local function detect_video_codec(snapshot)
    local actual_candidates = video_codec_candidates(snapshot)
    for _, value in ipairs(actual_candidates) do
        local label = detect_video_codec_value(value)
        if label ~= '' then return label end
    end
    for _, value in ipairs(actual_candidates) do
        local label = raw_codec_label(value)
        if label then return label end
    end
    local track = type(snapshot.video_track) == 'table' and snapshot.video_track or {}
    local title_label = detect_video_codec_value(track.title)
    if title_label ~= '' then return title_label end
    return '未知视频格式'
end

local function audio_codec_candidates(snapshot)
    local track = type(snapshot.audio_track) == 'table' and snapshot.audio_track or {}
    return {
        snapshot.audio_codec or '',
        track.codec or '',
        track['demux-codec'] or '',
        track.format or '',
        track['codec-desc'] or '',
        track['decoder-desc'] or '',
    }
end

local function detect_audio_codec_value(raw, context)
    if contains(context, 'dolbyatmos') or contains(context, 'atmos')
        or raw:match('%f[%w]joc%f[%W]') then
        return 'Dolby Atmos'
    end
    if contains(context, 'dtsx') then return 'DTS:X' end
    if contains(context, 'av3a') or contains(context, 'audiovivid')
        or contains(context, 'avs3audio') then
        return 'Audio Vivid'
    end
    if contains(context, 'atrac3plus') or contains(context, 'atrac3p') then return 'ATRAC3plus' end
    if contains(context, 'atrac3') then return 'ATRAC3' end
    if contains(context, 'atrac') then return 'ATRAC' end
    if contains(context, 'dtshdmasteraudio') or contains(context, 'dtshdmaster')
        or contains(context, 'dtshdma') or contains(context, 'dtsma') then
        return 'DTS-HD MA'
    end
    if contains(context, 'dtshdhighresolutionaudio')
        or contains(context, 'dtshdhighresolution')
        or contains(context, 'dtshdhra') or contains(context, 'dtshighres') then
        return 'DTS-HD HRA'
    end
    if contains(context, 'truehd') or contains(context, 'mlpfba') then
        return 'Dolby TrueHD'
    end
    if contains(context, 'eac3') or contains(context, 'dolbydigitalplus')
        or contains(context, 'ddplus') or contains(context, 'ddp') then
        return 'Dolby Digital Plus'
    end
    if contains(context, 'ac3') or contains(context, 'dolbydigital') then
        return 'Dolby Digital'
    end
    if contains(context, 'dca') or contains(context, 'dts')
        or raw:match('%f[%w]dts%f[%W]') then
        return 'DTS'
    end
    if contains(context, 'ac4') then return 'Dolby AC-4' end
    if contains(context, 'dolbye') then return 'Dolby E' end
    if contains(context, 'mpegh') or contains(context, 'mhm1')
        or contains(context, 'mha1') then
        return 'MPEG-H Audio'
    end
    if contains(context, 'heaacv2') or contains(context, 'heaac2')
        or contains(context, 'sbrps') then
        return 'HE-AAC v2'
    end
    if contains(context, 'heaac') or contains(context, 'aacplus')
        or contains(context, 'sbr') then
        return 'HE-AAC'
    end
    if contains(context, 'dabplus') then return 'DAB+' end
    if contains(context, 'amrwb') or contains(context, 'amrwideband') then return 'AMR-WB' end
    if contains(context, 'amrnb') or contains(context, 'amrnarrowband') then return 'AMR-NB' end
    if contains(context, 'amr') then return 'AMR' end
    if contains(context, 'speex') then return 'Speex' end
    if contains(context, 'musepack') or contains(context, 'mpc') then return 'Musepack' end
    if contains(context, 'flac') then return 'FLAC' end
    if contains(context, 'alac') then return 'ALAC' end
    if contains(context, 'wavpack') or contains(context, 'wavpak') then return 'WavPack' end
    if contains(context, 'tak') then return 'TAK' end
    if contains(context, 'tta') then return 'TTA' end
    if contains(context, 'ape') or contains(context, 'monkeysaudio') then return 'APE' end
    if context == 'wma' or contains(context, 'wmav1')
        or contains(context, 'wmav2') or contains(context, 'wmapro')
        or contains(context, 'wmavoice') or contains(context, 'wmalossless')
        or contains(context, 'windowsmediaaudio') then
        return 'WMA'
    end
    if contains(context, 'opus') then return 'Opus' end
    if contains(context, 'vorbis') then return 'Vorbis' end
    if contains(context, 'aac') then return 'AAC' end
    if contains(context, 'mpa1') or contains(context, 'mp1') then return 'MP1' end
    if contains(context, 'mpa2') or contains(context, 'mp2') then return 'MP2' end
    if contains(context, 'mpa3') or contains(context, 'mp3') then return 'MP3' end
    if raw:match('%f[%w]mpa%f[%W]') or raw:match('%f[%w]mpegaudio%f[%W]') then
        return 'MPEG Audio'
    end
    if contains(context, 'adpcm') then return 'ADPCM' end
    if contains(context, 'pcmalaw') or contains(context, 'alaw') then return 'G.711 A-law' end
    if contains(context, 'pcmmulaw') or contains(context, 'mulaw') then return 'G.711 mu-law' end
    if contains(context, 'pcm') or contains(context, 'lpcm') then return 'PCM' end
    if contains(context, 'mlp') then return 'MLP' end
    return nil
end

local function refine_audio_codec_from_title(actual, title)
    if not title then return actual end
    if title == 'Dolby Atmos'
        and (actual == 'Dolby Digital Plus' or actual == 'Dolby TrueHD'
            or actual == 'Dolby AC-4' or actual == 'MLP') then
        return title
    end
    if title == 'DTS:X'
        and (actual == 'DTS' or actual == 'DTS-HD MA' or actual == 'DTS-HD HRA') then
        return title
    end
    if (title == 'DTS-HD MA' or title == 'DTS-HD HRA') and actual == 'DTS' then
        return title
    end
    if (title == 'HE-AAC' or title == 'HE-AAC v2') and actual == 'AAC' then
        return title
    end
    return actual
end

local function detect_audio_codec(snapshot, raw, context)
    local actual = detect_audio_codec_value(raw, context)
    local track = type(snapshot.audio_track) == 'table' and snapshot.audio_track or {}
    local title_raw, title_context = track_title_context(track)
    local title = detect_audio_codec_value(title_raw, title_context)
    if actual then return refine_audio_codec_from_title(actual, title) end
    if title then return title end
    for _, value in ipairs(audio_codec_candidates(snapshot)) do
        local label = raw_codec_label(value)
        if label then return label end
    end
    return '未知音频格式'
end

local function direct_layout_label(value)
    local text = lower(value)
    local three = text:match('(%d+%.%d+%.%d+)')
    if three then return three end
    local two = text:match('(%d+%.%d+)')
    if two then return two end
    if text:find('stereo', 1, true) or text:find('2ch', 1, true) then return '2.0' end
    if text:find('mono', 1, true) or text:find('1ch', 1, true) then return '1.0' end
    return nil
end

local function speaker_layout_label(value)
    local text = tostring(value or ''):upper()
    local speakers = {}
    for token in text:gmatch('[A-Z][A-Z0-9]+') do speakers[token] = true end
    local top_names = {'TFL', 'TFR', 'TFC', 'TBL', 'TBR', 'TBC', 'TSL', 'TSR'}
    local main_names = {'FL', 'FR', 'FC', 'BL', 'BR', 'SL', 'SR', 'WL', 'WR', 'BC'}
    local top, main = 0, 0
    for _, name in ipairs(top_names) do if speakers[name] then top = top + 1 end end
    for _, name in ipairs(main_names) do if speakers[name] then main = main + 1 end end
    if main > 0 and top > 0 then
        return string.format('%d.%d.%d', main, speakers.LFE and 1 or 0, top)
    end
    return nil
end

local function layout_channel_count(layout)
    local main, lfe, top = tostring(layout or ''):match('^(%d+)%.(%d+)%.(%d+)$')
    if main then return tonumber(main) + tonumber(lfe) + tonumber(top) end
    main, lfe = tostring(layout or ''):match('^(%d+)%.(%d+)$')
    if main then return tonumber(main) + tonumber(lfe) end
    return nil
end

local function detect_audio_layout(snapshot)
    local params = type(snapshot.audio_params) == 'table' and snapshot.audio_params or {}
    local track = type(snapshot.audio_track) == 'table' and snapshot.audio_track or {}
    local candidates = {
        params['hr-channels'] or '', params.channels or '', params['channel-layout'] or '',
        track['demux-channel-layout'] or '', track['channel-layout'] or '',
    }
    for _, value in ipairs(candidates) do
        local layout = direct_layout_label(value) or speaker_layout_label(value)
        if layout then return layout end
    end

    local count = tonumber(params['channel-count'])
        or tonumber(snapshot.audio_channel_count)
        or tonumber(snapshot.audio_channels)
        or tonumber(track['demux-channel-count'])
        or 0
    local title_layout = direct_layout_label(track.title) or speaker_layout_label(track.title)
    local title_count = layout_channel_count(title_layout)
    if title_layout and (count <= 0 or title_count == count) then return title_layout end
    if count == 8 then return '7.1' end
    if count == 6 then return '5.1' end
    if count == 2 then return '2.0' end
    if count == 1 then return '1.0' end
    return count > 0 and (tostring(count) .. 'ch') or '声道未知'
end

-- 1080 及以下按扫描方式区分逐行/隔行（1080P/1080i、720P/720i），
-- 4K/8K/1440P 等名称保持不变；interlaced 来自 video-frame-info 属性。
local function resolution_labels(width, height, interlaced)
    if width <= 0 and height <= 0 then return '', '' end
    if width >= 7600 or height >= 4300 then return '8K', '8K UHD' end
    if width >= 3800 or height >= 2100 then return '4K', '4K UHD' end
    if width >= 2500 or height >= 1400 then return '1440P', '1440P QHD' end
    if width >= 1900 or height >= 1000 then
        local label = interlaced and '1080i' or '1080P'
        return label, label
    end
    if width >= 1200 or height >= 700 then
        local label = interlaced and '720i' or '720P'
        return label, label
    end
    if height > 0 then
        local label = tostring(math.floor(height + 0.5)) .. (interlaced and 'i' or 'P')
        return label, label
    end
    return '', ''
end

local function format_fps(value)
    local fps = tonumber(value) or 0
    if fps <= 0 then return '' end
    local rounded = math.floor(fps + 0.5)
    if math.abs(fps - rounded) < 0.015 then return tostring(rounded) .. 'FPS' end
    local precision = math.abs(fps * 1001 / 1000 - rounded) < 0.02 and 3 or 2
    return string.format('%.' .. tostring(precision) .. 'fFPS', fps)
end

function M.from_snapshot(snapshot)
    snapshot = type(snapshot) == 'table' and snapshot or {}
    local params = type(snapshot.video_params) == 'table' and snapshot.video_params or {}
    local frame_info = type(snapshot.video_frame_info) == 'table'
        and snapshot.video_frame_info or {}
    local width = tonumber(params.w or params.dw or params.width) or 0
    local height = tonumber(params.h or params.dh or params.height) or 0
    local _, video_context = build_codec_context(snapshot.video_codec, snapshot.video_track)
    local audio_raw, audio_context = build_codec_context(snapshot.audio_codec, snapshot.audio_track)
    local interlaced = frame_info.interlaced == true or snapshot.interlaced == true
    local resolution, resolution_long = resolution_labels(width, height, interlaced)
    local fps = tonumber(snapshot.fps) or 0
    if fps <= 0 then fps = tonumber(snapshot.container_fps) or 0 end

    local video_track = type(snapshot.video_track) == 'table' and snapshot.video_track or {}
    local audio_track = type(snapshot.audio_track) == 'table' and snapshot.audio_track or {}
    local audio_params = type(snapshot.audio_params) == 'table' and snapshot.audio_params or {}
    local audio_present = audio_track.type == 'audio'
        or trim(snapshot.audio_codec) ~= ''
        or positive(audio_params['channel-count'])
        or trim(audio_params.channels) ~= ''
        or positive(snapshot.audio_channel_count)
        or positive(snapshot.audio_channels)
    local video_present = width > 0 or height > 0
        or video_track.type == 'video'
        or trim(snapshot.video_codec) ~= ''
    local hwdec = 'UNKNOWN'
    if snapshot.hwdec == 'no' then
        hwdec = 'SW'
    elseif trim(snapshot.hwdec) ~= '' then
        hwdec = 'HW'
    end

    return {
        video_present = video_present,
        resolution = resolution ~= '' and resolution or '分辨率未知',
        resolution_long = resolution_long ~= '' and resolution_long or '分辨率未知',
        interlaced = interlaced,
        video_codec = detect_video_codec(snapshot),
        dynamic_range = detect_dynamic_range(snapshot, video_context),
        fps = fps,
        fps_label = format_fps(fps),
        audio_present = audio_present,
        audio_codec = audio_present
            and detect_audio_codec(snapshot, audio_raw, audio_context) or '',
        audio_layout = audio_present and detect_audio_layout(snapshot) or '',
        hwdec = hwdec,
    }
end

function M.collect()
    return M.from_snapshot(read_snapshot())
end

return M
