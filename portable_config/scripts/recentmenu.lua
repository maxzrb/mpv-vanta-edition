local utils = require("mp.utils")
local options = require("mp.options")
local safe_file = dofile(mp.find_config_file('script-modules/safe-file.lua')
    or (mp.get_script_directory() .. '/../script-modules/safe-file.lua'))
local pending_updates = {}
local input_available, input = pcall(require, "mp.input")

local o = {
    enabled = true,
    path = "~~/recent.json",
    title = 'Recently played',
    length = 10,
    width = 88,
    ignore_same_series = true,
    reduce_io = false,
}
options.read_options(o, _, function() end)

local path = mp.command_native({ "expand-path", o.path })

local uosc_available = false
local command_palette_available = false

local is_windows = package.config:sub(1, 1) == "\\" -- detect path separator, windows uses backslashes

local menu = {
    type = 'recent_menu',
    title = o.title,
    items = {},
    item_actions = {
        {
            name = 'remove',
            icon = "delete",
            label = "Remove (del)",
        }
    },
    item_actions_place = "outside",
    callback = { mp.get_script_name(), "uosc-callback" }
}

local dyn_menu = {
    ready = false,
    script_name = 'dyn_menu',
    type = 'submenu',
    submenu = {}
}

local current_item = { nil, nil, nil }

local function parse_history(bytes)
    if bytes:sub(1, 3) == '\239\187\191' then bytes = bytes:sub(4) end
    local items = bytes == '' and {} or utils.parse_json(bytes)
    if type(items) ~= 'table' then return nil, '历史文件格式异常' end
    for key, item in pairs(items) do
        if type(key) ~= 'number' or key < 1 or key > #items or key % 1 ~= 0
            or type(item) ~= 'table' or type(item.value) ~= 'table'
            or item.value[1] ~= 'loadfile' or type(item.value[2]) ~= 'string'
            or type(item.title) ~= 'string' or (item.hint ~= nil and type(item.hint) ~= 'string') then
            return nil, '历史条目格式异常'
        end
    end
    return items
end

function utf8_char_bytes(str, i)
    local char_byte = str:byte(i)
    if char_byte < 0xC0 then
        return 1
    elseif char_byte < 0xE0 then
        return 2
    elseif char_byte < 0xF0 then
        return 3
    elseif char_byte < 0xF8 then
        return 4
    else
        return 1
    end
end

function utf8_iter(str)
    local byte_start = 1
    return function()
        local start = byte_start
        if #str < start then return nil end
        local byte_count = utf8_char_bytes(str, start)
        byte_start = start + byte_count
        return start, str:sub(start, start + byte_count - 1)
    end
end

function utf8_to_table(str)
    local t = {}
    for _, ch in utf8_iter(str) do
        t[#t + 1] = ch
    end
    return t
end

function utf8_substring(str, indexStart, indexEnd)
    if indexStart > indexEnd then
        return str
    end

    local index = 1
    local substr = ""
    for _, char in utf8_iter(str) do
        if indexStart <= index and index <= indexEnd then
            local width = #char > 2 and 2 or 1
            index = index + width
            substr = substr .. char
        end
    end
    return substr, index
end

function jaro(s1, s2)
    local match_window = math.floor(math.max(#s1, #s2) / 2.0) - 1
    local matches1 = {}
    local matches2 = {}

    local m = 0;
    local t = 0;

    for i = 0, #s1, 1 do
        local start = math.max(0, i - match_window)
        local final = math.min(i + match_window + 1, #s2)

        for k = start, final, 1 do
            if not (matches2[k] or s1[i] ~= s2[k]) then
                matches1[i] = true
                matches2[k] = true
                m = m + 1
                break
            end
        end
    end

    if m == 0 then
        return 0.0
    end

    local k = 0
    for i = 0, #s1, 1 do
        if matches1[i] then
            while not matches2[k] do
                k = k + 1
            end

            if s1[i] ~= s2[k] then
                t = t + 1
            end

            k = k + 1
        end
    end

    t = t / 2.0

    return (m / #s1 + m / #s2 + (m - t) / m) / 3.0
end

function jaro_winkler_distance(s1, s2)
    if #s1 + #s2 == 0 then
        return 0.0
    end

    if s1 == s2 then
        return 1.0
    end

    s1 = utf8_to_table(s1)
    s2 = utf8_to_table(s2)

    local d = jaro(s1, s2)
    local p = 0.1
    local l = 0;
    while (s1[l] == s2[l] and l < 4) do
        l = l + 1
    end

    return d + l * p * (1 - d)
end

function split_path(path)
    -- return path, filename, extension
    return path:match("(.-)([^\\/]-)%.?([^%.\\/]*)$")
end

function is_protocol(path)
    return type(path) == 'string' and (path:find('^%a[%w.+-]-://') ~= nil or path:find('^%a[%w.+-]-:%?') ~= nil)
end

function normalize(path)
    if normalize_path ~= nil then
        if normalize_path then
            path = mp.command_native({"normalize-path", path})
        else
            local directory = mp.get_property("working-directory", "")
            path = utils.join_path(directory, path:gsub('^%.[\\/]',''))
            if is_windows then path = path:gsub("\\", "/") end
        end
        return path
    end

    normalize_path = false

    local commands = mp.get_property_native("command-list", {})
    for _, command in ipairs(commands) do
        if command.name == "normalize-path" then
            normalize_path = true
            break
        end
    end
    return normalize(path)
end

function is_same_series(path1, path2)
    if not o.ignore_same_series then
        return false
    end

    local dir1, filename1, extension1 = split_path(path1)
    local dir2, filename2, extension2 = split_path(path2)

    -- don't remove files are not in same folder
    if dir1 ~= dir2 then
        return false
    end

    -- don't remove same filename but different extensions
    if filename1 == filename2 then
        return false
    end

    -- by episode
    local episode1 = filename1:gsub("^[%[%(]+.-[%]%)]+[%s%[]*", ""):match("(.-%D+)0*%d+")
    local episode2 = filename2:gsub("^[%[%(]+.-[%]%)]+[%s%[]*", ""):match("(.-%D+)0*%d+")
    if episode1 and episode2 and episode1 == episode2 then
        return true
    end

    -- by similarity
    local threshold = 0.8
    local similarity = jaro_winkler_distance(filename1, filename2)
    if similarity > threshold then
        return true
    end

    return false
end

function read_json(force)
    if o.reduce_io and not force then
        return
    end
    local json, err = safe_file.read(path)
    if json == nil then mp.msg.error('无法读取历史记录：' .. tostring(err)); return false end
    local items, parse_err = parse_history(json)
    if not items then mp.msg.error(parse_err .. '，原文件已保留'); return false end
    menu.items = items
    -- 临时离线、共享盘断开不会自动抹去记录；只在用户主动删除时移除。
    return true
end

function write_json(force)
    if o.reduce_io and not force then
        return
    end
    if #pending_updates == 0 then return true end
    local saved
    local ok, err = safe_file.update(path, function(bytes)
        local items, parse_err = parse_history(bytes)
        if not items then return nil, parse_err end
        for _, change in ipairs(pending_updates) do
            if change.kind == 'append' then
                local next_items = {change.item}
                for _, item in ipairs(items) do
                    if #next_items < o.length and item.value[2] ~= change.item.value[2]
                        and not is_same_series(change.item.value[2], item.value[2]) then
                        next_items[#next_items + 1] = item
                    end
                end
                items = next_items
            elseif change.kind == 'remove' then
                local found
                for index, item in ipairs(items) do
                    if item.value[2] == change.item.value[2] then
                        if item.title ~= change.item.title or item.hint ~= change.item.hint then
                            return nil, '所选记录已由其他实例更新，请刷新后再删除'
                        end
                        found = index
                        break
                    end
                end
                if found then table.remove(items, found) end
            end
        end
        saved = items
        local bom = bytes:sub(1, 3) == '\239\187\191' and '\239\187\191' or ''
        return bom .. utils.format_json(items)
    end)
    if not ok then
        mp.msg.error('历史保存失败，原记录已保留：' .. tostring(err))
        mp.osd_message('历史保存失败，原记录已保留；请稍后重试', 4)
        return false
    end
    menu.items, pending_updates = saved, {}

    if dyn_menu.ready then
        update_dyn_menu_items()
    end
    return true
end

function clip_uosc_menu_item(menu)
    local display_menu = {}
    for key, value in pairs(menu) do display_menu[key] = value end
    local menu_items = {}
    for _, item in ipairs(menu.items) do
        local display_item = {}
        for key, value in pairs(item) do display_item[key] = value end
        display_item.title = utf8_substring(item.title, 1, o.width)
        table.insert(menu_items, display_item)
    end
    display_menu.items = menu_items
    return display_menu
end

function append_item(path, title, hint)
    local new_items = { { title = title, hint = hint, value = { "loadfile", path } } }
    read_json()
    for index, value in ipairs(menu.items) do
        local opath = value.value[2]
        if #new_items < o.length and
            path ~= opath and
            not is_same_series(path, opath)
        then
            new_items[#new_items + 1] = value
        end
    end
    menu.items = new_items
    pending_updates[#pending_updates + 1] = {kind = 'append', item = new_items[1]}
    write_json()
end

function remove_item(index, value)
    local selected = menu.items[index]
    if type(value) == 'table' then
        selected = nil
        for _, item in ipairs(menu.items) do if item.value[2] == value[2] then selected = item; break end end
    end
    if not selected then return end
    pending_updates[#pending_updates + 1] = {kind = 'remove', item = selected}
    if not write_json(true) then
        pending_updates[#pending_updates] = nil
        return
    end
    local json = utils.format_json(clip_uosc_menu_item(menu))
    mp.commandv('script-message-to', 'uosc', 'update-menu', json)
end

function open_menu_uosc()
    local json = utils.format_json(clip_uosc_menu_item(menu))
    mp.commandv('script-message-to', 'uosc', 'open-menu', json)
end

function open_menu_command_palette()
    local json = utils.format_json(menu)
    mp.commandv('script-message-to',
        'command_palette',
        'show-command-palette-json', json)
end

function open_menu_select()
    local item_titles, item_values = {}, {}
    for i, v in ipairs(menu.items) do
        item_titles[i] = v.title
        item_values[i] = v.value
    end
    mp.commandv('script-message-to', 'console', 'disable')
    input.select({
        prompt = menu.title .. ':',
        items = item_titles,
        submit = function(id)
            mp.commandv(unpack(item_values[id]))
        end,
    })
end

function open_menu()
    read_json()
    if uosc_available then
        open_menu_uosc()
    elseif input_available then
        open_menu_select()
    elseif command_palette_available then
        open_menu_command_palette()
    else
        mp.msg.warn("No menu providers available")
    end
end

function update_dyn_menu_items()
    if #menu.items == 0 then
        read_json()
    end
    local submenu = {}
    local menu_items = menu.items
    for _, item in ipairs(menu_items) do
        submenu[#submenu + 1] = {
            title = string.format("%s\t%s", utf8_substring(item.title, 1, o.width), item.hint),
            cmd = string.format("%s \"%s\"", item.value[1], item.value[2]:gsub("\\", "\\\\")),
        }
    end
    dyn_menu.submenu = submenu
    mp.commandv('script-message-to', dyn_menu.script_name, 'update', 'recent', utils.format_json(dyn_menu))
end

function play_last()
    read_json()
    if menu.items[1] then
        mp.command_native(menu.items[1].value)
    end
end

function on_load()
    current_item = { nil, nil, nil }
    if not o.enabled then return end
    local path = mp.get_property("path")
    if not path then return end
    if not is_protocol(path) then path = normalize(path) end
    local dir, filename, extension = split_path(path)
    local title = mp.get_property("media-title"):gsub('%.([^%./]+)$', '')
    local hint = os.date("%m/%d %H:%M")
    if is_protocol(path) then
        local scheme = path:match("^(%a[%w.+-]-)://")
        if scheme == "bd" or
            scheme == "dvd" or
            scheme == "dvb" or
            scheme == "cdda"
        then
            return
        end
        hint = scheme .. " | " .. hint
    else
        if not title or #utf8_to_table(title) < #utf8_to_table(filename) then
            title = filename
        end
        hint = extension .. " | " .. hint
    end
    hint = hint:upper()
    current_item = { path, title, hint }
    append_item(unpack(current_item))
end

function on_end(e)
    if not (e and e.reason and e.reason == "quit") then
        return
    end
    if not current_item[1] then
        return
    end
    -- 退出只提交尚未保存的操作，避免旧实例重新顶置已过时的记录。
    write_json(true)
end

mp.add_key_binding(nil, "open", open_menu)
mp.add_key_binding(nil, "last", play_last)
mp.register_event("file-loaded", on_load)
mp.register_event("end-file", on_end)

mp.register_script_message('open-recent-menu', function(provider)
    if provider == nil then
        open_menu()
    elseif provider == "uosc" then
        open_menu_uosc()
    elseif provider == "command-palette" then
        open_menu_command_palette()
    elseif provider == "select" then
        open_menu_select()
    else
        mp.msg.warn(provider .. " not available")
    end
end)

mp.register_script_message('uosc-version', function()
    uosc_available = true
end)
mp.register_script_message('uosc-callback', function(json)
    local event = utils.parse_json(json)

    if event.type == "activate" and not event.action then
        mp.command_native(event.value)
        mp.commandv('script-message-to', 'uosc', 'close-menu', menu.type)
        return
    end

    if event.type == "activate" and event.action == "remove" then
        remove_item(event.index, event.value)
        return
    end

    if event.type == "key" and event.id == "del" then
        remove_item(event.selected_item.index, event.selected_item.value)
        return
    end
end)

mp.register_script_message('command-palette-version', function()
    command_palette_available = true
end)

mp.register_script_message('menu-ready', function(script_name)
    dyn_menu.ready = true
    dyn_menu.script_name = script_name
    update_dyn_menu_items()
end)

if o.reduce_io then
    read_json(true)
end
mp.register_event('shutdown', function() write_json(true) end)
