"""生成 HDR 数学参考向量；不把数学复算当作 GPU 或显示器色准实测。"""
import argparse
import json
import math
import struct
from pathlib import Path


def pq_encode(nits):
    m1, m2 = 2610 / 16384, 2523 / 32
    c1, c2, c3 = 3424 / 4096, 2413 / 128, 2392 / 128
    value = max(0, min(1, nits / 10000)) ** m1
    return ((c1 + c2 * value) / (1 + c3 * value)) ** m2


def pq_decode(value):
    m1, m2 = 2610 / 16384, 2523 / 32
    c1, c2, c3 = 3424 / 4096, 2413 / 128, 2392 / 128
    value = max(0, min(1, value)) ** (1 / m2)
    return 10000 * (max(value - c1, 0) / (c2 - c3 * value)) ** (1 / m1)


def hlg_reference(rgb, peak=1000):
    # 零黑位的 BT.2100 参考条件；实际黑位和观看环境须另行纳入。
    a, b, c = 0.17883277, 0.28466892, 0.55991073
    scene = [v * v / 3 if v <= .5 else (math.exp((v - c) / a) + b) / 12 for v in rgb]
    luminance = sum(v * w for v, w in zip(scene, [.2627, .6780, .0593]))
    gamma = 1.2 + .42 * math.log10(peak / 1000)
    return [peak * luminance ** (gamma - 1) * v for v in scene]


def generate():
    pq = []
    for nits in [0, .005, .1, 1, 10, 80, 100, 203, 1000, 4000, 10000]:
        encoded = pq_encode(nits)
        decoded = pq_decode(encoded)
        assert math.isclose(decoded, nits, rel_tol=1e-10, abs_tol=1e-10)
        fp16 = struct.unpack('<e', struct.pack('<e', nits / 80))[0] * 80
        pq.append(dict(nits=nits, pq=encoded, decoded=decoded, scrgb=nits / 80,
                       fp16_nits=fp16, storage_error=fp16 - nits))
    hlg = [dict(encoded_rgb=v, linear_nits=hlg_reference(v)) for v in
           [(0, 0, 0), (.75, .75, .75), (.75, .25, .25), (.25, .75, .25), (.25, .25, .75)]]
    assert math.isclose(hlg[1]['linear_nits'][0], 203.1521453536661)
    # BT.2020 红原色转换后有负通道，线性 scRGB 参考不得先裁剪。
    red709 = [1.660491, -.124550, -.018151]
    assert red709[1] < 0 and red709[2] < 0
    return dict(scope='参考数学／FP16 存储量化，非 GPU 回读或仪器测量', pq=pq, hlg=hlg,
                bt2020_red_in_linear709=red709)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='tmp/modernization/color-reference.json')
    args = parser.parse_args()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(generate(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PQ／HLG／负值与 FP16 量化参考向量 PASS')
