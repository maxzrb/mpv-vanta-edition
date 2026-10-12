// 逐绘制维护读回：只在本工具启动的诊断进程内复制源纹理和各次实际写回。
const seen = new Set(), states = new Map(), shaderSources = new Map(), shaderIR = new Map(), bytecodes = new Map(), compiledIR = new Map();
const colorSpaces=new Map();
let requested = null, sequence = 0, busy = false, chainCount = 0;
function method(o, n) { return o.readPointer().add(n * Process.pointerSize).readPointer(); }
function call(o, n, result, args) { return new NativeFunction(method(o,n), result, ['pointer',...args]); }
function release(o) { if(o&&!o.isNull())call(o,2,'uint',[])(o); }
function state(o) {
    const key=o.toString(); if(!states.has(key))states.set(key,{ps:[],cs:[],rt:[],uav:[],psCB:[],csCB:[],psShader:'',csShader:''});
    return states.get(key);
}
function hook(o,n,label,handlers) {
    const address=method(o,n),key=label+address;
    if(seen.has(key))return;seen.add(key);Interceptor.attach(address,handlers);
}
function readTexture(context,source,meta) {
    let device=null,staging=null,mapped=false;
    try {
        const d=Memory.alloc(44),output=Memory.alloc(8);
        call(source,10,'void',['pointer'])(source,d);
        const width=d.readU32(),height=d.add(4).readU32(),format=d.add(16).readU32();
        const bytesPerPixel={10:8,11:8,24:4,28:4,87:4,56:2,61:1,49:2,35:4,54:2,34:4,2:16,41:4};
        if(!bytesPerPixel[format]||width*height>16777216||d.add(20).readU32()!==1)
            throw new Error('阶段纹理格式或尺寸不支持 '+format+' '+width+'x'+height);
        call(source,3,'void',['pointer'])(source,output);device=output.readPointer();
        const subresource=meta.subresource||0;
        d.add(8).writeU32(1);d.add(12).writeU32(1);d.add(28).writeU32(3);
        d.add(32).writeU32(0);d.add(36).writeU32(0x20000);d.add(40).writeU32(0);
        if(call(device,5,'int',['pointer','pointer','pointer'])(device,d,ptr(0),output)!==0)throw new Error('阶段 staging 创建失败');
        staging=output.readPointer();
        call(context,46,'void',['pointer','uint','uint','uint','uint','pointer','uint','pointer'])(context,staging,0,0,0,0,source,subresource,ptr(0));
        const map=Memory.alloc(16);
        if(call(context,14,'int',['pointer','uint','uint','uint','pointer'])(context,staging,0,1,0,map)!==0)throw new Error('阶段 Map 失败');
        mapped=true;const stride=map.add(8).readU32();
        send({...meta,capture:requested,sequence:sequence++,width,height,format,stride,bytes_per_pixel:bytesPerPixel[format]},
             map.readPointer().readByteArray(stride*height));
    } catch(e) {send({capture:requested,sequence:sequence++,...meta,error:String(e)});}
    finally {if(mapped)call(context,15,'void',['pointer','uint'])(context,staging,0);release(staging);release(device);}
}
function readView(context,view,meta) {
    if(!view||view.isNull())return;
    const output=Memory.alloc(8);let source=null;
    try {
        call(view,7,'void',['pointer'])(view,output);source=output.readPointer();
        const kind=Memory.alloc(4);call(source,7,'void',['pointer'])(source,kind);
        if(kind.readU32()!==3)return; // 读取二维主图像；辅助 LUT 的作用由独立数值参考检验。
        readTexture(context,source,{...meta,resource:source.toString()});
    } finally {release(source);}
}
function readConstants(context,buffers){
    const values=[];
    for(let slot=0;slot<buffers.length;slot++){const source=buffers[slot];if(!source||source.isNull())continue;
        let device=null,staging=null,mapped=false;
        try{const desc=Memory.alloc(24),output=Memory.alloc(8);call(source,10,'void',['pointer'])(source,desc);const size=desc.readU32();
            if(size>65536)throw new Error('常量缓冲尺寸异常');
            call(source,3,'void',['pointer'])(source,output);device=output.readPointer();
            desc.add(4).writeU32(3);desc.add(8).writeU32(0);desc.add(12).writeU32(0x20000);desc.add(16).writeU32(0);desc.add(20).writeU32(0);
            if(call(device,3,'int',['pointer','pointer','pointer'])(device,desc,ptr(0),output)!==0)throw new Error('常量 staging 创建失败');staging=output.readPointer();
            call(context,47,'void',['pointer','pointer'])(context,staging,source);
            const map=Memory.alloc(16);if(call(context,14,'int',['pointer','uint','uint','uint','pointer'])(context,staging,0,1,0,map)!==0)throw new Error('常量读回失败');mapped=true;
            const data=map.readPointer(),floats=[];for(let i=0;i<size/4;i++)floats.push(data.add(i*4).readFloat());values.push({slot,floats});
        }finally{if(mapped)call(context,15,'void',['pointer','uint'])(context,staging,0);release(staging);release(device);}
    }return values;
}
function snapshot(context,phase,compute,draw) {
    if(requested===null||busy||sequence>=160)return;
    busy=true;
    try {
        const s=state(context),source=shaderSources.get(compute?s.csShader:s.psShader)||'';
        const constants=phase==='input'?readConstants(context,compute?s.csCB:s.psCB):[];
        const views=phase==='input'?(compute?s.cs:s.ps):(compute?s.uav:s.rt);
        for(let slot=0;slot<views.length;slot++)if(views[slot]&&!views[slot].isNull())
            readView(context,views[slot],{phase,draw,compute,slot,shader:source,constants,shader_ir:shaderIR.get(compute?s.csShader:s.psShader)||''});
    } finally {busy=false;}
}
function watchContext(context) {
    for(const [n,field] of [[8,'ps'],[67,'cs'],[68,'uav'],[16,'psCB'],[71,'csCB']])hook(context,n,'bind'+n,{
        onEnter(a){if(busy)return;const s=state(a[0]),first=a[1].toUInt32(),count=a[2].toUInt32();
            for(let i=0;i<count;i++)s[field][first+i]=a[3].isNull()?ptr(0):a[3].add(i*8).readPointer();}
    });
    hook(context,33,'rt',{onEnter(a){if(busy)return;const s=state(a[0]),count=a[1].toUInt32();s.rt=[];
        for(let i=0;i<count;i++)s.rt.push(a[2].add(i*8).readPointer());}});
    hook(context,34,'rtuav',{onEnter(a){if(busy)return;const s=state(a[0]),count=a[1].toUInt32();
        if(count===0xffffffff)return;s.rt=[];
        for(let i=0;i<count;i++)s.rt.push(a[2].add(i*8).readPointer());}});
    for(const [n,field] of [[9,'psShader'],[69,'csShader']])hook(context,n,'shader'+n,{
        onEnter(a){if(!busy)state(a[0])[field]=a[1].toString();}
    });
    for(const n of [12,13,20,21,38,41,42])hook(context,n,'draw'+n,{
        onEnter(a){this.gpu_context=a[0];this.compute=n>=41;this.draw=sequence;
            snapshot(this.gpu_context,'input',this.compute,this.draw);},
        onLeave(){snapshot(this.gpu_context,'output',this.compute,this.draw);}
    });
}
function watchDevice(device) {
    const output=Memory.alloc(8);call(device,40,'void',['pointer'])(device,output);
    const context=output.readPointer();watchContext(context);release(context);
    // 硬解启用多线程保护后，驱动可能切换即时上下文的方法表；取得上下文时重新挂接。
    hook(device,40,'getContext',{onEnter(a){this.output=a[1];},onLeave(){
        if(!this.output.isNull())watchContext(this.output.readPointer());
    }});
    for(const n of [15,18])hook(device,n,'createShader'+n,{
        onEnter(a){this.code=a[1].toString();this.output=a[4];},
        onLeave(r){if(r.toInt32()===0){const key=this.output.readPointer().toString();shaderSources.set(key,bytecodes.get(this.code)||'');shaderIR.set(key,compiledIR.get(this.code)||'');}}
    });
}
function watchChain(chain) {
    chainCount++;
    colorSpaces.set(chain.toString(),0);
    const guid=Memory.alloc(16),output=Memory.alloc(8);
    guid.writeByteArray([0xdb,0x9b,0xd9,0x94,0xf8,0xf1,0xb0,0x4a,0xb2,0x36,0x7d,0xa0,0x17,0x0e,0xda,0xb1]);
    if(call(chain,0,'int',['pointer','pointer'])(chain,guid,output)===0){const modern=output.readPointer();
        hook(modern,38,'colorSpace',{onEnter(a){this.chain=a[0].toString();this.color=a[1].toUInt32();},onLeave(r){if(r.toInt32()===0)colorSpaces.set(this.chain,this.color);}});release(modern);
    }
    hook(chain,8,'present',{onEnter(a){
        if(requested===null||sequence===0||(a[2].toUInt32()&1))return;
        let source=null,device=null,context=null;
        try {
            const iid=Memory.alloc(16),output=Memory.alloc(8);
            iid.writeByteArray([0xf2,0xaa,0x15,0x6f,0x08,0xd2,0x89,0x4e,0x9a,0xb4,0x48,0x95,0x35,0xd3,0x4f,0x9c]);
            if(call(a[0],9,'int',['uint','pointer','pointer'])(a[0],0,iid,output)!==0)throw new Error('GetBuffer 失败');
            source=output.readPointer();call(source,3,'void',['pointer'])(source,output);device=output.readPointer();
            call(device,40,'void',['pointer'])(device,output);context=output.readPointer();busy=true;
            readTexture(context,source,{phase:'present',draw:sequence,compute:false,slot:0,shader:'',color_space:colorSpaces.get(a[0].toString())});
            send({capture:requested,done:true,count:sequence});
        } catch(e){send({capture:requested,error:String(e),done:true});}
        finally{busy=false;requested=null;release(context);release(device);release(source);}
    }});
}
function watchFactory(object) {
    const guid=Memory.alloc(16),output=Memory.alloc(8);
    guid.writeByteArray([0x1c,0x3a,0xc8,0x50,0x72,0xe0,0x48,0x4c,0x87,0xb0,0x36,0x30,0xfa,0x36,0xa6,0xd0]);
    const modern=call(object,0,'int',['pointer','pointer'])(object,guid,output)===0?output.readPointer():null;
    for(const [n,out] of (modern?[[10,3],[15,6],[24,4]]:[[10,3]]))hook(n===10?object:modern,n,'chain'+n,{
        onEnter(a){this.output=a[out];},onLeave(r){if(r.toInt32()===0&&!this.output.isNull())watchChain(this.output.readPointer());}
    });
    release(modern);
}
Process.attachModuleObserver({onAdded(module){
    const name=module.name.toLowerCase();
    if(name==='d3d11.dll'){
        const address=module.findExportByName('D3D11CreateDevice');
        if(address)Interceptor.attach(address,{onEnter(a){this.output=a[7];},onLeave(r){if(r.toInt32()===0&&!this.output.isNull())watchDevice(this.output.readPointer());}});
    }
    if(name==='dxgi.dll')for(const n of ['CreateDXGIFactory','CreateDXGIFactory1','CreateDXGIFactory2']){
        const address=module.findExportByName(n);if(!address)continue;
        Interceptor.attach(address,{onEnter(a){this.output=a[n==='CreateDXGIFactory2'?2:1];},onLeave(r){if(r.toInt32()===0)watchFactory(this.output.readPointer());}});
    }
    if(name.startsWith('d3dcompiler_')){
        const address=module.findExportByName('D3DCompile');if(!address||seen.has('compile'+address))return;seen.add('compile'+address);
        Interceptor.attach(address,{onEnter(a){
            this.output=a[9];this.source='';
            // 编译器内部也可能传入非文本数据；读取失败不影响原调用。
            try{this.source=a[0].readUtf8String(a[1].toUInt32());}catch(e){}
        },onLeave(r){
            if(r.toInt32()!==0||this.output.isNull())return;const blob=this.output.readPointer();
            const code=call(blob,3,'pointer',[])(blob);bytecodes.set(code.toString(),this.source);
            const dis=module.findExportByName('D3DDisassemble');
            if(dis){let assembly=null;try{const output=Memory.alloc(8),size=call(blob,4,'size_t',[])(blob);
                if(new NativeFunction(dis,'int',['pointer','size_t','uint','pointer','pointer'])(code,size,0,ptr(0),output)===0){assembly=output.readPointer();compiledIR.set(code.toString(),call(assembly,3,'pointer',[])(assembly).readUtf8String());}
            }finally{release(assembly);}}
        }});
    }
}});
rpc.exports={arm(id){requested=id;sequence=0;},status(){return {chainCount,contexts:states.size,shaderSources:shaderSources.size,sequence};}};
