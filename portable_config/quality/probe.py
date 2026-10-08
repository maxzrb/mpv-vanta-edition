"""维护者手动核查／准备 VS；起播、菜单及滤镜选择不调用本工具。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'portable_config'


def emit(data):
    print('VANTA_RESULT=' + json.dumps(data, ensure_ascii=False), flush=True)


def inventory():
    import importlib.metadata
    import vapoursynth as vs
    import k7sfunc
    plugins = {p.namespace: p.identifier for p in vs.core.plugins()}
    gpu_names = []
    try:
        result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
                                 'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name'],
                                capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        gpu_names = result.stdout.decode('utf-8', errors='replace').splitlines()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {'python': sys.version.split()[0], 'vapoursynth': str(vs.__version__),
            'k7sfunc': k7sfunc.__version__, 'plugins': plugins, 'gpu_names': gpu_names,
            'nvidia': any('nvidia' in name.lower() for name in gpu_names)}


def check_lock():
    lock = json.loads((CONFIG / 'components.lock.json').read_text(encoding='utf-8'))
    for item in lock['vs']['files']:
        path = ROOT / item['path']
        if not path.is_file():
            raise FileNotFoundError('套件文件缺失：' + item['path'])
        with path.open('rb') as handle:
            digest = hashlib.file_digest(handle, 'sha256').hexdigest()
        if digest != item['sha256']:
            raise RuntimeError('套件文件已被单独更改，请恢复整套版本：' + item['path'])


def prepare(args):
    check_lock()
    import vapoursynth as vs
    import k7sfunc  # 先检查依赖，随后才读取选中的脚本
    path = (CONFIG / 'vs' / args.script).resolve()
    if path.parent != CONFIG / 'vs' or path.suffix != '.vpy':
        raise ValueError('无效脚本路径')
    clip = vs.core.std.BlankClip(width=args.width, height=args.height,
                                format=vs.YUV420P10 if args.bits > 8 else vs.YUV420P8,
                                length=8, fpsnum=round(args.fps * 1000), fpsden=1000)
    clip = vs.core.std.SetFrameProps(clip, _Matrix=1, _Primaries=1, _Transfer=1, _ColorRange=1)
    # 交替亮度使补帧必须处理中间帧，避免静止帧捷径掩盖推理错误。
    other = vs.core.std.BlankClip(clip, color=[64 << (args.bits - 8), 128 << (args.bits - 8), 128 << (args.bits - 8)])
    other = vs.core.std.SetFrameProps(other, _Matrix=1, _Primaries=1, _Transfer=1, _ColorRange=1)
    clip = vs.core.std.Interleave([clip, other], modify_duration=False)
    clip = vs.core.std.AssumeFPS(clip, fpsnum=round(args.fps * 1000), fpsden=1000)
    vs.clear_outputs()
    runpy.run_path(str(path), init_globals={'video_in': clip, 'container_fps': args.fps})
    output = vs.get_output(0)
    output = output.clip if hasattr(output, 'clip') else output
    if not isinstance(output, vs.VideoNode):
        raise RuntimeError('脚本没有输出视频')
    # 请求真实输出帧，才能发现 DLL、设备、模型及引擎构建错误。
    for index in [0, min(1, output.num_frames - 1)]:
        with output.get_frame(index) as frame:
            if frame.format.bits_per_sample < args.bits:
                raise RuntimeError('处理链降低了源位深，暂不开放')
            for key, expected in [('_Matrix', 1), ('_Primaries', 1), ('_Transfer', 1), ('_ColorRange', 1)]:
                if frame.props.get(key) != expected:
                    raise RuntimeError('色彩元数据未保留：' + key)
    return {'state': 'ready', 'width': output.width, 'height': output.height,
            'fps': float(output.fps), 'bits': output.format.bits_per_sample}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['inventory', 'prepare'])
    parser.add_argument('--script')
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=360)
    parser.add_argument('--bits', type=int, default=8)
    parser.add_argument('--fps', type=float, default=24)
    args = parser.parse_args()
    os.chdir(ROOT)
    try:
        data = inventory() if args.action == 'inventory' else prepare(args)
        emit(data)
    except Exception as error:
        emit({'state': 'missing' if isinstance(error, (ImportError, FileNotFoundError)) or '缺失' in str(error) else 'failed',
              'reason': str(error)})
        sys.exit(1)


if __name__ == '__main__':
    main()
