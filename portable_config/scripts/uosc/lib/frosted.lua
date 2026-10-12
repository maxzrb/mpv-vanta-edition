-- 菜单材质按标准非线性混合拟合，只改变 ASS 图层，不写视频或输出色彩选项。
local M = {}
local background_cache, noise_cache = {}, {}
local background_count, noise_count = 0, 0

local function srgb_decode(v)
	return v <= 0.04045 and v / 12.92 or ((v + 0.055) / 1.055) ^ 2.4
end

local function srgb_encode(v)
	v = math.max(0, v)
	return v <= 0.0031308 and 12.92 * v or 1.055 * v ^ (1 / 2.4) - 0.055
end

local function decode(v, trc, black)
	if trc == 'srgb' then return srgb_decode(v) end
	local gamma = tonumber((trc or ''):match('^gamma([%d.]+)$')) or 2.4
	if trc == 'bt.1886' then
		local toe = black ^ (1 / gamma)
		return ((1 - toe) * v + toe) ^ gamma
	end
	return math.max(0, v) ^ gamma
end

local function encode(v, trc, black)
	if trc == 'srgb' then return srgb_encode(v) end
	local gamma = tonumber((trc or ''):match('^gamma([%d.]+)$')) or 2.4
	if trc == 'bt.1886' then
		local toe = black ^ (1 / gamma)
		return math.max(0, (math.max(0, v) ^ (1 / gamma) - toe) / (1 - toe))
	end
	return math.max(0, v) ^ (1 / gamma)
end

local function channel(color, index)
	-- ASS 颜色为 BBGGRR，不可按配置文件中的 RRGGBB 顺序读取。
	return (tonumber(color:sub(index, index + 1), 16) or 0) / 255
end

local function is_linear(target)
	return target and target.pipeline ~= 'standard' and (not target.primaries or target.primaries == 'bt.709')
		and (target.gamma == 'scrgb' or target.gamma == 'linear')
end

local function reference(standard)
	standard = standard or {gamma='bt.1886', black=0.203 / 80}
	return standard.gamma or 'bt.1886', math.max(0, math.min(0.1, standard.black or 0.203 / 80))
end

local function supported_reference(standard)
	local gamma = standard and standard.gamma or 'bt.1886'
	return gamma == 'bt.1886' or gamma == 'srgb' or gamma:match('^gamma[%d.]+$') ~= nil
end

function M.curtain_range(color, opacity, standard)
	local trc, black = reference(standard)
	local alpha = math.ceil(math.max(0, math.min(1, opacity)) * 255) / 255
	local highs = {}
	for index = 1, 5, 2 do
		local c = encode(black + (1 - black) * srgb_decode(channel(color, index)), trc, black)
		highs[#highs + 1] = decode(alpha * c + (1 - alpha), trc, black)
	end
	return black, highs
end

function M.background_style(color, opacity, target, standard, lower, upper, video_input)
	if not is_linear(target) or not supported_reference(standard) or opacity <= 0 then return color, opacity end
	local trc, black = reference(standard)
	local original_alpha = math.ceil(math.min(1, opacity) * 255) / 255
	lower = lower or 0
	upper = upper or {1, 1, 1}
	local key = table.concat({color, tostring(original_alpha), trc, tostring(black), tostring(lower),
		tostring(upper[1]), tostring(upper[2]), tostring(upper[3]), tostring(video_input)}, '|')
	local cached = background_cache[key]
	if cached then return cached[1], cached[2] end
	local models, slope = {}, 0
	-- ASS 共用一个 alpha；以感知均匀的背景样本拟合，避免只适配黑屏。
	for n, index in ipairs({1, 3, 5}) do
		local ui = encode(black + (1 - black) * srgb_decode(channel(color, index)), trc, black)
		local function wanted(q)
			local physical = video_input and (black + (1 - black) * q) or q
			return decode(original_alpha * ui + (1 - original_alpha) * encode(physical, trc, black), trc, black)
		end
		local top = math.max(lower + 0.0001, upper[n])
		local anchor, numerator, denominator, mean = wanted(lower), 0, 0, 0
		for sample = 0, 8 do
			local q = lower + (top - lower) * srgb_decode(sample / 8)
			local delta = q - lower
			numerator = numerator + delta * (wanted(q) - anchor)
			denominator = denominator + delta * delta
			mean = mean + q / 9
		end
		local b = numerator / math.max(0.000001, denominator)
		models[n] = {a=anchor - b * lower, b=b, mean=mean}
		-- ASS 为 BGR，亮度权重按对应顺序使用。
		slope = slope + b * ({0.0722, 0.7152, 0.2126})[n]
	end
	local alpha = math.max(1, math.min(255, math.ceil((1 - slope) * 255))) / 255
	local result = {}
	for _, model in ipairs(models) do
		local a = model.a + (model.b - (1 - alpha)) * model.mean
		local value = math.max(0, math.min(1, srgb_encode(a / alpha)))
		result[#result + 1] = string.format('%02X', math.floor(value * 255 + 0.5))
	end
	local output = table.concat(result)
	-- 动画只产生有限材质；有界缓存避免静止菜单每次重算曲线，也不随播放时长增长。
	if background_count >= 64 then background_cache, background_count = {}, 0 end
	background_cache[key], background_count = {output, alpha}, background_count + 1
	return output, alpha
end

function M.noise_style(foreground, background, opacity, strength, target, standard, adjusted_bg, adjusted_alpha)
	-- 非线性输出和标准模式保留原纹理；只处理当前实际线性工作空间。
	if not is_linear(target) or not supported_reference(standard) or strength <= 0 then
		return foreground, strength
	end
	local trc, black = reference(standard)
	local key = table.concat({foreground, background, tostring(opacity), tostring(strength), trc,
		tostring(black), tostring(adjusted_bg), tostring(adjusted_alpha)}, '|')
	local cached = noise_cache[key]
	if cached then return cached[1], cached[2] end
	local channels = {}
	local alpha_min = 0
	for index = 1, 5, 2 do
		local b = srgb_decode(channel(background, index))
		local f = srgb_decode(channel(foreground, index))
		-- 参考标准输出的编码混合；透明面板按暗背景估计，保留原纹理和透明度。
		local ref_b = encode(black + (1 - black) * b, trc, black) * opacity
		local ref_f = encode(black + (1 - black) * f, trc, black)
		local ref_plain = decode(ref_b, trc, black)
		local ref_grain = decode(ref_b + strength * (ref_f - ref_b), trc, black)
		local contrast = srgb_encode(ref_grain) - srgb_encode(ref_plain)
		local linear_plain = b * opacity
		if adjusted_bg then
			linear_plain = srgb_decode(channel(adjusted_bg, index)) * adjusted_alpha + black * (1 - adjusted_alpha)
		end
		local desired = srgb_decode(math.max(0, srgb_encode(linear_plain) + contrast))
		local delta = desired - linear_plain
		channels[#channels + 1] = {plain=linear_plain, delta=delta}
		-- 深色噪点同样保留极性，不能把浅色主题上的暗纹理截成零。
		local required = delta >= 0 and delta / math.max(0.001, 1 - linear_plain)
			or -delta / math.max(0.001, linear_plain)
		alpha_min = math.max(alpha_min, required)
	end
	-- 先选能表达所有通道的整数 alpha，再调整颜色；较低 alpha 可减轻透出画面变化的影响。
	local alpha = math.max(1, math.min(255, math.ceil(alpha_min * 255))) / 255
	local result = {}
	for _, c in ipairs(channels) do
		local corrected = c.plain + c.delta / alpha
		local value = math.max(0, math.min(1, srgb_encode(corrected)))
		result[#result + 1] = string.format('%02X', math.floor(value * 255 + 0.5))
	end
	local output = table.concat(result)
	if noise_count >= 64 then noise_cache, noise_count = {}, 0 end
	noise_cache[key], noise_count = {output, alpha}, noise_count + 1
	return output, alpha
end

return M
