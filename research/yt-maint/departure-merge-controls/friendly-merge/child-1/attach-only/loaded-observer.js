const CONFIG={"observe":false,"output":"/private/tmp/yt-maint-departure-first-mounts/friendly-merge/child-1/attach-only/host-time.json"};
'use strict';
const module = Process.mainModule;
const address = offset => module.base.add(offset);
const registers = address(0x1396d60), segments = address(0x1396e78);
const memoryGlobal = address(0x23abb90), pic = address(0x23abb98), cycles = address(0x1396ea8);
const libc = name => Module.getGlobalExportByName(name);
const creat = new NativeFunction(libc('creat'),'int',['pointer','int']);
const close = new NativeFunction(libc('close'),'int',['int']);
const write = new NativeFunction(libc('write'),'long',['int','pointer','ulong']);
const hex=(p,n)=>Array.from(new Uint8Array(p.readByteArray(n))).map(x=>x.toString(16).padStart(2,'0')).join('');
const events=[],errors=[];let dropped=0,flushed=false;
const prologue=hex(address(0xdb990),32);
function uuid(){
 let at=module.base.add(32);const count=module.base.add(16).readU32();
 for(let i=0;i<count;i++){const cmd=at.readU32(),size=at.add(4).readU32();
  if(cmd===0x1b){const h=hex(at.add(8),16);return [h.slice(0,8),h.slice(8,12),h.slice(12,16),h.slice(16,20),h.slice(20)].join('-').toUpperCase();}
  at=at.add(size);
 }throw new Error('missing MachO UUID');
}
const identity={name:module.name,path:module.path,base:module.base.toString(),size:module.size,arch:Process.arch,platform:Process.platform,uuid:uuid(),prologue};
if(identity.arch!=='arm64'||identity.platform!=='darwin'||identity.uuid!=='31CDF62F-E9EE-39ED-A05A-10E4072BD15E'||
   prologue!=='fc6fbaa9fa6701a9f85f02a9f65703a9f44f04a9fd7b05a9fd430191ffc314d1')throw new Error('unsupported host binary');
function snapshot(){
 const ram=memoryGlobal.readPointer();
 const ss=segments.add(4).readU16(),ds=segments.add(6).readU16(),cs=segments.add(2).readU16();
 const sp=registers.add(16).readU16();
 const stack=ram.add(ss*16+sp),interrupt_return=stack.readU16(),runtime=stack.add(2).readU16();
 const frames={0xc137:[0xc12f,7],0xc07f:[0xc06b,9],0xc0f7:[0xc0e3,9]};
 const frame=frames[interrupt_return];
 const runtime_signature=frame?hex(ram.add(runtime*16+frame[0]),8):null;
 const app=frame?stack.add((frame[1]+1)*2).readU16():0,ret=frame?stack.add(frame[1]*2).readU16():0;
 const application_call=frame?hex(ram.add(app*16+((ret-5)&65535)),5):null;
 const caller_code=hex(ram.add(runtime*16+((interrupt_return-16)&65535)),32);
 const nested_index=frame&&interrupt_return===0xc07f&&ret===0x79ed?20:
                    frame&&interrupt_return===0xc137&&(ret===0x78fd||ret===0x7943)?18:null;
 const nested_return=nested_index===null?0:stack.add(nested_index*2).readU16();
 const nested_cs=nested_index===null?0:stack.add((nested_index+1)*2).readU16();
 const nested_application_call=nested_index===null?null:hex(ram.add(nested_cs*16+((nested_return-5)&65535)),5);
 const bp=registers.add(20).readU16(),bp_frame=hex(ram.add(ss*16+bp),64);
 return {ax:registers.readU16(),cx:registers.add(4).readU16(),dx:registers.add(8).readU16(),
  ds,ss,cs,sp,ip:registers.add(32).readU32(),pic:pic.readU32(),cycles:cycles.readS32(),cycle_left:address(0x464ac0).readS32(),cycle_max:address(0x464ac4).readS32(),auto_adjust:address(0x1396ec0).readU8(),
  runtime_signature,application_call,caller_code,nested_application_call,bp,bp_frame,ds_phys:segments.add(28).readU32(),ss_phys:segments.add(24).readU32(),stack:hex(stack,64),port_raw:hex(ram.add(ds*16+0x7ad6),4),rng_raw:hex(ram.add(ds*16+0x234),4)};
}
if(CONFIG.observe)Interceptor.attach(address(0xdb990),{
 onEnter(){
  this.function=registers.add(1).readU8();
  this.time=this.function===0x2c||this.function===0x2a;
  if(this.time){try{this.before=snapshot();}catch(e){errors.push(String(e));this.time=false;}}
 },
 onLeave(){
  if(!this.time)return;
  try{if(events.length<16384)events.push({ordinal:events.length+1,function:this.function,before:this.before,after:snapshot()});else dropped++;}
  catch(e){errors.push(String(e));}
 }
});
function flush(code){
 if(flushed)return;flushed=true;
 const text=JSON.stringify({recipe:'host-dos-placement-cache-observer-v1',observe:CONFIG.observe,module:identity,exit_code:code,events,errors,dropped})+'\n';
 const bytes=Memory.allocUtf8String(text);const fd=creat(Memory.allocUtf8String(CONFIG.output),0o600);
 if(fd<0)throw new Error('trace creat failed');
 const count=write(fd,bytes,text.length);close(fd);
 send({kind:'flushed',exit_code:code,bytes:Number(count),expected_bytes:text.length,events:events.length,errors:errors.length,dropped});
}
for(const name of ['exit','_exit'])try{Interceptor.attach(libc(name),{onEnter(args){flush(args[0].toInt32());}});}catch(e){errors.push(String(e));}
send({kind:'ready',module:identity,observe:CONFIG.observe});
