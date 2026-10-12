"""由默认脚本自动校正的全码阶／灰阶／PQ／HLG 复验，不预装转换滤镜。"""
import json,os,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ['MPV_PIPELINE_OUT']=str(ROOT/'tmp/modernization/color-range-fix-20261011')
dense=runpy.run_path(str(ROOT/'tools/test-range-normalize-dense.py'))
t=dense['t'];t['EXCLUDED'].remove('color-range-fix.lua')
capture=t['capture']


def automatic(*args,**kwargs):
    candidate=os.environ.pop('MPV_PIPELINE_RANGE_NORMALIZE',None)
    try:
        rows,status=capture(*args,**kwargs)
        fix=status['validation_range_fix']
        assert fix and fix['active'] and fix['state']=='已校正',fix
        return rows,status
    finally:
        if candidate is not None:os.environ['MPV_PIPELINE_RANGE_NORMALIZE']=candidate


def main():
    t['capture']=automatic
    dense['main']()
    path=t['OUT']/'range-dense-results.json'
    rows=json.loads(path.read_text(encoding='utf-8'))
    for row in rows:row['production_enabled']=True;row['automatic_script_verified']=True
    (t['OUT']/'automatic-dense-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
