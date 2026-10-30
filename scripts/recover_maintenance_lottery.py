"""Run original lottery and inactivity controls in new disposable DOSBox mounts only."""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'archive/analysis/dos-validation/evidence'
RECIPE = 'maintenance-lottery-isolation-v1'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def scenarios():
    out=[]
    def add(name,patches=(),**kw):out.append(dict(name=name,patches=list(patches),**kw))
    for hour in (0,4,8):add('lottery-all-clock-'+str(hour),all_players=True,time=f'{hour:02}:00:00')
    add('lottery-dirty-free-slots',all_players=True,dirty_slots=True)
    add('lottery-all-dead-recent',all_players=True,player_death=True)
    add('lottery-all-dead-old',all_players=True,player_delete=True)
    add('lottery-empty-players',empty_players=True)
    add('lottery-full-planets',all_players=True,full_planets=True)
    add('lottery-cloaked-players',all_players=True,cloaked_players=True)
    add('lottery-union-only',all_players=True,union_only=True)
    add('lottery-selected-player-empty',[(12,85,0)],all_players=True)
    add('lottery-selected-sector-occupied',[(2216,93,2)],all_players=True)
    add('lottery-selected-sector-mined',[(2216,129,5)],all_players=True)
    add('lottery-selected-sector-xannor',[(2216,81,1),(2216,85,-1)],all_players=True)
    add('lottery-selected-slot-occupied',[(4096,85,8),(4096,41,298),(4096,77,1)],all_players=True)
    add('lottery-same-day',[],parent='lottery-dirty-free-slots')
    add('inactive-deleted-next-day',[],cleanup=True,parent='inactive-age-14-death-1',date='10/26/2026')
    add('inactive-port-live',[(2,41,284),(2,45,0),(3053,97,2),(3053,89,9),(3053,101,0)],cleanup=True)
    add('inactive-port-deleted',[(2,41,284),(2,45,1),(3053,97,2),(3053,89,9),(3053,101,0)],cleanup=True)
    add('lottery-next-day',[],parent='lottery-dirty-free-slots',date='10/26/2026')
    add('inactive-year-end',[(2,41,352),(2,45,1),(3,41,365)],cleanup=True,date='12/31/2026')
    add('inactive-year-start',[],cleanup=True,parent='inactive-year-end',date='01/01/2027')
    for age in (13,14,15):
        for dead in (0,1,-1):add('inactive-age-'+str(age)+'-death-'+str(dead),[(2,41,298-age),(2,45,dead)],cleanup=True)
    for cloak in (.01,.05,.1,-1):add('inactive-cloak-'+str(cloak),[(2,41,284),(2,45,1),(2,125,cloak)],cleanup=True)
    add('inactive-unnamed',[(2,41,284),(2,45,1),(2,85,0)],cleanup=True)
    for delay in (0,-1,30):add('inactive-delay-'+str(delay),[(1,77,delay),(2,41,298),(2,45,1)],cleanup=True)
    add('inactive-rich-planet',[(2,41,284),(2,45,1),(4053,117,1000000),(4053,41,297)],cleanup=True)
    add('inactive-expiry-next-day',[],cleanup=True,parent='inactive-cloak-0.01',date='10/26/2026')
    return out


def baseline():
    spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
    data=bytearray(gzip.decompress((ROOT/'research/yt-xannor-lifecycle/dos/baseline.dat.gz').read_bytes()))
    template=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()[137:274]
    data[137:274]=template
    for o,v in {41:297,45:0,57:7,85:2,89:0,105:0,109:0,125:0}.items():mbf.put(data,2,o,v)
    # Remove non-Union travel. Both factions remain at their extant homes.
    for sector in range(8,3001):
        for off in (41,45,49,53,57,61):mbf.put(data,51+sector,off,0)
    return bytes(data),mbf


def setup(before,case,mbf):
    if case.get('all_players'):
        template=bytes(before[137:274])
        for r in range(2,52):
            before[(r-1)*137:r*137]=template
            alias=('P'+str(r)+' ').encode();before[(r-1)*137:(r-1)*137+41]=alias.ljust(41,b' ')
            mbf.put(before,r,85,len(alias))
    if case.get('empty_players'):
        for r in range(2,52):mbf.put(before,r,85,0)
    for r in range(2,52):
        if case.get('player_death'):mbf.put(before,r,45,1)
        if case.get('player_delete'):mbf.put(before,r,45,1);mbf.put(before,r,41,284)
        if case.get('cloaked_players'):mbf.put(before,r,125,10)
    for r in range(4054,4150):
        if case.get('dirty_slots'):
            for off,v in {41:111,89:222,57:11,61:12,65:13,69:3,125:7,129:37,113:5,117:55}.items():mbf.put(before,r,off,v)
        if case.get('full_planets'):
            before[(r-1)*137:(r-1)*137+41]=b'Occupied'.ljust(41,b' ')
            for off,v in {41:298,85:8,77:1}.items():mbf.put(before,r,off,v)
    if case.get('union_only'):
        for sector in range(8,3001):
            if mbf.get(before,51+sector,93)==0:mbf.put(before,51+sector,93,2)
    if case.get('cleanup') and not case.get('parent'):
        template=bytes(before[137:274]);before[274:411]=template;before[274:315]=b'R '.ljust(41,b' ')
        for r,o,v in [(2,89,1),(52,77,2),(52,109,2),(52,117,3),(52,121,2),(52,125,0),(2,105,77),(3,85,2),(3,45,2),(3,89,1),(53,93,2),(54,81,123),(54,85,2),(4053,73,2),(4053,77,99),(4053,117,0),(4053,129,37),(3052,97,2),(3052,101,444)]:mbf.put(before,r,o,v)
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
        if case.get('cleanup') and not case.get('parent'):
            (d/'YTNAME.DAT').write_bytes(b'acct1,pw,Q,\r\nacct2,pw,Q,\r\nacct3,pw,R,\r\nother,pw,Other,User\r\n\x1a')
            def mail(to,fr,text):return mbf.enc(1)+mbf.enc(to)+mbf.enc(fr)+text.ljust(72,b' ')+bytes(2)
            (d/'YTRMSG.DAT').write_bytes(mail(2,3,b'TO Q')+mail(3,2,b'FROM Q')+mail(3,3,b'UNRELATED'))
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
