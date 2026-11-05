const CONFIG={"observe":true,"output":"/private/tmp/yt-maint-calendar-native/new-year-observed-a/host-time.json"};
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
 const stack=ram.add(ss*16+sp);const runtime=stack.add(2).readU16(),app=stack.add(16).readU16(),ret=stack.add(14).readU16();
 const qualified=stack.readU16()===0xc137;
 const runtime_signature=qualified?hex(ram.add(runtime*16+0xc12f),8):null;
 const application_call=qualified?hex(ram.add(app*16+ret-5),5):null;
 return {ax:registers.readU16(),cx:registers.add(4).readU16(),dx:registers.add(8).readU16(),
  ds,ss,cs,sp,ip:registers.add(32).readU32(),pic:pic.readU32(),cycles:cycles.readS32(),
  runtime_signature,application_call,ds_phys:segments.add(28).readU32(),ss_phys:segments.add(24).readU32(),stack:hex(stack,40),port_raw:hex(ram.add(ds*16+0x7ad6),4)};
}
if(CONFIG.observe)Interceptor.attach(address(0xdb990),{
 onEnter(){
  this.time=registers.add(1).readU8()===0x2c;
  if(this.time){try{this.before=snapshot();}catch(e){errors.push(String(e));this.time=false;}}
 },
 onLeave(){
  if(!this.time)return;
  try{if(events.length<8192)events.push({ordinal:events.length+1,before:this.before,after:snapshot()});else dropped++;}
  catch(e){errors.push(String(e));}
 }
});
function flush(code){
 if(flushed)return;flushed=true;
 const text=JSON.stringify({recipe:'host-dos-time-observer-v1',observe:CONFIG.observe,module:identity,exit_code:code,events,errors,dropped})+'\n';
 const bytes=Memory.allocUtf8String(text);const fd=creat(Memory.allocUtf8String(CONFIG.output),0o600);
 if(fd<0)throw new Error('trace creat failed');
 const count=write(fd,bytes,text.length);close(fd);
 send({kind:'flushed',exit_code:code,bytes:Number(count),expected_bytes:text.length,events:events.length,errors:errors.length,dropped});
}
for(const name of ['exit','_exit'])try{Interceptor.attach(libc(name),{onEnter(args){flush(args[0].toInt32());}});}catch(e){errors.push(String(e));}
send({kind:'ready',module:identity,observe:CONFIG.observe});
