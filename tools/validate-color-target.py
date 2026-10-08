"""五类素材的色彩状态与实际输出验证；模拟 HDR 只检验软件协商。"""
import json,time,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
Player=runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
OUT=ROOT/'tmp/modernization/validation'
def wait(p,key,predicate,seconds=8):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        value=p.get(key)
        if predicate(value):return value
        time.sleep(.1)
    raise AssertionError((key,p.get(key)))
def main():
    rows=[]
    args=['--no-config','--vo=gpu-next','--gpu-api=d3d11','--hwdec=auto-safe','--ao=null','--pause=yes',
        '--target-prim=bt.709','--target-trc=srgb','--d3d11-output-csp=srgb','--hdr-contrast-recovery=0',
        '--script='+str(ROOT/'portable_config/scripts/color-target.lua'),
        '--script='+str(ROOT/'portable_config/scripts/quality_status.lua')]
    for source in ['sdr8','quality-sdr10','wide-sdr','hdr10','hlg']:
        p=Player([*args,str(OUT/(source+'.mkv'))],'color-target-'+source)
        try:
            p.wait_video()
            s=wait(p,'user-data/color-target',lambda s:s and s['mode']=='sdr')
            before=p.get('video-params')
            assert s['requested']=='auto' and not s['manual']
            assert p.get('video-target-params')['gamma']=='srgb'
            p.command('set_property','target-trc','gamma2.4')
            wait(p,'user-data/color-target',lambda s:s['status']=='外部覆盖')
            p.command('script-message','color-select','sdr')
            wait(p,'target-trc',lambda t:t=='srgb')
            p.command('script-message','color-select','hdr')
            s=wait(p,'user-data/color-target',lambda s:s['mode']=='sdr' and 'HDR' in s['reason'])
            assert p.get('target-trc')=='srgb'
            p.command('set_property','target-contrast','1234');time.sleep(.2)
            p.command('script-message','color-select','restore');time.sleep(.3)
            assert str(p.get('target-contrast'))=='1234'
            assert p.get('video-params')==before
            p.command('script-message','color-status')
            rows.append({'source':source,'source_params':before,'state':s,'passed':True})
        finally:p.close()
        log=p.log.read_text(encoding='utf-8',errors='replace')
        assert 'Lua error:' not in log
    p=Player([*args,str(OUT/'hdr10.mkv')],'color-target-fixture')
    try:
        p.wait_video()
        vid,pause,position=p.get('vid'),p.get('pause'),p.get('time-pos')
        fixture={'hdr-status':'on','hdr-supported':'true','max-luminance':'1000','min-luminance':'0.01','uid':'fixture','bit-depth':10}
        p.command('set_property','user-data/display-info',fixture)
        s=wait(p,'user-data/color-target',lambda s:s['mode']=='hdr-scrgb')
        target=p.get('video-target-params')
        assert target['gamma']=='scrgb' and target['pixelformat']=='rgba16hf'
        assert p.get('vid')==vid and p.get('pause')==pause and abs(p.get('time-pos')-position)<.1
        p.command('loadfile',str(OUT/'hdr10.mkv'));time.sleep(.5);p.wait_video()
        wait(p,'user-data/color-target',lambda s:s['mode']=='hdr-scrgb')
        p.command('set_property','target-trc','gamma2.4')
        wait(p,'user-data/color-target',lambda s:s['status']=='外部覆盖')
        p.command('set_property','user-data/display-info',{**fixture,'max-luminance':'1200'})
        time.sleep(.3);assert p.get('target-trc')=='gamma2.4'
        p.command('script-message','color-select','auto')
        wait(p,'user-data/color-target',lambda s:s['mode']=='hdr-scrgb' and not s['manual'])
        p.command('set_property','user-data/display-info',{**fixture,'hdr-supported':False})
        wait(p,'user-data/color-target',lambda s:s['mode']=='sdr')
        assert p.get('vid')==vid and p.get('pause')==pause
        rows.append({'source':'模拟 HDR 能力，非 HDR 面板验收','state':s,'target':target,'passed':True})
    finally:p.close()
    log=p.log.read_text(encoding='utf-8',errors='replace')
    assert 'Lua error:' not in log
    (OUT/'color-target-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS 五类实际素材／外部覆盖／主动重选／自动恢复／模拟 HDR 输出')
if __name__=='__main__':main()
