"""单线程范围规范化的全码阶可逆性、灰阶与 HDR 数值补测。"""
import json
import math
import argparse
import os
import runpy
import struct
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
t=runpy.run_path(str(ROOT/'tools/test-gpu-pipeline.py'));OUT=t['OUT']
W,H=512,128


def fixture(bits,kind):
    count=1<<bits
    y=[i%count for i in range(W*H)]
    chroma=[[(i+plane*count//3)%count for i in range(W*H)] if kind=='planes' else [count//2]*(W*H)
            for plane in (1,2)]
    raw=struct.pack('<'+'H'*(W*H*3),*(y+chroma[0]+chroma[1]))
    name=f'range-dense-{bits}-{kind}'
    path=OUT/(name+'.yuv');path.write_bytes(raw*24)
    media=OUT/(name+'.mkv')
    subprocess.run([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y',
        '-f','rawvideo','-pixel_format',f'yuv444p{bits}le','-video_size',f'{W}x{H}','-framerate','24',
        '-color_range','pc','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1',
        '-i',str(path),'-c:v','ffv1','-threads','1','-pix_fmt',f'yuv444p{bits}le',
        '-color_range','pc','-colorspace','bt709','-color_primaries','bt709','-color_trc','iec61966-2-1',str(media)],check=True,timeout=20)
    decoded=subprocess.check_output([str(ROOT/'ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','error',
        '-i',str(media),'-frames:v','1','-pix_fmt',f'yuv444p{bits}le','-color_range','pc','-f','rawvideo','-'],timeout=20)
    assert decoded==raw, '夹具编码或元数据改变了原码值'
    return media,raw


def dense(bits,kind,backend):
    media,raw=fixture(bits,kind)
    rows,status=t['capture'](media,f'range-dense-{bits}-{kind}',backend,size=f'{W}x{H}')
    planes=[r for r in rows if r[0]['phase']=='input' and r[0]['format']==56 and r[0]['width']==W and r[0]['height']==H]
    assert len(planes)==3
    count=1<<bits;mapping_errors=[];uniques=[]
    for plane,(m,data) in enumerate(planes):
        pairs=[(struct.unpack_from('<H',raw,(plane*W*H+i)*2)[0],
                struct.unpack_from('<H',data,(i//W)*m['stride']+(i%W)*2)[0]) for i in range(W*H)]
        offset=4096 if plane==0 else 32768
        span=56064 if plane==0 else 57344
        center=0 if plane==0 else count//2
        wrong=[(code,mapped,round((mapped-offset)/span*(count-1)+center)) for code,mapped in pairs
               if round((mapped-offset)/span*(count-1)+center)!=code]
        assert not wrong, ('全码阶逆算不一致',plane,wrong[:10],min(pairs),max(pairs))
        mapping_errors.append(max(abs(mapped-(offset+(code-center)/(count-1)*span)) for code,mapped in pairs))
        # 整数取整半码阶，加两次 16bit 数值量级的 FP32 舍入预算。
        assert mapping_errors[-1]<.5+2/256,mapping_errors
        uniques.append(len(set(mapped for code,mapped in pairs)))
    result=dict(test='full-code-range-'+kind,bits=bits,backend=backend,mapping_max_code_errors=mapping_errors,
                all_original_codes_recovered=True,mapped_unique_codes_per_plane=uniques,production_enabled=False)
    if kind=='gray':
        values=[t['pixel'](rows[-1],i%W,i//W) for i in range(count)]
        expected=[t['output']['sdr_linear'](i/(count-1)) for i in range(count)]
        error=max(abs(c-expected[i]) for i,rgb in enumerate(values) for c in rgb)
        neutral=max(max(rgb)-min(rgb) for rgb in values)
        # 矩阵浮点舍入可能跨过 FP16 邻近值；中性通道差不能要求位级恒等。
        assert error<.00125 and neutral<.0005,(error,neutral)
        result.update(max_linear_error=error,max_neutral_channel_spread=neutral,output_unique_gray_values=len(set(v[0] for v in values)))
    return result


def hdr(bits,transfer,matrix=1):
    name=f'range-hdr-{bits}-{matrix}-{transfer}'
    media,_=t['fixtures']['fixture'](name,bits,matrix,True,matrix==9,transfer=transfer)
    raw=(OUT/(name+'.yuv')).read_bytes()
    encoded=[]
    for i in range(16):
        x=i%4*64+32;y=i//4*64+32
        codes=[struct.unpack_from('<H',raw,(plane*65536+y*256+x)*2)[0] for plane in range(3)]
        encoded.append(t['fixtures']['reference'](codes,bits,matrix,True))
    rows,status=t['capture'](media,name,'d3d11',hdr_transfer=transfer)
    ref=t['output']['reference']
    def hlg709(rgb):
        # 此夹具原色是 709，OOTF 的亮度系数不能套用 2020 参考。
        scene=[v*v/3 if v<=.5 else (math.exp((v-.55991073)/.17883277)+.28466892)/12 for v in rgb]
        luma=sum(v*w for v,w in zip(scene,(.2126,.7152,.0722)))
        return [1000*luma**.2*v/80 for v in scene]
    expected=[[ref['pq_decode'](v)/80 for v in rgb] if transfer=='smpte2084'
              else [v/80 for v in ref['hlg_reference'](rgb,1000)] if matrix==9 else hlg709(rgb) for rgb in encoded]
    if matrix==9:
        conversion=t['output']['hdr']['MATRIX']
        expected=[[sum(a*b for a,b in zip(row,rgb)) for row in conversion] for rgb in expected]
    errors=[]
    for row in rows:
        if row[0]['phase'] not in ('output','present'):continue
        actual=[t['pixel'](row,i%4*64+32,i//4*64+32) for i in range(16)]
        differences=[abs(a-b) for rgb,target in zip(actual,expected) for a,b in zip(rgb,target)]
        limits=[.00125+.002*abs(v) for rgb in expected for v in rgb]
        assert all(e<limit for e,limit in zip(differences,limits)),(bits,transfer,max(differences))
        errors.append(max(differences))
    assert status['validation_filtered']['gamma']==('pq' if transfer=='smpte2084' else 'hlg')
    return dict(test='full-range-hdr',bits=bits,matrix=matrix,backend='d3d11',transfer=transfer,stage_max_errors=errors,production_enabled=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--hdr-only',action='store_true');args=parser.parse_args()
    path=OUT/'range-dense-results.json'
    results=[row for row in json.loads(path.read_text(encoding='utf-8')) if row['test']!='full-range-hdr'] if args.hdr_only else []
    if args.hdr_only:assert len(results)==8,'缺少全码阶验收结果'
    os.environ['MPV_PIPELINE_RANGE_NORMALIZE']='1'
    try:
        for bits in (10,12):
            for kind in (() if args.hdr_only else ('planes','gray')):
                for backend in ('d3d11','vulkan'):
                    row=dense(bits,kind,backend);results.append(row);print('PASS',bits,kind,backend,row,flush=True)
            for matrix in (1,9):
                for transfer in ('smpte2084','arib-std-b67'):
                    row=hdr(bits,transfer,matrix);results.append(row);print('PASS HDR',bits,matrix,transfer,max(row['stage_max_errors']),flush=True)
    finally:os.environ.pop('MPV_PIPELINE_RANGE_NORMALIZE',None)
    assert len(results)==16
    path.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
