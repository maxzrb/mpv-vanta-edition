"""真实核心的固定编码样本：参考帧往返、硬解隔离、换片及开关保存。"""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import time

HOST_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('MPV_FATE_PACKAGE_ROOT', HOST_ROOT)).resolve()
OUT = HOST_ROOT / 'tmp/modernization/overload-fate'
OUT.mkdir(parents=True, exist_ok=True)
SAMPLE = json.loads((HOST_ROOT / 'tools/fate/samples/overload.json').read_text(encoding='utf-8'))
Player = runpy.run_path(str(HOST_ROOT / 'tools/validate-modernization.py'))['Player']
Player.__init__.__globals__['ROOT'] = ROOT


def wait(getter, predicate, name):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        value = getter()
        if predicate(value):
            return value
        time.sleep(.04)
    raise AssertionError((name, value))


def fixtures():
    sources = {}
    encoders = {
        'av1': ['-c:v', 'libaom-av1', '-cpu-used', '8', '-row-mt', '1', '-crf', '40', '-b:v', '0'],
        'h264': ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-bf', '3'],
        'hevc': ['-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '32', '-x265-params', 'log-level=error:pools=2:frame-threads=2'],
        'vp9': ['-c:v', 'libvpx-vp9', '-deadline', 'realtime', '-cpu-used', '8', '-crf', '40', '-b:v', '0'],
    }
    video = SAMPLE['video']
    for codec, args in encoders.items():
        media = OUT / (codec + '.mkv')
        subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                        '-f', 'lavfi', '-i', f"testsrc2=size={video['width']}x{video['height']}:rate={video['fps']}",
                        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
                        '-t', str(video['seconds']), '-threads', '2', *args, '-g', str(video['gop']),
                        '-c:a', 'flac', str(media)], check=True, timeout=90, capture_output=True)
        sources[codec] = media
    return sources


def configuration():
    config = Path(tempfile.mkdtemp(prefix='config-', dir=OUT))
    for folder in ['scripts', 'script-modules', 'script-opts', 'files']:
        (config / folder).mkdir()
    for name in ['safe-file.lua', 'preference-store.lua', 'overload-policy.lua']:
        shutil.copy2(ROOT / 'portable_config/script-modules' / name, config / 'script-modules' / name)
    shutil.copy2(ROOT / 'portable_config/scripts/decode-performance.lua', config / 'scripts/decode-performance.lua')
    shutil.copy2(ROOT / 'portable_config/script-opts/decode-performance.conf', config / 'script-opts/decode-performance.conf')
    (config / 'mpv.conf').write_text('load-scripts=no\nscripts=~~/scripts/decode-performance.lua\n'
                                   'hwdec=no\nvideo-sync=audio\nvd-lavc-threads=2\nhr-seek=no\n',
                                   encoding='utf-8', newline='\n')
    return config


def trial(backend, codec, media):
    config = configuration()
    subtitle = config / 'external.srt'
    subtitle.write_text('1\n00:00:00,000 --> 00:00:08,000\n固定样本字幕\n', encoding='utf-8', newline='\n')
    args = ['--config-dir=' + str(config), '--gpu-api=' + backend, '--ao=null', '--pause=yes',
            '--geometry=640x360', '--start=2', str(media)]
    p = Player(args, 'overload-fate-' + backend + '-' + codec)
    states = []
    try:
        p.wait_video()
        p.command('sub-add', str(subtitle), 'select')
        selection = {k: p.get(k) for k in ['vid', 'aid', 'sid', 'secondary-sid', 'pause']}
        original_seek = p.get('hr-seek')
        p.command('script-message', 'decode-performance-catchup', 'on')
        wait(lambda: p.get('user-data/decode-performance'), lambda v: v and v['catchup-enabled'], '开启')

        def reference(value):
            switches = p.get('user-data/decode-performance')['catchup-switches']
            p.command('script-message', 'decode-performance-reference', 'yes' if value else 'no')
            wait(lambda: p.get('user-data/decode-performance'),
                 lambda v: v and v['catchup-switches'] > switches and v['catchup-active'] == value,
                 '模式切换 ' + str(value))
            wait(lambda: p.get('seeking'), lambda v: v is False, '恢复位置')
            assert p.get('vd-lavc-skipframe') == ('nonref' if value else 'default')
            assert {k: p.get(k) for k in selection} == selection
            wait(lambda: p.get('hr-seek'), lambda v: v == original_seek, '还原日常跳转偏好')
            assert p.get('vd-lavc-threads') == 2
            states.append(dict(reference=value, position=p.get('time-pos'), state=p.get('user-data/decode-performance')))

        reference(True)
        reference(False)
        reference(True)
        p.command('script-message', 'decode-performance-catchup', 'off')
        wait(lambda: p.get('vd-lavc-skipframe'), lambda v: v == 'default', '关闭后恢复')
        wait(lambda: p.get('user-data/decode-performance'), lambda v: v and not v['catchup-active'], '退出追赶')
        p.command('script-message', 'decode-performance-catchup', 'on')
        reference(True)
        p.command('script-message', 'decode-performance-hwdec', 'd3d11va-copy')
        wait(lambda: p.get('hwdec-current'), lambda v: v == 'd3d11va-copy', '用户硬解优先')
        assert p.get('vd-lavc-skipframe') == 'default'
        switches = p.get('user-data/decode-performance')['catchup-switches']
        p.command('script-message', 'decode-performance-reference', 'yes')
        time.sleep(.3)
        assert p.get('user-data/decode-performance')['catchup-switches'] == switches
        assert p.get('hwdec-current') == 'd3d11va-copy'
        p.command('script-message', 'decode-performance-hwdec', 'no')
        wait(lambda: p.get('hwdec-current'), lambda v: v == 'no', '恢复软件解码')
        wait(lambda: p.get('seeking'), lambda v: v is False, '软件位置恢复')
        reference(True)
        p.command('loadfile', str(media), 'replace')
        wait(lambda: p.get('vd-lavc-skipframe'), lambda v: v == 'default', '重新打开不继承临时模式')
        p.wait_video()
        assert not p.get('user-data/decode-performance')['catchup-active']
        data = json.loads((config / 'files/playback-preferences.json').read_text(encoding='utf-8'))
        assert data['overload-catchup'] is True and 'vd-lavc-skipframe' not in data
    finally:
        p.close()
    errors = [line for line in p.log.read_text(encoding='utf-8', errors='replace').splitlines()
              if '[e]' in line or '[f]' in line or 'Lua error:' in line]
    assert not errors, errors[:10]
    p = Player(args, 'overload-fate-restart-' + backend + '-' + codec)
    try:
        p.wait_video()
        assert p.get('user-data/decode-performance')['catchup-enabled']
        assert p.get('vd-lavc-skipframe') == 'default'
    finally:
        p.close()
    return dict(codec=codec, backend=backend, passed=True, states=states, log=str(p.log))


def boundaries(backend, sources):
    rows = []
    for action in ['off', 'hardware', 'stop', 'replace', 'explicit', 'video-only', 'quality']:
        if action == 'quality':
            create_config = runpy.run_path(str(HOST_ROOT / 'tools/isolated-config.py'))['create_config']
            create_config.__globals__['ROOT'] = ROOT
            config = create_config('overload-quality-' + backend)
        else:
            config = configuration()
        (config / 'files/playback-preferences.json').write_text('{"overload-catchup":false}\n',
                                                               encoding='utf-8', newline='\n')
        extra = ['--vd-lavc-skipframe=none'] if action == 'explicit' else ['--audio=no'] if action == 'video-only' else []
        p = Player(['--config-dir=' + str(config), '--gpu-api=' + backend, '--hwdec=no', '--ao=null',
                    '--pause=yes', '--start=2', '--geometry=640x360',
                    '--script-opts-append=decode-performance-catchup=yes', *extra, str(sources['av1'])],
                   'overload-boundary-' + backend + '-' + action)
        try:
            p.wait_video()
            assert p.get('user-data/decode-performance')['catchup-enabled'], '命令行开关必须优先于保存的关闭状态'
            p.command('script-message', 'decode-performance-reference', 'yes')
            if action == 'off':
                p.command('script-message', 'decode-performance-catchup', 'off')
            elif action == 'hardware':
                p.command('script-message', 'decode-performance-hwdec', 'd3d11va-copy')
                wait(lambda: p.get('hwdec-current'), lambda v: v == 'd3d11va-copy', '快速硬解选择')
            elif action == 'stop':
                p.command('stop')
                wait(lambda: p.get('idle-active'), lambda v: v is True, '中途停止')
                p.command('loadfile', str(sources['hevc']), 'replace')
                p.wait_video()
            elif action == 'replace':
                p.command('loadfile', str(sources['hevc']), 'replace')
                p.wait_video()
            elif action in ['video-only', 'quality']:
                wait(lambda: p.get('user-data/decode-performance'), lambda v: v and v['catchup-active'], '参考帧生效')
                if action == 'quality':
                    for mode in ['hq', 'standard', 'hq']:
                        p.command('script-message', 'color-pipeline', mode)
                        wait(lambda: p.get('user-data/color-target'),
                             lambda v: v and v['pipeline'] == mode and v['status'] == '可用', '画质协调 ' + mode)
                        wait(lambda: p.get('seeking'), lambda v: v is False, '画质重建结束')
                p.command('script-message', 'decode-performance-catchup', 'off')
            elif action == 'explicit':
                time.sleep(.4)
                assert p.get('vd-lavc-skipframe') == 'none'
                assert not p.get('user-data/decode-performance')['catchup-active']
            if action != 'explicit':
                wait(lambda: p.get('vd-lavc-skipframe'), lambda v: v == 'default', '操作后还原完整解码 ' + action)
                wait(lambda: p.get('user-data/decode-performance'),
                     lambda v: v and not v['reload-active'] and not v['catchup-active'], '操作后事务释放 ' + action)
            if action in ['stop', 'replace']:
                assert p.get('path') == str(sources['hevc'])
            assert p.get('pause') is True
        finally:
            p.close()
        errors = [line for line in p.log.read_text(encoding='utf-8', errors='replace').splitlines()
                  if '[e]' in line or '[f]' in line or 'Lua error:' in line]
        assert not errors, (action, errors[:10])
        rows.append(dict(action=action, backend=backend, passed=True, log=str(p.log)))
    return rows


def continuing_catchup(backend, media):
    config = configuration()
    replay = config / 'replay.lua'
    shutil.copy2(HOST_ROOT / 'tools/fate/samples/overload-playback.lua', replay)
    # 短样本循环播放；缩短观测窗口，不改变生产中的默认时序。
    args = ['--config-dir=' + str(config), '--scripts=' + str(replay),
            '--gpu-api=' + backend, '--ao=null', '--pause=yes', '--loop-file=inf',
            '--geometry=640x360', '--start=2',
            '--script-opts-append=decode-performance-catchup=yes',
            '--script-opts-append=decode-performance-catchup_enter_hold=0.5',
            '--script-opts-append=decode-performance-catchup_settle=0.5',
            '--script-opts-append=decode-performance-catchup_drop_window=1',
            '--script-opts-append=decode-performance-catchup_sync_hold=1',
            '--script-opts-append=decode-performance-catchup_sync_interval=5', str(media)]
    p = Player(args, 'overload-continuing-' + backend)
    sensors = SAMPLE['playback_sensors']
    def state():
        return p.get('user-data/decode-performance')
    def sensor(value):
        p.command('set_property', 'user-data/fate-overload', value)
    def decoder_opens():
        return p.log.read_text(encoding='utf-8', errors='replace').count('Opening decoder ')
    try:
        p.wait_video()
        assert state()['catchup-auto-recover'] is False
        # 暂停时的掉帧计数不应触发；恢复后持续增加计数，低声画差也必须进入。
        sensor(dict(sensors['normal'], dropped=100))
        time.sleep(1.2)
        assert not state()['catchup-active']
        sensor(sensors['normal'])
        p.command('set_property', 'pause', False)
        deadline, dropped = time.monotonic() + 7, 0
        while time.monotonic() < deadline and not state()['catchup-active']:
            dropped += sensors['drop_delta']
            sensor(dict(sensors['normal'], dropped=dropped))
            time.sleep(.3)
        wait(state, lambda v: v['catchup-active'] and not v['reload-active'], '持续掉帧进入')
        assert state()['catchup-switches'] == 1
        # 暂停保护与恢复后两次同模式重新同步。
        p.command('set_property', 'pause', True)
        sensor(sensors['late'])
        time.sleep(1.3)
        assert state()['catchup-resyncs'] == 0
        initial_opens = decoder_opens()
        assert initial_opens >= 2, '必须实际打开解码器并经历模式重建'
        selection = {k: p.get(k) for k in ['vid', 'aid', 'sid', 'secondary-sid']}
        p.command('set_property', 'pause', False)
        wait(state, lambda v: v['catchup-resyncs'] >= 1 and not v['reload-active'], '首次模式内重新同步')
        first = time.monotonic()
        wait(state, lambda v: v['catchup-resyncs'] >= 2 and not v['reload-active'], '再次模式内重新同步')
        assert time.monotonic() - first >= 4.5, '重新同步必须限频'
        sensor(sensors['normal'])
        assert state()['catchup-switches'] == 1
        assert decoder_opens() == initial_opens, '同模式定位不得重新创建解码器'
        assert {k: p.get(k) for k in selection} == selection
        assert p.get('vd-lavc-skipframe') == 'nonref'
        # 用户跳转后仍保持本片模式，关闭开关才恢复。
        p.command('seek', 2, 'absolute+exact')
        wait(lambda: p.get('seeking'), lambda v: v is False, '参考帧模式用户跳转')
        assert p.get('vd-lavc-skipframe') == 'nonref'
        p.command('script-message', 'decode-performance-catchup', 'off')
        wait(state, lambda v: not v['catchup-active'] and not v['reload-active'], '明确关闭恢复全帧')
        assert p.get('vd-lavc-skipframe') == 'default'
        result = dict(backend=backend, passed=True, log=str(p.log), repeated_resyncs=2,
                      decoder_opens_during_resync=0)
    finally:
        p.close()
    errors = [line for line in p.log.read_text(encoding='utf-8', errors='replace').splitlines()
              if '[e]' in line or '[f]' in line or 'Lua error:' in line]
    assert not errors, errors[:10]
    return result


def main():
    sources = fixtures()
    rows, lines = [], []
    for backend in ['d3d11', 'vulkan']:
        for codec, media in sources.items():
            rows.append(trial(backend, codec, media))
            line = f'{backend} {codec} reference-full-user-hwdec-file-restart PASS'
            lines.append(line)
            print(line, flush=True)
        rows.extend(boundaries(backend, sources))
        line = f'{backend} user-interruption-override-video-only-quality PASS'
        lines.append(line)
        print(line, flush=True)
        rows.append(continuing_catchup(backend, sources['av1']))
        line = f'{backend} sustained-drops-sticky-repeat-sync-no-decoder-reopen PASS'
        lines.append(line)
        print(line, flush=True)
    actual = '\n'.join(lines) + '\n'
    (OUT / 'actual.txt').write_text(actual, encoding='utf-8', newline='\n')
    assert actual == (HOST_ROOT / 'tools/fate/ref/overload').read_text(encoding='utf-8')
    (OUT / 'results.json').write_text(json.dumps(dict(passed=True, rows=rows), ensure_ascii=False, indent=2) + '\n',
                                      encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
