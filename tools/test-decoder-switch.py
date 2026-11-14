"""验证解码器切换从安全位置重建，并对照旧直切在多种编码上的错误。"""
import json
import argparse
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(tempfile.mkdtemp(prefix='decoder-switch-', dir=ROOT/'tmp'))
CONFIG = OUT/'config'
MEDIA = OUT/'media'
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path,
                    default=ROOT/'docs/modernization/decoder-switch-safety-20261101.json')
REPORT = parser.parse_args().output
Player = runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
create_full_config = runpy.run_path(str(ROOT/'tools/isolated-config.py'))['create_config']
FULL_CONFIG = create_full_config('decoder-switch-full')
ERROR_MARKERS = (
    'Could not find ref',
    'Error constructing the frame RPS',
    'mmco: unref short failure',
    'co located POCs unavailable',
    'Error while decoding frame',
    'Skipping invalid undecodable NALU',
    'Invalid NALU',
    'Failed to decode',
)

for name in ('scripts', 'script-modules', 'script-opts', 'files'):
    (CONFIG/name).mkdir(parents=True)
for name in ('safe-file.lua', 'preference-store.lua', 'overload-policy.lua', 'load-config-scripts.lua'):
    shutil.copy2(ROOT/'portable_config/script-modules'/name, CONFIG/'script-modules'/name)
for name in ('decode-performance.lua', 'hwdec-select.lua'):
    shutil.copy2(ROOT/'portable_config/scripts'/name, CONFIG/'scripts'/name)
shutil.copy2(ROOT/'portable_config/script-opts/decode-performance.conf',
             CONFIG/'script-opts/decode-performance.conf')
(CONFIG/'mpv.conf').write_text(
    'load-scripts=no\n'
    'scripts=~~/script-modules/load-config-scripts.lua\n'
    'hwdec=auto-safe\n'
    'ao=null\n'
    'keep-open=yes\n',
    encoding='utf-8', newline='\n')
MEDIA.mkdir()


def wait(getter, predicate=lambda value: value is not None, timeout=20, label='状态'):
    deadline = time.monotonic()+timeout
    value = None
    while time.monotonic() < deadline:
        value = getter()
        if predicate(value):
            return value
        time.sleep(.03)
    raise AssertionError((label, value))


def log_tail(player, offset=0):
    try:
        return player.log.read_text(encoding='utf-8', errors='replace')[offset:]
    except FileNotFoundError:
        return ''


def codec_errors(text):
    return [line for line in text.splitlines() if any(marker in line for marker in ERROR_MARKERS)]


def lua_errors(text):
    return [line for line in text.splitlines()
            if '[e]' in line or '[f]' in line or 'Lua error:' in line]


def generate(name, pix_fmt, encoder):
    target = MEDIA/(name+'.mkv')
    command = [
        str(ROOT/'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=24', '-t', '8',
        '-pix_fmt', pix_fmt, *encoder, '-an', str(target),
    ]
    subprocess.run(command, check=True, timeout=180)
    return target


def start(label, media, pause, position=4.2):
    options = [
        '--config-dir='+str(CONFIG), '--gpu-api=d3d11', '--ao=null',
        '--pause='+('yes' if pause else 'no'), '--geometry=640x360',
    ]
    if position is not None:
        options.append('--start='+str(position))
    options.append(str(media))
    player = Player(options, 'decoder-switch-'+OUT.name[-8:]+'-'+label)
    player.wait_video()
    wait(lambda: player.get('user-data/config-script-loader/loaded'), timeout=10, label='脚本加载')
    wait(lambda: player.get('hwdec-current'), lambda value: value not in (None, ''), label='硬解初始化')
    wait(lambda: player.get('time-pos'),
         (lambda value: value is not None) if position is None else (
             lambda value: value is not None and value >= position-.05),
         label='定位')
    return player


def switch(player, policy, label):
    before_position = player.get('time-pos')
    before_pause = player.get('pause')
    offset = len(log_tail(player))
    player.command('script-message', 'decode-performance-hwdec', policy)
    wait(lambda: log_tail(player, offset),
         lambda text: '安全重建解码器：' in text and '解码器重载参数已应用：' in text,
         timeout=20, label=label+'重建')
    expected = (lambda value: value == 'no') if policy == 'no' else (
        lambda value: value not in (None, 'no', ''))
    wait(lambda: player.get('hwdec-current'), expected, timeout=20, label=label+'解码方式')
    wait(lambda: player.get('seeking'), lambda value: value is False, timeout=10, label=label+'定位结束')
    after_position = player.get('time-pos')
    assert after_position is not None and before_position is not None
    assert abs(after_position-before_position) < .35, (label, before_position, after_position)
    assert player.get('pause') == before_pause, (label, before_pause, player.get('pause'))
    segment = log_tail(player, offset)
    assert 'Run command: playlist-play-index' in segment, segment[-2000:]
    errors = codec_errors(segment)
    assert not errors, (label, errors[:8])
    return dict(policy=policy, before=before_position, after=after_position,
                pause=before_pause, log_offset=offset)


def direct_control(media, label, policy):
    (FULL_CONFIG/'files').mkdir(exist_ok=True)
    (FULL_CONFIG/'files/playback-preferences.json').write_text(
        '{"hwdec":"no"}\n', encoding='utf-8', newline='\n')
    player = Player([
        '--config-dir='+str(FULL_CONFIG), '--gpu-api=d3d11', '--ao=null',
        '--loop-file=inf', '--geometry=640x360', str(media),
    ], 'decoder-switch-'+OUT.name[-8:]+'-'+label+'-direct-'+policy)
    try:
        wait(lambda: log_tail(player),
             lambda text: 'playback restart complete @' in text,
             timeout=20, label=label+'直切时机')
        actual_before = player.get('hwdec-current')
        assert actual_before == 'no', actual_before
        time.sleep(.02)
        offset = len(log_tail(player))
        player.command('set_property', 'hwdec', policy)
        time.sleep(1.2)
        text = log_tail(player, offset)
        errors = codec_errors(text)
        return dict(codec=label, target=policy, actual_before=actual_before,
                    error_count=len(errors), errors=errors[:12], reproduced=bool(errors))
    finally:
        player.close()


def full_config_regression(media):
    (FULL_CONFIG/'files').mkdir(exist_ok=True)
    (FULL_CONFIG/'files/playback-preferences.json').write_text(
        '{"hwdec":"no"}\n', encoding='utf-8', newline='\n')
    player = Player([
        '--config-dir='+str(FULL_CONFIG), '--gpu-api=d3d11', '--ao=null',
        '--loop-file=inf', '--pause=yes', '--geometry=640x360', str(media),
    ], 'decoder-switch-'+OUT.name[-8:]+'-full-regression')
    try:
        wait(lambda: log_tail(player),
             lambda text: 'playback restart complete @' in text,
             timeout=20, label='完整配置起播')
        assert player.get('hwdec-current') == 'no'
        offset = len(log_tail(player))
        player.command('script-message', 'decode-performance-hwdec', 'd3d11va-copy')
        wait(lambda: log_tail(player, offset),
             lambda text: '安全重建解码器：' in text and '解码器重载参数已应用：' in text,
             timeout=20, label='完整配置安全重建')
        wait(lambda: player.get('hwdec-current'),
             lambda value: value in ('d3d11va', 'd3d11va-copy'),
             timeout=20, label='完整配置解码方式')
        wait(lambda: player.get('seeking'), lambda value: value is False,
             timeout=10, label='完整配置定位')
        segment = log_tail(player, offset)
        errors = codec_errors(segment)
        assert not errors, errors[:8]
        return dict(after_hwdec=player.get('hwdec-current'),
                    position=player.get('time-pos'),
                    errors=errors[:12], artifacts=str(player.log))
    finally:
        player.close()


cases = [
    ('hevc', 'yuv420p10le', ['-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '22',
                             '-x265-params',
                             'keyint=240:min-keyint=240:scenecut=0:bframes=4:rc-lookahead=20:open-gop=0']),
    ('h264', 'yuv420p', ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '20',
                         '-g', '240', '-keyint_min', '240', '-sc_threshold', '0', '-bf', '3']),
    ('av1', 'yuv420p10le', ['-c:v', 'libaom-av1', '-cpu-used', '8', '-crf', '35', '-b:v', '0',
                            '-g', '240', '-keyint_min', '240', '-lag-in-frames', '16', '-auto-alt-ref', '1']),
    ('vp9', 'yuv420p10le', ['-c:v', 'libvpx-vp9', '-deadline', 'realtime', '-cpu-used', '8',
                            '-crf', '35', '-b:v', '0', '-g', '240',
                            '-lag-in-frames', '16', '-auto-alt-ref', '1', '-row-mt', '1']),
]

direct_rows = []
safe_rows = []
logs = []
generated = []
for codec, pix_fmt, encoder in cases:
    generated.append((codec, generate(codec, pix_fmt, encoder)))
known_hevc = ROOT/'tmp/modernization/validation/compat-hevc10.mkv'
if known_hevc.exists():
    generated.append(('hevc-compat10', known_hevc))
for codec, media in generated:
    attempts = []
    for trial in range(3):
        attempts.append(direct_control(media, codec+'-t'+str(trial+1), 'd3d11va-copy'))
    direct_rows.append(dict(
        codec=codec,
        attempts=attempts,
        reproduced=any(row['reproduced'] for row in attempts),
        max_error_count=max(row['error_count'] for row in attempts),
    ))
for codec, media in generated:
    (CONFIG/'files/playback-preferences.json').write_text(
        '{"hwdec":"auto-safe"}\n', encoding='utf-8', newline='\n')
    player = start(codec+'-safe', media, True)
    logs.append(player.log)
    try:
        initial = player.get('hwdec-current')
        assert initial not in (None, 'no', ''), (codec, initial)
        if codec.startswith('hevc'):
            subtitle = OUT/'external.srt'
            subtitle.write_text('1\n00:00:00,000 --> 00:00:20,000\n安全切换字幕\n',
                                encoding='utf-8', newline='\n')
            player.command('sub-add', str(subtitle), 'select')
            wait(lambda: player.get('sid'), lambda value: value not in (None, False), label='外挂字幕')
            selected_subtitle = player.get('sid')
        transitions = [switch(player, 'no', codec+'-soft'),
                       switch(player, 'auto-safe', codec+'-hardware')]
        if codec.startswith('hevc'):
            assert player.get('sid') == selected_subtitle
            player.command('set_property', 'pause', False)
            wait(lambda: player.get('time-pos'),
                 lambda value: value is not None and value > transitions[-1]['after']+.1,
                 timeout=8, label='恢复播放')
            transitions.append(switch(player, 'no', codec+'-playing'))
            wait(lambda: player.get('time-pos'),
                 lambda value: value is not None and value > transitions[-1]['after']+.1,
                 timeout=8, label='播放中切换后继续')
        safe_rows.append(dict(codec=codec, initial_hwdec=initial, transitions=transitions))
    finally:
        player.close()

for log in logs:
    text = log.read_text(encoding='utf-8', errors='replace')
    assert 'Lua error:' not in text, log
    assert not codec_errors(text), (log, codec_errors(text)[:8])

report = {
    'passed': True,
    'scope': '安全路径覆盖D3D11VA到软件及软件到自动硬解；旧直切在完整配置中进行三轮对照；HEVC额外覆盖播放中切换和外挂字幕选择',
    'codec_matrix': safe_rows,
    'direct_switch_control': direct_rows,
    'known_full_config_regression': full_config_regression(known_hevc) if known_hevc.exists() else None,
    'boundary': '旧直切为完整配置下的三轮竞态对照，错误是否出现受起播时序影响；安全路径矩阵只验证本机可用D3D11VA，NVDEC、QSV、AMF等共用同一重载事务但未做实际后端认证',
    'artifacts': str(OUT),
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n',
                  encoding='utf-8', newline='\n')
print('PASS HEVC/H.264/AV1/VP9 安全重建、位置恢复与旧直切对照', flush=True)
print('REPORT', REPORT, flush=True)
