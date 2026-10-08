"""验证大分辨率源在首次解码前选定硬解，覆盖快进、切片与恢复默认路径。"""
import argparse
import json
from pathlib import Path
import runpy
import time

ROOT = Path(__file__).resolve().parents[1]
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']


def run(media, repeats):
    results = []
    small = ROOT / 'tmp/modernization/validation/compat-hevc10.mkv'
    for repeat in range(repeats):
        p = Player(['--config-dir=' + str(ROOT / 'portable_config'), '--ao=null', '--pause=yes',
                    '--start=0', '--resume-playback=no', '--autofit=1280x720',
                    '--msg-level=all=warn,vd=debug,ffmpeg/video=debug', str(media)],
                   'hwdec-startup-' + str(repeat + 1))
        row = {'repeat': repeat + 1, 'samples': []}
        try:
            p.wait_video()
            time.sleep(.5)
            row['source'] = p.get('video-params')
            p.command('set_property', 'pause', False)
            for phase, position in [('start', None), ('seek', 30)]:
                if position is not None:
                    p.command('seek', position, 'absolute+exact')
                for _ in range(4):
                    time.sleep(1)
                    sample = {k: p.get(k) for k in ['time-pos', 'hwdec-current', 'frame-drop-count']}
                    sample['phase'] = phase
                    assert sample['hwdec-current'] == 'd3d11va', sample
                    row['samples'].append(sample)
            if small.exists():
                p.command('loadfile', str(small), 'replace')
                p.wait_video()
                time.sleep(.5)
                row['small_hwdec'] = p.get('hwdec-current')
                assert row['small_hwdec'] == 'd3d11va-copy', row
                p.command('loadfile', str(media), 'replace')
                p.wait_video()
                time.sleep(1)
                row['reload_hwdec'] = p.get('hwdec-current')
                assert row['reload_hwdec'] == 'd3d11va', row
        finally:
            p.close()
        log = p.log.read_text(encoding='utf-8', errors='replace')
        assert 'Using software decoding.' not in log, '出现软解回退'
        assert 'Error while decoding frame (hardware decoding)' not in log, '硬解报错'
        # 日志必须证明规则在硬解尝试前应用，避免短测试遗漏迟到的重建。
        assert log.index('大分辨率源在解码前选择直接硬解') < log.index('Trying hardware decoding'), '规则生效过晚'
        row['passed'] = True
        results.append(row)
        print('PASS 第 ' + str(repeat + 1) + ' 次：启动／快进／切片硬解保持', flush=True)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('media', type=Path)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    out = ROOT / 'tmp/modernization/kaguya-hwdec'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'fixed-results.json').write_text(json.dumps(run(args.media, args.repeats), ensure_ascii=False,
                                                    indent=2) + '\n', encoding='utf-8', newline='\n')
