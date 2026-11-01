"""验证真实缩略图子进程在退出、快速退出及停止重开后正确回收。"""
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import runpy
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/thumbfast-lifecycle'
OUT.mkdir(parents=True, exist_ok=True)
MEDIA = OUT / 'fixture.mp4'
if not MEDIA.exists():
    subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=24', '-t', '8',
                    '-c:v', 'libx264', '-preset', 'ultrafast', str(MEDIA)], check=True)
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']


class Entry(ctypes.Structure):
    _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('pid', w.DWORD),
                ('heap', ctypes.c_size_t), ('module', w.DWORD), ('threads', w.DWORD),
                ('parent', w.DWORD), ('priority', w.LONG), ('flags', w.DWORD), ('exe', w.WCHAR * 260)]


kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
kernel.Process32FirstW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
kernel.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
kernel.CloseHandle.argtypes = [w.HANDLE]


def children(pid):
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    assert snapshot != ctypes.c_void_p(-1).value
    entry = Entry()
    entry.size = ctypes.sizeof(entry)
    result = []
    try:
        more = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            if entry.parent == pid and entry.exe.lower() == 'mpv.exe':
                result.append(entry.pid)
            more = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    return result


rows = []
for direct_io, name, delay in [(direct, name, delay) for direct in [False, True]
                              for name, delay in [('normal', 1), ('immediate', 0), ('stop-reopen', .1)]]:
    player = Player(['--no-config', '--script=' + str(ROOT / 'portable_config/scripts/thumbfast.lua'),
                     '--script-opts=thumbfast-mpv_path=' + str(ROOT / 'mpv.exe')
                     + ',thumbfast-direct_io=' + ('yes' if direct_io else 'no'),
                     '--vo=gpu-next', '--gpu-api=d3d11', '--geometry=320x180',
                     '--window-minimized=yes', '--pause=yes', str(MEDIA)],
                    'thumbfast-lifecycle-' + name + ('-native' if direct_io else '-pipe'))
    created = []
    try:
        player.wait_video()
        time.sleep(.2)
        player.command('script-message-to', 'thumbfast', 'thumb', '2', '10', '10')
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            created = children(player.process.pid)
            if created:
                break
            time.sleep(.02)
        assert created, '缩略图子进程没有启动'
        if name == 'stop-reopen':
            player.command('stop')
            player.command('loadfile', str(MEDIA))
            player.wait_video()
            player.command('script-message-to', 'thumbfast', 'thumb', '3', '10', '10')
            time.sleep(.2)
            created = sorted(set(created + children(player.process.pid)))
        time.sleep(delay)
    finally:
        player.close()
    deadline = time.monotonic() + 3
    while children(player.process.pid) and time.monotonic() < deadline:
        time.sleep(.05)
    remaining = children(player.process.pid)
    rows.append(dict(case=name, direct_io=direct_io, children=created, remaining=remaining))
    # 只清理本测试启动的播放器的直接子进程，失败后也不影响用户其他实例。
    for pid in remaining:
        subprocess.run(['taskkill', '/PID', str(pid), '/F'], capture_output=True)
    assert not remaining, rows[-1]
(OUT / 'result.json').write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
print('PASS 普通管道／原生写入 × 正常退出／刚生成缩略图退出／停止重开：六组均无子进程残留')
