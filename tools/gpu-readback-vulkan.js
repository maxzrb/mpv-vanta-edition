// 维护诊断：仅对自有暂停测试进程增加可读回用途，不修改色彩或视频数据。
const hooks=new Set(), devices=new Map(), queues=new Map(), chains=new Map(), surfaces=new Map();
let moduleVK=null, requested=null, captures=0;
function alloc(size,type=0) {const p=Memory.alloc(size);p.writeByteArray(new Uint8Array(size));if(type)p.writeU32(type);return p;}
function check(result,label) {if(result!==0)throw new Error(label+': '+result);}
function func(device,name,result,args) {
    const get=new NativeFunction(moduleVK.getExportByName('vkGetDeviceProcAddr'),'pointer',['pointer','pointer']);
    const address=get(device,Memory.allocUtf8String(name));
    if(address.isNull())throw new Error('缺少 '+name);
    return new NativeFunction(address,result,args);
}
function capture(queue,info,id) {
    let dev=null,buffer=null,memory=null,pool=null,mapped=false;
    try {
        const q=queues.get(queue.toString());if(!q)throw new Error('未知队列');dev=q.device;
        if(info.add(32).readU32()!==1)throw new Error('交换链数量不支持');
        const chain=info.add(40).readPointer().readPointer(),index=info.add(48).readPointer().readU32();
        const sw=chains.get(chain.toString());if(!sw)throw new Error('未知交换链');
        if(!sw.readback_supported)throw new Error('表面不支持合法的 TRANSFER_SRC 读回');
        // VO 重建后可复用已解析的函数表；读回时直接查询，避免漏记图像列表。
        const count=alloc(4),getImages=func(dev,'vkGetSwapchainImagesKHR','int',['pointer','pointer','pointer','pointer']);
        check(getImages(dev,chain,count,ptr(0)),'查询交换链图像数');
        const images=alloc(count.readU32()*8);check(getImages(dev,chain,count,images),'查询交换链图像');
        sw.images=[];for(let i=0;i<count.readU32();i++)sw.images.push(images.add(i*8).readPointer());
        if(!sw.images[index])throw new Error('交换链图像索引越界');
        if(![97,64].includes(sw.format)||sw.width*sw.height>4194304)throw new Error('仅允许有限尺寸 FP16／RGB10');
        const pixelBytes=sw.format===97?8:4;
        const size=sw.width*sw.height*pixelBytes, image=sw.images[index];
        check(func(dev,'vkDeviceWaitIdle','int',['pointer'])(dev),'等待 GPU');
        const output=alloc(8);
        const b=alloc(56,12);b.add(24).writeU64(size);b.add(32).writeU32(2);
        check(func(dev,'vkCreateBuffer','int',['pointer','pointer','pointer','pointer'])(dev,b,ptr(0),output),'创建暂存缓冲');buffer=output.readPointer();
        const req=alloc(24);func(dev,'vkGetBufferMemoryRequirements','void',['pointer','pointer','pointer'])(dev,buffer,req);
        const getProps=new NativeFunction(moduleVK.getExportByName('vkGetPhysicalDeviceMemoryProperties'),'void',['pointer','pointer']);
        const props=alloc(1024);getProps(devices.get(dev.toString()),props);
        let type=-1;const bits=req.add(16).readU32();
        for(let i=0;i<props.readU32();i++)if((bits&(1<<i))&&(props.add(4+8*i).readU32()&6)===6){type=i;break;}
        if(type<0)throw new Error('缺少 HOST_VISIBLE/COHERENT 内存');
        const m=alloc(32,5);m.add(16).writeU64(req.readU64());m.add(24).writeU32(type);
        check(func(dev,'vkAllocateMemory','int',['pointer','pointer','pointer','pointer'])(dev,m,ptr(0),output),'分配读回内存');memory=output.readPointer();
        check(func(dev,'vkBindBufferMemory','int',['pointer','pointer','pointer','uint64'])(dev,buffer,memory,0),'绑定缓冲');
        const cp=alloc(24,39);cp.add(20).writeU32(q.family);
        check(func(dev,'vkCreateCommandPool','int',['pointer','pointer','pointer','pointer'])(dev,cp,ptr(0),output),'创建命令池');pool=output.readPointer();
        const ca=alloc(32,40);ca.add(16).writePointer(pool);ca.add(28).writeU32(1);
        check(func(dev,'vkAllocateCommandBuffers','int',['pointer','pointer','pointer'])(dev,ca,output),'分配命令');const cmd=output.readPointer();
        const begin=alloc(32,42);begin.add(16).writeU32(1);
        check(func(dev,'vkBeginCommandBuffer','int',['pointer','pointer'])(cmd,begin),'开始复制');
        const barrier=alloc(72,45);barrier.add(16).writeU32(0x8000);barrier.add(20).writeU32(0x800);
        barrier.add(24).writeU32(1000001002);barrier.add(28).writeU32(6);
        barrier.add(32).writeU32(0xffffffff);barrier.add(36).writeU32(0xffffffff);barrier.add(40).writePointer(image);
        barrier.add(48).writeU32(1);barrier.add(56).writeU32(1);barrier.add(64).writeU32(1);
        const transition=func(dev,'vkCmdPipelineBarrier','void',['pointer','uint','uint','uint','uint','pointer','uint','pointer','uint','pointer']);
        transition(cmd,0x10000,0x1000,0,0,ptr(0),0,ptr(0),1,barrier);
        const region=alloc(56);region.add(16).writeU32(1);region.add(28).writeU32(1);region.add(44).writeU32(sw.width);region.add(48).writeU32(sw.height);region.add(52).writeU32(1);
        func(dev,'vkCmdCopyImageToBuffer','void',['pointer','pointer','uint','pointer','uint','pointer'])(cmd,image,6,buffer,1,region);
        barrier.add(16).writeU32(0x800);barrier.add(20).writeU32(0x8000);barrier.add(24).writeU32(6);barrier.add(28).writeU32(1000001002);
        transition(cmd,0x1000,0x10000,0,0,ptr(0),0,ptr(0),1,barrier);
        check(func(dev,'vkEndCommandBuffer','int',['pointer'])(cmd),'结束复制');
        const submit=alloc(72,4),cmds=alloc(8);cmds.writePointer(cmd);submit.add(40).writeU32(1);submit.add(48).writePointer(cmds);
        check(func(dev,'vkQueueSubmit','int',['pointer','uint','pointer','pointer'])(queue,1,submit,ptr(0)),'提交复制');
        check(func(dev,'vkDeviceWaitIdle','int',['pointer'])(dev),'等待复制');
        check(func(dev,'vkMapMemory','int',['pointer','pointer','uint64','uint64','uint','pointer'])(dev,memory,0,size,0,output),'映射读回');mapped=true;
        const bytes=output.readPointer().readByteArray(size);
        send({capture:id,format:sw.format===97?10:24,vk_format:sw.format,color_space:sw.color,width:sw.width,height:sw.height,stride:sw.width*pixelBytes,
              diagnostic_transfer_src:true,scope:'实际 Vulkan 交换链呈现前原始像素'},bytes);captures++;
    } catch(e) {send({capture:id,error:String(e)});}
    finally {
        if(dev){if(mapped)func(dev,'vkUnmapMemory','void',['pointer','pointer'])(dev,memory);
            if(pool)func(dev,'vkDestroyCommandPool','void',['pointer','pointer','pointer'])(dev,pool,ptr(0));
            if(buffer)func(dev,'vkDestroyBuffer','void',['pointer','pointer','pointer'])(dev,buffer,ptr(0));
            if(memory)func(dev,'vkFreeMemory','void',['pointer','pointer','pointer'])(dev,memory,ptr(0));}
    }
}
function watch(name,address) {
    if(address.isNull()||hooks.has(name+address))return;hooks.add(name+address);
    if(name==='vkCreateDevice')Interceptor.attach(address,{onEnter(a){this.phys=a[0];this.output=a[3];},onLeave(r){if(r.toInt32()===0)devices.set(this.output.readPointer().toString(),this.phys);}});
    if(name==='vkGetDeviceQueue')Interceptor.attach(address,{onEnter(a){this.dev=a[0];this.family=a[1].toUInt32();this.output=a[3];},onLeave(){queues.set(this.output.readPointer().toString(),{device:this.dev,family:this.family});}});
    if(name==='vkGetDeviceQueue2')Interceptor.attach(address,{onEnter(a){this.dev=a[0];this.family=a[1].add(20).readU32();this.output=a[2];},onLeave(){queues.set(this.output.readPointer().toString(),{device:this.dev,family:this.family});}});
    if(name==='vkGetPhysicalDeviceSurfaceCapabilitiesKHR')Interceptor.attach(address,{onEnter(a){this.surface=a[1].toString();this.output=a[2];},onLeave(r){if(r.toInt32()===0)surfaces.set(this.surface,this.output.add(48).readU32());}});
    if(name==='vkGetPhysicalDeviceSurfaceCapabilities2KHR')Interceptor.attach(address,{onEnter(a){this.surface=a[1].add(16).readPointer().toString();this.output=a[2];},onLeave(r){if(r.toInt32()===0)surfaces.set(this.surface,this.output.add(64).readU32());}});
    if(name==='vkCreateSwapchainKHR')Interceptor.attach(address,{onEnter(a){const d=a[1];
        this.output=a[3];this.meta={format:d.add(36).readU32(),color:d.add(40).readU32(),width:d.add(44).readU32(),height:d.add(48).readU32(),images:[],readback_supported:!!(surfaces.get(d.add(24).readPointer().toString())&1)};
        // libplacebo 默认交换链不申请 TRANSFER_SRC；诊断实例单独申请合法读回用途。
        if(this.meta.readback_supported)d.add(56).writeU32(d.add(56).readU32()|1);
    },onLeave(r){if(r.toInt32()===0)chains.set(this.output.readPointer().toString(),this.meta);}});
    if(name==='vkGetSwapchainImagesKHR')Interceptor.attach(address,{onEnter(a){this.chain=a[1].toString();this.count=a[2];this.images=a[3];},onLeave(r){
        const sw=chains.get(this.chain);if(r.toInt32()===0&&sw&&!this.images.isNull()){sw.images=[];for(let i=0;i<this.count.readU32();i++)sw.images.push(this.images.add(i*8).readPointer());}
    }});
    if(name==='vkQueuePresentKHR')Interceptor.attach(address,{onEnter(a){if(requested!==null){const id=requested;requested=null;capture(a[0],a[1],id);}}});
}
Process.attachModuleObserver({onAdded(module){if(module.name.toLowerCase()!=='vulkan-1.dll')return;moduleVK=module;
    for(const getName of ['vkGetInstanceProcAddr','vkGetDeviceProcAddr'])Interceptor.attach(module.getExportByName(getName),{
        onEnter(a){this.name=a[1].readUtf8String();},onLeave(result){watch(this.name,result);}
    });
}});
rpc.exports={arm(id){requested=id;},status(){return {chains:chains.size,devices:devices.size,queues:queues.size,captures};}};
