"""自动范围修复的 422 采样和非恒等 ICC 转换验证。"""
import json,math,os,runpy,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ['MPV_PIPELINE_OUT']=str(ROOT/'tmp/modernization/color-range-fix-20261011')
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']
t['EXCLUDED'].remove('color-range-fix.lua')


def main():
    results=[]
    _,encoded=t['fixtures']['fixture']('format-source',12,1,True,False)
    raw=(OUT/'format-source.yuv').read_bytes();plane=65536*2
    down=raw[:plane]
    for n in (1,2):
        down+=b''.join(raw[n*plane+(y*256+x)*2:n*plane+(y*256+x)*2+2]
                      for y in range(256) for x in range(0,256,2))
    path=OUT/'full422-12.yuv';path.write_bytes(down*48)
    media=OUT/'full422-12.mkv'
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y',
        '-f','rawvideo','-pixel_format','yuv422p12le','-video_size','256x256','-framerate','24',
        '-color_range','pc','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1',
        '-i',str(path),'-c:v','ffv1','-threads','1','-level','3','-pix_fmt','yuv422p12le',
        '-color_range','pc','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1',str(media)],check=True,timeout=60)
    decoded=subprocess.check_output([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error',
        '-i',str(media),'-frames:v','1','-pix_fmt','yuv422p12le','-f','rawvideo','-'],timeout=20)
    assert decoded==down,'422 夹具必须无损编码'
    expected=[[t['output']['sdr_linear'](v) for v in rgb] for rgb in encoded]
    for backend in ('d3d11','vulkan'):
        rows,status=t['capture'](media,'full422-12',backend)
        assert status['validation_range_fix']['state']=='已校正'
        assert status['validation_filtered']['pixelformat']=='yuv422p16'
        actual=[t['pixel'](rows[-1],i%4*64+32,i//4*64+32) for i in range(16)]
        error=max(abs(a-b) for rgb,ref in zip(actual,expected) for a,b in zip(rgb,ref))
        assert error<.00125,(backend,error)
        results.append(dict(test='422',backend=backend,maximum_linear_error=error,sampling_preserved=True))
        print('PASS 422',backend,error,flush=True)
    icc=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline-icc.py'))['profile']()
    for bits,matrix in ((10,1),(12,9)):
        name=f'fix-icc-{bits}-{matrix}'
        media,encoded=t['fixtures']['fixture'](name,bits,matrix,True,matrix==9)
        expected=[[math.sqrt(t['output']['sdr_linear'](v)) for v in rgb] for rgb in encoded]
        for backend in ('d3d11','vulkan'):
            rows,status=t['capture'](media,name,backend,mode='icc',icc_profile=icc)
            assert status['validation_range_fix']['state']=='已校正'
            final=rows[-1];assert final[0]['format']==24
            means=[]
            for i in range(16):
                samples=[t['pixel'](final,x,y) for y in range(i//4*64+8,i//4*64+56)
                         for x in range(i%4*64+8,i%4*64+56)]
                means.append([sum(v[c] for v in samples)/len(samples) for c in range(3)])
            error=max(abs(a-b) for rgb,ref in zip(means,expected) for a,b in zip(rgb,ref))
            assert error<.002,(name,backend,error)
            assert abs(means[12][0]-encoded[12][0])>.01,'ICC 非恒等转换未执行'
            results.append(dict(test='icc',bits=bits,matrix=matrix,backend=backend,
                                maximum_mean_encoded_error=error,target_gamma=2,profile_applied=True))
            print('PASS ICC',bits,matrix,backend,error,flush=True)
    (OUT/'format-icc-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
