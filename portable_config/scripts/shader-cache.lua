-- 缓存清理菜单仅安排退出后的维护，不改核心或正在使用的着色器。
-- License: MIT
local mp = require 'mp'
local msg = require 'mp.msg'
local utils = require 'mp.utils'
local safe_ok, safe = pcall(function()
    local path = mp.find_config_file('script-modules/safe-file.lua')
    if not path then error('找不到可选的可靠读取模块') end
    return dofile(path)
end)
safe_ok = safe_ok and type(safe) == 'table' and type(safe.read) == 'function'
local config = mp.command_native({'expand-path', '~~/'})
local helper = utils.join_path(config, '../installer/clear-shader-cache.ps1')
local report_path = utils.join_path(config, 'files/shader-cache-cleanup.json')
local requested, last_report

local function ReadReport()
    local text
    if safe_ok then text = safe.read(report_path)
    else
        local file = io.open(report_path, 'rb')
        if file then text = file:read('*a'); file:close() end
    end
    if not text or text == '' then return end
    return utils.parse_json(text)
end

local function Poll()
    local report = ReadReport()
    if not report then return end
    local encoded = utils.format_json(report)
    if encoded == last_report then return end
    last_report = encoded
    mp.set_property_native('user-data/shader-cache', report)
    if requested and report.requested_at ~= requested.previous then
        local text
        if report.status == 'waiting' then
            text = '已安排缓存清理：退出全部 mpv 窗口后执行，下次启动重建'
        elseif report.status == 'failed' then
            text = '着色器缓存清理失败：' .. tostring(report.error)
            msg.error(text)
        end
        if text then mp.osd_message(text, 6); requested = nil end
    end
end

mp.register_script_message('shader-cache-clean', function(mode)
    if mode ~= 'mpv' and mode ~= 'amd-vulkan' then msg.error('未知缓存清理模式'); return end
    if package.config:sub(1, 1) ~= '\\' then mp.osd_message('此清理入口适用于 Windows', 4); return end
    if not utils.file_info(helper) then
        msg.error('缺少 installer/clear-shader-cache.ps1，请同时更新维护脚本')
        mp.osd_message('缺少缓存维护脚本，请同时更新 installer', 5)
        return
    end
    local report = ReadReport()
    if requested then mp.osd_message('正在安排缓存清理，请稍候', 3); return end
    local previous = report and report.requested_at
    local function Quote(value) return "'" .. tostring(value):gsub("'", "''") .. "'" end
    -- Windows PowerShell 5.1 默认按系统代码页读无 BOM 文件，显式按 UTF-8 载入。
    local command = '& ([scriptblock]::Create([IO.File]::ReadAllText(' .. Quote(helper)
        .. ',[Text.Encoding]::UTF8))) -ConfigDirectory ' .. Quote(config)
        .. ' -Mode ' .. Quote(mode) .. ' -WaitForProcessId ' .. tostring(utils.getpid())
    -- 自定义路径也交给同一边界检查，拒绝把任意目录当作缓存删除。
    local directory = mp.get_property('gpu-shader-cache-dir', '')
    if directory ~= '' then
        local expanded = mp.command_native({'expand-path', directory})
        command = command .. ' -ShaderCacheDirectory ' .. Quote(expanded)
    end
    -- mpv 的 Windows subprocess 已使用无控制台创建；额外 WindowStyle 在无控制台环境会失败。
    local args = {'powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive',
        '-ExecutionPolicy', 'Bypass', '-Command', command}
    requested = {previous = previous, at = mp.get_time()}
    local inspect_args = {}
    for index, value in ipairs(args) do inspect_args[index] = value end
    inspect_args[#inspect_args] = command .. ' -Inspect'
    mp.command_native_async({name = 'subprocess', playback_only = false, capture_stdout = true,
        capture_stderr = true, args = inspect_args}, function(success, result)
        if not success or not result or result.status ~= 0 then
            requested = nil
            msg.error('缓存路径检查失败：' .. tostring(result and result.stderr))
            mp.osd_message('缓存路径检查失败，详情见日志；可使用离线入口', 5)
            return
        end
        local plan = utils.parse_json(result.stdout)
        if plan and plan.pending then
            requested = nil
            mp.osd_message('已有缓存清理任务，等待全部 mpv 窗口退出后执行', 5)
            return
        end
        local ok, spawned = pcall(mp.command_native, {name = 'subprocess', playback_only = false,
            detach = true, args = args})
        if not ok or not spawned or spawned.status ~= 0 then
            requested = nil
            msg.error('无法启动缓存清理：' .. tostring(spawned))
            mp.osd_message('无法启动缓存清理，请使用 installer 中的离线入口', 5)
            return
        end
        mp.osd_message('正在安排退出后的缓存清理；播放保持运行', 4)
    end)
end)

mp.register_script_message('shader-cache-status', function()
    local report = ReadReport()
    if not report then mp.osd_message('尚无着色器缓存清理记录', 4); return end
    local names = {waiting = '等待播放器退出', cleaning = '正在隔离缓存', complete = '清理完成',
        partial = '部分完成（占用或受保护文件已跳过）', failed = '清理失败'}
    local text = (names[report.status] or report.status) .. '\n已隔离 ' .. tostring(report.moved or 0)
        .. ' 个文件，跳过 ' .. tostring(report.skipped or 0) .. ' 个'
    if report.backup then text = text .. '\n备份：' .. report.backup end
    if report.error then text = text .. '\n' .. report.error end
    mp.osd_message(text, 8)
end)

mp.add_periodic_timer(.5, function()
    Poll()
    if requested and mp.get_time() - requested.at > 15 then
        requested = nil
        msg.error('未收到缓存维护任务的确认，请使用离线入口查看错误')
        mp.osd_message('缓存任务未确认，请使用 installer 中的离线入口', 5)
    end
end)
Poll()
