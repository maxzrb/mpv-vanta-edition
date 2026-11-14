"""固定播放快照与参考输出，验证过载判定、保护窗口和恢复退避。"""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sample = json.loads((ROOT / 'tools/fate/samples/overload.json').read_text(encoding='utf-8'))
lines = ["local M = dofile('portable_config/script-modules/overload-policy.lua')"]
for case in sample['cases']:
    settings = dict(sample['policy'], **case.get('options', {}))
    options = '{' + ','.join(k + '=' + (str(v).lower() if isinstance(v, bool) else str(v))
                             for k, v in settings.items()) + '}'
    lines += ['do', 'local p=M.new(' + options + ');p:reset(0)', 'local reference=false;local result={}']
    for row in case['samples']:
        now, lag = row[:2]
        blocked = row[2] if len(row) > 2 else False
        busy = row[3] if len(row) > 3 else False
        dropped = row[4] if len(row) > 4 else None
        fps = row[5] if len(row) > 5 else 24
        values = f'now={now},lag={lag if lag is not None else "nil"},blocked={str(blocked).lower()},busy={str(busy).lower()},reference=reference'
        values += f',dropped={dropped if dropped is not None else "nil"},fps={fps},speed=1'
        lines += [f'local action=p:step({{{values}}})',
                  f"if action then result[#result+1]='{now}:'..action;"
                  f"if action=='resync' then p:resynced({now}) else reference=action=='reference';p:commit(reference,{now}) end end"]
    lines += [f"io.write('{case['name']} ',#result>0 and table.concat(result,',') or 'none','\\n')", 'end']
with tempfile.TemporaryDirectory(prefix='vanta-fate-policy-') as directory:
    script = Path(directory) / 'policy.lua'
    script.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    actual = subprocess.check_output([str(ROOT / 'luajit.exe'), str(script)], cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
reference = (ROOT / 'tools/fate/ref/overload-policy').read_text(encoding='utf-8')
assert actual == reference, (actual, reference)
print(actual, end='')
