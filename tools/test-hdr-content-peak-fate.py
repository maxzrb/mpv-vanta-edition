"""真实 HEVC 静态元数据输入及独立映射参考；验证 MaxCLL 自动选择和生命周期。"""
import hashlib
import json
import runpy
import struct
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/hdr-content-peak-fate'
SAMPLE = json.loads((ROOT / 'tools/fate/samples/hdr-content-peak.json').read_text(encoding='utf-8'))
REF = runpy.run_path(str(ROOT / 'tools/color-map-reference.py'))
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
LABEL = 'hdr-content-peak'


def wait(player, predicate):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.05)
    raise AssertionError(dict(peak=player.get('user-data/hdr-content-peak'),
        color=player.get('user-data/color-target'), source=player.get('video-out-params'), vf=player.get('vf')))


def mine(player):
    return next((f for f in player.get('vf') or [] if f.get('label') == LABEL), None)


def fixture():
    size = SAMPLE['size']
    codes = [round(64 + 876 * REF['pq'](n / 10000)) for n in SAMPLE['gray_nits']]
    y = [codes[row // 64 * 4 + col // 64] for row in range(size) for col in range(size)]
    raw = struct.pack('<' + 'H' * len(y), *y) + struct.pack('<H', 512) * (2 * size * size)
    source = OUT / 'gray.yuv'
    source.write_bytes(raw * SAMPLE['frames'])
    media = {}
    for peak in SAMPLE['content_peaks']:
        target = OUT / f'pq-cll-{peak}.mkv'
        params = ('lossless=1:repeat-headers=1:pools=1:frame-threads=1:log-level=error:'
            'master-display=G(8500,39850)B(6550,2300)R(35400,14600)WP(15635,16450)L(10000000,10):'
            f'max-cll={peak},{55 if peak else 0}')
        subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
            '-f', 'rawvideo', '-pixel_format', 'yuv444p10le', '-video_size', f'{size}x{size}',
            '-framerate', str(SAMPLE['fps']), '-color_range', 'tv', '-colorspace', 'bt2020nc',
            '-color_primaries', 'bt2020', '-color_trc', 'smpte2084', '-i', str(source),
            '-c:v', 'libx265', '-preset', 'ultrafast', '-x265-params', params,
            '-color_range', 'tv', '-colorspace', 'bt2020nc', '-color_primaries', 'bt2020',
            '-color_trc', 'smpte2084', str(target)], check=True, timeout=30)
        decoded = subprocess.check_output([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel',
            'error', '-i', str(target), '-frames:v', '1', '-pix_fmt', 'yuv444p10le', '-f', 'rawvideo', '-'], timeout=15)
        assert decoded == raw, 'HEVC 无损回读改变了固定样本'
        media[peak] = target
    return media, codes, hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    policy = subprocess.check_output([str(ROOT / 'luajit.exe'),
        str(ROOT / 'tools/test-hdr-content-peak-lifecycle.lua')], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
    assert policy == (ROOT / 'tools/fate/ref/hdr-content-peak-policy').read_text(encoding='utf-8')
    (OUT / 'policy-actual.txt').write_text(policy, encoding='utf-8', newline='\n')
    print(policy, end='')
    media, codes, source_hash = fixture()
    results, lines = [], []
    disabled = Path(tempfile.mkdtemp(prefix='disabled-', dir=OUT))
    (disabled / 'script-opts').mkdir()
    (disabled / 'script-opts/hdr-content-peak.conf').write_text('enabled=no\n', encoding='utf-8', newline='\n')
    player = Player(['--config=yes', '--config-dir=' + str(disabled), '--vo=null',
        '--script=' + str(ROOT / 'portable_config/scripts/hdr-content-peak.lua')], 'hdr-content-peak-disabled')
    try:
        wait(player, lambda: (player.get('user-data/hdr-content-peak') or {}).get('reason') == '已禁用')
        assert mine(player) is None
        lines.append('options-file-loading PASS')
    finally:
        player.close()
    for backend in ('d3d11', 'vulkan'):
        module = 'gpu-readback.py' if backend == 'd3d11' else 'gpu-readback-vulkan.py'
        Probe = runpy.run_path(str(ROOT / 'tools' / module))['Probe']
        config = Path(tempfile.mkdtemp(prefix=backend + '-', dir=OUT))
        (config / 'files').mkdir()
        probe = Probe()
        player = Player(['--no-config', '--config-dir=' + str(config), '--load-auto-profiles=no',
            '--vo=gpu-next', '--gpu-api=' + backend, '--hwdec=no', '--ao=null', '--pause=yes',
            '--script=' + str(ROOT / 'portable_config/scripts/color-target.lua'),
            '--script=' + str(ROOT / 'portable_config/scripts/hdr-content-peak.lua'),
            '--script-opts=color-target-pipeline=hq', '--geometry=256x256', '--border=no',
            '--osc=no', '--osd-level=0'], 'hdr-content-peak-' + backend, before_resume=probe.attach)
        try:
            player.command('set_property', 'user-data/display-info', {'uid': 'content-peak',
                'hdr-status': 'unsupported', 'hdr-supported': False, 'max-luminance': 270})
            player.command('set_property', 'user-data/display-color', {'mode': 'wcg',
                'identity': 'content-peak', 'sdr_white_nits': SAMPLE['target_nits']})
            time.sleep(.2)
            for peak in SAMPLE['content_peaks']:
                player.command('loadfile', str(media[peak]), 'replace')
                player.wait_video()
                def ready():
                    source = player.get('video-params') or {}
                    output = player.get('video-out-params') or {}
                    return (source.get('max-cll', 0) == peak and source.get('max-luma') == 1000
                        and output.get('max-luma') == (peak or 1000) and bool(mine(player)) == bool(peak))
                wait(player, ready)
                frame = probe.read(player)
                actual = [frame.pixel(i % 4 * 64 + 32, i // 4 * 64 + 32)[:3] for i in range(16)]
                expected = [REF['unpq'](REF['spline']((code - 64) / 876,
                    REF['pq'](.001 / 10000), REF['pq']((peak or 1000) / 10000),
                    0, 0, REF['pq'](80 / 10000))) * 10000 / 80 for code in codes]
                error = max(abs(v - e) for rgb, e in zip(actual, expected) for v in rgb)
                assert error < SAMPLE['linear_tolerance'], (backend, peak, error, actual, expected)
                assert player.get('video-params')['max-luma'] == 1000
                assert player.get('hdr-compute-peak') in (False, 'no')
                assert player.get('hdr-contrast-recovery') == 0
                results.append(dict(backend=backend, max_cll=peak, source=player.get('video-params'),
                    output=player.get('video-out-params'), target=player.get('video-target-params'),
                    state=player.get('user-data/hdr-content-peak'), actual_linear=actual,
                    expected_linear=expected, max_linear_error=error, source_plane_sha256=source_hash))
            lines += [f'{backend} automatic-maxcll-independent-reference PASS',
                f'{backend} source-metadata-change-and-missing-fallback PASS']
            player.command('loadfile', str(media[97]), 'replace')
            player.wait_video()
            wait(player, lambda: mine(player) is not None)
            player.command('vf', 'add', '@user-crop:crop=256:256:0:0')
            wait(player, lambda: len(player.get('vf') or []) == 2)
            player.command('script-message', 'color-pipeline', 'standard')
            wait(player, lambda: mine(player) is None and (player.get('video-out-params') or {}).get('max-luma') == 1000)
            assert any(f.get('label') == 'user-crop' for f in player.get('vf'))
            player.command('script-message', 'color-pipeline', 'hq')
            wait(player, lambda: mine(player) is not None and (player.get('video-out-params') or {}).get('max-luma') == 97)
            assert any(f.get('label') == 'user-crop' for f in player.get('vf'))
            lines.append(f'{backend} standard-hq-and-user-filter-preservation PASS')
            player.command('vf', 'remove', '@' + LABEL)
            wait(player, lambda: (player.get('user-data/hdr-content-peak') or {}).get('state') == '外部已接管')
            time.sleep(.2)
            assert mine(player) is None
            player.command('script-message', 'refresh')
            wait(player, lambda: mine(player) is not None)
            lines.append(f'{backend} manual-filter-ownership-and-refresh PASS')
        finally:
            player.close()
            probe.close()
        log = player.log.read_text(encoding='utf-8')
        assert 'Lua error:' not in log and 'Failed compiling' not in log
    actual = '\n'.join(lines) + '\n'
    (OUT / 'actual.txt').write_text(actual, encoding='utf-8', newline='\n')
    (OUT / 'results.json').write_text(json.dumps(dict(passed=True, policy_cases=6, trials=results),
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    assert actual == (ROOT / 'tools/fate/ref/hdr-content-peak').read_text(encoding='utf-8')
    print(actual, end='')


if __name__ == '__main__':
    main()
