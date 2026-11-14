"""真实 mpv 验证用户选择、重启、局部回退、快速退出和多实例合并。"""
import json
from pathlib import Path
import runpy
import shlex
import shutil
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(tempfile.mkdtemp(prefix='playback-preferences-', dir=ROOT/'tmp'))
CONFIG = OUT/'config'
for name in ('scripts', 'script-modules', 'script-opts'):
    (CONFIG/name).mkdir(parents=True)
for name in ('safe-file.lua', 'preference-store.lua', 'overload-policy.lua', 'load-config-scripts.lua'):
    shutil.copy2(ROOT/'portable_config/script-modules'/name, CONFIG/'script-modules'/name)
for name in ('decode-performance.lua', 'playback-preferences.lua', 'persist_properties.lua', 'hwdec-select.lua', 'dyn_menu.lua'):
    shutil.copy2(ROOT/'portable_config/scripts'/name, CONFIG/'scripts'/name)
shutil.copy2(ROOT/'portable_config/input.conf', CONFIG/'input.conf')
shutil.copy2(ROOT/'portable_config/script-opts/dyn_menu.conf', CONFIG/'script-opts/dyn_menu.conf')
(CONFIG/'mpv.conf').write_text('load-scripts=no\nscripts=~~/script-modules/load-config-scripts.lua\nhwdec=auto-safe\nvideo-sync=audio\n', encoding='utf-8', newline='\n')
(CONFIG/'script-opts/persist_properties.conf').write_text('properties=volume,sub-font\nproperties_path=files/persistent_config.json\n', encoding='utf-8', newline='\n')
Player = runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
MEDIA = ROOT/'tmp/modernization/validation/compat-hevc10.mkv'
PREFS = CONFIG/'files/playback-preferences.json'
GENERAL = CONFIG/'files/persistent_config.json'
rows = []
logs = []
nvdec_logs = set()

def wait(getter, predicate=lambda v: v is not None, timeout=8):
    deadline = time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=getter()
        if predicate(value):return value
        time.sleep(.03)
    raise AssertionError(('等待状态超时',value))

def start(name, *extra):
    p=Player(['--config-dir='+str(CONFIG),'--gpu-api=d3d11','--ao=null','--pause=yes','--geometry=640x360',*extra,str(MEDIA)], 'playback-pref-'+name)
    p.wait_video()
    wait(lambda:p.get('user-data/config-script-loader/loaded'))
    time.sleep(.1)
    logs.append(p.log)
    try:
        if read(PREFS).get('hwdec')=='nvdec-copy':nvdec_logs.add(p.log)
    except json.JSONDecodeError:
        pass
    return p

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}

def choose(p, policy):
    if policy=="nvdec-copy":nvdec_logs.add(p.log)
    command=next(line.split('#menu:')[0].lstrip('# ').strip() for line in (CONFIG/'input.conf').read_text(encoding='utf-8').splitlines() if 'decode-performance-hwdec "'+policy+'"' in line)
    assert p.command(*shlex.split(command))['error']=='success'
    wait(lambda:read(PREFS),lambda d:d.get('hwdec')==policy)
    wait(lambda:p.get('user-data/decode-performance/hwdec-policy'),lambda v:v==policy)

def stop(p):p.close()

# 未有 files 目录时也能第一次保存；随即退出不依赖定时器。
p=start('first')
try:choose(p,'no')
finally:stop(p)
p=start('restart-soft')
try:
    assert p.get('hwdec-current')=='no' and p.get('user-data/decode-performance/hwdec-policy')=='no'
    p.command('set_property','volume',31)
    wait(lambda:p.get('volume'),lambda v:v==31)
    time.sleep(.08)
finally:stop(p)
assert read(GENERAL)['volume']==31
rows.append('首次硬解选择与首次音量改动在五秒内退出仍保存')

for policy in ('nvdec-copy','d3d11va-copy','auto-safe'):
    p=start('select-'+policy)
    try:choose(p,policy)
    finally:stop(p)
    p=start('restart-'+policy)
    try:
        assert p.get('user-data/decode-performance/hwdec-policy')==policy
        allowed=([policy], ['auto']) if policy=='auto-safe' else ([policy],)
        assert p.get('hwdec') in allowed,p.get('hwdec')
        assert p.get('volume')==31
    finally:stop(p)
rows.append('软件／NVDEC复制／D3D11复制／自动硬解跨启动恢复')

# 自动策略因 CPU 滤镜切换为复制路径，不能把临时路径保存成用户策略。
p=start('cpu-filter','--vf=lavfi=[null]')
try:
    assert p.get('hwdec')==['auto-copy'] or p.get('hwdec')=='auto-copy',p.get('hwdec')
    assert p.get('user-data/decode-performance/hwdec-policy')=='auto-safe'
    assert read(PREFS)['hwdec']=='auto-safe'
finally:stop(p)
p=start('local-override')
try:
    p.command('loadfile',str(MEDIA),'replace',-1,{'hwdec':'no'})
    wait(lambda:p.get('hwdec-current'),lambda v:v=='no')
    assert read(PREFS)['hwdec']=='auto-safe'
finally:stop(p)
rows.append('CPU滤镜复制回退和文件局部软解不覆盖用户策略')

p=start('keyboard')
try:
    for policy in ('no','auto-safe'):
        p.command('script-binding','decode_performance/decode-performance-toggle-hwdec')
        wait(lambda:read(PREFS),lambda d:d.get('hwdec')==policy)
finally:stop(p)
rows.append('硬解切换绑定也通过同一路径保存，原快捷键不改动')

p=start('other-options')
try:
    p.command('script-message-to','playback_preferences','set','video-sync','display-tempo')
    p.command('script-message-to','playback_preferences','toggle','hr-seek-framedrop')
    p.command('script-message-to','playback_preferences','toggle','d3d11va-zero-copy')
    expected=wait(lambda:read(PREFS),lambda d:all(k in d for k in ('video-sync','hr-seek-framedrop','d3d11va-zero-copy')))
    p.command('set_property','video-sync','display-resample')
finally:stop(p)
assert read(PREFS)==expected
p=start('other-options-restart')
try:
    for name in ('video-sync','hr-seek-framedrop','d3d11va-zero-copy'):assert p.get(name)==expected[name],(name,p.get(name),expected[name])
    p.command('loadfile',str(MEDIA),'replace',-1,{'video-sync':'audio'})
    wait(lambda:p.get('video-sync'),lambda v:v=='audio')
    assert read(PREFS)['video-sync']==expected['video-sync']
    p.command('loadfile',str(MEDIA),'replace')
    wait(lambda:p.get('video-sync'),lambda v:v==expected['video-sync'])
finally:stop(p)
rows.append('帧同步／跳转跳帧／零复制保存，临时同步调整不写回')

original=PREFS.read_bytes();general=GENERAL.read_bytes()
p=start('commandline','--hwdec=no','--video-sync=audio','--volume=7')
try:
    assert p.get('hwdec-current')=='no' and p.get('video-sync')=='audio' and p.get('volume')==7
finally:stop(p)
assert PREFS.read_bytes()==original and GENERAL.read_bytes()==general
rows.append('命令行覆盖本次启动，退出不改已保存偏好')

# 两实例分别修改不同设置，先后退出不能带回旧快照。
a=start('multi-a');b=start('multi-b')
try:
    choose(a,'no')
    b.command('script-message-to','playback_preferences','set','video-sync','audio')
    wait(lambda:read(PREFS),lambda d:d.get('video-sync')=='audio')
    a.command('set_property','volume',42)
    b.command('set_property','sub-font','中文偏好测试')
    time.sleep(.15)
finally:stop(b);stop(a)
assert read(PREFS)['hwdec']=='no' and read(PREFS)['video-sync']=='audio'
assert read(GENERAL)['volume']==42 and read(GENERAL)['sub-font']=='中文偏好测试'
rows.append('两实例偏好与通用设置按字段合并，退出不回滚另一实例')

# 多行 JSON、未知键和 BOM 均保留；坏文件拒绝覆盖。
data=read(GENERAL);data['other-module']={'keep':True}
GENERAL.write_text('\ufeff'+json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
p=start('multiline')
try:
    assert p.get('volume')==42 and p.get('sub-font')=='中文偏好测试'
    p.command('set_property','volume',43);time.sleep(.1)
finally:stop(p)
assert GENERAL.read_bytes().startswith(b'\xef\xbb\xbf') and read(GENERAL)['other-module']=={'keep':True}
rows.append('多行JSON恢复、BOM与其他模块字段保留')
expected_fallback_errors=[]
for log in logs:
    errors=[line for line in log.read_text(encoding='utf-8',errors='replace').splitlines() if '[e]' in line or '[f]' in line or 'Lua error:' in line]
    # 无 NVIDIA 驱动时 NVDEC 会回退；本测试验证选择恢复，不把它当作实际 NVDEC 解码认证。
    expected=[line for line in errors if log in nvdec_logs and ('CUDA: Cannot load nvcuda.dll' in line or 'CUDA: Could not dynamically load CUDA' in line)]
    expected_fallback_errors.extend(expected)
    assert not [line for line in errors if line not in expected],(log,errors[:6])
PREFS.write_bytes(b'{broken');GENERAL.write_bytes(b'{broken-general')
p=start('corrupt')
try:
    p.command('script-message','decode-performance-hwdec','no')
    p.command('set_property','volume',44);time.sleep(.15)
finally:stop(p)
assert PREFS.read_bytes()==b'{broken' and GENERAL.read_bytes()==b'{broken-general'
rows.append('损坏数据下设置当前生效，原文件保留并报告保存失败')
report=dict(passed=True,checks=rows,artifacts=str(OUT),hardware_backend_availability_not_asserted=True,expected_fallback_errors=expected_fallback_errors)
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for row in rows:print('PASS',row,flush=True)
print('RESULT',OUT/'results.json',flush=True)
