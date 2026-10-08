"""维护者手动应用 K7 色彩补丁；播放器不调用本工具。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'portable_config/vs/patches/k7sfunc-1.8.1-color.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def apply_fixes(root=ROOT, apply=False):
    root = Path(root).resolve()
    recipe_path = root / RECIPE.relative_to(ROOT)
    recipe = json.loads(recipe_path.read_text(encoding='utf-8'))
    edits = []
    for entry in recipe['files']:
        path = (root / entry['path']).resolve()
        assert (root / 'Lib/site-packages/k7sfunc').resolve() in path.parents and path.suffix == '.py'
        raw = path.read_bytes()
        actual = digest(raw)
        if actual == entry['result_sha256']:
            print(entry['path'], '已应用')
            continue
        if actual != entry['base_sha256']:
            raise RuntimeError(f"{entry['path']} 已有其他修改或上游版本变化；需维护者重新合并，不能覆盖")
        encoding = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
        text = raw.decode(encoding)
        for replacement in entry['replacements']:
            assert text.count(replacement['old']) == 1, entry['path']
            text = text.replace(replacement['old'], replacement['new'], 1)
        changed = text.encode(encoding)
        assert digest(changed) == entry['result_sha256'], entry['path']
        compile(text, str(path), 'exec')
        edits.append((path, changed))
        print(entry['path'], '可应用')
    if not apply:
        return
    # 全部源文件检查通过后才修改；留存本机原件供回退。
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
    backup = root / 'backup' / ('color-fixes-' + stamp + '-before')
    lock_path = root / 'portable_config/components.lock.json'
    if edits:
        for path in [*(path for path, _ in edits), lock_path]:
            destination = backup / path.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        (backup / 'manifest.json').write_text(json.dumps(
            [path.relative_to(root).as_posix() for path in [*(p for p, _ in edits), lock_path]],
            ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        for path, raw in edits:
            path.write_bytes(raw)
    # 仅维护阶段刷新清单；不改变组件版本、推理精度或后端支持策略。
    raw = lock_path.read_bytes()
    encoding = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    lock = json.loads(raw.decode(encoding))
    for entry in lock['vs']['files']:
        path = root / entry['path']
        if entry['path'] in {item['path'] for item in recipe['files']}:
            entry.update(sha256=digest(path.read_bytes()), size=path.stat().st_size)
    lock['vs']['local_patches'] = [patch for patch in lock['vs'].get('local_patches', [])
                                 if patch.get('id') != recipe['id']] + [
        {'id': recipe['id'], 'recipe': recipe_path.relative_to(root).as_posix(),
         'policy': 'maintainer-apply-only; no-playback-validation'}]
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding=encoding, newline='\n')
    print('维护补丁应用完成；备份', backup.relative_to(root) if edits else '无需重复备份')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='应用维护补丁；默认只查看')
    args = parser.parse_args()
    apply_fixes(apply=args.apply)


if __name__ == '__main__':
    main()
