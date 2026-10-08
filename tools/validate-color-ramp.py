"""高位深灰阶／色块 GPU 截图回归；非交换链线性纹理或面板测量。"""
import json
from pathlib import Path
import runpy
import struct
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/validation'
OUT.mkdir(parents=True, exist_ok=True)


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


def read_png(path):
    # 支持 PNG 五种行过滤；直接保留 16bit 样本，不经过 8bit 图像转换。
    data = path.read_bytes()
    pos, compressed = 8, b''
    while pos < len(data):
        size = struct.unpack('>I', data[pos:pos + 4])[0]
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + size]
        if kind == b'IHDR': w, h, depth, color, _, _, interlace = struct.unpack('>IIBBBBB', body)
        if kind == b'IDAT': compressed += body
        pos += size + 12
    assert depth == 16 and color in [2, 6] and interlace == 0, (depth, color, interlace)
    channels = 3 if color == 2 else 4
    bpp, stride = channels * 2, w * channels * 2
    raw, rows, prev = zlib.decompress(compressed), [], bytearray(stride)
    for y in range(h):
        offset = y * (stride + 1)
        filt = raw[offset]
        row = bytearray(raw[offset + 1:offset + 1 + stride])
        for x in range(stride):
            a, b, c = row[x - bpp] if x >= bpp else 0, prev[x], prev[x - bpp] if x >= bpp else 0
            if filt == 1: value = a
            elif filt == 2: value = b
            elif filt == 3: value = (a + b) // 2
            elif filt == 4:
                p = a + b - c
                choices = [abs(p - a), abs(p - b), abs(p - c)]
                value = [a, b, c][choices.index(min(choices))]
            else: assert filt == 0; value = 0
            row[x] = (row[x] + value) & 255
        rows.append(struct.unpack('>' + 'H' * (w * channels), row))
        prev = row
    return w, h, channels, rows


def srgb_linear(value):
    value /= 65535
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def main():
    width, height = 1024, 32
    colors = [(7000, 14000, 28000), (55000, 3000, 12000), (0, 65535, 0), (65535, 0, 0)]
    expected, raw = [], b''
    for y in range(height):
        row = [(round(x * 65535 / (width - 1)),) * 3 if y < 16 else colors[min(3, x * 4 // width)] for x in range(width)]
        expected.append(row)
        raw += b'\0' + b''.join(struct.pack('>HHH', *rgb) for rgb in row)
    source = OUT / 'color-ramp-source.png'
    source.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 16, 2, 0, 0, 0))
                       + chunk(b'sRGB', b'\0') + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
    Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
    player = Player(['--no-config', '--vo=gpu-next', '--gpu-api=d3d11', '--hwdec=no', '--ao=null',
                     '--pause=yes', '--image-display-duration=inf', '--target-trc=srgb', '--target-prim=bt.709',
                     '--treat-srgb-as-power22=no', '--icc-profile-auto=no', '--screenshot-sw=no',
                     '--screenshot-high-bit-depth=yes', '--screenshot-format=png', str(source)], 'color-ramp')
    destination = OUT / 'color-ramp-gpu.png'
    try:
        player.wait_video()
        time.sleep(.5)
        assert player.command('screenshot-to-file', str(destination), 'video')['error'] == 'success'
        params = player.get('video-params')
    finally:
        player.close()
    w, h, channels, decoded = read_png(destination)
    assert (w, h) == (width, height)
    errors, linear_errors = [], []
    for y in [8, 24]:
        for x in range(width):
            for c in range(3):
                a, b = decoded[y][x * channels + c], expected[y][x][c]
                errors.append(abs(a - b))
                linear_errors.append(abs(srgb_linear(a) - srgb_linear(b)))
    unique = len(set(decoded[8][x * channels] for x in range(width)))
    result = dict(scope='sRGB 编码的 16bit GPU 截图；线性误差为截图逆 EOTF 推导，非中间纹理回读／面板测量',
                  source=params, maximum_code_error=max(errors), maximum_derived_linear_error=max(linear_errors),
                  unique_gray_levels=unique, threshold_code_error=128)
    # 粗粒度管线回归阈值，不用它建立播放器色准排名。
    assert max(errors) <= 128 and unique > 256, result
    (OUT / 'color-ramp-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('高位深 GPU 截图回归 PASS', result['maximum_code_error'], unique)


if __name__ == '__main__':
    main()
