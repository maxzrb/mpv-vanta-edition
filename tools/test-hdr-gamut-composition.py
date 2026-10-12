"""彩色PQ→经典SDR：默认自适应曲线与perceptual色域表组合的独立参考。"""
import json, math, runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
d=runpy.run_path(str(ROOT/'tools/test-hdr-adaptive-reference.py'))
t=d['t'];r=d['r'];OUT=d['OUT'];hdr=d['hdr']


def main():
    nits=[(1000,10,10),(10,1000,10),(10,10,1000),(1000,1000,10),
        (1000,10,1000),(10,1000,1000),(4000,50,50),(50,4000,50),
        (50,50,4000),(80,203,1000),(1000,203,80),(203,1000,80),
        (1,2,3),(10,20,30),(203,203,203),(0,0,0)]
    colors=[tuple(r['pq'](v/10000) for v in rgb) for rgb in nits]
    media,decoded=hdr['fixture']('hdr-gamut-composition',colors,'smpte2084')
    source=[[r['unpq'](v)*10000 for v in rgb] for rgb in decoded]
    inverse=r['inv'](hdr['MATRIX']);results=[]
    for variant,size,extra in [('default',(48,32,256),['--libplacebo-opts=lut3d_size_I=48,lut3d_size_C=32,lut3d_size_h=256']),('dense',(96,64,256),
            ['--libplacebo-opts=lut3d_size_I=96,lut3d_size_C=64,lut3d_size_h=256'])]:
        table=r['PerceptualTable'](80/10000,size)
        for backend in ('d3d11','vulkan'):
            options={}
            def configure(p):
                p.command('set_property','target-contrast','inf')
                options['hdr-peak-percentile']=p.get('options/hdr-peak-percentile')
            rows,status=t['capture'](media,'composition-'+variant,backend,mode='sdr',
                extra_args=extra,post_configure=configure)
            first=next(v for v in rows if v[0]['phase']=='output');final=rows[-1]
            assert first[0]['format']==10 and final[0]['format']==24
            encoded_half=[t['pixel'](first,i%4*64+32,i//4*64+32) for i in range(16)]
            # 实际中间量单独核对源码整数值的FP16向零转换；不把它直接代入算法参考。
            import struct
            def half(v):
                bits=struct.unpack('<H',struct.pack('<e',v))[0]
                if struct.unpack('<e',struct.pack('<H',bits))[0]>v:bits-=1
                return struct.unpack('<e',struct.pack('<H',bits))[0]
            stored=[tuple(half(v) for v in rgb) for rgb in decoded]
            assert encoded_half==stored
            rendered=[[r['unpq'](v)*10000 for v in rgb] for rgb in stored]
            scene=d['scene_measure'](source,options['hdr-peak-percentile'])
            normalized709=[d['reference'](rgb,scene,256)[0] for rgb in rendered]
            normalized2020=[r['matvec'](inverse,rgb) for rgb in normalized709]
            physical2020=[[v*80/10000 for v in rgb] for rgb in normalized2020]
            encode=lambda rgb:[t['fixtures']['encode_srgb'](max(v,0)*10000/80) for v in rgb]
            expected=[encode(table.sample(rgb)) for rgb in physical2020]
            continuous=[encode(r['perceptual'](rgb,0,80/10000)) for rgb in physical2020]
            actual=[]
            for i in range(16):
                samples=[t['pixel'](final,x,y) for y in range(i//4*64+8,i//4*64+56)
                    for x in range(i%4*64+8,i%4*64+56)]
                actual.append([sum(v[c] for v in samples)/len(samples) for c in range(3)])
            error=max(abs(a-b) for x,y in zip(actual,expected) for a,b in zip(x,y))
            result=dict(backend=backend,variant=variant,actual=actual,table_reference=expected,
                continuous_reference=continuous,max_encoded_error=error,reference_passed=error<.004,
                scene_reference=scene,source_after_yuv=decoded,target=status['actual_target'],
                production_changed=False,scope='固定静态彩色PQ4000，非场景切换平滑时序验收')
            results.append(result);print(backend,variant,'组合表参考误差',error,flush=True)
            (OUT/'hdr-gamut-composition-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(v['reference_passed'] for v in results):raise SystemExit(1)


if __name__=='__main__':main()
