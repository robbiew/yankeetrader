"""Run original port/planet event controls in new disposable DOSBox mounts only."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'archive/analysis/dos-validation/evidence'
RECIPE = 'plague-civil-war-isolation-v1'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def scenarios():
    out=[]
    def add(name,patches=(),**kw):out.append(dict(name=name,patches=list(patches),**kw))
    def port(stocks,rates=(1000,1000,1000),record=3053):return [(record,o,v)for o,v in zip((49,53,57,61,65,69),list(stocks)+list(rates))]
    def planet(rates=(1000,1000,1000),ground=100,bank=0,record=4053,owner=0):return [(record,o,v)for o,v in zip((45,49,53,77,117,73),list(rates)+[ground,bank,owner])]
    add('quiet')
    for total in (999999,1000000,1000001):add('port-total-'+str(total),port((10,10,10),(total-2,1,1)))
    add('port-cargo-only',port((1000001,0,0),(1,1,1)))
    for rate in (499,500,501,1000,100000):add('port-rate-'+str(rate),port((100,10,10),(rate,1000001,1)))
    for hour in (4,8):add('port-rate-1000-clock-'+str(hour),port((100,10,10),(1000,1000001,1)),time=f'{hour:02}:00:00')
    add('port-earth',port((10,10,10),(1000001,1,1),record=3052))
    add('port-three',port((10,10,10),(1000001,1,1),record=3052)+port((10,10,10),(1000001,1,1))+port((10,10,10),(1000001,1,1),record=3054))
    add('port-mixed-cap',port((10000000,1000,2000),(1000001,100,200)))
    for index,stocks in enumerate(((100,100,100),(300,100,200),(100,300,200),(100,200,300)),1):add('port-selection-'+str(index),port(stocks,(100,100,100))+[(3053,73,-11),(3053,77,22),(3053,81,-33)])
    for prior in (1,3):add('port-zero-after-'+str(prior),port(tuple(10 if i==prior else 0 for i in (1,2,3)),(0,0,0),3052)+port((0,0,0),(0,0,0)))
    add('port-one-pass',port((10,10,10),(1000000,1000000,1000000)))
    add('port-growth',port((100,200,300),(100,200,300))+[(3053,45,297)])
    for ground in (0,1,999999,1000000,1000001,100000000):add('planet-ground-'+str(ground),planet(ground=ground))
    add('planet-rate-boundary',planet((1,1,99998),ground=1000000))
    for hour in (0,4,8):
        add('planet-plague-clock-'+str(hour),planet((100000000,100000000,100000000),ground=0),time=f'{hour:02}:00:00')
        add('planet-civil-clock-'+str(hour),planet(ground=100000000),time=f'{hour:02}:00:00')
        add('planet-both-clock-'+str(hour),planet((100000000,100000000,100000000),ground=100000000),time=f'{hour:02}:00:00')
    for bank in (1,1000000,1000000000):add('planet-civil-bank-'+str(bank),planet(ground=100000000,bank=bank))
    for owner in (0,2,-1,-2):add('planet-owner-'+str(owner),planet((100000000,100000000,100000000),ground=100,bank=12345,owner=owner),human=owner>0)
    add('planet-inactive',planet((100000000,100000000,100000000),ground=100000000)+[(4053,85,0)])
    add('planet-unprotected',planet((100000000,100000000,100000000),ground=100)+[(53,93,0),(59,93,2)])
    add('planet-one-day-rich',planet(ground=100000000,bank=1000000000)+[(4053,41,297)])
    add('planet-stock-cap',planet((100000000,100000000,100000000),ground=100)+[(4053,o,1000000000)for o in (57,61,65)])
    for mode in ('direct','quiet','zero-civil','reverse'):
        first=planet(ground=100000000,bank=1000000000)
        last=planet((100000000,100000000,100000000),ground=100,bank=12345,record=4055)
        patches=first+last+[(55,93,4),(4055,85,11),(4055,41,298)]
        names=[(4055,'Plague Last')]
        if mode in ('quiet','zero-civil'):
            patches+=planet(ground=100 if mode=='quiet' else 100000000,bank=0,record=4054)+[(54,93,3),(4054,85,12),(4054,41,298)]
            names.append((4054,'Middle Probe'))
        if mode=='reverse':patches=planet((100000000,100000000,100000000),ground=100,bank=12345)+planet(ground=100000000,bank=1000000000,record=4055)+[(55,93,4),(4055,85,10),(4055,41,298)];names=[(4055,'Civil Last')]
        add('planet-order-'+mode,patches,names=names)
    add('planet-next-day',parent='planet-civil-bank-1000000000',date='10/26/2026')
    add('planet-same-day',parent='planet-plague-clock-0')
    return out


def baseline():
    spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
    data=bytearray(gzip.decompress((ROOT/'research/yt-xannor-lifecycle/dos/baseline.dat.gz').read_bytes()))
    for r in range(3052,4052):
        for o,v in {45:298,49:10,53:10,57:10,61:1,65:1,69:1,73:-50,77:50,81:-50,89:0,97:0,101:0}.items():mbf.put(data,r,o,v)
    for o,v in {41:298,45:1000,49:1000,53:1000,57:0,61:0,65:0,69:11,73:0,77:100,89:0,113:13,117:0,125:17,129:7}.items():mbf.put(data,4053,o,v)
    mbf.put(data,53,93,2)
    for sector in range(8,3001):
        for off in (41,45,49,53,57,61):mbf.put(data,51+sector,off,0)
    return bytes(data),mbf


def setup(before,case,mbf):
    if not case.get('parent'):
        minutes=int(case.get('time','00:00:00')[:2])*60
        for r in range(3052,4052):mbf.put(before,r,101,minutes)
        for r in range(4052,4152):mbf.put(before,r,89,minutes)
    if case.get('human'):
        template=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()[137:274]
        before[137:274]=template
        for o,v in {41:297,45:0,57:1,85:2,89:0,109:0,125:0}.items():mbf.put(before,2,o,v)
    for r,name in case.get('names',[]):
        before[(r-1)*137:(r-1)*137+41]=name.encode().ljust(41,b' ')
        mbf.put(before,r,85,len(name))
    for r,o,v in case['patches']:mbf.put(before,r,o,v)

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
        if case.get('parent'):
            parent=args.parent_world.resolve().parent if args.parent_world else dest/case['parent']
            for n,h in json.loads((parent/'side-before.json').read_text()).items():(d/n).write_bytes(bytes.fromhex(h))
            for n,r in json.loads((parent/'sidefiles.json').read_text()).items():(d/n).write_bytes(bytes.fromhex(r['hex']))
        setup(before,case,mbf)
        before=bytes(before);(d/'YTDATA.DAT').write_bytes(before)
        initial={f.name:f.read_bytes()for f in d.iterdir()if f.suffix.upper()in('.DAT','.ASC')and f.name!='YTDATA.DAT'}
        (d/'side-before.json').write_text(json.dumps({n:b.hex()for n,b in sorted(initial.items())},indent=2)+'\n')
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
        keep={'before.dat.gz','after.dat.gz','transcript.txt','sidefiles.json','side-before.json','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
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
