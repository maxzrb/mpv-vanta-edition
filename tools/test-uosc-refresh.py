"""真实 uosc 验证格式信息失效缓存及中文／emoji 搜索编辑。"""
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(tempfile.mkdtemp(prefix='uosc-refresh-', dir=ROOT / 'tmp'))
CONFIG = OUT / 'config'
(CONFIG / 'scripts').mkdir(parents=True)
(CONFIG / 'script-opts').mkdir()
shutil.copytree(ROOT / 'portable_config/scripts/uosc', CONFIG / 'scripts/uosc')
shutil.copytree(ROOT / 'portable_config/script-modules', CONFIG / 'script-modules')
for name in ['uosc.conf', 'uosc-themes.json']:
    shutil.copy2(ROOT / 'portable_config/script-opts' / name, CONFIG / 'script-opts' / name)
with (CONFIG / 'scripts/uosc/main.lua').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('''
mp.register_script_message('test-media-cache', function(force)
    local element=Elements.media_info
    local original_get,original_visibility=mp.get_property,element.get_visibility
    local reads=0
    mp.get_property=function(name,...)
        if name=='video-codec' then reads=reads+1 end
        return original_get(name,...)
    end
    element.get_visibility=function() return 1 end
    if force=='yes' then element.media_info_dirty=true end
    for index=1,100 do element:render() end
    mp.get_property,element.get_visibility=original_get,original_visibility
    mp.set_property_native('user-data/uosc-refresh-test',{reads=reads,info=element.media_info})
end)
mp.register_script_message('test-poison-cache', function()
    Elements.media_info.media_info={video_present=true,video_codec='SENTINEL'}
    Elements.media_info.media_info_dirty=false
    mp.set_property_native('user-data/uosc-refresh-poisoned',true)
end)
mp.register_script_message('test-search-delete', function()
    local menu=Elements.menu
    menu.current.search.cursor=0
    menu:search_query_delete()
    mp.set_property_native('user-data/uosc-search-test',{query=menu.current.search.query,open=not menu.destroyed})
end)
''')
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']
media = ROOT / 'tmp/thumbfast-lifecycle/fixture.mp4'
assert media.is_file(), '请先运行 test-thumbfast-lifecycle.py'
player = Player(['--config-dir=' + str(CONFIG), '--vo=gpu-next', '--gpu-api=d3d11', '--ao=null',
                 '--pause=yes', '--geometry=960x540', '--window-minimized=yes', str(media)], 'uosc-refresh')


def wait(predicate, label):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.03)
    raise AssertionError(label)


def sample(force=False):
    player.command('set_property', 'user-data/uosc-refresh-test', None)
    player.command('script-message-to', 'uosc', 'test-media-cache', 'yes' if force else 'no')
    wait(lambda: player.get('user-data/uosc-refresh-test') is not None, '媒体信息缓存')
    result = player.get('user-data/uosc-refresh-test')
    assert result['reads'] == 1 if force else result['reads'] <= 1, result
    assert result['info']['video_codec'] == 'AVC', result
    return result


try:
    player.wait_video()
    time.sleep(.2)
    first = sample(True)
    player.command('script-message-to', 'uosc', 'test-poison-cache')
    wait(lambda: player.get('user-data/uosc-refresh-poisoned') is True, '标记旧缓存')
    player.command('set_property', 'video-rotate', 90)
    time.sleep(.2)
    second = sample()
    player.command('set_property', 'user-data/uosc-refresh-poisoned', False)
    player.command('script-message-to', 'uosc', 'test-poison-cache')
    wait(lambda: player.get('user-data/uosc-refresh-poisoned') is True, '标记换片旧缓存')
    player.command('loadfile', str(media))
    player.wait_video()
    time.sleep(.2)
    third = sample()
    data = dict(type='search-edit-test', title='测试', search_style='palette',
                search_suggestion='中🙂A', search_keep_open_on_empty=True, items=[],
                on_search=['ignore'], search_debounce='submit')
    player.command('script-message-to', 'uosc', 'open-menu', json.dumps(data, ensure_ascii=False))
    wait(lambda: player.get('user-data/uosc/menu/type') == 'search-edit-test', '搜索框打开')
    for expected in ['🙂A', 'A', '']:
        player.command('set_property', 'user-data/uosc-search-test', None)
        player.command('script-message-to', 'uosc', 'test-search-delete')
        wait(lambda: player.get('user-data/uosc-search-test') is not None, 'Delete 字符')
        state = player.get('user-data/uosc-search-test')
        assert state == dict(query=expected, open=True), state
finally:
    player.close()
errors = [line for line in player.log.read_text(encoding='utf-8').splitlines()
          if '[e]' in line or '[f]' in line or 'Lua error' in line]
assert not errors, errors[:5]
(OUT / 'result.json').write_text(json.dumps(dict(samples=[first, second, third], errors=errors),
                                          ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS 100次实际重绘只采集一次静态格式；旋转／重载后更新；中文和emoji整字符删除；空搜索框保持打开')
