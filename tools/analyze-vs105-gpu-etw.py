"""流式分析GPU ETW，按目标PID与QPC关联队列、DMA跨度和栅栏来源。"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import runpy


def main():
    from lxml import etree
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=Path)
    parser.add_argument('--allow-legacy-calibration', action='store_true')
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding='utf-8'))
    if result.get('control_events'):
        raise RuntimeError('含播放控制的回归窗口须分段分析，不能汇总为稳定播放成绩')
    manifest = json.loads(args.result.with_suffix('.etw.json').read_text(encoding='utf-8'))
    target = manifest.get('target_pid', manifest['host_pid'])
    begin, end = result['rows'][0]['qpc'], result['rows'][-1]['qpc']
    frequency = result['qpc_frequency']
    switches = [f['switch_qpc'] for f in manifest.get('filters', []) if 'switch_qpc' in f]
    if switches and max(switches) >= begin:
        raise RuntimeError('Profiler关键字未在稳定段前关闭，拒绝当精简采集成绩')
    ns = {'e': 'http://schemas.microsoft.com/win/2004/08/events/event'}
    devices, contexts, signals = {}, {}, {}
    queues, starts = {}, {}
    statistics = defaultdict(lambda: defaultdict(list))
    counts, all_counts = Counter(), Counter()
    waits = []
    anchor = None
    anchor_kind = None
    marker_lookup = {m['nonce']: m for m in manifest.get('qpc_markers', [])}
    marker_times = []
    lost = None
    repeated_starts = 0
    events = 0
    for _, event in etree.iterparse(str(args.result.with_suffix('.xml')), events=('end',), tag='{'+ns['e']+'}Event'):
        events += 1
        task = event.findtext('e:RenderingInfo/e:Task', default='', namespaces=ns)
        opcode = event.findtext('e:System/e:Opcode', default='', namespaces=ns)
        execution = event.find('e:System/e:Execution', ns)
        pid = int(execution.get('ProcessID', '0')) if execution is not None else 0
        data = {d.get('Name'): (d.text or '').strip() for d in event.findall('e:EventData/e:Data', ns)}
        time_node = event.find('e:System/e:TimeCreated', ns)
        stamp = datetime.fromisoformat(time_node.get('SystemTime')) if time_node is not None else None
        all_counts[task+'/'+opcode] += 1
        if 'EventsLost' in data:
            lost = int(data['EventsLost'], 0)
            if lost:
                raise RuntimeError(f'ETL报告丢失事件{lost}，拒绝完整队列结论')
        provider = event.find('e:System/e:Provider', ns)
        provider_guid = provider.get('Guid', '').strip('{}').lower() if provider is not None else ''
        if provider_guid == manifest.get('marker_provider', '').lower() and stamp:
            text = ''.join(event.itertext())
            for nonce, marker in marker_lookup.items():
                if nonce not in text:
                    continue
                mid = (marker['qpc_before'] + marker['qpc_after']) / 2
                marker_times.append({'time': stamp.isoformat(), 'qpc': mid, **marker})
                if anchor is None:
                    anchor = (stamp, mid)
                    anchor_kind = 'own-event-qpc-bracket'
                else:
                    expected = anchor[1] + (stamp - anchor[0]).total_seconds() * frequency
                    first = marker_times[0]
                    uncertainty = (first['qpc_after'] - first['qpc_before']) / 2 + frequency / 1e6
                    if not marker['qpc_before'] - uncertainty <= expected <= marker['qpc_after'] + uncertainty:
                        raise RuntimeError('前后QPC标记不一致，拒绝时间对齐')
                    marker_times[-1]['alignment_residual_us'] = (expected - mid) * 1e6 / frequency
                break
        if args.allow_legacy_calibration and not marker_lookup and task == 'CalibrateGpuClockTask' and anchor is None and data.get('CpuClock') and stamp:
            anchor = (stamp, int(data['CpuClock'], 0))
            anchor_kind = 'legacy-gpu-calibration-unverified-event-time'
        if task == 'Device' and data.get('hDevice') and data.get('hProcessId'):
            devices[data['hDevice']] = int(data['hProcessId'], 0)
        if task == 'Context' and data.get('hContext') and data.get('NodeOrdinal'):
            owner = devices.get(data.get('hDevice'), pid)
            contexts[data['hContext']] = {'pid': owner, 'node': int(data['NodeOrdinal'], 0), 'device': data.get('hDevice')}
        context = data.get('hContext')
        info = contexts.get(context)
        # 单对象栅栏只做精确对象＋值匹配；多对象数据保留原XML，避免错配。
        if task == 'SignalSynchronizationObjectFromGpu' and data.get('ObjectCount') == '1' and info:
            signals[(data.get('ObjectArray'), data.get('MonitoredFenceValue'))] = (info['pid'], info['node'])
        qpc = anchor[1] + round((stamp - anchor[0]).total_seconds() * frequency) if anchor and stamp else None
        if info and info['pid'] == target and qpc is not None and begin <= qpc <= end:
            node = info['node']
            counts[f'{node}:{task}/{opcode}'] += 1
            if task == 'QueuePacket' and opcode == '1' and data.get('SubmitSequence'):
                queues[(context, data['SubmitSequence'])] = qpc
            if task == 'DmaPacket' and data.get('ulQueueSubmitSequence'):
                key = (context, data['ulQueueSubmitSequence'])
                if opcode == '1':
                    if key in starts:
                        repeated_starts += 1
                    starts[key] = qpc
                    queued = queues.pop(key, None)
                    if queued is not None and qpc >= queued:
                        statistics[node]['queue_ms'].append((qpc - queued) * 1000 / frequency)
                elif opcode == '2':
                    started = starts.pop(key, None)
                    if started is not None and qpc >= started:
                        statistics[node]['dma_span_ms'].append((qpc - started) * 1000 / frequency)
            if task == 'WaitForSynchronizationObjectFromGpu' and data.get('ObjectCount') == '1':
                waits.append((node, (data.get('ObjectArray'), data.get('MonitoredFenceValue'))))
        event.clear()
        while event.getprevious() is not None:
            del event.getparent()[0]
    if anchor is None:
        raise RuntimeError('没有自己的QPC标记，拒绝猜测时间对齐')
    if marker_lookup and len(marker_times) != len(marker_lookup):
        raise RuntimeError('QPC标记未完整捕获，拒绝时间对齐')
    if not statistics:
        raise RuntimeError('没有目标稳定段GPU队列配对，拒绝空探针结果')
    edges = Counter()
    for node, key in waits:
        source = signals.get(key)
        label = 'unknown' if source is None else (
            str(source[1]) if source[0] == target else f'foreign:{source[0]}:{source[1]}')
        edges[f'{node} waits {label}'] += 1
    describe = runpy.run_path(str(Path(__file__).with_name('analyze-vs105-stages.py')))['describe']
    output = {'target_pid': target, 'event_count': events, 'all_event_counts': dict(all_counts),
        'events_lost': lost, 'anchor_kind': anchor_kind, 'markers': marker_times,
        'qpc_begin': begin, 'qpc_end': end, 'anchor': [anchor[0].isoformat(), anchor[1]],
        'contexts': {k:v for k,v in contexts.items() if v['pid'] == target},
        'statistics': {str(n): {kind: describe(values) for kind,values in stats.items()}
            for n,stats in statistics.items()}, 'signal_wait_edges': dict(edges),
        'event_counts': dict(counts), 'repeated_dma_starts': repeated_starts,
        'notes': ['DMA跨度可能包括等待／抢占，不是纯GPU忙时间；不能跨引擎相加。',
            '栅栏按全轨迹信号匹配，含先排队的等待及其它进程来源；未映射项明确unknown。',
            '本工具不从事件数量推断丢事件，需另核查ETL／采集器的EventsLost。']}
    destination = args.result.with_name(args.result.stem + '-gpu-summary.json')
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(destination)


if __name__ == '__main__':
    main()
