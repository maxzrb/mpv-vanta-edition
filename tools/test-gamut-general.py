"""跨两API的广覆盖色域数值验收；色差对连续算法，表示误差对离散表。"""
import argparse, json, math, os, runpy, time, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/gamut-general-20261012';OUT.mkdir(parents=True,exist_ok=True)
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));t['EXCLUDED'].remove('color-range-fix.lua')
r=runpy.run_path(str(ROOT/'tools/color-map-reference.py'))
m=runpy.run_path(str(ROOT/'tools/color-metrics.py'))
f=runpy.run_path(str(ROOT/'tools/gamut-study-fixture.py'))
VARIANTS={'default':(48,32,256),'middle':(64,48,256),'dense':(96,64,256),'production':(96,64,256)}


def means(final,fixture):
    values=[]
    for i in range(len(fixture['samples'])):
        x=i%fixture['columns']*fixture['tile'];y=i//fixture['columns']*fixture['tile']
        pixels=[t['pixel'](final,a,b) for b in range(y+4,y+12) for a in range(x+4,x+12)]
        values.append([sum(v[c] for v in pixels)/len(pixels) for c in range(3)])
    return values


def references(fixture,kind,size):
    rgb=fixture['decoded']
    if kind in ('hlg','pq'):
        # 经典SDR走1000nit源HLG与自适应映射；ACM/scRGB的HLG目标适配是另一分支。
        adaptive=runpy.run_path(str(ROOT/'tools/test-hdr-adaptive-reference.py'))
        os.environ['MPV_PIPELINE_OUT']=str(OUT)
        decode=(lambda item:[r['unpq'](max(v,0))*10000 for v in item]) if kind=='pq' else (lambda item:t['output']['reference']['hlg_reference']([max(v,0) for v in item],1000))
        source=[decode(item) for item in rgb]
        scene=adaptive['scene_measure'](source,99.995003)
        def half(v):
            bits=struct.unpack('<H',struct.pack('<e',v))[0]
            if abs(struct.unpack('<e',struct.pack('<H',bits))[0])>abs(v):bits-=1
            return struct.unpack('<e',struct.pack('<H',bits))[0]
        rendered=[decode([half(v) for v in item]) for item in rgb]
        inverse=r['inv'](adaptive['hdr']['MATRIX'])
        def mapped(item,lut):
            # 源HLG名义母版峰值1000nit；实测场景未越1.1倍峰值时，默认先作95%膝点软折返。
            def master_clip(value):
                x=value/1000;over=max(x-.95,0)/.05
                return (min(x,.95)+.05*over/(1+over))*1000
            clipped=[master_clip(v) for v in item] if kind=='hlg' else item
            return [v*80/10000 for v in r['matvec'](inverse,adaptive['reference'](clipped,scene,lut)[0])]
        rgb=[mapped(item,None) for item in source]
        quantized_rgb=[mapped(item,256) for item in rendered]
    else:
        rgb=[[t['output']['sdr_linear'](max(v,0))*80/10000 for v in item] for item in rgb]
        quantized_rgb=rgb
    src=r['Gamut']('2020',0,80/10000);dst=r['Gamut']('709',0,80/10000);table=r['PerceptualTable'](80/10000,size)
    if kind=='icc':
        helper=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline-icc.py'));helper['profile'].__globals__['OUT']=OUT
        transform=m['icc_linear_transform'](helper['profile']())
    def encode(item):
        if kind=='icc':
            target=r['matvec'](transform,[max(v*10000/80,0) for v in item])
            return [math.sqrt(max(v,0)) for v in target]
        return [t['fixtures']['encode_srgb'](max(v*10000/80,0)) for v in item]
    continuous=[];discrete=[]
    for i,item in enumerate(rgb):
        continuous.append(encode(dst.ipt_rgb(r['perceptual_ipt'](src.rgb_ipt(item),src,dst))))
        discrete.append(encode(table.sample(quantized_rgb[i])))
        if i%500==0:print('参考',kind,size,i,'/',len(rgb),flush=True)
    return continuous,discrete


def trial(fixture,kind,backend,variant,continuous,discrete):
    size=VARIANTS[variant];extra=[] if variant=='production' else ['--libplacebo-opts=lut3d_size_I=%d,lut3d_size_C=%d,lut3d_size_h=%d'%size]
    if kind=='icc':
        helper=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline-icc.py'));helper['profile'].__globals__['OUT']=OUT
        icc=helper['profile']()
    else:icc=None
    options={}
    def configure(player):
        player.command('set_property','target-contrast','inf')
        options.update(player.get('libplacebo-opts'))
        for key,value in zip(('lut3d_size_I','lut3d_size_C','lut3d_size_h'),size):assert int(options[key])==value
    rows,status=t['capture'](fixture['path'],f'general-{kind}-{variant}',backend,
        size=f"{fixture['width']}x{fixture['height']}",mode='icc' if kind=='icc' else 'sdr',icc_profile=icc,extra_args=extra,
        post_configure=configure)
    source=[v for v in rows if v[0]['phase']=='input' and v[0]['format']==56 and v[0]['width']==fixture['width'] and v[0]['height']==fixture['height']]
    assert len(source)==3
    plane_bytes=fixture['width']*fixture['height']*2
    for index,(meta,data) in enumerate(source):
        actual=b''.join(data[y*meta['stride']:y*meta['stride']+fixture['width']*2] for y in range(fixture['height']))
        assert actual==fixture['raw'][index*plane_bytes:(index+1)*plane_bytes]
    final=rows[-1];assert final[0]['format']==24 and (final[0]['width'],final[0]['height'])==(fixture['width'],fixture['height'])
    actual=means(final,fixture)
    inverse=r['inv'](m['icc_linear_transform'](icc)) if kind=='icc' else None
    lab=lambda rgb:m['lab_from_linear'](r['matvec'](inverse,[v*v for v in rgb])) if kind=='icc' else m['lab_from_srgb'](rgb)
    de00=[m['delta_e_2000'](lab(a),lab(b)) for a,b in zip(actual,continuous)]
    model_de00=[m['delta_e_2000'](lab(a),lab(b)) for a,b in zip(actual,discrete)]
    encoded=[max(abs(a-b) for a,b in zip(x,y)) for x,y in zip(actual,discrete)]
    groups={key:m['statistics']([v for v,item in zip(de00,fixture['samples']) if item['kind']==key]) for key in ('gray','near-gray','hsv','rgb-grid')}
    grays=[a for a,item in zip(actual,fixture['samples']) if item['kind']=='gray']
    result=dict(kind=kind,backend=backend,variant=variant,size=size,source_sha256=fixture['source_sha256'],source_all_integer_samples_exact=True,
        count=len(actual),continuous_delta_e_00=m['statistics'](de00),by_group=groups,
        discrete_max_encoded_error=max(encoded),discrete_delta_e_00=m['statistics'](model_de00),
        # ICC的17阶四面体表/黑点近似不等于解析矩阵；用实际ICC物理色差验收，保留编码误差。
        discrete_model_passed=max(model_de00)<.25 if kind=='icc' else max(encoded)<.004,
        discrete_acceptance='ICC物理ΔE00<0.25（包含内部ICC表近似）' if kind=='icc' else '编码值最大绝对误差<0.004',
        gray_max_encoded_channel_spread=max(max(v)-min(v) for v in grays),
        gray_luminance_monotonic=all(sum(a)<=sum(b)+1e-8 for a,b in zip(grays,grays[1:])),
        actual=actual,continuous_reference=continuous,discrete_reference=discrete,delta_e_00_by_sample=de00,
        target=status['actual_target'],options=options,production_default_verified=variant=='production')
    print('GPU',kind,backend,variant,'ΔE00',result['continuous_delta_e_00'],'表误差',max(encoded),'灰通道差',result['gray_max_encoded_channel_spread'],flush=True)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['sdr','hlg','pq','icc'],default='sdr')
    parser.add_argument('--production',action='store_true');args=parser.parse_args()
    metric_test=m['self_test'](OUT/'ciede2000testdata.txt')
    fixture=f['fixture']('arib-std-b67' if args.kind=='hlg' else 'smpte2084' if args.kind=='pq' else 'iec61966-2-1')
    results=[]
    variants={'production':VARIANTS['production']} if args.production else {key:value for key,value in VARIANTS.items() if key!='production'}
    for variant,size in variants.items():
        continuous,discrete=references(fixture,args.kind,size)
        for backend in ('d3d11','vulkan'):
            results.append(trial(fixture,args.kind,backend,variant,continuous,discrete))
            prefix='production' if args.production else 'general'
            (OUT/f'{prefix}-{args.kind}-results.json').write_text(json.dumps(dict(metric_test=metric_test,samples=fixture['samples'],trials=results),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(v['discrete_model_passed'] and v['gray_luminance_monotonic'] for v in results):raise SystemExit(1)


if __name__=='__main__':main()
