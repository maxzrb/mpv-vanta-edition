"""强制兼容回退，核验异步查询关闭、一次性显示和切片清理。"""
import runpy
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
module = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))
player = module['Player'](['--no-config', '--load-scripts=no', '--load-stats-overlay=no',
                          '--script=' + str(ROOT / 'portable_config/scripts/stats.lua'),
                          '--script-opts=stats-native_metrics=no', '--vo=null',
                          'av://lavfi:testsrc2=size=320x180:rate=24'], 'stats-fallback-lifecycle')
try:
    player.wait_video()
    player.command('script-binding', 'stats/display-stats-toggle')
    deadline = time.monotonic() + 3
    while not player.get('user-data/stats/system-pending'):
        assert time.monotonic() < deadline
        time.sleep(.01)
    player.command('script-binding', 'stats/display-stats-toggle')
    time.sleep(1)
    assert player.get('user-data/stats/system-pending') is False
    assert player.get('user-data/stats/subprocess-count') == 1
    player.command('script-binding', 'stats/display-stats')
    time.sleep(4.5)
    assert player.get('user-data/stats/system-pending') is False
    assert player.get('user-data/stats/toggled') is False
    player.command('script-binding', 'stats/display-stats-toggle')
    player.command('loadfile', 'av://lavfi:testsrc2=size=320x180:rate=30', 'replace')
    time.sleep(1)
    assert player.get('user-data/stats/subprocess-count') <= 3
    print('PASS：关闭取消、一次性显示清理、切片无重叠')
finally:
    player.close()
