"""汇总真实 GPU 软件色彩验收；保留失败，不能用后端一致代替独立参考。"""
import hashlib
import json
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/pipeline-validation-20261011'
DEST = ROOT / 'docs/modernization/color-pipeline-results-20261011.json'


def main():
    names = {
        'matrix': 'pipeline-results.json',
        'hdr_gray_scaling': 'pipeline-hdr-results.json',
        'classic_matrix_comparison': 'pipeline-classic-results.json',
        'icc': 'pipeline-icc-results.json',
        'op_color_frame': 'op-source-results.json',
        'readback_invariance': 'readback-invariance.json',
        'gamut_before_after': 'acm-gamut-closure.json',
        'full_range_midpoint': 'full-range-midpoint.json',
        'range_conversion_candidate': 'range-candidate-results.json',
        'range_dense_and_hdr': 'range-dense-results.json',
    }
    results = {key: json.loads((OUT / name).read_text(encoding='utf-8')) for key, name in names.items()}
    assert len(results['matrix']) == 48
    assert len(results['range_dense_and_hdr']) == 16
    assert all(row['requested_position'] == 5 and row['nontrivial_reference_range'][1] > .1
               for row in results['op_color_frame']), '真实色彩样片不能被黑场结果替代'
    timing = json.loads((OUT / 'gamut-timings.json').read_text(encoding='utf-8'))
    range_timing = json.loads((OUT / 'range-timings.json').read_text(encoding='utf-8'))
    summaries = []
    for source in ('av1', 'hevc'):
        for backend in ('d3d11', 'vulkan'):
            rows = [row for row in timing if row['source'] == source and row['backend'] == backend]
            assert [row['baseline'] for row in rows] == [True, False, False, True]
            before = statistics.mean(row['color_end_median_ns'] for row in rows if row['baseline'])
            after = statistics.mean(row['color_end_median_ns'] for row in rows if not row['baseline'])
            summaries.append(dict(source=source, backend=backend, before_ms=before / 1e6,
                                  after_ms=after / 1e6, reduction_percent=(before-after)/before*100))
    evidence = {}
    for backend in ('d3d11', 'vulkan'):
        graph = json.loads((OUT / f'12-1-0-{backend}-graph.json').read_text(encoding='utf-8'))
        manifest = json.loads((OUT / f'12-1-0-{backend}-manifest.json').read_text(encoding='utf-8'))
        if backend == 'vulkan':
            assert all(s['float_widths'] == [32] and s['relaxed_precision_decorations'] == 0
                       for s in manifest['shader_types'])
        else:
            shaders = [m for m in graph if m.get('shader')]
            assert shaders and all(m.get('shader_ir') and 'min16' not in m['shader_ir'] for m in shaders)
        evidence[backend] = {
            'graph': [{k: m[k] for k in ('sequence', 'phase', 'width', 'height', 'format', 'color_space') if k in m}
                      for m in graph],
            'compiled_shader_float_widths': [32],
            'vulkan_relaxed_precision_decorations': 0 if backend == 'vulkan' else None,
            'shader_count': len(manifest['shader_types']) if backend == 'vulkan' else manifest['shaderSources'],
            'main_intermediate': 'RGBA16F',
        }
    hashes = {name: hashlib.sha256((OUT/name).read_bytes()).hexdigest()
              for name in list(names.values()) + ['gamut-timings.json', 'range-timings.json']}
    failures = [row for row in results['matrix'] if not row['reference_passed']]
    summary = {
        'generated_at': datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),
        'software_acceptance_passed': False,
        'acceptance_reasons': ['全范围 10/12bit 色度中点使用了存储深度，而非信号深度；10bit 六组独立参考失败',
                               '默认 perceptual 色域映射和自适应 HDR→SDR 的完整独立算法参考尚未建立'],
        'physical_measurement_required': False,
        'environment': {'cpu': 'i5-12600KF', 'gpu': 'RX6600', 'mpv': '36bf3d529059a947d6700adefeab3b421e537c19',
                        'libplacebo': '0d043c7f6f79cd3687c023454bdacbe615e4d96f', 'ffmpeg': '5d4755f7d',
                        'mpv_binary_sha256': hashlib.sha256((ROOT/'mpv.exe').read_bytes()).hexdigest()},
        'matrix_reference_pass_count': 48-len(failures),
        'matrix_reference_fail_count': len(failures),
        'failed_matrix_cases': failures,
        'precision_evidence': evidence,
        'gpu_color_end_timing': summaries,
        'timing_scope': '1024×576；色彩末段可能合并横向缩放；ABBA 各两轮、每轮 GPU 样本中位数的均值；非全片帧率',
        'timing_trials': [{k: v for k, v in row.items() if k != 'passes'} for row in timing],
        'range_conversion_timing': range_timing,
        'source_result_sha256': hashes,
        'results': results,
    }
    DEST.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('已保存', DEST)
    print('软件总验收 FAIL；矩阵参考', 48-len(failures), '通过／', len(failures), '失败')


if __name__ == '__main__':
    main()
