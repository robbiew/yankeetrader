'use strict';
const module = Process.mainModule;
const address = offset => module.base.add(offset);
const registers = address(0x1396d60), segments = address(0x1396e78);
const memoryGlobal = address(0x23abb90), pic = address(0x23abb98), cycles = address(0x1396ea8);
const libc = name => Module.getGlobalExportByName(name);
const setenv = new NativeFunction(libc('setenv'), 'int', ['pointer','pointer','int']);
for (const [k,v] of [['SDL_VIDEODRIVER','dummy'],['SDL_AUDIODRIVER','dummy']])
  if (setenv(Memory.allocUtf8String(k),Memory.allocUtf8String(v),1)!==0) throw new Error('setenv failed');
const open = new NativeFunction(libc('open'),'int',['pointer','int','int']);
const dup2 = new NativeFunction(libc('dup2'),'int',['int','int']);
const close = new NativeFunction(libc('close'),'int',['int']);
const write = new NativeFunction(libc('write'),'long',['int','pointer','ulong']);
const logfd=open(Memory.allocUtf8String('/private/tmp/yt-clock-neutral-pilot/dosbox.log'),0x601,0o600);
if(logfd<0||dup2(logfd,1)!==1||dup2(logfd,2)!==2)throw new Error('log redirect failed');
close(logfd);
const hex=(p,n)=>Array.from(new Uint8Array(p.readByteArray(n))).map(x=>x.toString(16).padStart(2,'0')).join('');
const events=[],errors=[];let dropped=0,flushed=false;
function snapshot(){
 const ram=memoryGlobal.readPointer();
 const ss=segments.add(4).readU16(),ds=segments.add(6).readU16(),cs=segments.add(2).readU16();
 const sp=registers.add(16).readU16();
 return {ax:registers.readU16(),cx:registers.add(4).readU16(),dx:registers.add(8).readU16(),
  ds,ss,cs,sp,ip:registers.add(32).readU32(),pic:pic.readU32(),cycles:cycles.readS32(),
  stack:hex(ram.add(ss*16+sp),40),port_raw:hex(ram.add(ds*16+0x7ad6),4)};
}
Interceptor.attach(address(0xdb990),{
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
function flush(){
 if(flushed)return;flushed=true;
 const text=JSON.stringify({recipe:'host-dos-time-observer-pilot-v1',module:{name:module.name,path:module.path,base:module.base.toString(),size:module.size},events,errors,dropped})+'\n';
 const p=Memory.allocUtf8String(text);const fd=open(Memory.allocUtf8String('/private/tmp/yt-clock-neutral-pilot/host-time.json'),0x601,0o600);
 if(fd>=0){write(fd,p,text.length);close(fd);}send({kind:'flushed',events:events.length,errors:errors.length,dropped});
}
for(const name of ['exit','_exit'])try{Interceptor.attach(libc(name),{onEnter:flush});}catch(e){errors.push(String(e));}
send({kind:'ready',module:module.name,path:module.path,hook:address(0xdb990).toString()});
