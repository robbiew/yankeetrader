"""Verify original-DOS mobile fixtures, semantic accounting and REA byte evidence."""
import argparse, gzip, hashlib, importlib.util, json, math, re, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--evidence', type=Path, default=ROOT/'research/yt-xannor-mobile/dos')
args = p.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()


def get(data, record, offset):
    raw = data[(record-1)*137+offset:(record-1)*137+offset+4]
    mant = int.from_bytes(raw[:3], 'little')
    return 0 if not raw[3] else (-1 if mant & 0x800000 else 1) * (1+(mant & 0x7fffff)/2**23) * 2.0**(raw[3]-129)


def put(data, record, offset, value):
    raw = bytes(4)
    if value:
        fraction, exponent = math.frexp(abs(value))
        mant = round((fraction*2-1)*2**23)
        if mant == 2**23: mant = 0; exponent += 1
        raw = (mant | (0x800000 if value < 0 else 0)).to_bytes(3, 'little') + bytes([exponent+128])
    at = (record-1)*137+offset
    data[at:at+4] = raw


def force(data):
    return sum(get(data, r, 81) for r in range(52, int(get(data, 1, 57))+1) if get(data, r, 85) == -1)


def ptr(data, group=2):
    return int(get(data, 51+group, 105))


def groups(text):
    return [(int(g), int(q)) for g,q in re.findall(r'Group: (\d+) +Size: (\d+)', text)]


def regeneration(text):
    return int(re.search(r'Calculated Dynamic Xannor Regeneration is (\d+) fighters', text)[1])


seed = gzip.decompress((ROOT/'research/yt-xannor-lifecycle/dos/baseline.dat.gz').read_bytes())
assert sha(seed) == 'efcdeff0b353c2965e0874501941ec5c7c59c25aebe8cb9856da45d872a0d205'
assert sha((ROOT/'archive/analysis/dos-validation/evidence/YTDATA.DAT').read_bytes()) == 'a5cc0a7a06909d156802a4bcd55d5971d8b0472d03686a2fad4b9b4b406b1f59'
player = (ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
base = bytearray(seed); base[137:274] = player[137:274]
for r,o,v in [(2,41,297),(2,45,0),(2,57,7),(2,89,0),(2,109,4000),(2,125,10),(1165,81,1),(53,105,100),(151,81,100),(151,85,-1)]: put(base,r,o,v)
for sector,to in [(100,101),(101,1114)]:
    for off in (41,45,49,53,57,61): put(base,51+sector,off,to if off == 41 else 0)
base = bytes(base)
small = bytearray(seed[:51*137]+seed[51*137:72*137]+seed[3051*137:3072*137]+seed[4051*137:4151*137])
for r,o,v in [(1,57,72),(1,61,93),(1,93,193),(1,117,8)]: put(small,r,o,v)
for sector in range(1,22):
    for off in (41,45,49,53,57,61,81,85,93,105,129): put(small,51+sector,off,0)
    put(small,51+sector,41,sector%21+1); put(small,51+sector,45,(sector+19)%21+1)
for r,o,v in [(53,93,1),(54,93,99),(59,93,100),(59,81,10000),(59,85,-1),(52,105,8),(72,93,2),(95,73,-1)]: put(small,r,o,v)
for group,sector in enumerate([s for s in range(1,21) if s != 8],2):
    put(small,51+group,105,sector); put(small,51+sector,81,100); put(small,51+sector,85,-1)
small = bytes(small)
assert sha(base) == '601337e3cc2776bc6edb2faac04e055e0eaddd959dff57122c0c262df5aabbe0'
assert sha(small) == '5998b5d50d13ee124707960dec761d9cbad420247404e6ff9f216ed3eef06029'
for name,data in [('baseline',base),('small-baseline',small)]:
    assert gzip.decompress((args.evidence/(name+'.dat.gz')).read_bytes()) == data
recipe_raw = (args.evidence/'recipe.json').read_bytes()
assert sha(recipe_raw) == 'f83c76bd9b84e7de9d769967fae3d3e8c17b48787cc7c6476c8c57f4b86a9997', 'fixture declarations changed'
recipe = json.loads(recipe_raw)
expected = {c['name']: c for c in recipe['scenarios']}
assert recipe['recipe'] == 'xannor-mobile-isolation-v1' and len(expected) == 47
manifest = json.loads((args.evidence/'results.json').read_text())
assert manifest['recipe'] == recipe['recipe'] and len(manifest['scenarios']) == 47
assert {c['name'] for c in manifest['scenarios']} == set(expected)
exe = (ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
runtime = (ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
assert sha(exe) == '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
assert sha(runtime) == '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
worlds = {}; logs = {}
for c in manifest['scenarios']:
    name = c['name']; spec = expected[name]; d = args.evidence/name
    assert c == json.loads((d/'result.json').read_text()), name
    assert all(c[k] == v for k,v in spec.items()), (name,'declared setup')
    assert set(c) == set(spec) | {'recipe','baseline_sha256','before_sha256','after_sha256','executable_sha256','runtime_sha256','date','time','timed_out','timeout_seconds','complete','files'}, name
    baseline = small if spec.get('small_groups') else base
    assert c['recipe'] == recipe['recipe'] and c['baseline_sha256'] == sha(baseline), name
    assert c['executable_sha256'] == sha(exe) and c['runtime_sha256'] == sha(runtime), name
    assert c['complete'] and not c['timed_out'] and c['timeout_seconds'] == 45, name
    assert c['date'] == spec.get('date','10/25/2026') and c['time'] == spec.get('time','00:00:00'), name
    assert set(c['files']) == {'before.dat.gz','after.dat.gz','transcript.txt','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}, name
    for file,digest in c['files'].items(): assert sha((d/file).read_bytes()) == digest, (name,file)
    before = gzip.decompress((d/'before.dat.gz').read_bytes()); after = gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(before) == len(after) == len(baseline) and sha(before) == c['before_sha256'] and sha(after) == c['after_sha256'], name
    rebuilt = bytearray(worlds[spec['parent']][1] if spec.get('parent') else baseline)
    if spec.get('full_groups'):
        for group in range(3,21):
            for r,o,v in [(51+group,105,200+group),(251+group,81,100),(251+group,85,-1)]: put(rebuilt,r,o,v)
    for r,o,v in spec.get('patches',[]): put(rebuilt,r,o,v)
    assert before == bytes(rebuilt), (name,'undeclared input or broken exact-world chain')
    assert c['date'] in (d/'DOSDATE.LOG').read_text(), name
    observed = re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)',(d/'DOSTIME.LOG').read_text())
    assert observed, name
    h,m,s,f = map(int,observed.groups()[:4]); actual=(h%12+(12 if observed[5]=='pm' else 0))*3600+m*60+s+f/100
    assert abs((actual-int(c['time'][:2])*3600+43200)%86400-43200) <= 1, (name,'captured DOS clock')
    text = (d/'transcript.txt').read_text(); assert 'Daily Maintenance Completed OK' in text, name
    worlds[name] = before,after; logs[name] = text

route_names = set(expected) - {n for n,s in expected.items() if s.get('full_groups') or s.get('small_groups') or s.get('parent') or n.startswith('split-')}
for name in route_names:
    before,after = worlds[name]; text=logs[name]
    assert regeneration(text) == 0 and groups(text) == [(2,int(get(before,151,81)))], name
    assert ptr(after,1) == 1114 and all(ptr(after,g) == 0 for g in range(3,21)), name
safe = {'return-empty','mines-origin','defense-xannor-unpointed','defense-unowned','planet-xannor','planet-origin','path-protected-transit','protected-mines','path-branch-reversed','path-shorter-second','path-direct-first','path-unreachable'}
for name in safe:
    before,after=worlds[name]; text=logs[name]
    destination=100 if name=='path-unreachable' else 1114
    assert ptr(after) == destination and get(after,51+destination,81) == (100 if destination==100 else 101), (name,'route endpoint/force')
    assert force(after) == force(before), (name,'friendly force lost/created')
    assert 'hit sector mines' not in text and 'attacked the planet' not in text and ': lost' not in text, name
    if name=='path-unreachable': assert 'Sector path not found - from sector 100 to sector  1114' in text and get(after,1165,81)==1
for name,sector in [('mines-origin',100),('path-direct-first',101),('path-branch-reversed',101),('path-shorter-second',101)]:
    assert get(worlds[name][1],51+sector,129)==3, (name,'unvisited/protected mines consumed')
assert get(worlds['protected-mines'][1],58,129)==0, 'early Union mine cleanup was not preserved'
assert worlds['protected-mines'][1]==worlds['path-protected-transit'][1], 'Union cleanup changed otherwise identical complete-world outcome'
for name,owner in [('defense-xannor-unpointed',-1),('defense-unowned',0)]:
    assert get(worlds[name][1],152,81)==50 and get(worlds[name][1],152,85)==owner, name
fatal = {'mines-hop-small':101,'mines-hq':1114,'path-branch-order':101,'mines-before-defense':101,'mines-before-planet':101}
for name,sector in fatal.items():
    before,after=worlds[name];text=logs[name]
    assert ptr(after)==0 and get(after,51+sector,129)==2 and get(after,1165,81)==1, (name,'fatal-mine accounting')
    assert 'The Xannor were killed!' in text and 'hit sector mines' in text, name
    assert ': lost' not in text and 'attacked the planet' not in text, name
    if name=='mines-before-defense': assert get(after,152,81)==100000 and get(after,152,85)==2
    if name=='mines-before-planet': assert get(after,4053,77)==500000 and get(after,4053,129)==37
before,after=worlds['mines-hop-large'];loss=int(re.search(r'Lost a total of (\d+) fighters',logs['mines-hop-large'])[1])
assert 3<=loss<=3000 and get(after,152,129)==0 and ptr(after)==1114 and get(after,1165,81)==100001-loss
for name in ['defense-merc','defense-human','defense-human-strong','battle-500','battle-5000','battle-5001','defense-before-planet']:
    before,after=worlds[name];text=logs[name]
    match=re.search(r': lost (\d+), dstrd (\d+) \((Plyr ftrs dstrd|Xannor ftrs dstrd)\)',text);assert match,name
    lost,killed=map(int,match.groups()[:2]);a=get(before,151,81);d=get(before,152,81)
    assert 0<=lost<=a and 0<=killed<=d and (lost==a or killed==d),name
    assert get(after,152,81)==d-killed,name
    assert get(after,152,85)==(0 if killed==d else get(before,152,85)),name
    assert ptr(after)==(0 if lost==a else 1114) and get(after,1165,81)==1+a-lost,name
    if name=='battle-500': assert (lost,killed) in [(0,500),(500,0)]
    if name=='battle-5000': assert lost%500==killed%500==0
    if name=='defense-before-planet': assert 'attacked the planet' not in text and get(after,4053,77)==500000 and get(after,4053,129)==37
for name in ['planet-neutral','planet-human','protected-planet','planet-stops-before-later-mines','defense-then-planet']:
    before,after=worlds[name];text=logs[name]
    assert ptr(after)==0 and get(after,1165,81)==1 and 'attacked the planet "Probe Planet"' in text and 'Xannor fighters destroyed!' in text,name
    assert get(after,4053,85)==12 and 0<=get(after,4053,77)<=500000 and get(after,4053,129)==37,name
    if name=='planet-stops-before-later-mines':assert get(after,153,129)==3
    if name=='defense-then-planet':assert text.index('Plyr ftrs dstrd')<text.index('attacked the planet') and get(after,152,81)==0
before,after=worlds['planet-zero-ground'];text=logs['planet-zero-ground']
assert ptr(after)==1114 and get(after,152,93)==get(after,4053,85)==0 and 'Planet "Probe Planet" destroyed!' in text
assert get(after,4053,129)==37, 'deleted record retained stock is not recovered loot'
for name in [n for n in expected if n.startswith('split-')]:
    before,after=worlds[name];text=logs[name];seq=groups(text)
    assert regeneration(text)==0 and seq[0]==(2,int(get(before,151,81))),name
    assert [g for g,q in seq]==list(range(2,2+len(seq))),name
    balance=get(before,1165,81);score=get(before,2,109)
    for group,amount in seq[1:]:
        assert balance>=score/2000 and 1<=amount<=balance,(name,group,'allocation threshold/bound')
        balance-=amount
    if seq[-1][0]<20:assert balance<score/2000,(name,'premature allocation stop')
    assert force(after)==force(before),(name,'split created/lost force')
    if name in ['split-score-1999','split-score-2000']:assert seq==[(2,100),(3,1)]
    if name=='split-score-2001':assert seq==[(2,100)] and get(after,1165,81)==101
for name in [n for n,s in expected.items() if s.get('full_groups')]:
    before,after=worlds[name];text=logs[name]
    assert regeneration(text)==0 and groups(text)==[(g,100) for g in range(2,21)] and get(after,1165,81)==1000000,name
    hunt='Group 20 will hunt for Q' in text
    if name in ['top-threshold-below','top-hidden','top-cloak-one-00']:assert not hunt,name
    if name in ['top-threshold-equal','top-protected','top-cloak-one-04','top-cloak-one-08']:assert hunt,name
    if name=='top-threshold-equal':assert ptr(after,20)==0 and 'Q : lost 100' in text[text.index('Group: 20'):]
    if name=='top-protected':assert ptr(after,20)>=8 and 'Q : lost' not in text
# This sample isolates ship-loss output retaining sector250 below the special hunt threshold.
before,after=worlds['top-threshold-below'];text=logs['top-threshold-below']
for group in range(3,20):
    block=text.split(f'Group: {group} ')[1].split('Group:')[0]
    assert 'Q : lost 100' in block and ptr(after,group)==0,('sticky pursuit result',group)
assert ptr(after,20)>7 and ptr(after,20)!=250
assert ptr(worlds['top-hidden'][1],3)==250 and 'Q : lost' not in logs['top-hidden']
for name in ['preferred-sparse','preferred-no-probe']:
    before,after=worlds[name];seq=groups(logs[name]);ids=[g for g,q in seq]
    assert ids==sorted(ids) and set(ids)==set(range(2,21)) and len(ids)>19,name
    assert all(ptr(after,g)==0 or ptr(after,g)>=8 for g in range(1,21)),name
before,after=worlds['return-next-day'];assert before==worlds['return-empty'][1]
locations={ptr(before,g)for g in range(1,21)if ptr(before,g)>0}
normalized=sum(get(before,51+s,81)for s in locations if get(before,51+s,85)==-1)
assert normalized==101 and ptr(before,1)==ptr(before,2)==1114
score=get(before,2,109);regen=math.floor(score/500)if normalized<=math.floor(score/100)else 0
assert regeneration(logs['return-next-day'])==regen and force(after)==101+regen,'chained duplicate pointers inflated force'

# Complete inline Evidence is verified against the original MZ after relocations.
header=struct.unpack_from('<H',exe,8)[0]*16;image=bytearray(exe[header:])
for i in range(struct.unpack_from('<H',exe,6)[0]):
    offset,segment=struct.unpack_from('<HH',exe,struct.unpack_from('<H',exe,24)[0]+4*i);at=segment*16+offset
    struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
ranges={'0x1311e':267,'0x131e6':393,'0x133ee':145,'0x12fb1':36,'0x12567':354,'0x134eb':87,'0x1384d':131,'0x13a97':164,'0x13c90':416,'0x171af':281,'0x172f6':245,'0x178f3':243,'0x17522':367,'0x17776':370,'0x13e30':300,'0x19850':16,'0x19892':8,'0x19394':8,'0x19202':8,'0x13b94':252,'0x15da4':143,'0x10419':113}
records=json.loads((ROOT/'research/yt-xannor-mobile/rea/phase-paths.json').read_text())['records']
assert len(records)==len(ranges) and {r['normalized_result']['address']for r in records}==set(ranges)
for r in records:
    v=r['normalized_result'];at=int(v['address'],16)-0x10000
    assert r['operation']=='read_bytes' and r['subject']['digest']['sha256']==sha(exe) and v['complete']
    assert v['requested_bytes']==v['returned_bytes']==ranges[v['address']] and bytes.fromhex(v['bytes_hex'])==image[at:at+v['requested_bytes']]
def mbf64(raw):
    mant=int.from_bytes(raw[:7],'little');return (1+(mant&((1<<55)-1))/2**55)*2**(raw[7]-129)
assert mbf64(image[0x9850:0x9858])==5000 and mbf64(image[0x9858:0x9860])==500 and mbf64(image[0x9892:0x989a])==1
spec=importlib.util.spec_from_file_location('mobile_rules',ROOT/'research/yt-xannor-mobile/recovered_rules.py');rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
assert rules.allocate(1,1999,lambda:0)==(0,1) and rules.allocate(1,2000,lambda:0)==(0,1) and rules.allocate(1,2001,lambda:0)==(1,0)
assert rules.allocate(1000,0,lambda:.5)==(936,64) and rules.allocate(0,0,lambda:0,21)==(-21,21)
assert not rules.preferred_candidate(1,2,0) and rules.preferred_candidate(2,2,0) and not rules.preferred_candidate(2,-1,0)
assert rules.preferred_candidate(0,0,2) and not rules.preferred_candidate(0,0,1)
assert not rules.preferred_candidate(0,0,0,.5,.5) and rules.preferred_candidate(0,0,0,.5,.5001)
assert rules.destination(2,100,250,200,False,100,0,1114)==250
assert rules.destination(20,100,250,200,False,100,0,1114)==200
assert rules.destination(16,100,250,200,True,100,0,1114)==200
assert rules.destination(20,100,250,200,False,1,4000,1114)==1114
assert rules.hunting(2500000,0,0) and not rules.hunting(2499999,0,0) and not rules.hunting(2500000,10,.999)
assert [rules.defense_batch(n,n)for n in [499,500,5000,5001]]==[1,500,500,5000]
assert rules.defense_battle(500,500,lambda:.5)==(500,0,1)
assert rules.defense_battle(500,500,lambda:.50001)==(0,500,1)
assert rules.defense_battle(5001,5001,lambda:.5)==(5001,0,2)
rolls=[]
assert rules.mine_pass(2,3,lambda:rolls.append(1)or 0)==(0,1,2) and len(rolls)==3
print(f'Verified {len(expected)} completed Xannor mobile runs, exact next-day chain, frozen declarations, semantic accounting and {len(records)} REA observations.')
