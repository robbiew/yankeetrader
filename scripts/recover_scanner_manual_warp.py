"""Capture scanner purchase/queue and manual-warp integration in disposable DOS worlds."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
RECIPE='scanner-manual-warp-integration-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()
GRAPH={100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)


def cases():
    out=[]
    def add(name,command,patches=(),**kw):out.append(dict(name=name,command=command,patches=list(patches),**kw))
    shop=[(2,57,1),(52,65,1)]
    for label,cash in [('exact',250000),('below',249999),('above',250001)]:add('shop-'+label,'P;5\r~~0',shop+[(2,81,cash)])
    add('shop-repeat','P;5;5\r~~0',shop+[(2,81,500000)])
    add('shop-installed-poor','P;5\r~~0',shop+[(2,81,0),(2,93,-1)])
    add('shop-leave','P;0',shop+[(2,81,250000)])
    add('shop-blank','P;\r~~0',shop+[(2,81,250000)])
    add('shop-reconnect','P;5\r~~0',parent='shop-exact')
    add('shop-installed-use','M;101\r~~N',[(2,57,100),(152,129,1)],parent='shop-exact')
    for owner,label in [(-1,'xannor'),(-2,'mercenary'),(3,'human')]:add('scanner-'+label,'M;101\r~~N',[(2,93,-1),(152,81,100),(152,85,owner)])
    add('scanner-combined','M;101\r~~N',[(2,93,-1),(152,81,100),(152,85,3),(152,129,10)])
    add('scanner-autopilot-first-yes','C;3;110;Y\r~~Y',[(2,93,-1),(152,129,1)])
    add('scanner-autopilot-second-no','C;3;110;Y\r~~N',[(2,93,-1),(158,129,1)])
    add('scanner-autopilot-second-yes','C;3;110;Y\r~~Y',[(2,93,-1),(158,129,1)])
    add('scanner-stacked-no-fresh-yes','M;101;N\r~~Y',[(2,93,-1),(152,129,1)])
    add('scanner-decline-then-warp','M;101\r~~N\r~~W;Y',[(2,93,-1),(152,129,1)])
    add('scanner-invalid-nonadjacent','M;110',[(2,93,-1),(161,129,10)])
    for flag in (1,-2):add('scanner-flag-'+str(flag),'M;101\r~~N',[(2,93,flag),(152,129,1)])
    small=[(1,57,53),(1,61,53),(1,93,53),(2,57,1),(3,57,1),(3,125,1),(2,93,-1),(53,129,10),(53,81,100),(53,85,3)]
    add('scanner-disruption-combined','M;2\r~~N',small,small=True)
    add('warp-clear','W;Y')
    add('warp-meltdown','W;Y',time='02:00:00')
    # At the same clock these distant destination patches preserve initial RNG.
    for label,patch in [('mines',[(111,129,3)]),('fighters',[(111,81,100),(111,85,-1)]),('both',[(111,129,3),(111,81,100),(111,85,-1)]),('own',[(111,81,100),(111,85,2)])]:add('warp-landing-'+label,'W;Y',patch)
    add('warp-installed-mines','W;Y',[(2,93,-1),(111,129,1)])
    add('warp-installed-fighters','W;Y',[(2,93,-1),(111,81,100),(111,85,-1)])
    add('warp-meltdown-mines','W;Y',[(2,93,-1),(270,129,1)],time='02:00:00')
    add('warp-avoid-destination','C;7;1;60;1;W;Y')
    add('warp-empty-exits','W;Y',[(111,o,0)for o in range(41,65,4)])
    add('warp-avoided-landing','C;7;1;881;1;W;Y')
    add('warp-same-sector','W;Y',[(2,57,2665)])
    add('warp-current-sector','W;Y',[(2,57,60)])
    add('warp-from-earth','W;Y',[(2,57,1)])
    add('warp-one-turn','W;Y',[(2,49,1)])
    add('warp-zero-turns','W;Y',[(2,49,0)])
    add('warp-reconnect-meltdown','I',parent='warp-meltdown')
    add('warp-repeat-same-day','W;Y',parent='warp-clear')
    return out


def capture(destination,selected,workers=3):
    destination.mkdir(parents=True,exist_ok=False)
    base=(SOURCE/'YTDATA.DAT').read_bytes();(destination/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
    (destination/'recipe.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=selected),indent=2)+'\n')
    def run(c):
        d=destination/c['name'];d.mkdir()
        for p in SOURCE.iterdir():
            if p.suffix.upper()in('.DAT','.ASC','.ANS','.DOC','.DEF'):shutil.copy2(p,d/p.name)
        for name in('YT.EXE','BRUN30.EXE','LOCAL.EXE'):shutil.copy2(ROOT/'archive/dos-original'/name,d/name)
        shutil.copy2(ROOT/'archive/analysis/yt-combat/KEYFEED.COM',d/'KEYFEED.COM')
        if c.get('parent'):
            parent=destination/c['parent'];b=bytearray(gzip.decompress((parent/'after.dat.gz').read_bytes()))
            for name,value in json.loads(gzip.decompress((parent/'sidefiles.json.gz').read_bytes())).items():(d/name).write_bytes(bytes.fromhex(value['hex']))
            patches=[]
        else:
            b=bytearray(base)
            graph={1:[2],2:[1]}if c.get('small')else GRAPH
            for sector,warps in graph.items():
                start=(51+sector-1)*137;b[start:start+137]=bytes(137)
                for o,v in zip(range(41,65,4),warps):mbf.put(b,51+sector,o,v)
            patches=[(2,o,v)for o,v in {45:0,49:500,57:100,89:0,93:0,105:0,125:0}.items()]
            patches += [(3,o,v)for o,v in {45:0,57:103,61:42,53:7,89:0,125:0}.items()]
            patches += [(152,65,2),(3053,93,101),(153,93,2),(4053,73,0),(4053,77,12)]
        patches+=c['patches']
        for r,o,v in patches:mbf.put(b,r,o,v)
        before=bytes(b);(d/'YTDATA.DAT').write_bytes(before)
        side={p.name:p.read_bytes()for p in d.iterdir()if p.suffix.upper()in('.DAT','.ASC')and p.name!='YTDATA.DAT'}
        (d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({n:v.hex()for n,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
        keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+'\rQ;Y\r~~'*24).encode();(d/'KEYS.TXT').write_bytes(keys)
        commands=[f'mount c {d}','c:','date 10/24/2026','time '+c.get('time','00:00:00'),'date > dosdate.log','time > dostime.log','keyfeed','local TESTER > game.log','exit']
        timed_out=False
        try:
            with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for cmd in commands for x in('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=150,check=True)
        except subprocess.TimeoutExpired:timed_out=True
        after=(d/'YTDATA.DAT').read_bytes();text=(d/'GAME.LOG').read_bytes().decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text)
        for label,payload in [('before',before),('after',after)]:(d/(label+'.dat.gz')).write_bytes(gzip.compress(payload,mtime=0))
        final={name:dict(before_sha256=SHA(value),after_sha256=SHA((d/name).read_bytes()),hex=(d/name).read_bytes().hex())for name,value in side.items()}
        (d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps(final,indent=2)+'\n').encode(),mtime=0))
        keep={'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
        result={**c,'recipe':RECIPE,'baseline_sha256':SHA(base),'applied_patches':patches,'date':'10/24/2026','time':c.get('time','00:00:00'),'timeout_seconds':150,'timed_out':timed_out,'complete':not timed_out and 'Returning to Yankee Trader Local Logon Program...'in text,'binaries':{n:SHA((d/n).read_bytes())for n in('YT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')},'files':{n:SHA((d/n).read_bytes())for n in sorted(keep)}}
        (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        for p in d.iterdir():
            if p.is_file()and p.name not in keep|{'result.json'}:p.unlink()
        print(c['name'],result['complete'],'sector',mbf.get(before,2,57),'->',mbf.get(after,2,57),'turns',mbf.get(before,2,49),'->',mbf.get(after,2,49),'cash',mbf.get(after,2,81),'scanner',mbf.get(after,2,93),flush=True)
        return result
    with ThreadPoolExecutor(max_workers=workers)as pool:results=list(pool.map(run,[c for c in selected if not c.get('parent')]))
    for c in selected:
        if c.get('parent'):results.append(run(c))
    (destination/'results.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=3);a=p.parse_args();todo=cases()
    if a.only:
        unknown=set(a.only)-{c['name']for c in todo}
        if unknown:p.error('unknown cases: '+str(unknown))
        todo=[c for c in todo if c['name']in a.only]
        if any(c.get('parent')and c['parent']not in a.only for c in todo):p.error('select each required parent too')
    capture(a.destination.resolve(),todo,a.workers)
