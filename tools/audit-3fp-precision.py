"""固定公开 3FP 源码／预编译 Shader 的精度核查，不启动或重编译播放器。"""
import ctypes,hashlib,json,math,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tmp/modernization/3fp-current-20261011'
OUT=ROOT/'tmp/modernization/color-accuracy-20261011/3fp-bytecode'


def method(obj,index,result,args):
    table=ctypes.cast(obj,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    return ctypes.WINFUNCTYPE(result,ctypes.c_void_p,*args)(table[index])


def disassemble(data):
    library=ctypes.WinDLL('d3dcompiler_47.dll')
    fun=library.D3DDisassemble
    fun.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)]
    fun.restype=ctypes.c_long
    buffer=ctypes.create_string_buffer(data);output=ctypes.c_void_p()
    assert fun(buffer,len(data),0,None,ctypes.byref(output))==0
    try:
        address=method(output,3,ctypes.c_void_p,[])(output)
        size=method(output,4,ctypes.c_size_t,[])(output)
        return ctypes.string_at(address,size).rstrip(b'\0').decode('utf-8')
    finally:method(output,2,ctypes.c_ulong,[])(output)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True,encoding='utf-8').strip()
    assert commit=='20bcc001b24f6b6de4575bddf9b93ec452795b0d'
    rows=[]
    for filename in ('ShaderBytecode.h','SdrShaderBytecode.h'):
        header=SOURCE/'FFF.Native/3FP/Render'/filename
        text=header.read_text(encoding='utf-8-sig')
        arrays=re.findall(r'const BYTE (\w+)\[\]\s*=\s*\{([^}]+)\}',text,re.S)
        assert arrays,filename
        for name,body in arrays:
            data=bytes(map(int,re.findall(r'\b\d+\b',body)))
            assert data.startswith(b'DXBC'),name
            assembly=disassemble(data)
            profile=re.search(r'^\s*([pv]s_5_0)\s*$',assembly,re.M).group(1)
            reduced=bool(re.search(r'\b(?:min16\w*|min10\w*|half)\b',assembly))
            assert not reduced,name
            (OUT/(name+'.txt')).write_text(assembly+'\n',encoding='utf-8',newline='\n')
            rows.append(dict(name=name,profile=profile,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                             reduced_precision_declarations=False))
    renderer=SOURCE/'FFF.Native/3FP/Render/VideoRenderer.cpp'
    code=renderer.read_text(encoding='utf-8-sig')
    assert 'DXGI_FORMAT_R16G16B16A16_FLOAT' in code
    assert 'DXGI_FORMAT_R32G32B32A32_FLOAT' not in code
    assert 'pow(max(scene,0.0),1.2)' in code
    hlg=[]
    for encoded in ((.75,.75,.75),(.75,.25,.25),(.25,.75,.25)):
        scene=[v*v/3 if v<=.5 else (math.exp((v-.55991073)/.17883277)+.28466892)/12 for v in encoded]
        luminance=sum(v*k for v,k in zip(scene,(.2627,.6780,.0593)))
        standard=[1000*v*luminance**.2 for v in scene]
        implemented=[1000*v**1.2 for v in scene]
        hlg.append(dict(encoded=encoded,bt2100_reference_nits=standard,public_base_shader_nits=implemented,
                        max_absolute_difference_nits=max(abs(a-b) for a,b in zip(standard,implemented))))
    assert 'curve.Format = DXGI_FORMAT_R32_FLOAT' in code
    result=dict(commit=commit,public_shader_bytecode=rows,hdr_swapchain='R16G16B16A16_FLOAT',
        dynamic_tone_curve_auxiliary_texture='R32_FLOAT',
        scrgb_primaries='BT.709',scrgb_unit_nits=80,public_hdr_or_source_precision_output_bits=[8,10,16],
        all_fp32_storage_required=False,current_public_source_checked=True,
        physical_or_3fp_playback_measurement=False,hlg_base_formula_comparison=hlg,
        source_sha256={str(p.relative_to(SOURCE)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (renderer,SOURCE/'tools/compare-kernel-pixels.py',SOURCE/'tools/generate_shader_bytecode.py')})
    path=ROOT/'docs/modernization/3fp-precision-comparison-20261011.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('3FP公开字节码',len(rows),'组精度检查 PASS；HDR/scRGB为FP16存储，主Shader常规FP32算术')
    print('HLG彩色反例',hlg[1])


if __name__=='__main__':main()
