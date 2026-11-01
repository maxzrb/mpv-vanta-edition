"""用真实 Windows 文件锁和多进程验证可靠保存，不改用户配置。"""
import ctypes
from ctypes import wintypes
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(tempfile.mkdtemp(prefix='safe-file-', dir=ROOT / 'tmp'))


def literal(text):
    return "'" + ''.join('\\%03d' % byte for byte in str(text).encode('utf-8')) + "'"


def run(code, wait=True):
    command = [str(ROOT / 'luajit.exe'), '-e',
               'local m=dofile(' + literal(ROOT / 'portable_config/script-modules/safe-file.lua') + ');' + code]
    if not wait:
        return subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')


target = OUT / '中文 设置.conf'
target.write_bytes('# 中文注释\nfirst=old\nsecond=unchanged\n'.encode('utf-8'))
run('assert(m.update_options(' + literal(target) + ",{first='new'}))")
assert target.read_text(encoding='utf-8') == '# 中文注释\nfirst=new\nsecond=unchanged\n'
run('assert(m.update_options(' + literal(target) + ",{second='also-new'}))")
assert target.read_text(encoding='utf-8') == '# 中文注释\nfirst=new\nsecond=also-new\n'
original = target.read_bytes()
run('local ok=m.update(' + literal(target) + ",function() error('fixture') end);assert(not ok)")
assert target.read_bytes() == original
run('local ok=m.update(' + literal(target) + ',function() assert(m.write(' + literal(target) +
    ",'external'));return 'stale' end);assert(not ok)")
assert target.read_text(encoding='utf-8') == 'external'
target.write_bytes(original)

# 真实占用目标文件且不允许删除／改名，确认提交失败不会清空原件。
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                              ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
kernel.CreateFileW.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
handle = kernel.CreateFileW(str(target), 0x80000000, 1, None, 3, 0x80, None)
assert handle != ctypes.c_void_p(-1).value
try:
    run('local ok=m.write(' + literal(target) + ",'replacement');assert(not ok)")
    assert target.read_bytes() == original
finally:
    kernel.CloseHandle(handle)
assert not list(OUT.glob('*.lock')) and not list(OUT.glob('*.tmp-*'))

target.write_bytes(b'\xef\xbb\xbf# UTF-8\r\nfirst=old\r\nfirst=duplicate\r\nsecond=kept\r\n')
run('assert(m.update_options(' + literal(target) + ",{first='new'}))")
assert target.read_bytes() == b'\xef\xbb\xbf# UTF-8\r\nfirst=new\r\nfirst=new\r\nsecond=kept\r\n'
empty = OUT / '空文件.txt'
run('assert(m.write(' + literal(empty) + ",''))")
assert empty.is_file() and empty.read_bytes() == b''
run('local ok=m.write(' + literal(OUT / '不存在' / '配置.conf') + ",'x');assert(not ok)")

# 两个真实进程同时读改写，最终必须保留全部增量。
counter = OUT / '并发.txt'
counter.write_text('0', encoding='utf-8')
code = '''
local ffi=require('ffi')
for i=1,30 do
    local ok,err
    for retry=1,100 do
        ok,err=m.update(PATH,function(current) return tostring(tonumber(current)+1) end)
        if ok then break end
        ffi.C.Sleep(2)
    end
    assert(ok,err)
end
'''.replace('PATH', literal(counter))
processes = [run(code, wait=False) for _ in range(2)]
for process in processes:
    _, stderr = process.communicate(timeout=30)
    assert process.returncode == 0, stderr.decode('utf-8', errors='replace')
assert counter.read_text(encoding='utf-8') == '60'
assert not list(OUT.glob('*.lock')) and not list(OUT.glob('*.tmp-*'))
print('PASS 中文路径、保留注释、逐项合并、转换失败回滚、替换失败保留原件、双进程60次更新及锁／临时文件清理')
