"""Exercise original player-combat revenge queue producers in fresh DOS copies."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/surrender-xannor'
RECIPE='xannor-revenge-queue-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()


def scenarios():
    return [dict(name='ordinary-xannor-win',hq=1114,defenders=1,attack=10001),dict(name='xannor-hq-win',hq=100,defenders=1,attack=10001),dict(name='xannor-hq-loss',hq=100,defenders=1000000,attack=1)]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);args=p.parse_args()
    dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
    base=(SOURCE/'before.dat').read_bytes();(dest/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
    def run(case):
        d=dest/case['name'];d.mkdir()
        for f in SOURCE.iterdir():
            if f.suffix.upper()in('.DAT','.ASC','.ANS','.DOC','.DEF'):shutil.copy2(f,d/f.name)
        for name in('YT.EXE','BRUN30.EXE','LOCAL.EXE','XANNORHQ.TXT'):shutil.copy2(ROOT/'archive/dos-original'/name,d/name)
        shutil.copy2(ROOT/'archive/analysis/yt-combat/KEYFEED.COM',d/'KEYFEED.COM')
        b=bytearray(base)
        for r,o,v in[(1,117,case['hq']),(72,105,0),(151,81,case['defenders']),(151,85,-1)]:mbf.put(b,r,o,v)
        before=bytes(b);(d/'YTDATA.DAT').write_bytes(before)
        keys=b'\r~~~~~\r~A;'+str(case['attack']).encode()+b'\r~~~\r~~~Q;Y\r~~~\r'
        (d/'KEYS.TXT').write_bytes(keys)
        cmds=[f'mount c {d}','c:','date 10/24/2026','time 00:00:00','date > dosdate.log','time > dostime.log','keyfeed','local TESTER > game.log','exit']
        timeout=False
        try:
            with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in cmds for v in('-c',c)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=60,check=True)
        except subprocess.TimeoutExpired:timeout=True
        after=(d/'YTDATA.DAT').read_bytes();text=(d/'GAME.LOG').read_bytes().decode('cp437').replace('\r\n','\n')
        (d/'transcript.txt').write_text(text)
        for label,b in [('before',before),('after',after)]: (d/(label+'.dat.gz')).write_bytes(gzip.compress(b,mtime=0))
        keep={'before.dat.gz','after.dat.gz','transcript.txt','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
        result={**case,'recipe':RECIPE,'baseline_sha256':SHA(base),'before_sha256':SHA(before),'after_sha256':SHA(after),'date':'10/24/2026','time':'00:00:00','timed_out':timeout,'complete':not timeout and 'Returning to Yankee Trader Local Logon Program...'in text,'binaries':{n:SHA((d/n).read_bytes())for n in('YT.EXE','BRUN30.EXE','LOCAL.EXE','XANNORHQ.TXT','KEYFEED.COM')},'files':{n:SHA((d/n).read_bytes())for n in sorted(keep)}}
        (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        for f in d.iterdir():
            if f.name not in keep|{'result.json'}and f.is_file():f.unlink()
        print(case['name'],result['complete'],mbf.get(after,72,105),flush=True);return result
    with ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(run,scenarios()))
    (dest/'recipe.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=scenarios()),indent=2)+'\n')
    (dest/'results.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n')

if __name__=='__main__':main()
