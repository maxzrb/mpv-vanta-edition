"""生成整套 VS 候选锁定清单；只能在回归验证后人工替换正式清单。"""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
lock = json.loads((ROOT / 'portable_config/components.lock.json').read_text(encoding='utf-8'))
paths = {ROOT / item['path'] for item in lock['vs']['files']}
for directory in ['Lib', 'DLLs', 'vs-plugins', 'vs-coreplugins']:
    paths.update(path for path in (ROOT / directory).rglob('*') if path.is_file()
                 and '__pycache__' not in path.parts and path.suffix not in ['.pyc', '.pdb'])
def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


lock['vs']['files'] = [
    {'path': path.relative_to(ROOT).as_posix(),
     'sha256': digest(path), 'size': path.stat().st_size}
    for path in sorted(paths) if path.is_file()
]
lock['vs']['packages'] = sorted([
    {'name': distribution.metadata['Name'], 'version': distribution.version,
     'license': distribution.metadata.get('License-Expression') or distribution.metadata.get('License') or '未知'}
    for distribution in importlib.metadata.distributions()
], key=lambda item: item['name'].lower())
destination = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'tmp/modernization/components.candidate.json'
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(destination, len(lock['vs']['files']), '个文件')
