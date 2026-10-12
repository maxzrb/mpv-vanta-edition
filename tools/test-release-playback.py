"""发布候选的完整配置真实播放检查，不把音频时钟当成视频成功。"""
import argparse
import json
import runpy
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
helper = runpy.run_path(str(ROOT / 'tools/test-color-pipeline-modes.py'))
Player = helper['Player']


def moving_video(player):
    deadline = time.monotonic() + 15
    samples = []
    while time.monotonic() < deadline:
        state = {key: player.get(key) for key in ('current-vo', 'video-out-params', 'vid', 'pause', 'time-pos', 'seeking')}
        if state['current-vo'] == 'gpu-next' and state['video-out-params'] and state['time-pos'] is not None \
                and not state['pause'] and not state['seeking']:
            samples.append(state['time-pos'])
            if len(samples) >= 3 and max(samples) - min(samples) > .1:
                return dict(samples=samples, output=state['video-out-params'])
        else:
            samples.clear()
        time.sleep(.2)
    raise AssertionError(('未确认实际视频持续播放', state, samples))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package = args.package_root.resolve()
    # 所有历史及偏好写入隔离副本，运行库和核心使用实际候选的目录。
    Player.__init__.__globals__['ROOT'] = package
    config_helper = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))
    create_config = config_helper['create_config']
    create_config.__globals__['ROOT'] = package
    rows = []
    for backend in ('d3d11', 'vulkan'):
        for source in ('compat-hevc10', 'hdr10', 'hlg'):
            config = create_config('release-playback-' + backend)
            media = ROOT / 'tmp/modernization/validation' / (source + '.mkv')
            player = Player(['--config-dir=' + str(config), '--gpu-api=' + backend, '--ao=null',
                             '--loop-file=inf', '--geometry=800x500', str(media)],
                            'release-playback-' + backend + '-' + source, executable=package / 'mpv.exe')
            states = []
            try:
                player.wait_video()
                for mode in ('standard', 'hq', 'standard'):
                    player.command('script-message', 'color-pipeline', mode)
                    helper['stable'](player, mode)
                    playback = moving_video(player)
                    # 暂停恢复和窗口尺寸改变后仍须真实输出视频，不能只看到成功状态。
                    player.command('set_property', 'pause', True)
                    player.command('set_property', 'geometry', '760x460')
                    player.command('set_property', 'pause', False)
                    resumed = moving_video(player)
                    states.append(dict(mode=mode, playback=playback, resumed=resumed,
                                       target=player.get('video-target-params'),
                                       color=player.get('user-data/color-target')))
            finally:
                player.close()
            errors = [line for line in player.log.read_text(encoding='utf-8', errors='replace').splitlines()
                      if '[e]' in line or '[f]' in line or 'Lua error:' in line]
            assert not errors, errors[:8]
            rows.append(dict(backend=backend, source=source, states=states, errors=errors))
            print('PASS 实际视频／模式往返／窗口变化／暂停恢复', backend, source, flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(passed=True, package_root=str(package), rows=rows),
                                     ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
