"""Acquire longer survivor-chain controls with exact six-file child handoffs.

Each verified November4 output is copied unchanged per mode. Four
explicit two-child schedules measure November5/6 without resetting any file.
Original guests are unchanged; fresh paths and natural exits required; no retry.
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

from verify_maintenance_clock_neutral import GUESTS,HOST_SHA

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
PROFILES={name:(('11/05/2026','00:00:00'),('11/06/2026','00:00:00'))for name in ('mercenary-survivor','planet-survivor','neutral-survivor','mine-survivor')}
STAGES=('child-1','child-2')
COMBAT_PINS='fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5'
CLOCK_PINS='c6fc45c0d1adf29bf2104574d1e341791f9f9fa15d2059c52a04ecd917beb826'
PARENTS={
 'mercenary-survivor':dict(corpus='evolved-combat-controls',profile='route-mercenary-100000',stage='child-2',pins=COMBAT_PINS),
 'planet-survivor':dict(corpus='evolved-combat-controls',profile='route-planet-neutral',stage='child-2',pins=COMBAT_PINS),
 'neutral-survivor':dict(corpus='evolved-combat-controls',profile='route-neutral-37',stage='child-2',pins=COMBAT_PINS),
 'mine-survivor':dict(corpus='evolved-clock-controls',profile='second-two',stage='child-2',pins=CLOCK_PINS),
}


def parent_inputs(profile,mode):
    source=PARENTS[profile];base=ROOT/'research/yt-maint'/source['corpus']
    raw=(base/'pins.json').read_bytes();assert SHA(raw)==source['pins'],'verified corresponding parent corpus identity'
    pins=json.loads(raw)['files'];result={}
    for name in FILES:
        relative=source['profile']+'/'+source['stage']+'/'+mode+'/after-'+name+'.gz'
        compressed=(base/relative).read_bytes();assert SHA(compressed)==pins[relative],'immutable per-mode prior output'
        result[name]=gzip.decompress(compressed)
    return result


def capture(destination,scratch,profile,stage,mode,dosbox,frida):
    date,clock=PROFILES[profile][STAGES.index(stage)]
    parent='prior-child-2'if stage=='child-1'else'child-1'
    tmp=scratch/profile/stage/mode;tmp.mkdir(parents=True,exist_ok=False)
    binaries={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in GUESTS}
    assert {n:SHA(b)for n,b in binaries.items()}==GUESTS
    if stage=='child-1':inputs=parent_inputs(profile,mode)
    else:inputs={n:gzip.decompress((destination/profile/'child-1'/mode/('after-'+n+'.gz')).read_bytes())for n in FILES}
    for n,b in inputs.items():(tmp/n).write_bytes(b)
    guests=binaries
    for n,b in guests.items():(tmp/n).write_bytes(b)
    commands=['date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
    (tmp/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
    argv=[str(dosbox),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in ['mount c '+str(tmp),'c:']+commands+['exit']for v in('-c',c)]
    (tmp/'launch.json').write_text(json.dumps(argv,indent=2)+'\n');start=time.monotonic()
    actual=MODES[mode]
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
    out=destination/profile/stage/mode;out.mkdir(parents=True,exist_ok=False)
    names={'COMMANDS.TXT','launch.json','controller.json','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','TRACE.BIN','OK.LOG','ERROR.LOG','RETURN.LOG','dosbox.stdout','dosbox.stderr'}
    for n in names:shutil.copyfile(tmp/n,out/n)
    if actual!='unobserved':
        (out/'host-time.json.gz').write_bytes(gzip.compress((tmp/'host-time.json').read_bytes(),mtime=0));shutil.copyfile(tmp/'loaded-observer.js',out/'loaded-observer.js')
    outputs={}
    for n,b in inputs.items():(out/('before-'+n+'.gz')).write_bytes(gzip.compress(b,mtime=0))
    for p in tmp.iterdir():
        if p.suffix.upper()in('.DAT','.ASC'):
            outputs[p.name]=SHA(p.read_bytes());(out/('after-'+p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    meta=dict(recipe='maintenance-survivor-chains-v1',profile=profile,stage=stage,mode=mode,parent=parent,parent_mode=mode,parent_source=PARENTS[profile],parent_pins=PARENTS[profile]['pins'],date=date,clock=clock,cycles=200000,argv=argv,host_sha256=SHA(dosbox.resolve().read_bytes()),guests={n:SHA(b)for n,b in guests.items()},inputs={n:SHA(b)for n,b in inputs.items()},outputs=outputs,controller=controller,elapsed_seconds=time.monotonic()-start)
    meta['files']={p.name:SHA(p.read_bytes())for p in sorted(out.iterdir())};(out/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(profile,stage,mode,'complete6files',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--scratch',type=Path,required=True);p.add_argument('--frida-module',type=Path,required=True);p.add_argument('--profiles',default=','.join(PROFILES));a=p.parse_args()
    out=a.destination.absolute();scratch=a.scratch.absolute();host=Path('/opt/homebrew/bin/dosbox-staging')
    assert SHA(host.resolve().read_bytes())==HOST_SHA and a.frida_module.is_file(),'pinned installed host and Frida required'
    assert not out.exists()and not scratch.exists(),'fresh full chain paths required'
    out.mkdir(parents=True);scratch.mkdir(parents=True)
    selected=a.profiles.split(',');assert len(selected)==len(set(selected))and set(selected)<=set(PROFILES),'declared unique profiles required'
    for profile in selected:
        for stage in STAGES:
            for mode in MODES:capture(out,scratch,profile,stage,mode,host,a.frida_module)

if __name__=='__main__':main()
