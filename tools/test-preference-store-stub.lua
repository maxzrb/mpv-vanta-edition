local M = {}
local values = {}

function M.restore(name)
    return values[name]
end

function M.set(name, value)
    values[name] = value
    return true
end

function M.valid()
    return true
end

return M
