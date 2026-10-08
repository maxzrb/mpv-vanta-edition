"""维护者手动比较滤镜交接；隔离配置，三轮预热与至少20秒稳态采样。"""
import argparse
import ctypes
from ctypes import wintypes
import json
import hashlib
from pathlib import Path
import runpy
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/filter-handoff'
helpers = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))
Player, cpu = helpers['Player'], helpers['process_cpu_seconds']
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']


class Memory(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD),
                *[(name, ctypes.c_size_t) for name in ['PeakWorkingSetSize', 'WorkingSetSize',
                  'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                  'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage']]]


def memory(process):
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Memory), wintypes.DWORD]
    counters = Memory()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(int(process._handle), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {k: getattr(counters, field) / 1048576 for k, field in
            [('working_mb', 'WorkingSetSize'), ('private_mb', 'PrivateUsage')]}


def wait(p, check, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        quality = p.get('user-data/quality') or {}
        assert quality.get('state') != '失败', quality.get('error')
        if check():
            return
        time.sleep(.15)
    raise AssertionError('实际滤镜交接超时')


def enable(p, preset, group):
    started = time.monotonic()
    p.command('script-message', 'quality-select', preset)
    wait(p, lambda: (p.get('user-data/quality') or {}).get('state') == '已添加'
         and (p.get('user-data/quality') or {}).get('active', {}).get(group) == preset)
    return time.monotonic() - started


def sample(p, seconds, phase):
    p.command('script-message','test-handoff-phase',phase+'-start')
    keys = ['frame-drop-count', 'decoder-frame-drop-count']
    before = {k: p.get(k) or 0 for k in keys}
    position = p.get('time-pos')
    c0, wall = cpu(p.process), time.monotonic()
    points = []
    while time.monotonic() - wall < seconds:
        time.sleep(.5)
        assert p.get('pause') is False and p.get('speed') == 1, '采样被暂停或变速干扰'
        assert not p.get('window-minimized'),'窗口最小化，排除本轮'
        assert not p.get('eof-reached'), '素材长度不足，不能按低速或EOF计算性能'
        points.append(dict(seconds=time.monotonic()-wall, media=p.get('time-pos'),
                           drops=p.get('frame-drop-count'), **memory(p.process)))
    elapsed = time.monotonic() - wall
    p.command('script-message','test-handoff-phase',phase+'-end')
    return dict(seconds=elapsed, clock_ratio=(points[-1]['media']-position)/elapsed,
                cpu_core_percent=100*(cpu(p.process)-c0)/elapsed,
                counters={k: (p.get(k) or 0)-before[k] for k in keys},
                hwdec=p.get('hwdec-current'), output=p.get('video-out-params'),
                audio=p.get('audio-out-params'), samples=points)


def trial(media, preset, group, route, number, seconds, cycles):
    config = create_config('filter-handoff')
    # 仅测试副本解除最小化暂停；采样仍拒绝最小化窗口，不把不可见呈现当正常播放。
    with (config/'profiles.conf').open('a',encoding='utf-8',newline='\n') as file:
        file.write('\n[minimized]\n profile-cond=false\n')
    p = Player(['--config-dir='+str(config), '--hwdec='+route, '--d3d11va-zero-copy=no',
                '--ao=wasapi', '--mute=yes', '--pause=no', '--geometry=1920x1080',
                '--input-cursor=no', '--input-vo-keyboard=no', '--input-media-keys=no',
                '--input-terminal=no', str(media)], f'handoff-{preset}-{route}-{number}')
    p.ipc_timeout = 45
    try:
        p.wait_video()
        wait(p,lambda: p.get('hwdec-current') is not None,20)
        source = p.get('video-dec-params')
        original_hwdec = p.get('hwdec-current')
        assert original_hwdec == route, (route, original_hwdec)
        time.sleep(2)
        before = sample(p, 3,'before')
        load_seconds = enable(p, preset, group)
        time.sleep(5)
        filtered = sample(p, seconds,'filtered')
        assert p.get('hwdec-current') == original_hwdec
        # 跳转、暂停与三次启停在同一真实进程内验证，内存变化单列不冒充显存或泄漏结论。
        lifecycle = []
        for cycle in range(cycles):
            p.command('set_property', 'pause', True)
            p.command('seek', 5, 'absolute+exact')
            time.sleep(.5)
            assert p.get('pause') is True and abs(p.get('time-pos')-5)<.15
            p.command('script-message', 'quality-disable', group)
            wait(p, lambda: not p.get('vf'))
            assert p.get('hwdec-current') == original_hwdec
            p.command('set_property', 'pause', False)
            time.sleep(1)
            off = dict(cycle=cycle+1, phase='off', **memory(p.process))
            off['output'] = p.get('video-out-params')
            lifecycle.append(off)
            if cycle+1 < cycles:
                enable(p, preset, group)
                time.sleep(1)
                lifecycle.append(dict(cycle=cycle+1, phase='on', **memory(p.process)))
        time.sleep(5)
        restored = sample(p, min(5,seconds),'restored')
        assert not p.get('vf') and not (p.get('user-data/quality') or {}).get('active')
        assert restored['hwdec'] == original_hwdec
        assert source['w'] == restored['output']['w'] and source['h'] == restored['output']['h']
        assert restored['output']['pixelformat']==before['output']['pixelformat'], '关闭后GPU／copy交接格式未恢复'
        assert .97 < restored['clock_ratio'] < 1.03, '关闭后播放时钟未恢复'
        row = dict(preset=preset, route=route, round=number, source=source,
                   load_seconds=load_seconds, before=before, filtered=filtered,
                   restored=restored, lifecycle=lifecycle)
    finally:
        p.close()
    log = p.log.read_text(encoding='utf-8', errors='replace')
    assert not any(token in log for token in ['prepare_filter.py', 'capabilities.py',
                   'component_inventory', '--probe-frames'])
    assert not any(token in log for token in ['Lua error:', 'Script evaluation failed', 'No PTS after filter'])
    row['audio_underrun_log_lines'] = sum('underrun' in line.lower() for line in log.splitlines())
    for phase in ['before','filtered','restored']:
        # 日志参数格式由核心决定，下面按标记所在整行定位，不依赖字段引号形式。
        collecting=False;events=0;found=False
        for line in log.splitlines():
            if 'test-handoff-phase' in line and phase+'-start' in line:collecting=True;found=True
            elif 'test-handoff-phase' in line and phase+'-end' in line:collecting=False
            elif collecting and 'Audio device underrun detected.' in line:events+=1
        row[phase]['audio_underrun_events']=events if found else None
    return row


def extend(source, name):
    target = OUT/(name+'.mkv')
    # 复制压缩码流延长素材，稳态采样不跨短片循环，不重新编码原样本。
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-stream_loop', '-1', '-i', str(source), '-t', '150', '-map', '0:v:0',
                    '-map', '0:a?', '-c', 'copy', str(target)], check=True, timeout=60)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--cycles', type=int, default=3)
    parser.add_argument('--only', choices=['svp', 'ccd', 'rife-dml-426'])
    parser.add_argument('--resume', action='store_true', help='续跑已完成的本轮三轮20秒采样，不重计失败或短诊断')
    args = parser.parse_args()
    assert args.seconds > 0 and args.rounds > 0 and args.cycles > 0
    OUT.mkdir(parents=True, exist_ok=True)
    cases = [('svp', 'memc', ROOT/'tmp/modernization/optimization-20261005/svp-1080.mkv'),
             ('ccd', 'denoise', ROOT/'tmp/modernization/validation/size-2160.mkv'),
             ('rife-dml-426', 'memc', ROOT/'tmp/modernization/validation/compat-hevc10.mkv')]
    if args.only:
        cases = [c for c in cases if c[0] == args.only]
    cases = [(preset, group, extend(source, preset)) for preset, group, source in cases]
    filename='results.json' if args.seconds>=20 and args.rounds>=3 else 'diagnostic-'+str(args.only)+'.json'
    rows = []
    signature=hashlib.sha256(b''.join((ROOT/name).read_bytes() for name in [
        'portable_config/mpv.conf','portable_config/profiles.conf','portable_config/scripts/quality.lua',
        'portable_config/scripts/color-target.lua','portable_config/scripts/hwdec-select.lua'])).hexdigest()
    if args.resume:
        assert args.seconds>=20 and args.rounds>=3 and not args.only
        previous=json.loads((OUT/filename).read_text(encoding='utf-8'))
        assert previous['signature']==signature,'运行配置已变化，不能合并为同一组性能结论'
        rows=previous['trials']
        assert all(row['filtered']['seconds']>=20 and row['restored']['seconds']>=min(5,args.seconds)
                   and len([x for x in row['lifecycle'] if x['phase']=='off'])==args.cycles for row in rows)
    for number in range(1, args.rounds+1):
        for preset, group, media in cases:
            routes = ['d3d11va', 'd3d11va-copy']
            if number % 2 == 0:
                routes.reverse()
            for route in routes:
                if any(row['preset']==preset and row['route']==route and row['round']==number for row in rows):
                    continue
                row = trial(media, preset, group, route, number, args.seconds, args.cycles)
                rows.append(row)
                (OUT/filename).write_text(json.dumps(dict(
                    scope='串行实际播放；增强预热5秒后三轮20秒；关闭后5秒为状态回归',
                    signature=signature,trials=rows),
                    ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
                print(json.dumps(dict(preset=preset, route=route, round=number,
                    source=[row['source']['w'], row['source']['h']],
                    filtered={k:row['filtered'][k] for k in ['clock_ratio','cpu_core_percent','counters']},
                    restored={k:row['restored'][k] for k in ['clock_ratio','cpu_core_percent','counters']},
                    audio_underrun_log_lines=row['audio_underrun_log_lines']), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
