"""Vulkan SDR ACM 独立参考及与 D3D11 的 HDR→SDR 数值对照。"""
import ast,json,runpy
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'tmp/modernization/performance-followup-20261011';out.mkdir(parents=True,exist_ok=True)
test=runpy.run_path(str(root/'tools/test-color-output.py'))
vk=runpy.run_path(str(root/'tools/gpu-readback-vulkan.py'))
original_config=test['create_config']


def config(name,exclude_scripts=()):
    cfg=original_config('vk-'+name,exclude_scripts=exclude_scripts)
    return cfg


def create_player(args,name,executable=None):
    args=[a for a in args if not a.startswith('--gpu-api=')]
    return vk['create_player']([*args,'--gpu-api=vulkan','--target-colorspace-hint=yes'],name+'-vk',executable=executable)


def floating(frame):
    assert frame.meta['vk_format']==97 and frame.meta['color_space']==1000104002,frame.meta


g=test['launch'].__globals__
g['create_config']=config;g['create_player']=create_player;g['floating']=floating
g['OUT']=out/'vulkan-color';g['OUT'].mkdir(exist_ok=True)
test['hdr']['fixture'].__globals__['OUT']=g['OUT']
source=(root/'tools/test-color-output.py').read_text(encoding='utf-8')
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='run_calibration')
exec(ast.get_source_segment(source,node).replace("frame.meta['color_space']==1","frame.meta['color_space']==1000104002"),g)
test['run_calibration']=g['run_calibration']
rows=[]
for name in ['run_calibration','run_sdr']:
    rows.append(test[name]());print('PASS',rows[-1]['test'],flush=True)
wide=[(v,)*3 for v in [0,.01,.05,.1,.25,.5,.75,1]]
wide += [(1,0,0),(0,1,0),(0,0,1),(.75,.5,.25),(.5,.75,.25),(.25,.5,.75),(.5,.5,.5),(.75,.75,.75)]
rows.append(test['run_reference']('vk-wide-sdr',wide,'iec61966-2-1'));print('PASS 广 SDR 独立参考',flush=True)
rows.append(test['run_downscale']());print('PASS 线性缩小独立参考',flush=True)
# HDR 源片在本机 SDR ACM 的实际映射，与已保留的 D3D11 路线逐色块对照。
# 此处不注入 HDR 桌面能力，不冒充真实 HDR 桌面验收。
pq=[(test['reference']['pq_encode'](v),)*3 for v in [0,.01,1,10,80,100,203,1000]]
pq += [tuple(test['reference']['pq_encode'](v) for v in rgb) for rgb in [(100,0,0),(0,100,0),(0,0,100),(203,100,80),(1000,203,100),(10,20,30),(80,80,80),(203,203,203)]]
hlg=[(v,)*3 for v in [0,.01,.05,.1,.25,.5,.75,1]]+[(.75,0,0),(0,.75,0),(0,0,.75),(.75,.5,.25),(.5,.75,.25),(.25,.5,.75),(.5,.5,.5),(.75,.75,.75)]
for name,colors,trc in [('pq',pq,'smpte2084'),('hlg',hlg,'arib-std-b67')]:
    media,_=test['hdr']['fixture']('vk-sdr-'+name,colors,trc)
    values=[]
    for backend in ['d3d11','vulkan']:
        cfg=config('sdr-'+name,exclude_scripts=['uosc','stats.lua','startup-format-logos.lua','quality_status.lua','window-size-position.lua'])
        api=vk if backend=='vulkan' else runpy.run_path(str(root/'tools/gpu-readback.py'))
        p,probe=api['create_player'](['--config-dir='+str(cfg),'--gpu-api='+backend,'--hwdec=no','--ao=null','--pause=yes','--sid=no','--geometry=256x256','--autofit=256x256','--autofit-smaller=256x256','--loop-file=inf',str(media)],'followup-'+name+'-'+backend)
        try:
            p.wait_video();test['wait'](p,lambda s:s['mode']=='sdr-acm')
            f=probe.read(p)
            values.append([f.pixel(i%4*64+32,i//4*64+32)[:3] for i in range(16)])
            assert f.meta['format']==10
            if backend=='vulkan':floating(f)
        finally:probe.close();p.close()
    errors=[abs(a-b) for before,after in zip(values[0],values[1]) for a,b in zip(before,after)]
    assert all(e<=.00125+.002*abs(v) for before,after in zip(values[0],values[1]) for v,e in zip(before,[abs(a-b) for a,b in zip(before,after)])),(name,values,errors)
    rows.append({'test':name+' → 实际 SDR ACM 两后端对照','max_difference':max(errors),'values':values})
    print('PASS',name,'→ SDR',max(errors),flush=True)
(out/'vulkan-color.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
