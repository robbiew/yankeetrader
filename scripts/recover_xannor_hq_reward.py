"""Capture ordinary original-DOS HQ victory rewards in fresh disposable mounts."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/surrender-xannor'
RECIPE='xannor-hq-reward-v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)


def cases():
    out=[]
    def add(name,action='fighter',**kw):
        target=100 if action in('fighter','none')else 101
        c=dict(name=name,action=action,actor=2,hq=target,target=target,owner=-1,defenders=1,amount=10001 if action=='fighter'else(20 if action=='missile'else 1),patches=[])
        c.update(kw);out.append(c)
    for action in ('fighter','missile','plasma'):add(action+'-hq',action)
    add('fighter-away',hq=1114)
    add('fighter-mercenary',owner=-2)
    add('fighter-human',owner=3)
    add('fighter-partial',defenders=1000000,amount=1)
    add('fighter-empty',action='none',defenders=0)
    add('fighter-abort',amount=0)
    for action in ('missile','plasma'):
        add(action+'-away',action,hq=102)
        for owner,label in [(-2,'mercenary'),(3,'human'),(2,'own')]:add(action+'-'+label,action,owner=owner)
        add(action+'-empty',action,defenders=0)
        add(action+'-partial',action,defenders=1000000,amount=1)
        add(action+'-route',action,destination=102)
    add('missile-insufficient',action='missile',amount=101)
    add('fighter-team',team=True)
    add('fighter-actor3',actor=3,team=True)
    for label,balance in [('zero',0),('fraction',1005.75),('2p24-edge',2**24-1),('2p30-even',2**30),('2p30-odd',2**30+128),('2p43',2**43),('2p44',2**44),('modern-limit',9000000000000000)]:
        add('fighter-balance-'+label,patches=[(2,81,balance)])
    add('fighter-existing-queue',patches=[(72,105,3)])
    add('fighter-pause-auto',pause_auto=True,timeout_seconds=180)
    add('reconnect-no-repeat',action='none',parent='fighter-hq',no_setup=True,time='00:02:00')
    add('restored-hq-repeat',parent='fighter-hq',no_setup=True,patches=[(151,81,1),(151,85,-1)],time='00:02:00')
    return out


def capture(destination,selected):
    destination.mkdir(parents=True,exist_ok=False)
    base=(SOURCE/'before.dat').read_bytes();(destination/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
    recipe=dict(recipe=RECIPE,scenarios=selected);(destination/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
    def run(c):
        d=destination/c['name'];d.mkdir()
        for p in SOURCE.iterdir():
            if p.suffix.upper()in('.DAT','.ASC','.ANS','.DOC','.DEF'):shutil.copy2(p,d/p.name)
        for name in('YT.EXE','BRUN30.EXE','LOCAL.EXE','XANNORHQ.TXT'):shutil.copy2(ROOT/'archive/dos-original'/name,d/name)
        shutil.copy2(ROOT/'archive/analysis/yt-combat/KEYFEED.COM',d/'KEYFEED.COM')
        if c.get('parent'):
            parent=destination/c['parent']
            parent_side=json.loads(gzip.decompress((parent/'sidefiles.json.gz').read_bytes()))
            for name,value in parent_side.items():(d/name).write_bytes(bytes.fromhex(value['hex']))
            b=bytearray(gzip.decompress((parent/'after.dat.gz').read_bytes()))
        else:b=bytearray(base)
        patches=[(1,117,c['hq']),(72,105,0),(151,81,0),(151,85,0),(152,81,0),(152,85,0),(51+c['target'],81,c['defenders']),(51+c['target'],85,c['owner']),(2,97,100),(2,113,10)]
        if c.get('no_setup'):patches=[]
        if c['actor']==3:
            patches += [(3,o,mbf.get(b,2,o))for o in range(41,130,4)if o not in(81,85)] + [(3,57,100),(3,81,765432),(3,85,6)]
            (d/'YTNAME.DAT').write_bytes(b'Dummy,Dummy,Dummy,Dummy\r\nTester,,Enemy,\r\n\x1a')
        if c.get('team'):
            at=(52-1)*137;b[at:at+41]=b'Reward Team'.ljust(41,b' ');b[at+113:at+117]=b'TST1'
            patches += [(2,89,1),(3,89,1),(52,73,11),(52,77,c['actor']),(52,109,2),(52,117,3),(52,121,0),(52,125,0)]
        patches+=c['patches']
        for r,o,v in patches:mbf.put(b,r,o,v)
        before=bytes(b);(d/'YTDATA.DAT').write_bytes(before)
        action=('A;'+str(c['amount']))if c['action']=='fighter'else('!'if c['action']=='missile'else'+')+';'+str(c.get('destination',c['target']))+';'+str(c['amount'])
        if c['action']=='none':action='Q;Y'
        keys=b'\r~~~~~\r~'+action.encode()+(b'\r'+b'~'*55+b'Q;Y\r~~~\r~~~~~\r'if c.get('pause_auto')else b'\r~~~\r~~~Q;Y\r~~~\r')
        (d/'KEYS.TXT').write_bytes(keys)
        initial={p.name:p.read_bytes()for p in d.iterdir()if p.suffix.upper()in('.DAT','.ASC')and p.name!='YTDATA.DAT'}
        (d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({k:v.hex()for k,v in sorted(initial.items())},indent=2)+'\n').encode(),mtime=0))
        cmds=[f'mount c {d}','c:','date 10/24/2026','time '+c.get('time','00:00:00'),'date > dosdate.log','time > dostime.log','keyfeed','local TESTER > game.log','exit']
        timeout=False
        try:
            with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for command in cmds for v in('-c',command)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=c.get('timeout_seconds',60),check=True)
        except subprocess.TimeoutExpired:timeout=True
        after=(d/'YTDATA.DAT').read_bytes();text=(d/'GAME.LOG').read_bytes().decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text)
        final={name:dict(before_sha256=sha(value),after_sha256=sha((d/name).read_bytes()),hex=(d/name).read_bytes().hex())for name,value in initial.items()}
        (d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps(final,indent=2)+'\n').encode(),mtime=0))
        for name,data in [('before',before),('after',after)]:(d/(name+'.dat.gz')).write_bytes(gzip.compress(data,mtime=0))
        keep={'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
        result={**c,'applied_patches':patches,'recipe':RECIPE,'baseline_sha256':sha(base),'before_sha256':sha(before),'after_sha256':sha(after),'date':'10/24/2026','time':c.get('time','00:00:00'),'timeout_seconds':c.get('timeout_seconds',60),'timed_out':timeout,'complete':not timeout and 'Returning to Yankee Trader Local Logon Program...'in text,'binaries':{n:sha((d/n).read_bytes())for n in('YT.EXE','BRUN30.EXE','LOCAL.EXE','XANNORHQ.TXT','KEYFEED.COM')},'files':{n:sha((d/n).read_bytes())for n in sorted(keep)}}
        (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        for p in d.iterdir():
            if p.is_file()and p.name not in keep|{'result.json'}:p.unlink()
        print(c['name'],result['complete'],'credits',mbf.get(before,c['actor'],81),'->',mbf.get(after,c['actor'],81),'queue',mbf.get(after,72,105),'reward',text.count('Collect 1,000,000 credits bonus!'),flush=True)
        return result
    roots=[c for c in selected if not c.get('parent')];children=[c for c in selected if c.get('parent')]
    with ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(run,roots))
    for c in children:results.append(run(c))
    (destination/'results.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);a=p.parse_args();capture(a.destination.resolve(),cases())
