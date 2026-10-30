"""Independently rebuild and verify preserved lottery/deletion DOS controls."""
import argparse,datetime,gzip,hashlib,importlib.util,json,math,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--research',type=Path,default=ROOT/'research/yt-maintenance-lottery')
a=p.parse_args();D=a.research/'dos';sha=lambda b:hashlib.sha256(b).hexdigest()


def get(data,r,o):
    raw=data[(r-1)*137+o:(r-1)*137+o+4];mant=int.from_bytes(raw[:3],'little')
    return 0 if not raw[3] else (-1 if mant&0x800000 else 1)*(1+(mant&0x7fffff)/2**23)*2.0**(raw[3]-129)


def put(data,r,o,v):
    raw=bytes(4)
    if v:
        f,e=math.frexp(abs(v));mant=round((f*2-1)*2**23)
        if mant==2**23:mant=0;e+=1
        raw=(mant|(0x800000 if v<0 else 0)).to_bytes(3,'little')+bytes([e+128])
    at=(r-1)*137+o;data[at:at+4]=raw


def clock(d,date,time):
    assert date in (d/'DOSDATE.LOG').read_text(),'actual DOS date'
    m=re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)',(d/'DOSTIME.LOG').read_text());assert m,'actual DOS clock'
    h,mi,s,f=map(int,m.groups()[:4]);v=(h%12+(12 if m[5]=='pm'else 0))*3600+mi*60+s+f/100
    assert abs((v-int(time[:2])*3600+43200)%86400-43200)<=1,'clock mismatch'


source=ROOT/'archive/analysis/dos-validation/evidence'
base=bytearray(gzip.decompress((ROOT/'research/yt-xannor-lifecycle/dos/baseline.dat.gz').read_bytes()))
assert sha(base)=='efcdeff0b353c2965e0874501941ec5c7c59c25aebe8cb9856da45d872a0d205'
template=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()[137:274]
base[137:274]=template
for off,v in {41:297,45:0,57:7,85:2,89:0,105:0,109:0,125:0}.items():put(base,2,off,v)
for s in range(8,3001):
    for off in (41,45,49,53,57,61):put(base,51+s,off,0)
assert sha(base)=='f33c07c40113b4c89b73acf9892fdeb54abb04d1c9694885d8fd4e54b920f339'
assert gzip.decompress((D/'baseline.dat.gz').read_bytes())==base
raw=(D/'recipe.json').read_bytes()
assert sha(raw)=='7134e217504933ceaa27014e3685be305ed2706985de3122f6adb5f28d0f0fd7','frozen declarations'
recipe=json.loads(raw);specs={c['name']:c for c in recipe['scenarios']};assert len(specs)==41
manifest=json.loads((D/'results.json').read_text());assert manifest['recipe']==recipe['recipe']=='maintenance-lottery-isolation-v1'
assert len(manifest['scenarios'])==41 and {c['name']for c in manifest['scenarios']}==set(specs)
bins={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in ('YTMAINT.EXE','BRUN30.EXE')}
assert [sha(b)for b in bins.values()]==['8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6','3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8']
worlds={};sides={};awards={};texts={};deleted={}
for c in manifest['scenarios']:
    n=c['name'];spec=specs[n];d=D/n
    assert c==json.loads((d/'result.json').read_text())
    assert all(c[k]==v for k,v in spec.items()),(n,'scenario declaration')
    assert c['recipe']==recipe['recipe'] and c['baseline_sha256']==sha(base)
    assert c['complete'] and not c['timed_out'] and c['timeout_seconds']==45,(n,'normal completion')
    assert c['executable_sha256']==sha(bins['YTMAINT.EXE']) and c['runtime_sha256']==sha(bins['BRUN30.EXE'])
    assert set(c['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','sidefiles.json','side-before.json','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
    for f,h in c['files'].items():assert sha((d/f).read_bytes())==h,(n,f)
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(before)==len(after)==4151*137
    assert sha(before)==c['before_sha256'] and sha(after)==c['after_sha256']
    rebuilt=bytearray(worlds[spec['parent']][1]if spec.get('parent')else base)
    if spec.get('all_players'):
        t=bytes(rebuilt[137:274])
        for r in range(2,52):
            rebuilt[(r-1)*137:r*137]=t;alias=('P'+str(r)+' ').encode()
            rebuilt[(r-1)*137:(r-1)*137+41]=alias.ljust(41,b' ');put(rebuilt,r,85,len(alias))
    if spec.get('empty_players'):
        for r in range(2,52):put(rebuilt,r,85,0)
    for r in range(2,52):
        if spec.get('player_death'):put(rebuilt,r,45,1)
        if spec.get('player_delete'):put(rebuilt,r,45,1);put(rebuilt,r,41,284)
        if spec.get('cloaked_players'):put(rebuilt,r,125,10)
    for r in range(4054,4150):
        if spec.get('dirty_slots'):
            for o,v in {41:111,89:222,57:11,61:12,65:13,69:3,125:7,129:37,113:5,117:55}.items():put(rebuilt,r,o,v)
        if spec.get('full_planets'):
            rebuilt[(r-1)*137:(r-1)*137+41]=b'Occupied'.ljust(41,b' ')
            for o,v in {41:298,85:8,77:1}.items():put(rebuilt,r,o,v)
    if spec.get('union_only'):
        for s in range(8,3001):
            if get(rebuilt,51+s,93)==0:put(rebuilt,51+s,93,2)
    if spec.get('cleanup') and not spec.get('parent'):
        rebuilt[274:411]=rebuilt[137:274];rebuilt[274:315]=b'R '.ljust(41,b' ')
        for r,o,v in [(2,89,1),(52,77,2),(52,109,2),(52,117,3),(52,121,2),(52,125,0),(2,105,77),(3,85,2),(3,45,2),(3,89,1),(53,93,2),(54,81,123),(54,85,2),(4053,73,2),(4053,77,99),(4053,117,0),(4053,129,37),(3052,97,2),(3052,101,444)]:put(rebuilt,r,o,v)
    for r,o,v in spec['patches']:put(rebuilt,r,o,v)
    assert before==rebuilt,(n,'undeclared mutation or broken world chain')
    initial={f.name:f.read_bytes()for f in source.iterdir()if f.suffix.upper()in('.DAT','.ASC')and f.name!='YTDATA.DAT'}
    if spec.get('parent'):initial=sides[spec['parent']].copy()
    elif spec.get('cleanup'):
        initial['YTNAME.DAT']=b'acct1,pw,Q,\r\nacct2,pw,Q,\r\nacct3,pw,R,\r\nother,pw,Other,User\r\n\x1a'
        msgs=[]
        for to,fr,body in [(2,3,b'TO Q'),(3,2,b'FROM Q'),(3,3,b'UNRELATED')]:
            row=bytearray(86)
            for o,v in [(0,1),(4,to),(8,fr)]:put(row,1,o,v)
            row[12:84]=body.ljust(72,b' ');msgs.append(bytes(row))
        initial['YTRMSG.DAT']=b''.join(msgs)
    assert {k:bytes.fromhex(v)for k,v in json.loads((d/'side-before.json').read_text()).items()}==initial,(n,'broken auxiliary provenance/chain')
    final=initial.copy()
    for name,r in json.loads((d/'sidefiles.json').read_text()).items():
        assert name in initial and r['before_sha256']==sha(initial[name])
        final[name]=bytes.fromhex(r['hex']);assert sha(final[name])==r['after_sha256']
    sides[n]=final
    date=spec.get('date','10/25/2026');time=spec.get('time','00:00:00')
    assert c['date']==date and c['time']==time;clock(d,date,time)
    day=(datetime.datetime.strptime(date,'%m/%d/%Y').date()-datetime.date(2026,1,1)).days+1
    assert get(after,1,81)==day,(n,'published maintenance day')
    t=(d/'transcript.txt').read_text();texts[n]=t;assert 'Daily Maintenance Completed OK'in t
    phases=['Compressing Message','Loading players','Running port maintenance','Running planet maintenance','Moving The Wanderer','Processing the Xannor','Mercenary Maintenance','Running Super Planet Lottery','Generating Updated Scoreboard','Daily Maintenance Completed OK']
    indices=[t.index(s)for s in phases];assert indices==sorted(indices),(n,'phase order')
    qnamed=get(before,2,85)!=0;cloak=get(before,2,125);normalized=1 if cloak<0 else cloak
    decayed=max(0,struct.unpack('<f',struct.pack('<f',normalized-.05000000074505806))[0])if normalized>0 else 0
    expired=qnamed and normalized>0 and decayed==0
    delete=qnamed and not expired and get(before,2,41)<=day-get(before,1,77) and get(before,2,45)!=0
    deleted[n]=delete
    third_deleted=bool(get(before,3,85) and get(before,3,41)<=day-get(before,1,77) and get(before,3,45)!=0)
    if spec.get('cleanup'):
        assert ('Q  deleted from game'in t)==delete,(n,'deletion eligibility/notice')
        assert get(after,2,85)==(0 if delete else get(before,2,85)),(n,'name activation')
        assert before[137:178]==after[137:178],(n,'stale alias bytes')
        if qnamed:assert abs(get(after,2,125)-decayed)<.000001,(n,'cloak decay')
        else:assert get(after,2,125)==get(before,2,125),(n,'unnamed cloak unchanged')
        assert get(after,2,89)==(0 if delete else get(before,2,89)),(n,'team membership')
        assert get(after,2,105)==(0 if delete else get(before,2,105)),(n,'auxiliary field')
        if delete:
            assert get(after,3,45)==-98,(n,'deleted killer attribution')
            assert get(after,4053,73)==0,(n,'planet release')
            assert get(after,54,81)==get(after,54,85)==0,(n,'sector release')
            assert [get(after,52,o)for o in (77,109,117,121)]==[2,0,0 if third_deleted else 3,0],(n,'roster vs captain')
            assert final['YTNAME.DAT']==(b''if third_deleted else b'acct3,pw,R,\r\n')+b'other,pw,Other,User\r\n\x1a',(n,'duplicate alias filtering')
        assert get(after,3052,97)==get(before,3052,97),(n,'Earth title retained')
        # Compression occurs before deletion, and preserves nonzero unread records only.
        radio=initial['YTRMSG.DAT'];expected=[]
        assert len(radio)%86==0
        for i in range(0,len(radio),86):
            row=bytearray(radio[i:i+86])
            if not get(row,1,0):continue
            row[84:86]=bytes(2)
            if (delete and 2 in (get(row,1,4),get(row,1,8))) or (third_deleted and 3 in (get(row,1,4),get(row,1,8))):put(row,1,0,0)
            expected.append(bytes(row))
        expected=b''.join(expected)
        assert final['YTRMSG.DAT'].startswith(expected),(n,'radio compression/deletion order')
        assert len(final['YTRMSG.DAT'])==len(expected)+(86 if expired else 0),(n,'private expiry count')
        if expired:
            mail=final['YTRMSG.DAT'][-86:]
            assert [get(mail,1,o)for o in (0,4,8)]==[1,2,-2] and b'Your cloaking energy ran out' in mail,(n,'private expiry attribution')
        assert (b'Q  deleted from game' in final['YTNEWS.DAT'])==delete,(n,'public deletion notice')
    wins=[r for r in range(4052,4152)if get(before,r,85)==0 and get(after,r,85)>0]
    assert len(wins)<=1,(n,'multiple lottery awards');awards[n]=wins
    assert ('won a PLANET in the SUPER LOTTERY'in t)==bool(wins),(n,'success notice')
    if wins:
        r=wins[0];owner=int(get(after,r,73));slot=r-4051
        assert 2<=owner<=51 and get(after,owner,85)!=0,(n,'winner eligibility')
        loc=[s for s in range(1,3001)if get(after,51+s,93)==slot];assert len(loc)==1
        sector=loc[0]
        # These isolated award fixtures have no earlier combat freeing a planet.
        assert get(before,51+sector,93)<=0,(n,'occupied lottery destination')
        for off in (57,61,65,69,125):assert get(after,r,off)==0,(n,'award stock reset',off)
        for off in (41,89,113,129):assert get(after,r,off)==get(before,r,off),(n,'reused slot retention',off)
        for off in (45,49,53):assert 0<=get(after,r,off)<3000,(n,'production range')
        assert 1<=get(after,r,77)<=100 and get(after,r,77)==int(get(after,r,77))
        assert 0<=get(after,r,117)<1000000
        alias=after[(owner-1)*137:(owner-1)*137+int(get(after,owner,85))]
        name=after[(r-1)*137:(r-1)*137+int(get(after,r,85))]
        assert name==alias+b"'s Planet",(n,'award name')
        mail=final['YTRMSG.DAT'][-86:]
        assert [get(mail,1,o)for o in (0,4,8)]==[1,owner,-2]
        assert b'You won a PLANET in the SUPER-LOTTERY!'in mail and str(sector).encode()in mail
        assert b'won a PLANET in the SUPER LOTTERY' in final['YTNEWS.DAT']
    else:
        assert 'No one won a planet today.'in t
        assert b'No one won a planet today.'not in final['YTNEWS.DAT']
    worlds[n]=before,after

for n in ('lottery-all-clock-0','lottery-all-clock-8','lottery-dirty-free-slots','lottery-all-dead-recent','lottery-cloaked-players','lottery-selected-sector-mined'):assert awards[n],(n,'positive control')
for n in ('lottery-all-clock-4','lottery-empty-players','lottery-full-planets','lottery-all-dead-old','lottery-selected-player-empty','lottery-selected-sector-occupied','lottery-union-only'):assert not awards[n],(n,'negative control')
assert all(get(worlds['lottery-all-dead-old'][1],r,85)==0 for r in range(2,52))
assert get(worlds['lottery-all-dead-recent'][1],int(get(worlds['lottery-all-dead-recent'][1],awards['lottery-all-dead-recent'][0],73)),45)==1
assert get(worlds['lottery-selected-sector-mined'][1],2216,129)==5,'lottery did not clear minefield'
assert get(worlds['inactive-rich-planet'][1],4053,77)==100,'cleanup precedes bank-funded growth'
for n in ('inactive-port-live','inactive-port-deleted'):
    assert [get(worlds[n][1],3053,o)for o in (89,97)]==[9,2],'ordinary port title/treasury retention'
assert not deleted['inactive-year-end'] and deleted['inactive-year-start'],'year-boundary cutoff'
assert len(sides['inactive-deleted-next-day']['YTRMSG.DAT'])==86,'next-run physical radio deletion'
r=awards['lottery-dirty-free-slots'][0]
assert get(worlds['lottery-dirty-free-slots'][1],r,41)==111 and get(worlds['lottery-dirty-free-slots'][1],r,129)==37
assert get(worlds['lottery-next-day'][1],r,41)==299 and get(worlds['lottery-next-day'][1],r,129)>40000,'stale timestamp catch-up'
assert 'Maintenance not needed!'in texts['lottery-same-day'] and worlds['lottery-same-day'][0]!=worlds['lottery-same-day'][1],'legacy same-day fallthrough'

# Verify loaded MZ byte observations independently, including relocation fixups.
def image(exe):
    u=lambda off:struct.unpack_from('<H',exe,off)[0]
    out=bytearray(exe[u(8)*16:])
    for i in range(u(6)):
        off,seg=struct.unpack_from('<HH',exe,u(24)+i*4);at=seg*16+off
        struct.pack_into('<H',out,at,(struct.unpack_from('<H',out,at)[0]+0x1000)&65535)
    return out

bundle=json.loads((a.research/'rea/target-paths.json').read_text());assert len(bundle['observations'])==18
expected_ranges={'player-load':(0x104f9,700),'deletion-cleanup':(0x16c0d,1073),'alias-cleanup':(0x17039,284),'lottery':(0x15371,1117),'phase-entry':(0x10000,400),'cutoff-config':(0x10200,761),'random-bound':(0x178f3,240),'mail-writer':(0x17d0b,173),'config-fields':(0x100a0,217),'completion-score':(0x15773,94),'runtime-sign-zero':(0x1ac1e,70),'runtime-float-compare':(0x1a82c,180),'runtime-multiply':(0x1b440,220),'runtime-saved-float':(0x11e5b,50),'runtime-alias-compare':(0x19e1f,50),'message-compression':(0x1672d,426),'day-conversion':(0x179e3,803),'phase-prefix':(0x10389,368)}
assert {o['name']for o in bundle['observations']}==set(expected_ranges)
for o in bundle['observations']:
    e=o['evidence'];n=e['normalized_result'];exe=bins['BRUN30.EXE'if o['name'].startswith('runtime-')else'YTMAINT.EXE']
    assert e['subject']['digest']['sha256']==sha(exe) and e['operation']=='read_bytes'
    address,length=expected_ranges[o['name']]
    assert n['complete'] and int(n['address'],16)==address and n['requested_bytes']==n['returned_bytes']==length
    assert bytes.fromhex(n['bytes_hex'])==image(exe)[address-0x10000:address-0x10000+length],o['name']
spec=importlib.util.spec_from_file_location('model',ROOT/'research/yt-maintenance-lottery/recovered_rules.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model);model.check_model()
print('Verified 41 normally completed DOS controls, exact world/auxiliary chains, 18 native REA records and executable rule boundaries.')
