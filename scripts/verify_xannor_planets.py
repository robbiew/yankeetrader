"""Verify declared DOS planetary encounters, cleanup, chronology and REA byte evidence."""
import argparse, gzip, hashlib, importlib.util, json, math, re, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--evidence',type=Path,default=ROOT/'research/yt-xannor-planets/dos')
a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()


def get(data, rec, off):
    raw=data[(rec-1)*137+off:(rec-1)*137+off+4]
    m=int.from_bytes(raw[:3],'little')
    return 0 if raw[3]==0 else (-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/2**23)*2**(raw[3]-129)


def put(data, rec, off, value):
    raw=bytes(4)
    if value:
        f,e=math.frexp(abs(value));m=round((f*2-1)*2**23)
        if m==2**23:m=0;e+=1
        raw=(m|(0x800000 if value<0 else 0)).to_bytes(3,'little')+bytes([e+128])
    at=(rec-1)*137+off;data[at:at+4]=raw


base=bytearray(gzip.decompress((ROOT/'research/yt-xannor-mobile/dos/baseline.dat.gz').read_bytes()))
assert sha(base)=='601337e3cc2776bc6edb2faac04e055e0eaddd959dff57122c0c262df5aabbe0'
for r,o,v in [(152,93,2),(54,105,200),(251,81,10000),(251,85,-1),
                  (4053,45,1000),(4053,49,2000),(4053,53,3000),(4053,57,0),(4053,61,0),(4053,65,0),
                  (4053,73,2),(4053,77,0),(4053,117,0),(4053,69,11),(4053,113,5),(4053,125,3),(4053,129,37)]:put(base,r,o,v)
for off in(41,45,49,53,57,61):put(base,251,off,0)
base=bytes(base)
assert sha(base)=='c3e432bb8aef6e094a42fed4f2a22dabbd6c306079d19d455eb0d7b832619716'
assert gzip.decompress((a.evidence/'baseline.dat.gz').read_bytes())==base
raw=(a.evidence/'recipe.json').read_bytes()
assert sha(raw)=='95d34c7571c2fa6cde33dc23e7850b7957048572eec09926092eacef6dbc2847','fixture declarations changed'
recipe=json.loads(raw);expected={c['name']:c for c in recipe['scenarios']}
assert recipe['recipe']=='xannor-planet-isolation-v1' and len(expected)==71
manifest=json.loads((a.evidence/'results.json').read_text())
assert manifest['recipe']==recipe['recipe'] and len(manifest['scenarios'])==71
assert {c['name']for c in manifest['scenarios']}==set(expected)
exe=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
assert sha(exe)=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
assert sha(runtime)=='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
worlds={};logs={};sides={}
for c in manifest['scenarios']:
    n=c['name'];spec=expected[n];d=a.evidence/n
    assert c==json.loads((d/'result.json').read_text()) and all(c[k]==v for k,v in spec.items()),n
    assert set(c)==set(spec)|{'recipe','baseline_sha256','before_sha256','after_sha256','executable_sha256','runtime_sha256','date','time','timed_out','timeout_seconds','complete','files'},n
    assert c['recipe']==recipe['recipe'] and c['baseline_sha256']==sha(base),n
    assert c['executable_sha256']==sha(exe) and c['runtime_sha256']==sha(runtime),n
    assert c['complete'] and not c['timed_out'] and c['timeout_seconds']==45,n
    assert c['date']==spec.get('date','10/25/2026') and c['time']==spec.get('time','00:00:00'),n
    assert set(c['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','sidefiles.json','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'},n
    for f,h in c['files'].items():assert sha((d/f).read_bytes())==h,(n,f)
    b=gzip.decompress((d/'before.dat.gz').read_bytes());v=gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(b)==len(v)==len(base) and sha(b)==c['before_sha256'] and sha(v)==c['after_sha256'],n
    rebuilt=bytearray(worlds[spec['parent']][1]if spec.get('parent')else base)
    if spec.get('second'):
        rebuilt[274:411]=rebuilt[137:274];rebuilt[274:315]=b'R'.ljust(41,b' ')
    for r,o,value in spec['patches']:put(rebuilt,r,o,value)
    assert b==bytes(rebuilt),(n,'undeclared input or broken exact-world chain')
    assert c['date']in(d/'DOSDATE.LOG').read_text(),n
    clock=re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)',(d/'DOSTIME.LOG').read_text());assert clock,n
    h,m,s,f=map(int,clock.groups()[:4]);actual=(h%12+(12 if clock[5]=='pm'else 0))*3600+m*60+s+f/100
    assert abs((actual-int(c['time'][:2])*3600+43200)%86400-43200)<=1,(n,'captured DOS clock')
    t=(d/'transcript.txt').read_text();assert 'Daily Maintenance Completed OK'in t,n
    side=json.loads((d/'sidefiles.json').read_text())
    for name,data in side.items():
        raw=bytes.fromhex(data['hex']);assert sha(raw)==data['after_sha256'],(n,name)
        src=ROOT/'archive/analysis/dos-validation/evidence'/name
        assert data['before_sha256']==(sha(src.read_bytes())if src.exists()else None),(n,'sidefile baseline')
    news=bytes.fromhex(side['YTNEWS.DAT']['hex']).decode('cp437')
    battle_lines=[line for line in t.splitlines()if 'attacked the planet'in line or 'destroyed!'in line or ': lost'in line]
    for line in battle_lines:assert line.strip()in news,(n,'public battle journal')
    worlds[n]=(b,v);logs[n]=t;sides[n]=side
    if not spec.get('parent'):
        assert 'Calculated Dynamic Xannor Regeneration is 0 fighters'in t,n
        want=([(2,int(get(b,151,81)))]if get(b,151,81)>0 else[])+[(3,10000)]
        assert [(int(g),int(f))for g,f in re.findall(r'Group: (\d+) +Size: (\d+)',t)]==want,(n,'isolated mobile participants')
        assert get(v,54,105)==200 and get(v,251,81)==10000 and get(v,251,85)==-1,(n,'parked group moved or changed')


def planet(n,after=True):return worlds[n][1 if after else 0]
def p(n,o):return get(planet(n),4053,o)
def rates(n):return [p(n,o)for o in(45,49,53)]
def stocks(n):return [p(n,o)for o in(57,61,65)]
def force(v):return sum(get(v,r,81)for r in range(52,3052)if get(v,r,85)==-1)
def attacked(n):return 'attacked the planet "Probe Planet"'in logs[n]

skips={'no-planet-reference','zero-moving-force','inactive-record','xannor','origin-planet','friendly-screen','unowned-screen'}|{n for n in expected if 'no-arrival'in n or n=='warehouse-counterfactual'}
for n in skips:
    b,v=worlds[n]
    assert not attacked(n) and force(v)==force(b),(n,'skipped encounter changed force')
    assert p(n,73)==get(b,4053,73),(n,'skipped encounter neutralized title')
    if n!='inactive-record':assert p(n,85)==12,(n,'skipped encounter deleted active planet')
assert p('inactive-record',85)==0 and rates('inactive-record')==[1000,2000,3000]

for n in expected:
    if expected[n].get('parent'):continue
    b,v=worlds[n]
    if attacked(n):
        r=rates(n);assert all(x>=0 for x in r),(n,'negative published production')
        assert all(0<=stock<=10*rate*(1+1e-6)+1e-6 for stock,rate in zip(stocks(n),r)),(n,'warehouse cap after damage')
        if p(n,77)==0:assert p(n,73)==0,(n,'ground-zero neutralization')
        else:assert p(n,73)==get(b,4053,73),(n,'guarded planetary title changed')
        sector=7 if n=='protected-planet'else 101
        if all(x==0 for x in r):
            assert p(n,85)==0 and get(v,51+sector,93)==0,(n,'logical destruction links')
        else:
            assert p(n,85)==12 and get(v,51+sector,93)==2,(n,'surviving planet links')
        assert force(v)<=force(b),(n,'assault created or harvested Xannor force')
    assert get(v,2,81)==get(b,2,81) and get(v,2,129)==get(b,2,129),(n,'planet assault salvaged player inventory')
    if n!='ship-after-win':
        assert get(v,2,61)==get(b,2,61) and get(v,2,53)==get(b,2,53) and get(v,2,45)==0,(n,'planet assault damaged or killed ship directly')
        assert 'YTRMSG.DAT'not in sides[n],(n,'unexpected private planet message')

for n in ('production-large','neutral','mercenary','owner-one'):
    assert attacked(n) and p(n,85)==12 and p(n,73)==0 and all(0<x<y for x,y in zip(rates(n),rates('no-planet-reference'))),(n,'surviving production damage')
for amount in(1,499,500,999,1000,500000):
    n='ground-'+str(amount)
    assert p(n,77)==amount-1 and get(planet(n),53,105)==0 and rates(n)==[1000,2000,3000],(n,'one ground consumed against fatal first volley')
assert p('one-ground-one-attacker',77)==0 and get(planet('one-ground-one-attacker'),53,105)==0,'ground damage is at least one fighter'
n='large-group-ground-500000';used=500000-p(n,77)
assert 100<=used<=100000 and used<=100000<=1000*used and rates(n)==[1,1,1] and get(planet(n),53,105)==0,'large-ground casualty bounds'
assert p('large-group-ground-1',77)==0 and p('large-group-ground-1',85)==0 and 99001<=get(planet('large-group-ground-1'),1165,81)<=100001,'single-ground large-group survival'

# Earlier maintenance, rather than this helper, normalizes fractional/zero rates
# and surplus warehouses. Paired controls make that phase interference explicit.
for amount in(.25,.5,.75):
    n='fractional-ground-'+str(amount);counter='fractional-ground-no-arrival-'+str(amount)
    assert p(counter,77)==0 and rates(n)==rates('production-large'),(n,'fractional ground was normalized before assault')
assert rates('fractional-rates-no-arrival')==[1,1,1] and rates('zero-rates-no-arrival')==[1,1,1],'early minimum production clamp'
assert rates('surplus-zero-rates-no-arrival')==[1000,2000,3000],'earlier warehouse-driven rate restoration'
assert rates('surplus-zero-rates')==rates('production-large'),'restored rates were attacked, not original zeros'
for rate in(499,500,501,499.99993896484375):
    assert rates('rate-no-arrival-'+str(rate))==[rate]*3,('production threshold input',rate)
assert p('rate-501-force-1',45)<400 and p('rate-500-force-1',45)>499,'large batch occurs with only one attacker above rate threshold'
assert p('mixed-rates',49)==0 and p('mixed-rates',53)==0 and 0<p('mixed-rates',45)<501,'independent production components'
for hour in(4,8):
    n='production-clock-'+str(hour);counter='no-arrival-clock-'+str(hour)
    assert all(x<=y for x,y in zip(rates(n),rates(counter)))and p(counter,73)==2 and p(n,73)==0,(n,'clock/economy counterfactual')
assert rates('one-attacker-clock-eight')==rates('no-arrival-clock-8') and get(planet('one-attacker-clock-eight'),53,105)==0,'one-attacker production loss without rate damage'
assert all(x<y for x,y in zip(stocks('warehouse-damage'),stocks('warehouse-counterfactual'))),'damaged production did not cap warehouses'
for stock,rate in zip(stocks('warehouse-damage'),rates('warehouse-damage')):assert math.isclose(stock,rate*10,rel_tol=1e-6),'warehouse cap value'
assert all(math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-6)for a,b in zip(stocks('below-cap'),[get(worlds['below-cap'][0],4053,o)+get(worlds['no-planet-reference'][1],4053,o)for o in(57,61,65)])),'below-cap stocks changed beyond ordinary production'
assert p('bank-retained',117)==1234 and p('destroy-bank-retained',117)==1234,'bank retained by helper even after deletion'
for n in ('zero-rates','single-small-rate','fractional-rates','weapons-retained','destroy-bank-retained','hidden-ship-after-destruction','protected-planet'):
    assert rates(n)==[0,0,0] and p(n,85)==0 and get(planet(n),1165,81)>1,(n,'destruction did not preserve winning force')
assert [p('weapons-retained',o)for o in(69,113,125,129)]==[100000]*4,'logical deletion erased stale weapon bytes'
assert get(planet('weapons-retained'),1165,81)<101,'planet fighters were harvested instead of retained inactive'
for n in ('mines-before-planet','defense-before-planet'):
    assert not attacked(n)and rates(n)==[1000,2000,3000]and p(n,73)==2 and p(n,85)==12,(n,'earlier hazard did not gate planet')
assert get(planet('mines-before-planet'),152,129)==2,'fatal mine FIFO/count'
assert logs['defense-win-then-planet'].index('Plyr ftrs dstrd')<logs['defense-win-then-planet'].index('attacked the planet'),'sector battle before planetary attack'
assert get(planet('later-mines-after-loss'),153,129)==1 and get(planet('later-mines-after-win'),153,129)==0,'post-planet route continuation'
assert logs['ship-after-win'].index('Planet "Probe Planet" destroyed')<logs['ship-after-win'].index('Q : lost') and get(planet('ship-after-win'),2,61)<1000,'planet before ship dispatch'
assert 'Q : lost'not in logs['ship-after-loss'] and get(planet('ship-after-loss'),2,61)==1000,'fatal planet continued into ship combat'
assert worlds['destroyed-next-day'][0]==worlds['weapons-retained'][1],'broken exact-world chain'
assert p('destroyed-next-day',85)==0 and rates('destroyed-next-day')==[0,0,0] and [p('destroyed-next-day',o)for o in(69,113,125,129)]==[100000]*4,'inactive planet regrew or lost stale records on next day'

# Check every complete original-game/runtime Evidence record against MZ bytes
# with independent relocations, then pin the decisive dispatch operands/constants.
def loaded(exe):
    head=struct.unpack_from('<H',exe,8)[0]*16;image=bytearray(exe[head:])
    for i in range(struct.unpack_from('<H',exe,6)[0]):
        off,seg=struct.unpack_from('<HH',exe,struct.unpack_from('<H',exe,24)[0]+4*i);at=seg*16+off
        struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
    return image
images={sha(exe):loaded(exe),sha(runtime):loaded(runtime)}
game_ranges={'0x15efd':266,'0x16007':496,'0x161f7':515,'0x163fa':421,'0x1659f':395,'0x13a97':764,'0x19960':32,'0x192f0':4,'0x18e5e':4,'0x18c78':4}
run_ranges={'0x1038d':396,'0x10171':106,'0x11f6b':128,'0x1ac32':32,'0x1ac9d':184,'0x1c324':288,'0x1b354':96,'0x1b520':48,'0x1b4a0':48,'0x1b2c2':96}
records=json.loads((ROOT/'research/yt-xannor-planets/rea/assault-paths.json').read_text())['records']
assert len(records)==20
seen=set()
for r in records:
    v=r['normalized_result'];digest=r['subject']['digest']['sha256'];ranges=game_ranges if digest==sha(exe)else run_ranges
    key=(digest,v['address']);assert key not in seen;seen.add(key)
    at=int(v['address'],16)-0x10000;image=images[digest]
    assert r['operation']=='read_bytes'and v['complete'] and v['requested_bytes']==v['returned_bytes']==ranges[v['address']]
    assert bytes.fromhex(v['bytes_hex'])==image[at:at+v['returned_bytes']]
image=images[sha(exe)];run=images[sha(runtime)]
assert get(image[0x9960:0x9964],1,0)==1000 and get(image[0x9964:0x9968],1,0)==450
assert image[0x62e5:0x62ec]==bytes.fromhex('ba010081faf401'),'production batch reads location through constant false subscript'
for op,target in [(0x1d,0xac32),(0x81,0xb369),(0x89,0xb520),(0x91,0xb4a0),(0x99,0xb354),(0x9d,0xb359)]:assert struct.unpack_from('<H',run,0x38d+op*2)[0]==target
assert struct.unpack_from('<H',run,0x171+3*2)[0]==0xacb2
spec=importlib.util.spec_from_file_location('rules',ROOT/'research/yt-xannor-planets/recovered_rules.py')
rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
assert rules.ground_battle(1,1,lambda:0)==(0,0,1)
assert rules.ground_battle(100,500000,lambda:.999999)==(-900,499999,1)
assert rules.production_batch([500,500,500],101)==1 and rules.production_batch([501,0,0],101)==450
x=rules.assault(1,0,[501,1,1],[6000,20,20],2,lambda:.5)
assert x['raw_force']==-449 and x['force']==0 and x['rates']==[501,1,1]and x['owner']==0
seq=iter([.1,.6,.3,.9,.5]);x=rules.assault(1,0,[501,1,1],[6000,20,20],2,lambda:next(seq))
assert x['rates']==[411,0,0]and x['stocks']==[4110,0,0]and not x['destroyed']
# Static helper-only simultaneous-deletion branch; ordinary maintenance promotes
# initial zero rates to1, so this is not claimed as a whole-program DOS outcome.
x=rules.assault(1,1,[0,0,0],[0,0,0],2,lambda:0)
assert x['destroyed']and x['message']=='Xannor fighters destroyed'
print(f'Verified {len(expected)} completed Xannor planet runs, paired phase controls, exact next-day chain and {len(records)} game/runtime REA observations.')
