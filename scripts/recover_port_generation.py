"""Observe untouched DOS initializer ports before and after its maintenance chain."""
import argparse,gzip,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
# Declared disposable replacement for the initializer's final maintenance child:
# mov ax,4c00h; int21h. The archived initializer/runtime are never patched.
EXIT_STUB=bytes.fromhex('b8004ccd21')

def run(destination):
 destination.mkdir(parents=True,exist_ok=False)
 for name,clock in [('midnight','00:00:00'),('repeat','00:00:00'),('later','12:34:00')]:
  d=destination/name;d.mkdir()
  for binary in ['YT-INIT.EXE','BRUN30.EXE']:shutil.copy2(ROOT/'archive/dos-original'/binary,d/binary)
  (d/'YTMAINT.EXE').write_bytes(EXIT_STUB);(d/'ANSWERS.TXT').write_bytes(b'Y\r\n\r\n')
  metadata=dict(name=name,date='11/02/2026',time=clock,recipe='dos-port-generation-v1',maintenance_child='declared-exit-stub',binaries={p.name:SHA(p.read_bytes()) for p in d.glob('*.EXE')})
  def launch(commands,tag):
   with (d/(tag+'-dosbox.log')).open('w') as out:
    subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for c in ['mount c '+str(d),'c:','date 11/02/2026','time '+clock]+commands+['exit'] for x in ('-c',c)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
  launch(['yt-init < answers.txt > init.log','echo INITIALIZER_RETURNED > INITRET.LOG'],'init')
  before=(d/'YTDATA.DAT').read_bytes();(d/'before-maint.dat.gz').write_bytes(gzip.compress(before,mtime=0))
  shutil.copy2(ROOT/'archive/dos-original/YTMAINT.EXE',d/'YTMAINT.EXE')
  metadata['actual_maintenance_sha256']=SHA((d/'YTMAINT.EXE').read_bytes())
  launch(['ytmaint > maint.log','echo MAINTENANCE_RETURNED > MAINTRET.LOG'],'maint')
  (d/'after-maint.dat.gz').write_bytes(gzip.compress((d/'YTDATA.DAT').read_bytes(),mtime=0))
  keep=['before-maint.dat.gz','after-maint.dat.gz','INIT.LOG','MAINT.LOG','INITRET.LOG','MAINTRET.LOG','ANSWERS.TXT','init-dosbox.log','maint-dosbox.log']
  metadata['files']={n:SHA((d/n).read_bytes()) for n in keep}
  (d/'result.json').write_text(json.dumps(metadata,indent=2)+'\n')
  for p in d.iterdir():
   if p.name not in keep+['result.json']:p.unlink()
  print(name,len(before),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args();run(a.destination.resolve())
