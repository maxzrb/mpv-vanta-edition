"""隔离模拟上游覆盖、幂等应用与未知版本拒绝；不修改活动运行库。"""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    apply_fixes=runpy.run_path(str(ROOT/'tools/apply-k7-color-fixes.py'))['apply_fixes']
    relative=Path('portable_config/vs/patches/k7sfunc-1.8.1-color.json')
    recipe=json.loads((ROOT/relative).read_text(encoding='utf-8'))
    base=ROOT/'tmp/modernization';base.mkdir(parents=True,exist_ok=True)
    target=Path(tempfile.mkdtemp(prefix='k7-update-',dir=base))
    (target/relative).parent.mkdir(parents=True)
    (target/relative).write_bytes((ROOT/relative).read_bytes())
    originals={}
    for entry in recipe['files']:
        current=(ROOT/entry['path']).read_bytes()
        assert sha(current)==entry['result_sha256'],'活动库已有变化，先重新审阅配方'
        encoding='utf-8-sig' if current.startswith(b'\xef\xbb\xbf') else 'utf-8'
        text=current.decode(encoding)
        for change in reversed(entry['replacements']):
            assert text.count(change['new'])==1,entry['path']
            text=text.replace(change['new'],change['old'],1)
        original=text.encode(encoding)
        assert sha(original)==entry['base_sha256'],entry['path']
        path=target/entry['path'];path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(original);originals[entry['path']]=original
    lock_path=target/'portable_config/components.lock.json'
    lock={'vs':{'files':[dict(path=k,sha256=sha(v),size=len(v)) for k,v in originals.items()],
                'local_patches':[{'id':'unrelated-user-patch','keep':True}]}}
    lock_path.write_text(json.dumps(lock),encoding='utf-8',newline='\n')
    with contextlib.redirect_stdout(io.StringIO()):
        apply_fixes(target)
        assert all((target/k).read_bytes()==v for k,v in originals.items()),'默认检查不得修改'
        apply_fixes(target,True)
    patched={k:(target/k).read_bytes() for k in originals}
    for entry in recipe['files']:
        assert sha(patched[entry['path']])==entry['result_sha256']
    assert len(list((target/'backup').glob('*/manifest.json')))==1
    result=json.loads(lock_path.read_text(encoding='utf-8'))
    assert any(p['id']=='unrelated-user-patch' and p['keep'] for p in result['vs']['local_patches'])
    with contextlib.redirect_stdout(io.StringIO()):
        apply_fixes(target,True)
    assert all((target/k).read_bytes()==v for k,v in patched.items())
    assert len(list((target/'backup').glob('*/manifest.json')))==1,'幂等重跑不能重复备份'
    # 最后一个文件变成未知上游，前一个文件恢复原件：必须先全部检查，不能部分写入。
    first,last=recipe['files'][0]['path'],recipe['files'][-1]['path']
    (target/first).write_bytes(originals[first])
    (target/last).write_bytes(patched[last]+b'\n# unknown upstream\n')
    before={k:(target/k).read_bytes() for k in originals}
    try:
        with contextlib.redirect_stdout(io.StringIO()):apply_fixes(target,True)
    except RuntimeError as error:
        assert '上游版本变化' in str(error)
    else:raise AssertionError('未知上游被覆盖')
    assert all((target/k).read_bytes()==v for k,v in before.items())
    print('K7 上游覆盖后重用补丁／默认只读／幂等／未知版本全量拒绝 PASS')


if __name__=='__main__':main()
