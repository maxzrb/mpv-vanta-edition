--[[
 * window-size-position.lua
 * 窗口大小/位置默认设置 + 记住上次关闭时的窗口大小/位置（可分别开关）
 * + 窗口置顶状态持久化。
 * 默认设置写入 script-opts/window_size_position.conf；
 * 上次窗口状态写入 script-opts/window_state.conf（自动维护）。
 * Windows 下用 LuaJIT ffi 调用 Win32 API 读取窗口矩形。
]]

local msg = require 'mp.msg'
local options = require 'mp.options'
local input_loaded, input = pcall(require, 'mp.input')

local o = {
	size = 'auto',
	position = 'auto',
	remember_size = true,
	remember_position = true,
}
options.read_options(o, 'window_size_position')

local config_path = mp.command_native({
	'expand-path',
	'~~/script-opts/window_size_position.conf',
})
local state_path = mp.command_native({
	'expand-path',
	'~~/script-opts/window_state.conf',
})

-- 启动时 mpv.conf 里的 geometry（“自动”时恢复它）
local startup_geometry = mp.get_property('geometry') or ''

-- ---- Win32 API（Windows + LuaJIT 才可用） ----
local ffi_ok, ffi = pcall(require, 'ffi')
local user32, dwmapi, win_api = nil, nil, false
if ffi_ok then
	local ok1, u = pcall(ffi.load, 'user32')
	local ok2, d = pcall(ffi.load, 'dwmapi')
	if ok1 and ok2 then
		user32, dwmapi = u, d
		local ok_cdef = pcall(function()
			ffi.cdef[[
				typedef struct { long left; long top; long right; long bottom; } RECT;
				int GetWindowRect(void* hWnd, RECT* lpRect);
				int GetClientRect(void* hWnd, RECT* lpRect);
				int DwmGetWindowAttribute(void* hwnd, unsigned int dwAttribute, void* pvAttribute, unsigned int cbAttribute);
				unsigned GetDpiForWindow(void* hWnd);
				unsigned GetDpiForSystem(void);
				int GetSystemMetrics(int nIndex);
			]]
		end)
		win_api = ok_cdef
	end
end
local DWMWA_EXTENDED_FRAME_BOUNDS = 9
local SM_XVIRTUALSCREEN = 76
local SM_YVIRTUALSCREEN = 77
local SM_CXVIRTUALSCREEN = 78
local SM_CYVIRTUALSCREEN = 79

local state = nil
local positioned = false
local restore_timer, save_timer
local stopping = false

local function osd_show(text)
	mp.osd_message(text, 2.5)
end

local function prop_bool(name)
	local ok, v = pcall(mp.get_property_bool, name)
	return ok and v or false
end

local function normalize_size(value)
	value = tostring(value or ''):lower():gsub('^%s+', ''):gsub('%s+$', '')
	if value == '' or value == 'auto' then return 'auto' end
	return value
end

local function normalize_position(value)
	value = tostring(value or ''):lower():gsub('^%s+', ''):gsub('%s+$', '')
	if value == '' or value == 'auto' then return 'auto' end
	if value == 'center' then return 'center' end
	return value
end

o.size = normalize_size(o.size)
o.position = normalize_position(o.position)

local function normalize_bool(value, default)
	if type(value) == 'boolean' then return value end
	local v = tostring(value or ''):lower()
	if v == 'yes' or v == 'true' or v == '1' or v == 'on' then return true end
	if v == 'no' or v == 'false' or v == '0' or v == 'off' then return false end
	return default
end

o.remember_size = normalize_bool(o.remember_size, true)
o.remember_position = normalize_bool(o.remember_position, true)

-- ---- 窗口置顶：显式配置后持久化，未配置时跟随 mpv.conf ----
local ontop_configured = false
local ontop_value = false

local function load_ontop_option()
	local file = config_path and io.open(config_path, 'rb')
	if not file then return end
	local content = file:read('*a')
	file:close()
	if not content then return end
	for line in content:gmatch('[^\r\n]+') do
		local v = line:match('^ontop%s*=%s*(.-)%s*$')
		if v then
			ontop_configured = true
			ontop_value = normalize_bool(v, false)
		end
	end
end

local function apply_ontop()
	if ontop_configured then
		local ok = pcall(mp.set_property_bool, 'ontop', ontop_value)
		if ok then
			msg.info('已恢复窗口置顶：' .. (ontop_value and '开' or '关'))
		end
	end
end

-- ---- 状态文件读写 ----
local function read_state()
	if not state_path then return nil end
	local file = io.open(state_path, 'rb')
	if not file then return nil end
	local content = file:read('*a')
	file:close()
	if not content then return nil end
	local rect, client, dpi, frame = nil, nil, nil, nil
	for line in content:gmatch('[^\r\n]+') do
		local key, value = line:match('^([%w_]+)=(.*)$')
		if key and value then
			if key == 'rect' then
				local l, t, r, b = value:match('^(%-?%d+),(%-?%d+),(%-?%d+),(%-?%d+)$')
				if l and tonumber(r) > tonumber(l) and tonumber(b) > tonumber(t) then
					rect = {
						left = tonumber(l),
						top = tonumber(t),
						right = tonumber(r),
						bottom = tonumber(b),
					}
				end
			elseif key == 'client' then
				local w, h = value:match('^(%d+),(%d+)$')
				if w and tonumber(w) > 0 and tonumber(h) > 0 then
					client = { w = tonumber(w), h = tonumber(h) }
				end
			elseif key == 'frame' then
				local x, y = value:match('^(%-?%d+),(%-?%d+)$')
				if x then frame = { left = tonumber(x), top = tonumber(y) } end
			elseif key == 'dpi' then
				local v = tonumber(value)
				if v and v > 0 then dpi = v end
			end
		end
	end
	if rect and client then
		return { rect = rect, client = client, dpi = dpi or 96, frame = frame }
	end
	return nil
end

state = read_state()

local function persist()
	local file = config_path and io.open(config_path, 'wb')
	if not file then
		msg.error('无法保存窗口设置：' .. tostring(config_path))
		return false
	end
	file:write('# 窗口大小默认值：auto 或具体尺寸（如 1280x720）\n')
	file:write(string.format('size=%s\n', o.size))
	file:write('# 窗口位置默认值：auto / center / 位置（如 +0+220）\n')
	file:write(string.format('position=%s\n', o.position))
	file:write('# 记住上次关闭时的窗口大小：yes / no\n')
	file:write(string.format('remember_size=%s\n', o.remember_size and 'yes' or 'no'))
	file:write('# 记住上次关闭时的窗口位置：yes / no\n')
	file:write(string.format('remember_position=%s\n', o.remember_position and 'yes' or 'no'))
	file:write('# 窗口置顶：yes / no（切换后自动保存）\n')
	file:write(string.format('ontop=%s\n', ontop_value and 'yes' or 'no'))
	file:close()
	return true
end

local function write_state(rect, client, dpi, frame)
	local file = state_path and io.open(state_path, 'wb')
	if not file then return false end
	file:write('# 上次关闭时的窗口状态（由 window-size-position.lua 自动维护）\n')
	file:write(string.format('rect=%d,%d,%d,%d\n', rect.left, rect.top, rect.right, rect.bottom))
	file:write(string.format('client=%d,%d\n', client.w, client.h))
	file:write(string.format('dpi=%d\n', dpi or 96))
	if frame then
		file:write(string.format('frame=%d,%d\n', frame.left, frame.top))
	end
	file:close()
	return true
end

-- ---- 窗口状态采样 ----
local function get_window_state()
	if not win_api then return nil end
	local wid = mp.get_property_number('window-id', 0)
	if not wid or wid <= 0 then return nil end
	-- 全屏/最大化/最小化时不保存，避免把非正常窗口状态记下来
	if prop_bool('fullscreen') or prop_bool('window-maximized') or prop_bool('window-minimized') then
		return nil
	end
	local hwnd = ffi.cast('void*', wid)
	local rect = ffi.new('RECT')
	if user32.GetWindowRect(hwnd, rect) == 0 then return nil end
	local crect = ffi.new('RECT')
	if user32.GetClientRect(hwnd, crect) == 0 then return nil end
	if rect.right <= rect.left or rect.bottom <= rect.top then return nil end
	if crect.right <= 0 or crect.bottom <= 0 then return nil end
	local dpi = 96
	if user32.GetDpiForWindow then
		local ok, v = pcall(user32.GetDpiForWindow, hwnd)
		if ok and v and v > 0 then dpi = v end
	end
	-- 保存不可见边框偏移，下次创建窗口前即可还原可见位置。
	local ext = ffi.new('RECT')
	local frame
	if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ext, ffi.sizeof(ext)) == 0 then
		frame = { left = ext.left - rect.left, top = ext.top - rect.top }
	end
	return {
		frame = frame,
		rect = {
			left = rect.left,
			top = rect.top,
			right = rect.right,
			bottom = rect.bottom,
		},
		client = { w = crect.right, h = crect.bottom },
		dpi = dpi,
	}
end

local function save_current_state()
	if not (o.remember_size or o.remember_position) then return end
	local current = get_window_state()
	if current then
		write_state(current.rect, current.client, current.dpi, current.frame)
	end
end

-- ---- 恢复上次窗口状态 ----
local function current_frame_deltas()
	if not win_api then return nil end
	local wid = mp.get_property_number('window-id', 0)
	if not wid or wid <= 0 then return nil end
	local hwnd = ffi.cast('void*', wid)
	local rect = ffi.new('RECT')
	if user32.GetWindowRect(hwnd, rect) == 0 then return nil end
	local ext = ffi.new('RECT')
	if dwmapi.DwmGetWindowAttribute(
		hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ext, ffi.sizeof(ext)
	) ~= 0 then
		return nil
	end
	-- geometry 位置按“可见框”计算，GetWindowRect 含不可见边框，差值需动态测量
	return { left = ext.left - rect.left, top = ext.top - rect.top }
end

local function current_dpi()
	if not win_api then return nil end
	local wid = mp.get_property_number('window-id', 0)
	-- 窗口尚未创建时沿用保存的 DPI，避免先按 96 DPI 缩小、显示后又放大。
	if not wid or wid <= 0 then return state and state.dpi or user32.GetDpiForSystem() end
	if not user32.GetDpiForWindow then return 96 end
	local ok, v = pcall(user32.GetDpiForWindow, ffi.cast('void*', wid))
	if ok and v and v > 0 then return v end
	return 96
end

-- 保存的客户区尺寸按 DPI 换算为当前 geometry 尺寸
local function saved_size_string()
	if not (state and state.client) then return nil end
	local cur_dpi = current_dpi() or 96
	local ratio = cur_dpi / (state.dpi and state.dpi > 0 and state.dpi or cur_dpi)
	local w = math.max(1, math.floor(state.client.w * ratio + 0.5))
	local h = math.max(1, math.floor(state.client.h * ratio + 0.5))
	return w .. 'x' .. h
end

-- 保存的外框矩形按 DPI 换算并补偿不可见边框，得到 geometry 位置
local function saved_position_string()
	if not (state and state.rect) then return nil end
	local cur_dpi = current_dpi() or 96
	local ratio = cur_dpi / (state.dpi and state.dpi > 0 and state.dpi or cur_dpi)
	local deltas = current_frame_deltas()
	if not deltas and state.frame then
		deltas = { left = math.floor(state.frame.left * ratio + 0.5),
			top = math.floor(state.frame.top * ratio + 0.5) }
	end
	if not deltas then return nil end
	local left = math.floor(state.rect.left * ratio + 0.5)
	local top = math.floor(state.rect.top * ratio + 0.5)
	local right = math.floor(state.rect.right * ratio + 0.5)
	local bottom = math.floor(state.rect.bottom * ratio + 0.5)
	if user32.GetSystemMetrics then
		local vsx = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
		local vsy = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
		local vsw = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
		local vsh = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
		local ix = math.max(left, vsx)
		local iy = math.max(top, vsy)
		local ir = math.min(right, vsx + vsw)
		local ib = math.min(bottom, vsy + vsh)
		-- 屏幕布局变化导致原位置完全不可见：退化为居中
		if ir <= ix or ib <= iy then
			return '+50%+50%'
		end
	end
	return '+' .. (left + deltas.left) .. '+' .. (top + deltas.top)
end

local function default_size_string()
	if o.size == 'auto' then return nil end
	return o.size
end

local function default_position_string()
	if o.position == 'center' then return '+50%+50%' end
	if o.position == 'auto' then return nil end
	return o.position
end

-- 优先用保存的边框补偿一次组合尺寸和位置；旧状态没有补偿值时仅延后位置。
local function build_combined_geometry()
	local size
	if o.remember_size then size = saved_size_string() end
	if not size then size = default_size_string() end
	local position
	if o.remember_position then
		position = saved_position_string()
	else
		position = default_position_string()
	end
	if not size and not position then return nil end
	return (size or '') .. (position or '')
end

local function apply_remembered()
	-- 不能把只恢复了尺寸误判为位置也已就绪。
	if o.remember_position and not saved_position_string() then return false end
	local geometry = build_combined_geometry()
	if not geometry then return false end
	local ok = true
	-- 创建前已恢复且 DPI／边框未变时，不再写入同一 geometry。
	if mp.get_property('geometry') ~= geometry then
		ok = mp.set_property('geometry', geometry)
	end
	if ok then
		positioned = true
		msg.info('已恢复上次窗口状态：' .. geometry)
	end
	return ok
end

local function retry_apply_remembered(tries)
	if stopping or positioned or not (o.remember_size or o.remember_position) then return end
	if apply_remembered() then return end
	if tries < 6 then
		if restore_timer then restore_timer:kill() end
		restore_timer = mp.add_timeout(0.5, function()
			restore_timer = nil
			retry_apply_remembered(tries + 1)
		end)
	end
end

-- ---- 默认设置（size / position） ----
-- 组合 geometry：尺寸 + 位置；center 使用 mpv 百分比居中（自动测算）
local function build_geometry()
	local size, position = o.size, o.position
	if size == 'auto' and position == 'auto' then return nil end
	if position == 'center' then
		return size == 'auto' and '50%:50%' or (size .. '+50%+50%')
	end
	if size == 'auto' then return position end
	if position == 'auto' then return size end
	return size .. position
end

-- 直接应用默认设置（菜单里明确选择尺寸/位置时使用）
local function apply_defaults()
	local geometry = build_geometry()
	local ok
	if geometry then
		ok = pcall(mp.set_property, 'geometry', geometry)
	else
		ok = pcall(mp.set_property, 'geometry', startup_geometry or '')
	end
	if not ok then
		msg.warn('应用窗口设置失败')
		osd_show('窗口设置应用失败')
	end
	positioned = true
end

local function apply()
	positioned = false
	if win_api and state and (o.remember_size or o.remember_position) then
		-- 在首次显示前恢复几何；窗口出现后仅校正实际发生变化的 DPI／边框。
		local geometry = build_combined_geometry()
		if geometry then
			pcall(mp.set_property, 'geometry', geometry)
		end
		if not o.remember_position and mp.get_property_number('window-id', 0) > 0 then
			positioned = true
		end
		return
	end
	apply_defaults()
end

local function apply_and_persist(label)
	apply_defaults()
	persist()
	osd_show(label .. '：' .. (build_geometry() or '系统默认'))
end

local function custom_input(kind, prompt, placeholder)
	if not input_loaded then
		osd_show('自定义输入不可用（缺少 mp.input）')
		return
	end
	input.get({
		prompt = prompt,
		default_text = placeholder or '',
		submit = function(text)
			input.terminate()
			text = tostring(text or ''):gsub('^%s+', ''):gsub('%s+$', '')
			if text == '' then return end
			if kind == 'size' then
				-- 尺寸只接受 WxH（可带百分比），不允许再带位置
				if text:find('[%+%-]') then
					osd_show('窗口大小只能输入尺寸，例如 1280x720')
					return
				end
				o.size = normalize_size(text)
			else
				o.position = normalize_position(text)
			end
			apply_and_persist(kind == 'size' and '窗口大小' or '窗口位置')
		end,
		closed = function() end,
	})
end

mp.register_script_message('set-size', function(value)
	value = normalize_size(value)
	o.size = value
	apply_and_persist('窗口大小')
end)

mp.register_script_message('set-position', function(value)
	value = normalize_position(value)
	o.position = value
	apply_and_persist('窗口位置')
end)

local function toggle_remember(kind, value)
	local v = tostring(value or ''):lower()
	local on = v == 'yes' or v == 'true' or v == '1' or v == 'on'
	if kind == 'size' then
		o.remember_size = on
	else
		o.remember_position = on
	end
	persist()
	pcall(mp.set_property_bool, 'user-data/window-size-position/remember-' .. kind, on)
	local label = kind == 'size' and '记住上次窗口大小' or '记住上次窗口位置'
	osd_show(label .. '：' .. (on and '开' or '关'))
	if on then
		apply()
		if o.remember_position then
			retry_apply_remembered(0)
		end
	end
end

mp.register_script_message('set-remember-size', function(value)
	toggle_remember('size', value)
end)

mp.register_script_message('set-remember-position', function(value)
	toggle_remember('position', value)
end)

mp.register_script_message('toggle-remember-size', function()
	toggle_remember('size', o.remember_size and 'no' or 'yes')
end)

mp.register_script_message('toggle-remember-position', function()
	toggle_remember('position', o.remember_position and 'no' or 'yes')
end)

mp.register_script_message('custom-size', function()
	custom_input('size', '输入窗口大小（例如 1280x720）', o.size ~= 'auto' and o.size or '1280x720')
end)

mp.register_script_message('custom-position', function()
	custom_input(
		'position',
		'输入窗口位置（例如 +0+220，center 为居中）',
		o.position ~= 'auto' and o.position or '+0+220'
	)
end)

-- 发布菜单勾选状态
pcall(mp.set_property_bool, 'user-data/window-size-position/remember-size', o.remember_size)
pcall(mp.set_property_bool, 'user-data/window-size-position/remember-position', o.remember_position)

-- 启动时应用持久化设置
load_ontop_option()
apply()
apply_ontop()

-- 任何方式切换置顶（快捷键/菜单/脚本）都自动保存
mp.observe_property('ontop', 'bool', function(name, value)
	ontop_configured = true
	ontop_value = value == true
	persist()
end)

-- 窗口出现后检查 DPI／边框变化，旧记录只需首次补齐位置。
mp.observe_property('window-id', 'number', function(name, value)
	if (o.remember_size or o.remember_position) and win_api and state and not positioned and value and value > 0 then
		retry_apply_remembered(0)
	end
end)

-- 周期保存当前窗口状态，退出时再精确保存一次
save_timer = mp.add_periodic_timer(2.0, save_current_state)
mp.register_event('shutdown', function()
	stopping = true
	if restore_timer then restore_timer:kill(); restore_timer = nil end
	save_timer:kill()
	save_current_state()
end)

return {}
