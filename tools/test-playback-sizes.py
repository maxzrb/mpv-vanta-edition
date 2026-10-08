"""使用固定画面验证多个分辨率／帧率的默认原始播放，不启用增强。"""
import json
from pathlib import Path
import runpy
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
module = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))
Player, OUT = module['Player'], module['OUT']
results = []
config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']('playback-sizes')
for width, height, fps in [(1280,720,'60'), (1920,1080,'24000/1001'), (3840,2160,'30')]:
    media = OUT / f'size-{height}.mkv'
    if not media.exists():
        subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'lavfi', '-i', f'testsrc2=size={width}x{height}:rate={fps}', '-t', '5',
                    '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '4',
                    '-x264-params', 'colorprim=bt709:transfer=bt709:colormatrix=bt709', str(media)], check=True, timeout=120)
    player = Player(['--config-dir=' + str(config), '--ao=null', str(media)], f'size-{height}')
    try:
        player.wait_video()
        time.sleep(2)
        params = player.get('video-params')
        assert (params['w'], params['h']) == (width, height), params
        assert not player.get('interpolation') and not player.get('deband')
        assert not player.get('vf') and not player.get('glsl-shaders')
        numerator, _, denominator = fps.partition('/')
        expected = float(numerator) / float(denominator or 1)
        assert abs(player.get('container-fps') - expected) < .01
        results.append({key: player.get(key) for key in ['video-params','container-fps','hwdec-current',
            'frame-drop-count','mistimed-frame-count','vo-delayed-frame-count']})
    finally:
        player.close()
    errors = [line for line in player.log.read_text(encoding='utf-8').splitlines() if '[e]' in line or '[f]' in line]
    assert not errors, errors
destination = ROOT / 'docs/modernization/size-results.json'
destination.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('PASS 720p60／1080p23.976／2160p30 原始播放')
