local msg = require 'mp.msg'
local utils = require 'mp.utils'

local M = {}
local registry_cache = nil
local warned = {}

local function warn_once(key, text)
	if warned[key] then return end
	warned[key] = true
	msg.warn(text)
end

local function normalize_hex(value)
	if type(value) ~= 'string' then return nil end
	local normalized = value:gsub('^#', ''):upper()
	if not normalized:match('^[0-9A-F]+$') or (#normalized ~= 6 and #normalized ~= 8) then return nil end
	return normalized
end

local function load_registry()
	if registry_cache ~= nil then return registry_cache or nil end

	local path = mp.command_native({'expand-path', '~~/script-opts/uosc-themes.json'})
	local file = io.open(path, 'rb')
	if not file then
		registry_cache = false
		warn_once('missing', '未找到共享主题注册表：' .. path)
		return nil
	end

	local content = file:read('*a')
	file:close()
	local registry, parse_error = utils.parse_json(content)
	if type(registry) ~= 'table' or type(registry.palettes) ~= 'table' then
		registry_cache = false
		warn_once('invalid', '无法解析共享主题注册表：' .. tostring(parse_error or path))
		return nil
	end

	registry_cache = registry
	return registry
end

---@param palette table
---@return table|nil
local function normalize_palette(palette)
	if type(palette) ~= 'table' or type(palette.id) ~= 'string' or type(palette.name) ~= 'string' then
		return nil
	end
	local accent = normalize_hex(palette.accent)
	local accent_text = normalize_hex(palette.accentText)
	if not accent or not accent_text then return nil end
	return {
		id = palette.id,
		name = palette.name,
		description = palette.description or '',
		accent = accent,
		accent_text = accent_text,
	}
end

---@param selected_id string
---@return table|nil
function M.get(selected_id)
	local registry = load_registry()
	if not registry then return nil end

	local fallback_id = type(registry.default) == 'string' and registry.default or nil
	local selected, fallback = nil, nil
	for _, candidate in ipairs(registry.palettes) do
		local palette = normalize_palette(candidate)
		if palette then
			if palette.id == selected_id then selected = palette end
			if palette.id == fallback_id then fallback = palette end
		end
	end

	if selected then return selected end
	if selected_id and selected_id ~= '' then
		warn_once('unknown:' .. selected_id, '未知 uosc 主题：' .. selected_id .. '，已使用注册表默认主题。')
	end
	return fallback
end

---@param palette table|nil
---@return table
function M.to_color_overrides(palette)
	if not palette then return {} end
	return {
		accent = palette.accent,
		accent_text = palette.accent_text,
		match = palette.accent,
		heatmap = palette.accent,
		menu_selection = palette.accent,
		menu_active = palette.accent,
		menu_title = palette.accent,
		menu_title_text = palette.accent_text,
		chapter = palette.accent,
	}
end

return M
