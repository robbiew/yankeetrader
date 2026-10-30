"""Verify declared original-DOS revenge/targeting controls and native byte evidence."""
import argparse,gzip,hashlib,importlib.util,json,math,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--evidence',type=Path,default=ROOT/'research/yt-xannor-revenge/dos')
p.add_argument('--queue-evidence',type=Path,default=ROOT/'research/yt-xannor-revenge/queue')
a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()

def get(data,record,offset):
    raw=data[(record-1)*137+offset:(record-1)*137+offset+4];mant=int.from_bytes(raw[:3],'little')
    return 0 if not raw[3] else (-1 if mant&0x800000 else 1)*(1+(mant&0x7fffff)/2**23)*2.0**(raw[3]-129)

def put(data,record,offset,value):
    raw=bytes(4)
    if value:
        fraction,exponent=math.frexp(abs(value));mant=round((fraction*2-1)*2**23)
        if mant==2**23:mant=0;exponent+=1
        raw=(mant|(0x800000 if value<0 else 0)).to_bytes(3,'little')+bytes([exponent+128])
    at=(record-1)*137+offset;data[at:at+4]=raw

def force(b):return sum(get(b,51+s,81)for s in range(1,3001)if get(b,51+s,85)==-1)
def paths(text):return {int(s):int(t)for s,t in re.findall(r'from sector (\d+) to sector +(\d+)',text)}
def location(g):return 100 if g==2 else 200+g

def clock(d,date,time):
    assert date in (d/'DOSDATE.LOG').read_text(),'DOS date capture'
    match=re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)',(d/'DOSTIME.LOG').read_text());assert match,'DOS time capture'
    h,m,s,f=map(int,match.groups()[:4]);actual=(h%12+(12 if match[5]=='pm'else 0))*3600+m*60+s+f/100
    assert abs((actual-int(time[:2])*3600+43200)%86400-43200)<=1,'DOS time mismatch'

bins={name:(ROOT/'archive/dos-original'/name).read_bytes()for name in('YTMAINT.EXE','BRUN30.EXE','YT.EXE')}
assert [sha(bins[n])for n in bins]==['8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6','3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8','c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037']
base=bytearray(gzip.decompress((ROOT/'research/yt-xannor-mobile/dos/baseline.dat.gz').read_bytes()))
assert sha(base)=='601337e3cc2776bc6edb2faac04e055e0eaddd959dff57122c0c262df5aabbe0'
for sector in range(8,3001):
    for off in(41,45,49,53,57,61):put(base,51+sector,off,0)
for r,o,v in[(2,57,250),(2,109,4000),(2,125,0),(2,53,100000000),(2,61,100000000),(1165,81,1000000),(72,105,0)]:put(base,r,o,v)
for g in range(3,21):
    for r,o,v in[(51+g,105,200+g),(251+g,81,100),(251+g,85,-1)]:put(base,r,o,v)
base=bytes(base);assert sha(base)=='bf34079e27215d2c086ec750fc2b4fd30d90d4c869eb0bb26227d654a0292bc9'
assert gzip.decompress((a.evidence/'baseline.dat.gz').read_bytes())==base
raw=(a.evidence/'recipe.json').read_bytes();assert sha(raw)=='2e5fe8e760903cdbcf24e232746b3485b5f391bd5611e43a79974c2aad5ffda6','frozen declarations'
recipe=json.loads(raw);expected={c['name']:c for c in recipe['scenarios']};assert len(expected)==53
manifest=json.loads((a.evidence/'results.json').read_text());assert manifest['recipe']==recipe['recipe']=='xannor-revenge-isolation-v1'
assert len(manifest['scenarios'])==len(expected)and{c['name']for c in manifest['scenarios']}==set(expected)
worlds={};logs={}
for c in manifest['scenarios']:
    name=c['name'];spec=expected[name];d=a.evidence/name
    assert c==json.loads((d/'result.json').read_text()),name
    assert all(c[k]==v for k,v in spec.items()),(name,'declaration mismatch')
    assert c['recipe']==recipe['recipe']and c['baseline_sha256']==sha(base)
    assert c['complete']and not c['timed_out']and c['timeout_seconds']==45,name
    assert c['date']==spec.get('date','10/25/2026')and c['time']==spec.get('time','00:00:00'),name
    assert c['executable_sha256']==sha(bins['YTMAINT.EXE'])and c['runtime_sha256']==sha(bins['BRUN30.EXE'])
    assert set(c['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','sidefiles.json','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
    for file,digest in c['files'].items():assert sha((d/file).read_bytes())==digest,(name,file)
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(before)==len(after)==4151*137 and sha(before)==c['before_sha256']and sha(after)==c['after_sha256']
    rebuilt=bytearray(worlds[spec['parent']][1]if spec.get('parent')else base)
    if spec.get('second'):rebuilt[274:411]=rebuilt[137:274];rebuilt[274:315]=b'R'.ljust(41,b' ')
    if spec.get('arrival'):
        for origin in[100]+list(range(203,221)):put(rebuilt,51+origin,41,250)
    if spec.get('candidate_screen'):
        count,owner=spec['candidate_screen']
        for sector in range(8,3001):
            if get(rebuilt,51+sector,81)==0 and get(rebuilt,51+sector,93)==0:put(rebuilt,51+sector,81,count);put(rebuilt,51+sector,85,owner)
    if spec.get('candidate_planets'):
        for sector in range(8,3001):
            if get(rebuilt,51+sector,93)==0:put(rebuilt,51+sector,93,2 if spec['candidate_planets']is True else spec['candidate_planets'])
    for r,o,v in spec['patches']:put(rebuilt,r,o,v)
    assert before==bytes(rebuilt),(name,'undeclared setup or broken world chain')
    clock(d,c['date'],c['time'])
    text=(d/'transcript.txt').read_text();assert 'Daily Maintenance Completed OK'in text,name
    for side,record in json.loads((d/'sidefiles.json').read_text()).items():
        assert sha(bytes.fromhex(record['hex']))==record['after_sha256']
        original=ROOT/'archive/analysis/dos-validation/evidence'/side
        assert record['before_sha256']==(sha(original.read_bytes())if original.exists()else None)
    pointer=get(before,72,105);active=pointer>0 and get(before,int(pointer),57)>7
    assert ('Xannor REVENGE!'in text)==active,(name,'revenge activation')
    assert get(after,72,105)==(0 if pointer>0 else pointer),(name,'pointer consumption')
    if not spec.get('parent'):
        assert 'Calculated Dynamic Xannor Regeneration is 0 fighters'in text,name
        if not spec.get('arrival') and spec.get('candidate_screen',[0,0])[1] not in(-2,2):assert force(after)==force(before),(name,'target-only force conservation')
        for player in(2,3):
            if get(before,player,85)>0:
                initial=get(before,player,125);normalized=1 if initial<0 else initial;want=max(0,normalized-.05)if normalized>0 else 0
                assert abs(get(after,player,125)-want)<.000001,(name,'cloak decay')
    assert re.findall(r'Group: (\d+) +Size: (\d+)',text)==[(str(g),'100')for g in range(2,21)],(name,'activation count/force')
    if not spec.get('arrival'):assert ': lost'not in text.split('Mercenary Maintenance...')[0],(name,'unexpected Xannor combat')
    worlds[name]=before,after;logs[name]=text

for name in('revenge-active','revenge-hidden','revenge-dead-positive','revenge-cloak-0','revenge-cloak-1','revenge-cloak-10'):
    targets=paths(logs[name]);assert all(targets[location(g)]==250 for g in range(2,16)),(name,'retained revenge target')
    assert len({targets[location(g)]for g in range(16,21)})==1 and targets[216]>7,(name,'fallback group override')
for name in('revenge-top-other','revenge-top-dead','revenge-top-other-clock-4','revenge-top-other-clock-8'):
    target=paths(logs[name]);assert all(target[location(g)]==250 for g in range(2,16))and all(target[location(g)]==260 for g in range(16,21)),(name,'top vs revenge override')
    assert 'Group 20 will hunt for R'in logs[name]
assert 'Group 20 will hunt for Q'in logs['top-tie']and paths(logs['top-tie'])[220]==250,'strict top-score tie'
assert 'Group 20 will hunt'not in logs['top-unnamed']and 'Group 20 will hunt'not in logs['top-no-score']
assert 'Group 20 will hunt for R'in logs['revenge-top-protected']and len({paths(logs['revenge-top-protected'])[s]for s in range(216,221)})==1,'protected hunt replacement'
assert all(t==1114 for t in paths(logs['revenge-hq-override']).values()),'HQ overrides revenge/top'
assert 'Xannor REVENGE!'in logs['revenge-unnamed-live']and paths(logs['revenge-unnamed-live'])[100]!=250,'live sector does not invent cached location'
assert 'Xannor REVENGE!'in logs['revenge-inactive-slot-three']and get(worlds['revenge-inactive-slot-three'][0],3,85)==0,'inactive victim guard absent'
for hour in(0,4,8):
    assert ('Group 20 will hunt'in logs['hunt-cloak-1-clock-'+str(hour)])==(hour!=0),'observed valid-cloak sample'
    assert 'Group 20 will hunt'not in logs['hunt-cloak-10-clock-'+str(hour)],'diagnostic cloak detection'
plain=paths(logs['ordinary'])
for name in('candidate-force-1-owner-0','candidate-force-2-owner--1'):assert paths(logs[name])==plain,(name,'unqualified candidate changed draw path')
assert paths(logs['candidate-force-2-owner-0'])!=plain,'qualified candidate boundary'
# Dense planet references change earlier Wanderer placement/RNG too. Their
# target logs are diagnostic observations, not an isolated causal counterfactual.
for cloak in(0,10):
    name='revenge-arrival-cloak-'+str(cloak);before,after=worlds[name]
    if cloak==0:
        assert logs[name].count('(Xannor Lost)')==14 and force(before)-force(after)==1400,'uncloaked arrivals did not fight'
        assert all(get(after,51+g,105)==0 for g in range(2,16))
    else:
        assert ': lost'not in logs[name]and force(after)==force(before),'revenge bypassed interception cloak'
        assert all(get(after,51+g,105)==250 for g in range(2,16))and get(after,301,81)==1400,'hidden arrivals duplicated force'
assert worlds['revenge-next-day'][0]==worlds['revenge-active'][1]and 'Xannor REVENGE!'not in logs['revenge-next-day'],'consumed pointer reactivated'
for name in('revenge-arrival-cloak-0','revenge-arrival-cloak-10'):
    side=json.loads((a.evidence/name/'sidefiles.json').read_text())
    if name.endswith('-10'):assert 'YTRMSG.DAT'not in side,'hidden arrival emitted private battle mail'
    else:
        mail=bytes.fromhex(side['YTRMSG.DAT']['hex']);assert len(mail)==14*86,'private battle message count'
        losses=[]
        for i in range(14):
            record=mail[i*86:(i+1)*86]
            assert [get(record,1,o)for o in(0,4,8)]==[1,2,-1],'private battle recipient attribution'
            match=re.search(rb'We kilt (\d+) of yoor fyterz',record[12:]);assert match,'private battle content'
            losses.append(int(match[1]))
        assert losses==[int(n)for n in re.findall(r'Q : lost 100, dstrd (\d+) \(Xannor Lost\)',logs[name])],'private battle casualty correspondence'


# Independently apply MZ relocations before comparing every retained native byte.
def loaded(exe):
    head=struct.unpack_from('<H',exe,8)[0]*16;image=bytearray(exe[head:])
    for i in range(struct.unpack_from('<H',exe,6)[0]):
        off,seg=struct.unpack_from('<HH',exe,struct.unpack_from('<H',exe,24)[0]+4*i);at=seg*16+off
        struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
    return image
images={sha(b):loaded(b)for b in bins.values()}
ranges={
 'YTMAINT.EXE':{'0x1052e':265,'0x12454':128,'0x12534':154,'0x1260e':187,'0x12fab':324,'0x131e6':78,'0x13234':221,'0x13311':221,'0x133ee':145,'0x13dc0':144,'0x13baa':192,'0x13c90':141},
 'BRUN30.EXE':{'0x1a802':192,'0x11f6b':101,'0x1ac32':32,'0x11e5b':25,'0x11ec3':49,'0x1038d':396},
 'YT.EXE':{'0x29bfe':472,'0x111ee':156,'0x266b0':176,'0x2a430':133,'0x2b106':214}}
records=json.loads((ROOT/'research/yt-xannor-revenge/rea/target-paths.json').read_text())['records'];assert len(records)==23
seen=set()
for r in records:
    v=r['normalized_result'];digest=r['subject']['digest']['sha256'];name=next(n for n,b in bins.items()if sha(b)==digest)
    key=(name,v['address']);assert key not in seen;seen.add(key)
    assert r['operation']=='read_bytes'and v['complete']and v['requested_bytes']==v['returned_bytes']==ranges[name][v['address']]
    at=int(v['address'],16)-0x10000;assert bytes.fromhex(v['bytes_hex'])==images[digest][at:at+v['returned_bytes']]
run=images[sha(bins['BRUN30.EXE'])];image=images[sha(bins['YTMAINT.EXE'])]
for op,target in[(0x71,0x1e5b),(0xa1,0xa82c),(0xa5,0xa831)]:assert struct.unpack_from('<H',run,0x38d+op*2)[0]==target,'runtime dispatch'
assert image[0x3c13:0x3c1f]==bytes.fromhex('cd3fa5909080bb000076014b'),'ordinary .33 equality branch'
assert image[0x3348:0x334b]==bytes.fromhex('cd3d34'),'eager candidate detection draw'

# Model-only boundaries: these are not native draw counts or exact RNG replays.
spec=importlib.util.spec_from_file_location('rules',ROOT/'research/yt-xannor-revenge/recovered_rules.py');rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
assert rules.revenge_setup(2,{2:250},{2:0})==dict(pointer=0,flag=250,preferred=0)
assert rules.top_player({2:dict(named=True,score=2500000),3:dict(named=True,score=2500000)})==(2,2500000)
assert rules.intercept(.95-.33,.95)and not rules.intercept(.95-.33-.000001,.95),'route/top tie correction'
for revenge,want in[(False,1),(True,25)]:
    draws=[]
    def rng():draws.append(0);return 0
    assert rules.candidate_search(10,{}, {},3,0,revenge,rng)==(0,want)
    assert len(draws)==want*3,'candidate and eager per-record draws'
assert rules.candidate_search(10,{}, {},51,250,True,lambda:0)==(250,1),'retained preference short circuit'
seq=iter([.7,.95]);assert rules.candidate_search(10,{}, {2:dict(sector=8,cloak=.95)},2,0,False,lambda:next(seq))==(0,1),'candidate equality is strict'
seq=iter([.7,.95]);assert rules.candidate_search(10,{}, {2:dict(sector=8,cloak=.95)},2,0,True,lambda:next(seq))==(8,1),'revenge selection bypass'
assert rules.candidate_search(10,{1:dict(planet=2)},{},2,0,False,lambda:0)==(1,1),'protected raw candidate stops search'
assert rules.destination(2,8,1,260,False,1000,100,1114)==8
assert rules.destination(16,8,250,260,True,1,4000,1114)==1114
seq=iter([.62,.25]);assert rules.top_target(2,2500000,250,260,.95,3000,lambda:next(seq))==(250,2),'position tie keeps live field'
seq=iter([.62,.250001]);assert rules.top_target(2,2500000,250,260,.95,3000,lambda:next(seq))==(260,2)

# Queue controls are checked below after the maintenance matrix.
raw=(a.queue_evidence/'recipe.json').read_bytes()
assert sha(raw)=='4a5c614a78da3ddff0e1ba0ad356c8df997eb62eb1a01092c5261a3d3daa8e65','queue declarations'
qrecipe=json.loads(raw);qmanifest=json.loads((a.queue_evidence/'results.json').read_text())
assert qrecipe['recipe']==qmanifest['recipe']=='xannor-revenge-queue-v1'and len(qrecipe['scenarios'])==len(qmanifest['scenarios'])==3
qsource=ROOT/'archive/analysis/yt-combat/experiments/surrender-xannor'
qbase=(qsource/'before.dat').read_bytes();assert gzip.decompress((a.queue_evidence/'baseline.dat.gz').read_bytes())==qbase
for c,spec in zip(qmanifest['scenarios'],qrecipe['scenarios']):
    name=spec['name'];d=a.queue_evidence/name
    assert c==json.loads((d/'result.json').read_text())and all(c[k]==v for k,v in spec.items())
    assert c['recipe']==qrecipe['recipe']and c['baseline_sha256']==sha(qbase)and c['complete']and not c['timed_out']
    assert c['date']=='10/24/2026'and c['time']=='00:00:00';clock(d,c['date'],c['time'])
    assert set(c['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
    for file,digest in c['files'].items():assert sha((d/file).read_bytes())==digest,(name,file)
    for binary,digest in c['binaries'].items():
        source=ROOT/'archive/analysis/yt-combat/KEYFEED.COM'if binary=='KEYFEED.COM'else ROOT/'archive/dos-original'/binary
        assert sha(source.read_bytes())==digest,(name,'binary identity')
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(before)==len(after)==len(qbase)and sha(before)==c['before_sha256']and sha(after)==c['after_sha256']
    rebuilt=bytearray(qbase)
    for r,o,v in[(1,117,spec['hq']),(72,105,0),(151,81,spec['defenders']),(151,85,-1)]:put(rebuilt,r,o,v)
    assert before==bytes(rebuilt),(name,'undeclared producer setup')
    text=(d/'transcript.txt').read_text();assert 'Returning to Yankee Trader Local Logon Program...'in text
    assert (d/'KEYS.TXT').read_bytes()==b'\r~~~~~\r~A;'+str(spec['attack']).encode()+b'\r~~~\r~~~Q;Y\r~~~\r'
    assert get(after,72,105)==(2 if name=='xannor-hq-win'else 0),(name,'HQ revenge producer')
    if name=='xannor-hq-win':
        assert get(after,151,81)==0 and 'You defeated all the fighters'in text and 'Collect 1,000,000 credits bonus!'in text
    elif name=='ordinary-xannor-win':assert get(after,151,81)==0 and 'Collect 1,000,000 credits bonus!'not in text
    else:assert get(after,151,81)==1000000 and 'Collect 1,000,000 credits bonus!'not in text

print(f'Verified {len(expected)} maintenance controls, 3 player queue controls, exact next-day chain, model boundaries and {len(records)} complete REA observations.')
