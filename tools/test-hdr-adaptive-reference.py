"""默认 HDR 自适应映射的静态场景独立参考；诊断副本不改生产参数。"""
import json, math, os, runpy, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/color-accuracy-20261012'
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'))
t['EXCLUDED'].remove('color-range-fix.lua')
hdr=t['output']['hdr'];hdr['fixture'].__globals__['OUT']=OUT
r=runpy.run_path(str(ROOT/'tools/color-map-reference.py'))


def scene_measure(rgb_nits,percentile):
    # 各块与16×16工作组边界对齐；从源码值推导整数统计，不用GPU结果拟合。
    ys=[sum(a*b for a,b in zip((.2627,.6780,.0593),v)) for v in rgb_nits]
    yp=[int(16383*r['pq'](v/10000)*r['smooth'](0,.01,r['pq'](v/10000))) for v in ys]
    mx=[max(v) for v in rgb_nits]
    active=[i for i,v in enumerate(yp) if v>0]
    lin=[int(65535*min(v/10000,1)) for v in mx]
    average_pq=sum(yp[i] for i in active)/(len(active)*16383)
    scene_average=10000*sum(lin[i] for i in active)/(len(active)*65535)
    max_rgb=r['pq'](10000*max(lin)/65535/10000)
    hist=[0]*64
    for i in active:
        bin_index=max(0,min(63,(int(16383*r['pq'](mx[i]/10000))>>7)-64))
        hist[bin_index]+=4096
    total=sum(hist);target=math.ceil(percentile/100*total)
    if 0<percentile<100 and target<total:
        count=0
        for i,num in enumerate(hist):
            upper=count+num
            if upper>=target:
                lo=((i+64)<<7)/16383;hi=((i+65)<<7)/16383
                if upper+1>total:hi=max(max_rgb,lo)
                max_rgb=r['mix'](lo,hi,(target-count)/(upper+1-count));break
            count=upper
    return dict(average_pq=average_pq,scene_average=scene_average,
        maximum_pq=max(max(yp)/16383,max_rgb),active_blocks=len(active))


def reference(rgb,scene,lut_size=None):
    peak=r['unpq'](scene['maximum_pq'])*10000
    virtual,exposure=r['dynamic_target'](peak,scene['scene_average'],80)
    limits=(0,scene['maximum_pq'],scene['average_pq'],0,r['pq'](virtual/10000))
    def curve(v):
        if lut_size is None:return r['spline'](v,*limits)
        x=r['clamp'](v/limits[1])*(lut_size-1);i=int(x);k=x-i
        return r['mix'](r['spline'](i/(lut_size-1)*limits[1],*limits),
            r['spline'](min(i+1,lut_size-1)/(lut_size-1)*limits[1],*limits),k)
    forward=r['matmul'](r['matmul'](r['CROSS'],r['HPE']),r['rgb_xyz']('2020'))
    backward=r['inv'](forward)
    cones=r['matvec'](forward,[v/10000 for v in rgb])
    mapped=[r['unpq'](curve(r['pq'](v))) for v in cones]
    lx=min(max(rgb)/10000,1);gain=r['unpq'](curve(r['pq'](lx)))/max(lx,1e-9)
    knee=r['clamp'](scene['average_pq'],limits[1]*.1,limits[1]*.8)
    knee_in=r['unpq'](knee);knee_gain=r['unpq'](r['spline'](knee,*limits))/max(knee_in,1e-9)
    ramp=r['clamp'](1-gain/knee_gain)**2 if lx>knee_in else 0
    weights=[.3*r['mix'](r['clamp'](v/max(max(cones),1e-9)),1,ramp) for v in cones]
    result=[r['mix'](v*gain,w,k) for v,w,k in zip(cones,mapped,weights)]
    rgb_out=[v*exposure*10000/80 for v in r['matvec'](backward,result)]
    return r['matvec'](hdr['MATRIX'],rgb_out),virtual,exposure


def main():
    results=[]
    for name,transfer,colors in [
        ('pq1000','smpte2084',[(r['pq'](v/10000),)*3 for v in [0,1,5,10,20,40,80,100,203,300,400,500,600,700,800,1000]]),
        ('pq4000','smpte2084',[(r['pq'](v/10000),)*3 for v in [0,1,5,10,20,40,80,203,500,800,1000,1500,2000,2500,3000,4000]]),
        ('pq-color4000','smpte2084',[tuple(r['pq'](v/10000) for v in rgb) for rgb in
            [(1000,10,10),(10,1000,10),(10,10,1000),(1000,1000,10),
             (1000,10,1000),(10,1000,1000),(4000,50,50),(50,4000,50),
             (50,50,4000),(80,203,1000),(1000,203,80),(203,1000,80),
             (1,2,3),(10,20,30),(203,203,203),(0,0,0)]]),
        ('hlg1000','arib-std-b67',[(v,)*3 for v in [0,.01,.05,.1,.2,.3,.4,.5,.6,.65,.7,.75,.8,.85,.9,1]])]:
        media,decoded=hdr['fixture']('adaptive-'+name,colors,transfer)
        source=[[r['unpq'](v)*10000 for v in rgb] if transfer=='smpte2084'
            else t['output']['reference']['hlg_reference'](rgb,1000) for rgb in decoded]
        for backend in ('d3d11','vulkan'):
            for size in (256,1024):
                options={}
                def configure(p):
                    p.command('set_property','target-contrast','inf')
                    for key in ('tone-mapping','hdr-compute-peak','hdr-peak-percentile','hdr-contrast-recovery','libplacebo-opts'):
                        options[key]=p.get('options/'+key)
                rows,status=t['capture'](media,'adaptive-'+name+'-'+str(size),backend,
                    extra_args=['--msg-level=vo/gpu-next=debug']+([] if size==256 else ['--libplacebo-opts=tone_lut_size=1024']),post_configure=configure)
                final=rows[-1];assert final[0]['format']==10
                actual=[t['pixel'](final,i%4*64+32,i//4*64+32) for i in range(16)]
                scene=scene_measure(source,options['hdr-peak-percentile'])
                if transfer=='smpte2084':
                    # 峰值检测同次绘制把编码域RGB写入FP16；映射前必须计入这次实际量化。
                    def half(v):
                        bits=struct.unpack('<H',struct.pack('<e',v))[0]
                        nearest=struct.unpack('<e',struct.pack('<H',bits))[0]
                        return struct.unpack('<e',struct.pack('<H',bits-1))[0] if nearest>v else nearest
                    stored=[[half(v) for v in rgb] for rgb in decoded]
                    first=next(v for v in rows if v[0]['phase']=='output')
                    samples=[t['pixel'](first,i%4*64+32,i//4*64+32) for i in range(16)]
                    assert samples==[tuple(v) for v in stored],('编码域FP16向零写回验证失败',samples,stored)
                    rendered=[[r['unpq'](v)*10000 for v in rgb] for rgb in stored]
                    calculated=[reference(v,scene) for v in rendered]
                    lut_reference=[reference(v,scene,size)[0] for v in rendered]
                    branch='PQ 峰值检测、编码域FP16写回、动态虚拟目标、LMS film响应'
                else:
                    # HLG映射先推导80nit目标峰值和低亮度系统gamma，而不是固定1000nit后再套PQ曲线。
                    gamma=1.2*1.111**math.log2(80/1000)
                    scene_linear=[[v*v/3 if v<=.5 else (math.exp((v-.55991073)/.17883277)+.28466892)/12 for v in rgb] for rgb in decoded]
                    linear=[[v*max(sum(a*b for a,b in zip((.2627,.6780,.0593),rgb)),1e-30)**(gamma-1) for v in rgb] for rgb in scene_linear]
                    continuous=[r['matvec'](hdr['MATRIX'],v) for v in linear]
                    calculated=[(v,80,1) for v in continuous];lut_reference=continuous
                    branch='HLG 目标80nit低亮度系统gamma适配，无额外spline'
                continuous=[v[0] for v in calculated]
                error=max(abs(a-b) for rgb,ref in zip(actual,continuous) for a,b in zip(rgb,ref))
                lut_error=max(abs(a-b) for rgb,ref in zip(actual,lut_reference) for a,b in zip(rgb,ref))
                result=dict(case=name,backend=backend,lut_size=size,options=options,source_nits=source,
                    measured=actual,continuous_reference=continuous,lut_reference=lut_reference,
                    scene_reference=scene,virtual_peak=calculated[0][1],exposure=calculated[0][2],
                    max_linear_error=error,max_lut_linear_error=lut_error,reference_passed=error<.002,
                    neutral_static_scene_only='color' not in name,production_changed=False,target=status['actual_target'],actual_branch=branch)
                results.append(result)
                (OUT/'adaptive-hdr-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
                print(name,backend,size,'连续误差',error,'表误差',lut_error,'虚拟峰值',calculated[0][1],options,flush=True)
    if not all(v['reference_passed'] for v in results):raise SystemExit(1)


if __name__=='__main__':main()
