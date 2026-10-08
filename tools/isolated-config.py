"""将活动配置复制到忽略的测试目录，隔离历史、持久化状态及缓存写入。"""
from pathlib import Path
import shutil,tempfile
ROOT=Path(__file__).resolve().parents[1]
def create_config(name, exclude_scripts=()):
    base=ROOT/'tmp/modernization/isolated';base.mkdir(parents=True,exist_ok=True)
    target=Path(tempfile.mkdtemp(prefix=name+'-',dir=base))
    source=ROOT/'portable_config'
    for path in source.iterdir():
        if path.is_file() and path.suffix.lower() in ['.conf','.json']:
            shutil.copy2(path,target/path.name)
        elif path.is_dir() and path.name in ['scripts','script-opts','script-modules','script-assets','fonts','icc','osc-style','vs','shaders','quality']:
            ignored = ('backup','__pycache__',*exclude_scripts) if path.name=='scripts' else ('backup','__pycache__')
            shutil.copytree(path,target/path.name,ignore=shutil.ignore_patterns(*ignored))
    (target/'files').mkdir(exist_ok=True);(target/'cache').mkdir(exist_ok=True)
    # 测试关闭更新、位置记忆；生产配置不变。
    with (target/'mpv.conf').open('a',encoding='utf-8',newline='\n') as f:
        f.write('\nsave-position-on-quit=no\nsave-watch-history=no\n')
    return target
