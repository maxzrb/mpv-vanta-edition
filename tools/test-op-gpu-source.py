"""真实 4K AV1 12bit444 样片的解码至 GPU 源平面一致性验证。"""
import json,runpy,subprocess,hashlib,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']
SOURCE=Path(r'C:\Users\maxzr\Downloads\OP-yuv444p12-SWTest.mkv')
POSITION=5


def main():
    raw=OUT/'op-color-frame.yuv'
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y','-threads','1',
                    '-ss',str(POSITION),'-i',str(SOURCE),'-frames:v','1','-pix_fmt','yuv444p12le','-f','rawvideo',str(raw)],check=True,timeout=120)
    decoded=raw.read_bytes();plane_size=3840*2160*2
    assert len(decoded)==plane_size*3
    results=[]
    for backend in ('d3d11','vulkan'):
        rows,status=t['capture'](SOURCE,'op-source',backend,size='1024x576',seek_time=POSITION)
        planes=[r for r in rows if r[0]['phase']=='input' and r[0]['format']==56 and r[0]['width']==3840 and r[0]['height']==2160][:3]
        assert len(planes)==3
        digests=[]
        for i,(m,b) in enumerate(planes):
            visible=b''.join(b[y*m['stride']:y*m['stride']+3840*2] for y in range(2160))
            assert visible==decoded[i*plane_size:(i+1)*plane_size],(backend,i,'AV1 原始整数样本不同')
            digests.append(hashlib.sha256(visible).hexdigest())
        first=next(r for r in rows if r[0]['phase']=='output' and r[0]['format']==10 and r[0]['width']==3840 and r[0]['height']==2160)
        errors=[];sampled_values=[]
        for y in range(60,2160,240):
            for x in range(80,3840,320):
                codes=[struct.unpack_from('<H',decoded,i*plane_size+(y*3840+x)*2)[0] for i in range(3)]
                rgb=t['fixtures']['reference'](codes,12,1,False)
                # 缩小前的线性工作值以 203 nit 为单位；本场景 SDR 白为 80 nit。
                # 后续输出编码再乘 203/80，不能把此中间值当作最终 scRGB。
                expected=[max(v,0)**2.4*80/203 for v in rgb]
                actual=t['pixel'](first,x,y)
                sampled_values.extend(expected)
                errors.extend(abs(a-b) for a,b in zip(actual,expected))
        assert max(errors)<.00125,('真实 OP 的矩阵／BT.1886 线性化不符',max(errors))
        assert max(sampled_values)>.1 and max(sampled_values)-min(sampled_values)>.1,'不能用黑场冒充色彩变换验收'
        results.append(dict(backend=backend,source=status['validation_source'],all_24883200_integer_samples_exact=True,
                            plane_sha256=digests,bt1886_first_write_max_error=max(errors),reference_components=len(errors),
                            requested_position=POSITION,working_luminance_unit_nits=203,source_sdr_white_nits=80,
                            nontrivial_reference_range=[min(sampled_values),max(sampled_values)],
                            graph=[{'phase':m['phase'],'size':[m['width'],m['height']],'format':m['format']} for m,b in rows]))
        print('PASS',backend,'真实 AV1 12bit444 全帧 24,883,200 个整数样本逐字节相等',flush=True)
    (OUT/'op-source-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
