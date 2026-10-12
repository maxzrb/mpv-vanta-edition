"""当前配置的源平面、实际中间写回及交换链数值闭环验证。"""
import json,runpy,struct,time,os
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('MPV_PIPELINE_OUT',str(ROOT/'tmp/modernization/pipeline-validation-20261011')))
OUT.mkdir(parents=True,exist_ok=True)
pipeline=runpy.run_path(str(ROOT/'tools/gpu-pipeline-readback.py'))
output=runpy.run_path(str(ROOT/'tools/test-color-output.py'))
fixtures=runpy.run_path(str(ROOT/'tools/test-color-config.py'))
fixtures['fixture'].__globals__['OUT']=OUT
Frame=runpy.run_path(str(ROOT/'tools/gpu-readback.py'))['Frame']
COLOR_SCRIPTS={'color-target.lua','hdr-mode.lua','quality.lua','hwdec-select.lua','decode-performance.lua','dynamic-crop.lua','fix-avsync.lua'}
EXCLUDED=[p.name for p in (ROOT/'portable_config/scripts').iterdir() if p.name not in COLOR_SCRIPTS]
CONFIGS={}


def capture(media,name,backend,size='256x256',hdr_transfer=None,seek_time=None,mode='wcg',icc_profile=None,extra_args=None,force_redraw=False,post_configure=None):
    if backend not in CONFIGS:
        CONFIGS[backend]=output['create_config']('pipeline-'+backend,exclude_scripts=EXCLUDED)
        if os.environ.get('MPV_PIPELINE_BASELINE'):
            shutil.copyfile(OUT/'color-target-before-closed-loop.lua',CONFIGS[backend]/'scripts/color-target.lua')
    cfg=CONFIGS[backend]
    args=['--config-dir='+str(cfg),'--gpu-api='+backend,'--hwdec=no',
        '--pause=yes','--ao=null','--script-opts-append=color-target-pipeline=hq','--sid=no','--osd-level=0','--osd-bar=no','--osd-on-seek=no','--osc=no','--gpu-shader-cache=no',
        '--geometry='+size,'--autofit='+size,'--autofit-smaller='+size,'--loop-file=inf',str(media)]
    if os.environ.get('MPV_PIPELINE_NATIVE_RANGE'):
        args.extend(['--vf=format=fmt=yuv444p16:colorlevels=limited:convert=yes:force-scaler=zimg','--zimg-threads=1'])
    elif os.environ.get('MPV_PIPELINE_RANGE_NORMALIZE'):
        args.append('--vf=lavfi=[zscale=rangein=full:range=limited,format=yuv444p16le]:o=[threads=1]')
    args.extend(extra_args or [])
    p,probe=pipeline['create_player'](args,
        'pipeline-'+name+'-'+backend,backend)
    try:
        p.wait_video()
        # 软件场景固定在配置识别入口，不依赖诊断窗口被放到哪块显示器。
        peak=1000 if hdr_transfer=='arib-std-b67' else 10000 if hdr_transfer else 80
        p.command('set_property','user-data/display-info',{'uid':'pipeline-software','hdr-status':'on' if hdr_transfer else 'off','hdr-supported':bool(hdr_transfer),'max-luminance':peak,'min-luminance':0})
        p.command('set_property','user-data/display-color',{'mode':'sdr' if mode=='icc' else mode,'identity':'pipeline-software','sdr_white_nits':80})
        if mode=='icc':
            assert icc_profile is not None
            p.command('script-message','color-icc',str(icc_profile))
        p.command('set_property','pause',False)
        wanted='hdr-scrgb' if hdr_transfer and backend=='d3d11' else 'sdr-acm' if mode=='wcg' else 'icc' if mode=='icc' else 'sdr'
        status=output['wait'](p,lambda s:s['mode']==wanted)
        if hdr_transfer:
            if backend=='vulkan':
                # 当前管理器的 HDR 路线只启用 D3D11；这里单独验证核心 HDR 数学。
                p.command('set_property','target-peak',peak)
            p.command('set_property','target-colorspace-hint',False)
            p.command('set_property','hdr-reference-white',peak)
        if os.environ.get('MPV_PIPELINE_FORCE_SOURCE_GAMUT'):
            p.command('set_property','target-gamut',p.get('video-params')['primaries'])
        if post_configure:
            post_configure(p)
        p.command('set_property','pause',True)
        if seek_time is not None:
            p.command('seek',seek_time,'absolute+exact')
            deadline=time.monotonic()+60
            while p.get('seeking') or abs((p.get('time-pos') or 0)-seek_time)>.05:
                if time.monotonic()>deadline:raise AssertionError('诊断帧定位未完成')
                time.sleep(.1)
        time.sleep(.5)
        rows=probe.read(p,force_redraw=force_redraw)
        present=next(m for m,b in rows if m['phase']=='present')
        expected_space=1 if backend=='d3d11' and present['format']==10 else 1000104002 if backend=='vulkan' and present['format']==10 else 0
        assert present['color_space']==expected_space,('像素格式与提交色彩空间不匹配',present)
        status['validation_source']=p.get('video-params')
        status['validation_filtered']=p.get('video-out-params')
        status['validation_range_fix']=p.get('user-data/color-range-fix')
        status['validation_hwdec']=p.get('hwdec-current')
        status['actual_target']=p.get('video-target-params')
        manifest=probe.script.exports_sync.status()
        if backend=='vulkan':
            # 整数统计变量的 RelaxedPrecision 不等于浮点色彩计算降精度；逐项按类型核对。
            assert manifest['shader_types'] and all(s['float_widths']==[32] and s['relaxed_float_decorations']==0 and s['relaxed_unknown_decorations']==0 for s in manifest['shader_types']),manifest
        else:
            shaders=[m for m,b in rows if m.get('shader')]
            assert shaders and all(m.get('shader_ir') and 'min16' not in m['shader_ir'] for m in shaders),'缺少实际编译 Shader 的精度证明'
        (OUT/(name+'-'+backend+'-manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
        (OUT/(name+'-'+backend+'-graph.json')).write_text(json.dumps([m for m,b in rows],ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
        return rows,status
    finally:p.close();probe.close()


def pixel(row,x,y):
    m,b=row
    if m['format'] in (10,24,28,87):return Frame(m,b).pixel(x,y)[:3]
    if m['format']==11:return tuple(v/65535 for v in struct.unpack_from('<4H',b,y*m['stride']+x*8)[:3])
    return struct.unpack_from('<H' if m['format']==56 else '<B',b,y*m['stride']+x*m['bytes_per_pixel'])[0]


def check_case(bits,matrix,full,backend):
    name=f'{bits}-{matrix}-{int(full)}'
    media,encoded=fixtures['fixture'](name,bits,matrix,full,matrix==9)
    expected=[[output['sdr_linear'](v) for v in rgb] for rgb in encoded]
    rows,status=capture(media,name,backend)
    sources=[r for r in rows if r[0]['phase']=='input' and r[0]['format'] in (56,61) and r[0]['width']==256 and r[0]['height']==256]
    assert len(sources)==3,[(m['phase'],m['format']) for m,b in rows]
    raw=(OUT/(name+'.yuv')).read_bytes()
    sample_size=1 if bits==8 else 2
    source_errors=[]
    for plane,row in enumerate(sources):
        m,b=row
        visible=b''.join(b[y*m['stride']:y*m['stride']+256*sample_size] for y in range(256))
        assert visible==raw[plane*65536*sample_size:(plane+1)*65536*sample_size],'GPU 源平面整帧与解码整数样本不同'
        for i in range(16):
            x=i%4*64+32;y=i//4*64+32
            offset=(plane*65536+y*256+x)*sample_size
            code=raw[offset] if bits==8 else struct.unpack_from('<H',raw,offset)[0]
            source_errors.append(abs(pixel(row,x,y)-code))
    assert max(source_errors)==0,(name,backend,max(source_errors))
    stages=[r for r in rows if r[0]['phase'] in ('output','present')]
    # 同尺寸输入无空间滤波；整帧逐像素都须等于所在色块的数值。
    m,b=stages[0]
    for i in range(16):
        x0=i%4*64;y0=i//4*64
        center=b[(y0+32)*m['stride']+(x0+32)*8:(y0+32)*m['stride']+(x0+32)*8+6]
        assert all(b[y*m['stride']+x*8:y*m['stride']+x*8+6]==center for y in range(y0,y0+64) for x in range(x0,x0+64)),'无缩放色块内出现额外变动'
    errors=[]
    for row in stages:
        assert row[0]['format']==10,row[0]
        actual=[pixel(row,i%4*64+32,i//4*64+32) for i in range(16)]
        error=[abs(a-b) for rgb,ref in zip(actual,expected) for a,b in zip(rgb,ref)]
        errors.append(max(error))
    # 第二次绘制为同尺寸复制；比较全部可见像素而非只比色块中心。
    def packed(row):
        m,b=row;return b''.join(b[y*m['stride']+x*8:y*m['stride']+x*8+6] for y in range(m['height']) for x in range(m['width']))
    assert len(stages)>=3,len(stages)
    if not all(packed(row)==packed(stages[0]) for row in stages[1:]):
        differences=[]
        for row in stages[1:]:
            d=[(x,y,max(abs(a-b) for a,b in zip(pixel(row,x,y),pixel(stages[0],x,y)))) for y in range(256) for x in range(256)]
            differences.append((row[0]['sequence'],max(d,key=lambda t:t[2]),sum(t[2]!=0 for t in d)))
        raise AssertionError(('复制或呈现额外改变 RGB 像素',differences))
    return dict(case=name,backend=backend,source_max_code_error=max(source_errors),stage_max_linear_errors=errors,
                stages=len(stages),copy_all_pixels_exact=True,mode=status['mode'],reference_passed=max(errors)<.00125,
                gray_max_channel_spread=max(max(pixel(stages[0],i%4*64+32,i//4*64+32))-min(pixel(stages[0],i%4*64+32,i//4*64+32)) for i in (0,1,2,3,11,12,13,14,15)))


def main():
    results=[]
    for bits in (8,10,12,16):
        for matrix in (6,1,9):
            for full in (False,True):
                for backend in ('d3d11','vulkan'):
                    row=check_case(bits,matrix,full,backend);results.append(row)
                    print('PASS' if row['reference_passed'] else 'FAIL REFERENCE',row['case'],backend,max(row['stage_max_linear_errors']),flush=True)
    (OUT/'pipeline-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    # 独立参考失败时保留完整结果，同时让自动验收明确失败。
    if not all(row['reference_passed'] for row in results):
        raise SystemExit(1)


if __name__=='__main__':main()
