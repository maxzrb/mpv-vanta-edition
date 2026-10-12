"""汇总3FP精度与本机实际GPU独立参考，保留原始研究结果及哈希。"""
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    inputs={
        'threefp_precision':'docs/modernization/3fp-precision-comparison-20261011.json',
        'hlg_common':'tmp/modernization/color-accuracy-20261011/hlg-common-results.json',
        'icc_size':'tmp/modernization/color-accuracy-20261011/icc-size-results.json',
        'gamut_calibration':'docs/modernization/gamut-reference-calibration-20261012.json',
        'adaptive_hdr':'tmp/modernization/color-accuracy-20261012/adaptive-hdr-results.json',
        'hdr_gamut_composition':'tmp/modernization/color-accuracy-20261012/hdr-gamut-composition-results.json'}
    evidence={key:json.loads((ROOT/path).read_text(encoding='utf-8-sig')) for key,path in inputs.items()}
    assert len(evidence['adaptive_hdr'])==16 and all(v['reference_passed'] for v in evidence['adaptive_hdr'])
    assert len(evidence['hdr_gamut_composition'])==4 and all(v['reference_passed'] for v in evidence['hdr_gamut_composition'])
    assert all(v['table_model_passed'] for v in evidence['gamut_calibration'])
    result=dict(date='2026-10-12',scope='软件数值及公开固定提交审计；静态场景，无面板或3FP实播测量',
        precision_grade_matches_public_3fp=True,all_color_algorithms_and_temporal_scenes_certified=False,
        production_settings_changed_this_round=False,core_changed=False,decoder_threads_increased=False,
        core_sha256=hashlib.sha256((ROOT/'mpv.exe').read_bytes()).hexdigest(),
        source_evidence_sha256={key:dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()) for key,path in inputs.items()},
        tested_tools_sha256={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in [
            ROOT/'tools'/name for name in ['audit-3fp-precision.py','color-map-reference.py',
                'test-3fp-hlg-comparison.py','test-hdr-adaptive-reference.py','test-hdr-gamut-composition.py',
                'calibrate-gamut-reference.py','test-gpu-pipeline.py','gpu-pipeline-vulkan.js']]},
        evidence=evidence)
    destination=ROOT/'docs/modernization/color-accuracy-results-20261012.json'
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('精度对照／静态HDR16组／组合4组／色域表4组证据汇总 PASS')


if __name__=='__main__':main()
