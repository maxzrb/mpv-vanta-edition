"""同一 HLG 色块：mpv 实际 scRGB 读回与 BT.2100／3FP 基础公式的对照。"""
import json,math,os,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/color-accuracy-20261011'
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'))
t['EXCLUDED'].remove('color-range-fix.lua')
hdr=t['output']['hdr'];hdr['fixture'].__globals__['OUT']=OUT
ref=t['output']['reference']
mathref=runpy.run_path(str(ROOT/'tools/color-map-reference.py'))


def main():
    colors=[(.75,.75,.75),(.75,.25,.25),(.25,.75,.25),(.25,.25,.75),
        (.75,.75,.25),(.75,.25,.75),(.25,.75,.75),(.5,.5,.5),
        (0,0,0),(.1,.1,.1),(.25,.25,.25),(.9,.9,.9),
        (.75,.5,.25),(.5,.75,.25),(.25,.5,.75),(1,1,1)]
    media,decoded=hdr['fixture']('hlg-common-reference',colors,'arib-std-b67')
    rows,status=t['capture'](media,'hlg-common-reference','d3d11',hdr_transfer='arib-std-b67')
    final=rows[-1];assert final[0]['format']==10 and final[0]['color_space']==1
    actual=[t['pixel'](final,i%4*64+32,i//4*64+32) for i in range(16)]
    backward=mathref['inv'](hdr['MATRIX']);results=[]
    for i,(requested,rgb,observed) in enumerate(zip(colors,decoded,actual)):
        standard=ref['hlg_reference'](rgb,1000)
        source=[v*v/3 if v<=.5 else (math.exp((v-.55991073)/.17883277)+.28466892)/12 for v in rgb]
        public3fp=[1000*v**1.2 for v in source]
        expected=[sum(a*b for a,b in zip(row,standard))/80 for row in hdr['MATRIX']]
        assert all(abs(a-b)<=.00125+.002*abs(b) for a,b in zip(observed,expected)),(i,observed,expected)
        observed_nits=[v*80 for v in mathref['matvec'](backward,observed)]
        results.append(dict(requested=requested,encoded_after_yuv=rgb,standard_bt2020_nits=standard,
            mpv_gpu_scrgb=observed,mpv_equivalent_bt2020_nits=observed_nits,
            mpv_max_nits_error=max(abs(a-b) for a,b in zip(observed_nits,standard)),
            public_3fp_base_formula_nits=public3fp,
            public_3fp_formula_max_nits_error=max(abs(a-b) for a,b in zip(public3fp,standard))))
    result=dict(reference='BT.2100 黑位0、HLG参考峰值1000nit；实际16bit有限范围YUV同一编码色块',
        mpv_real_gpu_readback=True,threefp_formula_comparison_not_playback_measurement=True,
        max_mpv_nits_error=max(r['mpv_max_nits_error'] for r in results),cases=results)
    (OUT/'hlg-common-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('HLG同源参考 PASS；mpv全16色块最大等效通道误差',result['max_mpv_nits_error'],'nit')
    print('红色反例：mpv',results[1]['mpv_max_nits_error'],'nit；3FP公开基础公式',results[1]['public_3fp_formula_max_nits_error'],'nit')


if __name__=='__main__':main()
