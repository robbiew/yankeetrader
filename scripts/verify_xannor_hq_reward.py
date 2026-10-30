"""Independently verify original HQ credit rewards, chains, reports and native bytes."""
import argparse,gzip,hashlib,importlib.util,json,math,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--research',type=Path,default=ROOT/'research/yt-xannor-hq-reward');a=p.parse_args();D=a.research/'dos'
sha=lambda b:hashlib.sha256(b).hexdigest()


def get(data,r,o):
    raw=data[(r-1)*137+o:(r-1)*137+o+4];m=int.from_bytes(raw[:3],'little')
    return 0 if not raw[3]else(-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/2**23)*2.0**(raw[3]-129)


def put(data,r,o,v):
    if not v:raw=bytes(4)
    else:
        f,e=math.frexp(abs(v));m=round((f*2-1)*2**23)
        if m==2**23:m=0;e+=1
        raw=(m|(0x800000 if v<0 else 0)).to_bytes(3,'little')+bytes([e+128])
    at=(r-1)*137+o;data[at:at+4]=raw


def clock(d,expected):
    assert '10/24/2026'in(d/'DOSDATE.LOG').read_text(),'DOS date'
    m=re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)',(d/'DOSTIME.LOG').read_text());assert m,'DOS clock'
    h,mi,s,f=map(int,m.groups()[:4]);value=(h%12+(12 if m[5]=='pm'else 0))*3600+mi*60+s+f/100
    want=sum(int(v)*n for v,n in zip(expected.split(':'),(3600,60,1)))
    assert abs(value-want)<=1,'DOS clock mismatch'

source=ROOT/'archive/analysis/yt-combat/experiments/surrender-xannor'
base=(source/'before.dat').read_bytes();assert sha(base)=='cd1f9d5e99ef1d251fbbe9196ebeb21a8e401d6765419a2c7157ff729ed1cfb6'
assert gzip.decompress((D/'baseline.dat.gz').read_bytes())==base
raw=(D/'recipe.json').read_bytes();assert sha(raw)=='a70aa0f2ea6d4e2db0b8638df12fdeff7738c0d650486b32268e166622e4518e','frozen declarations'
recipe=json.loads(raw);specs={c['name']:c for c in recipe['scenarios']};manifest=json.loads((D/'results.json').read_text())
assert len(specs)==len(manifest['scenarios'])==38 and {c['name']for c in manifest['scenarios']}==set(specs)
assert recipe['recipe']==manifest['recipe']=='xannor-hq-reward-v1'
s=importlib.util.spec_from_file_location('rules',ROOT/'research/yt-xannor-hq-reward/recovered_rules.py');rules=importlib.util.module_from_spec(s);s.loader.exec_module(rules);rules.check_model()
bins={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in('YT.EXE','BRUN30.EXE','LOCAL.EXE','XANNORHQ.TXT')};bins['KEYFEED.COM']=(ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
assert {n:sha(b)for n,b in bins.items()}=={'YT.EXE':'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037','BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8','LOCAL.EXE':'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a','XANNORHQ.TXT':'72719e94dc04c655d7239e76f824b79ae6846e0f48c62148d48b9b07b9e694df','KEYFEED.COM':'06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596'}
worlds={};sides={};rewards={};transcripts={}
for c in manifest['scenarios']:
    n=c['name'];spec=specs[n];d=D/n
    assert c==json.loads((d/'result.json').read_text()) and all(c[k]==v for k,v in spec.items())
    assert c['recipe']==recipe['recipe'] and c['baseline_sha256']==sha(base)
    assert c['complete'] and not c['timed_out'] and c['timeout_seconds']==spec.get('timeout_seconds',60),'normal completion'
    assert c['date']=='10/24/2026'and c['time']==spec.get('time','00:00:00');clock(d,c['time'])
    assert c['binaries']=={n:sha(b)for n,b in bins.items()}
    assert set(c['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
    for f,h in c['files'].items():assert sha((d/f).read_bytes())==h,(n,f)
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(before)==len(after)==4151*137 and sha(before)==c['before_sha256'] and sha(after)==c['after_sha256']
    parent=spec.get('parent');rebuilt=bytearray(worlds[parent][1]if parent else base)
    patches=[(1,117,spec['hq']),(72,105,0),(151,81,0),(151,85,0),(152,81,0),(152,85,0),(51+spec['target'],81,spec['defenders']),(51+spec['target'],85,spec['owner']),(2,97,100),(2,113,10)]
    if spec.get('no_setup'):patches=[]
    initial=sides[parent].copy()if parent else{f.name:f.read_bytes()for f in source.iterdir()if f.suffix.upper()in('.DAT','.ASC')and f.name!='YTDATA.DAT'}
    if spec['actor']==3:
        patches += [(3,o,get(rebuilt,2,o))for o in range(41,130,4)if o not in(81,85)]+[(3,57,100),(3,81,765432),(3,85,6)]
        initial['YTNAME.DAT']=b'Dummy,Dummy,Dummy,Dummy\r\nTester,,Enemy,\r\n\x1a'
    if spec.get('team'):
        at=51*137;rebuilt[at:at+41]=b'Reward Team'.ljust(41,b' ');rebuilt[at+113:at+117]=b'TST1'
        patches += [(2,89,1),(3,89,1),(52,73,11),(52,77,spec['actor']),(52,109,2),(52,117,3),(52,121,0),(52,125,0)]
    patches+=spec['patches']
    assert c['applied_patches']==[list(v)for v in patches],'patch declaration'
    for r,o,v in patches:put(rebuilt,r,o,v)
    assert before==rebuilt,(n,'undeclared setup or broken world chain')
    assert {k:bytes.fromhex(v)for k,v in json.loads(gzip.decompress((d/'side-before.json.gz').read_bytes())).items()}==initial,(n,'auxiliary input chain')
    final={};rows=json.loads(gzip.decompress((d/'sidefiles.json.gz').read_bytes()));assert set(rows)==set(initial)
    for name,row in rows.items():
        final[name]=bytes.fromhex(row['hex']);assert row['before_sha256']==sha(initial[name])and row['after_sha256']==sha(final[name])
    action=('A;'+str(spec['amount']))if spec['action']=='fighter'else('!'if spec['action']=='missile'else'+')+';'+str(spec.get('destination',spec['target']))+';'+str(spec['amount'])
    if spec['action']=='none':action='Q;Y'
    keys=b'\r~~~~~\r~'+action.encode()+(b'\r'+b'~'*55+b'Q;Y\r~~~\r~~~~~\r'if spec.get('pause_auto')else b'\r~~~\r~~~Q;Y\r~~~\r')
    assert(d/'KEYS.TXT').read_bytes()==keys,'exact input stream'
    text=(d/'transcript.txt').read_text();transcripts[n]=text
    assert 'Returning to Yankee Trader Local Logon Program...'in text,'normal logout'
    actor=spec['actor'];target=51+spec['target'];prior=get(before,target,85);force=get(before,target,81);left=get(after,target,81)
    attempted=spec['action']!='none'and spec['amount']>0 and not(spec['action']=='missile'and spec['amount']>get(before,actor,97))
    reward=rules.eligible(spec['action'],force,left,prior,spec['target'],get(before,1,117),attempted)
    # The named controls must actually exercise their intended victory/negative.
    victory=spec['action']!='none'and spec['defenders']==1 and spec['amount']>0 and n!='missile-insufficient'and not(spec['action']=='missile'and prior==actor)
    if victory:assert left==0,(n,'intended victory did not occur')
    if 'partial'in n:assert left>0,(n,'partial fixture destroyed target')
    receipt='Collect 1,000,000 credits bonus!'
    assert text.count(receipt)==int(reward),(n,'reward gate/receipt')
    expected=rules.legacy_reward(get(before,actor,81))if reward else get(before,actor,81)
    assert get(after,actor,81)==expected,(n,'credit reward arithmetic/receipt without money',get(before,actor,81),get(after,actor,81),expected)
    for other in range(2,52):
        if other!=actor:assert get(before,other,81)==get(after,other,81),(n,'reward changed another account')
    for r in range(4052,4152):assert get(before,r,117)==get(after,r,117),(n,'reward changed planetary bank')
    for r in range(3052,4052):assert get(before,r,89)==get(after,r,89),(n,'reward changed port treasury')
    assert get(after,72,105)==(actor if reward else get(before,72,105)),(n,'revenge recipient/order')
    if reward:
        assert text.index('[PAUSE]')<text.index(receipt)<text.index('Generating ScoreBoard'),(n,'reward timing')
        assert left==0 and get(after,target,85)==0,(n,'reward before force removal')
    alias=before[(actor-1)*137:(actor-1)*137+int(get(before,actor,85))].decode('cp437').strip()
    marker='Congratulations go to '+alias+' who defeated the Xannor HQ!!!'
    old=' '.join(initial['YTNEWS.DAT'].decode('cp437').split());new=' '.join(final['YTNEWS.DAT'].decode('cp437').split())
    assert new.count(marker)-old.count(marker)==int(reward),(n,'new public reward announcement')
    assert final['YTNEWS.DAT'].startswith(initial['YTNEWS.DAT'].rstrip(b'\x1a')),(n,'public append provenance')
    def broadcast_messages(mail):
        assert len(mail)%86==0
        messages=[]
        for at in range(0,len(mail),86):
            row=mail[at:at+86];body=' '.join(row[12:].decode('cp437').split())
            if body==marker:assert get(row,1,4)==get(row,1,8)==-2,(n,'broadcast address')
            if get(row,1,4)==get(row,1,8)==-2:messages.append(body)
        return messages
    oldmail=broadcast_messages(initial['YTRMSG.DAT']);newmail=broadcast_messages(final['YTRMSG.DAT'])
    expected_mail=oldmail+(['*'*74,marker,'*'*74]if reward else[])
    assert newmail==expected_mail,(n,'fresh three-message broadcast block')
    worlds[n]=before,after;sides[n]=final;rewards[n]=reward

assert rewards['fighter-hq']and rewards['missile-hq']and rewards['plasma-hq']
assert rewards['plasma-mercenary']and rewards['plasma-human']and rewards['plasma-own'],'plasma owner-guard defect'
assert not any(rewards[n]for n in ('fighter-human','fighter-mercenary','missile-human','missile-mercenary','missile-own','fighter-away','missile-away','plasma-away','fighter-empty','missile-empty','plasma-empty','fighter-abort','missile-insufficient'))
assert rewards['missile-route']and rewards['plasma-route'],'encounter vs requested destination'
assert not rewards['reconnect-no-repeat']and rewards['restored-hq-repeat'],'repeat per new victory'
assert rewards['fighter-actor3']and get(worlds['fighter-actor3'][1],3,81)==1765432,'current player recipient'
assert rewards['fighter-existing-queue']and get(worlds['fighter-existing-queue'][1],72,105)==2,'existing queue is not a reward latch'

# Every retained byte is checked independently with the MZ loader's relocations.
def loaded(data):
    header=struct.unpack_from('<H',data,8)[0]*16;image=bytearray(data[header:])
    for i in range(struct.unpack_from('<H',data,6)[0]):
        off,seg=struct.unpack_from('<HH',data,struct.unpack_from('<H',data,24)[0]+4*i);at=seg*16+off
        struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
    return image
ranges={'reward':('YT.EXE','0x29bfe',472),'credit-helper':('YT.EXE','0x23f87',70),'fighter-gate':('YT.EXE','0x111ee',156),'missile-gate':('YT.EXE','0x266b0',176),'plasma-gate':('YT.EXE','0x2a430',133),'pause-helper':('YT.EXE','0x2891d',97),'million-constant':('YT.EXE','0x36ea8',4),'fighter-before-gate':('YT.EXE','0x11170',126),'plasma-positive-entry':('YT.EXE','0x2a217',57),'runtime-dispatch':('BRUN30.EXE','0x1038d',396),'runtime-floor':('BRUN30.EXE','0x1acb2',180),'runtime-single-add':('BRUN30.EXE','0x1b369',316)}
observations=json.loads((a.research/'rea/target-paths.json').read_text())['observations'];assert len(observations)==len(ranges)and {o['name']for o in observations}==set(ranges)
images={name:loaded(data)for name,data in bins.items()if name.endswith('.EXE')}
for o in observations:
    name,address,count=ranges[o['name']];e=o['evidence'];v=e['normalized_result']
    assert e['subject']['digest']['sha256']==sha(bins[name])and e['operation']=='read_bytes'
    assert v['address']==address and v['complete']and v['requested_bytes']==v['returned_bytes']==count
    at=int(address,16)-0x10000;assert bytes.fromhex(v['bytes_hex'])==images[name][at:at+count],('native bytes',o['name'])
assert struct.unpack_from('<H',images['BRUN30.EXE'],0x38d+0x81*2)[0]==0xb369
assert bins['YT.EXE'][0x27ca8:0x27cac]==bytes.fromhex('00247494')
print('Verified 38 completed DOS reward controls, exact world/auxiliary chains, eligibility, precision, recipient/report semantics and 12 complete byte observations.')
