"""真实8K后瞻取消回归：停止及切换模式后不得启动旧采样。"""
import json
from pathlib import Path
import runpy
import time

ROOT=Path(__file__).resolve().parents[1]
Player=runpy.run_path(str(ROOT/'tools/validate-modernization.py'))['Player']
create_config=runpy.run_path(str(ROOT/'tools/isolated-config.py'))['create_config']


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('media',type=Path)
    args=parser.parse_args()
    rows=[]
    for action in ['stop','mode-change']:
        p=Player(['--config-dir='+str(create_config('logo-lifecycle')),'--hwdec=no','--volume=0',
                  '--start=10','--pause=yes','--geometry=1280x720',str(args.media)],'logo-lifecycle-'+action)
        p.ipc_timeout=30
        try:
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                log=p.log.read_text(encoding='utf-8')
                if '[startup_format_logos] Starting subprocess:' in log:break
                time.sleep(.1)
            else:raise AssertionError('没有启动后瞻控制组')
            probe_line=next(line for line in log.splitlines() if '[startup_format_logos] Starting subprocess:' in line)
            executable=probe_line.split('Starting subprocess: [',1)[1].split(', -hide_banner',1)[0]
            executable=executable.replace('\\','/').replace('//','/')
            assert Path(executable).resolve()==(ROOT/'ffmpeg/ffmpeg.exe').resolve(), '必须选随包ffmpeg'
            offset=p.log.stat().st_size
            if action=='stop':
                assert p.command('stop')['error']=='success'
            else:
                assert p.command('script-message','startup-format-logos-set-mode','none')['error']=='success'
                deadline=time.monotonic()+20
                while p.get('user-data/startup-format-logos/mode')!='none':
                    assert time.monotonic()<deadline
                    time.sleep(.1)
            time.sleep(3)
            tail=p.log.read_bytes()[offset:].decode('utf-8')
            assert '[startup_format_logos] Starting subprocess:' not in tail,tail
            rows.append({'action':action,'cancelled_callbacks_launched_new_probes':False,'bundled_ffmpeg':True})
        finally:p.close()
        assert 'Lua error:' not in p.log.read_text(encoding='utf-8')
        print('PASS 徽标后瞻取消',action,flush=True)
    output=ROOT/'tmp/modernization/av1-scheduling-20261008/logo-lifecycle.json'
    output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
