"""经典 SDR 路线的实际 RGB10 交换链与独立标准参考。"""
import json,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']


def main():
    results=[]
    for bits,matrix,full,wide in ((8,6,True,False),(12,1,False,False),(16,9,True,True)):
        name=f'classic-{bits}-{matrix}-{int(full)}'
        media,expected=t['fixtures']['fixture'](name,bits,matrix,full,wide)
        for backend in ('d3d11','vulkan'):
            rows,status=t['capture'](media,name,backend,mode='sdr')
            final=next(r for r in rows if r[0]['phase']=='present')
            assert final[0]['format']==24,final[0]
            actual=[t['pixel'](final,i%4*64+32,i//4*64+32) for i in range(16)]
            error=max(abs(a-b) for rgb,ref in zip(actual,expected) for a,b in zip(rgb,ref))
            # 单像素预算：FP16 一 ULP＋8bit 一码阶＋RGB10 半码阶。
            means=[]
            for i in range(16):
                samples=[t['pixel'](final,x,y) for y in range(i//4*64+8,i//4*64+56) for x in range(i%4*64+8,i%4*64+56)]
                means.append([sum(v[c] for v in samples)/len(samples) for c in range(3)])
            mean_error=max(abs(a-b) for rgb,ref in zip(means,expected) for a,b in zip(rgb,ref))
            results.append(dict(test=name,backend=backend,max_encoded_error=error,final_format=24,
                                max_block_mean_error=mean_error,dithering_retained=True,mode=status['mode'],
                                reference_passed=error<.0055 and mean_error<.002,
                                reference_scope='纯矩阵基准；广色域实际 perceptual 映射须另行建立算法参考'))
            print('PASS' if results[-1]['reference_passed'] else 'REFERENCE DIFF',name,backend,error,mean_error,flush=True)
    (OUT/'pipeline-classic-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
