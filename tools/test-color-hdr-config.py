"""完整配置 HDR 元数据与静态滤镜像素回归，模拟输出不改变系统 HDR。"""
import json
from pathlib import Path
import runpy
import time

ROOT=Path(__file__).resolve().parents[1]
t=runpy.run_path(str(ROOT/'tools/test-color-config.py'))
OUT=t['OUT']


def snapshot(p,name):
    path=OUT/(name+'.png')
    assert p.command('screenshot-to-file',str(path),'video')['error']=='success'
    w,h,channels,rows=t['read_png'](path)
    assert (w,h)==(256,256)
    return [rows[y*64+32][(x*64+32)*channels+c] for y in range(4) for x in range(4) for c in range(3)]


def main():
    rows=[]
    for name,transfer,gamma in [('hdr10','smpte2084','pq'),('hlg','arib-std-b67','hlg')]:
        media,_=t['fixture']('color-config-'+name,10,9,False,True,frames=960,transfer=transfer)
        config=t['create_config']('color-hdr',exclude_scripts=['display-color.lua'])
        # 隔离副本中暂停真实显示检测，防止 VO 重建把模拟能力立即覆盖回 SDR。
        detector=config/'scripts/display-info.dll'
        if detector.exists():
            assert (ROOT/'tmp/modernization/isolated').resolve() in detector.resolve().parents
            detector.rename(detector.with_suffix('.dll.disabled'))
        p=t['Player'](['--config-dir='+str(config),'--ao=null','--hwdec=no',
            '--input-cursor=no','--input-vo-keyboard=no','--input-media-keys=no','--terminal=no',
            '--screenshot-sw=no','--screenshot-format=png','--screenshot-high-bit-depth=yes',str(media)],
            'color-config-'+name)
        try:
            p.wait_video()
            time.sleep(1)
            source=p.get('video-params')
            assert source['gamma']==gamma and source['primaries']=='bt.2020' and source['colorlevels']=='limited'
            baseline=snapshot(p,name+'-sdr-baseline')
            p.command('script-message','quality-select','ccd')
            t['wait_added'](p,'denoise','ccd')
            time.sleep(1)
            after=snapshot(p,name+'-sdr-ccd')
            error=max(abs(a-b) for a,b in zip(baseline,after))
            assert error<=128,(name,error)
            output=p.get('video-out-params')
            for key in ['gamma','primaries','colormatrix','colorlevels']:
                assert output[key]==source[key],(name,key,output)
            p.command('script-message','quality-select','rife-dml-426')
            t['wait_added'](p,'memc','rife-dml-426')
            time.sleep(1)
            combined=snapshot(p,name+'-sdr-ccd-rife')
            combo_error=max(abs(a-b) for a,b in zip(baseline,combined))
            assert combo_error<=128,(name,combo_error)
            before_hdr=p.get('time-pos')
            # 仅注入软件能力，实际 Windows HDR 始终保持原状态。
            fixture={'uid':'software-color-hdr','hdr-status':'on','hdr-supported':True,
                'max-luminance':'1000','min-luminance':'0.01','bit-depth':10}
            p.command('set_property','user-data/display-info',fixture)
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                target=p.get('video-target-params') or {}
                if target.get('gamma')=='scrgb' and target.get('pixelformat')=='rgba16hf':
                    break
                time.sleep(.1)
            else:
                raise AssertionError(p.get('user-data/color-target'))
            time.sleep(.5)
            assert p.get('user-data/quality')['active']['memc']=='rife-dml-426'
            deadline=time.monotonic()+12
            while time.monotonic()<deadline and p.get('time-pos')<=before_hdr:
                time.sleep(.2)
            assert p.get('pause') is False and p.get('time-pos')>before_hdr,{
                'pause':p.get('pause'),'before':before_hdr,'after':p.get('time-pos'),
                'quality':p.get('user-data/quality'),'color':p.get('user-data/color-target')}
            hdr_target=p.get('video-target-params')
            assert hdr_target['gamma']=='scrgb' and hdr_target['pixelformat']=='rgba16hf',hdr_target
            p.command('set_property','user-data/quality-status',{})
            p.command('script-message','show-color-status')
            deadline=time.monotonic()+5
            while time.monotonic()<deadline and not (p.get('user-data/quality-status') or {}).get('items'):
                time.sleep(.1)
            titles=[item['title'] for item in p.get('user-data/quality-status')['items']]
            precision_target=next(title for title in titles if title.startswith('渲染目标：'))
            assert '浮点存储 16bit [rgba16hf]' in precision_target,precision_target
            assert any('不能由最终输出推断' in title for title in titles)
            p.command('script-message-to','uosc','close-menu')
            p.command('set_property','user-data/display-info',{**fixture,'hdr-status':'off'})
            deadline=time.monotonic()+8
            while time.monotonic()<deadline and (p.get('video-target-params') or {}).get('gamma')!='srgb':
                time.sleep(.1)
            assert p.get('video-target-params')['gamma']=='srgb'
            rows.append(dict(source=name,gamma=gamma,hdr_to_sdr_ccd_max_code_difference=error,
                hdr_to_sdr_combination_max_code_difference=combo_error,source_params=source,
                simulated_hdr_target=hdr_target,precision_target=precision_target,passed=True))
        finally:p.close()
        log=p.log.read_text(encoding='utf-8',errors='replace')
        assert 'No PTS after filter' not in log and 'Script evaluation failed' not in log and 'Lua error:' not in log
        print('PASS',name,'静态HDR→SDR差异',error,combo_error,'模拟scRGB／恢复SDR')
    (OUT/'color-hdr-config-results.json').write_text(json.dumps(dict(
        scope='完整配置静态HDR像素一致性与真实输出协商；隔离副本暂停显示检测并模拟能力，非面板测量',trials=rows),
        ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
