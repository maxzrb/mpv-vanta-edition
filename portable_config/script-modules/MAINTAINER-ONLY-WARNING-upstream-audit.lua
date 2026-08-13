-- 维护者专用：只读检查脚本/着色器上游差异。普通用户不要运行，不负责产品更新。
local msg = require 'mp.msg'

local running = false

local function expand_path(path)
    return mp.command_native({'expand-path', path})
end

local function show_result(success, result)
    running = false

    local stdout = result and result.stdout or ''
    local stderr = result and result.stderr or ''
    local status = result and result.status or -1

    if stdout ~= '' then
        msg.info(stdout)
    end
    if stderr ~= '' then
        msg.warn(stderr)
    end

    if success and status == 0 then
        mp.osd_message('维护者只读审计完成，请查看控制台', 5)
    else
        mp.osd_message('维护者只读审计失败，请查看控制台', 6)
        msg.error('maintainer upstream audit failed, exit status:', status)
    end
end

local function audit_upstreams()
    if running then
        mp.osd_message('维护者审计正在运行', 3)
        return
    end

    local config_dir = expand_path('~~/')
    local helper = expand_path('~~/script-modules/MAINTAINER-ONLY-WARNING-upstream-audit.ps1')
    local args = {
        'powershell.exe',
        '-NoLogo',
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        helper,
        '-ConfigDir',
        config_dir,
        '-DryRun',
    }

    running = true
    mp.osd_message('维护者只读审计：不会修改脚本或着色器…', 4)
    msg.info('starting maintainer-only read-only upstream audit')

    local command = {
        name = 'subprocess',
        args = args,
        capture_stdout = true,
        capture_stderr = true,
        playback_only = false,
    }

    if mp.command_native_async then
        mp.command_native_async(command, show_result)
    else
        local result = mp.command_native(command)
        show_result(result and result.status == 0, result)
    end
end

-- 不注册按键，也不进入普通用户菜单；仅供维护者从控制台显式调用。
mp.register_script_message('maintainer-audit-upstreams-read-only', audit_upstreams)
