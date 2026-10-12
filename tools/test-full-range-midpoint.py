"""定位高位深 full-range 的中点偏差，并独立预测实际 GPU 数值。"""
import json,re,runpy,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']


def main():
    results=[]
    for bits in (8,10,12,16):
        name='midpoint-'+str(bits)
        media,expected_encoded=t['fixtures']['fixture'](name,bits,1,True,False)
        rows,status=t['capture'](media,name,'d3d11')
        first=next(m for m,b in rows if m['phase']=='input' and m['format'] in (56,61))
        slot=int(re.search(r'cbuffer[\s\S]*?register\(b(\d+)\)',first['shader']).group(1))
        constants=next(c['floats'] for c in first['constants'] if c['slot']==slot)
        measured_midpoint=-constants[14]/constants[6]
        texture_bits=8 if bits==8 else 16
        texture_max=2**texture_bits-1;model_midpoint=2**(texture_bits-1)/texture_max
        assert abs(measured_midpoint-model_midpoint)<1e-7,(bits,measured_midpoint,model_midpoint)
        raw=(OUT/(name+'.yuv')).read_bytes();sample_size=1 if bits==8 else 2
        final=rows[-1];errors=[]
        for i in range(16):
            x=i%4*64+32;y=i//4*64+32
            codes=[raw[plane*65536+y*256+x] if bits==8 else struct.unpack_from('<H',raw,(plane*65536+y*256+x)*2)[0] for plane in range(3)]
            luma=codes[0]/(2**bits-1)
            u=(codes[1]/(2**bits-1)-model_midpoint)*texture_max/(texture_max-1)
            v=(codes[2]/(2**bits-1)-model_midpoint)*texture_max/(texture_max-1)
            kr,kb=.2126,.0722;kg=1-kr-kb
            rgb=[luma+(2-2*kr)*v,luma-kb*(2-2*kb)/kg*u-kr*(2-2*kr)/kg*v,luma+(2-2*kb)*u]
            predicted=[t['output']['sdr_linear'](max(value,0)) for value in rgb]
            errors.extend(abs(a-b) for a,b in zip(t['pixel'](final,x,y),predicted))
        assert max(errors)<.0005,(bits,max(errors))
        nominal_midpoint=2**(bits-1)/(2**bits-1)
        results.append(dict(bits=bits,measured_midpoint=measured_midpoint,nominal_midpoint=nominal_midpoint,
                            model_max_error=max(errors),midpoint_bias=measured_midpoint-nominal_midpoint))
        print(bits,'中点',measured_midpoint,'应为',nominal_midpoint,'模型误差',max(errors),flush=True)
    assert abs(results[1]['midpoint_bias'])>.0004 and abs(results[2]['midpoint_bias'])>.0001
    (OUT/'full-range-midpoint.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
