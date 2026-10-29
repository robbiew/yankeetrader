"""Run original Xannor planetary controls in new disposable DOSBox mounts only."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'archive/analysis/dos-validation/evidence'
RECIPE = 'xannor-planet-isolation-v1'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def scenarios():
    out=[]
    def add(name,patches=(),**kw):out.append(dict(name=name,patches=list(patches),**kw))
    add('production-large')
    add('no-planet-reference',[(152,93,0)])
    add('zero-moving-force',[(151,81,0)])
    add('inactive-record',[(4053,85,0)])
    for name,owner in [('neutral',0),('mercenary',-2),('xannor',-1),('owner-one',1)]:add(name,[(4053,73,owner)])
    for amount in (1,499,500,999,1000,500000):add('ground-'+str(amount),[(4053,77,amount)])
    for amount in (.25,.5,.75):add('fractional-ground-'+str(amount),[(4053,77,amount)])
    add('zero-rates',[(4053,o,0)for o in(45,49,53)])
    add('zero-rates-ground-held',[(4053,o,0)for o in(45,49,53)]+[(4053,77,500000)])
    for force in (1,449,450,451,500,501):
        add('rate-501-force-'+str(force),[(151,81,force),(4053,45,501),(4053,49,0),(4053,53,0)])
    for force in (1,1000):add('rate-500-force-'+str(force),[(151,81,force)]+[(4053,o,500)for o in(45,49,53)])
    add('mixed-rates',[(151,81,1000),(4053,45,501),(4053,49,1),(4053,53,0)])
    add('single-small-rate',[(4053,45,1),(4053,49,0),(4053,53,0)])
    add('fractional-rates',[(4053,45,.25),(4053,49,.5),(4053,53,.75)])
    add('fractional-rates-no-arrival',[(152,93,0),(4053,45,.25),(4053,49,.5),(4053,53,.75)])
    add('over-cap-ground-held',[(4053,77,500000)]+[(4053,o,v)for o,v in[(57,50000),(61,60000),(65,70000)]])
    add('below-cap',[(4053,57,1),(4053,61,2),(4053,65,3)])
    add('bank-retained',[(4053,117,1234)])
    add('weapons-retained',[(4053,o,0)for o in(45,49,53)]+[(4053,o,100000)for o in(69,113,125,129)])
    add('mines-before-planet',[(152,129,3)])
    add('defense-before-planet',[(152,81,100000),(152,85,2)])
    add('defense-win-then-planet',[(152,81,1),(152,85,2)])
    add('friendly-screen',[(152,81,50),(152,85,-1)])
    add('unowned-screen',[(152,81,50),(152,85,0)])
    for win in (False,True):
        add('later-mines-after-'+('win'if win else'loss'),[(4053,77,0 if win else 500000)]+[(4053,o,0)for o in(45,49,53)]+[(152,41,102),(153,41,1114),(153,45,0),(153,49,0),(153,53,0),(153,57,0),(153,61,0),(153,129,1)])
    for win in(False,True):
        add('ship-after-'+('win'if win else'loss'),[(4053,77,0 if win else 500000)]+[(4053,o,0)for o in(45,49,53)]+[(2,57,101),(2,125,0)])
    add('protected-planet',[(151,41,7),(58,41,1114),(58,45,0),(58,49,0),(58,53,0),(58,57,0),(58,61,0),(58,93,2),(152,93,0)]+[(4053,o,0)for o in(45,49,53)])
    add('origin-planet',[(151,93,2),(152,93,0)])
    for hour in(4,8):
        add('production-clock-'+str(hour),[],time=f'{hour:02}:00:00')
        add('no-arrival-clock-'+str(hour),[(152,93,0)],time=f'{hour:02}:00:00')
    add('zero-rates-no-arrival',[(152,93,0)]+[(4053,o,0)for o in(45,49,53)])
    for ground in(1,500000):add('large-group-ground-'+str(ground),[(151,81,100000),(4053,77,ground)]+[(4053,o,0)for o in(45,49,53)])
    for value in(.25,.5,.75):add('fractional-ground-no-arrival-'+str(value),[(152,93,0),(4053,77,value)])
    for rate in(499,500,501,499.99993896484375):
        add('rate-no-arrival-'+str(rate),[(152,93,0)]+[(4053,o,rate)for o in(45,49,53)])
    add('rate-499-force-1',[(151,81,1)]+[(4053,o,499)for o in(45,49,53)])
    add('rate-adjusted-500-force-1',[(151,81,1)]+[(4053,o,499.99993896484375)for o in(45,49,53)])
    add('warehouse-damage',[(4053,57,10000),(4053,61,20000),(4053,65,30000)])
    add('warehouse-counterfactual',[(152,93,0),(4053,57,10000),(4053,61,20000),(4053,65,30000)])
    add('one-ground-one-attacker',[(151,81,1),(4053,77,1)])
    for arrival in(False,True):
        add('surplus-zero-rates'+(''if arrival else'-no-arrival'),[(4053,o,0)for o in(45,49,53)]+[(4053,57,10000),(4053,61,20000),(4053,65,30000)]+([]if arrival else[(152,93,0)]))
    add('destroy-bank-retained',[(4053,o,0)for o in(45,49,53)]+[(4053,117,1234)])
    add('hidden-ship-after-destruction',[(4053,o,0)for o in(45,49,53)]+[(2,57,101),(2,125,10)])
    add('one-attacker-clock-eight',[(151,81,1)],time='08:00:00')
    add('destroyed-next-day',[],parent='weapons-retained',date='10/26/2026')
    return out


def baseline():
    spec=importlib.util.spec_from_file_location('mbf', ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
    base=bytearray(gzip.decompress((ROOT/'research/yt-xannor-mobile/dos/baseline.dat.gz').read_bytes()))
    for r,o,v in [(152,93,2),(54,105,200),(251,81,10000),(251,85,-1),
                  (4053,45,1000),(4053,49,2000),(4053,53,3000),(4053,57,0),(4053,61,0),(4053,65,0),
                  (4053,73,2),(4053,77,0),(4053,117,0),(4053,69,11),(4053,113,5),(4053,125,3),(4053,129,37)]:mbf.put(base,r,o,v)
    for off in(41,45,49,53,57,61):mbf.put(base,251,off,0)
    return bytes(base),mbf


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
