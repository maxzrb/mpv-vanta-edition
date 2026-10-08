"""活动色彩配置的原始 GPU 输出回归；只在自有诊断进程内读取，不改系统 HDR。"""
import json
import math
import os
import runpy
import struct
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/modernization/color-output-20261008'
OUT.mkdir(parents=True, exist_ok=True)
create_config = runpy.run_path(str(ROOT / 'tools/isolated-config.py'))['create_config']
create_player = runpy.run_path(str(ROOT / 'tools/gpu-readback.py'))['create_player']
hdr = runpy.run_path(str(ROOT / 'tools/test-hdr-gpu-reference.py'))
hdr['fixture'].__globals__['OUT'] = OUT
reference = runpy.run_path(str(ROOT / 'tools/color-reference.py'))
chunk = runpy.run_path(str(ROOT / 'tools/validate-color-ramp.py'))['chunk']


def wait(player, predicate):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        value = player.get('user-data/color-target')
        if value and predicate(value):
            return value
        time.sleep(.1)
    raise AssertionError(player.get('user-data/color-target'))


def png(name, width, height, pixel):
    path = OUT / (name + '.png')
    rows = b''.join(b'\x00' + b''.join(struct.pack('>3H', *pixel(x, y)) for x in range(width)) for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 16, 2, 0, 0, 0))
                     + chunk(b'sRGB', b'\x00') + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
    return path


def sdr_linear(value):
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def launch(media, name, simulated_hdr=False, size='256x256'):
    # 去掉遮挡测试色块的 UI；保留主配置及实际色彩／滤镜／硬解管理脚本。
    excluded = ['uosc', 'stats.lua', 'startup-format-logos.lua', 'quality_status.lua', 'window-size-position.lua']
    if simulated_hdr:
        excluded += ['display-info.dll', 'display-color.lua']
    config = create_config(name, exclude_scripts=excluded)
    p, probe = create_player(['--config-dir=' + str(config), '--ao=null', '--hwdec=no', '--pause=yes',
        '--geometry=' + size, '--autofit=' + size, '--autofit-smaller=' + size,
        '--osd-level=0', '--input-default-bindings=no', '--input-vo-keyboard=no', '--input-media-keys=no',
        '--image-display-duration=inf', '--loop-file=inf', str(media)], name,
        executable=os.environ.get('MPV_COLOR_TEST_EXE'))
    p.wait_video()
    if simulated_hdr:
        p.command('set_property', 'user-data/display-info', {'uid': 'output-fixture', 'hdr-status': 'on',
            'hdr-supported': True, 'max-luminance': 10000, 'min-luminance': .01, 'bit-depth': 10})
        wait(p, lambda s: s['mode'] == 'hdr-scrgb')
    else:
        wait(p, lambda s: s['mode'] in ('sdr-acm','sdr','icc'))
    return p, probe


def close(p, probe):
    probe.close()
    p.close()


def floating(frame):
    assert frame.meta['format'] == 10, frame.meta
    # 格式记录包括源平面与辅助资源，不冒充逐阶段主图像证明。
    assert any(t['format'] == 10 and t['bind'] & 32 for t in frame.meta['textures'])


def run_calibration():
    source,_ = hdr['fixture']('readback-source',[(.5,)*3]*16,'iec61966-2-1')
    shader = OUT/'readback-calibration.glsl'
    def write_shader(values):
        shader.write_text('//!HOOK OUTPUT\n//!BIND HOOKED\n//!DESC 维护读回标尺\n'
            'vec4 hook() { return vec4(%s, 1.0); }\n' % ', '.join(map(str, values)),
            encoding='utf-8', newline='\n')
    write_shader([.25,.5,.75])
    p,probe = create_player(['--no-config','--vo=gpu-next','--gpu-api=d3d11','--ao=null',
        '--geometry=256x256','--border=no','--osc=no','--osd-level=0','--pause=yes',
        '--target-trc=scrgb','--target-prim=bt.709','--d3d11-output-format=rgba16f',
        '--d3d11-output-csp=linear','--dither-depth=no','--loop-file=inf',
        '--glsl-shaders='+str(shader),str(source)],'output-calibration',
        executable=os.environ.get('MPV_COLOR_TEST_EXE'))
    rows=[]
    try:
        p.wait_video()
        for values in ([.25,.5,.75],[2.54,-.125,1.25]):
            p.command('set_property','glsl-shaders',[])
            shader = OUT/('readback-calibration-'+str(len(rows))+'.glsl')
            write_shader(values)
            p.command('set_property','glsl-shaders',[str(shader)])
            time.sleep(.2)
            frame=probe.read(p);floating(frame)
            observed=frame.pixel(frame.meta['width']//2,frame.meta['height']//2)[:3]
            assert max(abs(a-b) for a,b in zip(values,observed)) < .002,observed
            assert frame.meta['color_space']==1,frame.meta
            rows.append(dict(written=values,read=observed))
        return dict(test='原始FP16读回标尺及扩展值',trials=rows)
    finally:close(p,probe)


def run_sdr():
    source = png('gray', 1024, 64, lambda x, y: (round(x / 1023 * 65535),) * 3)
    p, probe = launch(source, 'output-sdr', size='1024x64')
    try:
        status = wait(p, lambda s: s['mode'] == 'sdr-acm')
        frame = probe.read(p)
        floating(frame)
        assert frame.meta['width'] == 1024, frame.meta
        observed = [frame.pixel(x, frame.meta['height']//2)[0] for x in range(1024)]
        expected = [sdr_linear(round(x / 1023 * 65535) / 65535) for x in range(1024)]
        errors = [abs(a - b) for a, b in zip(observed, expected)]
        assert max(errors) < .00125, max(errors)
        assert len(set(observed)) == 1024, len(set(observed))
        assert abs(observed[-1] - 1) < .001 and observed[0] < .0001
        assert not p.get('icc-profile-auto') and p.get('dither-depth') in ('no',False)
        return dict(test='实际SDR ACM参考白／1024灰阶', max_linear_error=max(errors), unique_levels=len(set(observed)),
                    native_mode=status['system_color']['mode'], output_format=frame.meta['format'])
    finally:
        close(p, probe)


def run_reference(name, colors, transfer):
    media, decoded = hdr['fixture'](name, colors, transfer)
    p, probe = launch(media, 'output-' + name, simulated_hdr=transfer != 'iec61966-2-1')
    try:
        if transfer == 'arib-std-b67':
            p.command('set_property', 'user-data/display-info', {'uid': 'output-fixture', 'hdr-status': 'on',
                'hdr-supported': True, 'max-luminance': 1000, 'min-luminance': .001, 'bit-depth': 10})
            wait(p, lambda s: s['mode'] == 'hdr-scrgb' and s['peak'] == 1000)
        if transfer != 'iec61966-2-1':
            # 本机是 SDR 桌面；屏蔽真实桌面目标提示，避免覆盖软件注入的 HDR 峰值。
            p.command('set_property','target-colorspace-hint',False)
            # scRGB 在 SDR 桌面会用参考白覆盖目标峰值；这里仅为模拟 HDR 数学隔离。
            p.command('set_property','hdr-reference-white',1000 if transfer=='arib-std-b67' else 10000)
            time.sleep(.3)
        frame = probe.read(p)
        floating(frame)
        assert (frame.meta['width'], frame.meta['height']) == (256,256)
        observed = [frame.pixel(i % 4 * 64 + 32, i // 4 * 64 + 32)[:3] for i in range(16)]
        expected = []
        for rgb in decoded:
            if transfer == 'smpte2084': values = [reference['pq_decode'](v) / 80 for v in rgb]
            elif transfer == 'arib-std-b67': values = [v / 80 for v in reference['hlg_reference'](rgb,1000)]
            else: values = [sdr_linear(v) for v in rgb]
            expected.append([sum(a*b for a,b in zip(row,values)) for row in hdr['MATRIX']])
        errors = [abs(a-b) for actual, ref in zip(observed,expected) for a,b in zip(actual,ref)]
        limits = [.00125 + .002 * abs(v) for rgb in expected for v in rgb]
        assert all(e <= limit for e,limit in zip(errors,limits)), dict(test=name, observed=observed,expected=expected,errors=errors)
        assert any(v < 0 for rgb in observed for v in rgb), '广色域负值被提前截断'
        return dict(test=name, max_linear_error=max(errors), max_error_nits=max(errors)*80,
                    observed=observed, expected=expected, target=p.get('video-target-params'),
                    scope='活动色彩逻辑、原始FP16交换链；HDR能力注入，并隔离SDR桌面提示／参考白覆盖；非真实HDR桌面')
    finally:
        close(p, probe)


def run_downscale():
    source = png('checker',1024,256,lambda x,y:(65535 if x % 2 else 0,)*3)
    p,probe = launch(source,'output-downscale',size='512x128')
    try:
        wait(p,lambda s:s['mode']=='sdr-acm')
        rows=[]
        for linear in (False,True):
            p.command('set_property','linear-downscaling',linear)
            time.sleep(.2)
            f=probe.read(p);floating(f)
            assert f.meta['width']==512, f.meta
            values=[f.pixel(x,f.meta['height']//2)[0] for x in range(64,448,8)]
            rows.append(dict(linear=linear,mean=sum(values)/len(values),error=max(abs(v-.5) for v in values)))
        assert rows[1]['error'] < .002 and rows[1]['error'] < rows[0]['error']/10,rows
        return dict(test='SDR线性缩小保持黑白平均亮度',trials=rows)
    finally:close(p,probe)


def main():
    rows=[run_calibration(),run_sdr()]
    print('PASS',rows[-1]['test'],flush=True)
    pq=[(reference['pq_encode'](v),)*3 for v in [0,.01,1,10,80,100,203,1000]]
    pq += [tuple(reference['pq_encode'](v) for v in rgb) for rgb in
           [(100,0,0),(0,100,0),(0,0,100),(203,100,80),(1000,203,100),(10,20,30),(80,80,80),(203,203,203)]]
    wide=[(v,)*3 for v in [0,.01,.05,.1,.25,.5,.75,1]]
    wide += [(1,0,0),(0,1,0),(0,0,1),(.75,.5,.25),(.5,.75,.25),(.25,.5,.75),(.5,.5,.5),(.75,.75,.75)]
    hlg=[(v,)*3 for v in [0,.01,.05,.1,.25,.5,.75,1]]
    hlg += [(.75,0,0),(0,.75,0),(0,0,.75),(.75,.5,.25),(.5,.75,.25),(.25,.5,.75),(.5,.5,.5),(.75,.75,.75)]
    for name,colors,trc in [('wide-sdr',wide,'iec61966-2-1'),('pq',pq,'smpte2084'),('hlg',hlg,'arib-std-b67')]:
        rows.append(run_reference(name,colors,trc));print('PASS',name,flush=True)
    rows.append(run_downscale());print('PASS',rows[-1]['test'],flush=True)
    (OUT/'results.json').write_text(json.dumps({'scope':'自有诊断进程的原始交换链GPU读回，非DWM／驱动输出或物理面板测量',
        'passed':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
