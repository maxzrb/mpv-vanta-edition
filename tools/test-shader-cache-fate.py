"""固定文件样本及参考输出；用真实文件锁、目录联接和 mpv IPC 验证缓存维护。"""
import ctypes
from ctypes import wintypes
import hashlib
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
OUT = HOST_ROOT / 'tmp/modernization/shader-cache-fate'
OUT.mkdir(parents=True, exist_ok=True)
TASK = Path(tempfile.mkdtemp(prefix='run-', dir=OUT))
SAMPLE = json.loads((HOST_ROOT / 'tools/fate/samples/shader-cache.json').read_text(encoding='utf-8'))
HELPER = ROOT / 'installer/clear-shader-cache.ps1'
BOOTSTRAP = ("$p=ConvertFrom-Json $env:MPV_CACHE_PARAMETERS;$h=@{};"
             "foreach($v in $p.PSObject.Properties){$h[$v.Name]=$v.Value};"
             "& ([scriptblock]::Create([IO.File]::ReadAllText($env:MPV_CACHE_HELPER,[Text.Encoding]::UTF8))) @h")
LINES = []


def fixture(name):
    base = TASK / name
    for relative, content in SAMPLE['files'].items():
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8', newline='\n')
    return base


def environment(base):
    env = os.environ.copy()
    env['LOCALAPPDATA'] = str(base / 'local')
    env['MPV_CACHE_HELPER'] = str(HELPER)
    return env


def invoke(base, *, background=False, **options):
    parameters = dict(ConfigDirectory=str(base / 'config'), MaxWaitSeconds=10, **options)
    env = environment(base)
    env['MPV_CACHE_PARAMETERS'] = json.dumps(parameters, ensure_ascii=False)
    command = ['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
               'Bypass', '-Command', BOOTSTRAP]
    if background:
        return subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return subprocess.run(command, env=env, capture_output=True, timeout=20)


def report(base):
    return json.loads((base / 'config/files/shader-cache-cleanup.json').read_text(encoding='utf-8'))


def verify(base, count, *, partial=False):
    r = report(base)
    assert r['status'] == ('partial' if partial else 'complete'), r
    assert r['moved'] == count, r
    manifest = json.loads((Path(r['backup']) / 'manifest.json').read_text(encoding='utf-8'))
    assert len(manifest['moved']) == count
    for item in manifest['moved']:
        assert not Path(item['source']).exists()
        assert hashlib.sha256(Path(item['backup']).read_bytes()).hexdigest().upper() == item['sha256']
    for relative, content in SAMPLE['files'].items():
        path = base / relative
        if '/shaders_cache/' not in relative and not (r['mode'] == 'amd-vulkan' and path.suffix == '.parc'):
            assert path.read_text(encoding='utf-8') == content, path
    return r


def passed(name):
    LINES.append(name + ' PASS')
    print(LINES[-1], flush=True)


def wait(getter, predicate, name):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            value = getter()
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            value = None
        if predicate(value):
            return value
        time.sleep(.1)
    raise AssertionError((name, value))


def main():
    base = fixture('mpv')
    result = invoke(base)
    assert result.returncode == 0, result.stderr
    verify(base, SAMPLE['mpv_count'])
    passed('mpv-cache-only-preserves-source-history-icc-driver')

    base = fixture('amd')
    result = invoke(base, Mode='amd-vulkan')
    assert result.returncode == 0, result.stderr
    verify(base, SAMPLE['amd_count'])
    passed('amd-vulkan-archives-only-parc-and-mpv-cache')

    base = fixture('outside')
    result = invoke(base, ShaderCacheDirectory=str(base / 'config/shaders'))
    assert result.returncode != 0
    assert (base / 'config/shaders/source.glsl').read_text(encoding='utf-8') == SAMPLE['files']['config/shaders/source.glsl']
    assert not (base / 'backup').exists()
    passed('outside-cache-root-rejected')

    base = fixture('junction')
    link = base / 'config/cache/shaders_cache/link'
    subprocess.run(['cmd.exe', '/c', 'mklink', '/J', str(link), str(base / 'config/shaders')],
                   check=True, capture_output=True)
    result = invoke(base)
    assert result.returncode == 2, result.stderr
    verify(base, 2, partial=True)
    result = invoke(base, ShaderCacheDirectory=str(link))
    assert result.returncode != 0
    assert (link / 'source.glsl').is_file()
    passed('reparse-root-rejected-and-child-skipped')

    base = fixture('locked')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    locked = base / 'config/cache/shaders_cache/shader_a'
    handle = kernel.CreateFileW(str(locked), 0x80000000, 1, None, 3, 0x80, None)
    assert handle != ctypes.c_void_p(-1).value
    try:
        result = invoke(base)
        assert result.returncode == 2, result.stderr
        verify(base, 1, partial=True)
        assert locked.is_file()
    finally:
        kernel.CloseHandle(handle)
    assert invoke(base).returncode == 0
    verify(base, 1)
    passed('locked-file-partial-result-and-retry')

    base = fixture('inspect')
    result = invoke(base, Inspect=True)
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout.decode('utf-8-sig'))
    assert plan['count'] == 2 and not plan['pending']
    assert not (base / 'config/files/shader-cache-cleanup.json').exists() and not (base / 'backup').exists()
    assert (base / 'config/cache/shaders_cache/shader_a').is_file()
    passed('inspect-does-not-write-state-or-cache')

    # 真实播放器菜单启动独立维护进程；路径包含中文、引号及 PowerShell 特殊字符。
    base = fixture("中文 '配置 $()")
    (base / 'installer').mkdir()
    shutil.copy2(HELPER, base / 'installer/clear-shader-cache.ps1')
    (base / 'config/scripts').mkdir()
    shutil.copy2(ROOT / 'portable_config/scripts/shader-cache.lua', base / 'config/scripts/shader-cache.lua')
    (base / 'config/script-modules').mkdir()
    shutil.copy2(ROOT / 'portable_config/script-modules/safe-file.lua', base / 'config/script-modules/safe-file.lua')
    Player = runpy.run_path(str(HOST_ROOT / 'tools/validate-modernization.py'))['Player']
    Player.__init__.__globals__['ROOT'] = ROOT
    p = Player(['--config-dir=' + str(base / 'config'), '--vo=null', '--ao=null', '--force-window=no'],
               'shader-cache-menu')
    other = Player(['--no-config', '--vo=null', '--ao=null', '--force-window=no'], 'shader-cache-other')
    try:
        p.command('script-message-to', 'shader_cache', 'shader-cache-clean', 'mpv')
        pending = wait(lambda: report(base), lambda r: r and r['status'] == 'waiting', '任务确认')
        assert (base / 'config/cache/shaders_cache/shader_a').is_file()
        p.command('script-message-to', 'shader_cache', 'shader-cache-clean', 'mpv')
        time.sleep(1)
        assert report(base)['worker_pid'] == pending['worker_pid']
        late = base / 'config/cache/shaders_cache/shader_c'
        late.write_bytes(b'late-shutdown-cache')
        p.close()
        time.sleep(.8)
        assert report(base)['status'] == 'waiting' and late.is_file()
    finally:
        if p.process.poll() is None:
            p.close()
        other.close()
    wait(lambda: report(base), lambda r: r and r['status'] in ('complete', 'partial', 'failed'), '退出后隔离')
    verify(base, 3)
    log = p.log.read_text(encoding='utf-8', errors='replace')
    assert 'Lua error' not in log and '[e][shader_cache]' not in log
    passed('real-mpv-menu-defers-until-all-instances-exit')
    passed('late-shutdown-cache-and-duplicate-request')
    # 旧核心且缺少可选读取模块时，仍能使用同一入口；不能 dofile(nil) 阻塞读标准输入。
    older = HOST_ROOT / 'backup/core-upgrade-20261113/old/mpv.exe'
    assert older.is_file(), '旧核心兼容夹具缺失'
    base = fixture('old-core')
    (base / 'installer').mkdir()
    shutil.copy2(HELPER, base / 'installer/clear-shader-cache.ps1')
    p = Player(['--config-dir=' + str(base / 'config'), '--load-scripts=no',
                '--script=' + str(ROOT / 'portable_config/scripts/shader-cache.lua'),
                '--vo=null', '--ao=null', '--force-window=no'], 'shader-cache-old-core', executable=older)
    try:
        p.command('script-message-to', 'shader_cache', 'shader-cache-clean', 'mpv')
        wait(lambda: report(base), lambda r: r and r['status'] == 'waiting', '旧核心任务确认')
    finally:
        p.close()
    wait(lambda: report(base), lambda r: r and r['status'] in ('complete', 'partial', 'failed'), '旧核心退出后清理')
    verify(base, 2)
    assert 'Lua error' not in p.log.read_text(encoding='utf-8', errors='replace')
    passed('unicode-apostrophe-path-and-fallback-core')

    # 固定灰色视频通过真实 GPU 编译缓存；清理后再次启动应重新生成。
    media = TASK / 'gray.mkv'
    subprocess.run([str(ROOT / 'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-f', 'lavfi', '-i', 'color=c=gray:size=64x64:rate=24', '-t', '0.5',
                    '-c:v', 'ffv1', str(media)], check=True, capture_output=True)
    for backend in ['d3d11', 'vulkan']:
        base = fixture('gpu-' + backend)
        for cycle in range(2):
            p = Player(['--config-dir=' + str(base / 'config'), '--vo=gpu-next', '--gpu-api=' + backend,
                        '--ao=null', '--pause=yes', '--geometry=128x128', str(media)],
                       'shader-cache-regenerate-' + backend + '-' + str(cycle))
            try:
                p.wait_video()
            finally:
                p.close()
            log = p.log.read_text(encoding='utf-8', errors='replace')
            assert '[e]' not in log and '[f]' not in log
            cache_files = list((base / 'config/cache/shaders_cache').rglob('shader_*'))
            generated = [path for path in cache_files if path.name not in ('shader_a', 'shader_b')]
            assert generated and all(path.stat().st_size > 0 for path in generated), backend
            if cycle == 0:
                result = invoke(base)
                assert result.returncode == 0, result.stderr
                assert not list((base / 'config/cache/shaders_cache').rglob('shader_*'))
    passed('gpu-cache-regenerates-after-cleanup-d3d11-vulkan')

    # 执行 04 的实际复制片段验证依赖交付；不构建归档，不更改版本。
    stage = base / 'stage'
    env = os.environ.copy()
    env['MPV_CACHE_REPO'], env['MPV_CACHE_STAGE'] = str(HOST_ROOT), str(stage)
    code = ("$Root=$env:MPV_CACHE_REPO;$Stage=$env:MPV_CACHE_STAGE;"
            "$s=[IO.File]::ReadAllText((Join-Path $Root 'build-04-config.ps1'),[Text.Encoding]::UTF8);"
            "$a=$s.IndexOf('$installerDest =');$b=$s.IndexOf('foreach ($file in @(''README.MD''',$a);"
            "& ([scriptblock]::Create($s.Substring($a,$b-$a)))")
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', code],
                            env=env, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    for name in ['clear-shader-cache.ps1', 'mpv-清理着色器缓存.cmd']:
        assert (stage / 'installer' / name).read_bytes() == (ROOT / 'installer' / name).read_bytes()
    base_builder = (HOST_ROOT / 'build-01-base.ps1').read_text(encoding='utf-8')
    assert 'Invoke-CopyTo $BaseBuild @("installer", "updater.bat")' in base_builder
    private_builder = (HOST_ROOT / 'build-full-private.ps1').read_text(encoding='utf-8')
    assert '01-mpv-base' in private_builder and '04-mpv-config' in private_builder
    passed('package-01-04-private-maintenance-coverage')

    actual = '\n'.join(LINES) + '\n'
    (OUT / 'actual.txt').write_text(actual, encoding='utf-8', newline='\n')
    assert actual == (HOST_ROOT / 'tools/fate/ref/shader-cache').read_text(encoding='utf-8')
    (OUT / 'results.json').write_text(json.dumps(dict(passed=True, task=str(TASK), lines=LINES),
                                               ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
