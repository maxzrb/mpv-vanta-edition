local Element = require('elements/Element')

---@alias ButtonProps {icon: string; on_click?: function; on_secondary_click?: function; is_clickable?: boolean; anchor_id?: string; active?: boolean; badge?: string|number; foreground?: string; background?: string; tooltip?: string}

---@class Button : Element
local Button = class(Element)

---@param id string
---@param props ButtonProps
function Button:new(id, props) return Class.new(self, id, props) --[[@as Button]] end
---@param id string
---@param props ButtonProps
function Button:init(id, props)
	self.icon = props.icon
	self.active = props.active
	self.tooltip = props.tooltip
	self.badge = props.badge
	self.foreground = props.foreground or fg
	self.background = props.background or bg
	self.is_clickable = true
	---@type fun()|nil
	self.on_click = props.on_click
	---@type fun()|nil
	self.on_secondary_click = props.on_secondary_click
	Element.init(self, id, props)
end

function Button:on_coordinates() self.font_size = round((self.by - self.ay) * 0.78) end
function Button:handle_cursor_click()
	if not self.on_click or not self.is_clickable then return end
	-- We delay the callback to next tick, otherwise we are risking race
	-- conditions as we are in the middle of event dispatching.
	-- For example, handler might add a menu to the end of the element stack, and that
	-- than picks up this click event we are in right now, and instantly closes itself.
	mp.add_timeout(0.01, self.on_click)
end

function Button:handle_cursor_secondary_click()
	if not self.on_secondary_click or not self.is_clickable then return end
	mp.add_timeout(0.01, self.on_secondary_click)
end

function Button:render()
	local visibility = self:get_visibility()
	if visibility <= 0 then return end
	cursor:zone('primary_click', self, function() self:handle_cursor_click() end)
	cursor:zone('secondary_click', self, function() self:handle_cursor_secondary_click() end)

	local ass = assdraw.ass_new()
	local is_clickable = self.is_clickable and self.on_click ~= nil
	local is_hover = self.proximity_raw <= 0
	local foreground = self.active and (config.color.accent_text or config.color.background) or self.foreground
	local background = self.active and config.color.match or self.background
	local background_opacity = self.active and 1 or config.opacity.controls

	if is_hover and is_clickable and background_opacity < 0.3 then background_opacity = 0.3 end

	-- Background
	if background_opacity > 0 then
		ass:rect(self.ax, self.ay, self.bx, self.by, {
			color = (self.active or not is_hover) and background or foreground,
			radius = state.radius,
			opacity = visibility * background_opacity,
		})
	end

	-- Tooltip on hover
	if is_hover and self.tooltip and options.button_tooltips ~= false then ass:tooltip(self, self.tooltip) end

	-- Icon
	local x, y = round(self.ax + (self.bx - self.ax) / 2), round(self.ay + (self.by - self.ay) / 2)
	ass:icon(x, y, self.font_size, self.icon, {
		color = foreground,
		border = self.active and 0 or options.text_border * state.scale,
		border_color = background,
		opacity = visibility,
	})

	-- 极简角标：只保留描边文字，避免透明小圆点糊成一团。
	if self.badge then
		local badge_font_size = self.font_size * 0.43
		local badge_opts = {
			size = badge_font_size,
			color = foreground,
			opacity = visibility,
			bold = true,
			border = self.active and 0 or math.max(1.2, state.scale * 1.2),
			border_color = config.color.background,
		}
		local badge_x = math.min(self.bx - badge_font_size * 0.15, x + self.font_size * 0.36)
		local badge_y = math.min(self.by - badge_font_size * 0.2, y + self.font_size * 0.34)
		ass:txt(badge_x, badge_y, 5, self.badge, badge_opts)
	end

	return ass
end

return Button
