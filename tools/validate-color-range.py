"""用 10bit YUV 全／有限范围端点检查真实 GPU 截图，避免黑白位误展开。"""
import json
from pathlib import Path
import runpy
import struct
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/validation'
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
read_png = runpy.run_path(str(ROOT / 'tools/validate-color-ramp.py'))['read_png']
w, h = 64, 32
y = b''.join(struct.pack('<H', [0, 64, 940, 1023][x * 4 // w]) for _ in range(h) for x in range(w))
uv = struct.pack('<H', 512) * (w * h // 2)
rows = []
for levels in ['tv', 'pc']:
    source, image = OUT / ('color-range-' + levels + '.mkv'), OUT / ('color-range-' + levels + '.png')
    subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'rawvideo', '-pixel_format', 'yuv420p10le', '-video_size', '64x32',
                    '-framerate', '1', '-color_range', levels, '-colorspace', 'bt709',
                    '-color_primaries', 'bt709', '-color_trc', 'bt709',
                    '-i', 'pipe:0', '-frames:v', '1', '-c:v', 'ffv1',
                    '-color_range', levels, '-colorspace', 'bt709', '-color_primaries', 'bt709',
                    '-color_trc', 'bt709', str(source)], input=y + uv, check=True, timeout=20)
    # 先回读样本，避免生成工具先改范围而误归因于播放器。
    decoded = subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-v', 'error', '-i', str(source),
                              '-frames:v', '1', '-pix_fmt', 'yuv420p10le', '-f', 'rawvideo', '-'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=20)
    assert [struct.unpack_from('<H', decoded.stdout, x * 2)[0] for x in [8, 24, 40, 56]] == [0, 64, 940, 1023]
    player = Player(['--no-config', '--vo=gpu-next', '--gpu-api=d3d11', '--hwdec=no', '--ao=null',
                     '--pause=yes', '--target-trc=srgb', '--target-prim=bt.709', '--target-contrast=inf',
                     '--treat-srgb-as-power22=no', '--screenshot-sw=no', '--screenshot-high-bit-depth=yes',
                     '--screenshot-format=png', str(source)], 'color-range-' + levels)
    try:
        player.wait_video(); time.sleep(.4)
        params = player.get('video-params')
        assert params['colorlevels'] == ('limited' if levels == 'tv' else 'full')
        assert player.command('screenshot-to-file', str(image), 'video')['error'] == 'success'
    finally:
        player.close()
    width, height, channels, pixels = read_png(image)
    values = [pixels[height // 2][(width * i // 4 + width // 8) * channels] for i in range(4)]
    assert values[0] <= 128 and values[3] >= 65535 - 128, values
    if levels == 'tv': assert values[1] <= 128 and values[2] >= 65535 - 128, values
    else: assert values[1] > 128 and values[2] < 65535 - 128, values
    rows.append(dict(range=levels, decoded=params, screenshot_values=values, passed=True))
(OUT / 'color-range-results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('10bit 全／有限范围 GPU 黑白端点回归 PASS')
