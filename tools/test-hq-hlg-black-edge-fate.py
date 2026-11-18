"""比较 HLG 黑边样本在双后端的 FP16 交换链输出与固定参考。"""
import argparse
import difflib
import json
import math
import runpy
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FATE = ROOT / 'tools/fate'
OUT = ROOT / 'tmp/modernization/hq-hlg-black-edge-fate'
NAME = 'hq-hlg-black-edge'


def fixture(sample):
    row = b''.join(struct.pack('<H', code) * sample['band_width'] for code in sample['luma_codes'])
    width, height = len(row) // 2, sample['height']
    chroma = struct.pack('<H', sample['neutral_chroma_code']) * (width * height // 2)
    source = OUT / (NAME + '.yuv')
    source.write_bytes((row * height + chroma) * 24)
    return source, width, height


def trial(backend, executable, sample, source, width, height):
    suffix = '-vulkan' if backend == 'vulkan' else ''
    probe = runpy.run_path(str(ROOT / f'tools/gpu-readback{suffix}.py'))
    output_width, output_height = width // 2, height // 2
    geometry = f'{output_width}x{output_height}'
    white = sample['reference_white_nits']
    options = [
        '--no-config', '--load-scripts=no', '--vo=gpu-next', f'--gpu-api={backend}',
        '--hwdec=no', '--gpu-shader-cache=no', '--no-audio', '--osc=no', '--osd-level=0',
        '--pause=yes', '--border=no', '--hidpi-window-scale=no',
        f'--geometry={geometry}', f'--autofit={geometry}', '--loop-file=inf',
        '--target-prim=bt.709', '--target-gamut=bt.2020', '--target-trc=scrgb',
        f'--target-peak={white}', f'--hdr-reference-white={white}', '--target-contrast=inf',
        '--target-colorspace-hint=yes', '--target-colorspace-hint-mode=target',
        '--target-colorspace-hint-strict=yes', '--hdr-compute-peak=no',
        '--hdr-contrast-recovery=0', '--dither-depth=no', '--dscale=catmull_rom',
        '--linear-downscaling=yes', '--correct-downscaling=yes', '--dscale-antiring=0.5',
        '--demuxer=rawvideo', '--demuxer-rawvideo-mp-format=yuv420p10',
        f'--demuxer-rawvideo-w={width}', f'--demuxer-rawvideo-h={height}',
        '--vf=format:primaries=bt.2020:gamma=hlg:colormatrix=bt.2020-ncl:colorlevels=limited',
    ]
    if backend == 'd3d11':
        options.extend(['--d3d11-output-format=rgba16f', '--d3d11-output-csp=linear'])
    player, reader = probe['create_player']([*options, str(source)], f'{NAME}-{backend}', executable)
    try:
        player.wait_video()
        source_params = player.get('video-out-params')
        assert source_params['gamma'] == 'hlg' and source_params['primaries'] == 'bt.2020', source_params
        target = player.get('video-target-params')
        assert target['gamma'] == 'scrgb' and target['pixelformat'] == 'rgba16hf', target
        frame = reader.read(player)
        shape = (frame.meta['width'], frame.meta['height'], frame.meta['format'])
        assert shape == (output_width, output_height, 10), frame.meta
        nonfinite = sum(
            not all(map(math.isfinite, frame.pixel(col, row)[:3]))
            for row in range(output_height) for col in range(output_width)
        )
        band = sample['band_width'] // 2
        centers = [frame.pixel(col, output_height // 2)[:3]
                   for col in range(band // 2, output_width, band)]
        black = all(abs(channel) <= 1e-6
                    for code, rgb in zip(sample['luma_codes'], centers) if code <= 64
                    for channel in rgb)
        ramp = [rgb for code, rgb in zip(sample['luma_codes'], centers) if code >= 64]
        ordered = all(all(low < high for low, high in zip(left, right))
                      for left, right in zip(ramp, ramp[1:]))
        return [
            f'{backend} nonfinite-rgb-pixels {nonfinite}',
            f"{backend} black-is-zero {'yes' if black else 'no'}",
            f"{backend} near-black-order-preserved {'yes' if ordered else 'no'}",
        ]
    finally:
        player.close()
        reader.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mpv', type=lambda path: Path(path).resolve(), default=ROOT / 'mpv.exe')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sample = json.loads((FATE / 'samples' / (NAME + '.json')).read_text(encoding='utf-8'))
    source, width, height = fixture(sample)
    actual = '\n'.join(line for backend in ('d3d11', 'vulkan')
                       for line in trial(backend, args.mpv, sample, source, width, height)) + '\n'
    (OUT / 'actual.txt').write_text(actual, encoding='utf-8', newline='\n')
    reference = (FATE / 'ref' / NAME).read_text(encoding='utf-8')
    if actual != reference:
        raise SystemExit(''.join(difflib.unified_diff(reference.splitlines(keepends=True),
                                                    actual.splitlines(keepends=True),
                                                    fromfile='ref', tofile='actual')))
    print(actual, end='')


if __name__ == '__main__':
    main()
