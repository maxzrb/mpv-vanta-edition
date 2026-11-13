"""固定输入与参考输出的 HQ SDR 回归；使用真实 mpv，不改系统显示设置。"""
import json
import runpy
import struct
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/hq-sdr-fate'
OUT.mkdir(parents=True, exist_ok=True)
SAMPLE = json.loads((ROOT / 'tools/fate/samples/hq-sdr.json').read_text(encoding='utf-8'))
HELPER = runpy.run_path(str(ROOT / 'tools/test-hdr-gpu-reference.py'))
Player = HELPER['Player']
READBACK = runpy.run_path(str(ROOT / 'tools/gpu-readback.py'))


def fixture(name, transfer, blocks):
    # 样本为有限范围的中性灰；原始整数输入同时保留，便于独立复核。
    size = SAMPLE['size']
    frames = []
    for levels in blocks:
        y = [round((16 + 219 * levels[(row // 64) * 4 + col // 64]) * 256)
             for row in range(size) for col in range(size)]
        frames.append(struct.pack('<' + 'H' * len(y), *y)
                      + struct.pack('<H', 32768) * (size * size * 2))
    source, media = OUT / (name + '.yuv'), OUT / (name + '.mkv')
    source.write_bytes(b''.join(frames))
    subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'rawvideo', '-pixel_format', 'yuv444p16le', '-video_size', f'{size}x{size}',
                    '-framerate', str(SAMPLE['fps']), '-color_range', 'tv', '-colorspace', 'bt2020nc',
                    '-color_primaries', 'bt2020', '-color_trc', transfer, '-i', str(source),
                    '-c:v', 'ffv1', '-threads', '1', '-color_range', 'tv', '-colorspace', 'bt2020nc',
                    '-color_primaries', 'bt2020', '-color_trc', transfer, str(media)], check=True, timeout=30)
    return media


def wait(player, predicate):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        state = player.get('user-data/color-target') or {}
        if predicate(state):
            return state
        time.sleep(.05)
    raise AssertionError(player.get('user-data/color-target'))


def capture(player, probe, position):
    assert player.command('seek', position, 'absolute+exact')['error'] == 'success'
    deadline = time.monotonic() + 10
    while player.get('seeking') or abs((player.get('time-pos') or 0) - position) > .05:
        assert time.monotonic() < deadline, '样本定位超时'
        time.sleep(.05)
    frame = probe.read(player)
    assert frame.meta['format'] == 10, frame.meta
    return [frame.pixel(index % 4 * 64 + 32, index // 4 * 64 + 32)[:3] for index in range(16)]


def trial(backend, sdr, pq):
    config = Path(tempfile.mkdtemp(prefix=backend + '-', dir=OUT))
    (config / 'files').mkdir()
    probe = READBACK['Probe']()
    if backend == 'vulkan':
        # Vulkan 使用同一原始交换链读回工具的后端实现。
        probe = runpy.run_path(str(ROOT / 'tools/gpu-readback-vulkan.py'))['Probe']()
    p = Player(['--no-config', '--config-dir=' + str(config), '--load-auto-profiles=no',
                '--vo=gpu-next', '--gpu-api=' + backend, '--hwdec=no', '--ao=null', '--pause=yes',
                '--script=' + str(ROOT / 'portable_config/scripts/color-target.lua'),
                '--script-opts=color-target-pipeline=hq', '--geometry=256x256', '--border=no',
                '--osc=no', '--osd-level=0', str(sdr)],
               'hq-sdr-fate-' + backend, before_resume=probe.attach)
    output = []
    try:
        p.wait_video()
        display = {'uid': 'fate-A', 'hdr-status': 'unsupported', 'hdr-supported': False,
                   'max-luminance': 270}
        system = {'mode': 'wcg', 'identity': 'fate-A', 'sdr_white_nits': 80}
        p.command('set_property', 'user-data/display-info', display)
        p.command('set_property', 'user-data/display-color', system)
        wait(p, lambda s: s.get('mode') == 'sdr-acm')
        target = p.get('video-target-params')
        assert target['gamma'] == 'scrgb' and target['pixelformat'] == 'rgba16hf', target
        assert p.get('hdr-compute-peak') in ('no', False), p.get('hdr-compute-peak')
        # 先校验原始 FP16 交换链读回标尺，不经过截图的独立重渲染路径。
        calibration = OUT / 'calibrate.glsl'
        calibration.write_text('//!HOOK OUTPUT\n//!BIND HOOKED\n//!DESC 测试：固定读回标尺\n'
                               'vec4 hook() { return vec4(0.25,0.5,0.75,1.0); }\n',
                               encoding='utf-8', newline='\n')
        p.command('set_property', 'glsl-shaders', [str(calibration)])
        measured = capture(p, probe, .25)
        assert max(abs(a - b) for rgb in measured for a, b in zip(rgb, [.25, .5, .75])) < .0001, (backend, measured)
        p.command('set_property', 'glsl-shaders', [])
        observed = capture(p, probe, .25)
        for index, code in enumerate(SAMPLE['sdr_codes']):
            encoded = (round((16 + 219 * code) * 256) - 4096) / (219 * 256)
            expected = encoded / 12.92 if encoded <= .04045 else ((encoded + .055) / 1.055) ** 2.4
            assert max(abs(v - expected) for v in observed[index]) < .002, (index, observed[index], expected)
        output.append(f'{backend} sdr-gray-reference PASS')
        p.command('loadfile', str(pq), 'replace')
        p.wait_video()
        p.command('set_property', 'pause', True)
        p.command('vf', 'add', 'format=max-luma=1000:max_cll=1000')
        wait(p, lambda s: s.get('mode') == 'sdr-acm')
        dark = capture(p, probe, .25)[0]
        bright = capture(p, probe, 1.25)[0]
        assert max(abs(a - b) for a, b in zip(dark, bright)) < .002, (dark, bright)
        output.append(f'{backend} pq-surround-invariance PASS')
        assert float(p.get('target-peak')) == 80 and float(p.get('hdr-reference-white')) == 80
        p.command('set_property', 'user-data/display-color', {**system, 'sdr_white_nits': 0})
        wait(p, lambda s: '回退' in s.get('sdr_reference_source', ''))
        assert float(p.get('hdr-reference-white')) == 80
        p.command('set_property', 'user-data/display-info', {**display, 'uid': 'fate-B', 'max-luminance': 1000})
        wait(p, lambda s: s.get('display_id') == 'fate-B')
        assert float(p.get('hdr-reference-white')) == 80, '标称峰值不得替代 SDR 白位'
        p.command('set_property', 'user-data/display-color', {**system, 'identity': 'fate-B'})
        wait(p, lambda s: s.get('sdr_reference_source') == '系统 SDR 参考白')
        output.append(f'{backend} system-white-or-fallback PASS')
        p.command('set_property', 'hdr-compute-peak', 'yes')
        wait(p, lambda s: s.get('manual') is True)
        p.command('script-message', 'color-select', 'auto')
        wait(p, lambda s: s.get('manual') is False)
        assert p.get('hdr-compute-peak') in ('no', False)
        p.command('script-message', 'color-pipeline', 'standard')
        wait(p, lambda s: s.get('pipeline') == 'standard')
        assert p.get('hdr-compute-peak') == 'auto'
        output.append(f'{backend} manual-override-and-restore PASS')
    finally:
        probe.close()
        p.close()
    log = p.log.read_text(encoding='utf-8')
    assert 'Lua error:' not in log and 'Failed compiling' not in log
    return output


def main():
    codes = SAMPLE['sdr_codes'] + [0] * 11
    sdr = fixture('sdr-gray', 'iec61966-2-1', [codes] * SAMPLE['frames'])
    pq = HELPER['pq_encode']
    blocks = [[pq(SAMPLE['pq_probe_nits'])] + [pq(surround)] * 15
              for surround in SAMPLE['pq_surround_nits'] for _ in range(SAMPLE['frames'] // 2)]
    media = fixture('pq-surround', 'smpte2084', blocks)
    actual = '\n'.join(line for backend in ('d3d11', 'vulkan') for line in trial(backend, sdr, media)) + '\n'
    (OUT / 'actual.txt').write_text(actual, encoding='utf-8', newline='\n')
    reference = (ROOT / 'tools/fate/ref/hq-sdr').read_text(encoding='utf-8')
    assert actual == reference, (actual, reference)
    print(actual, end='')


if __name__ == '__main__':
    main()
