"""对照当前核心核验解码菜单覆盖、全部选项保存与实际 uosc 菜单。"""
import json
from pathlib import Path
import re
import runpy
import shlex
import shutil
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(tempfile.mkdtemp(prefix='hwdec-menu-',dir=ROOT/'tmp'))
Player=runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
source=(ROOT/'portable_config/input.conf').read_text(encoding='utf-8')
entries=[]
for line in source.splitlines():
    m=re.search(r'decode-performance-hwdec "([\w-]+)".*#menu:\s*(.*?)\s+#@',line)
    if m:entries.append(dict(policy=m[1],path=m[2],command=line.split('#menu:')[0].lstrip('# ').strip()))
assert len({e['policy'] for e in entries})==len(entries)
help_text=subprocess.check_output([str(ROOT/'mpv.com'),'--no-config','--hwdec=help']).decode('utf-8',errors='replace')
compiled=set(re.findall(r'^  ([\w-]+) \(',help_text,re.M))-{'auto'}
ignored={'vaapi':'官方文档列为Linux直出；Windows复制路径vaapi-copy保留'}
special={'auto-safe','auto-copy-safe','auto-unsafe','auto-copy-unsafe','no'}
offered={e['policy'] for e in entries}
assert compiled-set(ignored)==offered-special,(compiled-offered,offered-compiled-special)
assert all(e['policy'] in compiled|special for e in entries)
# 本轮不改变用户已整理的两套菜单。
previous=subprocess.check_output(['git','show','HEAD:portable_config/input.conf'],cwd=ROOT).decode('utf-8')
for title in ('着色器','视频滤镜'):
    pattern=re.compile(r'#(?:menu:|!)\s*'+title+r' > ')
    assert [s for s in previous.splitlines() if pattern.search(s)]==[s for s in source.splitlines() if pattern.search(s)]
config=OUT/'config'
for name in ('scripts','script-modules','script-opts'):(config/name).mkdir(parents=True)
for name in ('safe-file.lua','preference-store.lua','load-config-scripts.lua'):
    shutil.copy2(ROOT/'portable_config/script-modules'/name,config/'script-modules'/name)
for name in ('decode-performance.lua','dyn_menu.lua'):
    shutil.copy2(ROOT/'portable_config/scripts'/name,config/'scripts'/name)
shutil.copy2(ROOT/'portable_config/script-opts/dyn_menu.conf',config/'script-opts/dyn_menu.conf')
shutil.copy2(ROOT/'portable_config/input.conf',config/'input.conf')
(config/'mpv.conf').write_text('load-scripts=no\nscripts=~~/script-modules/load-config-scripts.lua\n',encoding='utf-8',newline='\n')
def wait(getter,predicate=lambda v:v is not None):
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        try:
            value=getter()
            if predicate(value):return value
        except (StopIteration, TypeError, KeyError, FileNotFoundError, PermissionError):
            value=None
        time.sleep(.03)
    raise AssertionError(('等待超时',value))
def start(label):
    p=Player(['--config-dir='+str(config),'--vo=null','--ao=null','--force-window=no'],'hwdec-matrix-'+label)
    wait(lambda:p.get('user-data/decode-performance/hwdec-policy'))
    return p
def node(items,title):return next(i for i in items if i.get('title','').strip()==title)
def children(item):return item.get('items',item.get('submenu',[]))
def selections(items):
    result=[]
    for item in items:
        if 'checked' in item.get('state',[]):result.append(item.get('cmd',''))
        result.extend(selections(children(item)))
    return result
results=[]
for entry in entries:
    policy=entry['policy'];p=start(policy+'-choose')
    try:
        p.command(*shlex.split(entry['command']))
        wait(lambda:p.get('user-data/decode-performance/hwdec-policy'),lambda v:v==policy)
        wait(lambda:json.loads((config/'files/playback-preferences.json').read_text(encoding='utf-8')),lambda d:d.get('hwdec')==policy)
    finally:p.close()
    p=start(policy+'-restart')
    try:
        assert p.get('user-data/decode-performance/hwdec-policy')==policy
        actual=p.get('hwdec')
        assert actual in ([policy], ['auto'] if policy=='auto-safe' else [policy], ['auto-copy'] if policy=='auto-copy-safe' else [policy]),(policy,actual)
        selected=wait(lambda:selections(children(node(children(node(p.get('menu-data'),'视频')),'解码方式'))),lambda v:len(v)==1 and '"'+policy+'"' in v[0])
    finally:p.close()
    results.append(dict(policy=policy,restored=True,single_checked=True))
    print('PASS 菜单保存／重启／唯一勾选',policy,flush=True)

# 用完整配置和实际视频验证临时补帧同步调整不会覆盖用户选择，并检查真实菜单。
create=runpy.run_path(str(ROOT/'tools/isolated-config.py'))['create_config']
full=create('hwdec-full')
with (full/'scripts/uosc/main.lua').open('a',encoding='utf-8',newline='\n') as f:
    f.write("\nmp.register_script_message('test-hwdec-menu', function() mp.set_property_native('user-data/hwdec-menu-test', get_menu_items()) end)\n")
media=ROOT/'tmp/modernization/validation/compat-hevc10.mkv'
screens=[]
p=Player(['--config-dir='+str(full),'--gpu-api=d3d11','--ao=null','--pause=yes',str(media)],'hwdec-full-menu')
try:
    p.wait_video();time.sleep(.3)
    p.command('script-message-to','playback_preferences','set','video-sync','audio')
    pref=full/'files/playback-preferences.json'
    wait(lambda:json.loads(pref.read_text(encoding='utf-8')),lambda d:d.get('video-sync')=='audio')
    p.command('script-message','quality-interpolation')
    wait(lambda:p.get('video-sync'),lambda v:v=='display-resample')
    assert json.loads(pref.read_text(encoding='utf-8'))['video-sync']=='audio'
    p.command('script-message','quality-interpolation')
    wait(lambda:p.get('video-sync'),lambda v:v=='audio')
    p.command('script-message','decode-performance-hwdec','d3d11va-copy')
    wait(lambda:p.get('user-data/decode-performance/hwdec-policy'),lambda v:v=='d3d11va-copy')
    wait(lambda:selections(children(node(children(node(p.get('menu-data'),'视频')),'解码方式'))),lambda v:len(v)==1 and '"d3d11va-copy"' in v[0])
    p.command('script-message-to','uosc','test-hwdec-menu')
    ui=wait(lambda:p.get('user-data/hwdec-menu-test'))
    main=children(node(children(node(ui,'视频')),'解码方式'))
    assert [i['title'].strip() for i in main]==['自动硬解','自动硬解 · copy','D3D11VA','D3D11VA · copy','NVDEC','NVDEC · copy','Vulkan Video','Vulkan Video · copy','其他后端','软件解码']
    assert node(main,'D3D11VA · copy')['icon']=='check'
    assert len(children(node(main,'其他后端')))==13
    p.command('set_property','geometry','1000x700');time.sleep(.2)
    p.command('show-text','')
    for title in ('视频 > 解码方式','视频 > 解码方式 > 其他后端'):
        p.command('script-message-to','uosc','show-submenu',title);time.sleep(.4)
        image=OUT/('other-backends.png' if title.endswith('其他后端') else 'decode-menu.png')
        assert p.command('screenshot-to-file',str(image),'window')['error']=='success';screens.append(str(image))
        p.command('script-message-to','uosc','menu');time.sleep(.15)
finally:p.close()
errors=[s for s in p.log.read_text(encoding='utf-8',errors='replace').splitlines() if '[e]' in s or '[f]' in s or 'Lua error:' in s]
assert not errors,errors[:6]
report=dict(passed=True,compiled_methods=sorted(compiled),excluded_methods=ignored,menu_choices=results,aliases_not_duplicated=True,protected_menus_unchanged=True,full_config_quality_temporary_sync_not_saved=True,screenshots=screens,limit='全部选项的保存／恢复在无片源状态验证；实际视频验证D3D11复制与临时同步，不代表每种显卡和互操作组合均可用',sources=['https://mpv.io/manual/master/#options-hwdec','https://raw.githubusercontent.com/mpv-player/mpv/master/video/decode/vd_lavc.c'])
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('PASS 当前核心覆盖／双菜单／完整配置／临时同步与截图',OUT/'results.json',flush=True)
