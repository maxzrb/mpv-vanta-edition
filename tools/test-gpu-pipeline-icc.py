"""显式 ICC 路线：构造精确 gamma=2 目标，用独立数学验证非恒等转换。"""
import json,math,runpy,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']


def profile():
    data=bytearray(Path(r'C:\Windows\System32\spool\drivers\color\sRGB Color Space Profile.icm').read_bytes())
    count=struct.unpack_from('>I',data,128)[0]
    for i in range(count):
        tag=data[132+i*12:136+i*12]
        if tag in (b'rTRC',b'gTRC',b'bTRC'):
            offset,size=struct.unpack_from('>II',data,136+i*12)
            assert data[offset:offset+4]==b'curv'
            # ICC v2 的单点 curv 表示精确 U8.8 gamma；不修改原色矩阵和白点。
            data[offset:offset+size]=b'curv'+bytes(4)+struct.pack('>IH',1,512)+bytes(size-14)
    path=OUT/'reference-gamma2.icc';path.write_bytes(data);return path


def main():
    icc=profile();results=[]
    for bits,matrix,full,wide in ((12,1,False,False),(16,9,True,True)):
        name=f'icc-{bits}-{matrix}-{int(full)}'
        media,source=t['fixtures']['fixture'](name,bits,matrix,full,wide)
        expected=[[math.sqrt(t['output']['sdr_linear'](v)) for v in rgb] for rgb in source]
        for backend in ('d3d11','vulkan'):
            rows,status=t['capture'](media,name,backend,mode='icc',icc_profile=icc)
            final=rows[-1];assert final[0]['format']==24
            means=[]
            for i in range(16):
                samples=[t['pixel'](final,x,y) for y in range(i//4*64+8,i//4*64+56) for x in range(i%4*64+8,i%4*64+56)]
                means.append([sum(v[c] for v in samples)/len(samples) for c in range(3)])
            error=max(abs(a-b) for rgb,target in zip(means,expected) for a,b in zip(rgb,target))
            assert error<.002,(name,backend,error,means,expected)
            assert abs(means[12][0]-source[12][0])>.01,'ICC 非恒等变换未执行'
            results.append(dict(test=name,backend=backend,max_mean_encoded_error=error,source_gamut='bt2020' if wide else 'bt709',target_gamma=2,
                                output_format=24,profile_applied=True))
            print('PASS',name,backend,error,flush=True)
    (OUT/'pipeline-icc-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
