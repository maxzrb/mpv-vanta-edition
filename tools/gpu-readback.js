// 维护诊断：只读取自有测试播放器的实际交换链，不修改视频像素和渲染选项。
const seen = new Set();
let requested = null;
const textures = [];
let chains = 0, factories = 0, presents = 0;
const colorSpaces = new Map();
function method(object, index) { return object.readPointer().add(index * Process.pointerSize).readPointer(); }
function call(object, index, result, args) { return new NativeFunction(method(object, index), result, ['pointer', ...args]); }
function release(object) { if (object && !object.isNull()) call(object, 2, 'uint', [])(object); }
function capture(chain, id) {
    let source = null, device = null, context = null, staging = null, mapped = false;
    try {
        const iid = Memory.alloc(16);
        iid.writeByteArray([0xf2,0xaa,0x15,0x6f,0x08,0xd2,0x89,0x4e,0x9a,0xb4,0x48,0x95,0x35,0xd3,0x4f,0x9c]);
        const output = Memory.alloc(Process.pointerSize);
        if (call(chain, 9, 'int', ['uint','pointer','pointer'])(chain, 0, iid, output) !== 0)
            throw new Error('交换链 GetBuffer 失败');
        source = output.readPointer();
        const desc = Memory.alloc(44);
        call(source, 10, 'void', ['pointer'])(source, desc);
        const width = desc.readU32(), height = desc.add(4).readU32(), format = desc.add(16).readU32();
        if (width === 0 || height === 0 || width * height > 4194304 || desc.add(20).readU32() !== 1)
            throw new Error('诊断图像尺寸或采样格式不支持');
        if (![10,24,28,87].includes(format)) throw new Error('未知交换链格式 ' + format);
        call(source, 3, 'void', ['pointer'])(source, output); device = output.readPointer();
        call(device, 40, 'void', ['pointer'])(device, output); context = output.readPointer();
        desc.add(28).writeU32(3); desc.add(32).writeU32(0);
        desc.add(36).writeU32(0x20000); desc.add(40).writeU32(0);
        if (call(device, 5, 'int', ['pointer','pointer','pointer'])(device, desc, ptr(0), output) !== 0)
            throw new Error('只读 staging 创建失败');
        staging = output.readPointer();
        call(context, 47, 'void', ['pointer','pointer'])(context, staging, source);
        const map = Memory.alloc(16);
        if (call(context, 14, 'int', ['pointer','uint','uint','uint','pointer'])(context, staging, 0, 1, 0, map) !== 0)
            throw new Error('只读 GPU Map 失败');
        mapped = true;
        const stride = map.add(8).readU32();
        if (stride * height > 67108864) throw new Error('诊断数据大小超限');
        const bytes = map.readPointer().readByteArray(stride * height);
        send({capture: id, width, height, format, stride, color_space:colorSpaces.get(chain.toString()),
            textures: textures.slice(-120), scope: '实际交换链呈现前原始存储值；非DWM或面板输出'}, bytes);
    } catch (e) { send({capture: id, error: String(e)}); }
    finally {
        if (mapped) call(context, 15, 'void', ['pointer','uint'])(context, staging, 0);
        release(staging); release(context); release(device); release(source);
    }
}
function watchChain(object) {
    chains++;
    colorSpaces.set(object.toString(),0);
    const guid=Memory.alloc(16), output=Memory.alloc(Process.pointerSize);
    guid.writeByteArray([0xdb,0x9b,0xd9,0x94,0xf8,0xf1,0xb0,0x4a,0xb2,0x36,0x7d,0xa0,0x17,0x0e,0xda,0xb1]);
    if (call(object,0,'int',['pointer','pointer'])(object,guid,output)===0) {
        const chain3=output.readPointer(), address=method(chain3,38), key='color:'+address;
        if (!seen.has(key)) {
            seen.add(key);
            Interceptor.attach(address,{onEnter(args) {this.object=args[0].toString();this.color=args[1].toUInt32();},
                onLeave(result) {if(result.toInt32()===0)colorSpaces.set(this.object,this.color);}});
        }
        release(chain3);
    }
    const address = method(object, 8), key = 'present:' + address;
    if (seen.has(key)) return; seen.add(key);
    Interceptor.attach(address, {onEnter(args) {
        presents++;
        // 在呈现线程读取，避免与视频绘制并行访问同一 immediate context。
        if (requested !== null && !(args[2].toUInt32() & 1)) { const id = requested; requested = null; capture(args[0], id); }
    }});
}
function watchDevice(device) {
    const address = method(device, 5), key = 'texture:' + address;
    if (seen.has(key)) return; seen.add(key);
    Interceptor.attach(address, {onEnter(args) {
        const d = args[1];
        this.description = {width:d.readU32(), height:d.add(4).readU32(), format:d.add(16).readU32(), bind:d.add(32).readU32()};
    }, onLeave(result) {
        const d = this.description;
        if (result.toInt32() === 0 && d.width >= 32 && d.height >= 32 && d.bind !== 0) {
            textures.push(d); if (textures.length > 240) textures.shift();
        }
    }});
}
function watchFactory(object) {
    factories++;
    const guid = Memory.alloc(16), output = Memory.alloc(Process.pointerSize);
    guid.writeByteArray([0x1c,0x3a,0xc8,0x50,0x72,0xe0,0x48,0x4c,0x87,0xb0,0x36,0x30,0xfa,0x36,0xa6,0xd0]);
    const result = call(object, 0, 'int', ['pointer','pointer'])(object, guid, output);
    const modern = result === 0 ? output.readPointer() : null;
    for (const [index, outputIndex] of (modern ? [[10,3],[15,6],[24,4]] : [[10,3]])) {
        const address = method(index === 10 ? object : modern, index), key = 'factory:' + address;
        if (seen.has(key)) continue; seen.add(key);
        Interceptor.attach(address, {onEnter(args) { this.output = args[outputIndex]; },
            onLeave(result) { if (result.toInt32() === 0 && !this.output.isNull()) watchChain(this.output.readPointer()); }});
    }
    release(modern);
}
Process.attachModuleObserver({onAdded(module) {
    if (module.name.toLowerCase() === 'dxgi.dll') {
        for (const name of ['CreateDXGIFactory','CreateDXGIFactory1','CreateDXGIFactory2']) {
            const address = module.findExportByName(name); if (!address) continue;
            Interceptor.attach(address, {onEnter(args) { this.output = args[name === 'CreateDXGIFactory2' ? 2 : 1]; },
                onLeave(result) { if (result.toInt32() === 0) watchFactory(this.output.readPointer()); }});
        }
    }
    if (module.name.toLowerCase() === 'd3d11.dll') {
        const address = module.findExportByName('D3D11CreateDevice');
        if (address) Interceptor.attach(address, {onEnter(args) { this.output=args[7]; },
            onLeave(result) { if (result.toInt32()===0 && !this.output.isNull()) watchDevice(this.output.readPointer()); }});
    }
}});
rpc.exports = {arm(id) { requested = id; }, status() { return {chains,factories,presents,textures:textures.length}; }};
