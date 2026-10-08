"""维护者手动 SVP 三轮实播采样；不降分辨率，不启动组件核验。"""
import argparse
import json
from pathlib import Path
import runpy
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/svp-benchmark'
OUT.mkdir(parents=True, exist_ok=True)
helpers = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))
Player, cpu = helpers['Player'], helpers['process_cpu_seconds']
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']


def run(media, passthrough):
    rows = []
    for repeat in range(3):
        player = Player(['--config-dir=' + str(create_config('svp-benchmark')),
                         '--hwdec=auto-safe', '--ao=wasapi', '--mute=yes', '--pause=no',
                         '--input-cursor=no', '--input-vo-keyboard=no', '--input-media-keys=no',
                         '--input-terminal=no', '--geometry=1920x1080', str(media)],
                        'svp-benchmark-' + str(repeat))
        player.ipc_timeout = 45
        try:
            player.wait_video()
            player.command('script-message', 'quality-select', 'svp')
            deadline = time.monotonic() + 90
            while True:
                quality = player.get('user-data/quality') or {}
                if quality.get('state') == '已添加' and quality.get('active', {}).get('memc') == 'svp':
                    break
                assert quality.get('state') != '失败', '实际滤镜初始化失败，见本轮日志'
                assert time.monotonic() < deadline, '实际滤镜初始化超时，见本轮日志'
                time.sleep(.2)
            assert player.get('user-data/quality')['state'] == '已添加'
            time.sleep(5)
            vf = player.get('vf')
            assert any(f.get('label') == 'quality-memc' for f in vf) != passthrough
            initial = player.get('time-pos')
            drops = player.get('frame-drop-count')
            decoder = player.get('decoder-frame-drop-count')
            initial_cpu = cpu(player.process)
            start = time.monotonic()
            samples = []
            while time.monotonic() - start < 20:
                time.sleep(1)
                assert player.get('pause') is False and player.get('speed') == 1, '采样被暂停／变速干扰'
                assert not player.get('eof-reached'), '素材长度不足，请使用至少 30 秒的视频'
                samples.append({'wall': time.monotonic() - start, 'pos': player.get('time-pos'),
                                'drops': player.get('frame-drop-count')})
            elapsed = time.monotonic() - start
            row = {'round': repeat + 1, 'seconds': elapsed,
                   'clock_ratio': (samples[-1]['pos'] - initial) / elapsed,
                   'cpu_core_percent': 100 * (cpu(player.process) - initial_cpu) / elapsed,
                   'drops': samples[-1]['drops'] - drops,
                   'decoder_drops': player.get('decoder-frame-drop-count') - decoder,
                   'source': player.get('video-params'), 'output': player.get('video-out-params'),
                   'fps': player.get('estimated-vf-fps'), 'hwdec': player.get('hwdec-current'),
                   'state': player.get('user-data/quality'), 'samples': samples}
            assert .97 < row['clock_ratio'] < 1.03, '时钟推进异常，不能把低速播放当成性能通过'
        finally:
            player.close()
        log = player.log.read_text(encoding='utf-8')
        row['audio_underruns'] = sum('underrun' in line.lower() for line in log.splitlines())
        row['script_errors'] = sum('Lua error:' in line or 'Script evaluation failed' in line
                                   for line in log.splitlines())
        rows.append(row)
        (OUT / 'results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                                         encoding='utf-8', newline='\n')
        print(json.dumps({k: row[k] for k in ['round', 'seconds', 'clock_ratio', 'drops',
                         'decoder_drops', 'audio_underruns', 'cpu_core_percent', 'hwdec']},
                         ensure_ascii=False), flush=True)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--media', type=Path, required=True)
    parser.add_argument('--passthrough', action='store_true', help='断言达到 59.94fps 的片源不添加补帧滤镜')
    args = parser.parse_args()
    run(args.media, args.passthrough)
