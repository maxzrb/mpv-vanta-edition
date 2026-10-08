"""按 QPC 边界分析 3FP 的稳定段日志，不混入首开和 seek 预热。"""
import argparse
import json
from pathlib import Path
import statistics


def describe(values):
    if not values:
        return None
    values = sorted(values)
    def percentile(p):
        position = (len(values) - 1) * p
        low = int(position)
        high = min(low + 1, len(values) - 1)
        return values[low] + (values[high] - values[low]) * (position - low)
    return {'count': len(values), 'mean': statistics.mean(values),
            'median': statistics.median(values), 'p95': percentile(.95), 'max': max(values)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=Path)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding='utf-8'))
    first, last = result['rows'][0], result['rows'][-1]
    begin, end = first['qpc'], last['qpc']
    frequency = result['qpc_frequency']
    elapsed = (end - begin) / frequency
    stages = {'upload': [], 'compose': [], 'present': []}
    submissions = []
    presents = []
    for line in args.result.with_suffix('.log').read_text(encoding='utf-8').splitlines():
        fields = line.split(',')
        if fields[0] == 'GPU_PROFILE' and len(fields) == 7:
            if begin <= int(fields[5]) and int(fields[6]) <= end:
                stages[fields[1]].append({'generation': int(fields[2]),
                    'cpu_ms': float(fields[3]), 'gpu_ms': float(fields[4])})
        elif fields[0] == 'PRESENT_PROFILE' and len(fields) == 4:
            tick, duration = int(fields[3]), float(fields[2])
            if begin <= tick - duration * frequency / 1000 and tick <= end:
                entry = {'generation': int(fields[1]), 'cpu_ms': duration, 'qpc_end': tick}
                stages['present'].append(entry)
                presents.append(entry)
        elif fields[0] == 'SUBMIT_PROFILE' and len(fields) == 4:
            if begin <= int(fields[3]) <= end:
                submissions.append({'generation': int(fields[1]), 'pts_ms': int(fields[2]), 'qpc': int(fields[3])})
    names = ['decodedVideoFrames', 'presentedVideoFrames', 'droppedVideoFrames',
             'coalescedVideoFrames', 'swapChainPresents', 'queuedVideoFrames', 'audioUnderruns']
    delta = {name: last[name] - first[name] for name in names}
    summary = {'wall_s': elapsed, 'window': result['window'], 'mode': result['mode'],
        'algorithm': result['algorithm'], 'quality': result['quality'], 'delta': delta,
        'media_rate': (last['position100ns'] - first['position100ns']) / 1e7 / elapsed,
        'decoded_fps': delta['decodedVideoFrames'] / elapsed,
        'accepted_net_fps': (delta['presentedVideoFrames'] - delta['coalescedVideoFrames']) / elapsed,
        # 队列端点、读取瞬间的渲染中帧会产生很小的计数偏差。
        'frame_accounting_residual': delta['decodedVideoFrames'] - delta['presentedVideoFrames']
            - delta['droppedVideoFrames'] - delta['queuedVideoFrames'],
        'stages': {stage: {key: describe([row[key] for row in rows])
            for key in ['cpu_ms', 'gpu_ms'] if rows and key in rows[0]}
            for stage, rows in stages.items()}}
    frame_ms = 1000 / (7001 / 146)
    gaps = [b['pts_ms'] - a['pts_ms'] for a, b in zip(submissions, submissions[1:])]
    summary['submitted_pts_gap_ms'] = describe(gaps)
    summary['estimated_missing_pts_between_submissions'] = sum(max(0, round(gap / frame_ms) - 1) for gap in gaps) if gaps else None
    summary['present_over_frame_budget_fraction'] = sum(row['cpu_ms'] > frame_ms for row in presents) / len(presents) if presents else None
    summary['present_over_50ms_fraction'] = sum(row['cpu_ms'] > 50 for row in presents) / len(presents) if presents else None
    destination = args.result.with_name(args.result.stem + '-stages.json')
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
