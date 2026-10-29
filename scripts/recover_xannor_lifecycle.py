"""Probe original Xannor lifecycle in fresh disposable DOSBox mounts only."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/dos-validation/evidence'
RECIPE='xannor-lifecycle-isolation-v1'


def scenarios():
    out=[{'name':'hq-held'},
         {'name':'missing-reference','patches':[(1165,93,0)]},
         {'name':'inactive-record','patches':[(4151,85,0)]},
         {'name':'missing-both','patches':[(1165,93,0),(4151,85,0)]},
         {'name':'captured-planet','human':True,'patches':[(4151,73,2),(4151,77,500000),(4151,117,1234)]},
         {'name':'zero-reserves','patches':[(4151,77,0),(4151,117,0)]},
         {'name':'zero-hq','patches':[(1165,81,0)]},
         {'name':'unowned-hq','patches':[(1165,85,0)]},
         {'name':'duplicate-pointer','patches':[(53,105,1114),(54,105,1114)]},
         {'name':'empty-hq-pointer','patches':[(52,105,0)]},
         {'name':'split-hq-pointers','patches':[(52,105,1200),(1251,81,5000),(1251,85,-1)]},
         {'name':'foreign-mobile-pointer','human':True,'patches':[(53,105,100),(151,81,999),(151,85,2)]},
         {'name':'friendly-mobile-pointer','patches':[(53,105,100),(151,81,999),(151,85,-1)]}]
    for score in (100000,999999,1000000,1000500,10000000):
        out.append({'name':f'regen-{score}','human':True,'patches':[(2,109,score)]})
    for owner in (-2,0,1,2):
        out.append({'name':f'reclaim-owner-{owner}','human':True,'patches':[(2,109,10000000),(1165,81,100),(1165,85,owner)]})
    out += [{'name':'reclaim-overwhelming','human':True,'patches':[(2,109,10000000),(1165,81,10000000),(1165,85,2)]},
            {'name':'reclaim-no-score','human':True,'patches':[(1165,81,100),(1165,85,2)]},
            {'name':'missing-both-time-04','time':'04:00:00','patches':[(1165,93,0),(4151,85,0)]},
            {'name':'missing-both-time-08','time':'08:00:00','patches':[(1165,93,0),(4151,85,0)]}]
    out += [
        {'name':'wrong-home-reference','patches':[(1165,93,2)]},
        {'name':'recreated-retained-stocks','patches':[(1165,93,0),(4151,117,0),(4151,129,37),(4151,125,3),(4151,113,5)]},
        {'name':'recreated-stock-reset','patches':[(1165,93,0),(4151,117,0),(4151,57,11),(4151,61,13),(4151,65,17),(4151,69,7),(4151,129,37),(4151,125,3),(4151,113,5)]},
        {'name':'recreated-stock-reset-inactive','patches':[(1165,93,0),(4151,85,0),(4151,117,0),(4151,57,11),(4151,61,13),(4151,65,17),(4151,69,7),(4151,129,37),(4151,125,3),(4151,113,5)]},
        {'name':'positive-home-reserves','patches':[(4151,77,100),(4151,117,1234)]},
        {'name':'zero-hq-next-day','parent':'zero-hq','date':'10/26/2026'},
        {'name':'missing-both-next-day','parent':'missing-both','date':'10/26/2026'},
    ]
    for label,owner,force,planet,score in (
        ('candidate-empty',0,0,0,0),('candidate-human-one',2,1,0,0),
        ('candidate-human-two',2,2,0,0),('candidate-merc-one',-2,1,0,0),
        ('candidate-merc-two',-2,2,0,0),('candidate-xannor-two',-1,2,0,0),
        ('candidate-planet-blocked',0,0,14,0),
        ('candidate-zero-hq-positive-score',0,0,0,1000000),
    ):
        blocked=label in ('candidate-human-two','candidate-merc-two','candidate-planet-blocked')
        out.append({'name':label,'small':True,'human':owner==2 or score>0,
                    'patches':[(72,81,force),(72,85,owner),(72,93,planet)]+([(2,109,score)] if score else []),
                    **({'expect_timeout':True,'timeout':8} if blocked else {})})
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path);parser.add_argument('--only',nargs='+')
    parser.add_argument('--parent-world',type=Path);args=parser.parse_args()
    todo=scenarios()
    if args.only:
        if set(args.only)-{c['name'] for c in todo}:parser.error('unknown case')
        todo=[c for c in todo if c['name'] in args.only]
    dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=False)
    dosbox=shutil.which('dosbox-staging')
    if not dosbox:parser.error('DOSBox Staging not found')
    spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
    source=(SOURCE/'YTDATA.DAT').read_bytes();base=bytearray(source)
    for r in range(2,52):base[(r-1)*137:r*137]=bytes(137);mbf.put(base,r,109,-1)
    for sector in range(1,3001):
        for off in (81,85,93,105,129):mbf.put(base,51+sector,off,0)
    for r in range(3052,4052):
        for off in (89,97):mbf.put(base,r,off,0)
    for r in range(4052,4152):base[(r-1)*137:r*137]=bytes(137)
    for slot,label,owner in ((1,'The Wanderer',0),(2,'Probe Planet',0),(99,'Mercenary Base',-2),(100,'Xannoron',-1)):
        r=4051+slot;at=(r-1)*137;base[at:at+41]=label.encode().ljust(41,b' ')
        for off,v in ((41,298),(73,owner),(77,1),(85,len(label)),(89,0),(117,1)):mbf.put(base,r,off,v)
    for r,o,v in ((2050,93,1),(2051,93,99),(1165,93,100),(1165,81,10000),(1165,85,-1),(1,117,1114),(52,105,1114)):mbf.put(base,r,o,v)
    base=bytes(base);sha=lambda b:hashlib.sha256(b).hexdigest()
    # A structurally consistent 21-sector world keeps all 20 group bookkeeping
    # records plus the revenge pointer inside the sector block. Ports21, planets100.
    small=bytearray(base[:51*137])
    for sector in range(1,22):small.extend(base[(50+sector)*137:(51+sector)*137])
    for port in range(1,22):small.extend(base[(3050+port)*137:(3051+port)*137])
    small.extend(base[4051*137:4151*137])
    for r,o,v in ((1,57,72),(1,61,93),(1,93,193),(1,117,8)):
        mbf.put(small,r,o,v)
    for sector in range(1,22):
        for off in (41,45,49,53,57,61,81,85,93,105,129):mbf.put(small,51+sector,off,0)
        mbf.put(small,51+sector,41,(sector+19)%21+1)
        mbf.put(small,51+sector,45,sector%21+1)
    for r,o,v in ((53,93,1),(54,93,99),(59,93,100),(59,85,-1),(52,105,8)):
        mbf.put(small,r,o,v)
    for sector in range(9,22):
        slot=sector-7;r=93+slot;at=(r-1)*137
        small[at:at+137]=bytes(137);label=('Block '+str(slot)).encode()
        small[at:at+41]=label.ljust(41,b' ')
        for off,v in ((41,298),(73,0),(77,1),(85,len(label)),(89,0),(117,1)):mbf.put(small,r,off,v)
        mbf.put(small,51+sector,93,slot)
    small=bytes(small)
    (dest/'small-baseline.dat.gz').write_bytes(gzip.compress(small,mtime=0))
    (dest/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
    def run(case):
        d=dest/case['name'];d.mkdir()
        for file in SOURCE.iterdir():
            if file.suffix.upper() in ('.DAT','.ASC'):shutil.copy2(file,d/file.name)
        for name in ('YTMAINT.EXE','BRUN30.EXE'):shutil.copy2(ROOT/'archive/dos-original'/name,d/name)
        data=bytearray(small if case.get('small') else base)
        if case.get('parent'):
            parent=args.parent_world or dest/case['parent']/'after.dat.gz'
            data=bytearray(gzip.decompress(parent.read_bytes()))
        if case.get('human'):
            player=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
            data[137:274]=player[137:274]
            for off,v in ((41,297),(45,0),(57,7),(89,0),(109,0),(125,10)):mbf.put(data,2,off,v)
        for r,o,v in case.get('patches',[]):mbf.put(data,r,o,v)
        if case.get('small') and any(r==72 and o==93 and v==0 for r,o,v in case.get('patches',[])):
            data[106*137:107*137]=bytes(137) # Remove the freed candidate's Block14 record too.
        before=bytes(data);(d/'YTDATA.DAT').write_bytes(before)
        date=case.get('date','10/25/2026');clock=case.get('time','00:00:00')
        commands=[f'mount c {d}','c:',f'date {date}',f'time {clock}','date > dosdate.log','time > dostime.log','ytmaint > maint.log','exit']
        timed_out=False
        try:
            with (d/'dosbox.log').open('w') as log:
                subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for command in commands for x in ('-c',command)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=case.get('timeout',45),check=True)
        except subprocess.TimeoutExpired:timed_out=True
        after=(d/'YTDATA.DAT').read_bytes()
        transcript=(d/'MAINT.LOG').read_bytes().decode('cp437').replace('\r\n','\n') if (d/'MAINT.LOG').exists() else ''
        (d/'transcript.txt').write_text(transcript)
        for label,raw in (('before',before),('after',after)):(d/(label+'.dat.gz')).write_bytes(gzip.compress(raw,mtime=0))
        keep={'before.dat.gz','after.dat.gz','transcript.txt','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
        result={**case,'recipe':RECIPE,'source_sha256':sha(source),'baseline_sha256':sha(small if case.get('small') else base),'before_sha256':sha(before),'after_sha256':sha(after),'executable_sha256':sha((d/'YTMAINT.EXE').read_bytes()),'runtime_sha256':sha((d/'BRUN30.EXE').read_bytes()),'date':date,'time':clock,'timed_out':timed_out,'timeout_seconds':case.get('timeout',45),'complete':not timed_out and 'Daily Maintenance Completed OK' in transcript,'files':{name:sha((d/name).read_bytes()) for name in keep if (d/name).exists()}}
        (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        for file in d.iterdir():
            if file.is_file() and file.name not in keep|{'result.json'}:file.unlink()
        print(case['name'],result['complete'],flush=True)
        return result
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,[c for c in todo if not c.get('parent')]))
    for case in todo:
        if case.get('parent'):results.append(run(case))
    (dest/'results.json').write_text(json.dumps({'recipe':RECIPE,'scenarios':results},indent=2)+'\n')
if __name__=='__main__':main()
