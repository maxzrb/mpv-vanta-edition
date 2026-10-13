"""在隔离配置中检查 ACM 冷启动的窗口重建与最终显示层级。"""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import runpy
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
helper = runpy.run_path(str(ROOT / 'tools/test-release-playback.py'))
Player = helper['Player']
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']
user = ctypes.WinDLL('user32', use_last_error=True)
user.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
    wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
user.CreateWindowExW.restype = wintypes.HWND
user.DestroyWindow.argtypes = [wintypes.HWND]
user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.UINT]
user.SetForegroundWindow.argtypes = [wintypes.HWND]
user.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
user.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
user.GetWindow.restype = wintypes.HWND
user.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]


def above(window, other):
    current = user.GetWindow(other, 3)
    while current:
        if current == window:
            return True
        current = user.GetWindow(current, 3)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--foreground-only', action='store_true')
    parser.add_argument('--case', default='')
    parser.add_argument('--idle', action='store_true')
    parser.add_argument('--backend', choices=['d3d11', 'vulkan'], default='d3d11')
    parser.add_argument('--pipeline', choices=['standard', 'hq'], default='hq')
    parser.add_argument('--media', type=Path, default=ROOT / 'tmp/modernization/validation/compat-hevc10.mkv')
    args = parser.parse_args()
    config = create_config('startup-acm-' + args.backend)
    if args.baseline or args.foreground_only:
        for relative in ('scripts/color-target.lua', 'scripts/display-color.lua',
                         'scripts/window-foreground.lua', 'script-modules/display-color-native.lua'):
            if args.foreground_only and relative == 'scripts/window-foreground.lua':
                continue
            (config / relative).write_bytes(subprocess.check_output(
                ['git', 'show', 'cc67ad9:portable_config/' + relative], cwd=ROOT))
    (config / 'files/color-pipeline-preferences.json').write_text(
        json.dumps({'pipeline': args.pipeline}), encoding='utf-8')
    (config / 'scripts/startup-window-probe.lua').write_text("""-- 只记录本次诊断播放器的窗口身份。
local ids = {}
mp.observe_property('window-id', 'number', function(_, id)
    if id and id > 0 then
        ids[#ids + 1] = id
        mp.set_property_native('user-data/startup-window-probe', ids)
    end
end)
""", encoding='utf-8', newline='\n')
    cover = user.CreateWindowExW(0, 'STATIC', 'MPV 起播窗口回归夹具', 0x10CF0000,
        20, 20, 1500, 1000, None, None, None, None)
    assert cover, ctypes.WinError(ctypes.get_last_error())
    player = None
    label = ('baseline' if args.baseline else 'foreground-only' if args.foreground_only else 'fixed') + '-' + args.backend + '-' + args.pipeline
    if args.case:
        label += '-' + args.case
    if args.idle:
        label += '-idle'
    try:
        assert user.SetWindowPos(cover, -1, 0, 0, 0, 0, 0x0013)
        assert user.SetWindowPos(cover, -2, 0, 0, 0, 0, 0x0013)
        user.SetForegroundWindow(cover)
        launch_args = ['--config-dir=' + str(config), '--gpu-api=' + args.backend,
            '--ao=null', '--loop-file=inf', '--ontop=no']
        if not args.idle:
            launch_args.append(str(args.media))
        player = Player(launch_args,
            'startup-acm-' + label,
            before_resume=lambda process: user.AllowSetForegroundWindow(process.pid))
        idle_window = None
        if args.idle:
            # 等待超过原验证超时，再主动加载媒体，捕获启动页的错误回退／二次重建。
            time.sleep(4)
            idle_window = player.get('window-id')
            player.command('loadfile', str(args.media))
        player.wait_video()
        playback = helper['moving_video'](player)
        helper['helper']['stable'](player, args.pipeline)
        time.sleep(.3)
        hwnd = player.get('window-id')
        row = dict(label=label, windows=player.get('user-data/startup-window-probe'),
            above_cover=above(hwnd, cover), topmost=bool(user.GetWindowLongW(hwnd, -20) & 8),
            ontop=player.get('ontop'), system=player.get('user-data/display-color'),
            target=player.get('video-target-params'), playback=playback)
        if args.idle:
            row['idle_window'] = idle_window
            assert hwnd == idle_window, row
    finally:
        if player is not None:
            player.close()
        user.DestroyWindow(cover)
    assert player.process.returncode == 0
    log = player.log.read_text(encoding='utf-8', errors='replace')
    row['contexts'] = log.count("Initializing GPU context '")
    row['detached_video'] = 'Set property: vid="no"' in log
    errors = [line for line in log.splitlines() if '[e]' in line or '[f]' in line or 'Lua error:' in line]
    assert not errors, errors[:8]
    out = ROOT / 'tmp/modernization/startup-acm-20261013' / (label + '.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(row, ensure_ascii=False), flush=True)
    if args.baseline:
        assert args.pipeline == 'hq' and row['system']['mode'] == 'wcg'
        assert row['contexts'] >= 2 and row['detached_video'], row
        print('PASS 旧版 ACM 起播撤轨和窗口重建已复现')
    elif args.foreground_only:
        assert row['contexts'] >= 2 and row['detached_video'], row
        assert row['above_cover'] and not row['topmost'] and row['ontop'] is False, row
        print('PASS 起播仍重建时的新窗口前台恢复／置顶偏好保留')
    else:
        assert row['contexts'] == 1 and not row['detached_video'], row
        assert row['above_cover'] and not row['topmost'] and row['ontop'] is False, row
        if args.pipeline == 'hq' and row['system']['mode'] == 'wcg':
            assert row['target']['gamma'] == 'scrgb' and row['target']['pixelformat'] == 'rgba16hf'
        print('PASS 单窗口冷启动／前台层级／置顶偏好／正确色彩输出／正常退出')


if __name__ == '__main__':
    main()
