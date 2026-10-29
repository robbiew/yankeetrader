"""Run original Xannor mobile controls only in fresh disposable DOSBox mounts."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'archive/analysis/dos-validation/evidence'
RECIPE = 'xannor-mobile-isolation-v1'


def scenarios():
    out = [{'name': 'return-empty'}]
    for label, patches in [
        ('mines-origin', [(151,129,3)]),
        ('mines-hop-small', [(152,129,3)]),
        ('mines-hop-large', [(151,81,100000),(152,129,3)]),
        ('mines-hq', [(1165,129,3)]),
        ('defense-merc', [(152,81,50),(152,85,-2)]),
        ('defense-human', [(152,81,50),(152,85,2)]),
        ('defense-human-strong', [(152,81,100000),(152,85,2)]),
        ('defense-xannor-unpointed', [(152,81,50),(152,85,-1)]),
        ('mines-before-defense', [(152,129,3),(152,81,100000),(152,85,2)]),
        ('planet-neutral', [(152,93,2),(4053,73,0),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('planet-human', [(152,93,2),(4053,73,2),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('planet-xannor', [(152,93,2),(4053,73,-1),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('planet-origin', [(151,93,2),(4053,73,0),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('defense-before-planet', [(152,81,100000),(152,85,2),(152,93,2),(4053,73,2),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('planet-zero-ground', [(152,93,2),(4053,73,2),(4053,77,0),(4053,117,0),(4053,129,37)]),
        ('path-protected-transit', [(151,41,7),(58,41,1114),(58,45,0),(58,49,0),(58,53,0),(58,57,0),(58,61,0)]),
        ('path-branch-order', [(151,41,101),(151,45,102),(153,41,1114),(153,45,0),(152,129,3)]),
        ('path-direct-first', [(151,41,1114),(151,45,101),(152,129,3)]),
        ('path-branch-reversed', [(151,41,102),(151,45,101),(153,41,1114),(153,45,0),(152,129,3)]),
        ('path-shorter-second', [(151,41,101),(151,45,102),(152,41,103),(154,41,1114),(154,45,0),(154,49,0),(154,53,0),(154,57,0),(154,61,0),(153,41,1114),(153,45,0),(153,49,0),(153,53,0),(153,57,0),(153,61,0),(152,129,3)]),
        ('protected-mines', [(151,41,7),(58,41,1114),(58,45,0),(58,49,0),(58,53,0),(58,57,0),(58,61,0),(58,129,3)]),
        ('defense-unowned', [(152,81,50),(152,85,0)]),
        ('mines-before-planet', [(152,129,3),(152,93,2),(4053,73,2),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('planet-stops-before-later-mines', [(152,41,102),(153,41,1114),(153,45,0),(153,49,0),(153,53,0),(153,57,0),(153,61,0),(153,129,3),(152,93,2),(4053,73,2),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('protected-planet', [(151,41,7),(58,41,1114),(58,45,0),(58,49,0),(58,53,0),(58,57,0),(58,61,0),(58,93,2),(4053,73,0),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('defense-then-planet', [(152,81,1),(152,85,2),(152,93,2),(4053,73,2),(4053,77,500000),(4053,117,0),(4053,129,37)]),
        ('split-equal', [(1165,81,2)]),
        ('split-above', [(1165,81,3)]),
        ('split-high', [(1165,81,10000),(2,109,1000000),(151,81,100000)]),
        ('split-score-1999', [(2,109,1999)]),
        ('split-score-2000', [(2,109,2000)]),
        ('split-score-2001', [(2,109,2001)]),
        ('battle-500', [(151,81,500),(152,81,500),(152,85,2)]),
        ('battle-5000', [(151,81,5000),(152,81,5000),(152,85,2)]),
        ('battle-5001', [(151,81,5001),(152,81,5001),(152,85,2)]),
    ]:
        out.append({'name':label,'patches':patches})
    for name,score,sector,cloak in [('top-threshold-below',2499999,250,0),('top-threshold-equal',2500000,250,0),('top-hidden',2500000,250,10),('top-protected',2500000,7,0)]:
        out.append({'name':name,'full_groups':True,'patches':[(1165,81,1000000),(2,109,score),(2,57,sector),(2,125,cloak),(2,53,100000000),(2,61,100000000)]})
    for hour in (0,4,8):
        out.append({'name':f'top-cloak-one-{hour:02}','full_groups':True,'time':f'{hour:02}:00:00','patches':[(1165,81,1000000),(2,109,2500000),(2,57,250),(2,125,1),(2,53,100000000),(2,61,100000000)]})
    out.append({'name':'path-unreachable','patches':[(151,41,0)]})
    out.extend([{'name':'preferred-sparse','small_groups':True},{'name':'preferred-no-probe','small_groups':True,'patches':[(72,93,0),(95,85,0)]}])
    out.append({'name':'return-next-day','parent':'return-empty','date':'10/26/2026'})
    return out


def baseline():
    original = gzip.decompress((ROOT/'research/yt-xannor-lifecycle/dos/baseline.dat.gz').read_bytes())
    spec = importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf = importlib.util.module_from_spec(spec); spec.loader.exec_module(mbf)
    data = bytearray(original)
    player = (ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
    data[137:274] = player[137:274]
    for r,o,v in [(2,41,297),(2,45,0),(2,57,7),(2,89,0),(2,109,4000),(2,125,10),
                  (1165,81,1),(53,105,100),(151,81,100),(151,85,-1)]:
        mbf.put(data,r,o,v)
    for sector,to in [(100,101),(101,1114)]:
        for off in (41,45,49,53,57,61):mbf.put(data,51+sector,off,to if off==41 else 0)
    return bytes(data),mbf


def small_baseline(mbf):
    full=gzip.decompress((ROOT/'research/yt-xannor-lifecycle/dos/baseline.dat.gz').read_bytes())
    small=bytearray(full[:51*137]+full[51*137:72*137]+full[3051*137:3072*137]+full[4051*137:4151*137])
    for r,o,v in [(1,57,72),(1,61,93),(1,93,193),(1,117,8)]:mbf.put(small,r,o,v)
    for sector in range(1,22):
        for off in (41,45,49,53,57,61,81,85,93,105,129):mbf.put(small,51+sector,off,0)
        mbf.put(small,51+sector,41,sector%21+1)
        mbf.put(small,51+sector,45,(sector+19)%21+1)
    for r,o,v in [(53,93,1),(54,93,99),(59,93,100),(59,81,10000),(59,85,-1),(52,105,8),(72,93,2),(95,73,-1)]:mbf.put(small,r,o,v)
    for group,sector in enumerate([s for s in range(1,21)if s!=8],2):
        mbf.put(small,51+group,105,sector)
        mbf.put(small,51+sector,81,100);mbf.put(small,51+sector,85,-1)
    return bytes(small)


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
    base,mbf=baseline();small=small_baseline(mbf);sha=lambda b:hashlib.sha256(b).hexdigest()
    (dest/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
    (dest/'small-baseline.dat.gz').write_bytes(gzip.compress(small,mtime=0))
    def run(case):
        d=dest/case['name'];d.mkdir()
        for f in SOURCE.iterdir():
            if f.suffix.upper()in('.DAT','.ASC'):shutil.copy2(f,d/f.name)
        for name in ('YTMAINT.EXE','BRUN30.EXE'):shutil.copy2(ROOT/'archive/dos-original'/name,d/name)
        casebase=small if case.get('small_groups')else base
        before=bytearray(gzip.decompress((args.parent_world or dest/case['parent']/'after.dat.gz').read_bytes()) if case.get('parent') else casebase)
        if case.get('full_groups'):
            for group in range(3,21):
                for r,o,v in [(51+group,105,200+group),(251+group,81,100),(251+group,85,-1)]:mbf.put(before,r,o,v)
        for r,o,v in case.get('patches',[]):mbf.put(before,r,o,v)
        before=bytes(before);(d/'YTDATA.DAT').write_bytes(before)
        date=case.get('date','10/25/2026');clock=case.get('time','00:00:00')
        commands=[f'mount c {d}','c:',f'date {date}',f'time {clock}','date > dosdate.log','time > dostime.log','ytmaint > maint.log','exit']
        timeout=False
        try:
            with (d/'dosbox.log').open('w')as log:
                subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for command in commands for x in ('-c',command)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=case.get('timeout',45),check=True)
        except subprocess.TimeoutExpired:timeout=True
        after=(d/'YTDATA.DAT').read_bytes()
        text=(d/'MAINT.LOG').read_bytes().decode('cp437').replace('\r\n','\n')if(d/'MAINT.LOG').exists()else''
        (d/'transcript.txt').write_text(text)
        for label,raw in [('before',before),('after',after)]:
            (d/(label+'.dat.gz')).write_bytes(gzip.compress(raw,mtime=0))
        keep={'before.dat.gz','after.dat.gz','transcript.txt','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
        result={**case,'recipe':RECIPE,'baseline_sha256':sha(casebase),'before_sha256':sha(before),'after_sha256':sha(after),'executable_sha256':sha((d/'YTMAINT.EXE').read_bytes()),'runtime_sha256':sha((d/'BRUN30.EXE').read_bytes()),'date':date,'time':clock,'timed_out':timeout,'timeout_seconds':case.get('timeout',45),'complete':not timeout and 'Daily Maintenance Completed OK'in text,'files':{n:sha((d/n).read_bytes())for n in sorted(keep)if(d/n).exists()}}
        (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        for f in d.iterdir():
            if f.name not in keep|{'result.json'}and f.is_file():f.unlink()
        print(case['name'],result['complete'],flush=True)
        return result
    with ThreadPoolExecutor(max_workers=4)as pool:results=list(pool.map(run,[c for c in todo if not c.get('parent')]))
    for case in todo:
        if case.get('parent'):results.append(run(case))
    (dest/'results.json').write_text(json.dumps({'recipe':RECIPE,'scenarios':results},indent=2)+'\n')

if __name__=='__main__':main()
