"""通用色域验收夹具：RGB网格、HSV网格、连续灰阶与近中性色，原始整数可核对。"""
import array, colorsys, hashlib, json, math, struct, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/gamut-general-20261012'
OUT.mkdir(parents=True,exist_ok=True)
TILE=16;COLS=48


def colors():
    result=[]
    def add(rgb,kind):result.append(dict(rgb=list(rgb),kind=kind))
    for i in range(257):add((i/256,)*3,'gray')
    for v in (.01,.03,.1,.25,.5,.75,.98):
        for delta in (-.002,-.0005,.0005,.002):
            for channel in range(3):
                rgb=[v]*3;rgb[channel]+=delta;add(rgb,'near-gray')
    for v in (.03,.1,.4,1):
        for saturation in (.1,.25,.5,.75,.95,1):
            for hue in range(24):add(colorsys.hsv_to_rgb(hue/24,saturation,v),'hsv')
    for a in range(9):
        for b in range(9):
            for c in range(9):add((a/8,b/8,c/8),'rgb-grid')
    return result


def fixture(transfer='iec61966-2-1',matrix=9,frames=48):
    samples=colors();w=COLS*TILE;h=math.ceil(len(samples)/COLS)*TILE
    padded=samples+[dict(rgb=[0,0,0],kind='padding')]*(w*h//(TILE*TILE)-len(samples))
    name=f'grid-{matrix}-{transfer}';path=OUT/(name+'.mkv');raw_path=OUT/(name+'.yuv')
    kr,kb=(.2627,.0593) if matrix==9 else (.2126,.0722)
    codes=[];decoded=[]
    for item in padded:
        red,green,blue=item['rgb'];y=kr*red+(1-kr-kb)*green+kb*blue
        cb=(blue-y)/(2-2*kb);cr=(red-y)/(2-2*kr)
        code=[min(65535,max(0,round(v))) for v in (y*65535,cb*65535+32768,cr*65535+32768)]
        codes.append(code);y=code[0]/65535;cb=(code[1]-32768)/65535;cr=(code[2]-32768)/65535
        red=y+(2-2*kr)*cr;blue=y+(2-2*kb)*cb;green=(y-kr*red-kb*blue)/(1-kr-kb)
        decoded.append([red,green,blue])
    raw=b''
    for plane in range(3):
        for line in range(h//TILE):
            row=b''.join(struct.pack('<H',codes[line*COLS+column][plane])*TILE for column in range(COLS))
            raw+=row*TILE
    raw_path.write_bytes(raw)
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y',
        '-stream_loop','-1','-f','rawvideo','-pixel_format','yuv444p16le','-video_size',f'{w}x{h}',
        '-framerate','24','-color_range','pc','-colorspace','bt2020nc' if matrix==9 else 'bt709',
        '-color_primaries','bt2020' if matrix==9 else 'bt709','-color_trc',transfer,'-i',str(raw_path),
        '-frames:v',str(frames),'-c:v','ffv1','-threads','1','-level','3','-slices','16',
        '-pix_fmt','yuv444p16le','-color_range','pc','-colorspace','bt2020nc' if matrix==9 else 'bt709',
        '-color_primaries','bt2020' if matrix==9 else 'bt709','-color_trc',transfer,
        str(path)],check=True,timeout=90)
    verify=subprocess.check_output([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-threads','1',
        '-i',str(path),'-frames:v','1','-pix_fmt','yuv444p16le','-f','rawvideo','-'],timeout=20)
    assert verify==raw
    return dict(path=path,raw=raw,width=w,height=h,decoded=decoded[:len(samples)],samples=samples,
        source_sha256=hashlib.sha256(raw).hexdigest(),tile=TILE,columns=COLS)


if __name__=='__main__':
    f=fixture();print(len(f['samples']),f['width'],f['height'],f['source_sha256'])
