"""将PresentMon CSV与内核QPC稳定段对齐，保留不可用指标。"""
import argparse
import csv
import json
from pathlib import Path
import runpy
from collections import Counter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=Path)
    args = parser.parse_args()
    data = json.loads(args.result.read_text(encoding='utf-8'))
    first, last = data['rows'][0], data['rows'][-1]
    begin, end = first['qpc'], last['qpc']
    with args.result.with_suffix('.presentmon.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = [row for row in csv.DictReader(stream) if begin <= int(row['CPUStartQPC']) <= end]
    describe = runpy.run_path(str(Path(__file__).with_name('analyze-vs105-stages.py')))['describe']
    metrics = ['FrameTime', 'CPUBusy', 'CPUWait', 'GPULatency', 'GPUTime',
               'GPUBusy', 'GPUWait', 'VideoBusy', 'DisplayLatency', 'DisplayedTime']
    summary = {'rows': len(rows), 'qpc_begin': begin, 'qpc_end': end,
        'wall_s': (end - begin) / data['qpc_frequency'],
        'process_ids': dict(Counter(row['ProcessID'] for row in rows)),
        'swap_chains': dict(Counter(row['SwapChainAddress'] for row in rows)),
        'present_runtimes': dict(Counter(row['PresentRuntime'] for row in rows)),
        'present_modes': dict(Counter(row['PresentMode'] for row in rows)),
        'sync_intervals': dict(Counter(row['SyncInterval'] for row in rows)),
        'allows_tearing': dict(Counter(row['AllowsTearing'] for row in rows)),
        'hybrid_present': dict(Counter(row.get('HybridPresent', 'unknown') for row in rows)),
        'metrics_ms': {}, 'missing_values': {}}
    for name in metrics:
        values = []
        for row in rows:
            try:
                values.append(float(row[name]))
            except (ValueError, KeyError):
                pass
        summary['metrics_ms'][name] = describe(values)
        summary['missing_values'][name] = len(rows) - len(values)
    summary['display_event_observed_frames'] = sum(row.get('DisplayedTime', 'NA') != 'NA' for row in rows)
    summary['display_event_missing_frames'] = len(rows) - summary['display_event_observed_frames']
    destination = args.result.with_name(args.result.stem + '-presentmon-summary.json')
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
