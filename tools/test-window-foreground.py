"""用自有遮挡窗口验证起播／重新打开／最小化恢复，不操作其它应用窗口。"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import runpy
import time

ROOT = Path(__file__).resolve().parents[1]
helper = runpy.run_path(str(ROOT/'tools/validate-modernization.py'))
create_config = runpy.run_path(str(ROOT/'tools/isolated-config.py'))['create_config']
user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
    wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.SetWindowPos.argtypes = [wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindow.argtypes = [wintypes.HWND,wintypes.UINT]
user32.GetWindow.restype = wintypes.HWND
user32.GetWindowLongW.argtypes = [wintypes.HWND,ctypes.c_int]
user32.ShowWindow.argtypes = [wintypes.HWND,ctypes.c_int]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
user32.GetAncestor.argtypes = [wintypes.HWND,wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND


def above(window, other):
    current = user32.GetWindow(other, 3)
    while current:
        if current == window:
            return True
        current = user32.GetWindow(current, 3)
    return False


def cover(window):
    # 测试进程没有用户输入资格；短暂置顶后立即还原，建立普通窗口遮挡夹具。
    assert user32.SetWindowPos(window, -1, 0,0,0,0,0x0013)
    assert user32.SetWindowPos(window, -2, 0,0,0,0,0x0013)
    user32.SetForegroundWindow(window)
    time.sleep(.2)


def snapshot(p, hwnd, cover_hwnd):
    return {'mpv_above_cover':above(hwnd,cover_hwnd),
            'foreground':user32.GetForegroundWindow()==hwnd,
            'topmost':bool(user32.GetWindowLongW(hwnd,-20)&8),
            'ontop':p.get('ontop'), 'minimized':bool(user32.IsIconic(hwnd))}


media = ROOT/'tmp/modernization/validation/compat-hevc10.mkv'
assert media.is_file(), '先运行 test-playback-compat.py 生成播放夹具'
cover_hwnd = user32.CreateWindowExW(0,'STATIC','MPV 起播前台回归临时窗口',0x10CF0000,
    20,20,700,500,None,None,None,None)
assert cover_hwnd, ctypes.WinError(ctypes.get_last_error())
rows = []
try:
    for enabled in (False, True):
        config = create_config('foreground-'+str(enabled),exclude_scripts=[] if enabled else ['window-foreground.lua'])
        cover(cover_hwnd)
        p = helper['Player'](['--config-dir='+str(config),'--ao=null','--pause=yes',
            '--geometry=640x360','--ontop=no',str(media)],'foreground-'+str(enabled),
            before_resume=lambda process:user32.AllowSetForegroundWindow(process.pid))
        try:
            p.wait_video()
            deadline=time.monotonic()+10
            while not p.get('window-id'):
                if time.monotonic()>deadline:raise TimeoutError('窗口没有创建')
                time.sleep(.1)
            hwnd=p.get('window-id')
            time.sleep(.7)
            initial=snapshot(p,hwnd,cover_hwnd)
            cover(cover_hwnd)
            assert not above(hwnd,cover_hwnd), {'error':'遮挡夹具未覆盖播放器','initial':initial,'covered':snapshot(p,hwnd,cover_hwnd),'hwnd':hwnd,'cover':cover_hwnd,'root':user32.GetAncestor(hwnd,2),'cover-root':user32.GetAncestor(cover_hwnd,2),'fg':user32.GetForegroundWindow()}
            user32.AllowSetForegroundWindow(p.process.pid)
            p.command('loadfile',str(media),'replace')
            time.sleep(1)
            reopened=snapshot(p,hwnd,cover_hwnd)
            row={'enabled':enabled,'initial':initial,'reopened':reopened}
            assert reopened['mpv_above_cover'] == enabled, row
            assert not reopened['topmost'] and reopened['ontop'] is False, row
            if enabled:
                assert initial['mpv_above_cover'], row
                user32.ShowWindow(hwnd,6)
                time.sleep(.3)
                assert user32.IsIconic(hwnd), '最小化夹具未生效'
                cover(cover_hwnd)
                user32.AllowSetForegroundWindow(p.process.pid)
                p.command('loadfile',str(media),'replace')
                time.sleep(1)
                row['restored']=snapshot(p,hwnd,cover_hwnd)
                assert row['restored']['mpv_above_cover'] and not row['restored']['minimized'], row
                cover(cover_hwnd)
                p.command('set_property','pause',False)
                time.sleep(.5)
                p.command('set_property','pause',True)
                time.sleep(.5)
                row['pause_cycle']=snapshot(p,hwnd,cover_hwnd)
                assert not row['pause_cycle']['mpv_above_cover'], row
                p.command('loadfile',str(media),'replace')
                p.command('loadfile',str(media),'append')
                p.command('set_property','pause',False)
                time.sleep(.3)
                cover(cover_hwnd)
                p.command('seek',11.6,'absolute')
                deadline=time.monotonic()+8
                while p.get('playlist-pos') != 1:
                    if time.monotonic()>deadline:raise TimeoutError('自动切集没有发生')
                    time.sleep(.1)
                time.sleep(.3)
                row['automatic_next']=snapshot(p,hwnd,cover_hwnd)
                assert not row['automatic_next']['mpv_above_cover'], row
                saved=(config/'script-opts/window_size_position.conf').read_text(encoding='utf-8')
                assert 'ontop=no' in saved and 'ontop=yes' not in saved, saved
                p.command('set_property','ontop',True)
                p.command('loadfile',str(media),'replace')
                time.sleep(.5)
                row['existing_ontop']=snapshot(p,hwnd,cover_hwnd)
                assert row['existing_ontop']['ontop'] and row['existing_ontop']['topmost'], row
                p.command('set_property','ontop',False)
            rows.append(row)
        finally:
            p.close()
        log=p.log.read_text(encoding='utf-8',errors='replace')
        assert not [line for line in log.splitlines() if '[e]' in line or '[f]' in line],log
finally:
    user32.DestroyWindow(cover_hwnd)
out=ROOT/'tmp/release-prep-20261008/window-foreground-results.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(rows,ensure_ascii=False,indent=2))
print('PASS 起播抬窗／旧版遮挡复现／重新打开／最小化恢复／置顶偏好保留／暂停与自动切集不抢前台')
