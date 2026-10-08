// 仅供独立测试进程动态插桩；记录COM调用的QPC和调用位置，不修改磁盘DLL。
const seen = new Set();
const callbacks = [];
const interfaces = new Set();
const contexts = [];
const context1Checked=new Set();
const context1Objects=new Map();
const descriptions = new Map();
const presenting = new Set();
const adapters = [];
const copyContexts = new Map();
const separateSurfaces = new Map();
const completionQueries=new Map();
const replayRetained=new Set();
let replayCopy=null;
const activeRenderers=new Map();
const earlyFrames=new Map();
let renderingDevice=null;
let renderingContext=null;
let lastDecodeBegin=0;
function texture(object) {
    const key=object.toString();if (descriptions.has(key)) return descriptions.get(key);
    const memory=Memory.alloc(44);
    new NativeFunction(method(object,10),'void',['pointer','pointer'])(object,memory);
    const values=Array.from({length:11},(_,i)=>memory.add(i*4).readU32());
    descriptions.set(key,values);return values;
}
const kernel = Process.getModuleByName('kernel32.dll');
const qpc = new NativeFunction(kernel.getExportByName('QueryPerformanceCounter'), 'int', ['pointer']);
const clock = Memory.alloc(8);
let records = [];
function now() { qpc(clock); return clock.readS64().toNumber(); }
function location(address) {
    const module = Process.findModuleByAddress(address);
    return module ? module.name + '+' + address.sub(module.base) : address.toString();
}
function method(object, index) { return object.readPointer().add(index * Process.pointerSize).readPointer(); }
function watch(address, name, detail) {
    const key = address.toString();
    if (seen.has(key)) return;
    seen.add(key);
    send({hook: name, address: location(address)});
    if (name==='CopySubresourceRegion' && DISCARD_COPY) {
        // 完整像素实验：按mpv的做法使用明确有效区域和CopySubresourceRegion1 DISCARD。
        const callback=new NativeCallback(function(object,destination,subresource,x,y,z,source,sourceSubresource,box) {
            const begin=now(),key=object.toString();let context1=copyContexts.get(key);
            if (!context1) {
                const iid=Memory.alloc(16),output=Memory.alloc(Process.pointerSize);
                iid.writeByteArray([0xaa,0x6f,0x2c,0xbb,0xfb,0xb5,0x82,0x40,0x8e,0x6b,0x38,0x8b,0x8c,0xfa,0x90,0xe1]);
                const result=new NativeFunction(method(object,0),'int',['pointer','pointer','pointer'])(object,iid,output);
                if (result!==0) throw new Error('无法取得Context1执行完整复制');
                context1=output.readPointer();copyContexts.set(key,context1);
            }
            const desc=texture(destination),region=Memory.alloc(24);
            [0,0,0,desc[0],desc[1],1].forEach((value,i)=>region.add(i*4).writeU32(value));
            new NativeFunction(method(context1,115),'void',
                ['pointer','pointer','uint','uint','uint','uint','pointer','uint','pointer','uint'])(
                    context1,destination,subresource,x,y,z,source,sourceSubresource,region,2);
            records.push({name:'CopyDiscardReplacement',begin,end:now(),thread:Process.getCurrentThreadId(),result:0,
                detail:{source:texture(source),destination:desc,source_subresource:sourceSubresource}});
        },'void',['pointer','pointer','uint','uint','uint','uint','pointer','uint','pointer']);
        callbacks.push(callback);Interceptor.replace(address,callback);return;
    }
    if ((name === 'Draw' && SKIP_DRAW) || (name.startsWith('Copy') && SKIP_COPY)) {
        // 跳过绘制或纹理复制分别隔离GPU负载；此时画面不具有效性。
        const types=name==='Draw' ? ['pointer','uint','uint'] :
            name==='CopyResource' ? ['pointer','pointer','pointer'] :
            ['pointer','pointer','uint','uint','uint','uint','pointer','uint','pointer',
             ...(name==='CopySubresourceRegion1' ? ['uint'] : [])];
        const callback=new NativeCallback(function() {
            const tick=now(); records.push({name:name+'Skipped',begin:tick,end:tick,
                thread:Process.getCurrentThreadId(),result:0,detail:{}});
        },'void',types);
        callbacks.push(callback); Interceptor.replace(address,callback); return;
    }
    if (name === 'VideoProcessorBlt' && SKIP_VIDEO_PROCESSOR) {
        // 因果隔离实验：跳过像素处理，输出无效，仅检查硬解／呈现吞吐。
        const callback = new NativeCallback(function(object,processor,output,frame,count,streams) {
            const tick = now();
            records.push({name:'VideoProcessorBltSkipped',begin:tick,end:tick,
                          thread:Process.getCurrentThreadId(),result:0,detail:{}});
            return 0;
        }, 'int', ['pointer','pointer','pointer','uint','uint','pointer']);
        callbacks.push(callback);
        Interceptor.replace(address,callback);
        return;
    }
    Interceptor.attach(address, {
        onEnter(args) {
            if (name==='DecoderBeginFrame' && DECODE_INTERVAL_MS>0) {
                const tick=now(),remaining=DECODE_INTERVAL_MS-(tick-lastDecodeBegin)/10000;
                if (remaining>0) new NativeFunction(kernel.getExportByName('Sleep'),'void',['uint'])(Math.ceil(remaining));
                lastDecodeBegin=now();
                records.push({name:'DecodePacingWait',begin:tick,end:lastDecodeBegin,
                    thread:this.threadId,result:0,detail:{interval_ms:DECODE_INTERVAL_MS}});
            }
            this.begin = now(); this.thread = this.threadId;
            this.object=args[0];
            if (name==='Present') presenting.add(this.threadId);
            this.caller = location(this.returnAddress);
            this.detail = detail ? detail(args) : {};
            if (name==='CopySubresourceRegion') {
                this.detail={destination:texture(args[1]),source:texture(args[6]),
                    source_subresource:args[7].toInt32()};
                if (COPY_BOX>0) {
                    const box=Memory.alloc(24);[0,0,0,COPY_BOX,COPY_BOX,1].forEach((x,i)=>box.add(i*4).writeU32(x));
                    this.box=box;args[8]=box;this.detail.box=COPY_BOX;
                }
                if (IDLE_COPY_PROBE && this.caller.startsWith('FFF.Native.dll')) {
                    const values=Array.from({length:9},(_,i)=>args[i]);
                    const box=Memory.alloc(24);
                    if (args[8].isNull()) throw new Error('复制区域未提供');
                    box.writeByteArray(args[8].readByteArray(24));values[8]=box;
                    for (const index of [0,1,6]) {
                        const resource=values[index],key=resource.toString();
                        if (!replayRetained.has(key)) {
                            replayRetained.add(key);
                            new NativeFunction(method(resource,1),'uint',['pointer'])(resource);
                        }
                    }
                    replayCopy={address,values};
                }
            }
        },
        onLeave(result) {
            if ((name==='CopySubresourceRegion' && WAIT_COPY && this.caller.startsWith('FFF.Native.dll')) ||
                (name==='DecoderEndFrame' && WAIT_DECODE && renderingContext)) {
                const object=name==='DecoderEndFrame' ? renderingContext : this.object;
                const key=object.toString();let query=completionQueries.get(key);
                if (!query) {
                    const definition=Memory.alloc(8),output=Memory.alloc(Process.pointerSize);
                    definition.writeU32(0);definition.add(4).writeU32(0);
                    const status=new NativeFunction(method(renderingDevice,24),'int',
                        ['pointer','pointer','pointer'])(renderingDevice,definition,output);
                    if (status!==0) throw new Error('GPU完成查询创建失败：'+status);
                    query=output.readPointer();completionQueries.set(key,query);
                }
                const begin=now();
                new NativeFunction(method(object,28),'void',['pointer','pointer'])(object,query);
                new NativeFunction(method(object,111),'void',['pointer'])(object);
                const getData=new NativeFunction(method(object,29),'int',['pointer','pointer','pointer','uint','uint']);
                const sleep=new NativeFunction(kernel.getExportByName('Sleep'),'void',['uint']);
                let status=1;
                while ((status=getData(object,query,ptr(0),0,1))===1) {
                    if (now()-begin>20000000) throw new Error('GPU复制完成查询超时');
                    sleep(1);
                }
                if (status!==0) throw new Error('GPU复制完成查询失败：'+status);
                records.push({name:name==='DecoderEndFrame' ? 'DecodeCompletionWait' : 'CopyCompletionWait',begin,end:now(),thread:this.thread,
                    caller:this.caller,result:status,detail:{}});
            }
            // 完整像素实验：只改变提交时机，不跳过解码、复制或绘制。
            if ((name==='CopySubresourceRegion' && FLUSH_COPY) ||
                (name==='DecoderEndFrame' && FLUSH_DECODE && renderingContext)) {
                const object=name==='DecoderEndFrame' ? renderingContext : this.object;
                new NativeFunction(method(object,111),'void',['pointer'])(object);
            }
            if (name==='Present') presenting.delete(this.threadId);
            records.push({name, begin: this.begin, end: now(), thread: this.thread,
                          caller: this.caller, result: result.toInt32(), detail: this.detail});
        }
    });
}
function query(object) {
    const address = method(object, 0), key = 'query' + address;
    if (seen.has(key)) return;
    seen.add(key);
    Interceptor.attach(address, {
        onEnter(args) {
            this.iid = Array.from(new Uint8Array(args[1].readByteArray(16))).map(x => x.toString(16).padStart(2, '0')).join('');
            this.output = args[2];
        },
        onLeave(result) {
            if (result.toInt32() !== 0) return;
            const object = this.output.readPointer();
            if (!interfaces.has(this.iid)) {
                interfaces.add(this.iid);send({interface:this.iid});
            }
            if (this.iid === 'aa6f2cbbfbb582408e6b388b8cfa90e1') {
                context(object); watch(method(object,115),'CopySubresourceRegion1');
            }
            if (this.iid === '004e7e9b2c340641a19f4f2704f689f0') {
                const address=method(object,5),key='protected'+address;
                if (!seen.has(key)) {
                    seen.add(key);
                    Interceptor.attach(address,{onLeave() {
                        // 启用多线程保护会切换上下文方法表，必须重新采集实际入口。
                        for (const value of contexts) context(value);
                    }});
                }
            }
            if (this.iid === '451cf2610e3c744a9cea67100d9ad5e4') {
                for (const [index, name] of [[9,'DecoderBeginFrame'],[10,'DecoderEndFrame'],
                     [11,'SubmitDecoderBuffers'],[53,'VideoProcessorBlt']])
                    watch(method(object,index),name);
            }
            if (this.iid==='5b4dec105a978946b9e4d0aac30fe333') {
                const createDecoder=method(object,3),decoderKey='createDecoder'+createDecoder;
                if (!seen.has(decoderKey)) {
                    seen.add(decoderKey);
                    Interceptor.attach(createDecoder,{onEnter(args) {
                        send({decoder_descriptor:Array.from(new Uint8Array(args[1].readByteArray(28))),
                            decoder_config:Array.from(new Uint8Array(args[2].readByteArray(100)))});
                    }});
                }
            }
            if (this.iid==='5b4dec105a978946b9e4d0aac30fe333' && SEPARATE_SURFACES) {
                const address=method(object,7),key='decoderView'+address;
                if (!seen.has(key)) {
                    seen.add(key);
                    Interceptor.attach(address,{
                        onEnter(args) {
                            const source=args[1],desc=texture(source);
                            if (desc[0]!==7680 || desc[1]!==4352 || desc[3]!==22) return;
                            let surfaces=separateSurfaces.get(source.toString());
                            if (!surfaces) {
                                surfaces=[];
                                const definition=Memory.alloc(44),output=Memory.alloc(Process.pointerSize);
                                desc.forEach((value,i)=>definition.add(i*4).writeU32(i===3 ? 1 : value));
                                const create=new NativeFunction(method(renderingDevice,5),'int',
                                    ['pointer','pointer','pointer','pointer']);
                                for (let i=0;i<22;i++) {
                                    const result=create(renderingDevice,definition,ptr(0),output);
                                    if (result!==0) throw new Error('创建独立解码纹理失败：'+result);
                                    surfaces.push(output.readPointer());
                                }
                                separateSurfaces.set(source.toString(),surfaces);
                                send({separate_surface_count:surfaces.length});
                            }
                            const index=args[2].add(20).readU32(),view=Memory.alloc(24);
                            view.writeByteArray(args[2].readByteArray(24));view.add(20).writeU32(0);
                            this.view=view;args[1]=surfaces[index];args[2]=view;
                        }
                    });
                }
            }
            if (this.iid === '0f97db777662ba48ba28070143b4392c')
                watch(method(object,12),'SetMaximumFrameLatency', args => ({value:args[1].toInt32()}));
            if (this.iid === '1c3ac85072e0484c87b03630fa36a6d0') factory(object);
        }
    });
}
function context(object) {
    if (!contexts.some(x => x.equals(object))) contexts.push(object);
    query(object);
    for (const [index,name] of [[13,'Draw'],[14,'Map'],[15,'Unmap'],[29,'GetData'],
          [46,'CopySubresourceRegion'],[47,'CopyResource'],[58,'ExecuteCommandList'],[111,'Flush']])
        watch(method(object,index),name);
    const key=object.toString();
    if (!context1Checked.has(key)) {
        context1Checked.add(key);
        const iid=Memory.alloc(16),output=Memory.alloc(Process.pointerSize);
        iid.writeByteArray([0xaa,0x6f,0x2c,0xbb,0xfb,0xb5,0x82,0x40,0x8e,0x6b,0x38,0x8b,0x8c,0xfa,0x90,0xe1]);
        if (new NativeFunction(method(object,0),'int',['pointer','pointer','pointer'])(object,iid,output)===0) {
            const context1=output.readPointer();
            context1Objects.set(key,context1);
            watch(method(context1,115),'CopySubresourceRegion1',args=>({
                destination:texture(args[1]),source:texture(args[6]),
                source_subresource:args[7].toInt32(),flags:args[9].toInt32()}));
            new NativeFunction(method(context1,2),'uint',['pointer'])(context1);
        }
    }
    const context1=context1Objects.get(key);
    if (context1) watch(method(context1,115),'CopySubresourceRegion1',args=>({
        destination:texture(args[1]),source:texture(args[6]),
        source_subresource:args[7].toInt32(),flags:args[9].toInt32()}));
}
function chain(object) {
    watch(method(object,8),'Present', args => ({sync:args[1].toInt32(),flags:args[2].toInt32()}));
    watch(method(object,31),'SwapChainSetMaximumFrameLatency',args=>({value:args[1].toInt32()}));
}
function factory(object) {
    query(object);
    const address = method(object,15), key = 'factory' + address;
    if (seen.has(key)) return;
    seen.add(key);
    Interceptor.attach(address, {
        onEnter(args) {
            this.output = args[6];
            {
                const device=args[1],guid=Memory.alloc(16),output=Memory.alloc(Process.pointerSize);
                guid.writeByteArray([0x0f,0x97,0xdb,0x77,0x76,0x62,0xba,0x48,0xba,0x28,0x07,0x01,0x43,0xb4,0x39,0x2c]);
                const result=new NativeFunction(method(device,0),'int',['pointer','pointer','pointer'])(device,guid,output);
                if (result===0) {
                    const dxgi=output.readPointer(),old=Memory.alloc(4);
                    const priority=Memory.alloc(4);
                    const priorityRead=new NativeFunction(method(dxgi,11),'int',['pointer','pointer'])(dxgi,priority);
                    const priorityChanged=GPU_PRIORITY===null ? null :
                        new NativeFunction(method(dxgi,10),'int',['pointer','int'])(dxgi,GPU_PRIORITY);
                    send({gpu_priority_before:priorityRead===0 ? priority.readS32() : null,
                        gpu_priority_requested:GPU_PRIORITY,gpu_priority_result:priorityChanged});
                    const adapterPointer=Memory.alloc(Process.pointerSize);
                    if (new NativeFunction(method(dxgi,7),'int',['pointer','pointer'])(dxgi,adapterPointer)===0) {
                        const adapter=adapterPointer.readPointer(),adapter3=Memory.alloc(Process.pointerSize);
                        const iid=Memory.alloc(16);iid.writeByteArray([0xa4,0x67,0x59,0x64,0x92,0x13,0x10,0x43,0xa7,0x98,0x80,0x53,0xce,0x3e,0x93,0xfd]);
                        if (new NativeFunction(method(adapter,0),'int',['pointer','pointer','pointer'])(adapter,iid,adapter3)===0)
                            adapters.push(adapter3.readPointer());
                        new NativeFunction(method(adapter,2),'uint',['pointer'])(adapter);
                    }
                    new NativeFunction(method(dxgi,13),'int',['pointer','pointer'])(dxgi,old);
                    const changed=DEVICE_LATENCY>0 ? new NativeFunction(method(dxgi,12),'int',['pointer','uint'])(dxgi,DEVICE_LATENCY) : null;
                    send({device_latency_before:old.readU32(),requested:DEVICE_LATENCY,result:changed});
                    new NativeFunction(method(dxgi,2),'uint',['pointer'])(dxgi);
                } else send({device_latency_query_error:result});
            }
        },
        onLeave(result) { if (result.toInt32() === 0) chain(this.output.readPointer()); }
    });
}
const modules = new Set();
function instrument(module) {
    if (modules.has(module.name.toLowerCase())) return;
    modules.add(module.name.toLowerCase());
    if (module.name.toLowerCase()==='avutil-61.dll') {
        if (EARLY_COPY) Interceptor.attach(module.getExportByName('av_frame_clone'),{
            onLeave(frame) {
                const renderer=activeRenderers.get(this.threadId);
                if (!renderer || frame.isNull()) return;
                const object=renderer.add(0x18).readPointer(),destination=renderer.add(0x78).readPointer();
                const source=frame.readPointer(),slice=frame.add(8).readPointer().toUInt32();
                const desc=texture(source);
                if (desc[0]!==7680 || desc[1]!==4352 || desc[4]!==104 || destination.isNull())
                    throw new Error('提前复制资源与已核验的P010路径不匹配');
                const box=Memory.alloc(24);
                [0,0,0,renderer.add(0x330).readU32(),renderer.add(0x334).readU32(),1].forEach(
                    (value,i)=>box.add(i*4).writeU32(value));
                const begin=now();
                new NativeFunction(method(object,46),'void',
                    ['pointer','pointer','uint','uint','uint','uint','pointer','uint','pointer'])(
                    object,destination,0,0,0,0,source,slice,box);
                earlyFrames.set(renderer.toString(),frame);
                records.push({name:'EarlyCopy',begin,end:now(),thread:this.threadId,result:0,
                    detail:{source:desc,destination:texture(destination),slice}});
            }
        });
        Interceptor.attach(module.getExportByName('av_hwframe_ctx_init'),{
            onEnter(args) {
                // 当前AVHWFramesContext公共布局；先校验尺寸和池大小再修改实验值。
                const frame=args[0].add(8).readPointer();
                const width=frame.add(68).readS32(),height=frame.add(72).readS32(),pool=frame.add(56).readS32();
                send({frame_pool:pool,width,height});
                if (POOL_SIZE>0 && width===7680 && height===4352 && pool===22) {
                    frame.add(56).writeS32(POOL_SIZE);send({frame_pool_changed:POOL_SIZE});
                }
            }
        });
    }
    if (module.name.toLowerCase()==='avcodec-63.dll' && SEPARATE_SURFACES) {
        Interceptor.attach(module.getExportByName('avcodec_receive_frame'),{
            onEnter(args) { this.frame=args[1]; },
            onLeave(result) {
                if (result.toInt32()!==0) return;
                const source=this.frame.readPointer(),surfaces=separateSurfaces.get(source.toString());
                if (!surfaces) return;
                const index=this.frame.add(8).readPointer().toInt32();
                if (index<0 || index>=surfaces.length) throw new Error('解码slice超出独立纹理范围');
                // 内部解码引用仍使用原surface编号，只替换交给播放器的输出帧资源。
                this.frame.writePointer(surfaces[index]);this.frame.add(8).writePointer(ptr(0));
            }
        });
    }
    if (module.name.toLowerCase()==='fff.native.dll') {
        if (RELEASE_AFTER_COPY) Interceptor.attach(module.base.add(0x35ac0),{
            onEnter(args) { this.renderer=args[0]; },
            onLeave() {
                const renderer=this.renderer,field=renderer.add(0x11d0);
                if (field.readPointer().isNull() || renderer.add(0x11d8).readU8()!==1) return;
                // 复制命令已提交，按mpv映射器的行为释放自己的硬件帧引用。
                const free=Process.getModuleByName('avutil-61.dll').getExportByName('av_frame_free');
                new NativeFunction(free,'void',['pointer'])(field);
                send({released_after_copy:true});
            }
        });
        if (EARLY_COPY) {
            // 已核验函数起点：把真正的像素复制移到Render持锁的帧接收阶段。
            Interceptor.attach(module.base.add(0x3aaf0),{
                onEnter(args) { activeRenderers.set(this.threadId,args[0]); },
                onLeave() { activeRenderers.delete(this.threadId); }
            });
            Interceptor.attach(module.base.add(0x35ac0),{onEnter(args) {
                const renderer=args[0],frame=earlyFrames.get(renderer.toString());
                if (frame && frame.equals(renderer.add(0x11d0).readPointer()))
                    renderer.add(0x11d8).writeU8(1);
            }});
        }
        // 偏移仅匹配已核验SHA的094c19e…版本，现场取实际渲染上下文再安装COM探针。
        for (const offset of [0x347a0,0x35520,0x3cf60]) {
            Interceptor.attach(module.base.add(offset),{onEnter(args) {
                context(args[0].add(0x18).readPointer()); Interceptor.flush();
            }});
        }
    }
    if (module.name.toLowerCase() === 'd3d11.dll') {
        send({module:module.name,base:module.base});
        Interceptor.attach(module.getExportByName('D3D11CreateDevice'), {
            onEnter(args) {
                this.device=args[7]; this.ctxOut=args[9];
                send({device_create_flags:args[3].toInt32(),driver_type:args[1].toInt32()});
                if (DEVICE_FLAGS>=0) {
                    args[3]=ptr(DEVICE_FLAGS);send({device_flags_changed:DEVICE_FLAGS});
                }
            },
            onLeave(result) {
                send({created:result.toInt32(), device:this.device.toString(),context:this.ctxOut.toString()});
                if (result.toInt32() !== 0) return;
                if (!this.device.isNull()) {
                    const object=this.device.readPointer();
                    renderingDevice=object;
                    query(object);
                    const createView=method(object,7),viewKey='srv'+createView;
                    if (!seen.has(viewKey)) {
                        seen.add(viewKey);
                        Interceptor.attach(createView,{
                            onEnter(args) {
                                this.resource=args[1];this.output=args[3];
                                this.desc=args[2].isNull() ? null :
                                    Array.from({length:6},(_,i)=>args[2].add(i*4).readU32());
                            },
                            onLeave(result) {
                                // 记录实际平面视图，核查是否直接读取解码数组。
                                send({shader_view_result:result.toInt32(),resource:this.resource.toString(),
                                    descriptor:this.desc,texture:this.desc && [4,5].includes(this.desc[1]) ? texture(this.resource) : null});
                            }
                        });
                    }
                    const createTexture=method(object,5),textureKey='texture'+createTexture;
                    if (!seen.has(textureKey)) {
                        seen.add(textureKey);
                        Interceptor.attach(createTexture,{
                            onEnter(args) {
                                const desc=args[1],width=desc.readU32(),array=desc.add(12).readU32(),flags=desc.add(32).readU32();
                                if (width>=7680 && flags===520 &&
                                    ((SHADER_TEXTURE_ONLY && array===1) || (DECODER_ONLY && array>1))) {
                                    const copy=Memory.alloc(44);copy.writeByteArray(desc.readByteArray(44));
                                    copy.add(32).writeU32(array===1 ? 8 : 512);
                                    this.descriptor=copy;args[1]=copy;
                                    send({texture_flags_before:flags,after:array===1 ? 8 : 512,array});
                                }
                            }
                        });
                    }
                    const address=method(object,40),key='immediate'+address;
                    if (!seen.has(key)) {
                        seen.add(key);
                        Interceptor.attach(address,{
                            onEnter(args) { this.output=args[1]; },
                            onLeave() { context(this.output.readPointer()); }
                        });
                    }
                    const deferred=method(object,27),deferredKey='deferred'+deferred;
                    if (!seen.has(deferredKey)) {
                        seen.add(deferredKey);
                        Interceptor.attach(deferred,{
                            onEnter(args) { this.output=args[2]; },
                            onLeave(result) { if (result.toInt32()===0) context(this.output.readPointer()); }
                        });
                    }
                }
                if (!this.ctxOut.isNull()) {
                    renderingContext=this.ctxOut.readPointer();context(renderingContext);
                }
            }
        });
        Interceptor.flush();
    }
    if (module.name.toLowerCase() === 'dxgi.dll') {
        send({module:module.name,base:module.base});
        for (const name of ['CreateDXGIFactory','CreateDXGIFactory1']) {
            Interceptor.attach(module.getExportByName(name), {
                onEnter(args) { this.output=args[1]; },
                onLeave(result) { if (result.toInt32() === 0) factory(this.output.readPointer()); }
            });
        }
        Interceptor.flush();
    }
}
const observer = Process.attachModuleObserver({onAdded:instrument});
// 提前加载并明确安装导出探针，避免Windows动态加载通知时序漏掉首个设备。
for (const name of ['d3d11.dll','dxgi.dll']) instrument(Module.load(name));
// 只保留测试进程Present线程内部的长等待，不采集其它进程。
for (const moduleName of ['ntdll.dll','win32u.dll']) {
    const module=Module.load(moduleName);
    const names=moduleName==='ntdll.dll' ? ['NtWaitForSingleObject','NtWaitForMultipleObjects','NtDelayExecution'] :
        module.enumerateExports().filter(x=>/WaitForSynchronization|WaitForVerticalBlank|SubmitPresent|Present$/.test(x.name)).map(x=>x.name);
    for (const name of names) {
        const address=module.findExportByName(name);if (!address) continue;
        Interceptor.attach(address,{
            onEnter() {
                this.active=presenting.has(this.threadId);if (!this.active) return;
                this.begin=now();this.stack=Thread.backtrace(this.context,Backtracer.ACCURATE).map(location);
            },
            onLeave(result) {
                if (!this.active) return;
                const end=now();if (end-this.begin<10000) return;
                records.push({name,begin:this.begin,end,thread:this.threadId,caller:this.stack[0],
                    result:result.toInt32(),detail:{stack:this.stack}});
            }
        });
    }
}
setInterval(()=>{
    for (const adapter of adapters) {
        for (const segment of [0,1]) {
            const info=Memory.alloc(32);
            const result=new NativeFunction(method(adapter,14),'int',['pointer','uint','uint','pointer'])(adapter,0,segment,info);
            if (result===0) send({memory_qpc:now(),segment,budget:info.readU64().toNumber(),
                usage:info.add(8).readU64().toNumber()});
        }
    }
},1000);
setInterval(() => { if (records.length) { send({calls:records}); records=[]; } },500);
// 驱动／运行时可能在首次使用时切换方法入口，再次核查已取得的上下文。
setInterval(() => {
    const native=Process.findModuleByName('FFF.Native.dll');if (native) instrument(native);
    const avutil=Process.findModuleByName('avutil-61.dll');if (avutil) instrument(avutil);
    const avcodec=Process.findModuleByName('avcodec-63.dll');if (avcodec) instrument(avcodec);
    for (const object of contexts) { try { context(object); } catch (_) {} }
},200);
send({ready:true,pid:Process.id});
rpc.exports={replaycopy() {
    if (!replayCopy) throw new Error('未捕获真实复制参数');
    const values=replayCopy.values,object=values[0],definition=Memory.alloc(8),output=Memory.alloc(Process.pointerSize);
    definition.writeU32(0);definition.add(4).writeU32(0);
    if (new NativeFunction(method(renderingDevice,24),'int',['pointer','pointer','pointer'])(
        renderingDevice,definition,output)!==0) throw new Error('独立复制查询创建失败');
    const query=output.readPointer();
    const copy=new NativeFunction(replayCopy.address,'void',
        ['pointer','pointer','uint','uint','uint','uint','pointer','uint','pointer']);
    const end=new NativeFunction(method(object,28),'void',['pointer','pointer']);
    const flush=new NativeFunction(method(object,111),'void',['pointer']);
    const getData=new NativeFunction(method(object,29),'int',['pointer','pointer','pointer','uint','uint']);
    const sleep=new NativeFunction(kernel.getExportByName('Sleep'),'void',['uint']);
    const result={source:texture(values[6]),destination:texture(values[1]),samples:{}};
    for (const size of [0,64]) {
        const box=Memory.alloc(24);
        box.writeByteArray(values[8].readByteArray(24));
        if (size) {box.add(12).writeU32(size);box.add(16).writeU32(size);}
        const samples=[];
        for (let i=0;i<110;i++) {
            const begin=now();
            copy(object,values[1],values[2].toUInt32(),values[3].toUInt32(),values[4].toUInt32(),
                values[5].toUInt32(),values[6],values[7].toUInt32(),box);
            end(object,query);flush(object);
            let status=1;
            while ((status=getData(object,query,ptr(0),0,1))===1) {
                if (now()-begin>20000000) throw new Error('独立复制查询超时');
                sleep(1);
            }
            if (status!==0) throw new Error('独立复制查询失败');
            if (i>=10) samples.push((now()-begin)/10000);
        }
        result.samples[size===0 ? 'full' : '64x64']=samples;
    }
    new NativeFunction(method(query,2),'uint',['pointer'])(query);
    return result;
}};
