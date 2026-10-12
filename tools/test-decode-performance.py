"""验证12-bit 4:4:4 AV1的自动软解事务、精确跳转和手动解码选择。"""
import json,runpy,time,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'tmp/modernization/performance-lossless-20261010'
out.mkdir(parents=True,exist_ok=True)
Player=runpy.run_path(str(root/'tools/validate-modernization.py'))['Player']
config=runpy.run_path(str(root/'tools/isolated-config.py'))['create_config']('performance-lifecycle',exclude_scripts=['window-size-position.lua'])
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('media',type=Path)
args=parser.parse_args()
media=args.media.resolve()
p=Player(['--config-dir='+str(config),'--pause=yes','--start=10','--volume=0','--sid=no','--geometry=1280x720',str(media)],'performance-auto-lifecycle')
rows=[]
def wait(pred):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if pred():return
        time.sleep(.1)
    raise AssertionError({'status':p.get('user-data/decode-performance'),'options':p.get('vd-lavc-o'),'params':p.get('video-params')})
def state(name):
    row={'phase':name,**{k:p.get(k) for k in ['path','time-pos','hwdec','hwdec-current','vd-lavc-threads','vd-lavc-o','video-params','user-data/decode-performance']}}
    rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
try:
    wait(lambda:(p.get('user-data/decode-performance') or {}).get('frame_delay') is not None)
    state('auto-fallback');assert rows[-1]['video-params']['pixelformat']=='yuv444p12'
    assert rows[-1]['hwdec-current']=='no' and int(rows[-1]['vd-lavc-o']['max_frame_delay'])==rows[-1]['user-data/decode-performance']['frame_delay']
    p.command('seek',25,'absolute+exact');wait(lambda:not p.get('seeking') and 24.9<(p.get('time-pos') or 0)<25.1)
    state('seek');assert rows[-1]['vd-lavc-o']==rows[0]['vd-lavc-o']
    small=root/'tmp/modernization/validation/compat-hevc10.mkv'
    assert small.exists(),small
    p.command('loadfile',str(small),'replace',-1,{'start':'0'})
    wait(lambda:(p.get('path') or '')==str(small) and (p.get('video-params') or {}).get('pixelformat') is not None)
    state('hevc');assert rows[-1]['vd-lavc-o']=={} and rows[-1]['vd-lavc-threads']==0
    p.command('loadfile',str(media),'replace')
    wait(lambda:(p.get('user-data/decode-performance') or {}).get('frame_delay') is not None)
    state('reload')
    log_offset=len(p.log.read_text(encoding='utf-8'))
    p.command('script-message','decode-performance-hwdec','no')
    wait(lambda:'playback restart complete @' in p.log.read_text(encoding='utf-8')[log_offset:] and p.get('hwdec-current')=='no' and (p.get('vd-lavc-o') or {}).get('max_frame_delay') is not None and p.get('time-pos') is not None)
    state('manual-soft')
    subtitle=out/'external-lifecycle.srt'
    subtitle.write_text('1\n00:00:00,000 --> 00:01:30,000\n字幕保留验证\n',encoding='utf-8')
    p.command('sub-add',str(subtitle),'select')
    selected=p.get('sid')
    p.command('loadfile',str(small),'append')
    playlist=[t['filename'] for t in p.get('playlist')]
    p.command('set_property','file-local-options/vf',[])
    log_offset=len(p.log.read_text(encoding='utf-8'))
    p.command('script-message','decode-performance-hwdec','no')
    wait(lambda:'playback restart complete @' in p.log.read_text(encoding='utf-8')[log_offset:] and (p.get('vd-lavc-o') or {}).get('max_frame_delay') is not None and p.get('sid')==selected and not p.get('seeking'))
    assert [t['filename'] for t in p.get('playlist')]==playlist
    assert p.get('option-info/vf/set-locally') is True and p.get('pause') is True
    assert any(t.get('external-filename')==str(subtitle) and t.get('selected') for t in p.get('track-list'))
    state('playlist-external-subtitle-preserved')
    p.command('loadfile',str(small),'replace',-1,{'start':'0'})
    wait(lambda:(p.get('path') or '')==str(small) and 'no' in (p.get('hwdec') or []) and (p.get('video-params') or {}).get('pixelformat')=='yuv420p10')
    state('manual-soft-next-file')
    p.command('script-message','decode-performance-hwdec','auto-safe')
    wait(lambda:p.get('hwdec-current')=='d3d11va')
    state('manual-hardware')
finally:p.close()
log=p.log.read_text(encoding='utf-8')
assert 'Lua error:' not in log and "AVOption 'max_frame_delay' not found" not in log
assert 'No frames available to take screenshot' not in log
assert 'Error while decoding frame!' not in log
(out/'lifecycle.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
shutil.copy2(p.log,out/'lifecycle.log')
print('PASS automatic fallback, seek, HEVC restoration, reload, screenshot readiness',flush=True)
