"""汇总通用色域表验收；保留所有色块测量、性能计时及输入哈希。"""
import hashlib, json, statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tmp/modernization/gamut-general-20261012'
DOC=ROOT/'docs/modernization';HASHES={}


def load(name):
    path=OUT/name;data=path.read_bytes();HASHES[name]=hashlib.sha256(data).hexdigest()
    return json.loads(data.decode('utf-8'))


def main():
    colors={key:load(f'general-{key}-results.json') for key in ('sdr','hlg','pq','icc')}
    production={key:load(f'production-{key}-results.json') for key in colors}
    metric=next(iter(colors.values()))['metric_test']
    # 每色差均针对连续公式；加密收益/局部误差变化分别报告，不能只选最大值下降。
    color_summary=[]
    for kind,data in colors.items():
        assert len(data['samples'])==1646 and len(data['trials'])==6
        assert all(v['source_all_integer_samples_exact'] and v['gray_luminance_monotonic'] and v['discrete_model_passed'] for v in data['trials'])
        for backend in ('d3d11','vulkan'):
            pair={v['variant']:v for v in data['trials'] if v['backend']==backend}
            default=pair['default'];dense=pair['dense']
            changes=[b-a for a,b in zip(default['delta_e_00_by_sample'],dense['delta_e_00_by_sample'])]
            worst=max(range(len(changes)),key=changes.__getitem__)
            row=dict(kind=kind,backend=backend,default_delta_e_00=default['continuous_delta_e_00'],
                dense_delta_e_00=dense['continuous_delta_e_00'],max_local_error_increase=max(changes),
                max_local_increase_sample=data['samples'][worst],local_increases_over_025=sum(v>.25 for v in changes),
                dense_gray_delta_e_00=dense['by_group']['gray'],dense_gray_max_channel_spread=dense['gray_max_encoded_channel_spread'])
            assert row['dense_delta_e_00']['maximum']<1 and row['local_increases_over_025']==0
            color_summary.append(row)
        for v in production[kind]['trials']:
            assert v['production_default_verified'] and v['source_all_integer_samples_exact'] and v['discrete_model_passed']
            assert v['gray_luminance_monotonic'] and v['continuous_delta_e_00']['maximum']<1
            assert [int(v['options'][key]) for key in ('lut3d_size_I','lut3d_size_C','lut3d_size_h')]==[96,64,256]
    performances={case:load(f'performance-{case}.json') for case in ('grid','4k-soft','4k-hard','real-hlg','real-vvc','real-hevc60')}
    performance_summary=[]
    for case,rows in performances.items():
        assert len(rows)==8
        for v in rows:
            assert v['settings']['vd-lavc-threads']==16 and v['no_gpu_readback_instrumentation']
            assert v['raw_media_clock_advance']>0 and all(value>=0 for value in v['drop_counters'].values())
            assert v['raw_media_clock_advance']*v['settings'].get('container-fps',24)-sum(v['drop_counters'][key] for key in ('frame-drop-count','decoder-frame-drop-count'))-2>=258
        for backend in ('d3d11','vulkan'):
            controls=[v for v in rows if v['backend']==backend]
            def fused(v):return next((p['mean_ns']/1e6 for p in v['gpu_fresh_segments'] if 'gamut map' in p['desc']),None)
            d=[v for v in controls if v['variant']=='default'];n=[v for v in controls if v['variant']=='dense']
            active=fused(d[0]) is not None
            delta=(statistics.mean(fused(v) for v in n)-statistics.mean(fused(v) for v in d))*1000 if active else None
            if active:assert delta<10,('色域表所在融合阶段增量超过10微秒',case,backend,delta)
            performance_summary.append(dict(case=case,backend=backend,gamut_pass_active=active,
                fused_stage_mean_ms_default=[fused(v) for v in d],fused_stage_mean_ms_dense=[fused(v) for v in n],
                fused_stage_mean_delta_microseconds=delta,
                default_drops=[v['drop_counters'] for v in d],dense_drops=[v['drop_counters'] for v in n],
                default_cpu_cores=[v['cpu_cores_used'] for v in d],dense_cpu_cores=[v['cpu_cores_used'] for v in n],
                warm_ready_seconds_default=d[-1]['startup_ready_seconds'],warm_ready_seconds_dense=n[-1]['startup_ready_seconds'],
                warm_cache_sizes_dense=n[-1]['cached_lut_sizes'],
                warm_private_bytes_delta=(n[-1]['memory']['PrivateUsage']-d[-1]['memory']['PrivateUsage']) if 'memory' in n[-1] else None))
    temporal=load('temporal-hdr-results.json');unaffected=load('unaffected-routes-results.json');invariance=load('readback-invariance.json')
    startup=load('full-config-startup.json');assert startup['passed']
    assert len(temporal)==2 and all(v['all_frames_passed'] and v['compiled_float32_verified'] and len(v['frames'])==31 for v in temporal)
    assert len(unaffected)==6 and all(v['all_rgba_bytes_exact'] for v in unaffected)
    assert len(invariance)==2 and all(v['all_rgba_pixels_exact'] for v in invariance)
    result=dict(generated_at=datetime.now().isoformat(timespec='seconds'),core_sha256=hashlib.sha256((ROOT/'mpv.exe').read_bytes()).hexdigest(),
        production_option='lut3d_size_I=96,lut3d_size_C=64,lut3d_size_h=256',no_core_rebuild=True,no_thread_increase=True,
        metric_test=metric,color_summary=color_summary,performance_summary=performance_summary,
        color_trials=colors,production_trials=production,performance_trials=performances,
        temporal_hdr=temporal,unaffected_routes=unaffected,readback_invariance=invariance,full_config_startup=startup,input_sha256=HASHES,
        precision_reference='独立float64连续映射；ICC按配置文件实际XYZ/TRC；非原片色彩不经映射保持的主张',
        software_acceptance=dict(dense_max_delta_e_00_less_than=1,per_sample_error_increase_less_than=.25,
            icc_analytic_residual_delta_e_00_less_than=.25,temporal_max_linear_error_less_than=.002,
            gamut_fused_stage_mean_increment_less_than_microseconds=10),
        performance_conclusion='未证明CPU吞吐提速。4K60仍丢帧；OP整片零丢帧目标未达成。',passed=True)
    path=DOC/'gamut-density-results-20261012.json'
    path.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
    print('PASS',len(color_summary),'精度汇总，',sum(len(v) for v in performances.values()),'性能轮次；',path,'bytes',path.stat().st_size)


if __name__=='__main__':main()
