"""完整配置的 GPU 像素／实际滤镜回归；不要求专业测量设备。"""
import json
from pathlib import Path
import runpy
import struct
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/validation'
Player=runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
read_png=runpy.run_path(str(ROOT/'tools/validate-color-ramp.py'))['read_png']
reference=runpy.run_path(str(ROOT/'tools/test-color-precision.py'))['rgb_reference']
create_config=runpy.run_path(str(ROOT/'tools/isolated-config.py'))['create_config']
COLORS=[(.10,.10,.10),(.25,.25,.25),(.50,.50,.50),(.85,.85,.85),
        (.60,.45,.48),(.45,.60,.50),(.45,.50,.65),(.60,.55,.43),
        (.28,.30,.35),(.45,.35,.50),(.35,.45,.38),(.65,.65,.65),
        (.02,.02,.02),(.05,.05,.05),(.90,.90,.90),(.98,.98,.98)]


def decode_srgb(v):
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4


def encode_srgb(v):
    return v*12.92 if v<=.0031308 else 1.055*v**(1/2.4)-.055


def target_rgb(rgb,wide):
    if not wide:
        return rgb
    # 标准 D65 线性 BT.2020→BT.709；色块选在目标色域内，避免映射策略歧义。
    matrix=[[1.660491002108,-.587641138789,-.072849863319],
            [-.124550474522,1.132899897126,-.008349422604],
            [-.018150763355,-.100578898008,1.118729661363]]
    linear=list(map(decode_srgb,rgb))
    converted=[sum(a*b for a,b in zip(row,linear)) for row in matrix]
    assert all(0<=v<=1 for v in converted),converted
    return list(map(encode_srgb,converted))


def fixture(name,bits,matrix,full,wide,frames=48,transfer='iec61966-2-1'):
    w=h=256
    kr,kb={1:(.2126,.0722),6:(.299,.114),9:(.2627,.0593)}[matrix]
    scale=2**(bits-8)
    max_code=2**bits-1
    codes=[]
    for r,g,b in COLORS:
        y=kr*r+(1-kr-kb)*g+kb*b
        cb=(b-y)/(2-2*kb)
        cr=(r-y)/(2-2*kr)
        codes.append([round(y*(max_code if full else 219*scale)+(0 if full else 16*scale)),
                      round(cb*(max_code if full else 224*scale)+128*scale),
                      round(cr*(max_code if full else 224*scale)+128*scale)])
    raw=b''
    for plane in range(3):
        values=[codes[(y//64)*4+x//64][plane] for y in range(h) for x in range(w)]
        raw+=bytes(values) if bits==8 else struct.pack('<'+'H'*len(values),*values)
    raw_path=OUT/(name+'.yuv')
    raw_path.write_bytes(raw*frames)
    media=OUT/(name+'.mkv')
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y',
                    '-f','rawvideo','-pixel_format','yuv444p' if bits==8 else f'yuv444p{bits}le',
                    '-video_size','256x256','-framerate','24',
                    '-color_range','pc' if full else 'tv',
                    '-colorspace',{1:'bt709',6:'smpte170m',9:'bt2020nc'}[matrix],
                    '-color_primaries','bt2020' if wide else 'bt709',
                    '-color_trc',transfer,'-i',str(raw_path),
                    '-c:v','ffv1','-color_range','pc' if full else 'tv',
                    '-colorspace',{1:'bt709',6:'smpte170m',9:'bt2020nc'}[matrix],
                    '-color_primaries','bt2020' if wide else 'bt709',
                    '-color_trc',transfer,str(media)],check=True,timeout=20)
    # 回读同范围的实际编码样本；避免夹具生成时先改范围而误归因于播放器。
    decoded=subprocess.check_output([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error',
        '-i',str(media),'-frames:v','1','-color_range','pc' if full else 'tv',
        '-pix_fmt','yuv444p' if bits==8 else f'yuv444p{bits}le','-f','rawvideo','-'],timeout=20)
    assert decoded==raw,'夹具编码／回读改变了样本'
    expected=[target_rgb(reference(c,bits,matrix,full),wide) for c in codes]
    return media,expected


def wait_added(p,group,preset):
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
        s=p.get('user-data/quality')
        if s and s['state']=='失败':
            raise AssertionError(s['error'])
        if s and s['state']=='已添加' and isinstance(s.get('active'),dict) and s['active'].get(group)==preset:
            return s
        time.sleep(.1)
    raise AssertionError('实际滤镜初始化未完成')


def capture(p,name,expected):
    path=OUT/(name+'.png')
    assert p.command('screenshot-to-file',str(path),'video')['error']=='success'
    w,h,channels,rows=read_png(path)
    assert (w,h)==(256,256),(w,h)
    errors=[]
    for i,rgb in enumerate(expected):
        x=(i%4)*64+32
        y=(i//4)*64+32
        errors.extend(abs(rows[y][x*channels+c]-round(rgb[c]*65535)) for c in range(3))
    return max(errors)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # 固定经典 SDR 路线，ACM 浮点路线另由原始 GPU 读回工具覆盖。
    config=create_config('color-config',exclude_scripts=['display-color.lua'])
    results=[]
    cases=[('full-601-8',8,6,True,False),('limited-709-10',10,1,False,False),
           ('full-709-16',16,1,True,False),('limited-2020-10',10,9,False,True),
           ('full-2020-16',16,9,True,True)]
    for name,bits,matrix,full,wide in cases:
        media,expected=fixture('color-config-'+name,bits,matrix,full,wide)
        p=Player(['--config-dir='+str(config),'--ao=null','--hwdec=no',
                  '--input-cursor=no','--input-vo-keyboard=no','--input-media-keys=no','--terminal=no',
                  '--geometry=512x512','--screenshot-sw=no','--screenshot-high-bit-depth=yes',
                  '--screenshot-format=png','--loop-file=inf',str(media)],'color-config-'+name)
        try:
            p.wait_video()
            time.sleep(.5)
            assert p.get('glsl-shaders')==[],'基线不应恢复临时Shader'
            assert p.get('target-trc')=='srgb' and p.get('target-prim')=='bt.709'
            assert p.get('hdr-contrast-recovery')==0
            baseline=capture(p,'color-config-'+name+'-baseline',expected)
            assert baseline<=128,(name,'baseline',baseline)
            p.command('script-message','quality-select','ccd')
            wait_added(p,'denoise','ccd')
            time.sleep(.3)
            ccd=capture(p,'color-config-'+name+'-ccd',expected)
            assert ccd<=128,(name,'ccd',ccd)
            if bits==16:
                assert '16' in p.get('video-params')['pixelformat'],p.get('video-params')
            row=dict(source=name,bits=bits,matrix=matrix,full=full,wide=wide,
                     baseline_maximum_code_error=baseline,ccd_maximum_code_error=ccd,
                     output_format=p.get('video-params')['pixelformat'],passed=True)
            if name=='full-2020-16':
                p.command('script-message','quality-select','rife-dml-426')
                wait_added(p,'memc','rife-dml-426')
                time.sleep(.3)
                row['combination_maximum_code_error']=capture(p,'color-config-'+name+'-ccd-rife',expected)
                assert row['combination_maximum_code_error']<=128,row
                assert '16' in p.get('video-params')['pixelformat']
                assert p.get('user-data/quality')['active']['denoise']=='ccd'
                assert p.get('user-data/quality')['active']['memc']=='rife-dml-426'
                # 短片反复重建模型有初始化开销，先单独验证 EOF／循环不撤链。
                time.sleep(5)
                assert p.get('user-data/quality')['active']['memc']=='rife-dml-426'
                row['short_loop_passed']=True
                long_media,_=fixture('color-config-full-2020-16-long',bits,matrix,full,wide,frames=960)
                p.command('loadfile',str(long_media))
                p.wait_video()
                p.command('script-message','quality-select','ccd')
                wait_added(p,'denoise','ccd')
                p.command('script-message','quality-select','rife-dml-426')
                wait_added(p,'memc','rife-dml-426')
                time.sleep(2)
                # 长素材初始化后再采样正常时钟，不能将循环的加载间隔混入稳态。
                start=time.monotonic()
                last=p.get('time-pos')
                duration=p.get('duration')
                advance=0
                loops=0
                drops=p.get('frame-drop-count')
                decoder_drops=p.get('decoder-frame-drop-count')
                while time.monotonic()-start<20:
                    time.sleep(.1)
                    now=p.get('time-pos')
                    delta=now-last
                    if delta<-.5:
                        delta+=duration
                        loops+=1
                    advance+=max(0,delta)
                    last=now
                    assert p.get('user-data/quality')['state']=='已添加'
                row['steady_seconds']=time.monotonic()-start
                row['loop_count']=loops
                row['clock_ratio']=advance/row['steady_seconds']
                row['display_drops']=p.get('frame-drop-count')-drops
                row['decoder_drops']=p.get('decoder-frame-drop-count')-decoder_drops
                assert .97<row['clock_ratio']<1.03 and loops==0,row
                p.command('seek',.5,'absolute+exact')
                time.sleep(.5)
                assert p.get('user-data/quality')['active']['memc']=='rife-dml-426'
            results.append(row)
        finally:
            p.close()
        log=p.log.read_text(encoding='utf-8',errors='replace')
        assert 'Lua error:' not in log and 'Script evaluation failed' not in log
        assert 'No PTS after filter' not in log
        assert 'quality/probe.py' not in log and 'quality/discovery.py' not in log
        print('PASS',name,'基线',baseline,'CCD',ccd)
    (OUT/'color-config-results.json').write_text(json.dumps(dict(
        scope='完整配置、GPU高位深截图与静态色块真实滤镜；非面板测量',trials=results),
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    main()
