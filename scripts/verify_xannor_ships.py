"""Verify declared DOS ship encounters, cleanup, chronology and REA byte evidence."""
import argparse, gzip, hashlib, importlib.util, json, math, re, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--evidence',type=Path,default=ROOT/'research/yt-xannor-ships/dos')
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
for r,o,v in [(2,57,101),(2,125,0),(2,81,12345),(2,129,5)]:put(base,r,o,v)
base=bytes(base)
assert sha(base)=='ffa58f171db5efe4e325846346fa826daee4e35c0193a3ba666546ec9fd666ef'
assert gzip.decompress((a.evidence/'baseline.dat.gz').read_bytes())==base
raw=(a.evidence/'recipe.json').read_bytes()
assert sha(raw)=='c17a8a6dba81f62cf9f8a36a6ca5400e991aca47e78a58995c77bb7e5efaacb0','fixture declarations changed'
recipe=json.loads(raw);expected={c['name']:c for c in recipe['scenarios']}
assert recipe['recipe']=='xannor-ship-isolation-v1' and len(expected)==42
manifest=json.loads((a.evidence/'results.json').read_text())
assert manifest['recipe']==recipe['recipe'] and len(manifest['scenarios'])==42
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
    battle_lines=[line for line in t.splitlines()if ': lost'in line and 'Xannor ftrs dstrd'not in line]
    for line in battle_lines:assert line.strip()in news,(n,'public battle journal')
    worlds[n]=(b,v);logs[n]=t;sides[n]=side
    if not spec.get('parent'):
        assert 'Calculated Dynamic Xannor Regeneration is 0 fighters'in t,n
        assert [(int(g),int(f))for g,f in re.findall(r'Group: (\d+) +Size: (\d+)',t)]==[(2,int(get(b,151,81)))],(n,'isolated single mobile group')


def q(n,off):return get(worlds[n][1],2,off)
def force(v):return sum(get(v,r,81)for r in range(52,3052)if get(v,r,85)==-1)
def messages(n):
    raw=bytes.fromhex(sides[n]['YTRMSG.DAT']['hex'])if 'YTRMSG.DAT'in sides[n]else b''
    assert len(raw)%86==0,(n,'message record size')
    return [(get(raw[i:i+86],1,4),raw[i+12:i+84].decode('cp437').rstrip())for i in range(0,len(raw),86)]

# Every single encounter's logged human casualties must match saved fighters.
for n in expected:
    if expected[n].get('parent'):continue
    b,v=worlds[n];t=logs[n]
    hits=re.findall(r'\*\*\* ([QR]) : lost (\d+), dstrd (\d+)([^\n]*)',t)
    for actor in ('Q','R'):
        rec=2 if actor=='Q'else 3
        encounters=[(int(lost),int(kills),suffix)for who,lost,kills,suffix in hits if who==actor and 'Xannor ftrs dstrd'not in suffix]
        if not encounters:continue
        assert len(encounters)==1,n
        lost,kills,suffix=encounters[0]
        assert get(v,rec,61)==get(b,rec,61)-kills and 0<=kills<=get(b,rec,61),(n,'saved fighter casualties')
        assert get(v,rec,81)==get(b,rec,81) and get(v,rec,129)==get(b,rec,129),(n,'no salvage or carried-mine debit')
        assert get(v,rec,97)==get(b,rec,97),(n,'no missile retaliation')
        assert all(get(v,rec,off)==get(b,rec,off)for off in(65,69,73,77,113,121)),(n,'retained cargo and equipment')
        if kills:
            assert any(to==rec and text.startswith(f'Ha! We kilt {kills} of yoor fyterz')for to,text in messages(n)),(n,'private casualty delivery')
        if 'Player Killed'in suffix:
            assert get(v,rec,45)==-1 and get(v,rec,57)==0 and get(v,rec,61)==0,(n,'death identity and position')
            assert get(v,rec,53)==get(b,rec,53),(n,'DOS exhausted-shield persistence defect')
            assert any(to==rec and 'We kilt yoo'in text for to,text in messages(n)),(n,'private death delivery')
        else:
            assert 'Xannor Lost'in suffix and get(v,rec,45)==get(b,rec,45) and get(v,rec,57)==get(b,rec,57),(n,'surviving identity')
            saved=float(re.search(r'Shields: ([\d.]+)',suffix)[1])
            assert get(v,rec,53)==saved,(n,'saved surviving shields')
            if get(v,rec,61)>0:assert get(v,rec,53)==get(b,rec,53),(n,'fighters before shields')
        for to,text in messages(n):assert to in(2,3)and text,(n,'private message addressee')

safe={'no-ship','origin-ship','cloak-diagnostic-hidden'}|{f'cloak-one-{h:02}'for h in(0,4,8,12,16)}
for n in safe:
    b,v=worlds[n]
    assert ': lost'not in logs[n] and force(v)==101 and get(v,53,105)==1114,(n,'skipped encounter changed force')
    assert q(n,61)==1000 and q(n,53)==10000 and 'YTRMSG.DAT'not in sides[n],(n,'skipped ship changed')
assert ': lost'in logs['cloak-one-20'] and q('cloak-one-20',61)<1000,'valid full cloak can be intercepted'
for n in ('strong-ship','fighters-only','shields-only','hq-ship','cloak-0.33','cloak-0.66','no-missiles','many-missiles','dead-2','dead-3','dead--1'):
    b,v=worlds[n]
    assert force(v)==1 and get(v,53,105)==0,(n,'destroyed group cleared without force creation')
for n in ('no-missiles','many-missiles','dead-2','dead-3','dead--1','cloak-0.33','cloak-0.66'):
    assert q(n,61)==q('strong-ship',61)and q(n,53)==10000,(n,'non-damage fields changed battle')
for n in ('unarmed','weak-ship','fighters-499','fighters-5000','shields-500','shields-5001','staged-5000','two-unarmed'):
    b,v=worlds[n];loss=sum(int(x)for x in re.findall(r'\*\*\* [QR] : lost (\d+), dstrd',logs[n]))
    assert force(v)==force(b)-loss and get(v,53,105)==1114,(n,'post-victory group conservation')
assert get(worlds['weak-ship'][1],152,129)==0 and q('weak-ship',129)==5,'no wreck mine drop'
assert q('weak-ship',53)==1 and q('shields-500',53)==500 and q('shields-5001',53)==5001,'exhausted shields retained'
assert q('fighters-only',53)==0 and q('shields-only',61)==0 and 0<q('shields-only',53)<10000
assert q('fighters-500',61)in(0,500)and q('fighters-5000',61)%500==0,'fighter batch boundary'
assert q('fighters-5001',61)>=0 and ': lost 5001, dstrd 1'in logs['fighters-5001'],'large fighter then unit batch'
assert q('shields-5000',53)%500==0 and q('shields-500',45)==-1,'shield batch boundary'
assert ': lost'in logs['mines-before-ship'] and logs['mines-before-ship'].index('hit sector mines')<logs['mines-before-ship'].index('Q : lost'), 'mines before ship'
loss=int(re.search(r'Q : lost (\d+)',logs['mines-before-ship'])[1]);assert 1<=10000-loss<=1000,'mine and battle accounting'
assert q('defense-before-ship',61)==1000 and q('defense-before-ship',53)==10000 and not messages('defense-before-ship'),'sector defense precedes ship'
assert get(worlds['mines-after-loss'][1],153,129)==1 and get(worlds['mines-after-win'][1],153,129)==0,'post-battle route continuation'
for n in ('two-ships','two-ships-first-dead'):
    assert get(worlds[n][1],3,61)==1000 and 'R : lost'not in logs[n],'record-order survivor stopping'
assert logs['two-ships-first-unarmed'].index('Q : lost')<logs['two-ships-first-unarmed'].index('R : lost'),'record-order multiple encounters'
assert q('two-unarmed',45)==-1 and get(worlds['two-unarmed'][1],3,45)==-1
b,v=worlds['kill-assets']
assert get(b,3052,97)==2 and get(v,3052,97)==0 and get(v,3052,89)==0 and q('kill-assets',117)==0,'port release and treasury cleanup'
assert get(v,4053,73)==2,'planet title remains after NPC death'
assert get(b,351,81)==37 and get(b,351,85)==2 and '37 Mercenaries moving from sector 300'in logs['kill-assets'],'human defense became Mercenary before later Mercenary actions'
b,v=worlds['kill-team-captain']
assert get(v,2,89)==0 and get(v,3,89)==1 and get(v,52,109)==0 and get(v,52,117)==3 and get(v,52,77)==2,'team removal with stale captain'
assert get(v,52,105)==1114,'team fixture corrupted HQ pointer'
assert worlds['strong-next-day'][0]==worlds['strong-ship'][1],'broken exact-world chain'

# Complete REA records are checked against independently relocated MZ bytes.
header=struct.unpack_from('<H',exe,8)[0]*16;image=bytearray(exe[header:])
for i in range(struct.unpack_from('<H',exe,6)[0]):
    off,seg=struct.unpack_from('<HH',exe,struct.unpack_from('<H',exe,24)[0]+4*i);at=seg*16+off
    struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
ranges={'0x15811':675,'0x15ab4':512,'0x15cb4':576,'0x13b94':636,'0x16924':1792,'0x1052e':264,'0x16b24':228,'0x104b0':126,'0x19850':16,'0x19892':8,'0x192f0':4}
records=json.loads((ROOT/'research/yt-xannor-ships/rea/ship-paths.json').read_text())['records']
assert len(records)==len(ranges)and {r['normalized_result']['address']for r in records}==set(ranges)
for r in records:
    v=r['normalized_result'];at=int(v['address'],16)-0x10000
    assert r['operation']=='read_bytes'and r['subject']['digest']['sha256']==sha(exe)and v['complete']
    assert v['requested_bytes']==v['returned_bytes']==ranges[v['address']]and bytes.fromhex(v['bytes_hex'])==image[at:at+v['requested_bytes']]
def double(raw):
    m=int.from_bytes(raw[:7],'little');return (1+(m&((1<<55)-1))/2**55)*2**(raw[7]-129)
assert double(image[0x9850:0x9858])==5000 and double(image[0x9858:0x9860])==500 and double(image[0x9892:0x989a])==1
assert image[0x92f0:0x92f4]==b'\x00\x00\x00\x80'  # MBF single .5
spec=importlib.util.spec_from_file_location('rules',ROOT/'research/yt-xannor-ships/recovered_rules.py')
rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
assert [rules.batch(n,n)for n in(499,500,5000,5001)]==[1,500,500,5000]
threshold=.95-.33
assert not rules.detected(.95,threshold)and rules.detected(.95,threshold+.000001)
x=rules.battle(500,500,0,lambda:.5);assert x['killed']and x['group']==500 and x['human_lost']==500
x=rules.battle(500,500,0,lambda:.500001);assert not x['killed']and x['group']==0 and x['fighters']==500
x=rules.battle(500,0,500,lambda:.5);assert x['killed']and x['group']==500 and x['computed_shields']==0 and x['stored_shields']==500
x=rules.battle(500,0,500,lambda:.499999);assert not x['killed']and x['group']==0 and x['stored_shields']==500
x=rules.battle(5001,5001,0,lambda:.5);assert x['human_lost']==5001 and x['rounds']==2
print(f'Verified {len(expected)} completed Xannor ship runs, exact next-day chain, private/public aftermath, frozen declarations and {len(records)} REA observations.')
