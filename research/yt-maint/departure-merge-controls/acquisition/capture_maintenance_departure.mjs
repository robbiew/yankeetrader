import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
// Pure post-exit validation; exported for portable corruption regressions.
export function validateFlush(directory,messages,mode){
 if(!['observed','attach-only'].includes(mode)||!Array.isArray(messages))throw new Error('exact capture mode and message array required');
 if(messages.some(m=>m.type==='error'))throw new Error('observer script error reported');
 const body=fs.readFileSync(path.join(directory,'host-time.json'));
 const receiptBody=fs.readFileSync(path.join(directory,'host-flush.json'));
 const trace=JSON.parse(body.toString('utf8')),receipt=JSON.parse(receiptBody.toString('utf8'));
 const keys=(value,wanted)=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join(',')===[...wanted].sort().join(',');
 const traceKeys=['recipe','observe','module','exit_code','events','errors','dropped'];
 const receiptKeys=['recipe','exit_code','bytes','expected_bytes','events','errors','dropped'];
 if(!keys(trace,traceKeys)||!keys(receipt,receiptKeys))throw new Error('exact trace and flush receipt schemas required');
 if(!body.equals(Buffer.from(JSON.stringify(trace)+'\n','utf8'))||!receiptBody.equals(Buffer.from(JSON.stringify(receipt)+'\n','utf8')))throw new Error('complete canonical UTF8 trace and receipt writes required');
 if(trace.recipe!=='host-dos-placement-cache-observer-v1'||receipt.recipe!=='departure-exit-flush-receipt-v1'||trace.observe!==(mode==='observed'))throw new Error('trace and receipt protocol/mode identity differs');
 if(!Array.isArray(trace.events)||!Array.isArray(trace.errors)||!Number.isInteger(trace.dropped)||trace.dropped!==0||trace.errors.length!==0||trace.exit_code!==0)throw new Error('complete clean zero-exit trace required');
 if((mode==='observed'&&trace.events.length<1)||(mode==='attach-only'&&trace.events.length!==0))throw new Error('exact observed versus attach-only event inventory required');
 for(const field of ['exit_code','bytes','expected_bytes','events','errors','dropped'])if(!Number.isSafeInteger(receipt[field])||receipt[field]<0)throw new Error('nonnegative exact integer receipt fields required');
 if(receipt.exit_code!==0||receipt.bytes!==body.length||receipt.expected_bytes!==body.length||receipt.events!==trace.events.length||receipt.errors!==trace.errors.length||receipt.dropped!==trace.dropped)throw new Error('flush receipt differs from actual UTF8 bytes or complete trace counts');
 const flushed=messages.filter(m=>m.type==='send'&&m.payload?.kind==='flushed');
 if(flushed.length>1)throw new Error('duplicate asynchronous flush acknowledgements');
 if(flushed.length===1){
  const ack=flushed[0].payload;
  if(!keys(ack,['kind','exit_code','bytes','expected_bytes','events','errors','dropped']))throw new Error('exact asynchronous flush acknowledgement schema required');
  for(const field of ['exit_code','bytes','expected_bytes','events','errors','dropped'])if(ack[field]!==receipt[field])throw new Error('asynchronous flush acknowledgement disagrees with synchronous receipt');
 }
 return {trace,receipt,acknowledged:flushed.length===1};
}

export async function main(args=process.argv.slice(2)){
const [modulePath,directory,observerPath,mode,limit='30000']=args;
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
 if(fs.existsSync(path.join(directory,'host-time.json'))||fs.existsSync(path.join(directory,'host-flush.json')))throw new Error('fresh trace and receipt paths required');
 const frida=await bounded(import(pathToFileURL(modulePath).href));
 device=await bounded(frida.getLocalDevice());
 device.output.connect((id,fd,data)=>{if(id===pid&&data)logs.push({fd,data:Buffer.from(data)});});
 pid=await bounded(device.spawn(argv[0],{argv,env:{SDL_VIDEODRIVER:'dummy',SDL_AUDIODRIVER:'dummy'},stdio:'pipe'}).then(value=>{pid=value;if(expired){try{process.kill(pid,'SIGKILL');}catch(e){if(e.code!=='ESRCH')throw e;}}return value;}));
 const session=await bounded(device.attach(pid));
 const detached=new Promise(resolve=>session.detached.connect(r=>{reason=r;resolve();}));
 const config={observe:mode==='observed',output:path.join(directory,'host-time.json'),flush_output:path.join(directory,'host-flush.json')};
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
 const {trace,receipt,acknowledged}=validateFlush(directory,messages,mode);
 outcome.exit_code=trace.exit_code;
 if(reason!=='process-terminated'||alive||trace.exit_code!==0)throw new Error('capture did not exit naturally and cleanly');
 outcome.flush_receipt=receipt;outcome.flush_acknowledged=acknowledged;
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

}

if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)await main();
