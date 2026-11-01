"""隔离配置验证自动连播菜单、真实 EOF、手动切集和重启记忆。"""
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/auto-next'
OUT.mkdir(parents=True, exist_ok=True)
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
CONFIG = Path(tempfile.mkdtemp(prefix='config-', dir=OUT))
(CONFIG / 'scripts').mkdir()
(CONFIG / 'script-opts').mkdir()
shutil.copytree(ROOT / 'portable_config/script-modules', CONFIG / 'script-modules')
for name in ['uosc', 'dyn_menu.lua', 'autoload.lua']:
    source = ROOT / 'portable_config/scripts' / name
    target = CONFIG / 'scripts' / name
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)
for name in ['uosc.conf', 'uosc-themes.json', 'dyn_menu.conf', 'autoload.conf']:
    shutil.copy2(ROOT / 'portable_config/script-opts' / name, CONFIG / 'script-opts' / name)
shutil.copy2(ROOT / 'portable_config/input.conf', CONFIG / 'input.conf')
MEDIA = Path(tempfile.mkdtemp(prefix='episodes-', dir=OUT))
for name in ['第01集.wav', '第02集.wav']:
    with wave.open(str(MEDIA / name), 'wb') as stream:
        stream.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
        stream.writeframes(bytes(8000 * 2 * 2))


def wait_for(player, predicate, label, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.04)
    raise AssertionError(label)


def start(name):
    player = Player(['--config-dir=' + str(CONFIG), '--vo=null', '--ao=null',
                     '--force-window=no', '--audio-display=no', '--pause=yes',
                     str(MEDIA / '第01集.wav')], 'auto-next-' + name)
    wait_for(player, lambda: player.get('duration') is not None and
             player.get('user-data/uosc/auto-next') is not None, '脚本加载')
    return player


def menu_toggle(player):
    def find(items):
        for item in items or []:
            if item.get('title') == '自动连播':
                assert 'submenu' not in item, '自动连播应为直接切换项'
                return item
            found = find(item.get('submenu'))
            if found:
                return found
        return None
    return find(player.get('menu-data') or player.get('user-data/menu/items'))


def select(player, enabled):
    # 执行实际生成菜单内的指令，验证菜单和处理器的连接。
    wait_for(player, lambda: menu_toggle(player) is not None, '自动连播菜单')
    assert player.get('user-data/uosc/auto-next') is not enabled
    item = menu_toggle(player)
    command = item['cmd'].split('#', 1)[0].split()
    assert command == ['script-message-to', 'uosc', 'auto-next', 'toggle']
    result = player.command(*command)
    assert result['error'] == 'success', result
    wait_for(player, lambda: player.get('user-data/uosc/auto-next') is enabled, '连播状态')
    wait_for(player, lambda: ('checked' in menu_toggle(player).get('state', [])) is enabled, '菜单选中状态')
    assert ('auto_next=' + ('yes' if enabled else 'no')) in (CONFIG / 'script-opts/uosc.conf').read_text(encoding='utf-8')


def finish_first(player):
    player.command('seek', 1.5, 'absolute+exact')
    player.command('set_property', 'pause', False)


def stopped(player):
    wait_for(player, lambda: player.get('eof-reached') is True, '本集 EOF')
    time.sleep(.5)
    assert player.get('playlist-pos') == 0
    assert player.get('pause') is True
    assert player.get('keep-open') == 'always'


logs = []
rows = []
p = start('default')
try:
    wait_for(p, lambda: p.get('playlist-count') == 2, '同目录自动加入播放列表')
    assert p.get('user-data/uosc/auto-next') is False
    wait_for(p, lambda: menu_toggle(p) is not None, '菜单加载')
    (OUT / 'menu.json').write_text(json.dumps(menu_toggle(p), ensure_ascii=False, indent=2), encoding='utf-8')
    finish_first(p)
    stopped(p)
    rows.append('默认关闭：自动载入两集但播完第一集停住')
    p.command('playlist-next')
    wait_for(p, lambda: p.get('playlist-pos') == 1, '手动下一集')
    rows.append('关闭时仍可手动下一集')
    p.command('loadfile', str(MEDIA / '第01集.wav'), 'replace')
    wait_for(p, lambda: p.get('playlist-pos') == 0 and p.get('playlist-count') == 2, '重载第一集')
    select(p, True)
    finish_first(p)
    wait_for(p, lambda: p.get('playlist-pos') == 1, '开启后自动下一集')
    rows.append('菜单开启：自动切换第二集并保存')
finally:
    p.close()
    logs.append(p.log)

p = start('restart-yes')
try:
    assert p.get('user-data/uosc/auto-next') is True
    select(p, False)
    finish_first(p)
    stopped(p)
    rows.append('重启记住开启；菜单关闭立即生效')
    p.command('set_property', 'loop-file', 'inf')
    p.command('seek', 1.5, 'absolute+exact')
    p.command('set_property', 'pause', False)
    time.sleep(1)
    assert p.get('playlist-pos') == 0 and p.get('eof-reached') is False
    assert p.get('pause') is False and p.get('time-pos') < 1.5
    rows.append('关闭连播时单集循环仍有效')
finally:
    p.close()
    logs.append(p.log)

# 用真实 uosc 随机播放与目录续播，确认临近末尾的定时器也服从关闭选项。
with (CONFIG / 'script-opts/uosc.conf').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\nshuffle=yes\nautoload=yes\n')
for directory_only in [False, True]:
    if directory_only:
        with (CONFIG / 'script-opts/autoload.conf').open('a', encoding='utf-8', newline='\n') as stream:
            stream.write('\ndisabled=yes\n')
    p = start('directory' if directory_only else 'shuffle')
    try:
        assert p.get('user-data/uosc/auto-next') is False
        wait_for(p, lambda: p.get('playlist-count') == (1 if directory_only else 2), '播放列表数量')
        finish_first(p)
        stopped(p)
        assert Path(p.get('path')).name == '第01集.wav'
        rows.append('关闭后目录续播被阻止' if directory_only else '重启记住关闭；随机播放不会绕过关闭')
        if directory_only:
            select(p, True)
            p.command('seek', 0, 'absolute+exact')
            p.command('set_property', 'pause', False)
            wait_for(p, lambda: Path(p.get('path') or '').name == '第02集.wav', '开启目录续播')
            rows.append('开启后目录续播恢复')
            select(p, False)
    finally:
        p.close()
        logs.append(p.log)

# 使用整套活动配置的独立副本检查脚本之间的实际交接，避免改写用户历史和偏好。
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']
full_config = create_config('auto-next-full')
p = Player(['--config-dir=' + str(full_config), '--vo=null', '--ao=null',
            '--force-window=no', '--audio-display=no', '--pause=yes',
            str(MEDIA / '第01集.wav')], 'auto-next-full-config')
try:
    wait_for(p, lambda: p.get('playlist-count') == 2 and menu_toggle(p) is not None, '完整配置启动')
    finish_first(p)
    stopped(p)
    rows.append('完整配置：自动加载两集，默认播完第一集暂停')
finally:
    p.close()
    logs.append(p.log)

errors = []
for log in logs:
    errors.extend(line for line in log.read_text(encoding='utf-8').splitlines()
                  if '[e]' in line or '[f]' in line or 'Lua error' in line)
assert not errors, errors[:10]
assert 'auto_next=no' in (ROOT / 'portable_config/script-opts/uosc.conf').read_text(encoding='utf-8')
(OUT / 'result.json').write_text(json.dumps(dict(passed=True, rows=rows, config=str(CONFIG), errors=errors),
                                         ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(rows, ensure_ascii=False, indent=2))
