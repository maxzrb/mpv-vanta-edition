"""隔离验证可信 ICC 与峰值按显示器／桌面模式保存，以及同目标切集免重建。"""
import json
import runpy
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/validation'
helper = runpy.run_path(str(ROOT / 'tools/validate-color-target.py'))
Player, wait = helper['Player'], helper['wait']
config = Path(tempfile.mkdtemp(prefix='color-prefs-', dir=ROOT / 'tmp/modernization/isolated'))
(config / 'files').mkdir()
icc = str(ROOT / 'portable_config/icc/ITU-RBT709ReferenceDisplay.icc')
fixture = {'uid': 'fixture-A', 'hdr-status': 'off', 'hdr-supported': True,
           'max-luminance': '1000', 'min-luminance': '0.01', 'bit-depth': 10}
args = ['--config-dir=' + str(config), '--vo=gpu-next', '--gpu-api=d3d11',
        '--ao=null', '--pause=yes', '--script=' + str(ROOT / 'portable_config/scripts/color-target.lua'),
        str(OUT / 'hdr10.mkv')]
for launch in range(2):
    p = Player(args, 'color-preferences-' + str(launch))
    try:
        p.wait_video()
        native = {'mode': 'sdr', 'identity': 'native-A', 'system_icc': 'association-A.icc'}
        p.command('set_property', 'user-data/display-color', native)
        p.command('set_property', 'user-data/display-info', fixture)
        if launch == 0:
            p.command('script-message', 'color-icc', icc)
        s = wait(p, 'user-data/color-target', lambda s: s and s['mode'] == 'icc')
        assert p.get('icc-profile') == icc
        # 测试 ICC 只是文件／偏好流程夹具，不能视作当前面板校准。
        if launch == 0:
            p.command('set_property', 'user-data/display-info', {**fixture, 'uid': 'fixture-B'})
            wait(p, 'user-data/color-target', lambda s: s['mode'] == 'sdr')
            assert p.get('icc-profile') == ''
            p.command('set_property', 'user-data/display-info', fixture)
            wait(p, 'user-data/color-target', lambda s: s['mode'] == 'icc')
            assert p.get('icc-profile') == icc
            # 相同显示器的系统 ICC 关联改变，旧信任失效；恢复原关联可复用偏好。
            p.command('set_property', 'user-data/display-color', {**native, 'system_icc': 'association-B.icc'})
            wait(p, 'user-data/color-target', lambda s: s['mode'] == 'sdr')
            assert p.get('icc-profile') == ''
            p.command('set_property', 'user-data/display-color', native)
            wait(p, 'user-data/color-target', lambda s: s['mode'] == 'icc')
            assert p.get('icc-profile') == icc
            p.command('script-message', 'color-select', 'auto')
        p.command('set_property', 'user-data/display-info', {**fixture, 'hdr-status': 'on'})
        wait(p, 'user-data/color-target', lambda s: s['mode'] == 'hdr-scrgb')
        if launch == 0:
            p.command('script-message', 'color-peak', '900')
        s = wait(p, 'user-data/color-target', lambda s: s['mode'] == 'hdr-scrgb' and s['peak'] == 900)
        assert not s['manual']
        p.command('set_property', 'user-data/display-info', {**fixture, 'uid': 'fixture-B', 'hdr-status': 'on', 'max-luminance': '1100'})
        wait(p, 'user-data/color-target', lambda s: s['mode'] == 'hdr-scrgb' and s['peak'] == 1100)
        p.command('set_property', 'user-data/display-info', {**fixture, 'hdr-status': 'on'})
        wait(p, 'user-data/color-target', lambda s: s['mode'] == 'hdr-scrgb' and s['peak'] == 900)
        # 已生效目标切集，日志增量中不能出现管理器撤轨重建。
        offset = p.log.stat().st_size
        p.command('loadfile', str(OUT / 'hdr10.mkv'))
        p.wait_video()
        time.sleep(.5)
        wait(p, 'user-data/color-target', lambda s: s['mode'] == 'hdr-scrgb')
        fragment = p.log.read_bytes()[offset:].decode('utf-8', errors='replace')
        assert 'Set property: vid="no"' not in fragment
    finally:
        p.close()
    assert 'Lua error:' not in p.log.read_text(encoding='utf-8')
data = json.loads((config / 'files/color-target-preferences.json').read_text(encoding='utf-8'))
assert data['fixture-A|off']['icc'] == icc and data['fixture-A|on']['peak'] == 900
assert 'fixture-B|on' not in data
(OUT / 'color-preferences-results.json').write_text(json.dumps({'passed': True,
    'scope': '模拟显示身份／真实输出协商；ICC 文件为流程夹具，非面板校准',
    'preferences': data}, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print('PASS ICC／峰值跨启动与显示身份隔离；同 HDR 输出切集免撤轨')
