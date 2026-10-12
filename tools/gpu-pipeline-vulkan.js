// Vulkan 逐次实际写回：在自有诊断命令流中插入只读复制，保持原图像布局。
// 由 Python 组合在已有交换链读回工具后，复用设备、队列与过程地址解析。
const imageMeta=new Map(),views=new Map(),passes=new Map(),framebuffers=new Map();
const descriptorWrites=new Map(),commandStates=new Map(),stageCopies=[];
const shaderTypes=[];
let stageRequested=null,stageNumber=0,insideStage=false;
function commandState(cmd){const key=cmd.toString();if(!commandStates.has(key))commandStates.set(key,{sets:[],framebuffer:null,pass:null});return commandStates.get(key);}
function stageSnapshot(cmd,device,image,layout,meta){
    if(stageRequested===null||insideStage||stageNumber>=160)return;
    const im=imageMeta.get(image.toString());
    if(!im||!im.readable||!im.bytes||im.width*im.height>16777216||im.depth!==1)return;
    insideStage=true;let buffer=null,memory=null;
    try{
        const output=alloc(8),size=im.width*im.height*im.bytes;
        const b=alloc(56,12);b.add(24).writeU64(size);b.add(32).writeU32(2);
        check(func(device,'vkCreateBuffer','int',['pointer','pointer','pointer','pointer'])(device,b,ptr(0),output),'创建阶段缓冲');buffer=output.readPointer();
        const req=alloc(24);func(device,'vkGetBufferMemoryRequirements','void',['pointer','pointer','pointer'])(device,buffer,req);
        const getProps=new NativeFunction(moduleVK.getExportByName('vkGetPhysicalDeviceMemoryProperties'),'void',['pointer','pointer']);
        const props=alloc(1024);getProps(devices.get(device.toString()),props);
        let type=-1;for(let i=0;i<props.readU32();i++)if((req.add(16).readU32()&(1<<i))&&(props.add(4+i*8).readU32()&6)===6){type=i;break;}
        if(type<0)throw new Error('阶段 HOST_VISIBLE/COHERENT 不可用');
        const m=alloc(32,5);m.add(16).writeU64(req.readU64());m.add(24).writeU32(type);
        check(func(device,'vkAllocateMemory','int',['pointer','pointer','pointer','pointer'])(device,m,ptr(0),output),'阶段内存');memory=output.readPointer();
        check(func(device,'vkBindBufferMemory','int',['pointer','pointer','pointer','uint64'])(device,buffer,memory,0),'绑定阶段缓冲');
        const barrier=alloc(72,45);barrier.add(16).writeU32(0x18000);barrier.add(20).writeU32(0x800);
        barrier.add(24).writeU32(layout);barrier.add(28).writeU32(6);
        barrier.add(32).writeU32(0xffffffff);barrier.add(36).writeU32(0xffffffff);barrier.add(40).writePointer(image);
        barrier.add(48).writeU32(1);barrier.add(56).writeU32(1);barrier.add(64).writeU32(1);
        const transition=func(device,'vkCmdPipelineBarrier','void',['pointer','uint','uint','uint','uint','pointer','uint','pointer','uint','pointer']);
        transition(cmd,0x10000,0x1000,0,0,ptr(0),0,ptr(0),1,barrier);
        const region=alloc(56);region.add(16).writeU32(1);region.add(28).writeU32(1);
        region.add(44).writeU32(im.width);region.add(48).writeU32(im.height);region.add(52).writeU32(1);
        func(device,'vkCmdCopyImageToBuffer','void',['pointer','pointer','uint','pointer','uint','pointer'])(cmd,image,6,buffer,1,region);
        barrier.add(16).writeU32(0x800);barrier.add(20).writeU32(0x18000);barrier.add(24).writeU32(6);barrier.add(28).writeU32(layout);
        transition(cmd,0x1000,0x10000,0,0,ptr(0),0,ptr(0),1,barrier);
        stageCopies.push({device,buffer,memory,size,meta:{...meta,capture:stageRequested,sequence:stageNumber++,width:im.width,height:im.height,
            format:im.dxgi,vk_format:im.format,stride:im.width*im.bytes,bytes_per_pixel:im.bytes,diagnostic_transfer_src:im.extraUsage,resource:image.toString()}});
        buffer=null;memory=null;
    }catch(e){send({capture:stageRequested,error:String(e),phase:'stage'});}
    finally{
        if(buffer)func(device,'vkDestroyBuffer','void',['pointer','pointer','pointer'])(device,buffer,ptr(0));
        if(memory)func(device,'vkFreeMemory','void',['pointer','pointer','pointer'])(device,memory,ptr(0));insideStage=false;
    }
}
const commandDevices=new Map();
function descriptorSnapshots(cmd,phase,storage){
    const s=commandState(cmd),dev=commandDevices.get(cmd.toString());if(!dev)return;
    const done=new Set();
    for(const set of s.sets)for(const item of descriptorWrites.get(set)||[]){
        if((item.type===3)!==storage||done.has(item.view))continue;done.add(item.view);
        const image=views.get(item.view);if(image)stageSnapshot(cmd,dev,image,item.layout,{phase,compute:storage,slot:item.binding});
    }
}
function readDescriptors(count,pointer,key){
    for(let i=0;i<count;i++){const d=pointer.add(i*64),type=d.add(36).readU32();if(![1,2,3].includes(type))continue;
        const set=key||d.add(16).readPointer().toString(),items=descriptorWrites.get(set)||[],binding=d.add(24).readU32();
        const filtered=items.filter(v=>v.binding!==binding);
        for(let j=0;j<d.add(32).readU32();j++){const info=d.add(40).readPointer().add(j*24);filtered.push({type,binding,view:info.add(8).readPointer().toString(),layout:info.add(16).readU32()});}
        descriptorWrites.set(set,filtered);
    }
}
function flushStages(queue){
    if(!stageCopies.length)return;
    const dev=queues.get(queue.toString()).device;
    check(func(dev,'vkDeviceWaitIdle','int',['pointer'])(dev),'等待各阶段复制');
    for(const copy of stageCopies){let mapped=false;
        try{const output=alloc(8);check(func(copy.device,'vkMapMemory','int',['pointer','pointer','uint64','uint64','uint','pointer'])(copy.device,copy.memory,0,copy.size,0,output),'读回阶段');
            mapped=true;send(copy.meta,output.readPointer().readByteArray(copy.size));
        }finally{if(mapped)func(copy.device,'vkUnmapMemory','void',['pointer','pointer'])(copy.device,copy.memory);
            func(copy.device,'vkDestroyBuffer','void',['pointer','pointer','pointer'])(copy.device,copy.buffer,ptr(0));
            func(copy.device,'vkFreeMemory','void',['pointer','pointer','pointer'])(copy.device,copy.memory,ptr(0));}
    }
    stageCopies.length=0;stageRequested=null;
}
function watch(name,address){
    watchFinal(name,address);
    if(address.isNull()||hooks.has('stage:'+name+address))return;hooks.add('stage:'+name+address);
    if(name==='vkCreateShaderModule')Interceptor.attach(address,{onEnter(a){const d=a[1],n=d.add(24).readU64().toNumber()/4,code=d.add(32).readPointer();let floats=[],relaxedIds=[],instructions=[],types=new Map(),results=new Map(),executionModels=[];
        for(let i=5;i<n;){const word=code.add(i*4).readU32(),length=word>>>16,op=word&65535;if(!length)break;
            const args=[];for(let j=1;j<length;j++)args.push(code.add((i+j)*4).readU32());instructions.push({op,args});
            if(op===22)floats.push(args[1]);
            if(op>=19&&op<=39)types.set(args[0],{op,args:args.slice(1)});
            if(op===15)executionModels.push(args[0]);
            if(op===71&&args[1]===0)relaxedIds.push(args[0]);
            i+=length;
        }
        for(const inst of instructions)if(inst.op>=41&&types.has(inst.args[0]))results.set(inst.args[1],inst.args[0]);
        function classify(id){const ty=types.get(id);if(!ty)return 'unknown';if(ty.op===22)return 'float';if(ty.op===21)return 'integer';if(ty.op===20)return 'boolean';if(ty.op===23||ty.op===24)return classify(ty.args[0]);if(ty.op===32)return classify(ty.args[1]);return 'other';}
        const relaxed=relaxedIds.map(id=>({id,type:classify(results.get(id)||id),result_type:results.get(id)||null}));
        shaderTypes.push({float_widths:floats,execution_models:executionModels,relaxed_precision_decorations:relaxed.length,
            relaxed_float_decorations:relaxed.filter(v=>v.type==='float').length,relaxed_unknown_decorations:relaxed.filter(v=>v.type==='unknown'||v.type==='other').length,relaxed_targets:relaxed});}});
    if(name==='vkCreateImage')Interceptor.attach(address,{onEnter(a){
        this.device=a[0];this.output=a[3];const d=a[1],format=d.add(24).readU32();
        const mapping={9:[61,1],16:[49,2],64:[24,4],70:[56,2],76:[54,2],77:[35,4],83:[34,4],91:[11,8],97:[10,8],100:[41,4],109:[2,16]};
        const fmt=mapping[format]||[null,null],usage=d.add(56).readU32();
        let supported=!!(usage&1);
        if(!supported&&fmt[1]&&d.add(36).readU32()===1){
            const props=alloc(12);new NativeFunction(moduleVK.getExportByName('vkGetPhysicalDeviceFormatProperties'),'void',['pointer','uint','pointer'])(devices.get(a[0].toString()),format,props);
            if(props.add(4).readU32()&0x4000){d.add(56).writeU32(usage|1);supported=true;}
        }
        this.meta={format,dxgi:fmt[0],bytes:fmt[1],width:d.add(28).readU32(),height:d.add(32).readU32(),depth:d.add(36).readU32(),readable:supported,extraUsage:!(usage&1)};
    },onLeave(r){if(r.toInt32()===0)imageMeta.set(this.output.readPointer().toString(),this.meta);}});
    if(name==='vkCreateImageView')Interceptor.attach(address,{onEnter(a){this.image=a[1].add(24).readPointer();this.output=a[3];},onLeave(r){if(r.toInt32()===0)views.set(this.output.readPointer().toString(),this.image);}});
    if(name==='vkCreateRenderPass')Interceptor.attach(address,{onEnter(a){this.output=a[3];const d=a[1];this.layout=d.add(20).readU32()?d.add(24).readPointer().add(32).readU32():null;},onLeave(r){if(r.toInt32()===0)passes.set(this.output.readPointer().toString(),this.layout);}});
    if(name==='vkCreateFramebuffer')Interceptor.attach(address,{onEnter(a){this.output=a[3];const d=a[1];this.images=[];
        for(let i=0;i<d.add(32).readU32();i++)this.images.push(views.get(d.add(40).readPointer().add(i*8).readPointer().toString()));
    },onLeave(r){if(r.toInt32()===0)framebuffers.set(this.output.readPointer().toString(),this.images);}});
    if(name==='vkAllocateCommandBuffers')Interceptor.attach(address,{onEnter(a){this.device=a[0];this.count=a[1].add(28).readU32();this.output=a[2];},onLeave(r){if(r.toInt32()===0)for(let i=0;i<this.count;i++)commandDevices.set(this.output.add(i*8).readPointer().toString(),this.device);}});
    if(name==='vkUpdateDescriptorSets')Interceptor.attach(address,{onEnter(a){
        for(let i=0;i<a[1].toUInt32();i++){const d=a[2].add(i*64),type=d.add(36).readU32();if(![1,2,3].includes(type))continue;
            const set=d.add(16).readPointer().toString(),items=descriptorWrites.get(set)||[],binding=d.add(24).readU32();
            const filtered=items.filter(v=>v.binding!==binding);
            for(let j=0;j<d.add(32).readU32();j++){const info=d.add(40).readPointer().add(j*24);filtered.push({type,binding,view:info.add(8).readPointer().toString(),layout:info.add(16).readU32()});}
            descriptorWrites.set(set,filtered);
        }
    }});
    if(name==='vkCmdBindDescriptorSets')Interceptor.attach(address,{onEnter(a){const s=commandState(a[0]);s.sets=[];for(let i=0;i<a[4].toUInt32();i++)s.sets.push(a[5].add(i*8).readPointer().toString());}});
    if(name==='vkCmdPushDescriptorSetKHR'||name==='vkCmdPushDescriptorSet')Interceptor.attach(address,{onEnter(a){const key='push:'+a[0];descriptorWrites.set(key,[]);readDescriptors(a[4].toUInt32(),a[5],key);commandState(a[0]).sets=[key];}});
    if(name==='vkGetSwapchainImagesKHR')Interceptor.attach(address,{onEnter(a){this.chain=a[1].toString();},onLeave(){const sw=chains.get(this.chain);if(sw&&[97,64].includes(sw.format))for(const image of sw.images)imageMeta.set(image.toString(),{format:sw.format,dxgi:sw.format===97?10:24,bytes:sw.format===97?8:4,width:sw.width,height:sw.height,depth:1,readable:sw.readback_supported,extraUsage:true});}});
    if(name==='vkCmdBeginRenderPass')Interceptor.attach(address,{onEnter(a){if(insideStage)return;
        const s=commandState(a[0]);s.framebuffer=a[1].add(24).readPointer().toString();s.pass=a[1].add(16).readPointer().toString();
    }});
    if(name==='vkCmdEndRenderPass')Interceptor.attach(address,{onEnter(a){this.cmd=a[0];},onLeave(){if(insideStage)return;
        // 描述符通常在 BeginRenderPass 之后绑定，结束后读取只读采样源。
        descriptorSnapshots(this.cmd,'input',false);
        const s=commandState(this.cmd),dev=commandDevices.get(this.cmd.toString()),layout=passes.get(s.pass);
        for(const image of framebuffers.get(s.framebuffer)||[])if(image&&layout!==undefined)stageSnapshot(this.cmd,dev,image,layout,{phase:'output',compute:false,slot:0});
    }});
    if(name==='vkCmdDispatch')Interceptor.attach(address,{onEnter(a){this.cmd=a[0];if(!insideStage)descriptorSnapshots(a[0],'input',false);},onLeave(){if(!insideStage)descriptorSnapshots(this.cmd,'output',true);}});
}
rpc.exports={arm(id){requested=id;stageRequested=id;stageNumber=0;},status(){return {chains:chains.size,images:[...imageMeta.values()],views:views.size,descriptors:[...descriptorWrites.values()],commands:commandDevices.size,stages:stageNumber,copies:stageCopies.length,shader_types:shaderTypes};}};
