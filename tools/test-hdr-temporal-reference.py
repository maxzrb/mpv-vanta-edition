"""默认峰值IIR、渐变、明暗切换的逐帧独立参考；无seek推进，不拟合GPU曲线。"""
import hashlib, json, math, os, runpy, struct, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/gamut-general-20261012';OUT.mkdir(parents=True,exist_ok=True)
os.environ['MPV_PIPELINE_OUT']=str(OUT)
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));t['EXCLUDED'].remove('color-range-fix.lua')
r=runpy.run_path(str(ROOT/'tools/color-map-reference.py'))
a=runpy.run_path(str(ROOT/'tools/test-hdr-adaptive-reference.py'))
os.environ['MPV_PIPELINE_OUT']=str(OUT)
PEAKS=[500]*4+list(range(510,601,10))+[500]*3+[4000]*3+[0]*3+[100]*4+[500]*4
LEVELS=[0,.01,.05,.1,.2,.3,.4,.5,.6,.65,.7,.75,.8,.85,.9,1]


def fixture():
    frames=[];encoded=[]
    for peak in PEAKS:
        codes=[round(r['pq'](peak*v/10000)*219*256+16*256) for v in LEVELS]
        rows=[struct.pack('<H',code)*64 for code in codes]
        y=b''.join(b''.join(rows[row*4:row*4+4])*64 for row in range(4))
        frames.append(y+struct.pack('<H',32768)*(256*256*2))
        encoded.append([[(v-4096)/(219*256)]*3 for v in codes])
    raw=b''.join(frames);path=OUT/'hdr-temporal.mkv';source=OUT/'hdr-temporal.yuv';source.write_bytes(raw)
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y',
        '-f','rawvideo','-pixel_format','yuv444p16le','-video_size','256x256','-framerate','24',
        '-color_range','tv','-colorspace','bt2020nc','-color_primaries','bt2020','-color_trc','smpte2084',
        '-i',str(source),'-c:v','ffv1','-threads','1','-pix_fmt','yuv444p16le',
        '-color_range','tv','-colorspace','bt2020nc','-color_primaries','bt2020','-color_trc','smpte2084',str(path)],
        check=True,timeout=30)
    decoded=subprocess.check_output([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-threads','1',
        '-i',str(path),'-pix_fmt','yuv444p16le','-f','rawvideo','-'],timeout=20)
    assert decoded==raw
    return path,encoded,frames,hashlib.sha256(raw).hexdigest()


def measured_scene(rgb):
    if not any(max(v)>0 for v in rgb):
        return {key:1e-6 for key in ('average_pq','maximum_pq','scene_average_pq','max_y_pq')}|{'active_blocks':0}
    scene=a['scene_measure'](rgb,99.995003)
    ys=[sum(x*y for x,y in zip((.2627,.6780,.0593),v)) for v in rgb]
    max_y=max(int(16383*r['pq'](v/10000)*r['smooth'](0,.01,r['pq'](v/10000))) for v in ys)/16383
    return dict(average_pq=scene['average_pq'],maximum_pq=scene['maximum_pq'],
        scene_average_pq=r['pq'](scene['scene_average']/10000),max_y_pq=max_y,active_blocks=scene['active_blocks'])


def update(previous,current):
    keys=('average_pq','maximum_pq','scene_average_pq','max_y_pq')
    if previous is None:return {key:current[key] for key in keys},1
    # 先去一个PQ统计单位以内的抖动，再IIR，最后按活跃工作组比例作场景滞回。
    values={key:previous[key] if abs(current[key]-previous[key])<1/16383 else current[key] for key in keys}
    coeff=1-math.exp(-1/20)
    state={key:previous[key]+coeff*(values[key]-previous[key]) for key in keys}
    delta=current['active_blocks']/16*abs(values['average_pq']-state['average_pq'])
    mix=r['smooth'](.01,.03,delta)
    return {key:r['mix'](state[key],values[key],mix) for key in keys},mix


def half(value):
    bits=struct.unpack('<H',struct.pack('<e',value))[0]
    if struct.unpack('<e',struct.pack('<H',bits))[0]>value:bits-=1
    return struct.unpack('<e',struct.pack('<H',bits))[0]


def trial(media,encoded,frames,source_hash,backend):
    cfg=t['output']['create_config']('hdr-temporal-'+backend,exclude_scripts=t['EXCLUDED'])
    p,probe=t['pipeline']['create_player'](['--config-dir='+str(cfg),'--gpu-api='+backend,'--hwdec=no',
        '--pause=yes','--ao=null','--script-opts-append=color-target-pipeline=hq','--sid=no','--osd-level=0','--osd-bar=no','--osd-on-seek=no','--osc=no',
        '--gpu-shader-cache=no','--geometry=256x256','--autofit=256x256','--autofit-smaller=256x256',
        '--loop-file=no',str(media)],'hdr-temporal-'+backend,backend)
    try:
        p.wait_video()
        p.command('set_property','user-data/display-info',{'uid':'temporal-software','hdr-status':'off',
            'hdr-supported':False,'max-luminance':80,'min-luminance':0})
        p.command('set_property','user-data/display-color',{'mode':'wcg','identity':'temporal-software','sdr_white_nits':80})
        t['output']['wait'](p,lambda s:s['mode']=='sdr-acm')
        p.command('set_property','target-contrast','inf')
        time.sleep(.3)
        options={key:p.get('options/'+key) for key in ('hdr-compute-peak','hdr-peak-decay-rate',
            'hdr-scene-threshold-low','hdr-scene-threshold-high','allow-delayed-peak-detect','hdr-peak-percentile')}
        assert options['hdr-peak-decay-rate']==20 and options['hdr-scene-threshold-low']==1 and options['hdr-scene-threshold-high']==3
        assert options['allow-delayed-peak-detect'] is False
        state=None;results=[]
        for index,values in enumerate(encoded):
            rows=probe.read(p,advance_frame=index>0)
            assert abs((p.get('time-pos') or 0)-index/24)<.022,('逐帧时间不一致',index,p.get('time-pos'))
            source=[row for row in rows if row[0]['phase']=='input' and row[0]['format']==56 and row[0]['width']==256]
            assert len(source)==3
            for plane,(meta,data) in enumerate(source):
                raw=b''.join(data[y*meta['stride']:y*meta['stride']+512] for y in range(256))
                assert raw==frames[index][plane*131072:(plane+1)*131072]
            scene=measured_scene([[r['unpq'](v)*10000 for v in rgb] for rgb in values])
            previous=state;state,mix=update(state,scene)
            reference_scene=dict(average_pq=state['average_pq'],maximum_pq=state['maximum_pq'],
                scene_average=r['unpq'](state['scene_average_pq'])*10000)
            # 峰值统计用写回前源值；映射消费编码域FP16向零写回后的值。
            rendered=[[r['unpq'](half(v))*10000 for v in rgb] for rgb in values]
            expected=[a['reference'](v,reference_scene,256)[0] for v in rendered]
            final=rows[-1];assert final[0]['format']==10
            actual=[t['pixel'](final,i%4*64+32,i//4*64+32) for i in range(16)]
            error=max(abs(x-y) for av,bv in zip(actual,expected) for x,y in zip(av,bv))
            previous_error=None
            if previous is not None:
                delayed=dict(average_pq=previous['average_pq'],maximum_pq=previous['maximum_pq'],
                    scene_average=r['unpq'](previous['scene_average_pq'])*10000)
                lagged=[a['reference'](v,delayed,256)[0] for v in rendered]
                previous_error=max(abs(x-y) for av,bv in zip(actual,lagged) for x,y in zip(av,bv))
            results.append(dict(frame=index,source_peak=PEAKS[index],scene=scene,smoothed=state,mix=mix,
                max_linear_error=error,previous_frame_peak_error=previous_error,
                actual=actual,reference=expected,source_all_integer_samples_exact=True))
            print(backend,'时序帧',index,'峰值',PEAKS[index],'IIR混合',round(mix,5),'线性误差',error,flush=True)
        result=dict(backend=backend,options=options,source_sha256=source_hash,frames=results,
            seek_only_before_sequence=True,all_frames_passed=all(v['max_linear_error']<.002 for v in results))
        assert results[17]['previous_frame_peak_error']>.01,'亮场突切须能排除上一帧峰值模型'
        manifest=probe.script.exports_sync.status()
        if backend=='vulkan':
            assert manifest['shader_types'] and all(s['float_widths']==[32] and not s['relaxed_float_decorations'] and not s['relaxed_unknown_decorations'] for s in manifest['shader_types'])
        else:
            shaders=[meta for meta,data in rows if meta.get('shader')]
            assert shaders and all(meta.get('shader_ir') and 'min16' not in meta['shader_ir'] for meta in shaders)
        result['compiled_float32_verified']=True
        return result
    finally:p.close();probe.close()


def main():
    media,encoded,frames,source_hash=fixture();results=[]
    for backend in ('d3d11','vulkan'):
        results.append(trial(media,encoded,frames,source_hash,backend))
        (OUT/'temporal-hdr-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(v['all_frames_passed'] for v in results):raise SystemExit(1)


if __name__=='__main__':main()
