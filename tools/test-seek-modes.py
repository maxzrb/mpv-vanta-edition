"""隔离配置验证统一跳转方式：真实方向键、时间轴方法、精准快捷键及重启记忆。"""
import json
from pathlib import Path
import re
import runpy
import time
import ctypes
from ctypes import wintypes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'tmp/seek-modes-20261017'
OUT.mkdir(exist_ok=True)
BasePlayer = runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
class Player(BasePlayer):
    def __init__(self, *args, **kwargs):
        self.restarts = 0
        self.pending_restart = 0
        super().__init__(*args, **kwargs)
        self.command('enable_event', 'playback-restart')
    def command(self, *args):
        if args[0] in ['seek', 'keypress'] or (args[0] == 'script-message-to' and 'test-seek-cursor' in args):
            self.pending_restart = self.restarts
        self.request_id += 1
        self.pipe.write((json.dumps(dict(command=args, request_id=self.request_id))+'\n').encode('utf-8'))
        deadline = time.monotonic()+self.ipc_timeout
        while time.monotonic() < deadline:
            if b'\n' not in self.response_buffer:
                available = wintypes.DWORD()
                if not self.kernel.PeekNamedPipe(self.pipe_handle, None, 0, None, ctypes.byref(available), None):
                    raise RuntimeError('IPC已关闭')
                if not available.value:
                    time.sleep(.005)
                    continue
                self.response_buffer += self.pipe.read(available.value)
                continue
            line, self.response_buffer = self.response_buffer.split(b'\n', 1)
            data = json.loads(line)
            if data.get('event') == 'playback-restart':
                self.restarts += 1
            if data.get('request_id') == self.request_id:
                return data
        raise TimeoutError(args)
create_config = runpy.run_path(str(ROOT/'tools/isolated-config.py'))['create_config']
config = create_config('seek-modes')
source = Path('C:/Users/maxzr/Downloads/youtube-UCoCy_rS-xtdTtW0GBV8zC_w_ねこしろ - [2017年10月7日]【MMD】「Happy Halloween」 - Miku  Halloween Edit【4K UHD】-5DHyKTW20RE.mp4')
assert source.is_file()
# 仅隔离副本增加测试入口，调用正式时间轴点击／松手方法，不替换seek实现。
with (config/'scripts/uosc/main.lua').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('''
mp.register_script_message('test-seek-cursor', function(target, drag)
    local timeline = Elements.timeline
    local left, right = timeline.ax, timeline.bx
    target = tonumber(target)
    for _ = 1, 32 do
        local middle = (left + right) / 2
        if timeline:get_time_at_x(middle) < target then left = middle else right = middle end
    end
    cursor.x = (left + right) / 2
    timeline:handle_cursor_down()
    if drag == 'yes' then
        timeline.pressed.dragging = true
        mp.set_property_native('pause', true)
        timeline:set_from_cursor(true)
    end
    timeline:handle_cursor_up()
    mp.set_property_native('user-data/seek-test', {target = target, mode = options.seek_mode, wheel_flag = config.timeline_step_flag})
end)
''')
args = ['--config-dir='+str(config), '--geometry=960x540', '--pause=yes', '--volume=0', str(source)]
rows = []
def settle(player):
    deadline = time.monotonic()+8
    time.sleep(.08)
    while time.monotonic() < deadline:
        value = player.get('time-pos')
        if value is not None and not player.get('seeking') and player.restarts > player.pending_restart:
            return value
        time.sleep(.015)
    raise AssertionError('跳转未结束')
def mode(player, value):
    assert player.command('script-message-to', 'uosc', 'seek-mode', value)['error'] == 'success'
    deadline = time.monotonic()+3
    while time.monotonic() < deadline:
        if player.get('user-data/uosc/seek-mode') == value:
            break
        time.sleep(.02)
    assert player.get('user-data/uosc/seek-mode') == value
    assert player.get('hr-seek') in (['yes', True] if value == 'exact' else ['no', False]), player.get('hr-seek')
    assert f'seek_mode={value}' in (config/'script-opts/uosc.conf').read_text(encoding='utf-8')

logs = []
p = Player(args, 'seek-modes-controls')
try:
    p.wait_video()
    time.sleep(.5)
    assert p.get('user-data/uosc/seek-mode') == 'exact'
    menu = p.get('menu-data') or p.get('user-data/menu/items')
    text = json.dumps(menu, ensure_ascii=False)
    assert '跳转方式' in text and '关键帧快速（落点可能偏移）' in text
    (OUT/'menu.json').write_text(json.dumps(menu, ensure_ascii=False, indent=2), encoding='utf-8')
    for selected in ['exact', 'keyframes']:
        mode(p, selected)
        for key, start, offset in [('RIGHT', 68.4, 5), ('LEFT', 68.4, -5), ('UP', 30.3, 60), ('DOWN', 100.3, -60)]:
            p.command('seek', start, 'absolute+exact')
            before = settle(p)
            p.command('keypress', key)
            actual = settle(p)
            target = before+offset
            if selected == 'exact':
                assert abs(actual-target) < .06, (key, target, actual)
            rows.append(dict(mode=selected, action=key, target=target, actual=actual, delta=actual-target))
        for drag in [False, True]:
            p.command('script-message-to', 'uosc', 'test-seek-cursor', '73.4', 'yes' if drag else 'no')
            actual = settle(p)
            state = p.get('user-data/seek-test')
            assert state['mode'] == selected and state['wheel_flag'] == selected
            assert p.get('pause') is True
            if selected == 'exact':
                assert abs(actual-73.4) < .06, actual
            rows.append(dict(mode=selected, action='drag-release' if drag else 'click', target=73.4, actual=actual, delta=actual-73.4))
        # 显式精准快捷键必须能覆盖关键帧模式。
        p.command('seek', 68.4, 'absolute+exact')
        settle(p)
        p.command('keypress', 'Shift+RIGHT')
        actual = settle(p)
        assert abs(actual-69.4) < .06, actual
        rows.append(dict(mode=selected, action='Shift+RIGHT', target=69.4, actual=actual))
    assert any(abs(row.get('delta', 0)) > .1 for row in rows if row['mode'] == 'keyframes')
    mode(p, 'keyframes')
finally:
    p.close()
    logs.append(p.log)

# 使用同一隔离配置重启，确认核心和时间轴都恢复所选方式；再改回精确复验。
for expected in ['keyframes', 'exact']:
    p = Player(args, 'seek-modes-restart-'+expected)
    try:
        p.wait_video()
        assert p.get('user-data/uosc/seek-mode') == expected
        assert p.get('hr-seek') in (['no', False] if expected == 'keyframes' else ['yes', True]), p.get('hr-seek')
        mode(p, 'exact')
    finally:
        p.close()
        logs.append(p.log)
for log in logs:
    errors = [s for s in log.read_text(encoding='utf-8').splitlines() if '[e]' in s or '[f]' in s or 'Lua error' in s]
    assert not errors, errors[:5]
assert 'seek_mode=exact' in (ROOT/'portable_config/script-opts/uosc.conf').read_text(encoding='utf-8')
result = dict(passed=True, source=str(source), default='exact', config=str(config), rows=rows,
              persistence=['keyframes', 'exact'], forced_exact_passed=True, errors=[])
(ROOT/'docs/modernization/seek-modes-20261017.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
print('PASS 方向键四向、时间轴点击／拖拽松手、滚轮标记、强制精准、双向重启记忆', flush=True)
print(json.dumps(rows, ensure_ascii=False, indent=2), flush=True)
