local Element = require('elements/Element')

local SPEED_LAYOUT_GAP = 6

local function rects_overlap(rect_a, rect_b)
	return rect_a and rect_b
		and rect_a.ax < rect_b.bx and rect_a.bx > rect_b.ax
		and rect_a.ay < rect_b.by and rect_a.by > rect_b.ay
end

---@alias Dragging { start_time: number; start_x: number; distance: number; speed_distance: number; start_speed: number; }

---@class Speed : Element
local Speed = class(Element)

---@param props? ElementProps
function Speed:new(props) return Class.new(self, props) --[[@as Speed]] end
function Speed:init(props)
	Element.init(self, 'speed', props)

	self.width = 0
	self.height = 0
	self.notches = 10
	self.notch_every = 0.1
	---@type number
	self.notch_spacing = nil
	---@type number
	self.font_size = nil
	---@type Dragging|nil
	self.dragging = nil
end

function Speed:get_visibility()
	-- 速度滑块直接复用媒体信息胶囊的可见度：靠近进度条时同步隐藏，离开后同步渐显。
	return Elements:maybe('media_info', 'get_visibility') or Element.get_visibility(self)
end

function Speed:on_coordinates()
	self.height, self.width = self.by - self.ay, self.bx - self.ax
	self.notch_spacing = self.width / (self.notches + 1)
	-- 速度数字字号比左侧媒体信息胶囊大 4px
	local media_font = Elements:maybe('media_info', 'get_font_size')
		or round(self.height * 0.48 * options.font_scale)
	self.font_size = media_font + round(4 * state.scale)
end
function Speed:on_options() self:on_coordinates() end

-- 独立于底部控制栏：居中显示在时间轴上方几个像素处。
-- Controls 只提供尺寸、不保留横向占位，避免窄窗口下挤掉播放键的居中空间。
---@return boolean 是否定位成功（时间轴可用）
function Speed:update_position()
	local timeline = Elements.timeline
	if not (timeline and timeline.enabled and timeline.size > 0) then return false end

	-- 与左侧媒体信息胶囊同高，保持底部视觉统一
	local height = Elements:maybe('media_info', 'get_height')
		or round(options.controls_size * get_controls_scale())
	local width = self.width
	if height <= 0 or width <= 0 then return false end
	local ax = round((display.width - width) / 2)
	-- 垂直中心对齐媒体胶囊；胶囊不可用时退回时间轴上方 6px
	local center_y = Elements:maybe('media_info', 'get_center_y')
	local ay
	if center_y then
		ay = round(center_y - height / 2)
	else
		ay = timeline.ay - height - round(SPEED_LAYOUT_GAP * state.scale)
	end

	-- 小窗口下媒体信息可能从左侧伸到速度滑块，碰撞时将速度滑块上移一行。
	-- 优先放在媒体信息上方；若画面顶部空间不足，则尝试放到下方。
	local normal_rect = {ax = ax, ay = ay, bx = ax + width, by = ay + height}
	local media_rect = Elements:maybe('media_info', 'get_layout_rect')
	if rects_overlap(media_rect, normal_rect) then
		local gap = round(SPEED_LAYOUT_GAP * state.scale)
		local above_ay = media_rect.ay - gap - height
		local below_ay = media_rect.by + gap
		local picture_top, picture_bottom = Elements:maybe('media_info', 'get_picture_bounds')
		local min_ay = picture_top or 0
		local max_ay = (picture_bottom or display.height) - height
		if min_ay <= max_ay then
			if above_ay >= min_ay then
				ay = above_ay
			elseif below_ay <= max_ay then
				ay = below_ay
			else
				ay = clamp(min_ay, above_ay, max_ay)
			end
		else
			-- 画面高度不足以容纳两行时，至少保持速度滑块在媒体信息上方。
			ay = above_ay
		end
	end
	if self.ax ~= ax or self.ay ~= ay or self.height ~= height then
		self:set_coordinates(ax, ay, ax + width, ay + height)
	end
	return true
end

function Speed:speed_step(speed, up)
	if options.speed_step_is_factor then
		if up then
			return speed * options.speed_step
		else
			return speed * 1 / options.speed_step
		end
	else
		if up then
			return speed + options.speed_step
		else
			return speed - options.speed_step
		end
	end
end

function Speed:handle_cursor_down()
	self:tween_stop() -- Stop and cleanup possible ongoing animations
	self.dragging = {
		start_time = mp.get_time(),
		start_x = cursor.x,
		distance = 0,
		speed_distance = 0,
		start_speed = state.speed,
	}
end

function Speed:on_global_mouse_move()
	if not self.dragging then return end

	self.dragging.distance = cursor.x - self.dragging.start_x
	self.dragging.speed_distance = (-self.dragging.distance / self.notch_spacing * self.notch_every)

	local speed_current = state.speed
	local speed_drag_current = self.dragging.start_speed + self.dragging.speed_distance
	speed_drag_current = clamp(0.01, speed_drag_current, 100)
	local drag_dir_up = speed_drag_current > speed_current

	local speed_step_next = speed_current
	local speed_drag_diff = math.abs(speed_drag_current - speed_current)
	while math.abs(speed_step_next - speed_current) < speed_drag_diff do
		speed_step_next = self:speed_step(speed_step_next, drag_dir_up)
	end
	local speed_step_prev = self:speed_step(speed_step_next, not drag_dir_up)

	local speed_new = speed_step_prev
	local speed_next_diff = math.abs(speed_drag_current - speed_step_next)
	local speed_prev_diff = math.abs(speed_drag_current - speed_step_prev)
	if speed_next_diff < speed_prev_diff then
		speed_new = speed_step_next
	end

	if speed_new ~= speed_current then
		mp.set_property_native('speed', speed_new)
	end
end

function Speed:handle_cursor_up()
	self.dragging = nil
	request_render()
end

function Speed:on_global_mouse_leave()
	self.dragging = nil
	request_render()
end

function Speed:handle_wheel_up() mp.set_property_native('speed', self:speed_step(state.speed, true)) end
function Speed:handle_wheel_down() mp.set_property_native('speed', self:speed_step(state.speed, false)) end

function Speed:render()
	if not self:update_position() then return end
	local visibility = self:get_visibility()
	local opacity = visibility

	if opacity <= 0 then return end

	cursor:zone('primary_down', self, function()
		self:handle_cursor_down()
		cursor:once('primary_up', function() self:handle_cursor_up() end)
	end)
	cursor:zone('secondary_click', self, function() mp.set_property_native('speed', 1) end)
	cursor:zone('wheel_down', self, function() self:handle_wheel_down() end)
	cursor:zone('wheel_up', self, function() self:handle_wheel_up() end)

	local ass = assdraw.ass_new()

	-- Background
	ass:rect(self.ax, self.ay, self.bx, self.by, {
		color = bg,
		border = 1,
		border_color = config.color.timeline_track or fg,
		radius = state.radius,
		opacity = opacity * config.opacity.speed,
	})

	-- Coordinates
	local ax, ay = self.ax, self.ay
	local bx, by = self.bx, ay + self.height
	local half_width = (self.width / 2)
	local half_x = ax + half_width

	-- Notches
	local speed_at_center = state.speed
	if self.dragging then
		speed_at_center = self.dragging.start_speed + self.dragging.speed_distance
		speed_at_center = clamp(0.01, speed_at_center, 100)
	end
	local nearest_notch_speed = round(speed_at_center / self.notch_every) * self.notch_every
	local nearest_notch_x = half_x + (((nearest_notch_speed - speed_at_center) / self.notch_every) * self.notch_spacing)
	local guide_size = math.floor(self.height / 7.5)
	local notch_by = by - guide_size
	-- 数字已移到视觉范围上方，刻度从顶部开始铺满整个滑块范围
	local notch_padding = math.max(1, round(2 * state.scale))
	local notch_ay_big = ay + notch_padding
	local notch_ay_medium = notch_ay_big + ((notch_by - notch_ay_big) * 0.2)
	local notch_ay_small = notch_ay_big + ((notch_by - notch_ay_big) * 0.4)
	local from_to_index = math.floor(self.notches / 2)

	for i = -from_to_index, from_to_index do
		local notch_speed = nearest_notch_speed + (i * self.notch_every)

		if notch_speed >= 0 and notch_speed <= 100 then
			local notch_x = nearest_notch_x + (i * self.notch_spacing)
			local notch_thickness = 1
			local notch_ay = notch_ay_small
			local notch_color = config.color.time_muted or fg
			if (notch_speed % (self.notch_every * 10)) < 0.00000001 then
				notch_ay = notch_ay_big
				notch_thickness = 1.5
				notch_color = config.color.match or fg
			elseif (notch_speed % (self.notch_every * 5)) < 0.00000001 then
				notch_ay = notch_ay_medium
				notch_color = config.color.time_current or fg
			end

			ass:rect(notch_x - notch_thickness, notch_ay, notch_x + notch_thickness, notch_by, {
				color = notch_color,
				opacity = math.min(1.2 - (math.abs((notch_x - ax - half_width) / half_width)), 1) * opacity,
			})
		end
	end

	-- Center guide
	ass:new_event()
	ass:append('{\\rDefault\\an7\\blur0\\bord0\\shad0\\1c&H' .. (config.color.match or fg) .. '}')
	ass:opacity(opacity)
	ass:pos(0, 0)
	ass:draw_start()
	ass:move_to(half_x, by - 2 - guide_size)
	ass:line_to(half_x + guide_size, by - 2)
	ass:line_to(half_x - guide_size, by - 2)
	ass:draw_stop()

	-- Speed value：居中显示在滑块视觉范围上方
	local speed_text = (round(state.speed * 100) / 100) .. ' x'
	local text_y = ay - round(4 * state.scale) - self.font_size / 2
	ass:txt(half_x, text_y, 5, speed_text, {
		size = self.font_size,
		color = config.color.time_current or bgt,
		border = options.text_border * state.scale,
		border_color = bg,
		opacity = opacity,
	})

	return ass
end

return Speed
