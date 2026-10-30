"""Run original Xannor revenge and cloak controls in new disposable DOSBox mounts only."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'archive/analysis/dos-validation/evidence'
RECIPE = 'xannor-revenge-isolation-v1'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def scenarios():
    out=[]
    def add(name,patches=(),**kw):out.append(dict(name=name,patches=list(patches),**kw))
    add('ordinary')
    add('revenge-active',[(72,105,2)])
    add('revenge-hidden',[(72,105,2),(2,125,10)])
    add('revenge-negative',[(72,105,-1)])
    for sector in(0,7,8):add('revenge-sector-'+str(sector),[(72,105,2),(2,57,sector)])
    add('revenge-dead-positive',[(72,105,2),(2,45,1)])
    add('revenge-unnamed-live',[(72,105,2),(2,85,0)])
    add('revenge-unnamed-protected',[(72,105,2),(2,85,0),(2,57,7)])
    add('revenge-unnamed-zero',[(72,105,2),(2,85,0),(2,57,0)])
    add('revenge-inactive-slot-three',[(72,105,3),(3,57,260)])
    for label,score,sector,cloak in [('top-other',2500000,260,0),('top-protected',2500000,7,0),('top-hidden',2500000,260,10),('top-below',2499999,260,0),('top-dead',2500000,260,0)]:
        add('revenge-'+label,[(72,105,2),(2,125,10),(3,109,score),(3,57,sector),(3,125,cloak)]+([(3,45,1)]if label=='top-dead'else[]),second=True)
    add('revenge-hq-override',[(72,105,2),(2,125,10),(1165,81,1),(2,109,4000)])
    add('top-tie',[(2,109,2500000),(3,109,2500000),(3,57,260),(3,125,0)],second=True)
    add('top-unnamed',[(2,109,4000),(3,109,2500000),(3,57,260),(3,125,0),(3,85,0)],second=True)
    add('top-no-score',[(2,109,0)])
    for cloak in(0,.025,.05,.1,1,10,-1):
        for revenge in(False,True):
            add(('revenge'if revenge else'ordinary')+'-cloak-'+str(cloak),[(2,125,cloak),(72,105,2 if revenge else 0)])
    for hour in(4,8):
        add('revenge-top-other-clock-'+str(hour),[(72,105,2),(2,125,10),(3,109,2500000),(3,57,260),(3,125,0)],second=True,time=f'{hour:02}:00:00')
    # Routes only in these controls: arrival need not imply a ship attack.
    for cloak in(0,10):
        add('revenge-arrival-cloak-'+str(cloak),[(72,105,2),(2,125,cloak)],arrival=True)
    for force,owner in[(1,0),(2,0),(2,-1),(2,-2),(2,2)]:
        add('candidate-force-'+str(force)+'-owner-'+str(owner),candidate_screen=[force,owner])
    add('candidate-planets',candidate_planets=True)
    add('candidate-planet-one',candidate_planets=1)
    for cloak in(1,10):
        for hour in(0,4,8):add('hunt-cloak-'+str(cloak)+'-clock-'+str(hour),[(2,109,2500000),(2,125,cloak)],time=f'{hour:02}:00:00')
    add('revenge-next-day',[],parent='revenge-active',date='10/26/2026')
    return out


def baseline():
    spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
    data=bytearray(gzip.decompress((ROOT/'research/yt-xannor-mobile/dos/baseline.dat.gz').read_bytes()))
    # Missing paths isolate target choices from casualties, shared pursuit writes,
    # protected-sector reactivation and production/destruction.
    for sector in range(8,3001):
        for off in(41,45,49,53,57,61):mbf.put(data,51+sector,off,0)
    for r,o,v in[(2,57,250),(2,109,4000),(2,125,0),(2,53,100000000),(2,61,100000000),(1165,81,1000000),(72,105,0)]:mbf.put(data,r,o,v)
    for group in range(3,21):
        for r,o,v in[(51+group,105,200+group),(251+group,81,100),(251+group,85,-1)]:mbf.put(data,r,o,v)
    return bytes(data),mbf


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--parent-world',type=Path)
    args=p.parse_args();todo=scenarios()
    if args.only:
        if set(args.only)-{c['name']for c in todo}:p.error('unknown case')
        todo=[c for c in todo if c['name']in args.only]
    dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=False)
    dosbox=shutil.which('dosbox-staging')
    if not dosbox:p.error('DOSBox Staging not found')
    base,mbf=baseline();(dest/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
    def run(case):
        d=dest/case['name'];d.mkdir()
        for f in SOURCE.iterdir():
            if f.suffix.upper() in ('.DAT','.ASC'):shutil.copy2(f,d/f.name)
        for name in ('YTMAINT.EXE','BRUN30.EXE'):shutil.copy2(ROOT/'archive/dos-original'/name,d/name)
        before=bytearray(gzip.decompress((args.parent_world or dest/case['parent']/'after.dat.gz').read_bytes())if case.get('parent')else base)
        if case.get('second'):
            before[274:411]=before[137:274]
            before[274:315]=b'R'.ljust(41,b' ')
        if case.get('arrival'):
            for origin in [100]+list(range(203,221)):
                mbf.put(before,51+origin,41,250)
        if case.get('candidate_screen'):
            force,owner=case['candidate_screen']
            for sector in range(8,3001):
                if mbf.get(before,51+sector,81)==0 and mbf.get(before,51+sector,93)==0:
                    mbf.put(before,51+sector,81,force);mbf.put(before,51+sector,85,owner)
        if case.get('candidate_planets'):
            for sector in range(8,3001):
                if mbf.get(before,51+sector,93)==0:mbf.put(before,51+sector,93,2 if case['candidate_planets'] is True else case['candidate_planets'])
        for r,o,v in case['patches']:mbf.put(before,r,o,v)
        before=bytes(before);(d/'YTDATA.DAT').write_bytes(before)
        # Preserve private delivery and public journal bytes alongside world state.
        side_before={f.name:SHA(f.read_bytes())for f in d.iterdir()if f.suffix.upper()in('.DAT','.ASC')and f.name!='YTDATA.DAT'}
        date=case.get('date','10/25/2026');clock=case.get('time','00:00:00')
        commands=[f'mount c {d}','c:',f'date {date}',f'time {clock}','date > dosdate.log','time > dostime.log','ytmaint > maint.log','exit']
        timeout=False
        try:
            with(d/'dosbox.log').open('w')as log:
                subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for command in commands for x in('-c',command)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=45,check=True)
        except subprocess.TimeoutExpired:timeout=True
        after=(d/'YTDATA.DAT').read_bytes()
        text=(d/'MAINT.LOG').read_bytes().decode('cp437').replace('\r\n','\n')if(d/'MAINT.LOG').exists()else''
        (d/'transcript.txt').write_text(text)
        for label,raw in [('before',before),('after',after)]: (d/(label+'.dat.gz')).write_bytes(gzip.compress(raw,mtime=0))
        changed={f.name:f.read_bytes()for f in d.iterdir()if f.suffix.upper()in('.DAT','.ASC')and f.name!='YTDATA.DAT'and SHA(f.read_bytes())!=side_before.get(f.name)}
        (d/'sidefiles.json').write_text(json.dumps({name:{'before_sha256':side_before.get(name),'after_sha256':SHA(raw),'hex':raw.hex()}for name,raw in sorted(changed.items())},indent=2)+'\n')
        keep={'before.dat.gz','after.dat.gz','transcript.txt','sidefiles.json','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
        result={**case,'recipe':RECIPE,'baseline_sha256':SHA(base),'before_sha256':SHA(before),'after_sha256':SHA(after),'executable_sha256':SHA((d/'YTMAINT.EXE').read_bytes()),'runtime_sha256':SHA((d/'BRUN30.EXE').read_bytes()),'date':date,'time':clock,'timed_out':timeout,'timeout_seconds':45,'complete':not timeout and 'Daily Maintenance Completed OK'in text,'files':{n:SHA((d/n).read_bytes())for n in sorted(keep)if(d/n).exists()}}
        (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        for f in d.iterdir():
            if f.name not in keep|{'result.json'}and f.is_file():f.unlink()
        print(case['name'],result['complete'],flush=True);return result
    with ThreadPoolExecutor(max_workers=4)as pool: results=list(pool.map(run,[c for c in todo if not c.get('parent')]))
    for case in todo:
        if case.get('parent'):results.append(run(case))
    (dest/'recipe.json').write_text(json.dumps({'recipe':RECIPE,'scenarios':todo},indent=2)+'\n')
    (dest/'results.json').write_text(json.dumps({'recipe':RECIPE,'scenarios':results},indent=2)+'\n')

if __name__=='__main__':main()
