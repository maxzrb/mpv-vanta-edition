"""验证便携硬解、音频、普通／双字幕和 HTTP 文件播放，输出界面检查图。"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import runpy
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
module = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))
Player, OUT = module['Player'], module['OUT']
media = OUT / 'compat-hevc10.mkv'
subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=30',
                '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '12',
                '-pix_fmt', 'yuv420p10le', '-c:v', 'libx265', '-preset', 'ultrafast',
                '-x265-params', 'log-level=error', '-c:a', 'aac', '-color_primaries', 'bt709',
                '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv', str(media)], check=True)
subtitles = []
for name, text in [('primary', '普通字幕测试'), ('secondary', 'Dual subtitle test')]:
    path = OUT / (name + '.srt')
    path.write_text('1\n00:00:00,000 --> 00:00:12,000\n' + text + '\n', encoding='utf-8', newline='\n')
    subtitles.append(path)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(OUT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']('playback-compat')
player = Player(['--config-dir=' + str(config), '--volume=0',
                 '--screenshot-format=png', '--geometry=1280x720', str(media)], 'playback-compat')
try:
    player.wait_video()
    time.sleep(1)
    assert player.get('hwdec-current') == 'd3d11va', player.get('hwdec-current')
    assert player.get('audio-params'), '音频解码未初始化'
    assert player.get('current-ao'), '音频设备未初始化'
    for path in subtitles:
        assert player.command('sub-add', str(path), 'auto')['error'] == 'success'
    tracks = [track for track in player.get('track-list') if track['type'] == 'sub']
    assert len(tracks) >= 2, tracks
    player.command('set_property', 'sid', tracks[0]['id'])
    player.command('set_property', 'secondary-sid', tracks[1]['id'])
    time.sleep(.5)
    assert player.get('sub-text') == '普通字幕测试', player.get('sub-text')
    assert player.get('secondary-sub-text') == 'Dual subtitle test', player.get('secondary-sub-text')
    player.command('screenshot-to-file', str(OUT / 'dual-subtitles.png'), 'window')
    player.command('script-binding', 'stats/display-stats-toggle')
    time.sleep(4.3)
    player.command('screenshot-to-file', str(OUT / 'stats-native.png'), 'window')
    player.command('script-binding', 'stats/display-stats-toggle')
    player.command('script-message', 'quality-menu', 'memc')
    time.sleep(4)
    player.command('screenshot-to-file', str(OUT / 'quality-menu.png'), 'window')
    player.command('script-message-to', 'uosc', 'close-menu')
    player.command('script-message', 'startup-format-logos-preview', 'sdr', 'dra')
    time.sleep(.3)
    assert player.get('user-data/startup-format-logos/audio') == 'dra'
    player.command('screenshot-to-file', str(OUT / 'startup-dra.png'), 'window')
    local = {key: player.get(key) for key in ['hwdec-current', 'video-dec-params', 'audio-params', 'current-ao']}
    url = f'http://127.0.0.1:{server.server_port}/{media.name}'
    assert player.command('loadfile', url)['error'] == 'success'
    player.wait_video()
    time.sleep(1)
    assert player.get('path') == url and player.get('time-pos') is not None
    assert not player.get('vf') and not player.get('glsl-shaders')
    (OUT / 'compat-results.json').write_text(json.dumps({'local': local, 'http': 'passed',
        'subtitles': 'primary + secondary passed'}, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
finally:
    player.close()
    server.shutdown()
errors = [line for line in player.log.read_text(encoding='utf-8').splitlines() if '[e]' in line or '[f]' in line]
assert not errors, errors
print('PASS 便携 HEVC 10bit 硬解／静音音频设备／双字幕／DRA 徽标预览／HTTP 文件播放')
