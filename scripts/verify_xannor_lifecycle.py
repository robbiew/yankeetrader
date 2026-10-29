"""Verify preserved original-DOS Xannor lifecycle provenance and semantic controls."""
import argparse,gzip,hashlib,json,math,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,default=ROOT/'research/yt-xannor-lifecycle/dos');args=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()

def get(data,r,o):
    raw=data[(r-1)*137+o:(r-1)*137+o+4];m=int.from_bytes(raw[:3],'little')
    return 0 if not raw[3] else (-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/2**23)*2.0**(raw[3]-129)

def put(data,r,o,v):
    raw=bytes(4)
    if v:
        f,e=math.frexp(abs(v));m=round((f*2-1)*2**23)
        if m==2**23:m=0;e+=1
        raw=(m|(0x800000 if v<0 else 0)).to_bytes(3,'little')+bytes([e+128])
    at=(r-1)*137+o;data[at:at+4]=raw

original=(ROOT/'archive/analysis/dos-validation/evidence/YTDATA.DAT').read_bytes()
assert sha(original)=='a5cc0a7a06909d156802a4bcd55d5971d8b0472d03686a2fad4b9b4b406b1f59'
player=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
exe=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
assert sha(exe)=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
assert sha(runtime)=='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
base=bytearray(original)
for r in range(2,52):base[(r-1)*137:r*137]=bytes(137);put(base,r,109,-1)
for sector in range(1,3001):
    for off in (81,85,93,105,129):put(base,51+sector,off,0)
for r in range(3052,4052):
    for off in (89,97):put(base,r,off,0)
for r in range(4052,4152):base[(r-1)*137:r*137]=bytes(137)
for slot,label,owner in ((1,'The Wanderer',0),(2,'Probe Planet',0),(99,'Mercenary Base',-2),(100,'Xannoron',-1)):
    r=4051+slot;at=(r-1)*137;base[at:at+41]=label.encode().ljust(41,b' ')
    for off,v in ((41,298),(73,owner),(77,1),(85,len(label)),(89,0),(117,1)):put(base,r,off,v)
for r,o,v in ((2050,93,1),(2051,93,99),(1165,93,100),(1165,81,10000),(1165,85,-1),(1,117,1114),(52,105,1114)):put(base,r,o,v)
base=bytes(base)
assert gzip.decompress((args.evidence/'baseline.dat.gz').read_bytes())==base,'full-size baseline recipe'
small=bytearray(base[:51*137])
small.extend(base[51*137:72*137]);small.extend(base[3051*137:3072*137]);small.extend(base[4051*137:4151*137])
for r,o,v in ((1,57,72),(1,61,93),(1,93,193),(1,117,8)):put(small,r,o,v)
for sector in range(1,22):
    for off in (41,45,49,53,57,61,81,85,93,105,129):put(small,51+sector,off,0)
    put(small,51+sector,41,21 if sector==1 else sector-1);put(small,51+sector,45,1 if sector==21 else sector+1)
for r,o,v in ((53,93,1),(54,93,99),(59,93,100),(59,85,-1),(52,105,8)):put(small,r,o,v)
for sector in range(9,22):
    slot=sector-7;r=93+slot;at=(r-1)*137;small[at:at+137]=bytes(137);label=('Block '+str(slot)).encode();small[at:at+41]=label.ljust(41,b' ')
    for off,v in ((41,298),(73,0),(77,1),(85,len(label)),(89,0),(117,1)):put(small,r,off,v)
    put(small,51+sector,93,slot)
small=bytes(small)
assert len(small)==193*137 and gzip.decompress((args.evidence/'small-baseline.dat.gz').read_bytes())==small,'21-sector baseline recipe'
expected={
'hq-held':{},'missing-reference':{(1165,93):0},'inactive-record':{(4151,85):0},'missing-both':{(1165,93):0,(4151,85):0},
'captured-planet':{(4151,73):2,(4151,77):500000,(4151,117):1234},'zero-reserves':{(4151,77):0,(4151,117):0},
'zero-hq':{(1165,81):0},'unowned-hq':{(1165,85):0},'duplicate-pointer':{(53,105):1114,(54,105):1114},
'empty-hq-pointer':{(52,105):0},'split-hq-pointers':{(52,105):1200,(1251,81):5000,(1251,85):-1},
'foreign-mobile-pointer':{(53,105):100,(151,81):999,(151,85):2},'friendly-mobile-pointer':{(53,105):100,(151,81):999,(151,85):-1},
'reclaim-overwhelming':{(2,109):10000000,(1165,81):10000000,(1165,85):2},'reclaim-no-score':{(1165,81):100,(1165,85):2},
'missing-both-time-04':{(1165,93):0,(4151,85):0},'missing-both-time-08':{(1165,93):0,(4151,85):0},
'wrong-home-reference':{(1165,93):2},'recreated-retained-stocks':{(1165,93):0,(4151,117):0,(4151,129):37,(4151,125):3,(4151,113):5},
'recreated-stock-reset':{(1165,93):0,(4151,117):0,(4151,57):11,(4151,61):13,(4151,65):17,(4151,69):7,(4151,129):37,(4151,125):3,(4151,113):5},
'recreated-stock-reset-inactive':{(1165,93):0,(4151,85):0,(4151,117):0,(4151,57):11,(4151,61):13,(4151,65):17,(4151,69):7,(4151,129):37,(4151,125):3,(4151,113):5},
'positive-home-reserves':{(4151,77):100,(4151,117):1234},'zero-hq-next-day':{},'missing-both-next-day':{},
}
for score in (100000,999999,1000000,1000500,10000000):expected[f'regen-{score}']={(2,109):score}
for owner in (-2,0,1,2):expected[f'reclaim-owner-{owner}']={(2,109):10000000,(1165,81):100,(1165,85):owner}
small_specs={'candidate-empty':(0,0,0,0),'candidate-human-one':(2,1,0,0),'candidate-human-two':(2,2,0,0),'candidate-merc-one':(-2,1,0,0),'candidate-merc-two':(-2,2,0,0),'candidate-xannor-two':(-1,2,0,0),'candidate-planet-blocked':(0,0,14,0),'candidate-zero-hq-positive-score':(0,0,0,1000000)}
for name,(owner,force,planet,score) in small_specs.items():expected[name]={(72,81):force,(72,85):owner,(72,93):planet,**({(2,109):score} if score else {})}
humans={'captured-planet','foreign-mobile-pointer','reclaim-overwhelming','reclaim-no-score'}|{f'regen-{s}'for s in (100000,999999,1000000,1000500,10000000)}|{f'reclaim-owner-{o}'for o in (-2,0,1,2)}|{'candidate-human-one','candidate-human-two','candidate-zero-hq-positive-score'}
blocked={'candidate-human-two','candidate-merc-two','candidate-planet-blocked'}
parents={'zero-hq-next-day':'zero-hq','missing-both-next-day':'missing-both'}
manifest=json.loads((args.evidence/'results.json').read_text());cases=manifest['scenarios']
assert manifest['recipe']=='xannor-lifecycle-isolation-v1' and len(cases)==len(expected) and {c['name']for c in cases}==set(expected)
worlds={};logs={}
for c in cases:
    name=c['name'];d=args.evidence/name;is_small=name in small_specs;baseline=small if is_small else base
    assert c==json.loads((d/'result.json').read_text()),name
    assert c['recipe']==manifest['recipe'] and c['source_sha256']==sha(original) and c['baseline_sha256']==sha(baseline),name
    assert c['executable_sha256']==sha(exe) and c['runtime_sha256']==sha(runtime),name
    assert bool(c.get('small'))==is_small and bool(c.get('human'))==(name in humans),name
    assert c.get('parent')==parents.get(name),name
    clock={'missing-both-time-04':'04:00:00','missing-both-time-08':'08:00:00'}.get(name,'00:00:00');date='10/26/2026'if name in parents else '10/25/2026'
    assert c['time']==clock and c['date']==date,name
    assert set(c['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'},name
    for file,digest in c['files'].items():assert sha((d/file).read_bytes())==digest,(name,file)
    assert ('Current date: '+('Mon 'if name in parents else 'Sun ')+date) in (d/'DOSDATE.LOG').read_text(),name
    clock_text=(d/'DOSTIME.LOG').read_text()
    observed=re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)',clock_text)
    assert observed,name
    hour,minute,second,hundredth=map(int,observed.groups()[:4])
    actual=(hour%12+(12 if observed[5]=='pm' else 0))*3600+minute*60+second+hundredth/100
    target=int(clock[:2])*3600
    assert abs((actual-target+43200)%86400-43200)<=1,(name,'captured DOS clock differs')
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(before)==len(after)==len(baseline) and sha(before)==c['before_sha256'] and sha(after)==c['after_sha256'],name
    overrides={(r,o):v for r,o,v in c.get('patches',[])}
    assert len(overrides)==len(c.get('patches',[])) and overrides==expected[name],(name,'fixture overrides')
    rebuilt=bytearray(gzip.decompress((args.evidence/parents[name]/'after.dat.gz').read_bytes()) if name in parents else baseline)
    if name in humans:
        rebuilt[137:274]=player[137:274]
        for off,v in ((41,297),(45,0),(57,7),(89,0),(109,0),(125,10)):put(rebuilt,2,off,v)
    for (r,o),v in overrides.items():put(rebuilt,r,o,v)
    if is_small and overrides[(72,93)]==0:rebuilt[106*137:107*137]=bytes(137)
    assert bytes(rebuilt)==before,(name,'undeclared fixture mutation/parent chain')
    text=(d/'transcript.txt').read_text();logs[name]=text;worlds[name]=(before,after)
    timeout=name in blocked
    assert c['timed_out']==timeout and c['complete']==(not timeout) and bool(c.get('expect_timeout'))==timeout,name
    assert c['timeout_seconds']==(8 if timeout else 45),name
    assert ('Daily Maintenance Completed OK' in text)==(not timeout),name
    n=21 if is_small else 3000;port_base=72 if is_small else 3051;planet_base=93 if is_small else 4051
    assert all(get(after,port_base+i,89)==get(before,port_base+i,89)==0 for i in range(1,22 if is_small else 1001)),(name,'unfunded port taxes')
    score=max([get(before,r,109)for r in range(2,52)if get(before,r,85)>0]+[0])
    # Normalization harvests Xannor-owned pointed sectors only, once even when
    # pointers are duplicated. Unpointed sector forces do not enter the cache.
    locations={int(get(before,51+i,105))for i in range(1,21)if get(before,51+i,105)>0}
    cached=sum(get(before,51+s,81)for s in locations if s<=n and get(before,51+s,85)==-1)
    regen=0 if cached>math.floor(score/100) else math.floor(score/500)
    reported=int(re.search(r'Calculated Dynamic Xannor Regeneration is (\d+) fighters',text)[1])
    assert reported==regen,(name,'regeneration cutoff/rounding')
    if timeout:
        assert 'Processing the Xannor' in text and 'MOVED their Headquarters' not in text and 'Mercenary Maintenance' not in text,name
        assert get(after,1,117)==8 and get(after,72,81)==overrides[(72,81)] and get(after,72,85)==overrides[(72,85)],name
        continue
    hq=int(get(after,1,117));assert 1<=hq<=n and get(after,52,105)==hq,(name,'HQ pointer consistency')
    assert all(0<=get(after,51+i,105)<=n and float(get(after,51+i,105)).is_integer() for i in range(1,21)),name
    home=planet_base+100
    if name not in parents:
        assert get(after,home,73)==-1,(name,'home retitling')
        created=not is_small and overrides.get((1165,93),100)==0
        assert ('The Xannor have made a Planet!' in text)==created,(name,'recreation predicate')
        if created:
            raw=after[(home-1)*137:(home-1)*137+41]
            assert raw.rstrip()==b'Xannoron' and get(after,home,85)==8,name
            assert all(get(after,home,o)==100000 for o in (45,49,53)),name
            assert all(get(after,home,o)==0 for o in (57,61,65,69,125)),(name,'creation reset stocks')
            assert 0<=get(after,home,77)<=273 and 100000<=get(after,home,117)<=10100000,name
        elif not is_small:
            assert 0<=get(after,home,77)-get(before,home,77)<=24,(name,'home ground increment')
            assert get(after,home,117)==(1000000 if get(before,home,117)==0 else get(before,home,117)),(name,'home reserve policy')
    if name=='inactive-record':assert get(after,home,85)==0 and get(after,1165,93)==100,name
    if name=='wrong-home-reference':assert get(after,1165,93)==2 and get(after,home,85)==8,name
    if name=='captured-planet':assert get(before,home,73)==2 and get(after,home,73)==-1 and get(after,home,77)>=500000,name
    if name.startswith('recreated-stock') or name=='recreated-retained-stocks':assert get(after,home,129)==37 and get(after,home,113)==5 and get(after,home,125)==0,(name,'retained fighters/plasma versus reset mines')
    if name in ('zero-hq','unowned-hq','empty-hq-pointer') or name.startswith('reclaim-owner-'):
        assert hq!=1114 and get(after,1165,93)==0 and get(after,51+hq,93)==100,(name,'relocation references')
    if name in ('reclaim-owner--2','reclaim-owner-2'):
        assert 'attempting to reclaim' in text and '*** Successful!' in text and get(after,1165,81)==get(after,1165,85)==0,name
    if name in ('reclaim-owner-0','reclaim-owner-1'):assert 'attempting to reclaim' not in text and get(after,1165,85)==overrides[(1165,85)],name
    if name in ('reclaim-overwhelming','reclaim-no-score'):
        assert 'attempting to reclaim' in text and '*** Failed!' in text and hq==1114,name
        if name=='reclaim-overwhelming':assert get(after,1165,85)==2 and 0<get(after,1165,81)<10000000,name
    if name=='foreign-mobile-pointer':assert get(after,151,81)==999 and get(after,151,85)==2,name
    if name=='friendly-mobile-pointer':assert get(after,151,81)==get(after,151,85)==0,name
    if name=='split-hq-pointers':assert hq==1114 and get(after,1251,81)==get(after,1251,85)==0,name
    if is_small:
        assert hq==21 and get(after,59,93)==0 and get(after,72,93)==100,name
        if name!='candidate-zero-hq-positive-score':
            force=small_specs[name][1]
            assert get(after,72,81)==21+force and get(after,72,85)==-1 and re.search(r'Group: 2 +Size: 21\b',text),(name,'stale-result phantom/absorbed force')
    if name=='zero-hq':
        assert cached==regen==0 and get(after,51+hq,81)==hq and re.search(r'Group: 2 +Size: '+str(hq)+r'\b',text),(name,'zero-bound stale result')
assert worlds['duplicate-pointer'][1]==worlds['hq-held'][1],'duplicate pointers changed conserved normalized outcome'

# Original MZ relocation-aware code byte observations.
header=struct.unpack_from('<H',exe,8)[0]*16;image=bytearray(exe[header:])
for i in range(struct.unpack_from('<H',exe,6)[0]):
    offset,segment=struct.unpack_from('<HH',exe,struct.unpack_from('<H',exe,24)[0]+4*i);at=segment*16+offset
    struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
ranges={'0x120ad':60,'0x127ce':81,'0x12a0c':51,'0x12b1f':62,'0x12d55':78,'0x12e13':79,'0x12331':173,'0x121ab':247,'0x12c15':128,'0x12e65':246,'0x1315f':135}
records=json.loads((ROOT/'research/yt-xannor-lifecycle/rea/phase-paths.json').read_text())['records']
assert len(records)==len(ranges) and {r['normalized_result']['address']for r in records}==set(ranges)
for r in records:
    v=r['normalized_result'];at=int(v['address'],16)-0x10000
    assert r['subject']['digest']['sha256']==sha(exe) and r['operation']=='read_bytes'
    assert v['complete'] and v['requested_bytes']==ranges[v['address']] and bytes.fromhex(v['bytes_hex'])==image[at:at+v['requested_bytes']]
# The reclaim threshold is an MBF64 250, not the misleading single-width zero.
raw=exe[0x8e30+0x8518-0x7e60:0x8e30+0x8518-0x7e60+8];mant=int.from_bytes(raw[:7],'little')
assert (1+(mant&((1<<55)-1))/2**55)*2.0**(raw[7]-129)==250


# Synthetic boundary checks describe the derived branches, not DOS RNG replay.
import importlib.util,sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('xannor_rules',ROOT/'research/yt-xannor-lifecycle/recovered_rules.py')
rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
assert [rules.regeneration(s,10000)for s in (100000,999999,1000000,1000500,10000000)]==[0,0,2000,2001,20000]
assert rules.creates_xannoron(0) and not rules.creates_xannoron(2) and not rules.creates_xannoron(100)
assert rules.attempts_reclaim(-2,1) and rules.attempts_reclaim(2,1) and not rules.attempts_reclaim(1,1) and not rules.attempts_reclaim(0,1)
assert rules.relocates(False,0,0) and rules.relocates(False,2000,2000) and not rules.relocates(False,2001,2000)
assert rules.relocates(True,1,2000) and not rules.relocates(True,0,2000)
assert rules.candidate_allowed(1,2,0) and not rules.candidate_allowed(2,2,0)
assert rules.candidate_allowed(2,-1,0) and rules.candidate_allowed(0,0,1) and not rules.candidate_allowed(0,0,2)
assert rules.reclaim_battle(251,251,lambda:0)==(251,0,2)
assert rules.reclaim_battle(251,251,lambda:.5)==(251,0,2)
assert rules.reclaim_battle(251,251,lambda:.500001)==(0,251,2)
assert rules.reclaim_battle(250,251,lambda:.5)==(250,0,251)
assert rules.shrinking_roll(0,4,lambda:0,21)==21
assert rules.shrinking_roll(1000,4,lambda:.5,21)==64

# Reuse the already preserved generic shrinking-bound helper observation.
prior=json.loads((ROOT/'research/yt-mercenary-maintenance/rea/phase-paths.json').read_text())['records']
helper=next(r for r in prior if r['normalized_result']['address']=='0x17939')
v=helper['normalized_result'];at=0x7939
assert helper['subject']['digest']['sha256']==sha(exe) and v['complete'] and v['requested_bytes']==159
assert bytes.fromhex(v['bytes_hex'])==image[at:at+159]
print(f'Verified {len(cases)-len(blocked)} completed Xannor lifecycle runs, {len(blocked)} bounded relocation stalls, exact two-day chains, provenance/state accounting and {len(records)} REA observations.')
