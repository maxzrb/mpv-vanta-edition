"""验证主色彩模式的首次默认、往返切换、跨启动记忆与实际输出。"""
import json
import runpy
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/color-modes-20261012'
OUT.mkdir(parents=True, exist_ok=True)
helper = runpy.run_path(str(ROOT / 'tools/validate-color-target.py'))
Player, wait = helper['Player'], helper['wait']
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']


def stable(p, pipeline, mode=None):
    return wait(p, 'user-data/color-target', lambda s: s and s['pipeline'] == pipeline
                and s['status'] == '可用' and (mode is None or s['mode'] == mode))


def capture_state(p):
    return {k: p.get(k) for k in ('user-data/color-target', 'video-params', 'video-target-params',
            'vid', 'pause', 'time-pos', 'scale', 'dscale', 'cscale', 'linear-downscaling', 'libplacebo-opts')}


def menu_state(p, pipeline):
    def collect(value):
        if isinstance(value, dict):
            if value.get('title', '') in ('标准', 'HQ 高色准'):
                yield value
            for v in value.values():
                yield from collect(v)
        elif isinstance(value, list):
            for v in value:
                yield from collect(v)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        rows = list(collect(p.get('menu-data') or p.get('user-data/menu/items')))
        if len(rows) == 2 and all(('checked' in row.get('state', [])) ==
                                (row['title'].startswith('HQ') == (pipeline == 'hq')) for row in rows):
            return rows
        time.sleep(.1)
    raise AssertionError(('菜单勾选未跟随主模式', pipeline, rows))


def main():
    results = []
    for backend in ('d3d11', 'vulkan'):
        config = create_config('color-modes-' + backend)
        media = ROOT / 'tmp/modernization/validation/sdr8.mkv'
        assert media.exists(), media
        args = ['--config-dir=' + str(config), '--gpu-api=' + backend, '--ao=null', '--pause=yes',
                '--geometry=640x360', '--loop-file=inf', str(media)]
        for launch in range(3):
            p = Player(args, 'color-modes-' + backend + '-' + str(launch))
            try:
                p.wait_video()
                expected = 'hq' if launch == 1 else 'standard'
                stable(p, expected)
                menu_state(p, expected)
                start = capture_state(p)
                if launch == 0:
                    assert not (config / 'files/color-pipeline-preferences.json').exists()
                    s = start['user-data/color-target']['actual_settings']
                    for key in ('target-prim', 'target-trc', 'target-colorspace-hint',
                                'd3d11-output-format', 'd3d11-output-csp', 'treat-srgb-as-power22'):
                        assert s[key] == 'auto', (key, s[key])
                    assert s['hdr-contrast-recovery'] == .3
                    assert start['libplacebo-opts']['lut3d_size_I'] == '48'
                    # 显示器通知／切集不改变主模式；外部覆盖仍能暂缓自动写回。
                    p.command('set_property', 'target-trc', 'gamma2.4')
                    wait(p, 'user-data/color-target', lambda s: s['status'] == '外部覆盖')
                    p.command('loadfile', str(media)); p.wait_video(); time.sleep(.25)
                    assert p.get('target-trc') == 'gamma2.4'
                    p.command('script-message', 'color-pipeline', 'standard')
                    stable(p, 'standard')
                    p.command('script-message', 'color-pipeline', 'hq')
                    stable(p, 'hq')
                    menu_state(p, 'hq')
                    hq = capture_state(p)
                    assert hq['libplacebo-opts']['lut3d_size_I'] == '96'
                    assert hq['libplacebo-opts']['lut3d_size_C'] == '64'
                    assert hq['user-data/color-target']['actual_settings']['hdr-contrast-recovery'] == 0
                    for key in ('scale', 'dscale', 'cscale', 'linear-downscaling'):
                        assert hq[key] == start[key], key
                    assert hq['video-params'] == start['video-params'], (start['video-params'], hq['video-params'])
                    assert hq['pause'] is True and hq['vid'] == start['vid']
                    assert abs(hq['time-pos'] - start['time-pos']) < .1
                    # 同模式重选不能额外撤视频轨；新的表对象也必须按内容比较。
                    offset = p.log.stat().st_size
                    p.command('script-message', 'color-pipeline', 'hq'); stable(p, 'hq'); time.sleep(.25)
                    fragment = p.log.read_bytes()[offset:].decode('utf-8', errors='replace')
                    assert 'Set property: vid="no"' not in fragment
                elif launch == 1:
                    p.command('script-message', 'color-pipeline', 'standard'); stable(p, 'standard')
                    menu_state(p, 'standard')
                    assert p.get('libplacebo-opts')['lut3d_size_C'] == '32'
                    assert p.get('d3d11-output-format') == 'auto'
                    assert p.get('d3d11-output-csp') == 'auto'
                else:
                    assert p.get('target-trc') == 'auto'
                    # 既有目标入口明确转入 HQ，避免“信任 ICC”选择被标准模式吞掉。
                    p.command('script-message', 'color-select', 'sdr'); stable(p, 'hq')
                    assert p.get('user-data/color-target')['requested'] == 'sdr'
                    p.command('script-message', 'color-pipeline', 'standard'); stable(p, 'standard')
                results.append(dict(backend=backend, launch=launch, startup=start, final=capture_state(p)))
            finally:
                p.close()
            log = p.log.read_text(encoding='utf-8', errors='replace')
            assert 'Lua error:' not in log
            assert 'Error parsing option' not in log
        saved = json.loads((config / 'files/color-pipeline-preferences.json').read_text(encoding='utf-8'))
        assert saved == {'pipeline': 'standard'}
    (OUT / 'modes-results.json').write_text(json.dumps(dict(passed=True, trials=results), ensure_ascii=False,
                                          indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS 双后端全脚本：首次标准／HQ 与标准跨启动记忆／源参数与缩放不变／免重复重建／外部覆盖')


if __name__ == '__main__':
    main()
