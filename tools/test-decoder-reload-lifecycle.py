"""用实际 mpv 验证解码重载失败、停止和切换文件后的恢复，不修改活动配置。"""
import argparse
import json
from pathlib import Path
import runpy
import re
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
Player = runpy.run_path(str(ROOT / 'tools/validate-modernization.py'))['Player']


def wait(getter, predicate, label):
    deadline = time.monotonic() + 20
    value = None
    while time.monotonic() < deadline:
        value = getter()
        if predicate(value):
            return value
        time.sleep(.03)
    raise AssertionError((label, value))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package = args.package_root.resolve()
    Player.__init__.__globals__['ROOT'] = package
    create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']
    create_config.__globals__['ROOT'] = package
    task = Path(tempfile.mkdtemp(prefix='decoder-lifecycle-', dir=ROOT / 'tmp'))
    fixture = ROOT / 'tmp/modernization/validation/compat-hevc10.mkv'
    assert fixture.is_file()
    replacement = task / 'next.mkv'
    replacement.write_bytes(fixture.read_bytes())
    injector = task / 'interrupt.lua'
    injector.write_text("""local mp = require 'mp'
local action, target
mp.register_script_message('lifecycle-arm', function(mode, path)
    action, target = mode, path
    mp.set_property('user-data/lifecycle-test/armed', mode)
end)
mp.add_hook('on_load', 80, function()
    if not action then return end
    local mode, path = action, target
    action, target = nil, nil
    mp.set_property('user-data/lifecycle-test/injected', mode)
    -- 在真实加载钩子内制造失败／停止／换片，覆盖 on_loaded 不会到达的分支。
    if mode == 'failure' then
        mp.set_property('stream-open-filename', path)
    elseif mode == 'stop' then
        mp.commandv('stop')
    elseif mode == 'replace' then
        mp.commandv('loadfile', path, 'replace')
    end
end)
""", encoding='utf-8', newline='\n')
    rows = []
    for mode in ('normal', 'failure', 'stop', 'replace'):
        config = create_config('decoder-lifecycle-' + mode)
        # 固定单项播放列表，避免失败后自动加载同目录的其他测试视频。
        with (config / 'script-opts/autoload.conf').open('a', encoding='utf-8', newline='\n') as f:
            f.write('\ndisabled=yes\n')
        uosc = config / 'script-opts/uosc.conf'
        uosc.write_bytes(re.sub(rb'(?m)^seek_mode=.*$', b'seek_mode=keyframes', uosc.read_bytes()))
        (config / 'files/playback-preferences.json').write_text(
            '{"hwdec":"no"}\n', encoding='utf-8', newline='\n')
        player = Player(['--config-dir=' + str(config), '--gpu-api=d3d11',
                         '--ao=null', '--pause=yes', '--geometry=640x360',
                         '--script=' + str(injector), '--start=1', str(fixture)],
                        'decoder-lifecycle-' + task.name + '-' + mode,
                        executable=package / 'mpv.exe')
        try:
            player.wait_video()
            wait(lambda: player.get('hwdec-current'), lambda v: v == 'no', '初始软解')
            player.command('seek', '1', 'absolute+exact')
            wait(lambda: player.get('seeking'), lambda v: v is False, '初始精确位置')
            wait(lambda: player.get('time-pos'), lambda v: v is not None and abs(v - 1) < .05,
                 '初始位置稳定')
            original_seek = player.get('hr-seek')
            offset = player.log.stat().st_size

            def segment():
                return player.log.read_bytes()[offset:].decode('utf-8', errors='replace')

            before = player.get('time-pos')
            if mode != 'normal':
                target = task / 'missing.mkv' if mode == 'failure' else replacement
                player.command('script-message', 'lifecycle-arm', mode, str(target))
                wait(lambda: player.get('user-data/lifecycle-test/armed'),
                     lambda v: v == mode, '注入已就绪')
            player.command('script-message', 'decode-performance-hwdec', 'd3d11va-copy')
            if mode == 'normal':
                wait(segment, lambda v: '解码器重载参数已应用：' in v, '正常重载')
                wait(lambda: player.get('hwdec-current'),
                     lambda v: v == 'd3d11va-copy', '实际复制硬解')
                wait(lambda: player.get('seeking'), lambda v: v is False, '定位结束')
                assert abs(player.get('time-pos') - before) < .05
                wait(lambda: player.get('hr-seek'), lambda v: v == original_seek,
                     '还原日常跳转偏好')
                assert '取消解码器重载：' not in segment()
            else:
                wait(segment, lambda v: '取消解码器重载：' in v, '异常清理')
                if mode in ('failure', 'stop'):
                    wait(lambda: player.get('idle-active'), lambda v: v is True, '返回空闲')
                    player.command('script-message', 'decode-performance-hwdec', 'no')
                    wait(lambda: player.get('hwdec'), lambda v: v in ('no', ['no']),
                         '空闲选择立即生效')
                    assert '解码器正在重建，完成后应用最新选择' not in segment()
                    player.command('loadfile', str(fixture), 'replace')
                else:
                    wait(lambda: player.get('path'), lambda v: v == str(replacement), '用户换片')
                player.wait_video()
            # 异常后再次完整切换，确认没有残留锁、轨道或旧文件定位。
            offset = player.log.stat().st_size
            player.command('script-message', 'decode-performance-hwdec', 'no')
            wait(segment, lambda v: '解码器重载参数已应用：' in v, '后续重载')
            wait(lambda: player.get('hwdec-current'), lambda v: v == 'no', '后续软解')
            wait(lambda: player.get('seeking'), lambda v: v is False, '后续定位')
            errors = [line for line in segment().splitlines()
                      if '[e]' in line or '[f]' in line or 'Lua error:' in line]
            assert not errors, errors[:8]
            assert player.get('pause') is True
            wait(lambda: player.get('hr-seek'), lambda v: v == original_seek, '最终跳转偏好')
            rows.append(dict(mode=mode, passed=True, path=player.get('path'),
                             final_hwdec=player.get('hwdec-current'),
                             final_position=player.get('time-pos'), log=str(player.log),
                             expected_load_error=mode == 'failure'))
            print('PASS 真实解码重载生命周期', mode, flush=True)
        finally:
            player.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(passed=True, package_root=str(package), rows=rows),
                                      ensure_ascii=False, indent=2) + '\n',
                           encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
