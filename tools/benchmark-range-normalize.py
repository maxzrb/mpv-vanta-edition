"""固定单线程测量 4K 全范围规范化 CPU 代价，不作为完整播放器帧率。"""
import array
import json
import re
import statistics
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/modernization/pipeline-validation-20261011'
W,H=3840,2160
FRAMES=96


def trial(path,bits,enabled,number):
    args=[str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','info','-benchmark',
          '-stream_loop','-1','-f','rawvideo','-pixel_format',f'yuv444p{bits}le','-video_size',f'{W}x{H}',
          '-framerate','48','-color_range','pc','-colorspace','bt709','-color_primaries','bt709',
          '-threads','1','-filter_threads','1','-i',str(path),'-an','-frames:v',str(FRAMES),
          '-vf','zscale=rangein=full:range=limited,format=yuv444p16le' if enabled else 'null',
          '-threads','1','-f','null','-']
    p=subprocess.run(args,capture_output=True,encoding='utf-8',errors='replace',check=True,timeout=90)
    times=re.findall(r'bench: utime=([\d.]+)s stime=([\d.]+)s rtime=([\d.]+)s',p.stderr)
    assert len(times)==1,p.stderr[-2000:]
    user,system,wall=map(float,times[0])
    return dict(bits=bits,enabled=enabled,round=number,frames=FRAMES,threads=1,filter_threads=1,
                user_seconds=user,system_seconds=system,wall_seconds=wall,wall_ms_per_frame=wall/FRAMES*1000)


def main():
    OUT.mkdir(parents=True,exist_ok=True);results=[];summaries=[]
    for bits in (10,12):
        count=1<<bits
        plane=array.array('H',(i%count for i in range(W*H)))
        neutral=array.array('H',[count//2])*(W*H)
        path=OUT/f'range-time-4k-{bits}.yuv'
        path.write_bytes(plane.tobytes()+neutral.tobytes()*2)
        rows=[]
        for number,enabled in enumerate((False,True,True,False)):
            row=trial(path,bits,enabled,number);rows.append(row);results.append(row)
            print(bits,'转换' if enabled else '基线',row['wall_ms_per_frame'],'ms/frame',flush=True)
        baseline=statistics.mean(r['wall_ms_per_frame'] for r in rows if not r['enabled'])
        candidate=statistics.mean(r['wall_ms_per_frame'] for r in rows if r['enabled'])
        cpu_baseline=statistics.mean((r['user_seconds']+r['system_seconds'])/r['frames']*1000 for r in rows if not r['enabled'])
        cpu_candidate=statistics.mean((r['user_seconds']+r['system_seconds'])/r['frames']*1000 for r in rows if r['enabled'])
        summaries.append(dict(bits=bits,baseline_ms_per_frame=baseline,candidate_ms_per_frame=candidate,
                              incremental_ms_per_frame=candidate-baseline,baseline_cpu_ms_per_frame=cpu_baseline,
                              candidate_cpu_ms_per_frame=cpu_candidate,incremental_cpu_ms_per_frame=cpu_candidate-cpu_baseline))
    (OUT/'range-timings.json').write_text(json.dumps(dict(scope='独立 FFmpeg 原始帧至 null；全进程总时长／96 帧，ABBA；非 mpv 总体帧率',
        trials=results,summaries=summaries),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
