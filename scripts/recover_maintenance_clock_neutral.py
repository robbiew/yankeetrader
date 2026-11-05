"""Acquire a bounded host-observed TIMER corpus from disposable original DOS copies.

macOS ARM64 DOSBox Staging0.83.0 with the pinned binary is required. Frida is
operator supplied, not a project dependency. Outputs are captured without
consulting expected after files. Run the portable verifier separately.
"""
import argparse
import gzip,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from verify_maintenance_clock_neutral import GUESTS,HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
NAMES=['YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC']
sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('destination',type=Path)
p.add_argument('--scratch',type=Path,required=True,help='new disposable directory; retained for operator inspection')
p.add_argument('--frida-module',type=Path,required=True,help='existing Frida17.23.2 ESM entrypoint')
p.add_argument('--dosbox',type=Path,default=Path('/opt/homebrew/bin/dosbox-staging'))
args=p.parse_args()
LOGICAL=args.dosbox.absolute();HOST=LOGICAL.resolve(strict=True)
assert sha(HOST.read_bytes())==HOST_SHA,'unsupported DOSBox binary: do not apply offsets'
assert args.frida_module.is_file(),'operator-supplied Frida entrypoint required'
DEST=args.destination.absolute();SCRATCH=args.scratch.absolute()
assert not DEST.exists()and not SCRATCH.exists(),'new output and scratch directories required'
DEST.mkdir(parents=True);SCRATCH.mkdir(parents=True)
for name,mode in [('unobserved-a','unobserved'),('observed-a','observed'),('attach-only','attach-only'),('observed-b','observed'),('unobserved-b','unobserved'),('observed-c','observed')]:
 tmp=SCRATCH/name;tmp.mkdir()
 for n in GUESTS:shutil.copyfile(ROOT/'archive/dos-original'/n,tmp/n)
 for n in NAMES[:3]:(tmp/n).write_bytes(gzip.decompress((ROOT/'research/yt-maint/initial-controls/baseline-split'/('before-'+n+'.gz')).read_bytes()))
 commands=['date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN',
           'if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG',
           'echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
 (tmp/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
 argv=[str(LOGICAL),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in ['mount c '+str(tmp),'c:']+commands+['exit']for v in ('-c',c)]
 (tmp/'launch.json').write_text(json.dumps(argv,indent=2)+'\n')
 before={n:sha((tmp/n).read_bytes())for n in NAMES[:3]};guests={n:sha((tmp/n).read_bytes())for n in GUESTS};assert guests==GUESTS
 argv=json.loads((tmp/'launch.json').read_text())
 start=time.monotonic()
 if mode=='unobserved':
  env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
  with (tmp/'dosbox.stdout').open('wb')as out,(tmp/'dosbox.stderr').open('wb')as err:
   child=subprocess.Popen(argv,env=env,stdout=out,stderr=err)
   try:code=child.wait(timeout=30)
   except subprocess.TimeoutExpired:
    child.kill();child.wait();raise
  controller={'mode':mode,'success':code==0,'exit_code':code,'forced':False,'process_exited':child.poll()is not None,'pid':child.pid}
  (tmp/'controller.json').write_text(json.dumps(controller,indent=2)+'\n')
 else:
  subprocess.run(['node',str(ROOT/'scripts/capture_maintenance_clock_neutral.mjs'),str(args.frida_module),str(tmp),str(ROOT/'scripts/observe_maintenance_clock.js'),mode],check=True,timeout=40)
  controller=json.loads((tmp/'controller.json').read_text())
 assert controller['success']and not controller['forced']and controller['process_exited']
 guests_after={n:sha((tmp/n).read_bytes())for n in guests};assert guests_after==guests
 output={n:sha((tmp/n).read_bytes())for n in NAMES}
 case=DEST/name;case.mkdir()
 for n in NAMES:(case/('after-'+n+'.gz')).write_bytes(gzip.compress((tmp/n).read_bytes(),mtime=0))
 for n in ['COMMANDS.TXT','controller.json','launch.json','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','OK.LOG','ERROR.LOG','RETURN.LOG','TRACE.BIN','dosbox.stdout','dosbox.stderr']:
  shutil.copyfile(tmp/n,case/n)
 if mode!='unobserved':
  (case/'host-time.json.gz').write_bytes(gzip.compress((tmp/'host-time.json').read_bytes(),mtime=0));shutil.copyfile(tmp/'loaded-observer.js',case/'loaded-observer.js')
 meta={'recipe':'maintenance-clock-neutral-v1','date':'11/02/2026','clock':'00:00:00','name':name,'mode':mode,'argv':argv,'host':{'path':str(HOST),'sha256':sha(HOST.read_bytes()),'size':HOST.stat().st_size,'version':'0.83.0','architecture':'arm64','uuid':'31CDF62F-E9EE-39ED-A05A-10E4072BD15E','source_commit':'7b40053b7ac580843d0461eba8c36a47a990e66c'},'guest_before':guests,'guest_after':guests_after,'inputs':before,'before':before,'after':output,'elapsed_seconds':time.monotonic()-start,'controller':controller,'environment':{'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},'source_input':'research/yt-maint/initial-controls/baseline-split'}
 meta['files']={p.name:sha(p.read_bytes())for p in sorted(case.iterdir())}
 (case/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')
 print(name,'captured six outputs; natural exit; verification is separate',flush=True)
