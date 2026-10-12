"""汇总默认范围修复的实际软件读回与独立播放代价，不覆盖历史失败记录。"""
import hashlib,json
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/color-range-fix-20261011'
DEST=ROOT/'docs/modernization/color-range-fix-results-20261011.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files=['automatic-fix-results.json','automatic-dense-results.json','integration-results.json',
           'format-icc-results.json','readback-invariance.json','playback-timings.json']
    data={name:json.loads((OUT/name).read_text(encoding='utf-8')) for name in files}
    matrix=[r for r in data[files[0]] if 'matrix' in r]
    dense=data[files[1]];integration=data[files[2]];formats=data[files[3]]
    assert len(matrix)==12 and all(r['maximum_linear_error']<.00125 and r['all_source_codes_recovered'] for r in matrix)
    assert len(dense)==16 and all(r['automatic_script_verified'] for r in dense)
    assert all(r.get('all_original_codes_recovered',True) for r in dense)
    assert len(integration['hardware'])==2 and all(r['max_linear_error']<.00125 for r in integration['hardware'])
    assert len(formats)==6 and all(r.get('maximum_linear_error',0)<.00125 and r.get('maximum_mean_encoded_error',0)<.002 for r in formats)
    assert all(r['all_rgba_pixels_exact'] for r in data[files[4]])
    timings=[]
    for backend in ('d3d11','vulkan'):
        trials=[r for r in data[files[5]]['trials'] if r['backend']==backend]
        base=[r['cpu_ms_per_media_frame'] for r in trials if not r['enabled']]
        fix=[r['cpu_ms_per_media_frame'] for r in trials if r['enabled']]
        assert len(base)==len(fix)==2 and all(r['decoder_threads']==16 for r in trials)
        timings.append(dict(backend=backend,baseline_cpu_ms_per_frame=sum(base)/2,
            corrected_cpu_ms_per_frame=sum(fix)/2,increment_cpu_ms_per_frame=(sum(fix)-sum(base))/2,
            trial_cpu_ms_per_frame=[r['cpu_ms_per_media_frame'] for r in trials],
            zero_drops_all_windows=all(not any(r['drop_counters'].values()) for r in trials)))
    sources={str((OUT/name).relative_to(ROOT)).replace('\\','/'):sha(OUT/name) for name in files}
    code=['portable_config/scripts/color-range-fix.lua','portable_config/script-opts/color-range-fix.conf',
          'tools/test-color-range-fix.py','tools/test-color-range-dense.py','tools/test-color-range-integration.py',
          'tools/test-color-range-formats.py','tools/test-color-range-lifecycle.lua','tools/benchmark-color-range-fix.py',
          'tools/gpu-pipeline-d3d11.js','tools/gpu-pipeline-readback.py','tools/test-gpu-pipeline.py']
    historical=json.loads((ROOT/'docs/modernization/color-pipeline-results-20261011.json').read_text(encoding='utf-8'))
    result=dict(generated_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),
        identified_midpoint_configuration_fix_passed=True,core_recompiled=False,core_binary_changed=False,
        environment=historical['environment'],enabled_by_default=True,filter_threads=1,decoder_thread_increase=False,
        software_validation_only=True,all_color_pipeline_certified=False,
        remaining_work=['默认 perceptual 色域映射完整独立算法参考','自适应 HDR→SDR 完整独立算法参考'],
        matrix_cases=matrix,bypass_cases=[r for r in data[files[0]] if r.get('test')=='bypass'],
        dense_cases=dense,hardware_and_lifecycle=integration,format_and_icc= formats,
        readback_invariance=data[files[4]],
        performance=dict(scope=data[files[5]]['scope'],cpu_time_is_sum_of_process_threads=True,
                         short_window_not_full_clip_proof=True,summary=timings),
        source_result_sha256=sources,tested_code_sha256={p:sha(ROOT/p) for p in code})
    assert sha(ROOT/'mpv.exe')==historical['environment']['mpv_binary_sha256'],'核心二进制发生变化'
    DEST.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(timings,ensure_ascii=False,indent=2))
    print('范围修复结果汇总 PASS；历史整体验收仍保留 FAIL')


if __name__=='__main__':main()
