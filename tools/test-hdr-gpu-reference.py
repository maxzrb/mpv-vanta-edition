"""维护者手动独立参考：GPU HDR 输出正负分离编码到16bit PNG，非原始FP16或面板回读。"""
import json
from pathlib import Path
import runpy
import struct
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/hdr-gpu-reference'
Player=runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
read_png=runpy.run_path(str(ROOT/'tools/validate-color-ramp.py'))['read_png']
refs=runpy.run_path(str(ROOT/'tools/color-reference.py'))
pq_encode,pq_decode,hlg_reference=refs['pq_encode'],refs['pq_decode'],refs['hlg_reference']
MATRIX=[[1.660491002108,-.587641138789,-.072849863319],
        [-.124550474522,1.132899897126,-.008349422604],
        [-.018150763355,-.100578898008,1.118729661363]]


def fixture(name,colors,transfer):
    bits=16;maximum=65535;scale=256
    codes=[]
    for r,g,b in colors:
        y=.2627*r+.6780*g+.0593*b
        cb=(b-y)/(2-2*.0593);cr=(r-y)/(2-2*.2627)
        codes.append([round(y*219*scale+16*scale),round(cb*224*scale+128*scale),
                      round(cr*224*scale+128*scale)])
    raw=b''
    for plane in range(3):
        values=[codes[(y//64)*4+x//64][plane] for y in range(256) for x in range(256)]
        assert all(0<=value<=maximum for value in values)
        raw+=struct.pack('<'+'H'*len(values),*values)
    input_file=OUT/(name+'.yuv');input_file.write_bytes(raw*48)
    media=OUT/(name+'.mkv')
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y',
        '-f','rawvideo','-pixel_format','yuv444p16le','-video_size','256x256','-framerate','24',
        '-color_range','tv','-colorspace','bt2020nc','-color_primaries','bt2020','-color_trc',transfer,
        '-i',str(input_file),'-c:v','ffv1','-color_range','tv','-colorspace','bt2020nc',
        '-color_primaries','bt2020','-color_trc',transfer,str(media)],check=True,timeout=20)
    actual=subprocess.check_output([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error',
        '-i',str(media),'-frames:v','1','-pix_fmt','yuv444p16le','-f','rawvideo','-'],timeout=20)
    assert actual==raw,'夹具回读与原始样本不同'
    decoded=[]
    for y,cb,cr in codes:
        y=(y-16*scale)/(219*scale);cb=(cb-128*scale)/(224*scale);cr=(cr-128*scale)/(224*scale)
        r=y+(2-2*.2627)*cr;b=y+(2-2*.0593)*cb
        g=(y-.2627*r-.0593*b)/.6780
        decoded.append([max(0,min(1,v)) for v in [r,g,b]])
    return media,decoded


def screenshot(p,name):
    path=OUT/(name+'.png')
    assert p.command('screenshot-to-file',str(path),'window')['error']=='success'
    w,h,channels,rows=read_png(path)
    assert (w,h)==(256,256),(w,h)
    return [[rows[(i//4)*64+32][((i%4)*64+32)*channels+c]/65535 for c in range(3)]
            for i in range(16)]


def run(name,colors,transfer):
    media,decoded=fixture(name,colors,transfer)
    measurements=[]
    for polarity in [1,-1]:
        shader=OUT/('measurement-'+str(polarity)+'.glsl')
        shader.write_text('''//!HOOK OUTPUT
//!BIND HOOKED
//!DESC 维护测试：正负输出分别编码，避免固定偏移吞掉暗部精度
vec4 hook() { return vec4(max(HOOKED_tex(HOOKED_pos).rgb * %s, vec3(0.0)) / 32.0, 1.0); }
''' % str(float(polarity)),encoding='utf-8',newline='\n')
        measurements.append(shader)
    calibration=OUT/'calibration.glsl'
    calibration.write_text('''//!HOOK OUTPUT
//!BIND HOOKED
//!DESC 维护测试：读回标尺校验
vec4 hook() { return vec4(0.25, 0.5, 0.75, 1.0); }
''',encoding='utf-8',newline='\n')
    p=Player(['--no-config','--vo=gpu-next','--gpu-api=d3d11','--hwdec=no','--ao=null',
        '--pause=yes','--geometry=256x256','--border=no','--osc=no','--osd-level=0',
        '--input-cursor=no','--input-vo-keyboard=no','--input-media-keys=no',
        '--target-prim=bt.709','--target-trc=scrgb','--target-gamut=bt.2020',
        '--target-peak='+('10000' if transfer=='smpte2084' else '1000'),
        '--target-contrast=inf','--target-colorspace-hint=no',
        '--d3d11-output-format=rgba16f','--d3d11-output-csp=linear',
        '--tone-mapping=clip','--gamut-mapping-mode=clip','--hdr-compute-peak=no',
        '--hdr-contrast-recovery=0','--inverse-tone-mapping=no','--deband=no','--dither=no',
        '--screenshot-sw=no','--screenshot-format=png','--screenshot-high-bit-depth=yes',
        '--glsl-shaders='+str(calibration),str(media)],'hdr-reference-'+name)
    try:
        p.wait_video();time.sleep(.5)
        calibrated=screenshot(p,name+'-calibration')
        assert max(abs(a-b) for rgb in calibrated for a,b in zip(rgb,[.25,.5,.75]))<2/65535,'读回标尺被转换'
        # 改动只在测试进程，生产配置无测量 Shader。
        readings=[]
        for index,measurement in enumerate(measurements):
            p.command('set_property','glsl-shaders',[str(measurement)])
            time.sleep(.5)
            readings.append(screenshot(p,name+'-measured-'+str(index)))
        observed=[[(positive-negative)*32*80 for positive,negative in zip(a,b)]
                  for a,b in zip(*readings)]
        expected=[]
        for rgb in decoded:
            nits=[pq_decode(v) for v in rgb] if transfer=='smpte2084' else hlg_reference(rgb,1000)
            expected.append([sum(a*b for a,b in zip(row,nits)) for row in MATRIX])
        errors=[abs(a-b) for actual,reference in zip(observed,expected) for a,b in zip(actual,reference)]
        # 包含 FP16 工作纹理、正负编码及16bit整数读回的误差，阈值不依观测放宽。
        tolerance=[.10+.002*abs(v) for rgb in expected for v in rgb]
        assert all(error<=limit for error,limit in zip(errors,tolerance)),dict(
            name=name,observed=observed,expected=expected,errors=errors)
        row=dict(source=name,source_params=p.get('video-params'),target=p.get('video-target-params'),
                 expected_linear709_nits=expected,observed_linear709_nits=observed,
                 max_absolute_error_nits=max(errors),passed=True)
        assert any(v<-.2 for rgb in expected for v in rgb),'色块未覆盖负值'
        assert any(v>80 for rgb in expected for v in rgb),'色块未覆盖scRGB超过1'
    finally:p.close()
    print('PASS',name,'独立HDR GPU参考，最大亮度误差',row['max_absolute_error_nits'],flush=True)
    return row


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pq=[tuple([pq_encode(v)]*3) for v in [0,.1,1,10,80,100,203,1000]]
    pq += [tuple(pq_encode(v) for v in rgb) for rgb in
           [(100,0,0),(0,100,0),(0,0,100),(203,100,80),(1000,203,100),(10,20,30),(80,80,80),(203,203,203)]]
    hlg=[tuple([v]*3) for v in [0,.1,.25,.5,.75,.9,1,.6]]
    hlg += [(0.75,0.25,0.25),(0.25,0.75,0.25),(0.25,0.25,0.75),
            (.9,.5,.25),(.5,.9,.25),(.25,.5,.9),(.6,.6,.6),(.75,.75,.75)]
    rows=[run('pq',pq,'smpte2084'),run('hlg',hlg,'arib-std-b67')]
    (OUT/'results.json').write_text(json.dumps(dict(
        scope='受控GPU HDR转换，正负分离16bitPNG读回；非原始FP16／物理面板／默认色调映射验收',
        trials=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
