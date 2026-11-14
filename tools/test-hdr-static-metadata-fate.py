"""固定 PQ 灰阶及独立样条参考：区分母版峰值与内容峰值，不修改播放配置。"""
import hashlib
import json
import runpy
import struct
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/hdr-static-metadata-fate'
SAMPLE = json.loads((ROOT / 'tools/fate/samples/hdr-static-metadata.json').read_text(encoding='utf-8'))
REF = runpy.run_path(str(ROOT / 'tools/color-map-reference.py'))
HQ = runpy.run_path(str(ROOT / 'tools/test-hq-sdr-fate.py'))
Player = HQ['Player']


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # 原始整数码值由固定输入及 ST 2084 公式生成，参考值不从 GPU 拟合。
    codes = [REF['pq'](v / 10000) for v in SAMPLE['gray_nits']]
    HQ['fixture'].__globals__['OUT'] = OUT
    media = HQ['fixture']('static-gray', 'smpte2084', [codes] * SAMPLE['frames'])
    source_hash = hashlib.sha256(media.read_bytes()).hexdigest()
    expected = {}
    for variant in SAMPLE['variants']:
        peak = variant['mapping_peak_nits']
        values = []
        for code in codes:
            # 与固定有限范围 16 位输入的取整完全对应。
            actual_code = (round((16 + 219 * code) * 256) - 4096) / (219 * 256)
            mapped = REF['spline'](actual_code,
                REF['pq'](SAMPLE['minimum_nits'] / 10000), REF['pq'](peak / 10000),
                0, 0, REF['pq'](SAMPLE['target_nits'] / 10000))
            values.append(REF['unpq'](mapped) * 10000 / 80)
        expected[variant['name']] = values
    rows, lines = [], []
    for backend in ('d3d11', 'vulkan'):
        module = 'gpu-readback.py' if backend == 'd3d11' else 'gpu-readback-vulkan.py'
        Probe = runpy.run_path(str(ROOT / 'tools' / module))['Probe']
        config = Path(tempfile.mkdtemp(prefix=backend + '-', dir=OUT))
        (config / 'files').mkdir()
        probe = Probe()
        player = Player(['--no-config', '--config-dir=' + str(config), '--load-auto-profiles=no',
            '--vo=gpu-next', '--gpu-api=' + backend, '--hwdec=no', '--aid=no', '--ao=null',
            '--pause=yes', '--script=' + str(ROOT / 'portable_config/scripts/color-target.lua'),
            '--script-opts=color-target-pipeline=hq', '--geometry=256x256', '--border=no',
            '--osc=no', '--osd-level=0', str(media)], 'hdr-static-metadata-' + backend,
            before_resume=probe.attach)
        try:
            player.wait_video()
            player.command('set_property', 'user-data/display-info', {
                'uid': 'static-metadata', 'hdr-status': 'unsupported', 'hdr-supported': False,
                'max-luminance': 270})
            player.command('set_property', 'user-data/display-color', {
                'mode': 'wcg', 'identity': 'static-metadata', 'sdr_white_nits': SAMPLE['target_nits']})
            HQ['wait'](player, lambda s: s.get('mode') == 'sdr-acm')
            for variant in SAMPLE['variants']:
                peak = variant['mapping_peak_nits']
                result = player.command('vf', 'set', 'format=max-luma=' + str(peak)
                    + ':min-luma=' + str(SAMPLE['minimum_nits'])
                    + ':max_cll=' + str(SAMPLE['content_peak_nits']))
                assert result['error'] == 'success', result
                # 等待重新配置，所有样本帧相同，读回不会受帧推进影响。
                time.sleep(.25)
                frame = probe.read(player)
                assert frame.meta['format'] == 10, frame.meta
                measured = [frame.pixel(i % 4 * 64 + 32, i // 4 * 64 + 32)[:3] for i in range(16)]
                errors = [abs(v - wanted) for rgb, wanted in zip(measured, expected[variant['name']]) for v in rgb]
                assert max(errors) < SAMPLE['linear_tolerance'], (backend, variant, measured, expected, max(errors))
                source = player.get('video-out-params')
                assert source['gamma'] == 'pq' and source['pixelformat'] == 'yuv444p16', source
                assert source['max-luma'] == peak and source['max-cll'] == SAMPLE['content_peak_nits'], source
                assert player.get('hdr-compute-peak') in (False, 'no')
                assert player.get('hdr-contrast-recovery') == 0
                rows.append(dict(backend=backend, variant=variant['name'], source=source,
                    target=player.get('video-target-params'), expected_linear=expected[variant['name']],
                    actual_linear=measured, max_linear_error=max(errors), sample_sha256=source_hash))
                lines.append(f"{backend} {variant['name']} independent-spline-reference PASS")
            assert hashlib.sha256(media.read_bytes()).hexdigest() == source_hash
            lines.append(f'{backend} sample-file-unchanged PASS')
        finally:
            # 先退出测试播放器，避免运行中设备回调与 Frida 脱离互相等待。
            player.close()
            probe.close()
    actual = '\n'.join(lines) + '\n'
    (OUT / 'actual.txt').write_text(actual, encoding='utf-8', newline='\n')
    (OUT / 'results.json').write_text(json.dumps(dict(sample=SAMPLE, trials=rows,
        scope='固定输入、静态 HDR 元数据与独立样条数学参考；不代表面板光学色准'),
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    assert actual == (ROOT / 'tools/fate/ref/hdr-static-metadata').read_text(encoding='utf-8')
    print(actual, end='')


if __name__ == '__main__':
    main()
