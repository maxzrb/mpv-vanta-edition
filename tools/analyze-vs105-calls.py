"""按QPC切片逐调用插桩记录，保留方法、线程、返回码和实际资源信息。"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import runpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=Path)
    args = parser.parse_args()
    data = json.loads(args.result.read_text(encoding='utf-8'))
    if data.get('control_events'):
        raise RuntimeError('含播放控制的回归窗口须分段分析，不能汇总为稳定播放成绩')
    first, last = data['rows'][0], data['rows'][-1]
    groups = defaultdict(list)
    metadata = []
    messages = [json.loads(line) for line in args.result.with_suffix('.calls.jsonl').read_text(
        encoding='utf-8').splitlines()]
    if any(message['type'] == 'error' for message in messages):
        raise RuntimeError('存在插桩错误，拒绝作为有效统计')
    for message in messages:
        payload = message.get('payload', {})
        if 'calls' not in payload:
            metadata.append(payload)
        for call in payload.get('calls', []):
            if first['qpc'] <= call['begin'] <= last['qpc']:
                groups[call['name']].append(call)
    if not groups.get('Present'):
        raise RuntimeError('没有捕获稳定段Present，拒绝空探针结果')
    describe = runpy.run_path(str(Path(__file__).with_name('analyze-vs105-stages.py')))['describe']
    wall = (last['qpc'] - first['qpc']) / data['qpc_frequency']
    summary = {'wall_s': wall, 'metadata': metadata, 'calls': {}}
    if 'presentedVideoFrames' in first:
        summary.update({
        'accepted_fps': (last['presentedVideoFrames'] - first['presentedVideoFrames']) / wall,
        'progress': (last['position100ns'] - first['position100ns']) / 1e7 / wall,
        'counter_deltas': {name: last[name] - first[name] for name in [
            'decodedVideoFrames', 'presentedVideoFrames', 'droppedVideoFrames',
            'coalescedVideoFrames', 'swapChainPresents', 'audioUnderruns']}})
    else:
        # mpv没有相同的接受帧计数，保留时间进度与自身掉帧口径，不估算成同一指标。
        summary.update({'player': 'mpv', 'progress': (last['time-pos'] - first['time-pos']) / wall,
            'counter_deltas': {name: last[name] - first[name] for name in [
                'frame-drop-count', 'decoder-frame-drop-count']}})
    for name, calls in groups.items():
        summary['calls'][name] = {'duration_ms': describe([
            (call['end'] - call['begin']) * 1000 / data['qpc_frequency'] for call in calls]),
            'callers': dict(Counter(call.get('caller', 'replacement') for call in calls)),
            'threads': dict(Counter(call['thread'] for call in calls)),
            'results': dict(Counter(call['result'] for call in calls)),
            'details': list({json.dumps(call['detail'], sort_keys=True) for call in calls})}
    destination = args.result.with_name(args.result.stem + '-calls-summary.json')
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
