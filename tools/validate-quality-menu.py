"""通过真实 mpv IPC 验证原菜单恢复及两类处理的独立性。"""
import json
from pathlib import Path
import runpy
import time

ROOT = Path(__file__).resolve().parents[1]
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
OUT = ROOT / 'tmp/modernization/validation'
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']


def run():
    config = create_config('quality-menu')
    player = Player(['--config-dir=' + str(config), '--ao=null',
                     '--hwdec=no', '--pause=yes', '--geometry=1280x720',
                     str(OUT / 'quality-sdr10.mkv')], 'quality-menu')
    results = []
    # 首次真实 Shader 编译可能超过普通 IPC 时限，不额外启动模拟预热。
    player.ipc_timeout = 45
    try:
        player.wait_video()
        time.sleep(2)
        menu = player.get('menu-data') or player.get('user-data/menu/items')
        assert menu, '原生菜单未生成'
        text = json.dumps(menu, ensure_ascii=False)
        assert '着色器' in text and '视频滤镜' in text
        assert '画质增强' not in text and '专家库' in text
        assert all(tier not in text for tier in ['3050级参考', '4060级参考', '5060Ti级参考'])
        assert all(section in text for section in ['片源修复', '帧率改写', '修复错误标记'])
        assert all(x in text for x in ['播放性能', 'HQ · 默认', '恢复自动匹配', 'RIFE 4.26'])
        def performance_paths(items, parents=()):
            paths=[]
            for item in items:
                title=item.get('title','')
                if '播放性能' in title:paths.append((*parents,title))
                paths.extend(performance_paths(item.get('items',item.get('submenu',[])),(*parents,title)))
            return paths
        paths=performance_paths(menu if isinstance(menu,list) else menu.get('items',[]))
        assert paths and all('其它' in path and '画面' not in path for path in paths), paths
        assert '低功耗' not in text and '关闭全部补帧' not in text
        roots=menu if isinstance(menu,list) else menu.get('items',[])
        names=[item.get('title','') for item in roots]
        assert names.index('工具') < names.index('其它') < names.index('最小化'), names
        filters=next(item for item in roots if item.get('title')=='视频滤镜')
        children=filters.get('items',filters.get('submenu',[]))
        assert any(item.get('title')=='清空全部视频滤镜' for item in children)
        assert player.get('user-data/quality')['performance']=='balanced'
        assert player.get('linear-downscaling') is True
        assert '解锁' not in text and '尚未开放' not in text
        results.append('原菜单结构保留；滤镜一次启用／性能档位／自动匹配入口正常')

        # 用轻量外部滤镜检查独立性，不要求本机能运行任何 AI 模型。
        player.command('vf', 'add', '@menu-external:lavfi=[hflip]')
        original_vf = player.get('vf')
        for profile in ['FSRCNNX', 'Anime4K', 'Anime4K-Fast-A', 'Anime4K-HQ-B']:
            player.command('script-message', 'quality-shader-command', 'apply-profile ' + profile)
            time.sleep(.4)
            assert player.get('glsl-shaders'), profile
            assert player.get('vf') == original_vf, 'Shader 预设改变了视频滤镜'
        results.append('原有推荐／Anime4K 方案实际应用，外部 VF 保持')

        shaders = player.get('glsl-shaders')
        player.command('script-message', 'quality-clear-filters')
        time.sleep(.2)
        assert not player.get('vf') and player.get('glsl-shaders') == shaders
        player.command('vf', 'add', '@menu-external:lavfi=[hflip]')
        player.command('script-message', 'quality-clear-shaders')
        time.sleep(.2)
        assert not player.get('glsl-shaders') and player.get('vf')
        results.append('分别清空：另一类处理保持')

        player.command('script-message', 'quality-shader-command',
                       'change-list glsl-shaders toggle "~~/shaders/not-installed.glsl"')
        time.sleep(.2)
        assert player.get('glsl-shaders'), '专家入口不应人为拦截'
        results.append('缺失 Shader 请求交给实际加载器报告')
        player.command('script-message', 'quality-clear-shaders')

        player.command('set_property', 'video-unscaled', 'yes')
        time.sleep(.4)
        player.command('script-message', 'quality-shader-preset', 'Anime4K-HQ-AA')
        time.sleep(.2)
        assert player.get('glsl-shaders'), '不足 2× 只能提示，不得拦截'
        player.command('set_property', 'video-unscaled', 'no')
        time.sleep(.4)
        for quality in ['Fast', 'HQ']:
            for mode in ['A', 'B', 'C', 'AA', 'BB', 'CA']:
                profile = f'Anime4K-{quality}-{mode}'
                player.command('script-message', 'quality-shader-preset', profile)
                time.sleep(.2)
                assert player.get('user-data/quality')['active'].get('shader') == profile
        results.append('十二组 Anime4K 应用；倍率不再限制菜单')

        player.command('script-message', 'quality-menu', 'vs-upscale')
        time.sleep(2)
        assert player.get('user-data/uosc/menu/type') == 'quality-vs-upscale'
        player.command('screenshot-to-file', str(OUT / 'quality-vs-menu.png'), 'window')
        player.command('script-message', 'quality-shader-preset', 'Anime4K-Fast-A')
        time.sleep(.2)
        player.command('loadfile', str(OUT / 'quality-sdr10.mkv'), 'replace')
        player.wait_video()
        time.sleep(.4)
        assert not player.get('glsl-shaders')
        assert not player.get('user-data/quality')['active']
        results.append('VS 菜单打开；切片清除会话增强')

        # 广色域由用户主动选择，只提示尚未验证。
        player.command('loadfile', str(OUT / 'wide-sdr.mkv'), 'replace')
        player.wait_video()
        player.command('script-message', 'quality-select', 'artcnn')
        time.sleep(.2)
        assert player.get('glsl-shaders') and player.get('user-data/quality')['warning']
        results.append('广色域增强可用，色彩未验证只提示')
    finally:
        player.close()
    errors = [line for line in player.log.read_text(encoding='utf-8', errors='replace').splitlines()
              if '[e]' in line or '[f]' in line]
    assert not any('Lua error:' in x for x in errors), '\n'.join(errors)
    log = player.log.read_text(encoding='utf-8', errors='replace')
    assert 'probe.py' not in log and 'prepare_filter' not in log
    (OUT / 'quality-menu-results.json').write_text(
        json.dumps({'passed': results, 'limits': '320×180 功能回归；非显卡性能与色准验收'},
                   ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('\n'.join('PASS ' + result for result in results))


if __name__ == '__main__':
    run()
