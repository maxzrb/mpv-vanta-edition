"""检查活动脚本语法、Shader 引用、回归记录和用户配置保留。"""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
paths = [path for base in ['scripts', 'script-modules', 'osc-style']
         for path in (ROOT / 'portable_config' / base).rglob('*.lua') if 'backup' not in path.parts]
destination = ROOT / 'tmp/modernization/lua-files.txt'
destination.write_text('\n'.join(path.relative_to(ROOT).as_posix() for path in paths) + '\n', encoding='utf-8', newline='\n')
code = 'for p in io.lines("tmp/modernization/lua-files.txt") do local f,e=loadfile(p); assert(f,p..": "..tostring(e)) end'
subprocess.run([str(ROOT / 'luajit.exe'), '-e', code], cwd=ROOT, check=True)
print('Lua syntax', len(paths))
python_paths = (list((ROOT / 'tools').glob('*.py')) + list((ROOT / 'portable_config/vs').glob('*.vpy'))
                + list((ROOT / 'portable_config/vs').glob('*.py')) + list((ROOT / 'portable_config/quality').glob('*.py')))
for path in python_paths:
    compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec')
print('Python syntax', len(python_paths))
input_text = (ROOT / 'portable_config/input.conf').read_text(encoding='utf-8-sig')
missing = [name for name in re.findall(r'~~/shaders/([^"\n]+?\.glsl)', input_text)
           if not (ROOT / 'portable_config/shaders' / name).is_file()]
assert not missing, missing
assert 'danmaku' not in input_text and '弹幕' not in input_text
assert len(re.findall(r'^CTRL\+0\s+script-message quality-clear-shaders\b', input_text, re.M)) == 1
assert len(re.findall(r'^Ctrl\+1\s+script-message quality-shader-command .*apply-profile FSRCNNX;', input_text, re.M)) == 1
assert 'script-message quality-reset #menu: 工具 > 画质处理' in input_text
assert not (ROOT / 'portable_config/scripts/uosc_danmaku').exists()
print('Shader 引用／弹幕活动入口 PASS')
stats = json.loads((ROOT / 'docs/modernization/stats-results.json').read_text(encoding='utf-8'))
assert len(stats['trials']) == 24
assert all(not any(trial['counters'].values()) for trial in stats['trials'])
assert all(trial['logged_subprocesses'] == 0 for trial in stats['trials'] if trial['implementation'] == 'after')
print('统计掉帧／外部查询 PASS')
for name in ['startup_format_logos.conf', 'window_size_position.conf']:
    relative = Path('portable_config/script-opts') / name
    assert (ROOT / relative).read_bytes() == (ROOT / 'backup/modernization-20261004' / relative).read_bytes()
print('用户既有选项逐字节保留 PASS')
manifest_path = ROOT / 'portable_config/script-assets/startup-format-logos/runtime/manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
assert manifest['version'] == 24
for key, asset in manifest['logos'].items():
    for prefix in ['', 'white_']:
        for name in asset.get(prefix + 'files', {}).values():
            path = manifest_path.parent / name
            assert path.stat().st_size == asset['w'] * asset['h'] * 4, str(path)
print('徽标主素材尺寸／文件完整性 PASS')
assert not subprocess.check_output(['git', 'diff', '--name-only', '--', '发布流程.md'], cwd=ROOT)
print('发布流程未修改 PASS')
