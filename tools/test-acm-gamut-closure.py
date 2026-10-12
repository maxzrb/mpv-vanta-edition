"""同轮比较修复前后 709 ACM 全码阶，保留原始着色器证据。"""
import json,os,runpy,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    results=[]
    for baseline in (True,False):
        if baseline:os.environ['MPV_PIPELINE_BASELINE']='1'
        else:os.environ.pop('MPV_PIPELINE_BASELINE',None)
        t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline-hdr.py'))
        original=t['capture']
        def capture(media,name,backend,**kwargs):
            return original(media,('before-' if baseline else 'after-')+name,backend,**kwargs)
        t['dense_gray_case'].__globals__['capture']=capture
        for backend in ('d3d11','vulkan'):
            row=t['dense_gray_case'](backend);row['baseline']=baseline
            graph=json.loads((t['OUT']/(('before-' if baseline else 'after-')+'stage-gray16-all-'+backend+'-graph.json')).read_text(encoding='utf-8'))
            if backend=='d3d11':
                shader=next(m for m in graph if m.get('shader') and 'SampleLevel' in m['shader'])
                row['color_shader_3d_lut']='Texture3D' in shader['shader']
                row['color_shader_instruction_slots']=re.findall(r'Approximately (\d+) instruction slots',shader['shader_ir'])
            results.append(row);print('BEFORE' if baseline else 'AFTER',backend,max(row['stage_max_errors']),max(row['stage_max_delta_L']),flush=True)
    os.environ.pop('MPV_PIPELINE_BASELINE',None)
    for backend in ('d3d11','vulkan'):
        before=next(r for r in results if r['backend']==backend and r['baseline'])
        after=next(r for r in results if r['backend']==backend and not r['baseline'])
        assert max(after['stage_max_errors'])<max(before['stage_max_errors'])/3
        assert after['reference_passed']
    assert not next(r for r in results if r['backend']=='d3d11' and not r['baseline'])['color_shader_3d_lut']
    (t['OUT']/'acm-gamut-closure.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
