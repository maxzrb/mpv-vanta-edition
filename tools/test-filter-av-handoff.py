"""隔离实际音视频验证滤镜交接、组合、缺后端回退和精度详情；不是性能推广采样。"""
import json
from pathlib import Path
import runpy
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/filter-handoff'
helpers=runpy.run_path(str(ROOT/'tools/benchmark-filter-handoff.py'))
Player,enable,wait,sample=[helpers[k] for k in ['Player','enable','wait','sample']]
create_config=helpers['create_config']


def main():
    rows=[]
    for route in ['d3d11va','d3d11va-copy']:
        config=create_config('filter-av-handoff')
        p=Player(['--config-dir='+str(config),'--hwdec='+route,'--ao=wasapi','--mute=yes',
            '--geometry=1920x1080','--input-cursor=no','--input-vo-keyboard=no',
            '--input-media-keys=no',str(OUT/'rife-dml-426.mkv')],'filter-av-'+route)
        try:
            p.wait_video()
            wait(p,lambda: p.get('hwdec-current')==route,20)
            wait(p,lambda: bool(p.get('audio-out-params')),20)
            assert p.get('audio-out-params'), '夹具必须有实际音频输出'
            for name,preset,group in [('svp','svp','memc'),('ccd+svp','ccd','denoise'),
                                      ('ccd+rife','rife-dml-426','memc')]:
                enable(p,preset,group)
                time.sleep(5)
                row=sample(p,5,name)
                assert .97<row['clock_ratio']<1.03 and not any(row['counters'].values()),row
                assert row['audio'] and p.get('hwdec-current')==route
                p.command('set_property','user-data/quality-status',{})
                p.command('script-message','show-color-status')
                wait(p,lambda: (p.get('user-data/quality-status') or {}).get('view')=='quality-details')
                titles=[item['title'] for item in p.get('user-data/quality-status')['items']]
                assert any('整数 10bit [p010]' in title for title in titles),'硬解源必须显示有效10bit'
                assert any(('复制到系统内存' if route.endswith('-copy') else '下载帧供 VS 处理') in title for title in titles)
                assert any('不能由最终输出推断' in title for title in titles)
                p.command('script-message-to','uosc','close-menu')
                rows.append(dict(route=route,case=name,playback=row,precision=titles[:9]))
            active=p.get('user-data/quality')['active']
            p.command('script-message','quality-select','rife-std')
            deadline=time.monotonic()+20
            while (p.get('user-data/quality') or {}).get('state')!='失败' and time.monotonic()<deadline:
                time.sleep(.1)
            state=p.get('user-data/quality')
            assert state['state']=='失败' and 'rife' in state['error'] and state['active']==active,state
            time.sleep(5)
            rollback=sample(p,5,'rollback')
            assert .97<rollback['clock_ratio']<1.03 and not any(rollback['counters'].values())
            assert rollback['audio'] and p.get('hwdec-current')==route
            p.command('set_property','pause',True)
            p.command('seek',5,'absolute+exact')
            time.sleep(.5)
            assert p.get('pause') and abs(p.get('time-pos')-5)<.15
            p.command('loadfile',str(OUT/'rife-dml-426.mkv'))
            p.wait_video()
            wait(p,lambda: not p.get('vf'))
            assert not p.get('user-data/quality')['active'] and p.get('pause')
            rows.append(dict(route=route,case='missing-std-rollback+seek+file-change',playback=rollback))
        finally:p.close()
        log=p.log.read_text(encoding='utf-8',errors='replace')
        assert 'Lua error:' not in log
        assert not any(token in log for token in ['prepare_filter.py','capabilities.py','component_inventory','--probe-frames'])
        for row in [r for r in rows if r['route']==route]:
            phase=row['case'].split('+seek')[0]
            if phase=='missing-std-rollback':phase='rollback'
            collecting=False;events=0
            for line in log.splitlines():
                if 'test-handoff-phase' in line and '"'+phase+'-start"' in line:collecting=True
                elif 'test-handoff-phase' in line and '"'+phase+'-end"' in line:collecting=False
                elif collecting and 'Audio device underrun detected.' in line:events+=1
            row['playback']['audio_underrun_events']=events
            assert events==0,row
        print('PASS',route,'音频／CCD+SVP／CCD+RIFE／STD失败回退／暂停跳转切集／精度详情',flush=True)
    (OUT/'av-handoff.json').write_text(json.dumps(dict(
        scope='640×360 HEVC10+AAC，预热后5秒兼容回归，非三轮20秒性能结论',trials=rows),
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
