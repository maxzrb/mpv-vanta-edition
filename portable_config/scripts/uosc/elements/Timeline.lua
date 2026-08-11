local Element = require('elements/Element')

---@class Timeline : Element
local Timeline = class(Element)

-- 细进度条保持视觉轻盈，同时让指针交互更宽容。数值为逻辑像素，随 uosc/DPI 缩放。
local SEEK_HITBOX_EXPAND_TOP = 1
local SEEK_HITBOX_EXPAND_BOTTOM = 1
local MISS_GUARD_HEIGHT = 12
local CONTROLS_HITBOX_GAP = 2

function Timeline:new() return Class.new(self) --[[@as Timeline]] end
function Timeline:init()
	Element.init(self, 'timeline', {render_order = 5})
	---@type false|{pause: boolean, distance: number, dragging: boolean, last: {x: number, y: number}}
	self.pressed = false
	self.obstructed = false
	self.size = 0
	self.progress_size = 0
	self.progress_scale = state.scale
	self.min_progress_size = 0 -- used for `flash-progress`
	self.font_size = 0
	self.top_border = 0
	self.line_width = 0
	self.progress_line_width = 0
	self.is_hovered = false
	self.has_thumbnail = false
	self.heatmap = nil

	self:decide_progress_size()
	self:update_dimensions()

	-- Load Youtube heatmap data if available
	self:register_mp_event('file-loaded', function()
		self.heatmap = load_youtube_heatmap()
	end)
	-- Release any dragging and clear heatmap when file gets unloaded
	self:register_mp_event('end-file', function()
		self.pressed = false
		self.heatmap = nil
	end)
end

function Timeline:get_visibility()
	return math.max(Elements:maybe('controls', 'get_visibility') or 0, Element.get_visibility(self))
end

function Timeline:decide_enabled()
	local previous = self.enabled
	self.enabled = not self.obstructed and state.duration ~= nil and state.duration > 0 and state.time ~= nil
	if self.enabled ~= previous then Elements:trigger('timeline_enabled', self.enabled) end
end

function Timeline:get_effective_size()
	if Elements:v('speed', 'dragging') then return self.size end
	local progress_size = math.max(self.min_progress_size, self.progress_size)
	return progress_size + math.ceil((self.size - self.progress_size) * self:get_visibility())
end

function Timeline:get_is_hovered() return self.enabled and self.is_hovered end

---@return number|nil
function Timeline:get_loaded_pos_safe()
	if type(state.duration) ~= 'number' or state.duration <= 0 then return nil end
	if type(state.time) ~= 'number' then return nil end

	-- 优先使用 uncached_ranges：找当前时间之后的第一个未缓存缺口
	if type(state.uncached_ranges) == 'table' and #state.uncached_ranges > 0 then
		for _, range in ipairs(state.uncached_ranges) do
			if type(range) == 'table'
				and type(range[1]) == 'number'
				and type(range[2]) == 'number'
			then
				if range[1] <= state.time and range[2] >= state.time then
					return nil -- 当前位置位于未缓存缺口内
				end
				if range[1] > state.time then
					return math.max(state.time, math.min(range[1], state.duration))
				end
			end
		end
		return state.duration -- 当前时间之后没有未缓存缺口
	end

	-- 兜底：cache_duration
	if type(state.cache_duration) == 'number' and state.cache_duration > 0 then
		return math.min(state.time + state.cache_duration, state.duration)
	end

	return nil
end

-- 进度条两端对齐控制栏两端按钮的视觉中心，形成“进度条与按钮一体”的观感。
function Timeline:sync_horizontal_bounds()
	local controls_ax, controls_bx = Elements:maybe('controls', 'get_visual_bounds')
	if controls_ax and controls_bx and controls_bx > controls_ax then
		self.ax, self.bx = controls_ax, controls_bx
		self.width = self.bx - self.ax
	end
end

function Timeline:update_dimensions()
	self.size = round(options.timeline_size * state.scale)
	self.top_border = round(options.timeline_border * state.scale)
	self.line_width = round(options.timeline_line_width * state.scale)
	self.progress_line_width = round(options.progress_line_width * state.scale)
	self.font_size = math.floor(math.min((self.size + 60 * state.scale) * 0.2, self.size * 0.96) * options.font_scale)
	local window_border_size = Elements:v('window_border', 'size', 0)
	local controls_scale = get_controls_scale()
	local controls_size = round(options.controls_size * controls_scale)
	local controls_margin = round(options.controls_margin * controls_scale)
	-- 进度条向两端按钮的视觉中心收拢，而不是拉满整个窗口宽度
	local side_margin = round(math.max(24, options.controls_margin * 2) * controls_scale)
	local fullscreen_timeline_gap = state.fullormaxed
		and round(controls_size * 0.18)
		or 0
	self.ax = window_border_size + side_margin
	self.ay = display.height - window_border_size - controls_size - controls_margin * 2
		- fullscreen_timeline_gap - self.size
	self.bx = display.width - window_border_size - side_margin
	self.by = self.ay + self.size
	self.width = self.bx - self.ax
	self.panel_top = self.ay - round(8 * state.scale)
	self.chapter_size = math.max((self.by - self.ay) / 10, 3 * state.scale)
	self.chapter_size_hover = self.chapter_size * 2

	-- Disable if not enough space
	local available_space = display.height - window_border_size * 2 - Elements:v('top_bar', 'size', 0)
	self.obstructed = available_space < self.size + round(10 * state.scale)
	self:decide_enabled()
end

function Timeline:decide_progress_size()
	local show = options.progress == 'always'
		or (options.progress == 'fullscreen' and state.fullormaxed)
		or (options.progress == 'windowed' and not state.fullormaxed)
	self.progress_size = show and round(options.progress_size * state.scale) or 0
	self.progress_scale = state.scale
end

function Timeline:toggle_progress()
	local current = self.progress_size
	self:tween_property('progress_size', current,
		current > 0 and 0 or round(options.progress_size * state.scale))
	request_render()
end

function Timeline:flash_progress()
	if self.enabled and options.flash_duration > 0 then
		if not self._flash_progress_timer then
			self._flash_progress_timer = mp.add_timeout(options.flash_duration / 1000, function()
				self:tween_property('min_progress_size', round(options.progress_size * state.scale), 0)
			end)
			self._flash_progress_timer:kill()
		end

		self:tween_stop()
		self.min_progress_size = round(options.progress_size * state.scale)
		request_render()
		self._flash_progress_timer.timeout = options.flash_duration / 1000
		self._flash_progress_timer:kill()
		self._flash_progress_timer:resume()
	end
end

function Timeline:get_time_at_x(x)
	local line_width = (options.timeline_style == 'line' and self.line_width - 1 or 0)
	local time_width = self.width - line_width - 1
	local fax = (time_width) * state.time / state.duration
	local fbx = fax + line_width
	-- time starts 0.5 pixels in
	x = x - self.ax - 0.5
	if x > fbx then
		x = x - line_width
	elseif x > fax then
		x = fax
	end
	local progress = clamp(0, x / time_width, 1)
	return state.duration * progress
end

---@param fast? boolean
function Timeline:set_from_cursor(fast)
	if state.time and state.duration then
		mp.commandv('seek', self:get_time_at_x(cursor.x), fast and 'absolute+keyframes' or 'absolute+exact')
	end
end

function Timeline:clear_thumbnail()
	if self.has_thumbnail then
		mp.commandv('script-message-to', 'thumbfast', 'clear')
		self.has_thumbnail = false
	end
end

function Timeline:handle_cursor_down()
	self.pressed = {
		pause = state.pause,
		distance = 0,
		dragging = false,
		last = {x = cursor.x, y = cursor.y},
	}
end
function Timeline:on_prop_duration() self:decide_enabled() end
function Timeline:on_prop_time() self:decide_enabled() end
function Timeline:on_prop_uncached_ranges() request_render() end
function Timeline:on_prop_cache_duration() request_render() end
function Timeline:on_prop_pause() request_render() end
function Timeline:on_prop_border() self:update_dimensions() end
function Timeline:on_prop_title_bar() self:update_dimensions() end
function Timeline:on_prop_fullormaxed()
	self:decide_progress_size()
	self:update_dimensions()
end
function Timeline:on_display()
	-- 普通窗口缩放只更新几何，不应把用户手动 toggle 的细进度条恢复为配置默认值。
	-- 仅在跨显示器等导致 DPI 比例变化时，按比例换算当前动画/切换状态。
	local previous_scale = math.max(0.01, self.progress_scale or state.scale)
	if previous_scale ~= state.scale then
		self:tween_stop()
		local scale_ratio = state.scale / previous_scale
		self.progress_size = round(self.progress_size * scale_ratio)
		self.min_progress_size = round(self.min_progress_size * scale_ratio)
		self.progress_scale = state.scale
	end
	self:update_dimensions()
end
function Timeline:on_options()
	self:decide_progress_size()
	self:update_dimensions()
end
function Timeline:handle_cursor_up()
	if self.pressed then
		local was_dragging = self.pressed.dragging
		self:set_from_cursor()
		if was_dragging then mp.set_property_native('pause', self.pressed.pause) end
		self.pressed = false
	end
end
function Timeline:on_global_mouse_leave()
	if self.pressed and self.pressed.dragging then
		mp.set_property_native('pause', self.pressed.pause)
	end
	self.pressed = false
end

function Timeline:on_global_mouse_move()
	if self.pressed then
		self.pressed.distance = self.pressed.distance + get_point_to_point_proximity(self.pressed.last, cursor)
		self.pressed.last.x, self.pressed.last.y = cursor.x, cursor.y
		local drag_threshold = math.max(4, round(4 * state.scale))
		if not self.pressed.dragging and self.pressed.distance >= drag_threshold then
			self.pressed.dragging = true
			mp.set_property_native('pause', true)
		end
		if self.pressed.dragging then
			-- 拖拽过程中保持廉价的关键帧定位，松手时再精确落点
			self:set_from_cursor(true)
		end
	end
end

function Timeline:cursor_command(command)
	if type(command) == 'string' and #command > 0 and state.time and state.duration then
		local expanded_command = command:gsub('{time}', self:get_time_at_x(cursor.x))
		mp.command(expanded_command)
	end
end

function Timeline:render()
	if self.size == 0 then
		self:clear_thumbnail()
		return
	end

	local size = self:get_effective_size()
	local visibility = self:get_visibility()
	self.is_hovered = false
	self:sync_horizontal_bounds()

	-- 加宽的 seek 命中区与按钮区之间的空档守卫，避免误触发
	local interaction_scale = math.max(0.1, state.scale or 1)
	local expand_top = math.max(1, round(SEEK_HITBOX_EXPAND_TOP * interaction_scale))
	local expand_bottom = math.max(1, round(SEEK_HITBOX_EXPAND_BOTTOM * interaction_scale))
	local guard_height = math.max(1, round(MISS_GUARD_HEIGHT * interaction_scale))
	local controls_gap = math.max(1, round(CONTROLS_HITBOX_GAP * interaction_scale))
	local controls = Elements.controls
	local controls_visibility = controls and controls.enabled and controls:get_visibility() or 0
	local controls_limit = controls_visibility > 0 and controls.ay
		and math.max(self.by, controls.ay - controls_gap) or nil
	local seek_by = self.by + expand_bottom
	if controls_limit then seek_by = math.max(self.by, math.min(seek_by, controls_limit)) end
	local seek_hitbox = {
		ax = self.ax,
		ay = self.ay - expand_top,
		bx = self.bx,
		by = seek_by,
	}
	local miss_guard_hitbox = nil
	if controls_visibility > 0 and controls_limit then
		local guard_by = seek_hitbox.by + guard_height
		if controls_limit then guard_by = math.min(guard_by, controls_limit) end
		if guard_by > seek_hitbox.by then
			miss_guard_hitbox = {
				ax = self.ax,
				ay = seek_hitbox.by,
				bx = self.bx,
				by = guard_by,
			}
		end
	end
	local seek_hovered = cursor:collides_with(seek_hitbox)

	if size < 1 then
		self:clear_thumbnail()
		return
	end

	if seek_hovered then
		self.is_hovered = true
	end
	-- 先注册空档守卫，再注册 seek 区域；按钮随后渲染，重叠处以按钮为准
	if miss_guard_hitbox then
		cursor:zone('primary_down', miss_guard_hitbox, function() end)
	end
	if visibility > 0 then
		cursor:zone('primary_down', seek_hitbox, function()
			self:handle_cursor_down()
			cursor:once('primary_up', function() self:handle_cursor_up() end)
		end)
		if #options.timeline_mbtn_right > 0 then
			cursor:zone('secondary_down', seek_hitbox, function()
				self:cursor_command(options.timeline_mbtn_right)
			end)
		end
		if config.timeline_step ~= 0 then
			cursor:zone('wheel_down', seek_hitbox, function()
				mp.commandv('seek', -config.timeline_step, config.timeline_step_flag)
			end)
			cursor:zone('wheel_up', seek_hitbox, function()
				mp.commandv('seek', config.timeline_step, config.timeline_step_flag)
			end)
		end
	end

	local ass = assdraw.ass_new()
	local progress_size = math.max(self.min_progress_size, self.progress_size)

	-- 底部连续面板：进度条与按钮共享同一块半透明背景，消除割裂感
	local panel_visibility = math.max(visibility, Elements:maybe('controls', 'get_visibility') or 0)
	if panel_visibility > 0 then
		local window_border = Elements:v('window_border', 'size', 0)
		local panel_ax, panel_bx = window_border, display.width - window_border
		local panel_by = display.height + state.radius * 2
		local blur = round(15 * state.scale)
		ass:rect(panel_ax - blur, self.panel_top, panel_bx + blur, panel_by + blur, {
			color = bg,
			opacity = panel_visibility * 0.70,
			blur = blur,
		})
		ass:rect(panel_ax, self.panel_top + blur, panel_bx, panel_by, {
			color = bg,
			opacity = panel_visibility * 0.34,
		})
	end

	local tooltip_gap = round(2 * state.scale)
	local timestamp_gap = tooltip_gap

	local progress = state.time / state.duration
	local is_line = options.timeline_style == 'line'

	-- 细圆角进度条：视觉上内嵌于面板中，而非悬浮
	local bax, hit_bay, bbx, hit_bby = self.ax, self.by - size - self.top_border, self.bx, self.by
	local bar_height = math.max(3, round(4 * state.scale))
	local bay = hit_bay + (size - bar_height) / 2
	local bby = bay + bar_height
	local fax, fay, fbx, fby = 0, bay + self.top_border, 0, bby

	local line_width = 0

	if is_line then
		local minimized_fraction = 1 - math.min((size - progress_size) / ((self.size - progress_size) / 8), 1)
		local progress_delta = progress_size > 0 and self.progress_line_width - self.line_width or 0
		line_width = self.line_width + (progress_delta * minimized_fraction)
		fax = bax + (self.width - line_width) * progress
		fbx = fax + line_width
		line_width = line_width - 1
	else
		fax, fbx = bax, bax + self.width * progress
	end

	local foreground_size = fby - fay

	-- time starts 0.5 pixels in
	local time_ax = bax + 0.5
	local time_width = self.width - line_width - 1

	-- time to x: calculates x coordinate so that it never lies inside of the line
	local function t2x(time)
		local x = time_ax + time_width * time / state.duration
		return time <= state.time and x or x + line_width
	end

	-- 安静的轨道底色
	ass:rect(bax, bay, bbx, bby, {
		color = config.color.timeline_track or fg,
		opacity = visibility * config.opacity.timeline,
		radius = bar_height / 2,
	})

	-- 已缓冲/加载进度（uncached_ranges + cache_duration 兜底）
	local loaded_progress_min_ahead = 15
	local loaded_progress_opacity = 0.22
	local loaded_pos = self:get_loaded_pos_safe()
	if type(loaded_pos) == 'number'
		and type(state.time) == 'number'
		and loaded_pos - state.time >= loaded_progress_min_ahead
	then
		local loaded_x = bax + self.width * (loaded_pos / state.duration)
		if loaded_x > bax + 1 then
			ass:rect(bax, bay, loaded_x, bby, {
				color = config.color.match,
				opacity = visibility * loaded_progress_opacity,
				radius = bar_height / 2,
			})
		end
	end

	-- Progress
	local function draw_progress()
		ass:rect(fax, fay, fbx, fby, {
			color = config.color.match,
			opacity = visibility * config.opacity.position,
			radius = bar_height / 2,
		})
		ass:circle(fbx, fay + (fby - fay) / 2, math.max(3, bar_height * 1.2), {
			color = config.color.match,
			opacity = visibility * config.opacity.position,
		})
	end

	-- Youtube heatmap
	local function draw_heatmap()
		if options.timeline_heatmap ~= 'no' and self.heatmap and config.opacity.heatmap > 0 and visibility > 0 then
			local is_above = options.timeline_heatmap == 'above'
			local heatmap_height = round(40 * state.scale)
			local height = math.min(heatmap_height, size / self.size * heatmap_height)
			local ax, ay = bax, is_above and (bay - height) or (bay + self.top_border)
			local bx, by = bbx, is_above and bay or bby
			local opts = {color = config.color.heatmap, opacity = config.opacity.heatmap * visibility}
			local clip_ay = is_above and (ay - round(10 * state.scale)) or ay
			opts.clip = string.format('\\clip(%d,%d,%d,%d)', ax, clip_ay, bx, by)
			ass:smooth_curve(ax, ay, bx, by, self.heatmap, opts)
		end
	end

	-- Change draw order based on 'timeline_style' to keep the heatmap visible
	if is_line then
		draw_heatmap()
		draw_progress()
	else
		draw_progress()
		draw_heatmap()
	end

	-- Uncached ranges
	if state.uncached_ranges then
		local opts = {size = 80, anchor_y = fby}
		local texture_char = visibility > 0 and 'b' or 'a'
		local offset = opts.size / (visibility > 0 and 24 or 28)
		for _, range in ipairs(state.uncached_ranges) do
			if options.timeline_cache then
				local ax = range[1] < 0.5 and bax or math.floor(t2x(range[1]))
				local bx = range[2] > state.duration - 0.5 and bbx or math.ceil(t2x(range[2]))
				opts.color, opts.opacity, opts.anchor_x = 'ffffff', 0.4 - (0.2 * visibility), bax
				ass:texture(ax, fay, bx, fby, texture_char, opts)
				opts.color, opts.opacity, opts.anchor_x = '000000', 0.6 - (0.2 * visibility), bax + offset
				ass:texture(ax, fay, bx, fby, texture_char, opts)
			end
		end
	end

	-- Custom ranges
	for _, chapter_range in ipairs(state.chapter_ranges) do
		local rax = chapter_range.start < 0.1 and bax or t2x(chapter_range.start)
		local rbx = chapter_range['end'] > state.duration - 0.1 and bbx
			or t2x(math.min(chapter_range['end'], state.duration))
		ass:rect(rax, fay, rbx, fby, {
			color = chapter_range.color,
			opacity = visibility * chapter_range.opacity,
		})
		-- 细条上保留显式的片段边界刻度，让片头/片尾起止点可读
		local tick_width = math.max(2, round(2 * state.scale))
		local tick_overhang = math.max(3, round(3 * state.scale))
		ass:rect(
			rax - tick_width / 2, fay - tick_overhang,
			rax + tick_width / 2, fby + tick_overhang,
			{color = chapter_range.color, opacity = visibility * math.max(chapter_range.opacity, 0.92)}
		)
		ass:rect(
			rbx - tick_width / 2, fay - tick_overhang,
			rbx + tick_width / 2, fby + tick_overhang,
			{color = chapter_range.color, opacity = visibility * math.max(chapter_range.opacity, 0.92)}
		)
	end

	-- Chapters
	local hovered_chapter = nil
	-- 直接复用进度条的可见度动画，章节、片段边界与 A-B 标记同步随鼠标渐隐。
	local chapter_visibility = visibility * config.opacity.chapters
	if (chapter_visibility > 0 and (#state.chapters > 0 or state.ab_loop_a or state.ab_loop_b)) then
		-- 章节标记：每个章节位置绘制上下两个低饱和钢蓝色小三角形，
		-- 上方尖端朝下、下方尖端朝上，保持双箭头辨识度
		-- 章节颜色统一复用当前主题 accent；实心色块不加深色描边，避免边缘显脏。
		local CHAPTER_COLOR = config.color.chapter or config.color.accent or config.color.match
		local chapter_marker_border = math.max(0, options.chapter_marker_border or 0) * state.scale
		local chapter_border = math.max(1, options.timeline_border or 0) * state.scale
		local triangle_half_width = math.max(round(2 * state.scale), round(self.chapter_size * 0.9))
		local triangle_height = math.max(round(2 * state.scale), round(self.chapter_size * 1.5))
		local triangle_radius = math.max(triangle_half_width, triangle_height)
		local triangle_radius_hovered = triangle_radius * 2

		if triangle_height > 0 and triangle_half_width > 0 then
			local chapter_y = fay + foreground_size / 2

			---@param time number
			---@param half_width number 三角形底边半宽
			---@param height number 三角形高
			local function draw_chapter(time, half_width, height)
				local chapter_x = t2x(time)
				local function draw_triangle(x1, y1, x2, y2, x3, y3)
					ass:new_event()
					ass:append(string.format(
						'{\\pos(0,0)\\rDefault\\an7\\blur0\\bord%f\\shad0\\1c&H%s\\3c&H%s\\alpha&H%X&}',
						chapter_marker_border, CHAPTER_COLOR, CHAPTER_COLOR,
						opacity_to_alpha(chapter_visibility)
					))
					ass:draw_start()
					ass:move_to(x1, y1)
					ass:line_to(x2, y2)
					ass:line_to(x3, y3)
					ass:draw_stop()
				end
				-- 上三角形：底边在进度条上方，尖端朝下贴住进度条上边缘
				draw_triangle(
					chapter_x - half_width, fay - height,
					chapter_x + half_width, fay - height,
					chapter_x, fay
				)
				-- 下三角形：底边在进度条下方，尖端朝上贴住进度条下边缘
				draw_triangle(
					chapter_x - half_width, fby + height,
					chapter_x + half_width, fby + height,
					chapter_x, fby
				)
			end

			if #state.chapters > 0 then
				-- Find hovered chapter indicator
				local closest_delta = math.huge

				if self.proximity_raw < triangle_radius_hovered then
					for i, chapter in ipairs(state.chapters) do
						local chapter_x = t2x(chapter.time)
						local cursor_chapter_delta = math.sqrt((cursor.x - chapter_x) ^ 2 + (cursor.y - chapter_y) ^ 2)
						if cursor_chapter_delta <= triangle_radius_hovered and cursor_chapter_delta < closest_delta then
							hovered_chapter, closest_delta = chapter, cursor_chapter_delta
							self.is_hovered = true
						end
					end
				end

				for i, chapter in ipairs(state.chapters) do
					if chapter ~= hovered_chapter then draw_chapter(chapter.time, triangle_half_width, triangle_height) end
					local circle = {point = {x = t2x(chapter.time), y = chapter_y}, r = triangle_radius_hovered}
					if visibility > 0 and chapter == hovered_chapter then
						cursor:zone('primary_down', circle, function()
							mp.commandv('seek', chapter.time, 'absolute+exact')
						end)
					end
				end

				-- Render hovered chapter above others
				if hovered_chapter then
					draw_chapter(hovered_chapter.time, triangle_half_width * 2, triangle_height * 2)
					timestamp_gap = tooltip_gap + round(triangle_radius_hovered)
				else
					timestamp_gap = tooltip_gap + round(triangle_radius)
				end
			end

			-- A-B loop indicators
			local has_a, has_b = state.ab_loop_a and state.ab_loop_a >= 0, state.ab_loop_b and state.ab_loop_b > 0
			local ab_radius = round(math.min(math.max(8 * state.scale, foreground_size * 0.25), foreground_size))
			local ab_tip_inset = round(3 * state.scale)

			---@param time number
			---@param kind 'a'|'b'
			local function draw_ab_indicator(time, kind)
				local x = t2x(time)
				ass:new_event()
				ass:append(string.format(
					'{\\pos(0,0)\\rDefault\\an7\\blur0\\yshad0.01\\bord%f\\1c&H%s\\3c&H%s\\4c&H%s\\alpha&H%X&}',
					chapter_border, fg, bg, bg, opacity_to_alpha(chapter_visibility)
				))
				ass:draw_start()
				ass:move_to(x, fby - ab_radius)
				if kind == 'b' then ass:line_to(x + ab_tip_inset, fby - ab_radius) end
				ass:line_to(x + (kind == 'a' and 0 or ab_radius), fby)
				ass:line_to(x - (kind == 'b' and 0 or ab_radius), fby)
				if kind == 'a' then ass:line_to(x - ab_tip_inset, fby - ab_radius) end
				ass:draw_stop()
			end

			if has_a then draw_ab_indicator(state.ab_loop_a, 'a') end
			if has_b then draw_ab_indicator(state.ab_loop_b, 'b') end
		end
	end

	-- Hovered time and chapter
	local rendered_thumbnail = false
	if (seek_hovered or self.pressed or hovered_chapter) and not Elements:v('speed', 'dragging') then
		local cursor_x = hovered_chapter and t2x(hovered_chapter.time) or cursor.x
		local hovered_seconds = hovered_chapter and hovered_chapter.time or self:get_time_at_x(cursor.x)

		-- Cursor line
		-- 0.5 to switch when the pixel is half filled in
		local color = ((fax - 0.5) < cursor_x and cursor_x < (fbx + 0.5)) and bg or fg
		local ax, ay, bx, by = cursor_x - 0.5, fay, cursor_x + 0.5, fby
		ass:rect(ax, ay, bx, by, {color = color, opacity = 0.33})
		local tooltip_anchor = {ax = ax, ay = ay - self.top_border, bx = bx, by = by}

		-- Timestamp
		local opts = {
			size = math.max(round(self.font_size * 1.35), round(15 * state.scale)),
			offset = timestamp_gap,
			margin = tooltip_gap,
			timestamp = options.time_precision > 0,
			bold = true,
		}
		local hovered_time_human = format_time(hovered_seconds, state.duration)
		opts.width_overwrite = timestamp_width(hovered_time_human, opts)
		tooltip_anchor = ass:tooltip(tooltip_anchor, hovered_time_human, opts)

		-- Thumbnail
		if not thumbnail.disabled
			and (not self.pressed or self.pressed.distance < round(5 * state.scale))
			and thumbnail.width ~= 0
			and thumbnail.height ~= 0
		then
			-- state.radius 已包含 DPI 缩放，不能再次乘 state.scale。
			local border = math.ceil(math.max(2 * state.scale, state.radius / 2))
			local thumb_x_margin, thumb_y_margin = border + tooltip_gap + bax, border + tooltip_gap
			local thumb_width, thumb_height = thumbnail.width, thumbnail.height
			local thumb_x = round(clamp(
				thumb_x_margin,
				cursor_x - thumb_width / 2,
				display.width - thumb_width - thumb_x_margin
			))
			local thumb_y = round(tooltip_anchor.ay - thumb_y_margin - thumb_height)
			local ax, ay = (thumb_x - border), (thumb_y - border)
			local bx, by = (thumb_x + thumb_width + border), (thumb_y + thumb_height + border)
			ass:rect(ax, ay, bx, by, {
				color = bg,
				border = 1,
				opacity = {main = config.opacity.thumbnail, border = 0.08 * config.opacity.thumbnail},
				border_color = fg,
				radius = state.radius,
			})
			local thumb_seconds = (state.rebase_start_time == false and state.start_time) and
				(hovered_seconds - state.start_time) or hovered_seconds
			mp.commandv('script-message-to', 'thumbfast', 'thumb', thumb_seconds, thumb_x, thumb_y)
			self.has_thumbnail, rendered_thumbnail = true, true
			tooltip_anchor.ay = ay
		end

		-- Chapter title
		if config.opacity.chapters > 0 and #state.chapters > 0 then
			local _, chapter = itable_find(state.chapters, function(c) return hovered_seconds >= c.time end,
				#state.chapters, 1)
			if chapter and not chapter.is_end_only then
				ass:tooltip(tooltip_anchor, chapter.title_wrapped, {
					size = self.font_size,
					offset = tooltip_gap,
					responsive = false,
					bold = true,
					width_overwrite = chapter.title_wrapped_width * self.font_size,
					lines = chapter.title_lines,
					margin = tooltip_gap,
				})
			end
		end
	end

	-- Clear thumbnail
	if not rendered_thumbnail then self:clear_thumbnail() end

	return ass
end

return Timeline
