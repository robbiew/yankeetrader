import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
const [modulePath,directory,observerPath,mode]=process.argv.slice(2);
if(!['observed','attach-only'].includes(mode))throw new Error('mode must be observed or attach-only');
const packagePath=path.resolve(path.dirname(modulePath),'../../package.json');
const pkg=JSON.parse(fs.readFileSync(packagePath,'utf8'));
if(pkg.name!=='frida'||pkg.version!=='17.23.2')throw new Error('Frida17.23.2 required for this capture recipe');
const fridaIdentity={version:pkg.version,module:path.resolve(modulePath),module_sha256:crypto.createHash('sha256').update(fs.readFileSync(modulePath)).digest('hex'),package_sha256:crypto.createHash('sha256').update(fs.readFileSync(packagePath)).digest('hex')};
const frida=await import(pathToFileURL(modulePath).href);
const device=await frida.getLocalDevice();
const argv=JSON.parse(fs.readFileSync(path.join(directory,'launch.json'),'utf8'));
const messages=[];const logs=[];let pid=null,forced=false,reason=null,ready=false;
device.output.connect((id,fd,data)=>{if(id===pid&&data)logs.push({fd,data:Buffer.from(data)});});
const outcome={mode,frida:fridaIdentity,node_version:process.version,started:new Date().toISOString()};
try {
 pid=await device.spawn(argv[0],{argv,env:{SDL_VIDEODRIVER:'dummy',SDL_AUDIODRIVER:'dummy'},stdio:'pipe'});
 const session=await device.attach(pid);
 const detached=new Promise(resolve=>session.detached.connect(r=>{reason=r;resolve();}));
 const config={observe:mode==='observed',output:path.join(directory,'host-time.json')};
 const source='const CONFIG='+JSON.stringify(config)+';\n'+fs.readFileSync(observerPath,'utf8');
 fs.writeFileSync(path.join(directory,'loaded-observer.js'),source);
 const script=await session.createScript(source);
 const readyPromise=new Promise((resolve,reject)=>script.message.connect(message=>{
  messages.push(message);
  if(message.type==='error')reject(new Error(message.description));
  if(message.type==='send'&&message.payload.kind==='ready'){ready=true;resolve();}
 }));
 await script.load();await readyPromise;
 await device.resume(pid);
 let timer;
 try{await Promise.race([detached,new Promise((_,reject)=>timer=setTimeout(()=>reject(new Error('30-second capture limit')),30000))]);}
 finally{clearTimeout(timer);}
 outcome.detached_reason=reason;
 outcome.pid=pid;outcome.forced=false;
 let alive=true;try{process.kill(pid,0);}catch(e){if(e.code==='ESRCH')alive=false;else throw e;}
 outcome.process_exited=!alive;
 const trace=JSON.parse(fs.readFileSync(path.join(directory,'host-time.json'),'utf8'));
 outcome.exit_code=trace.exit_code;
 if(reason!=='process-terminated'||alive||trace.exit_code!==0)throw new Error('capture did not exit naturally and cleanly');
 const flushed=messages.filter(m=>m.type==='send'&&m.payload.kind==='flushed');
 if(flushed.length!==1||flushed[0].payload.bytes!==flushed[0].payload.expected_bytes)throw new Error('incomplete trace flush');
 outcome.success=true;
}catch(e){
 outcome.success=false;outcome.error=String(e);
 if(pid){try{process.kill(pid,0);await device.kill(pid);forced=true;}catch(e){if(e.code!=='ESRCH')outcome.cleanup_error=String(e);}}
 outcome.forced=forced;process.exitCode=1;
}finally{
 outcome.ready=ready;outcome.finished=new Date().toISOString();outcome.messages=messages;
 fs.writeFileSync(path.join(directory,'controller.json'),JSON.stringify(outcome,null,2)+'\n');
 fs.writeFileSync(path.join(directory,'dosbox.stdout'),Buffer.concat(logs.filter(x=>x.fd===1).map(x=>x.data)));
 fs.writeFileSync(path.join(directory,'dosbox.stderr'),Buffer.concat(logs.filter(x=>x.fd===2).map(x=>x.data)));
 console.log(JSON.stringify({...outcome,messages:messages.map(x=>x.payload?.kind||x.type)}));
}

process.exit(process.exitCode||0);
