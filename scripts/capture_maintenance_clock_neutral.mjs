import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
const [modulePath,directory,observerPath,mode,limit='30000']=process.argv.slice(2);
const deadlineMs=Number(limit);
if(!Number.isInteger(deadlineMs)||deadlineMs<1||deadlineMs>30000)throw new Error('deadline must be 1..30000 milliseconds');
if(!['observed','attach-only'].includes(mode))throw new Error('mode must be observed or attach-only');
const packagePath=path.resolve(path.dirname(modulePath),'../../package.json');
const pkg=JSON.parse(fs.readFileSync(packagePath,'utf8'));
if(pkg.name!=='frida'||pkg.version!=='17.23.2')throw new Error('Frida17.23.2 required for this capture recipe');
const fridaIdentity={version:pkg.version,module:path.resolve(modulePath),module_sha256:crypto.createHash('sha256').update(fs.readFileSync(modulePath)).digest('hex'),package_sha256:crypto.createHash('sha256').update(fs.readFileSync(packagePath)).digest('hex')};
let device;
const argv=JSON.parse(fs.readFileSync(path.join(directory,'launch.json'),'utf8'));
const messages=[];const logs=[];let pid=null,forced=false,reason=null,ready=false;
let expired=false;
let deadlineTimer;
const deadline=new Promise((_,reject)=>{deadlineTimer=setTimeout(()=>{expired=true;reject(new Error('capture deadline, including initialization'));},deadlineMs);});
const bounded=p=>Promise.race([p,deadline]);
async function terminateOwned(){
 if(!pid)return;
 try{process.kill(pid,'SIGKILL');forced=true;}catch(e){if(e.code!=='ESRCH')throw e;}
 const until=Date.now()+2000;
 while(Date.now()<until){
  await new Promise(resolve=>setTimeout(resolve,10));
  try{process.kill(pid,0);}catch(e){if(e.code==='ESRCH'){outcome.process_exited=true;return;}throw e;}
 }
 throw new Error('owned process did not exit after SIGKILL');
}
const outcome={mode,frida:fridaIdentity,node_version:process.version,started:new Date().toISOString()};
try {
 const frida=await bounded(import(pathToFileURL(modulePath).href));
 device=await bounded(frida.getLocalDevice());
 device.output.connect((id,fd,data)=>{if(id===pid&&data)logs.push({fd,data:Buffer.from(data)});});
 pid=await bounded(device.spawn(argv[0],{argv,env:{SDL_VIDEODRIVER:'dummy',SDL_AUDIODRIVER:'dummy'},stdio:'pipe'}).then(value=>{pid=value;if(expired){try{process.kill(pid,'SIGKILL');}catch(e){if(e.code!=='ESRCH')throw e;}}return value;}));
 const session=await bounded(device.attach(pid));
 const detached=new Promise(resolve=>session.detached.connect(r=>{reason=r;resolve();}));
 const config={observe:mode==='observed',output:path.join(directory,'host-time.json')};
 const source='const CONFIG='+JSON.stringify(config)+';\n'+fs.readFileSync(observerPath,'utf8');
 fs.writeFileSync(path.join(directory,'loaded-observer.js'),source);
 const script=await bounded(session.createScript(source));
 const readyPromise=new Promise((resolve,reject)=>script.message.connect(message=>{
  messages.push(message);
  if(message.type==='error')reject(new Error(message.description));
  if(message.type==='send'&&message.payload.kind==='ready'){ready=true;resolve();}
 }));
 await bounded(script.load());await bounded(readyPromise);
 await bounded(device.resume(pid));
 await bounded(detached);
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
 try{await terminateOwned();}catch(cleanup){outcome.cleanup_error=String(cleanup);}
 outcome.forced=forced;process.exitCode=1;
}finally{
 clearTimeout(deadlineTimer);
 outcome.ready=ready;outcome.finished=new Date().toISOString();outcome.messages=messages;
 fs.writeFileSync(path.join(directory,'controller.json'),JSON.stringify(outcome,null,2)+'\n');
 fs.writeFileSync(path.join(directory,'dosbox.stdout'),Buffer.concat(logs.filter(x=>x.fd===1).map(x=>x.data)));
 fs.writeFileSync(path.join(directory,'dosbox.stderr'),Buffer.concat(logs.filter(x=>x.fd===2).map(x=>x.data)));
 console.log(JSON.stringify({...outcome,messages:messages.map(x=>x.payload?.kind||x.type)}));
}

process.exit(process.exitCode||0);
