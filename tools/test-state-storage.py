"""真实双实例验证历史合并、书签整次提交、过期列表和保存失败保护。"""
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(tempfile.mkdtemp(prefix='storage-', dir=ROOT / 'tmp'))
CONFIG = OUT / 'config'
for name in ['scripts', 'script-opts', 'script-modules', 'files']:
    (CONFIG / name).mkdir(parents=True)
for name in ['recentmenu.lua', 'simplebookmark.lua']:
    shutil.copy2(ROOT / 'portable_config/scripts' / name, CONFIG / 'scripts' / name)
with (CONFIG / 'scripts/recentmenu.lua').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write("\nmp.register_script_message('test-save-pending',function() mp.set_property_native('user-data/recent-test',{ok=not not write_json(true)}) end)\n")
shutil.copy2(ROOT / 'portable_config/script-modules/safe-file.lua', CONFIG / 'script-modules/safe-file.lua')
(CONFIG / 'script-opts/recentmenu.conf').write_text(
    'path=~~/files/recent.json\nlength=100\nignore_same_series=no\n', encoding='utf-8')
(CONFIG / 'script-opts/simplebookmark.conf').write_text(
    'log_path=/:dir%mpvconf%/files\nlog_file=bookmarks.log\nauto_run_list_idle=none\n', encoding='utf-8')
PROBE = '''
local test_snapshot
local function test_report(ok, err)
    mp.set_property_native('user-data/storage-test', {ok=not not ok,error=err,entries=read_log_table() or {}})
end
mp.register_script_message('test-save', function(position) test_report(write_log(tonumber(position))) end)
mp.register_script_message('test-snapshot', function()
    test_snapshot=read_log_table();test_report(true)
end)
mp.register_script_message('test-delete-snapshot', function()
    osd_log_contents=test_snapshot;list_cursor=#test_snapshot;test_report(delete_selected())
end)
mp.register_script_message('test-edit-first', function()
    osd_log_contents=read_log_table();test_report(add_additional_param_log_entry(2,1,'group='))
end)
mp.register_script_message('test-quicksave', function() test_report(quicksave_slot(1)) end)
'''
with (CONFIG / 'scripts/simplebookmark.lua').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write(PROBE)
for name in ['甲.wav', '乙.wav']:
    with wave.open(str(OUT / name), 'wb') as stream:
        stream.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
        stream.writeframes(bytes(30 * 8000 * 2))
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']


def wait(predicate, label):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.03)
    raise AssertionError(label)


def action(player, name, *args):
    player.command('set_property', 'user-data/storage-test', None)
    response = player.command('script-message-to', 'simplebookmark', name, *args)
    assert response['error'] == 'success', response
    wait(lambda: player.get('user-data/storage-test') is not None, name)
    return player.get('user-data/storage-test')


def history():
    return json.loads((CONFIG / 'files/recent.json').read_text(encoding='utf-8'))


players = []
rows = []
try:
    for name in ['甲.wav', '乙.wav']:
        player = Player(['--config-dir=' + str(CONFIG), '--vo=null', '--ao=null', '--pause=yes',
                         '--force-window=no', str(OUT / name)], 'state-storage-' + str(len(players)))
        players.append(player)
        wait(lambda: player.get('duration') is not None, '媒体载入')
        wait(lambda: (CONFIG / 'files/recent.json').is_file() and
             any(Path(item['value'][1]).name == name for item in history()), '历史载入')
    first, second = players
    assert len(history()) == 2 and Path(history()[0]['value'][1]).name == '乙.wav'
    rows.append('两个实例载入不同影片，历史合并保留双方条目')
    response = first.command('script-message-to', 'recentmenu', 'uosc-callback', json.dumps(dict(
        type='activate', action='remove', index=1, value=['loadfile', str(OUT / '甲.wav')]), ensure_ascii=False))
    assert response['error'] == 'success'
    wait(lambda: len(history()) == 1, '按实际身份删除旧列表条目')
    assert Path(history()[0]['value'][1]).name == '乙.wav'
    rows.append('旧列表索引变化后仍只删除选中的影片')
    assert action(first, 'test-save', '1')['ok']
    assert action(second, 'test-save', '2')['ok']
    state = action(first, 'test-snapshot')
    assert len(state['entries']) == 2
    assert action(first, 'test-quicksave')['ok']
    log = CONFIG / 'files/bookmarks.log'
    assert 'slot=1' in log.read_text(encoding='utf-8')
    assert len(action(first, 'test-snapshot')['entries']) == 3
    rows.append('书签追加和槽位组合提交保留另一实例记录')
    assert action(second, 'test-edit-first')['ok']
    before = log.read_bytes()
    assert not action(first, 'test-delete-snapshot')['ok']
    assert log.read_bytes() == before
    rows.append('过期书签列表拒绝删除已由另一实例修改的条目')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p, w.DWORD, w.DWORD, w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    handle = kernel.CreateFileW(str(log), 0x80000000, 1, None, 3, 0x80, None)
    assert handle != ctypes.c_void_p(-1).value
    try:
        assert not action(first, 'test-save', '4')['ok']
        assert log.read_bytes() == before
    finally:
        kernel.CloseHandle(handle)
    assert action(first, 'test-save', '4')['ok']
    assert len(action(first, 'test-snapshot')['entries']) == 4
    rows.append('真实文件占用导致保存失败时原件不变，解除占用后可重试')
    first.close()
    players.remove(first)
    assert len(history()) == 1 and Path(history()[0]['value'][1]).name == '乙.wav'
    rows.append('旧实例退出不会复活删除条目或覆盖新实例历史')
    history_file = CONFIG / 'files/recent.json'
    valid_history = history_file.read_bytes()
    history_file.write_bytes(b'[42]')
    third = Player(['--config-dir=' + str(CONFIG), '--vo=null', '--ao=null', '--pause=yes',
                    '--force-window=no', str(OUT / '甲.wav')], 'state-storage-malformed')
    players.append(third)
    wait(lambda: third.get('duration') is not None, '损坏历史下继续播放')
    third.command('script-message-to', 'recentmenu', 'test-save-pending')
    wait(lambda: third.get('user-data/recent-test') is not None, '损坏历史保护')
    assert third.get('user-data/recent-test')['ok'] is False
    assert history_file.read_bytes() == b'[42]'
    third.close()
    players.remove(third)
    history_file.write_bytes(valid_history)
    rows.append('损坏历史不会导致脚本退出或被空列表覆盖，播放继续')
finally:
    for player in players:
        player.close()
assert not list((CONFIG / 'files').glob('*.tmp-*'))
(OUT / 'result.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(rows, ensure_ascii=False, indent=2))
