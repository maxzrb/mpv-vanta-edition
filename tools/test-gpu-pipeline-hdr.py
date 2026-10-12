"""逐阶段灰阶、广色域、HDR 数学与线性缩小独立参考。"""
import json,runpy,math,struct,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
test=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'))
OUT=test['OUT'];pixel=test['pixel'];capture=test['capture'];output=test['output']
hdr=output['hdr'];hdr['fixture'].__globals__['OUT']=OUT
ref=output['reference']


def stages(rows):return [r for r in rows if r[0]['phase'] in ('output','present')]


def reference_case(backend,kind):
    if kind=='pq':
        colors=[(ref['pq_encode'](v),)*3 for v in [0,.01,1,10,80,100,203,1000]]
        colors += [tuple(ref['pq_encode'](v) for v in rgb) for rgb in [(100,0,0),(0,100,0),(0,0,100),(1000,1000,1000),(4000,4000,4000),(10000,10000,10000),(80,203,1000),(10,20,30)]]
        transfer='smpte2084'
    else:
        colors=[(v,)*3 for v in [0,.01,.05,.1,.25,.5,.75,1]]+[(.75,0,0),(0,.75,0),(0,0,.75),(.75,.5,.25),(.5,.75,.25),(.25,.5,.75),(.5,.5,.5),(.75,.75,.75)]
        transfer='arib-std-b67' if kind=='hlg' else 'iec61966-2-1'
    media,decoded=hdr['fixture']('stage-'+kind,colors,transfer)
    expected=[]
    for rgb in decoded:
        if kind=='pq':linear=[ref['pq_decode'](v)/80 for v in rgb]
        elif kind=='hlg':linear=[v/80 for v in ref['hlg_reference'](rgb,1000)]
        else:linear=[output['sdr_linear'](v) for v in rgb]
        expected.append([sum(a*b for a,b in zip(row,linear)) for row in hdr['MATRIX']])
    rows,status=capture(media,'stage-'+kind,backend,hdr_transfer=transfer if kind!='wide' else None)
    errors=[];values=[]
    for row in stages(rows):
        assert row[0]['format']==10,row[0]
        actual=[pixel(row,i%4*64+32,i//4*64+32) for i in range(16)]
        differences=[abs(a-b) for rgb,target in zip(actual,expected) for a,b in zip(rgb,target)]
        limits=[.00125+.002*abs(v) for rgb in expected for v in rgb]
        assert all(e<=limit for e,limit in zip(differences,limits)),(kind,backend,actual,expected,differences)
        errors.append(max(differences));values.append(actual)
    assert any(v<0 for rgb in values[-1] for v in rgb),'广色域负分量被截断'
    assert values[0]==values[-1],'中间至交换链额外改变色块'
    return dict(test=kind,backend=backend,stage_max_errors=errors,expected=expected,observed=values[-1],negative_preserved=True,
                high_value_preserved=max(v for rgb in values[-1] for v in rgb)>1 if kind!='wide' else None,software_mode=status['mode'])


def gray_case(backend):
    media=output['png']('stage-gray',1024,64,lambda x,y:(round(x/1023*65535),)*3)
    rows,status=capture(media,'stage-gray',backend,size='1024x64')
    expected=[output['sdr_linear'](round(x/1023*65535)/65535) for x in range(1024)]
    errors=[]
    for row in stages(rows):
        if row[0]['format']==11:
            actual=[pixel(row,x,32)[0] for x in range(1024)]
            assert actual==[round(x/1023*65535)/65535 for x in range(1024)],'上传重排丢失 RGB16 源精度'
            continue
        assert row[0]['format']==10
        actual=[pixel(row,x,32)[0] for x in range(1024)]
        assert len(set(actual))==1024
        error=max(abs(a-b) for a,b in zip(actual,expected));assert error<.00125,error
        errors.append(error)
    return dict(test='1024-gray',backend=backend,stage_max_errors=errors,unique_levels=1024)


def scale_case(backend):
    media=output['png']('stage-checker',1024,256,lambda x,y:(65535 if x%2 else 0,)*3)
    rows,status=capture(media,'stage-checker',backend,size='512x128')
    final=stages(rows)[-1]
    values=[pixel(final,x,64)[0] for x in range(64,448)]
    assert max(abs(v-.5) for v in values)<.002,values[:8]
    return dict(test='linear-downscale',backend=backend,maximum_error=max(abs(v-.5) for v in values),
                graph=[{'phase':m['phase'],'format':m['format'],'size':[m['width'],m['height']]} for m,b in rows])


def dense_gray_case(backend):
    media=output['png']('stage-gray16-all',512,128,lambda x,y:(y*512+x,)*3)
    rows,status=capture(media,'stage-gray16-all',backend,size='512x128')
    errors=[];lightness_errors=[];unique=[]
    def lightness(v):return 116*v**(1/3)-16 if v>216/24389 else 24389/27*v
    for row in stages(rows):
        values=[pixel(row,x,y)[0] for y in range(128) for x in range(512)]
        if row[0]['format']==11:
            assert values==[i/65535 for i in range(65536)],'RGB16 全码阶上传丢码'
            continue
        expected=[output['sdr_linear'](i/65535) for i in range(65536)]
        error=max(abs(a-b) for a,b in zip(values,expected))
        de=max(abs(lightness(a)-lightness(b)) for a,b in zip(values,expected));assert de<.1,de
        errors.append(error);lightness_errors.append(de);unique.append(len(set(values)))
    return dict(test='65536-gray',backend=backend,stage_max_errors=errors,stage_max_delta_L=lightness_errors,stage_unique_linear_levels=unique,
                source_16bit_all_codes_exact=True,reference_passed=max(errors)<.00125)


def hdr_709_case():
    media,decoded=test['fixtures']['fixture']('stage-pq709',16,1,False,False,transfer='smpte2084')
    rows,status=capture(media,'stage-pq709','d3d11',hdr_transfer='smpte2084')
    expected=[[ref['pq_decode'](v)/80 for v in rgb] for rgb in decoded]
    errors=[]
    for row in stages(rows):
        actual=[pixel(row,i%4*64+32,i//4*64+32) for i in range(16)]
        diff=[abs(a-b) for rgb,target in zip(actual,expected) for a,b in zip(rgb,target)]
        limits=[.00125+.002*abs(v) for rgb in expected for v in rgb]
        assert all(e<=limit for e,limit in zip(diff,limits)),(actual,expected,diff)
        errors.append(max(diff))
    return dict(test='pq-bt709',backend='d3d11',stage_max_errors=errors,source_gamut='bt.709')


def rgb_case(backend):
    colors=test['fixtures']['COLORS']
    media=output['png']('stage-rgb16',256,256,lambda x,y:tuple(round(v*65535) for v in colors[y//64*4+x//64]))
    rows,status=capture(media,'stage-rgb16',backend)
    expected=[[output['sdr_linear'](round(v*65535)/65535) for v in rgb] for rgb in colors]
    errors=[];checked=False
    for row in stages(rows):
        actual=[pixel(row,i%4*64+32,i//4*64+32) for i in range(16)]
        if row[0]['format']==11:
            assert actual==[tuple(round(v*65535)/65535 for v in rgb) for rgb in colors]
            checked=True;continue
        diff=max(abs(a-b) for rgb,target in zip(actual,expected) for a,b in zip(rgb,target));assert diff<.00125,diff
        errors.append(diff)
    assert checked,'未捕获真实 RGB16 上传重排'
    return dict(test='rgb16-colors',backend=backend,source_rgb_channels_exact=True,stage_max_errors=errors)


def video_gray12_case(backend):
    count=3505;w,h=512,128
    luma=[min(i,count-1)+256 for i in range(w*h)]
    raw=struct.pack('<'+'H'*(w*h),*luma)+struct.pack('<H',2048)*(w*h*2)
    raw_path=OUT/'gray12-tv.yuv';raw_path.write_bytes(raw*48)
    media=OUT/'gray12-tv.mkv'
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y','-f','rawvideo',
        '-pixel_format','yuv444p12le','-video_size','512x128','-framerate','24','-color_range','tv',
        '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-i',str(raw_path),'-c:v','ffv1',str(media)],check=True,timeout=20)
    rows,status=capture(media,'video-gray12',backend,size='512x128')
    sources=[r for r in rows if r[0]['phase']=='input' and r[0]['format']==56]
    assert len(sources)==3
    for plane,(m,b) in enumerate(sources):
        visible=b''.join(b[y*m['stride']:y*m['stride']+w*2] for y in range(h))
        assert visible==raw[plane*w*h*2:(plane+1)*w*h*2]
    values=[pixel(rows[-1],i%512,i//512)[0] for i in range(count)]
    expected=[(i/3504)**2.4 for i in range(count)]
    error=max(abs(a-b) for a,b in zip(values,expected));assert error<.00125,error
    return dict(test='12bit-TV-all-gray',backend=backend,input_legal_gray_levels=count,output_unique_levels=len(set(values)),
                max_linear_error=error,integer_source_exact=True)


def main():
    results=[]
    for backend in ('d3d11','vulkan'):
        for kind in (('wide','pq','hlg') if backend=='d3d11' else ('wide',)):
            row=reference_case(backend,kind);results.append(row);print('PASS',backend,kind,max(row['stage_max_errors']),flush=True)
        row=gray_case(backend);results.append(row);print('PASS',backend,'gray',max(row['stage_max_errors']),flush=True)
        row=scale_case(backend);results.append(row);print('PASS',backend,'scale',row['maximum_error'],flush=True)
        row=dense_gray_case(backend);results.append(row);print('PASS',backend,'65536 gray',max(row['stage_max_errors']),row['stage_unique_linear_levels'],flush=True)
        row=rgb_case(backend);results.append(row);print('PASS',backend,'RGB16 全通道',max(row['stage_max_errors']),flush=True)
        row=video_gray12_case(backend);results.append(row);print('PASS',backend,'12bit TV gray',row['output_unique_levels'],row['max_linear_error'],flush=True)
    row=hdr_709_case();results.append(row);print('PASS PQ 709',max(row['stage_max_errors']),flush=True)
    (OUT/'pipeline-hdr-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
