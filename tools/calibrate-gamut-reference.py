"""独立重建默认perceptual表，验证已保存的实际GPU色块；不重写历史研究结果。"""
import json, math, runpy, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/color-accuracy-20261011'
r=runpy.run_path(str(ROOT/'tools/color-map-reference.py'))
t=runpy.run_path(str(ROOT/'tools/test-color-output.py'))
f=runpy.run_path(str(ROOT/'tools/test-color-config.py'))


def main():
    raw=(OUT/'gamut-continuous.yuv').read_bytes();encoded=[]
    for i in range(16):
        offset=(i//4*64+32)*256+i%4*64+32
        codes=[struct.unpack_from('<H',raw,(p*65536+offset)*2)[0] for p in range(3)]
        y=codes[0]/65535;cb=(codes[1]-32768)/65535;cr=(codes[2]-32768)/65535
        red=y+1.4746*cr;blue=y+1.8814*cb;green=(y-.2627*red-.0593*blue)/.678
        encoded.append([red,green,blue])
    measurements=json.loads((OUT/'gamut-continuous-results.json').read_text(encoding='utf-8'))
    results=[]
    for variant,size in [('default',(48,32,256)),('linear-dense',(96,64,256))]:
        table=r['PerceptualTable'](80/10000,size)
        linear=[[t['sdr_linear'](max(v,0))*80/10000 for v in rgb] for rgb in encoded]
        to_output=lambda rgb:[f['encode_srgb'](max(v,0)*10000/80) for v in rgb]
        continuous=[to_output(r['perceptual'](rgb,0,80/10000)) for rgb in linear]
        table_reference=[to_output(table.sample(rgb)) for rgb in linear]
        for backend in ('d3d11','vulkan'):
            row=next(v for v in measurements if v['backend']==backend and v['variant']==variant)
            table_errors=[abs(a-b) for x,y in zip(row['actual'],table_reference) for a,b in zip(x,y)]
            continuous_errors=[abs(a-b) for x,y in zip(row['actual'],continuous) for a,b in zip(x,y)]
            def lab(rgb):
                xyz=r['matvec'](r['rgb_xyz']('709'),[t['sdr_linear'](v) for v in rgb])
                white=(.3127/.329,1,(1-.3127-.329)/.329)
                def transform(v):return v**(1/3) if v>(6/29)**3 else v/(3*(6/29)**2)+4/29
                x,y,z=[transform(a/b) for a,b in zip(xyz,white)]
                return [116*y-16,500*(x-y),200*(y-z)]
            de76=[math.dist(lab(a),lab(b)) for a,b in zip(row['actual'],continuous)]
            results.append(dict(backend=backend,variant=variant,size=size,source_after_yuv=encoded,
                measured=row['actual'],continuous_reference=continuous,table_reference=table_reference,
                max_table_encoded_error=max(table_errors),max_continuous_encoded_error=max(continuous_errors),
                max_continuous_delta_e_76=max(de76),mean_continuous_delta_e_76=sum(de76)/len(de76),
                table_model_passed=max(table_errors)<.002,reference_calibration_complete=True,
                continuous_comparison_is_algorithm_approximation=True,production_changed=False))
            print(backend,variant,'实际表参考',max(table_errors),'连续算法近似差',max(continuous_errors),flush=True)
    destination=ROOT/'docs/modernization/gamut-reference-calibration-20261012.json'
    destination.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(v['table_model_passed'] for v in results):raise SystemExit(1)


if __name__=='__main__':main()
