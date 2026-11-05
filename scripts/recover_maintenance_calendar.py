"""Acquire independent initial-world calendar/clock pairs with original guest binaries."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from recover_initial_maintenance import ROOT, BINARIES, launch
from verify_maintenance_clock_neutral import HOST_SHA

SHA=lambda b:hashlib.sha256(b).hexdigest()
CASES={'next-day':('11/03/2026','00:00:00'), 'new-year':('01/01/2027','00:00:00'),
       'leap-day':('02/29/2028','00:00:00'), 'noon':('11/02/2026','12:34:00')}
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')


def capture(destination,scratch,frida):
    assert not destination.exists() and not scratch.exists(), 'new evidence and scratch paths required'
    host=Path('/opt/homebrew/bin/dosbox-staging')
    assert SHA(host.resolve().read_bytes())==HOST_SHA, 'pinned supported host required'
    binaries={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in BINARIES}
    assert {n:SHA(b)for n,b in binaries.items()}==BINARIES
    destination.mkdir(parents=True);scratch.mkdir(parents=True)
    for name,(date,clock)in CASES.items():
        init=scratch/(name+'-init');init.mkdir()
        for n,b in binaries.items():(init/n).write_bytes(b)
        (init/'YTMAINT.EXE').write_bytes(bytes.fromhex('b8004ccd21'))
        (init/'ANSWERS.TXT').write_bytes(b'Y\r\n\r\n')
        commands=['date '+date,'time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG',
                  'yt-init < answers.txt > INIT.LOG','echo INITIALIZER_RETURNED > INITRET.LOG']
        launch(init,commands,'init')
        assert b'<YT-INIT Normal Termination>'in(init/'INIT.LOG').read_bytes()
        case=destination/name;case.mkdir()
        before={n:(init/n).read_bytes()for n in FILES[:3]}
        for n,b in before.items():(case/('before-'+n+'.gz')).write_bytes(gzip.compress(b,mtime=0))
        for n in ('ANSWERS.TXT','DOSDATE.LOG','DOSTIME.LOG','INIT.LOG','INITRET.LOG','init-commands.txt','init-dosbox.log'):
            shutil.copyfile(init/n,case/('init-'+n))
        for mode in ('unobserved','observed-a','observed-b'):
            d=scratch/(name+'-'+mode);d.mkdir()
            for n in ('YTMAINT.EXE','BRUN30.EXE'):(d/n).write_bytes(binaries[n])
            for n,b in before.items():(d/n).write_bytes(b)
            commands=['date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG',
                      'ytmaint > TRACE.BIN','echo PROGRAM_RETURNED > RETURN.LOG',
                      'date > ENDDATE.LOG','time > ENDTIME.LOG']
            argv=[str(host),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[
                v for c in ['mount c '+str(d),'c:']+commands+['exit']for v in ('-c',c)]
            (d/'launch.json').write_text(json.dumps(argv,indent=2)+'\n')
            (d/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
            start=time.monotonic()
            if mode=='unobserved':
                with(d/'dosbox.stdout').open('wb')as out,(d/'dosbox.stderr').open('wb')as err:
                    child=subprocess.Popen(argv,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=out,stderr=err)
                    try:code=child.wait(timeout=30)
                    except subprocess.TimeoutExpired:child.kill();child.wait();raise
                assert code==0
                controller={'success':True,'forced':False,'exit_code':code,'process_exited':True}
                (d/'controller.json').write_text(json.dumps(controller,indent=2)+'\n')
            else:
                subprocess.run(['node',str(ROOT/'scripts/capture_maintenance_clock_neutral.mjs'),str(frida),str(d),
                                str(ROOT/'scripts/observe_maintenance_clock.js'),'observed'],check=True,timeout=40,
                               stdout=subprocess.DEVNULL)
                controller=json.loads((d/'controller.json').read_text())
                assert controller['success']and not controller['forced']and controller['process_exited']
            assert b'Daily Maintenance Completed OK'in(d/'TRACE.BIN').read_bytes()
            assert all((d/n).read_bytes()==binaries[n]for n in ('YTMAINT.EXE','BRUN30.EXE'))
            target=case/mode;target.mkdir()
            for n in FILES:(target/('after-'+n+'.gz')).write_bytes(gzip.compress((d/n).read_bytes(),mtime=0))
            for n in ('launch.json','COMMANDS.TXT','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG',
                      'TRACE.BIN','RETURN.LOG','dosbox.stdout','dosbox.stderr','controller.json'):
                shutil.copyfile(d/n,target/n)
            if mode!='unobserved':
                shutil.copyfile(d/'loaded-observer.js',target/'loaded-observer.js')
                (target/'host-time.json.gz').write_bytes(gzip.compress((d/'host-time.json').read_bytes(),mtime=0))
            meta=dict(recipe='independent-maintenance-calendar-v1',name=name,mode=mode,date=date,clock=clock,
                      binaries=BINARIES,host_sha256=HOST_SHA,elapsed_seconds=time.monotonic()-start,
                      files={p.name:SHA(p.read_bytes())for p in sorted(target.iterdir())})
            (target/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')
            print(name,mode,flush=True)
        (case/'input.json').write_text(json.dumps(dict(name=name,date=date,clock=clock,binaries=BINARIES,
            files={p.name:SHA(p.read_bytes())for p in sorted(case.iterdir())if p.is_file()}),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    p.add_argument('--scratch',type=Path,required=True);p.add_argument('--frida-module',type=Path,required=True)
    a=p.parse_args();capture(a.destination.resolve(),a.scratch.resolve(),a.frida_module.resolve())
