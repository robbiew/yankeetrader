"""Acquire separate date/clock maintenance controls without changing guest code.

Clock schedules are declared a priori. Every run is disposable and retains all
outputs; the portable verifier independently classifies equality and model gaps.
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

from verify_maintenance_clock_neutral import GUESTS, HOST_SHA

ROOT=Path(__file__).resolve().parents[1]
INPUTS=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT')
RECIPES={
    'shift-two':('11/02/2026','00:00:02',200000),
    'noon':('11/02/2026','12:00:00',200000),
    'late':('11/02/2026','23:59:59',200000),
    'near-midnight-100k':('11/02/2026','23:59:59',100000),
    'rollover':('11/02/2026','23:59:59',10000),
    'next-day':('11/03/2026','00:00:00',200000),
    'eleven-days':('11/13/2026','00:00:00',200000),
    'next-year':('01/01/2027','00:00:00',200000),
}
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only',
       'observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def capture(destination,scratch,recipe,mode_name,dosbox,frida):
    date,clock,cycles=RECIPES[recipe];mode=MODES[mode_name]
    tmp=scratch/recipe/mode_name;tmp.mkdir(parents=True)
    for name in GUESTS:shutil.copyfile(ROOT/'archive/dos-original'/name,tmp/name)
    for name in INPUTS:(tmp/name).write_bytes(gzip.decompress((ROOT/'research/yt-maint/initial-controls/baseline-split'/('before-'+name+'.gz')).read_bytes()))
    guests={name:SHA((tmp/name).read_bytes())for name in GUESTS};assert guests==GUESTS
    before={name:SHA((tmp/name).read_bytes())for name in INPUTS}
    commands=['date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN',
              'if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG',
              'echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
    (tmp/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
    argv=[str(dosbox),'--noprimaryconf','--nolocalconf','--set','cpu_cycles='+str(cycles),'--set','nosound=true']+[value for command in ['mount c '+str(tmp),'c:']+commands+['exit']for value in ('-c',command)]
    (tmp/'launch.json').write_text(json.dumps(argv,indent=2)+'\n')
    start=time.monotonic()
    if mode=='unobserved':
        env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
        with(tmp/'dosbox.stdout').open('wb')as out,(tmp/'dosbox.stderr').open('wb')as err:
            child=subprocess.Popen(argv,env=env,stdout=out,stderr=err)
            try:code=child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill();child.wait();raise
        controller={'mode':mode,'success':code==0,'exit_code':code,'forced':False,'process_exited':child.poll()is not None,'pid':child.pid}
        (tmp/'controller.json').write_text(json.dumps(controller,indent=2)+'\n')
    else:
        subprocess.run(['node',str(ROOT/'scripts/capture_maintenance_clock_neutral.mjs'),str(frida),str(tmp),str(ROOT/'scripts/observe_maintenance_clock_matrix.js'),mode],check=True,timeout=40,stdout=subprocess.DEVNULL)
        controller=json.loads((tmp/'controller.json').read_text())
    assert controller['success']and not controller['forced']and controller['process_exited']
    guest_after={name:SHA((tmp/name).read_bytes())for name in GUESTS};assert guest_after==guests
    case=destination/recipe/mode_name;case.mkdir(parents=True)
    outputs={}
    for file in sorted(tmp.iterdir()):
        if file.suffix.upper()in('.DAT','.ASC'):
            outputs[file.name]=SHA(file.read_bytes());(case/('after-'+file.name+'.gz')).write_bytes(gzip.compress(file.read_bytes(),mtime=0))
    for name in ['COMMANDS.TXT','controller.json','launch.json','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','OK.LOG','ERROR.LOG','RETURN.LOG','TRACE.BIN','dosbox.stdout','dosbox.stderr']:shutil.copyfile(tmp/name,case/name)
    if mode!='unobserved':
        (case/'host-time.json.gz').write_bytes(gzip.compress((tmp/'host-time.json').read_bytes(),mtime=0));shutil.copyfile(tmp/'loaded-observer.js',case/'loaded-observer.js')
    host=dosbox.resolve(strict=True)
    meta={'recipe':'maintenance-clock-matrix-v1','profile':recipe,'date':date,'clock':clock,'cycles':cycles,'name':mode_name,'mode':mode,
          'argv':argv,'host':{'path':str(host),'sha256':SHA(host.read_bytes()),'size':host.stat().st_size,'version':'0.83.0','architecture':'arm64','uuid':'31CDF62F-E9EE-39ED-A05A-10E4072BD15E','source_commit':'7b40053b7ac580843d0461eba8c36a47a990e66c'},
          'guest_before':guests,'guest_after':guest_after,'inputs':before,'after':outputs,'elapsed_seconds':time.monotonic()-start,'controller':controller,
          'environment':{'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},'source_input':'research/yt-maint/initial-controls/baseline-split'}
    meta['files']={file.name:SHA(file.read_bytes())for file in sorted(case.iterdir())}
    (case/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(recipe,mode_name,'natural exit; retained',len(outputs),'outputs',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination',type=Path);p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--frida-module',type=Path,required=True)
    p.add_argument('--dosbox',type=Path,default=Path('/opt/homebrew/bin/dosbox-staging'))
    p.add_argument('--profiles',default=','.join(RECIPES));p.add_argument('--modes',default=','.join(MODES))
    args=p.parse_args();destination=args.destination.absolute();scratch=args.scratch.absolute();dosbox=args.dosbox.absolute()
    assert SHA(dosbox.resolve(strict=True).read_bytes())==HOST_SHA,'unsupported installed DOSBox binary'
    assert args.frida_module.is_file(),'existing Frida module required'
    assert not destination.exists()and not scratch.exists(),'new output and disposable scratch directories required'
    profiles=args.profiles.split(',');modes=args.modes.split(',')
    assert len(set(profiles))==len(profiles)and all(name in RECIPES for name in profiles),'declared recipe selection'
    assert len(set(modes))==len(modes)and all(name in MODES for name in modes),'declared mode selection'
    destination.mkdir(parents=True);scratch.mkdir(parents=True)
    for profile in profiles:
        for mode in modes:capture(destination,scratch,profile,mode,dosbox,args.frida_module)

if __name__=='__main__':main()
