"""维护者只读上游审计，输出版本、许可与现存文件差异，不覆盖定制文件。"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/modernization'


def api(path):
    result = subprocess.run(['gh', 'api', path], capture_output=True, text=True, encoding='utf-8', timeout=60)
    if result.returncode:
        raise RuntimeError(result.stderr[:180])
    return json.loads(result.stdout)


def lua_pattern(pattern):
    # 当前源清单只使用简单 Lua 模式；保持白名单／黑名单的匹配语义。
    return pattern.replace('%.', r'\.').replace('%-', '-').replace('.-', '.*?')


def audit(source):
    repo = source['git'].split('github.com/')[-1].removesuffix('.git')
    result = {'name': source['name'], 'repository': repo, 'branch': source.get('branch'),
              'enabled': source.get('enabled', True), 'policy': 'review-before-merge'}
    try:
        commit = api(f"repos/{repo}/commits/{source.get('branch', 'HEAD')}")
        result['commit'] = commit['sha']
        result['commit_date'] = commit['commit']['committer']['date']
        try:
            license_data = api(f'repos/{repo}/license')
            result['license'] = license_data.get('license', {}).get('spdx_id', '需审阅')
            result['license_url'] = license_data['html_url']
        except Exception:
            result['license'] = '未找到独立许可证，需逐文件审阅'
        tree = api(f"repos/{repo}/git/trees/{commit['sha']}?recursive=1")['tree']
        differences, identical = [], 0
        dest = source.get('dest', '~~/scripts').replace('~~/', 'portable_config/')
        for item in tree:
            if item['type'] != 'blob':
                continue
            path = item['path']
            if source.get('whitelist') and not re.search(lua_pattern(source['whitelist']), path):
                continue
            if source.get('blacklist') and re.search(lua_pattern(source['blacklist']), path):
                continue
            stripped = source.get('strip_prefix')
            if stripped:
                prefix = stripped.rstrip('/') + '/'
                if not path.startswith(prefix):
                    continue
                path = path[len(prefix):]
            path = source.get('renames', {}).get(path, path)
            if source.get('flatten_folders'):
                path = Path(path).name
            local = ROOT / dest / path
            if not local.is_file():
                continue
            data = local.read_bytes()
            digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if digest == item['sha']:
                identical += 1
            else:
                differences.append({'local': local.relative_to(ROOT).as_posix(), 'upstream': item['path'],
                                    'local_blob': digest, 'upstream_blob': item['sha']})
        result['identical_files'] = identical
        result['differences'] = differences
    except Exception as error:
        result['error'] = str(error)
    return result


def main():
    sources = json.loads((ROOT / 'portable_config/MAINTAINER-ONLY-WARNING-upstream-sources.json').read_text(encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(audit, sources))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'upstream-audit.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    for result in results:
        print(result['name'], result.get('commit', '')[:10], len(result.get('differences', [])), result.get('error', ''))


if __name__ == '__main__':
    main()
