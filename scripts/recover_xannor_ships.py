"""Run original Xannor ship controls in new disposable DOSBox mounts only."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'archive/analysis/dos-validation/evidence'
RECIPE = 'xannor-ship-isolation-v1'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def scenarios():
    cases = []
    def add(name, patches=(), **kw):
        cases.append(dict(name=name, patches=list(patches), **kw))
    add('strong-ship')
    add('no-ship', [(2,57,7)])
    add('origin-ship', [(2,57,100)])
    add('hq-ship', [(2,57,1114)])
    for name,f,s,g in [('fighters-only',1000,0,100),('shields-only',0,10000,100),
                       ('unarmed',0,0,100),('weak-ship',1,1,100),

                       ('fighters-499',499,0,500),('fighters-500',500,0,500),
                       ('fighters-5000',5000,0,5000),('fighters-5001',5001,0,5001),
                       ('shields-499',0,499,500),('shields-500',0,500,500),
                       ('shields-5000',0,5000,5000),('shields-5001',0,5001,5001),
                       ('staged-5000',5000,5000,10000)]:
        add(name, [(2,61,f),(2,53,s),(151,81,g)])
    for hour in (0,4,8,12,16,20):
        add(f'cloak-one-{hour:02}',[(2,125,1)],time=f'{hour:02}:00:00')
    add('cloak-diagnostic-hidden',[(2,125,10)])
    for value in (.33,.66):add('cloak-'+str(value),[(2,125,value)])
    add('no-missiles',[(2,97,0)])
    add('many-missiles',[(2,97,100000)])
    for marker in (2,3,-1):add(f'dead-{marker}',[(2,45,marker)])
    add('mines-before-ship',[(152,129,1),(151,81,10000)])
    add('defense-before-ship',[(152,81,100000),(152,85,2)])
    add('mines-after-win',[(2,61,0),(2,53,0),(153,129,1),(152,41,102),(153,41,1114),(153,45,0)])
    add('mines-after-loss',[(153,129,1),(152,41,102),(153,41,1114),(153,45,0)])
    add('two-ships',[],second=True)
    add('two-ships-first-dead',[(2,45,3)],second=True)
    add('two-ships-first-unarmed',[(2,61,0),(2,53,0)],second=True)
    add('kill-assets',[(2,61,0),(2,53,0),(3052,97,2),(3052,89,777),(3052,101,3),(2,117,1),(351,81,37),(351,85,2),(351,41,301),(351,45,0),(351,49,0),(351,53,0),(351,57,0),(351,61,0),(352,41,300),(352,45,0),(352,49,0),(352,53,0),(352,57,0),(352,61,0),(4053,73,2)])
    add('kill-team-captain',[(2,61,0),(2,53,0),(2,89,1),(3,89,1),(3,57,7),(52,73,5),(52,77,2),(52,109,2),(52,117,3),(52,121,0),(52,125,0)],second=True)
    add('two-unarmed',[(2,61,0),(2,53,0),(3,61,0),(3,53,0)],second=True)
    add('strong-next-day',[],parent='strong-ship',date='10/26/2026')
    return cases


def baseline():
    spec=importlib.util.spec_from_file_location('mbf', ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
    base=bytearray(gzip.decompress((ROOT/'research/yt-xannor-mobile/dos/baseline.dat.gz').read_bytes()))
    for r,o,v in [(2,57,101),(2,125,0),(2,81,12345),(2,129,5)]:mbf.put(base,r,o,v)
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
