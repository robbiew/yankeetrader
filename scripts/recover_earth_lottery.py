"""Recover Earth's paid Pick-6 lottery using isolated copies of original DOS worlds."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
RECIPE='earth-paid-lottery-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()
GRAPH={1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)


def cases():
    out=[]
    def add(name,command,patches=(),**kw):out.append(dict(name=name,command=command,patches=list(patches),port_rescue=True,**kw))
    def ticket(name,number='123456',patches=(),**kw):add(name,'P;4\r~~'+number+'\r~~~~\r~0',patches,**kw)
    add('control-earth','P;0')
    for digit in range(10):ticket('digit-'+str(digit),str(digit)*6)
    ticket('ticket-baseline')
    for label,cash in [('below',4),('exact',5),('above',6)]:ticket('cash-'+label,'000000',[(2,81,cash)])
    ticket('limit-zero','000000',[(1,101,0)])
    ticket('limit-reached','000000',[(2,105,5)])
    ticket('limit-above','000000',[(2,105,6)])
    ticket('limit-negative','000000',[(1,101,-1)])
    for label,number in [('blank',''),('short','12345'),('long','1234567'),('letter','12A456'),('sign','-12345'),('point','12.456'),('space','12 456')]:
        ticket('input-'+label,number+'\r~~000000')
    add('repeat-limit-two','P;4\r~~000000\r~~~~~~~~~~~~4\r~~000000\r~~~~~~~~~~~~4\r~~0',[(1,101,2)])
    add('same-day-reconnect','P;4\r~~0',parent='repeat-limit-two')
    add('next-day-reset','I',parent='repeat-limit-two',date='10/25/2026')
    add('next-day-play','P;4\r~~000000\r~~~~\r~0',parent='next-day-reset',date='10/25/2026')
    ticket('large-loss-24','000000',[(2,81,16777216)])
    ticket('large-loss-27','000000',[(2,81,134217728)])
    ticket('large-loss-40','000000',[(2,81,1099511627776)])
    for count,number in enumerate(['000000','100000','120000','126000','126700','126780','126788']):
        ticket('tier-'+str(count),number)
    ticket('jackpot-permuted','887621')
    ticket('duplicates-limited','888888')
    ticket('jackpot-poor','126788',[(2,81,5)])
    for label,cash in [('24',16777216),('27',134217728),('40',1099511627776)]:
        ticket('large-win-'+label,'126788',[(2,81,cash)])
    ticket('limit-nine-last','000000',[(1,101,9),(2,105,8)])
    ticket('limit-nine-reached','000000',[(1,101,9),(2,105,9)])
    ticket('limit-high','000000',[(1,101,10)])
    return out


def capture(destination,selected,workers=4):
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
            patches=[(2,o,v)for o,v in {45:0,49:500,57:1,89:0,93:0,105:0,125:0}.items()]
            patches += [(3,o,v)for o,v in {45:0,57:2,61:42,53:7,89:0,125:1}.items()]
            patches += [(52,65,1),(152,65,2),(3053,93,101),(153,93,2),(4053,73,0),(4053,77,12)]
        patches+=c['patches']
        for r,o,v in patches:mbf.put(b,r,o,v)
        before=bytes(b);(d/'YTDATA.DAT').write_bytes(before)
        side={p.name:p.read_bytes()for p in d.iterdir()if p.suffix.upper()in('.DAT','.ASC')and p.name!='YTDATA.DAT'}
        (d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({n:v.hex()for n,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
        tail='\r0\r~Q;Y\r~~' if c.get('port_rescue') else '\rQ;Y\r~~'
        keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+tail*24).encode();(d/'KEYS.TXT').write_bytes(keys)
        commands=[f'mount c {d}','c:','date '+c.get('date','10/24/2026'),'time '+c.get('time','00:00:00'),'date > dosdate.log','time > dostime.log','keyfeed','local TESTER > game.log','exit']
        timed_out=False
        try:
            with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for cmd in commands for x in('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=150,check=True)
        except subprocess.TimeoutExpired:timed_out=True
        after=(d/'YTDATA.DAT').read_bytes();text=(d/'GAME.LOG').read_bytes().decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text)
        for label,payload in [('before',before),('after',after)]:(d/(label+'.dat.gz')).write_bytes(gzip.compress(payload,mtime=0))
        final={name:dict(before_sha256=SHA(value),after_sha256=SHA((d/name).read_bytes()),hex=(d/name).read_bytes().hex())for name,value in side.items()}
        (d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps(final,indent=2)+'\n').encode(),mtime=0))
        keep={'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
        result={**c,'recipe':RECIPE,'baseline_sha256':SHA(base),'applied_patches':patches,'date':c.get('date','10/24/2026'),'time':c.get('time','00:00:00'),'timeout_seconds':150,'timed_out':timed_out,'complete':not timed_out and 'Returning to Yankee Trader Local Logon Program...'in text,'binaries':{n:SHA((d/n).read_bytes())for n in('YT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')},'files':{n:SHA((d/n).read_bytes())for n in sorted(keep)}}
        (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        for p in d.iterdir():
            if p.is_file()and p.name not in keep|{'result.json'}:p.unlink()
        print(c['name'],result['complete'],'sector',mbf.get(before,2,57),'->',mbf.get(after,2,57),'turns',mbf.get(before,2,49),'->',mbf.get(after,2,49),'cash',mbf.get(after,2,81),'plays',mbf.get(after,2,105),flush=True)
        return result
    with ThreadPoolExecutor(max_workers=workers)as pool:results=list(pool.map(run,[c for c in selected if not c.get('parent')]))
    for c in selected:
        if c.get('parent'):results.append(run(c))
    (destination/'results.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=5);a=p.parse_args();todo=cases()
    if a.only:
        unknown=set(a.only)-{c['name']for c in todo}
        if unknown:p.error('unknown cases: '+str(unknown))
        todo=[c for c in todo if c['name']in a.only]
        if any(c.get('parent')and c['parent']not in a.only for c in todo):p.error('select required parent too')
    capture(a.destination.resolve(),todo,a.workers)
