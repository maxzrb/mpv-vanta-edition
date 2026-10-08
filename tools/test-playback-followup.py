"""真实播放验证：SVP 低帧率、手动裁剪、简洁状态及可滚动详情。"""
import json
from pathlib import Path
import runpy
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/playback-followup'
OUT.mkdir(parents=True, exist_ok=True)
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']


def wait_for(check, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(.2)
    raise AssertionError('播放状态未在时限内完成')


def crop_compatibility(fixture):
    hdr = OUT / 'crop-hdr10.mkv'
    subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'lavfi', '-i', 'testsrc2=size=640x270:rate=24',
                    '-vf', 'pad=640:360:0:45:black', '-t', '12', '-pix_fmt', 'yuv420p10le',
                    '-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '18',
                    '-x265-params', 'log-level=error:colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc',
                    '-color_primaries', 'bt2020', '-color_trc', 'smpte2084', '-colorspace', 'bt2020nc', str(hdr)], check=True)
    rows = []
    for mode, media in [('no', fixture), ('d3d11va-copy', fixture), ('auto-safe', hdr)]:
        player = Player(['--config-dir=' + str(create_config('crop-compatibility')),
                         '--hwdec=' + mode, '--ao=null', '--pause=no', '--geometry=960x540',
                         str(media)], 'crop-compatibility-' + mode)
        try:
            player.wait_video()
            time.sleep(1)
            before = player.get('video-params')
            player.command('script-binding', 'dynamic_crop/toggle_crop')
            wait_for(lambda: player.get('video-crop') not in ['', None, '640x360+0+0'])
            wait_for(lambda: (player.get('video-out-params') or {}).get('crop-h') == 270)
            after = player.get('video-out-params')
            for key in ['primaries', 'gamma', 'colormatrix', 'colorlevels']:
                assert after[key] == before[key], (mode, key)
            if mode == 'auto-safe':
                assert after['pixelformat'] == 'd3d11' and after['hw-pixelformat'] == before['hw-pixelformat']
            rows.append({'mode': mode, 'detected': player.get('video-crop'),
                         'input': before, 'output': after})
        finally:
            player.close()
        log = player.log.read_text(encoding='utf-8')
        assert 'Lua error:' not in log and 'Disabling filter' not in log
        assert 'Switch to SW decoding or HW -copy variant' not in log
    return rows


def run():
    fixture = OUT / 'crop-sdr.mkv'
    subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'lavfi', '-i', 'testsrc2=size=640x270:rate=24000/1001',
                    '-vf', 'pad=640:360:0:45:black', '-t', '45', '-c:v', 'libx264',
                    '-preset', 'ultrafast', '-crf', '18', str(fixture)], check=True)
    player = Player(['--config-dir=' + str(create_config('playback-followup')),
                     '--hwdec=auto-safe', '--ao=wasapi', '--mute=yes', '--pause=no',
                     '--geometry=960x540', str(fixture)], 'playback-followup')
    rows = {}
    try:
        player.wait_video()
        time.sleep(2)
        assert not player.get('vf') and player.get('hwdec-current') == 'd3d11va'
        assert 'Switch to SW decoding or HW -copy variant' not in player.log.read_text(encoding='utf-8')
        player.command('script-binding', 'dynamic_crop/toggle_crop')
        wait_for(lambda: player.get('video-crop') not in ['', None, '640x360+0+0'])
        wait_for(lambda: (player.get('video-out-params') or {}).get('crop-h') == 270)
        crop = player.get('video-crop')
        assert not crop.startswith('640x360'), crop
        assert player.get('hwdec-current') == 'd3d11va'
        assert player.get('video-out-params')['pixelformat'] == 'd3d11', '检测旁路不应下载主输出'
        rows['crop'] = {'detected': crop, 'hwdec': player.get('hwdec-current')}
        player.command('script-binding', 'dynamic_crop/toggle_crop')
        time.sleep(.3)
        assert player.get('video-crop') == crop
        player.command('script-binding', 'dynamic_crop/toggle_crop')
        time.sleep(.3)
        assert player.get('video-crop') == ''
        player.command('vf', 'clr', '')

        player.command('script-message', 'quality-select', 'svp')
        wait_for(lambda: (player.get('user-data/quality') or {}).get('state') == '已添加', 45)
        time.sleep(2)
        assert any(f.get('label') == 'quality-memc' for f in player.get('vf'))
        # estimated-vf-fps 为时间戳滚动估计，短样本允许小幅舍入波动。
        assert abs(player.get('estimated-vf-fps') - 60000/1001) < .1
        rows['svp-low-fps'] = {'input': player.get('container-fps'),
                               'output': player.get('estimated-vf-fps'), 'vf': player.get('vf')}
        player.command('script-message', 'quality-reset')
        # 撤链完成到下一帧重配置之间，video-out-params 仍可能描述旧 VS 帧。
        wait_for(lambda: (player.get('video-out-params') or {}).get('pixelformat')=='d3d11')
        player.command('set_property', 'pause', True)
        player.command('script-message', 'show-quality-status')
        wait_for(lambda: player.get('user-data/uosc/menu/type') == 'quality-active')
        compact = player.get('user-data/quality-status')
        assert len(compact['items']) <= 12 and not any('交换链' in i['title'] for i in compact['items'])
        time.sleep(1)
        player.command('screenshot-to-file', str(OUT / 'active-items-compact.png'), 'window')
        player.command('script-message', 'color-status')
        wait_for(lambda: player.get('user-data/uosc/menu/type') == 'quality-details')
        details = player.get('user-data/quality-status')
        assert len(details['items']) > 20 and any('实际设置' in i['title'] for i in details['items'])
        assert any('整数 8bit [nv12]' in i['title'] for i in details['items']), '硬解源格式须明确整数精度'
        assert any('主输出保持 GPU 表面' in i['title'] for i in details['items']), '无 VS 时应标注实际 GPU 交接'
        assert any('不能由最终输出推断' in i['title'] for i in details['items']), '最终输出不能证明中间链路'
        time.sleep(1)
        player.command('screenshot-to-file', str(OUT / 'color-details-top.png'), 'window')
        # 键盘 PageDown 必须可查看信息列表，不能把只读列表困在首屏。
        player.command('keypress', 'PGDWN')
        player.command('keypress', 'END')
        time.sleep(.5)
        player.command('screenshot-to-file', str(OUT / 'color-details-page2.png'), 'window')
        rows['status'] = {'compact_items': len(compact['items']), 'detail_items': len(details['items'])}
    finally:
        player.close()
    log = player.log.read_text(encoding='utf-8')
    assert 'Lua error:' not in log and 'Script evaluation failed' not in log
    assert 'Switch to SW decoding or HW -copy variant' not in log
    assert 'probe.py' not in log and 'prepare_filter' not in log
    rows['application-flow'] = '无裁剪硬解误报、Lua 错误、组件扫描或模拟试跑'
    rows['crop-compatibility'] = crop_compatibility(fixture)
    (OUT / 'results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                                    encoding='utf-8', newline='\n')
    print('PASS 裁剪直接／copy／软解／HDR10；SVP 低帧率；简洁状态／详情翻页；普通流程无核验')


if __name__ == '__main__':
    run()
