"""自动范围校正的真实硬解、420 色度、外部改链和暂停切片验证。"""
import json,os,runpy,struct,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ['MPV_PIPELINE_OUT']=str(ROOT/'tmp/modernization/color-range-fix-20261011')
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']
t['EXCLUDED'].remove('color-range-fix.lua')


def wait(p,predicate):
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if predicate():return
        time.sleep(.05)
    raise AssertionError((p.get('user-data/color-range-fix'),p.get('vf'),p.get('video-out-params')))


def hardware():
    media,encoded=t['fixtures']['fixture']('hardware-source',10,1,True,False)
    raw=(OUT/'hardware-source.yuv').read_bytes();plane=65536*2
    down=raw[:plane]
    for n in (1,2):
        down+=b''.join(raw[n*plane+(y*256+x)*2:n*plane+(y*256+x)*2+2] for y in range(0,256,2) for x in range(0,256,2))
    path=OUT/'full420-10.yuv';path.write_bytes(down*48);target=OUT/'full420-10.mkv'
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y','-f','rawvideo',
        '-pixel_format','yuv420p10le','-video_size','256x256','-framerate','24','-color_range','pc',
        '-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1','-i',str(path),
        '-c:v','libx265','-threads','1','-x265-params','pools=none:frame-threads=1:wpp=0:lossless=1:range=full:log-level=error',
        '-color_range','pc','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1',str(target)],check=True,timeout=60)
    decoded=subprocess.check_output([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-threads','1',
        '-i',str(target),'-frames:v','1','-pix_fmt','yuv420p10le','-color_range','pc','-f','rawvideo','-'],timeout=20)
    assert decoded==down,'HEVC 夹具必须无损编码'
    expected=[[t['output']['sdr_linear'](v) for v in rgb] for rgb in encoded]
    results=[]
    for backend in ('d3d11','vulkan'):
        route='d3d11va' if backend=='d3d11' else 'd3d11va-copy'
        rows,status=t['capture'](target,'hardware-full420',backend,extra_args=['--hwdec='+route],force_redraw=True)
        assert status['validation_hwdec']==route,status
        post=status['validation_filtered'];fix=status['validation_range_fix']
        assert fix['active'] and fix['state']=='已校正'
        assert post['pixelformat']=='yuv420p16' and post['colorlevels']=='limited',post
        actual=[t['pixel'](rows[-1],i%4*64+32,i//4*64+32) for i in range(16)]
        error=max(abs(a-b) for rgb,target in zip(actual,expected) for a,b in zip(rgb,target))
        assert error<.00125,(backend,error)
        results.append(dict(backend=backend,hwdec=status['validation_hwdec'],output=post,max_linear_error=error,fix=fix))
        print('PASS 硬解',backend,error,flush=True)
    return results


def lifecycle():
    media,_=t['fixtures']['fixture']('lifecycle-full',12,1,True,False)
    limited,_=t['fixtures']['fixture']('lifecycle-limited',10,1,False,False)
    cfg=t['output']['create_config']('range-life',exclude_scripts=t['EXCLUDED'])
    p=t['pipeline']['api']['Player'](['--config-dir='+str(cfg),'--hwdec=no','--gpu-api=d3d11',
        '--ao=null','--pause=yes','--loop-file=inf','--geometry=256x256',str(media)],'range-life')
    try:
        p.wait_video();wait(p,lambda:(p.get('user-data/color-range-fix') or {}).get('state')=='已校正')
        mine=p.get('vf')[-1]
        user={'name':'lavfi','label':'user-transform','params':{'graph':'null','o':'threads=1'}}
        p.command('set_property','vf',[user,mine])
        wait(p,lambda:len(p.get('vf'))==2 and (p.get('user-data/color-range-fix') or {}).get('state')=='已校正')
        assert p.get('vf')[0]['label']=='user-transform' and p.get('vf')[-1]['label']=='color-full-range'
        mine=p.get('vf')[-1];user['params']['graph']='format=rgb48le'
        p.command('set_property','vf',[user,mine])
        wait(p,lambda:p.get('video-out-params')['pixelformat']=='rgb48' and len(p.get('vf'))==1)
        assert p.get('vf')[0]['label']=='user-transform'
        user['params']['graph']='null';p.command('set_property','vf',[user])
        wait(p,lambda:(p.get('user-data/color-range-fix') or {}).get('state')=='已校正')
        p.command('set_property','vf',[p.get('vf')[0]])
        wait(p,lambda:(p.get('user-data/color-range-fix') or {}).get('state')=='外部已接管')
        p.command('seek',1,'absolute+exact');time.sleep(.2)
        assert p.get('pause') and len(p.get('vf'))==1 and not p.get('user-data/color-range-fix')['active']
        p.command('loadfile',str(limited));p.wait_video()
        wait(p,lambda:p.get('path')==str(limited) and p.get('video-params')['colorlevels']=='limited'
             and not p.get('user-data/color-range-fix')['active'])
        assert not p.get('user-data/color-range-fix')['active'] and p.get('pause')
        p.command('loadfile',str(media));p.wait_video()
        wait(p,lambda:p.get('path')==str(media) and (p.get('user-data/color-range-fix') or {}).get('state')=='已校正')
        assert p.get('pause')
        p.command('seek',1,'absolute+exact');time.sleep(.2)
        assert abs(p.get('time-pos')-1)<.1 and p.get('pause')
        for _ in range(3):
            previous=p.get('user-data/color-range-fix')['generation']
            p.command('loadfile',str(media))
            wait(p,lambda:(p.get('user-data/color-range-fix') or {}).get('generation',0)>previous
                 and p.get('user-data/color-range-fix')['state']=='已校正')
            assert p.get('pause')
        print('PASS 改链／RGB旁路／用户删除／暂停跳转／切片重新校正',flush=True)
        return {'external_chain_preserved':True,'rgb_bypassed':True,'manual_removal_respected':True,'pause_seek_file_change':True,'same_file_reloads':3}
    finally:p.close()


def main():
    results={'hardware':hardware(),'lifecycle':lifecycle()}
    (OUT/'integration-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
