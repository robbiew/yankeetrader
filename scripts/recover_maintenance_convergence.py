"""Acquire final-pointer convergence and an exact three-day six-file chain.

All full runs use unchanged original guests in new mounts. Early-cache probes
are explicitly patched, distinct runs and never full maintenance controls.
No automatic retries; rejected artifacts stay in the external mount directory.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from replay_qb_graph import mbf
from recover_maintenance_sequence import patch
from verify_maintenance_clock_neutral import GUESTS,HOST_SHA

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
DAYS={'day-1':('11/02/2026',None),'day-2':('11/03/2026','day-1'),'day-3':('11/04/2026','day-2')}


def initial_inputs():
    files={n:gzip.decompress((ROOT/'research/yt-maint/initial-controls/baseline-split'/('before-'+n+'.gz')).read_bytes())for n in FILES[:3]}
    world=bytearray(files['YTDATA.DAT']);record=4053;at=(record-1)*137;name='Convergence Haven'
    world[at:at+137]=name.encode().ljust(41,b' ')+bytes(96)
    for off,value in [(41,305),(45,1000),(49,1000),(53,1000),(73,-1),(77,500000),(85,len(name))]:mbf.put(world,record,off,value)
    mbf.put(world,2853,93,2) # sector2802 is the first active-world preferred candidate.
    files['YTDATA.DAT']=bytes(world);return files


def cache_probe(raw):
    result=bytearray(patch(raw,0x29b7,1,0x1c52))
    assert result[0x244:0x272].count(bytes.fromhex('b90400'))==1
    result[0x244:0x272]=bytes(result[0x244:0x272]).replace(bytes.fromhex('b90400'),bytes.fromhex('b9a800'))
    return bytes(result)


def capture(destination,scratch,day,mode,dosbox,frida,*,probe=False):
    date,parent=DAYS[day];label='cache-'+mode if probe else mode
    tmp=scratch/day/label;tmp.mkdir(parents=True,exist_ok=False)
    binaries={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in GUESTS}
    assert {n:SHA(b)for n,b in binaries.items()}==GUESTS
    if parent is None:
        assert not probe,'initial cache normalization is already recovered'
        inputs=initial_inputs()
    else:
        inputs={n:gzip.decompress((destination/parent/mode/('after-'+n+'.gz')).read_bytes())for n in FILES}
    for n,b in inputs.items():(tmp/n).write_bytes(b)
    guests={n:cache_probe(b)if probe and n=='YTMAINT.EXE'else b for n,b in binaries.items()}
    for n,b in guests.items():(tmp/n).write_bytes(b)
    commands=['date '+date,'time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
    (tmp/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
    argv=[str(dosbox),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in ['mount c '+str(tmp),'c:']+commands+['exit']for v in('-c',c)]
    (tmp/'launch.json').write_text(json.dumps(argv,indent=2)+'\n');start=time.monotonic()
    actual='unobserved'if probe else MODES[mode]
    if actual=='unobserved':
        with(tmp/'dosbox.stdout').open('wb')as out,(tmp/'dosbox.stderr').open('wb')as err:
            child=subprocess.Popen(argv,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=out,stderr=err)
            try:code=child.wait(timeout=30)
            except subprocess.TimeoutExpired:child.kill();child.wait();raise
        controller=dict(mode=actual,success=code==0,exit_code=code,forced=False,process_exited=child.poll()is not None,pid=child.pid)
        (tmp/'controller.json').write_text(json.dumps(controller,indent=2)+'\n')
    else:
        subprocess.run(['node',str(ROOT/'scripts/capture_maintenance_clock_neutral.mjs'),str(frida),str(tmp),str(ROOT/'scripts/observe_maintenance_placement.js'),actual],check=True,timeout=40,stdout=subprocess.DEVNULL)
        controller=json.loads((tmp/'controller.json').read_text())
    assert controller['success']and controller['process_exited']and not controller['forced'],'natural child completion required'
    assert {n:SHA((tmp/n).read_bytes())for n in guests}=={n:SHA(b)for n,b in guests.items()},'guest bytes changed during run'
    out=destination/day/label;out.mkdir(parents=True,exist_ok=False)
    names={'COMMANDS.TXT','launch.json','controller.json','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','TRACE.BIN','OK.LOG','ERROR.LOG','RETURN.LOG','dosbox.stdout','dosbox.stderr'}
    for n in names:shutil.copyfile(tmp/n,out/n)
    if actual!='unobserved':
        (out/'host-time.json.gz').write_bytes(gzip.compress((tmp/'host-time.json').read_bytes(),mtime=0));shutil.copyfile(tmp/'loaded-observer.js',out/'loaded-observer.js')
    outputs={}
    for n,b in inputs.items():(out/('before-'+n+'.gz')).write_bytes(gzip.compress(b,mtime=0))
    for p in tmp.iterdir():
        if p.suffix.upper()in('.DAT','.ASC'):
            outputs[p.name]=SHA(p.read_bytes());(out/('after-'+p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    meta=dict(recipe='maintenance-convergence-chain-v1',day=day,mode=label,parent=parent,parent_mode=mode if parent else None,probe=probe,date=date,clock='00:00:00',cycles=200000,argv=argv,host_sha256=SHA(dosbox.resolve().read_bytes()),guests={n:SHA(b)for n,b in guests.items()},inputs={n:SHA(b)for n,b in inputs.items()},outputs=outputs,controller=controller,elapsed_seconds=time.monotonic()-start)
    meta['files']={p.name:SHA(p.read_bytes())for p in sorted(out.iterdir())};(out/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(day,label,'early cache168bytes'if probe else'complete6files',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--scratch',type=Path,required=True);p.add_argument('--frida-module',type=Path,required=True);a=p.parse_args()
    out=a.destination.absolute();scratch=a.scratch.absolute();host=Path('/opt/homebrew/bin/dosbox-staging')
    assert SHA(host.resolve().read_bytes())==HOST_SHA and a.frida_module.is_file(),'pinned installed host and Frida required'
    assert not out.exists()and not scratch.exists(),'fresh full chain paths required'
    out.mkdir(parents=True);scratch.mkdir(parents=True)
    for day,(_,parent)in DAYS.items():
        for mode in MODES:capture(out,scratch,day,mode,host,a.frida_module)
        if parent:
            for mode in MODES:capture(out,scratch,day,mode,host,a.frida_module,probe=True)

if __name__=='__main__':main()
