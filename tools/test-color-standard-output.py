"""将标准模式与继承色彩参数的静态基线逐字节比较，保持当前核心及通用修复。"""
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/color-modes-20261012'
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']
gpu = runpy.run_path(str(ROOT / 'tools/gpu-pipeline-readback.py'))
wait = runpy.run_path(str(ROOT / 'tools/validate-color-target.py'))['wait']


def packed(row):
    meta, raw = row
    size = 8 if meta['format'] == 10 else 4
    assert meta['format'] in (10, 24, 28, 87), meta
    return b''.join(raw[y * meta['stride']:y * meta['stride'] + meta['width'] * size]
                    for y in range(meta['height']))


def main():
    results = []
    for backend in ('d3d11', 'vulkan'):
        configs = {}
        for variant in ('static', 'standard'):
            included = {'color-range-fix.lua'} | ({'color-target.lua'} if variant == 'standard' else set())
            excluded = [p.name for p in (ROOT / 'portable_config/scripts').iterdir() if p.name not in included]
            configs[variant] = create_config('standard-output-' + variant + '-' + backend, exclude_scripts=excluded)
        for source in ('sdr8', 'quality-sdr10', 'wide-sdr', 'hdr10', 'hlg'):
            media = ROOT / 'tmp/modernization/validation' / (source + '.mkv')
            captures = []
            for variant, config in configs.items():
                p, probe = gpu['create_player'](['--config-dir=' + str(config), '--gpu-api=' + backend,
                    '--hwdec=no', '--ao=null', '--pause=yes', '--sid=no', '--osd-level=0', '--osc=no',
                    '--geometry=256x256', '--autofit=256x256', '--autofit-smaller=256x256',
                    '--loop-file=inf', str(media)], 'standard-output-' + variant + '-' + source + '-' + backend, backend)
                try:
                    p.wait_video()
                    if variant == 'standard':
                        wait(p, 'user-data/color-target', lambda s: s and s['mode'] == 'standard')
                    rows = probe.read(p, force_redraw=True)
                    final = next(row for row in rows if row[0]['phase'] == 'present')
                    captures.append((packed(final), final[0], p.get('video-params'), p.get('video-target-params')))
                finally:
                    p.close(); probe.close()
                assert 'Lua error:' not in p.log.read_text(encoding='utf-8', errors='replace')
            a, b = captures
            assert a[0] == b[0], (backend, source, sum(x != y for x, y in zip(a[0], b[0])))
            assert a[1]['format'] == b[1]['format'] and a[1]['color_space'] == b[1]['color_space']
            assert a[2] == b[2] and a[3] == b[3]
            results.append(dict(backend=backend, source=source, all_rgba_bytes_exact=True,
                                sha256=hashlib.sha256(a[0]).hexdigest(), bytes=len(a[0]),
                                target=b[3], output_format=b[1]['format'], color_space=b[1]['color_space']))
            print('PASS standard/static', backend, source, flush=True)
    (OUT / 'standard-output-results.json').write_text(json.dumps(dict(passed=True, trials=results),
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
