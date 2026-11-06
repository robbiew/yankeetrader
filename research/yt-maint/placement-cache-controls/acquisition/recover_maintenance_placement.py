"""Acquire bounded placement/cache controls in disposable copied DOS worlds.

Positive/fractional inactive planet links are explicitly synthetic branch gates.
No capture retries or in-place original edits are performed. A separate early
cache probe has a declared168-byte output and is not an untouched full run.
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
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
CASES={
 'wanderer-reject-two':[(51+1095,93,2),(51+1792,93,2)],
 'wanderer-reject-three':[(51+1095,93,2),(51+1792,93,2),(51+1295,93,2)],
 'wanderer-positive-fraction':[(51+1095,93,.25)],
 'wanderer-negative-link':[(51+1095,93,-1)],
 'wanderer-zero-residue':[(51+1095,93,'00004800')],
 'base-positive-fraction':[(51+2598,93,.25)],
 'duplicate-hq':[(53,105,849)],
 'duplicate-hq-chain':[(53,105,849),(54,105,849),(71,105,849)],
 'duplicate-mobile':[(53,105,1000),(54,105,1000),(1051,81,37),(1051,85,-1)],
 'pointer-neutral-sector':[(53,105,3000),(3051,81,37),(3051,85,0)],
 'pointer-mercenary-sector':[(53,105,3000),(3051,81,37),(3051,85,-2)],
 'unpointed-friendly-merge':[(1599,81,37),(1599,85,-1)],
}


def before_inputs(case):
    data={n:gzip.decompress((ROOT/'research/yt-maint/initial-controls/baseline-split'/('before-'+n+'.gz')).read_bytes())for n in ('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT')}
    world=bytearray(data['YTDATA.DAT'])
    for rec,offset,value in CASES[case]:
        at=(rec-1)*137+offset;world[at:at+4]=bytes.fromhex(value)if type(value)is str else mbf.enc(value)
    data['YTDATA.DAT']=bytes(world);return data


def cache_probe(raw):
    result=bytearray(patch(raw,0x29b7,1,0x1c52))
    assert result[0x244:0x272].count(bytes.fromhex('b90400'))==1
    payload=bytes(result[0x244:0x272]).replace(bytes.fromhex('b90400'),bytes.fromhex('b9a800'))
    result[0x244:0x272]=payload;return bytes(result)


def capture(destination,scratch,case,mode,dosbox,frida):
    tmp=scratch/case/mode;tmp.mkdir(parents=True,exist_ok=False)
    binaries={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in GUESTS}
    assert {n:SHA(b)for n,b in binaries.items()}==GUESTS
    inputs=before_inputs(case)
    for n,b in inputs.items():(tmp/n).write_bytes(b)
    for n,b in binaries.items():(tmp/n).write_bytes(cache_probe(b)if mode=='cache-probe'and n=='YTMAINT.EXE'else b)
    commands=['date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
    (tmp/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
    argv=[str(dosbox),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in ['mount c '+str(tmp),'c:']+commands+['exit']for v in ('-c',c)]
    (tmp/'launch.json').write_text(json.dumps(argv,indent=2)+'\n');start=time.monotonic()
    actual='unobserved'if mode=='cache-probe'else MODES[mode]
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
    assert {n:SHA((tmp/n).read_bytes())for n in GUESTS}=={n:SHA(cache_probe(b)if mode=='cache-probe'and n=='YTMAINT.EXE'else b)for n,b in binaries.items()},'guest file changed during execution'
    caseout=destination/case/mode;caseout.mkdir(parents=True,exist_ok=False)
    names={'COMMANDS.TXT','launch.json','controller.json','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','TRACE.BIN','OK.LOG','ERROR.LOG','RETURN.LOG','dosbox.stdout','dosbox.stderr'}
    for n in names:shutil.copyfile(tmp/n,caseout/n)
    if actual!='unobserved':
        (caseout/'host-time.json.gz').write_bytes(gzip.compress((tmp/'host-time.json').read_bytes(),mtime=0));shutil.copyfile(tmp/'loaded-observer.js',caseout/'loaded-observer.js')
    outputs={}
    for p in tmp.iterdir():
        if p.suffix.upper()in('.DAT','.ASC'):
            outputs[p.name]=SHA(p.read_bytes());(caseout/('after-'+p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    meta=dict(recipe='maintenance-placement-cache-v1',case=case,mode=mode,date='11/02/2026',clock='00:00:00',cycles=200000,patches=CASES[case],argv=argv,host_sha256=SHA(dosbox.resolve().read_bytes()),guests={n:SHA((tmp/n).read_bytes())for n in GUESTS},inputs={n:SHA(b)for n,b in inputs.items()},outputs=outputs,controller=controller,elapsed_seconds=time.monotonic()-start)
    meta['files']={p.name:SHA(p.read_bytes())for p in sorted(caseout.iterdir())};(caseout/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(case,mode,'natural exit;6outputs'if mode!='cache-probe'else'168byte earlycache probe',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--scratch',type=Path,required=True);p.add_argument('--frida-module',type=Path,required=True);p.add_argument('--cases',default=','.join(CASES));p.add_argument('--modes',default=','.join(MODES)+',cache-probe');a=p.parse_args()
    out=a.destination.absolute();scratch=a.scratch.absolute();host=Path('/opt/homebrew/bin/dosbox-staging')
    assert SHA(host.resolve().read_bytes())==HOST_SHA and a.frida_module.is_file(),'pinned installed host and existingFrida required'
    assert not out.exists()and not scratch.exists(),'fresh destinations required'
    cases=a.cases.split(',');modes=a.modes.split(',');assert len(set(cases))==len(cases)and set(cases)<=set(CASES)and len(set(modes))==len(modes)and set(modes)<=set(MODES)|{'cache-probe'}
    out.mkdir(parents=True);scratch.mkdir(parents=True)
    for case in cases:
        for mode in modes:capture(out,scratch,case,mode,host,a.frida_module)

if __name__=='__main__':main()
