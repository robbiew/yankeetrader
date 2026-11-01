"""Capture original broadcast-radio routing and delivery in copied DOS worlds."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
RECIPE='broadcast-radio-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()
GRAPH={1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)


def cases():
    command='C;5;ALL\r~~YT BROADCAST PROBE\r\r~~S\r~~~~6;1'
    return [
      dict(name='broadcast-send',command=command,patches=[]),
      dict(name='broadcast-abort',command=command.replace('~~S','~~A;Y'),patches=[]),
      dict(name='recipient-read',command='\r~~~~C;6;1',patches=[],parent='broadcast-send',actor='ENEMY'),
      dict(name='sender-read',command='\r~~~~C;6;1',patches=[],parent='broadcast-send'),
      dict(name='recipient-again',command='\r~~~~C;6;1',patches=[],parent='recipient-read',actor='ENEMY'),
      dict(name='sender-after-recipient',command='\r~~~~C;6;1',patches=[],parent='recipient-read')]


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
            parent=destination/c['parent']
            if not json.loads((parent/'result.json').read_text())['complete']:raise RuntimeError('refusing an incomplete parent')
            b=bytearray(gzip.decompress((parent/'after.dat.gz').read_bytes()))
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
        if c.get('roster') is not None:
            start=51*137;b[start:start+41]=b'Orion'.ljust(41,b' ')
            b[start+113:start+117]=b'ABCD'
            for offset,value in [(73,5),(77,c['roster'][0])]+list(zip((109,117,121,125),c['roster']+[0]*(4-len(c['roster'])))):mbf.put(b,52,offset,value)
        patches+=c['patches']
        for r,o,v in patches:mbf.put(b,r,o,v)
        before=bytes(b);(d/'YTDATA.DAT').write_bytes(before)
        side={p.name:p.read_bytes()for p in d.iterdir()if p.suffix.upper()in('.DAT','.ASC')and p.name!='YTDATA.DAT'}
        (d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({n:v.hex()for n,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
        tail='\r0\r~Q;Y\r~~' if c.get('port_rescue') else '\rQ;Y\r~~'
        keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+tail*24).encode();(d/'KEYS.TXT').write_bytes(keys)
        commands=[f'mount c {d}','c:','date 10/24/2026','time '+c.get('time','00:00:00'),'date > dosdate.log','time > dostime.log','keyfeed',f"local {c.get('actor','TESTER')} > game.log",'exit']
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
    pending=[c for c in selected if c.get('parent')]
    while pending:
        complete={r['name']for r in results}
        ready=[c for c in pending if c['parent']in complete]
        if not ready:raise RuntimeError('missing or cyclic parent dependency')
        with ThreadPoolExecutor(max_workers=workers)as pool:results.extend(pool.map(run,ready))
        pending=[c for c in pending if c not in ready]
    (destination/'results.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=4);a=p.parse_args();todo=cases()
    if a.only:
        unknown=set(a.only)-{c['name']for c in todo}
        if unknown:p.error('unknown cases: '+str(unknown))
        todo=[c for c in todo if c['name']in a.only]
        if any(c.get('parent')and c['parent']not in a.only for c in todo):p.error('select required parent too')
    capture(a.destination.resolve(),todo,a.workers)
