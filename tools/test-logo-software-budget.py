"""跨编解码器和图形后端验证软解徽标探针预算、暗场后瞻与取消行为。"""
import argparse
import json
from pathlib import Path
import runpy
import time

ROOT = Path(__file__).resolve().parents[1]
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']


def check(media, dark, action=None, backend='d3d11', av1=True, hardware=False):
    config = create_config('logo-manual-budget', exclude_scripts=['window-size-position.lua'])
    # 自动调优关闭且显式设线程，确保后台预算不依赖调优脚本的状态。
    decoder_options = ['--vd-lavc-threads=32', '--vd-lavc-o=max_frame_delay=32'] if av1 else []
    p = Player(['--config-dir=' + str(config), '--hwdec=' + ('auto-safe' if hardware else 'no'), '--gpu-api=' + backend, *decoder_options,
                '--script-opts-append=decode-performance-enabled=no',
                '--volume=0', '--pause=yes', '--geometry=640x360', '--sid=no',
                '--start=' + ('0' if dark else '10'), str(media)], 'logo-budget-' + backend + '-' + media.stem[:12] + '-' + str(action or 'bright'))
    p.ipc_timeout = 30
    try:
        p.wait_video()
        assert not (p.get('user-data/decode-performance') or {}).get('frame_delay')
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            log = p.log.read_text(encoding='utf-8')
            lines = [line for line in log.splitlines() if '[startup_format_logos] Starting subprocess:' in line]
            if hardware and lines:
                assert p.get('hwdec-current') not in ('no', None)
                assert '-threads, 4,' in lines[0], lines[0]
                break
            if dark and lines:
                assert '-threads, 1,' in lines[0], lines[0]
                assert 'playback restart complete @' in log[:log.index(lines[0])]
                break
            if not dark and '[startup_format_logos] show (' in log:
                assert not lines, lines
                break
            time.sleep(.1)
        else:
            raise AssertionError('徽标定位未完成预期分支')
        offset = p.log.stat().st_size
        if action == 'stop':
            assert p.command('stop')['error'] == 'success'
        elif action == 'mode-change':
            assert p.command('script-message', 'startup-format-logos-set-mode', 'none')['error'] == 'success'
            deadline = time.monotonic() + 10
            while p.get('user-data/startup-format-logos/mode') != 'none':
                assert time.monotonic() < deadline
                time.sleep(.1)
        time.sleep(3)
        tail = p.log.read_bytes()[offset:].decode('utf-8')
        if hardware:
            # 硬解继续原来的深探针流程，可正常启动后续请求。
            assert all('-threads, 4,' in line for line in tail.splitlines()
                       if '[startup_format_logos] Starting subprocess:' in line)
        else:
            assert '[startup_format_logos] Starting subprocess:' not in tail
        row = dict(dark=dark, action=action, manual_threads=av1, automatic_tuning=False, backend=backend,
                   hardware=hardware, hwdec=p.get('hwdec-current'),
                   codec=p.get('current-tracks/video/codec'), video_params=p.get('video-params'),
                   background_decoder_threads=4 if hardware else (1 if dark else None), unnecessary_probe=False)
    finally:
        p.close()
    log = p.log.read_text(encoding='utf-8')
    assert 'Lua error:' not in log and 'No frames available to take screenshot' not in log
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('media', type=Path)
    parser.add_argument('dark_fixture', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--other-codec', type=Path)
    args = parser.parse_args()
    rows = [check(args.media, False)]
    print('PASS 手动软解亮场徽标不启动额外解码', flush=True)
    for action in ['stop', 'mode-change']:
        rows.append(check(args.dark_fixture, True, action))
        print('PASS 手动软解暗场单线程及取消', action, flush=True)
    if args.other_codec:
        for backend in ['d3d11', 'vulkan']:
            rows.append(check(args.other_codec, False, backend=backend, av1=False))
            print('PASS 非 AV1 软解按需探针', backend, flush=True)
        rows.append(check(args.other_codec, False, av1=False, hardware=True))
        print('PASS D3D11 硬解预探针策略保留', flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
