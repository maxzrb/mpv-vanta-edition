"""实际菜单交换链读回，比较标准／线性输出的感知噪点强度与无菜单画面。"""
import argparse
import hashlib
import json
import math
import runpy
import struct
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/menu-grain-20261012'
OUT.mkdir(parents=True, exist_ok=True)
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']


def srgb(linear):
    return 12.92 * linear if linear <= .0031308 else 1.055 * linear ** (1 / 2.4) - .055


def linear(value, target):
    trc = target['gamma']
    low = target.get('min-luma', 0) / target.get('max-luma', 80)
    if trc == 'scrgb':
        return value
    if trc == 'linear':
        return value
    if trc == 'bt.1886':
        return ((1 - low ** (1 / 2.4)) * value + low ** (1 / 2.4)) ** 2.4
    if trc == 'srgb':
        return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
    if trc.startswith('gamma'):
        return value ** float(trc[5:])
    raise AssertionError(trc)


def perceptual(frame, target):
    # BT.709 白点相同；使用统一 sRGB 感知编码比较 UI 纹理，不混比 FP16 和 RGB10 的码值。
    assert target['primaries'] == 'bt.709', target
    return [[tuple(srgb(max(0, linear(v, target))) for v in frame.pixel(x, y)[:3])
             for x in range(frame.meta['width'])] for y in range(frame.meta['height'])]


def png(path, pixels):
    h = len(pixels); w = len(pixels[0])
    raw = b''.join(b'\0' + bytes(round(min(1, max(0, v)) * 255)
                   for pixel in row for v in pixel) for row in pixels)
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def trial(config, backend, pipeline, noise, match, background):
    api = runpy.run_path(str(ROOT / 'tools' / ('gpu-readback.py' if backend == 'd3d11' else 'gpu-readback-vulkan.py')))
    tag = f'{backend}-{pipeline}-{noise}-{match}-{background}'
    color = '%02x%02x%02x' % ((background,) * 3)
    p, probe = api['create_player'](['--config-dir=' + str(config), '--gpu-api=' + backend, '--ao=null',
        '--hwdec=no', '--pause=yes', '--osd-level=0', '--osc=no', '--border=no', '--title-bar=no',
        '--geometry=800x500', '--autofit=800x500', '--autofit-smaller=800x500',
        '--script-opts-append=color-target-pipeline=' + ('hq' if pipeline == 'icc' else pipeline),
        '--script-opts-append=uosc-menu_frosted_noise=' + str(noise),
        '--script-opts-append=uosc-menu_frosted_match=' + ('yes' if match else 'no'),
        '--vf=format=gamma=bt.1886', 'av://lavfi:color=c=0x' + color + ':s=800x500:r=24'], 'menu-grain-' + tag)
    try:
        p.wait_video()
        until = time.monotonic() + 8
        while True:
            s = p.get('user-data/color-target')
            if s and s['pipeline'] == ('hq' if pipeline == 'icc' else pipeline) and s['status'] == '可用': break
            assert time.monotonic() < until, s
            time.sleep(.1)
        if pipeline == 'icc':
            p.command('script-message', 'color-select', 'icc')
            until = time.monotonic() + 8
            while True:
                s = p.get('user-data/color-target')
                if s and s['requested'] == 'icc' and s['status'] == '可用': break
                assert time.monotonic() < until, s
                time.sleep(.1)
        # 先读无菜单图像，随后以同一几何打开空白菜单，隔离纹理和文字／悬停。
        time.sleep(.3)
        before = probe.read(p)
        data = dict(type='grain-study', min_width=400, items=[dict(title=' ', selectable=False) for _ in range(6)])
        p.command('script-message-to', 'uosc', 'open-menu', json.dumps(data))
        time.sleep(.5)
        frame = probe.read(p)
        target = p.get('video-target-params')
        pixels = perceptual(frame, target)
        png(OUT / (tag + '.png'), pixels)
        # 主面板中心区域远离圆角／高光／文字，保留细噪点及不变的分隔线。
        roi = [pixels[y][x] for y in range(195, 305) for x in range(300, 500)]
        raw = b''.join(frame.data[y * frame.meta['stride']:y * frame.meta['stride'] + 800 * (8 if frame.meta['format'] == 10 else 4)]
                       for y in range(500))
        (OUT / (tag + '.rgba')).write_bytes(raw)
        bare = b''.join(before.data[y * before.meta['stride']:y * before.meta['stride'] + 800 * (8 if before.meta['format'] == 10 else 4)]
                        for y in range(500))
        (OUT / (tag + '-bare.rgba')).write_bytes(bare)
        size = 8 if before.meta['format'] == 10 else 4
        # 页脚进度和标题栏属于动态 UI；单独核对它们之外的实际视频像素。
        clean = b''.join(before.data[y * before.meta['stride'] + 50 * size:y * before.meta['stride'] + 750 * size]
                         for y in range(50, 450))
        return dict(tag=tag, backend=backend, pipeline=pipeline, noise=noise, match=match, background=background,
                    target=target, color_state=s, roi=roi, without_menu_sha256=hashlib.sha256(bare).hexdigest(),
                    clean_video_sha256=hashlib.sha256(clean).hexdigest(), bare_format=before.meta['format'])
    finally:
        p.close(); probe.close()
        assert 'Lua error:' not in p.log.read_text(encoding='utf-8', errors='replace')


def live_trial(config, backend):
    # 仅在隔离副本增加诊断入口，核对切换期间的标准参考，不给活动脚本增加接口。
    with (config / 'scripts/uosc/main.lua').open('a', encoding='utf-8', newline='\n') as stream:
        stream.write("\nmp.register_script_message('frosted-probe', function() "
                     "mp.set_property_native('user-data/frosted-probe', "
                     "{target=state.menu_target, reference=state.menu_standard_target, match=options.menu_frosted_match}) end)\n")
    api = runpy.run_path(str(ROOT / 'tools' / ('gpu-readback.py' if backend == 'd3d11' else 'gpu-readback-vulkan.py')))
    p, probe = api['create_player'](['--config-dir=' + str(config), '--gpu-api=' + backend, '--ao=null',
        '--pause=yes', '--geometry=800x500', '--autofit=800x500', '--border=no', '--title-bar=no',
        '--osd-level=0', '--vf=format=gamma=bt.1886', 'av://lavfi:color=c=black:s=800x500:r=24'],
        'menu-grain-live-' + backend)
    rows = []
    try:
        p.wait_video(); time.sleep(.6)
        p.command('script-message-to', 'uosc', 'show-submenu-blurred', '画面 > 色彩'); time.sleep(.5)
        for tag, pipeline, match in [('standard', 'standard', 'yes'), ('hq-before', 'hq', 'no'),
                                    ('hq-after', 'hq', 'yes'), ('standard-return', 'standard', 'yes'),
                                    ('hq-return', 'hq', 'yes')]:
            opts = p.get('script-opts') or {}
            opts['uosc-menu_frosted_match'] = match
            p.command('set_property', 'script-opts', opts)
            p.command('script-message', 'color-pipeline', pipeline); time.sleep(.9)
            p.command('script-message-to', 'uosc', 'frosted-probe'); time.sleep(.1)
            state = p.get('user-data/frosted-probe')
            assert state['reference']['gamma'] == 'bt.1886', state
            assert state['reference']['pipeline'] == 'standard' and state['target']['pipeline'] == pipeline, state
            assert state['match'] == (match == 'yes'), state
            p.command('show-text', ''); time.sleep(.1)
            frame = probe.read(p); target = p.get('video-target-params')
            png(OUT / ('actual-' + backend + '-' + tag + '.png'), perceptual(frame, target))
            size = 8 if frame.meta['format'] == 10 else 4
            # 色彩子菜单内部固定几何，排除动态页脚／顶部 OSD。
            panel = b''.join(frame.data[y * frame.meta['stride'] + 300 * size:y * frame.meta['stride'] + 490 * size]
                             for y in range(185, 285))
            rows.append(dict(tag=tag, state=state, target=target, panel_sha256=hashlib.sha256(panel).hexdigest()))
            print('实际菜单切换', backend, tag, state, flush=True)
        assert rows[1]['panel_sha256'] != rows[2]['panel_sha256'], '实际菜单未应用校正'
        assert rows[0]['panel_sha256'] == rows[3]['panel_sha256'], '返回标准未恢复原菜单'
        assert rows[2]['panel_sha256'] == rows[4]['panel_sha256'], '往返切换后 HQ 材质漂移'
    finally:
        p.close(); probe.close()
        assert 'Lua error:' not in p.log.read_text(encoding='utf-8', errors='replace')
    (OUT / ('live-switch-' + backend + '.json')).write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--backend', default='d3d11', choices=['d3d11', 'vulkan'])
    parser.add_argument('--background', type=int, default=0)
    parser.add_argument('--match', action='store_true'); parser.add_argument('--include-icc', action='store_true')
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    included = {'uosc', 'color-target.lua', 'display-color.lua', 'display-info.dll'}
    if args.live: included.add('dyn_menu.lua')
    config = create_config('menu-grain', exclude_scripts=[p.name for p in (ROOT / 'portable_config/scripts').iterdir() if p.name not in included])
    if args.live:
        live_trial(config, args.backend)
        return
    rows = []
    for pipeline in (('standard', 'hq', 'icc') if args.include_icc else ('standard', 'hq')):
        pair = [trial(config, args.backend, pipeline, noise, args.match, args.background) for noise in (0, .05)]
        delta = [b[c] - a[c] for a, b in zip(pair[0]['roi'], pair[1]['roi']) for c in range(3)]
        rms = math.sqrt(sum(v * v for v in delta) / len(delta))
        values = sorted(delta)
        row = dict(pipeline=pipeline, noise_rms=rms, mean=sum(delta)/len(delta), p99=values[int(len(values)*.99)],
                   target=pair[1]['target'], without_menu_pixels_exact=pair[0]['without_menu_sha256']==pair[1]['without_menu_sha256'],
                   clean_video_pixels_exact=pair[0]['clean_video_sha256']==pair[1]['clean_video_sha256'], trials=pair)
        rows.append(row); print(pipeline, rms, row['p99'], pair[1]['target'], flush=True)
        assert rms > .001, ('菜单或噪点没有实际绘制', pipeline, rms)
        assert row['clean_video_pixels_exact'], ('噪点选项影响了视频区域', pipeline)
    name = f'grain-{args.backend}-{args.background}-{args.match}.json'
    (OUT / name).write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('HQ／标准纹理 RMS 比', rows[1]['noise_rms'] / rows[0]['noise_rms'])


if __name__ == '__main__':
    main()
