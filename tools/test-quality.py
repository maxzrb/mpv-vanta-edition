"""一次选择真实播放回归；普通流程必须没有组件扫描与模拟试跑进程。"""
import json,time,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
Player=runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
OUT=ROOT/'tmp/modernization/validation'
def state(p):return p.get('user-data/quality') or {}
def enable(p,preset):
    assert p.command('script-message','quality-select',preset)['error']=='success'
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        s=state(p)
        if s.get('state')=='失败':raise AssertionError(s)
        if s.get('state')=='已添加':return s
        time.sleep(.2)
    raise AssertionError(state(p))
def main():
    p=Player(['--no-config','--vo=gpu-next','--gpu-api=d3d11','--hwdec=auto-safe','--ao=null',
        '--loop-file=inf','--geometry=640x360','--script='+str(ROOT/'portable_config/scripts/quality.lua'),
        str(OUT/'quality-sdr10.mkv')],'quality-one-click')
    rows=[]
    try:
        p.wait_video();p.command('script-message','quality-menu','memc')
        for id in ['mvt','rife-dml','rife-dml-426','rife-dml-heavy','drba-dml','svp','ccd']:
            p.command('script-message','quality-reset');time.sleep(.2);s=enable(p,id);time.sleep(2)
            t0=p.get('time-pos');time.sleep(1);t1=p.get('time-pos')
            assert t1>t0,(id,t0,t1)
            rows.append({'id':id,'state':s,'fps':p.get('estimated-vf-fps'),'output':p.get('video-out-params')})
        p.command('script-message','quality-reset');enable(p,'rife-dml-426')
        # 无 STD 后端必须实际报错，恢复此前有效 DML 链。
        p.command('script-message','quality-select','rife-std')
        deadline=time.monotonic()+15
        while state(p)['state']!='失败' and time.monotonic()<deadline:time.sleep(.1)
        assert state(p)['state']=='失败' and 'rife' in state(p)['error']
        assert state(p)['active']['memc']=='rife-dml-426'
        rows.append({'id':'rife-std','expected_failure':state(p)})
        enable(p,'uai-dml')
        assert state(p)['active']['memc']=='rife-dml-426'
        deadline=time.monotonic()+30
        while p.get('video-out-params')['w']!=640 and time.monotonic()<deadline:time.sleep(.2)
        assert p.get('video-out-params')['w']==640
        enable(p,'ccd');enable(p,'artcnn')
        labels=[f.get('label') for f in p.get('vf')]
        assert labels==['quality-denoise','quality-upscale','quality-memc'],labels
        assert [stage['group'] for stage in state(p)['chain']]==['denoise','upscale','memc']
        assert p.get('glsl-shaders')
        # 首次初始化结束后确认组合持续按正常时钟推进，而非仅有滤镜列表。
        t0=p.get('time-pos');start=time.monotonic();duration=p.get('duration')
        advance=0;last=t0
        while time.monotonic()-start<20:
            time.sleep(.5);now=p.get('time-pos');delta=now-last
            if delta<-.5:delta+=duration
            advance+=max(0,delta);last=now
        assert .9<advance/(time.monotonic()-start)<1.1,advance
        p.command('seek',5,'absolute+exact');time.sleep(1)
        assert p.get('time-pos')>=5
        rows.append({'id':'denoise+upscale+memc+shader','state':state(p),'output':p.get('video-out-params')})
        p.command('loadfile',str(OUT/'hdr10.mkv'));time.sleep(1);p.wait_video()
        assert not p.get('vf') and not state(p)['active']
        enable(p,'artcnn');assert state(p)['warning'] and p.get('glsl-shaders')
        rows.append({'id':'hdr-warning-only','state':state(p)})
        p.command('script-message','quality-reset')
        p.command('loadfile',str(OUT/'compat-hevc10.mkv'));time.sleep(1);p.wait_video()
        assert p.get('hwdec-current')=='d3d11va'
        enable(p,'mvt');time.sleep(2)
        assert p.get('video-out-params') and p.get('hwdec-current')=='d3d11va'
        rows.append({'id':'direct-hwdec+cpu-filter','fps':p.get('estimated-vf-fps')})
    finally:p.close()
    text=p.log.read_text(encoding='utf-8',errors='replace')
    assert not any(x in text for x in ['prepare_filter.py','capabilities.py','component_inventory','--probe-frames'])
    assert 'Run command: subprocess,' not in text,'起播、菜单或滤镜选择启动了子进程'
    assert not any('Lua error:' in x for x in text.splitlines())
    (OUT/'quality-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS',len(rows),'一次启用／DML／MVT／SVP／组合／失败恢复／HDR 提示／无预检子进程')
if __name__=='__main__':main()
