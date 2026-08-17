local Element = require('elements/Element')
local mp_utils = require('mp.utils')

local function load_media_format_info()
	local candidates = {
		mp.command_native({'expand-path', '~~/script-modules/media-format-info.lua'}),
	}
	local source = debug.getinfo(1, 'S').source:gsub('^@', '')
	local script_dir = select(1, mp_utils.split_path(source))
	local parent = ''
	for _ = 1, 4 do
		parent = parent .. '../'
		candidates[#candidates + 1] = mp_utils.join_path(
			script_dir, parent .. 'script-modules/media-format-info.lua'
		)
	end
	for _, path in ipairs(candidates) do
		local ok, result = pcall(dofile, path)
		if ok and type(result) == 'table' then return result end
	end
	error('无法加载 media-format-info.lua')
end

local MediaFormatInfo = load_media_format_info()

---@class MediaInfo : Element
local MediaInfo = class(Element)

-- 与参考版一致的胶囊几何参数（逻辑像素，随底栏 DPI/窄窗口比例统一缩放）
local MEDIA_INFO_FONT_SIZE = 14
local MEDIA_INFO_CAPSULE_HEIGHT = 27
local MEDIA_INFO_TIMELINE_OFFSET = 30
local MEDIA_INFO_PICTURE_INSET = 10
local MEDIA_INFO_LETTER_SPACING = 0.2

local function format_rate(bits_per_second)
	local value = tonumber(bits_per_second) or 0
	if value <= 0 then return '' end
	if value >= 100000000 then return string.format('%d Mbps', math.floor(value / 1000000 + 0.5)) end
	if value >= 1000000 then return string.format('%.1f Mbps', value / 1000000) end
	return string.format('%d Kbps', math.floor(value / 1000 + 0.5))
end

-- 实时码率：视频 + 音频（mpv 实时属性）
local function read_live_bitrate()
	local video = mp.get_property_number('video-bitrate', 0)
	local audio = mp.get_property_number('audio-bitrate', 0)
	local bitrate = (video or 0) + (audio or 0)
	if bitrate > 0 then return bitrate end
	-- 兜底：当前视频/音频轨道 demux 码率求和
	local vtrack = mp.get_property_native('current-tracks/video', {})
	local atrack = mp.get_property_native('current-tracks/audio', {})
	local vbr = type(vtrack) == 'table' and tonumber(vtrack['demux-bitrate']) or 0
	local abr = type(atrack) == 'table' and tonumber(atrack['demux-bitrate']) or 0
	bitrate = (vbr or 0) + (abr or 0)
	if bitrate > 0 then return bitrate end
	return 0
end

-- 平均码率：文件总大小 / 时长（含音频及全部封装数据）
local function read_average_bitrate()
	local size = mp.get_property_number('file-size', 0)
	local duration = mp.get_property_number('duration', 0)
	if size > 0 and duration > 0 then return size * 8 / duration end
	return 0
end

-- 实时码率平滑：视频/音频属性的刷新频率不同，直接求和会时快时慢地跳。
-- 用按时间常数的指数移动平均，让显示值以均匀速度逼近目标值。
local function smooth_bitrate(filter, target)
	local tau = options.media_info_bitrate_smoothing or 0
	if tau <= 0 then
		-- 平滑关闭：直接显示目标值
		filter.value, filter.time, filter.display, filter.mean = target, mp.get_time(), target, target
		return target
	end
	local now = mp.get_time()
	if filter.time <= 0 then
		-- 首个样本直接采用，避免文件开头从 0 缓慢爬升
		filter.value, filter.time, filter.display, filter.mean = target, now, target, target
		return target
	end
	local dt = math.max(0, now - filter.time)
	filter.time = now

	-- 一级滤波：短期平均，抹掉帧级高频抖动（如 VBR 场景切换时的码率横跳）
	local short_tau = math.max(0.2, tau / 5)
	local alpha1 = dt > 0 and (1 - math.exp(-dt / short_tau)) or 1
	filter.mean = filter.mean + (target - filter.mean) * alpha1

	-- 二级滤波：基于短期平均做平滑，波动越大时间常数越大，抑制剧烈抖动
	local deviation = math.abs(filter.mean - filter.display) / math.max(math.abs(filter.display), 1)
	local smooth_tau = tau
	if deviation >= 0.5 then
		smooth_tau = tau * 3
	elseif deviation >= 0.25 then
		smooth_tau = tau * 2
	end

	-- 严格按时间常数的 EMA。不设下限（高频刷新时自然平滑），
	-- 仅限制单次最大步长，防止低频刷新或突变时数字瞬跳
	local alpha2 = dt > 0 and (1 - math.exp(-dt / smooth_tau)) or 1
	alpha2 = math.min(alpha2, 0.3)
	filter.value = filter.value + (filter.mean - filter.value) * alpha2

	-- 滞回阈值：与当前显示值偏差不足该比例时不更新显示，避免数字来回跳
	local threshold = options.media_info_bitrate_deadband or 0.02
	if math.abs(filter.value - filter.display) / math.max(math.abs(filter.display), 1) >= threshold then
		filter.display = filter.value
	end
	return filter.display
end

local function read_bitrate(mode, filter)
	-- 返回格式化字符串与是否为平均值，标签随实际数据源显示
	local live, avg = read_live_bitrate(), read_average_bitrate()
	local bitrate, is_avg
	if mode == 'avg' and avg > 0 then
		bitrate, is_avg = avg, true
	elseif mode == 'live' and live > 0 then
		bitrate, is_avg = live, false
	elseif avg > 0 then
		bitrate, is_avg = avg, true
	elseif live > 0 then
		bitrate, is_avg = live, false
	end
	if bitrate and bitrate > 0 then
		-- 仅实时码率需要平滑；平均码率是常量，直接显示
		if not is_avg and filter then bitrate = smooth_bitrate(filter, bitrate) end
		return format_rate(bitrate), is_avg
	end
	return '', false
end

local function read_network_speed()
	-- 使用 mpv 的解复用状态，而非从路径文本推断网络媒体。
	if mp.get_property_native('demuxer-via-network', false) ~= true then return '' end
	local bytes = mp.get_property_number('cache-speed', 0)
	if bytes <= 0 then return '' end
	if bytes >= 1024 * 1024 then return string.format('↓ %.1f MB/s', bytes / 1024 / 1024) end
	return string.format('↓ %d KB/s', math.floor(bytes / 1024 + 0.5))
end

-- 信箱黑边时返回视频画面的纵向范围（uosc 坐标），用于把胶囊夹在画面内
local function get_video_display_vertical_bounds()
	local dimensions = mp.get_property_native('osd-dimensions', {})
	local osd_height = type(dimensions) == 'table' and tonumber(dimensions.h) or nil
	local display_height = tonumber(display.height)
	if not osd_height or osd_height <= 0 or not display_height or display_height <= 0 then
		return nil, nil
	end
	local scale_y = display_height / osd_height
	local top = clamp(0, (tonumber(dimensions.mt) or 0) * scale_y, display_height)
	local bottom = clamp(0, (osd_height - (tonumber(dimensions.mb) or 0)) * scale_y, display_height)
	if bottom <= top then return nil, nil end
	return top, bottom
end

local function append(parts, text, tone, group, compact_before)
	if text and text ~= '' then
		parts[#parts + 1] = {
			text = tostring(text),
			tone = tone or 'base',
			group = group or 'base',
			compact_before = compact_before == true,
		}
	end
end

local function build_segments(mode, filter)
	local info = MediaFormatInfo.collect()
	if not info.video_present then return {} end
	local parts = {}
	-- 硬解/软解放在最前，一眼确认当前解码状态
	if info.hwdec == 'HW' then
		append(parts, '硬解', 'muted', 'decode')
	elseif info.hwdec == 'SW' then
		append(parts, '软解', 'muted', 'decode')
	else
		append(parts, '解码未知', 'muted', 'decode')
	end
	append(parts, info.resolution_long, 'primary', 'picture')
	if info.dynamic_range ~= '' then
		append(parts, info.dynamic_range, 'hero', 'picture')
	end
	append(parts, info.video_codec, 'primary', 'video')
	append(parts, info.fps_label, 'muted', 'video')
	if info.audio_present then
		append(parts, info.audio_codec, 'primary', 'audio')
		append(parts, info.audio_layout, 'muted', 'audio')
	end
	local output_format = mp.get_property('audio-out-params/format', ''):lower()
	if output_format:find('spdif-', 1, true) == 1 then
		append(parts, '源码直通', 'hero', 'audio', true)
	end
	local bitrate, is_avg = read_bitrate(mode, filter)
	if bitrate ~= '' then
		append(parts, is_avg and '平均码率' or '实时码率', 'muted', 'throughput')
		append(parts, bitrate, 'primary', 'throughput', true)
		-- 标记可点击：点击后在实时码率 / 平均码率之间循环切换
		parts[#parts - 1].click_target = 'bitrate'
		parts[#parts].click_target = 'bitrate'
	end
	local network = read_network_speed()
	if network ~= '' then
		append(parts, '网络', 'muted', 'throughput')
		append(parts, network, 'primary', 'throughput', true)
	end
	return parts
end

-- 参考版胶囊渲染：按视觉分组（硬解+画面归 picture），hero/primary/muted 三档配色
local function render_segments(ass, x, y, segments, visibility, max_width, scale)
	local size = round(MEDIA_INFO_FONT_SIZE * scale)
	local item_gap = round(12 * scale)
	local compact_gap = round(5 * scale)
	local capsule_gap = round(7 * scale)
	local capsule_padding = round(9 * scale)
	local capsule_height = round(MEDIA_INFO_CAPSULE_HEIGHT * scale)
	local capsule_radius = round(5 * scale)
	local cursor_x = x
	local max_x = max_width and (x + max_width) or display.width
	local base_opts = {
		size = size,
		color = config.color.menu_text or config.color.time_current or bgt,
		opacity = visibility * 0.98,
		-- 描边保持与底栏按钮相同的 DPI 线宽，不叠加窄窗口压缩。
		border = math.max(1, options.text_border * state.scale),
		border_color = bg,
		shadow = 0,
		bold = false,
	}
	local hero_accent = config.color.menu_active or config.color.match
		or config.color.menu_foreground or fg
	-- 记录可点击文本（如码率）的命中区域，供 render 注册鼠标事件
	local click_hits = {}
	local function visual_group(segment)
		local group = segment.group or segment.tone or 'base'
		if group == 'decode' or group == 'picture' then return 'picture' end
		return group
	end

	local groups = {}
	for _, segment in ipairs(segments) do
		local text = segment.text or ''
		if text ~= '' then
			local key = visual_group(segment)
			local group = groups[#groups]
			if not group or group.key ~= key then
				group = {key = key, segments = {}}
				groups[#groups + 1] = group
			end
			group.segments[#group.segments + 1] = segment
		end
	end

	for _, group in ipairs(groups) do
		local content_width = 0
		local prepared = {}
		local hero_group = false
		for index, segment in ipairs(group.segments) do
			local text_opts = table_assign({}, base_opts)
			if segment.tone == 'hero' then
				hero_group = true
				text_opts.color = config.color.match or hero_accent
				text_opts.opacity = visibility * 0.92
				text_opts.bold = true
			elseif segment.tone == 'primary' then
				text_opts.opacity = visibility
				text_opts.bold = true
			elseif segment.tone == 'muted' then
				text_opts.color = config.color.time_current or bgt
				text_opts.opacity = visibility * 0.90
			end
			if segment.text:match('^[%w%s%./%-]+$') then
				text_opts.spacing = MEDIA_INFO_LETTER_SPACING * scale
			end
			local width = text_width(segment.text, text_opts)
			if text_opts.spacing then width = width + math.max(0, #segment.text - 1) * text_opts.spacing end
			local gap_before = segment.compact_before and compact_gap or item_gap
			prepared[#prepared + 1] = {
				segment = segment,
				opts = text_opts,
				width = width,
				gap_before = gap_before,
			}
			if index > 1 then content_width = content_width + gap_before end
			content_width = content_width + width
		end

		local capsule_width = content_width + capsule_padding * 2
		local leading_gap = cursor_x > x and capsule_gap or 0
		if cursor_x + leading_gap + capsule_width > max_x then break end
		cursor_x = cursor_x + leading_gap

		ass:rect(cursor_x, y - capsule_height / 2, cursor_x + capsule_width, y + capsule_height / 2, {
			color = config.color.menu_background or bg,
			border = math.max(0.75, 0.85 * scale),
			border_color = hero_group and hero_accent
				or config.color.menu_foreground or config.color.timeline_track or fg,
			opacity = {
				main = visibility * 0.38,
				border = visibility * (hero_group and 0.54 or 0.44),
			},
			radius = capsule_radius,
		})

		local text_x = cursor_x + capsule_padding
		for index, item in ipairs(prepared) do
			if index > 1 then text_x = text_x + item.gap_before end
			local item_x0 = text_x
			ass:txt(text_x, y, 4, item.segment.text, item.opts)
			text_x = text_x + item.width
			-- 同一 click_target 的连续文本合并为一个命中区（码率标签 + 数值）
			if item.segment.click_target then
				local target = item.segment.click_target
				local hit = click_hits[target]
				if not hit then
					hit = {
						ax = item_x0,
						ay = y - capsule_height / 2,
						bx = text_x,
						by = y + capsule_height / 2,
					}
					click_hits[target] = hit
				else
					hit.bx = text_x
				end
			end
		end

		cursor_x = cursor_x + capsule_width
	end
	return click_hits, math.max(0, cursor_x - x)
end

function MediaInfo:new() return Class.new(self) --[[@as MediaInfo]] end

function MediaInfo:init()
	Element.init(self, 'media_info', {render_order = 5.5, anchor_id = 'controls'})
	-- 码率显示模式：'live' 实时码率 / 'avg' 平均码率，点击胶囊文本循环切换
	self.bitrate_mode = 'live'
	-- 记录本帧实际绘制的胶囊范围，供速度滑块做碰撞检测
	self.layout_x, self.layout_y, self.layout_width = 0, 0, 0
	-- 实时码率平滑滤波器状态：value=内部跟踪值，display=实际显示值，mean=短期平均
	self.bitrate_filter = { value = 0, time = 0, display = 0, mean = 0 }
	local function refresh() request_render() end
	for _, property in ipairs({
		'hwdec-current', 'video-params', 'video-frame-info', 'video-codec',
		'estimated-vf-fps', 'container-fps',
		'video-bitrate', 'audio-bitrate', 'audio-codec', 'audio-params', 'audio-out-params/format',
		'current-tracks/video', 'current-tracks/audio', 'track-list', 'vid', 'aid',
		'cache-speed', 'demuxer-via-network',
	}) do
		self:observe_mp_property(property, 'native', refresh)
	end
	self:register_mp_event('file-loaded', function()
		-- 切换文件后重置平滑状态，避免沿用上一文件的码率
		self.bitrate_filter.value = 0
		self.bitrate_filter.time = 0
		self.bitrate_filter.display = 0
		self.bitrate_filter.mean = 0
		refresh()
	end)
	self:register_mp_event('video-reconfig', refresh)
end

function MediaInfo:on_display() request_render() end
function MediaInfo:on_options() request_render() end

-- 鼠标 Y 轴靠近进度条时与速度滑块同步渐隐（避免遮挡悬停信息），
-- 鼠标位于胶囊或双行后的速度滑块区域内保持可见，不影响交互
function MediaInfo:get_visibility()
	local base = Element.get_visibility(self)
	local timeline = Elements.timeline
	if not (timeline and timeline.enabled and timeline.size > 0) then return base end
	local center_y = self:get_center_y()
	local height = self:get_height()
	local top, bottom = nil, nil
	if center_y and height and height > 0 then
		local pad = round(2 * get_controls_scale())
		top = center_y - height / 2 - pad
		bottom = center_y + height / 2 + pad
	end
	local speed = Elements.speed
	local mouse_in_speed = speed and speed.enabled
		and cursor.x >= speed.ax and cursor.x <= speed.bx
		and cursor.y >= speed.ay and cursor.y <= speed.by
	if mouse_in_speed then return base end
	local fade, mouse_in_element = get_timeline_hover_fade(timeline, top, bottom)
	if mouse_in_element then return base end
	if fade <= 0 then return base end
	if fade >= 1 then return 0 end
	return base * (1 - fade)
end

-- 供速度滑块等元素对齐胶囊高度
function MediaInfo:get_height()
	return round(MEDIA_INFO_CAPSULE_HEIGHT * get_controls_scale())
end

-- 返回本帧媒体信息胶囊的实际布局范围；未绘制时返回 nil
function MediaInfo:get_layout_rect()
	if not self.layout_width or self.layout_width <= 0 then return nil end
	local height = self:get_height()
	return {
		ax = self.layout_x,
		ay = self.layout_y - height / 2,
		bx = self.layout_x + self.layout_width,
		by = self.layout_y + height / 2,
	}
end

-- 暴露信箱黑边对应的画面纵向范围，供速度滑块的双行布局复用
function MediaInfo:get_picture_bounds()
	return get_video_display_vertical_bounds()
end

-- 供速度滑块等元素对齐胶囊字号
function MediaInfo:get_font_size()
	return round(MEDIA_INFO_FONT_SIZE * get_controls_scale())
end

-- 供速度滑块等元素对齐胶囊中心（与 render 中 mi_y 同一计算）
function MediaInfo:get_center_y()
	local timeline = Elements.timeline
	if not (timeline and timeline.enabled and timeline.size > 0) then return nil end
	local scale = get_controls_scale()
	-- 时间轴厚度本身不做 compact，必须与 Timeline 的实际绘制公式一致。
	local bar_height = math.max(3, round(4 * state.scale))
	local hit_bay = timeline.by - timeline.size - timeline.top_border
	local bay = hit_bay + (timeline.size - bar_height) / 2
	local mi_y = bay - round(MEDIA_INFO_TIMELINE_OFFSET * scale)
	-- 与 render 相同的信箱黑边夹持，保证胶囊和滑块在任何画幅下都对齐
	local picture_top, picture_bottom = get_video_display_vertical_bounds()
	if picture_top and picture_bottom then
		local half_height = round(MEDIA_INFO_CAPSULE_HEIGHT * scale) / 2
		local picture_inset = round(MEDIA_INFO_PICTURE_INSET * scale)
		local min_y = picture_top + picture_inset + half_height
		local max_y = picture_bottom - picture_inset - half_height
		if min_y <= max_y then mi_y = clamp(min_y, mi_y, max_y) end
	end
	return mi_y
end

function MediaInfo:render()
	if not state.is_video or state.is_idle then
		self.layout_width = 0
		return
	end
	local visibility = self:get_visibility()
	if visibility <= 0 then
		self.layout_width = 0
		return
	end
	local segments = build_segments(self.bitrate_mode, self.bitrate_filter)
	if #segments == 0 then
		self.layout_width = 0
		return
	end

	local scale = get_controls_scale()
	local ass = assdraw.ass_new()

	-- 与参考版一致：胶囊悬在时间轴上方约 45px，而不是贴进底部面板
	local timeline = Elements.timeline
	if not (timeline and timeline.enabled and timeline.size > 0) then
		self.layout_width = 0
		return ass
	end
	local bar_height = math.max(3, round(4 * state.scale))
	local hit_bay = timeline.by - timeline.size - timeline.top_border
	local bay = hit_bay + (timeline.size - bar_height) / 2
	local mi_x = timeline.ax
	local mi_y = bay - round(MEDIA_INFO_TIMELINE_OFFSET * scale)

	-- 信箱黑边时把整行文字夹在视频画面内，避免胶囊落在黑边上
	local picture_top, picture_bottom = get_video_display_vertical_bounds()
	if picture_top and picture_bottom then
		local half_height = round(MEDIA_INFO_CAPSULE_HEIGHT * scale) / 2
		local picture_inset = round(MEDIA_INFO_PICTURE_INSET * scale)
		local min_y = picture_top + picture_inset + half_height
		local max_y = picture_bottom - picture_inset - half_height
		if min_y <= max_y then mi_y = clamp(min_y, mi_y, max_y) end
	end

	local click_hits, layout_width = render_segments(
		ass, mi_x, mi_y, segments, visibility, timeline.bx - mi_x, scale
	)
	self.layout_x, self.layout_y, self.layout_width = mi_x, mi_y, layout_width

	-- 码率胶囊点击：实时码率 / 平均码率 循环切换
	local bitrate_hit = click_hits and click_hits.bitrate
	if bitrate_hit then
		cursor:zone('primary_click', bitrate_hit, function()
			self.bitrate_mode = self.bitrate_mode == 'avg' and 'live' or 'avg'
			request_render()
		end)
	end
	return ass
end

return MediaInfo
