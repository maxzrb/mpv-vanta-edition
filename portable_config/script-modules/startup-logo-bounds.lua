--[[
  * startup-logo-bounds.lua
  * 起播格式徽章专用：检测视频帧中实际编码的对称上下/左右黑边，并合并多帧结果。
  * 来源：杳知 mpv 整合包（Yaozhil/mpv-Yaozhi，MIT License）8.11/8.12「特殊画幅与黑边起播徽章优化」。
  * 相比旧版单帧 + 画幅白名单方案，本模块直接按像素检测黑边，去掉固定画幅白名单，
  * 通过多帧中位数合并降低全黑首帧、片头渐变与瞬时画面造成的误判；
  * 8.12 起额外返回 16×9 网格画面覆盖率，供调用方判断"全黑/片头 Logo 等低覆盖开场"
  * 并安排少量延迟复检，避免把稀疏开场误锁成徽章锚点。
]]

local M = {}

local function clamp(value, low, high)
    return math.max(low, math.min(high, value))
end

local function median(values)
    table.sort(values)
    local count = #values
    if count == 0 then return 0 end
    if count % 2 == 1 then return values[(count + 1) / 2] end
    return (values[count / 2] + values[count / 2 + 1]) / 2
end

---Detect symmetric encoded letterbox/pillarbox bars in a BGR0 frame.
---@param frame table
---@param threshold number
---@return table|nil insets
---@return boolean meaningful 画面是否具有足够内容（非全黑/稀疏开场）
---@return number coverage 16×9 网格亮像素覆盖率 0~1
function M.detect(frame, threshold)
    if type(frame) ~= 'table' or frame.format ~= 'bgr0'
        or type(frame.data) ~= 'string' then return nil end
    local width = tonumber(frame.w) or 0
    local height = tonumber(frame.h) or 0
    local stride = tonumber(frame.stride) or width * 4
    if width < 320 or height < 180 or stride < width * 4 then return nil end

    local data = frame.data
    threshold = clamp(math.floor(tonumber(threshold) or 16), 0, 48)
    local samples = 64
    local max_bright = math.floor(samples * 0.12)

    local function pixel_is_bright(x, y)
        local offset = y * stride + x * 4 + 1
        local blue, green, red = data:byte(offset, offset + 2)
        return not blue or math.max(blue, green, red) > threshold
    end

    local function line_is_black(length, point_at)
        local bright = 0
        for index = 0, samples - 1 do
            -- Ignore the outermost 5%, where the other bar orientation and
            -- rounded mastering edges can otherwise contaminate the probe.
            local position = math.min(length - 1, math.floor((0.05 + (index + 0.5) * 0.90 / samples) * length))
            local x, y = point_at(position)
            if pixel_is_bright(x, y) then
                bright = bright + 1
                if bright > max_bright then return false end
            end
        end
        return true
    end

    local function row_is_black(y)
        return line_is_black(width, function(x) return x, y end)
    end
    local function column_is_black(x)
        return line_is_black(height, function(y) return x, y end)
    end
    local function scan_edges(length, check)
        local step = math.max(1, math.floor(length / 720))
        local limit = math.floor(length * 0.30)
        local first = 0
        while first < limit and check(first) do first = first + step end
        local last = 0
        while last < limit and check(length - 1 - last) do last = last + step end
        return math.min(first, limit), math.min(last, limit)
    end
    local function symmetric(a, b, length)
        return a >= length * 0.012 and b >= length * 0.012
            and math.abs(a - b) <= math.max(12, length * 0.025)
            and length - a - b >= length * 0.40
    end

    local top, bottom = scan_edges(height, row_is_black)
    local left, right = scan_edges(width, column_is_black)
    local insets = {left = 0, top = 0, right = 0, bottom = 0}
    local found = false

    -- 全黑开场、片头 Logo 等稀疏画面不足以锁定徽章位置：把采样画面覆盖率
    -- 返回给调用方，让它安排少量廉价复检，而不是延迟普通全帧内容的起播。
    local grid_columns, grid_rows = 16, 9
    local bright_points = 0
    for row = 0, grid_rows - 1 do
        local y = math.min(height - 1, math.floor((row + 0.5) * height / grid_rows))
        for column = 0, grid_columns - 1 do
            local x = math.min(width - 1, math.floor((column + 0.5) * width / grid_columns))
            if pixel_is_bright(x, y) then bright_points = bright_points + 1 end
        end
    end
    local coverage = bright_points / (grid_columns * grid_rows)
    local meaningful = coverage >= 0.06

    if symmetric(top, bottom, height)
        and not row_is_black(math.min(height - 1, top + math.max(2, math.floor(height * 0.004))))
        and not row_is_black(math.max(0, height - 1 - bottom - math.max(2, math.floor(height * 0.004)))) then
        insets.top, insets.bottom = top / height, bottom / height
        found = true
    end
    if symmetric(left, right, width)
        and not column_is_black(math.min(width - 1, left + math.max(2, math.floor(width * 0.004))))
        and not column_is_black(math.max(0, width - 1 - right - math.max(2, math.floor(width * 0.004)))) then
        insets.left, insets.right = left / width, right / width
        found = true
    end

    return found and insets or nil, meaningful, coverage
end

---Merge several successful probes without letting a single fade frame win.
---@param probes table[]
---@return table|nil
function M.merge(probes)
    if type(probes) ~= 'table' or #probes == 0 then return nil end
    local values = {left = {}, top = {}, right = {}, bottom = {}}
    for _, probe in ipairs(probes) do
        for side in pairs(values) do
            values[side][#values[side] + 1] = tonumber(probe[side]) or 0
        end
    end
    return {
        left = median(values.left),
        top = median(values.top),
        right = median(values.right),
        bottom = median(values.bottom),
    }
end

return M
