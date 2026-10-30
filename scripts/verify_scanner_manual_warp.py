"""Independently verify focused DOS scanner/warp evidence and its bounded claims."""
import argparse,gzip,hashlib,importlib.util,json,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--research',type=Path,default=ROOT/'research/yt-scanner-warp');a=p.parse_args();D=a.research/'dos'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(path):return json.loads(path.read_text())
def side(path):return json.loads(gzip.decompress(path.read_bytes()))
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
get=mbf.get
source=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
base=(source/'YTDATA.DAT').read_bytes()
assert sha(base)=='04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec'
assert gzip.decompress((D/'baseline.dat.gz').read_bytes())==base
raw=(D/'recipe.json').read_bytes()
assert sha(raw)=='da66c10029fbe63a30c302acee6ec520bb4819d833c5bed42ba9ebef4c4fbc7d','frozen declarations'
recipe=json.loads(raw);specs={c['name']:c for c in recipe['scenarios']};rows=read(D/'results.json')['scenarios']
assert len(rows)==len(specs)==41 and len({c['name']for c in rows})==41
assert {c['name']for c in rows}==set(specs)
bins={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in ('YT.EXE','BRUN30.EXE','LOCAL.EXE')};bins['KEYFEED.COM']=(ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
GRAPH={100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
worlds={};sides={};texts={}
# The manifest puts independent sessions before their linked reconnects.
for c in rows:
    n=c['name'];decl=specs[n];d=D/n
    assert c==read(d/'result.json')and all(c[k]==v for k,v in decl.items())
    assert c['complete']and not c['timed_out']and c['timeout_seconds']==150,'incomplete session'
    assert c['recipe']=='scanner-manual-warp-integration-v1'and c['baseline_sha256']==sha(base)
    assert c['binaries']=={n:sha(b)for n,b in bins.items()},'binary identity'
    keep={'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
    assert set(c['files'])==keep
    for f,h in c['files'].items():assert sha((d/f).read_bytes())==h,(n,f)
    assert '10/24/2026'in(d/'DOSDATE.LOG').read_text(),'DOS date'
    clock=re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)',(d/'DOSTIME.LOG').read_text());assert clock,'DOS clock'
    hour,minute,second,frac,ampm=clock.groups();actual=(int(hour)%12)+(12 if ampm=='pm'else 0)
    requested=list(map(int,c['time'].split(':')));target=requested[0]*3600+requested[1]*60+requested[2]
    observed=actual*3600+int(minute)*60+int(second)+int(frac)/(10**len(frac))
    assert abs(observed-target)<=.06,'DOS clock mismatch'
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(before)==len(after)==568687
    parent=c.get('parent')
    if parent:
        expected=bytearray(worlds[parent][1]);patches=[];initial=sides[parent]
    else:
        expected=bytearray(base);g={1:[2],2:[1]}if c.get('small')else GRAPH
        for sector,warps in g.items():
            at=(51+sector-1)*137;expected[at:at+137]=bytes(137)
            for o,v in zip(range(41,65,4),warps):mbf.put(expected,51+sector,o,v)
        patches=[[2,o,v]for o,v in {45:0,49:500,57:100,89:0,93:0,105:0,125:0}.items()]
        patches += [[3,o,v]for o,v in {45:0,57:103,61:42,53:7,89:0,125:0}.items()]
        patches += [[152,65,2],[3053,93,101],[153,93,2],[4053,73,0],[4053,77,12]]
        initial={f.name:f.read_bytes()for f in source.iterdir()if f.suffix.upper()in('.DAT','.ASC')and f.name!='YTDATA.DAT'}
    patches+=decl['patches'];assert c['applied_patches']==patches
    for r,o,v in patches:mbf.put(expected,r,o,v)
    assert before==expected,'undeclared setup or broken world chain'
    assert {n:bytes.fromhex(h)for n,h in side(d/'side-before.json.gz').items()}==initial,'auxiliary input chain'
    final={};aux=side(d/'sidefiles.json.gz');assert set(aux)==set(initial)
    for name,e in aux.items():
        final[name]=bytes.fromhex(e['hex']);assert e['before_sha256']==sha(initial[name])and e['after_sha256']==sha(final[name])
    sides[n]=final;worlds[n]=(before,after)
    keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+'\rQ;Y\r~~'*24).encode()
    assert(d/'KEYS.TXT').read_bytes()==keys,'exact input stream'
    text=(d/'transcript.txt').read_text();texts[n]=text
    assert 'Returning to Yankee Trader Local Logon Program...'in text,'normal quit'
    allowed={49,57,109}
    if n.startswith('shop-'):allowed|={81,93}
    if n in {'scanner-autopilot-first-yes','scanner-autopilot-second-yes','scanner-stacked-no-fresh-yes'}or 'mines'in n or n=='warp-landing-both':allowed|={53,93}
    # All actor bytes except explicit turn/position/score/purchase/damage fields
    # remain identical: no hidden equipment, cargo, credits or death mutation.
    x=bytearray(before[137:274]);y=bytearray(after[137:274])
    for o in allowed:x[o:o+4]=y[o:o+4]
    assert x==y,(n,'actor asset/death conservation')
    for r in range(3,52):
        x=bytearray(before[(r-1)*137:r*137]);y=bytearray(after[(r-1)*137:r*137]);x[109:113]=y[109:113]
        assert x==y,(n,'other player changed')
    for r in range(3052,4052):assert get(before,r,89)==get(after,r,89),(n,'port treasury changed')
    for r in range(4052,4152):assert get(before,r,117)==get(after,r,117),(n,'planet bank changed')
    if n.startswith('shop-'):
        bought=n in {'shop-exact','shop-above','shop-repeat'}
        spent=250000 if bought else 0
        assert get(after,2,81)==get(before,2,81)-spent,'scanner debit'
        assert get(after,2,93)==(-1 if bought else get(before,2,93)),'scanner installation'
        assert get(after,2,49)==get(before,2,49)-(0 if n=='shop-installed-use'else 1),'docking-only turns'
        assert get(after,2,57)==get(before,2,57)
        assert text.count('Danger Scanner installed in your ship!')==int(bought),'install receipt'
        if n in {'shop-repeat','shop-installed-poor','shop-reconnect'}:assert 'You already HAVE a Danger Scanner!'in text,'duplicate refusal'
        if n=='shop-below':assert 'You cannot afford a Danger Scanner!'in text,'poor refusal'
    if n.startswith('scanner-')or n=='shop-installed-use':
        if n=='scanner-invalid-nonadjacent':assert 'Danger Scanner has detected'not in text,'invalid destination scanned'
        else:
            target=2 if c.get('small')else(107 if 'second-'in n else 101)
            header=f'Danger Scanner has detected the following in sector {target}!'
            assert text.count(header)==text.count('Danger Scanner has detected')==1 and text.count('*** WARP DRIVE DEACTIVATED ***')==1,'warning count'
            assert text.count(f'Move into sector {target}? [y/N]')==1,'fresh prompt'
            mines=int(get(before,51+target,129));fighters=int(get(before,51+target,81))
            assert len(re.findall(r'[*][*] [0-9]+ SECTOR MINES! [*][*]',text))==int(mines>0),'mine warning count'
            if mines:assert text.count(f'** {mines} SECTOR MINES! **')==1,'mine warning quantity'
            assert len(re.findall(r'[*][*][*] [0-9]+ Fighters Belonging to ',text))==int(fighters>0),'fighter warning count'
            assert text.count('** Space-time disruption! **')==int(bool(c.get('small'))),'disruption warning count'
        if n in {'scanner-autopilot-first-yes','scanner-autopilot-second-yes','scanner-stacked-no-fresh-yes'}:
            target=107 if 'second-'in n else 101
            cost=2 if target==107 else 1
            assert (get(after,2,57),get(after,2,49))==(target,500-cost),'autopilot partial progress'
            assert get(after,51+target,129)==0 and get(after,2,53)<get(before,2,53),'accepted mine aftermath'
        elif n=='scanner-autopilot-second-no':assert (get(after,2,57),get(after,2,49))==(101,499)and get(after,158,129)==1,'declined second hop'
        elif n!='scanner-decline-then-warp':
            assert (get(after,2,57),get(after,2,49))==(get(before,2,57),get(before,2,49)),'declined travel changed position/turns'
            assert before[51*137:3051*137]==after[51*137:3051*137],'declined travel changed hazards'
        if n in {'scanner-combined','scanner-disruption-combined'}:
            assert text.index('SECTOR MINES! **')<text.index('100 Fighters Belonging to Enemy'),'warning order'
            if c.get('small'):assert text.index('** Space-time disruption! **')<text.index('SECTOR MINES! **'),'disruption order'
        if n in {'scanner-xannor','scanner-mercenary','scanner-human'}:
            label={'scanner-xannor':'The Xannor','scanner-mercenary':'Mercenaries','scanner-human':'Enemy'}[n]
            assert f'100 Fighters Belonging to {label}'in text,'NPC/human label'
    if n.startswith('warp-')or n=='scanner-decline-then-warp':
        assert get(after,2,81)==get(before,2,81),'warp charged credits'
        if n in {'warp-zero-turns','warp-reconnect-meltdown'}:
            assert (get(after,2,57),get(after,2,49))==(get(before,2,57),get(before,2,49))and '* EMERGENCY WARP ENGAGED! *'not in text,'zero-turn/reconnect warp'
        else:
            assert text.count('* EMERGENCY WARP ENGAGED! *')==1,'warp engagement'
            gauge=re.search(r'={32}\n\[([*]+)',text);assert gauge,'heat gauge'
            heat=len(gauge[1]);assert 0<=heat<=31
            assert 1<=get(after,2,57)<=3000
            if n in {'warp-meltdown','warp-meltdown-mines'}:assert heat==31,'expected meltdown branch'
            if heat==31:
                assert 'MELT DOWN!'in text and 'Your engines are disabled!'in text and 'It will take a solar day to repair them.'in text and get(after,2,49)==0,'meltdown accounting'
                assert f'You are stranded in sector {int(get(after,2,57))}.'in text,'meltdown destination receipt'
            else:
                match=re.search(r'sector (\d+)\. However, it takes you (\d+) turns to recharge',text);assert match,'warp recharge receipt'
                dest,cost=map(int,match.groups());assert dest==get(after,2,57)and cost==get(before,2,49)-get(after,2,49),'recharge receipt/state'
                assert min(get(before,2,49),4*heat)<=cost<=min(get(before,2,49),4*heat+3),'heat/recharge relationship'
        if n in {'warp-clear','warp-landing-mines','warp-landing-fighters','warp-landing-both','warp-landing-own','warp-installed-mines','warp-installed-fighters','warp-empty-exits'}:
            assert get(after,2,57)==60,'declared landing not reached'
        if n in {'warp-landing-mines','warp-landing-both','warp-installed-mines','warp-meltdown-mines'}:
            target=int(get(after,2,57))
            assert get(before,51+target,129)>0 and get(after,51+target,129)==0 and get(after,2,53)<get(before,2,53),'warp mine aftermath'
            assert '** WARNING! SECTOR HAS'in text and 'EXPLODE!'in text,'warp mine warning'
        if n.startswith('warp-installed-'):assert 'Danger Scanner has detected'not in text,'manual warp preflight'
        if n in {'warp-landing-fighters','warp-landing-both','warp-installed-fighters','warp-landing-own'}:
            assert get(after,111,81)==100 and get(after,111,85)==get(before,111,85),'warp changed deployed fighters'
            encounter='You have to defeat the fighters before you can enter this sector.'
            if n=='warp-landing-own':assert encounter not in text,'own fighters blocked arrival'
            else:assert encounter in text and 'Option? (A,B,D,I,Q,S,T,W,?=Help):?'in text,'hostile arrival encounter'
        if n=='warp-same-sector':assert get(after,2,57)==get(before,2,57)==2665,'same-sector landing'
        if n=='warp-avoided-landing':assert get(after,2,57)==881 and c['command']=='C;7;1;881;1;W;Y'and 'Sector 881 now locked out.'in text,'avoided-sector landing'
        if n=='warp-empty-exits':assert all(get(after,111,o)==0 for o in range(41,65,4)),'empty-exit landing'

# Recheck every retained native byte independently, with original MZ relocations.
def loaded(data):
    header=struct.unpack_from('<H',data,8)[0]*16;image=bytearray(data[header:])
    for i in range(struct.unpack_from('<H',data,6)[0]):
        off,seg=struct.unpack_from('<HH',data,struct.unpack_from('<H',data,24)[0]+4*i);at=seg*16+off
        struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
    return image
ranges={'0x11594':134,'0x11c3e':113,'0x17820':143,'0x16d3f':40,'0x17c2e':143,'0x1a470':19,'0x300de':998,'0x293e4':1084,'0x20ef9':34,'0x1081f':98}
records=read(a.research/'rea/yt.json')['records'];assert len(records)==10
image=loaded(bins['YT.EXE']);seen=set()
for e in records:
    v=e['normalized_result'];address=v['address'];count=ranges[address];seen.add(address)
    assert e['operation']=='read_bytes'and e['subject']['digest']['sha256']==sha(bins['YT.EXE'])
    assert v['complete']and v['requested_bytes']==v['returned_bytes']==count,'incomplete native bytes'
    at=int(address,16)-0x10000;assert bytes.fromhex(v['bytes_hex'])==image[at:at+count],'native bytes'
assert seen==set(ranges)
# Mathematical branch controls supplement, but do not replace, original execution.
model_spec=importlib.util.spec_from_file_location('encounters',ROOT/'research/yt-navigation/encounter_rules.py');model=importlib.util.module_from_spec(model_spec);model_spec.loader.exec_module(model)
assert model.emergency_warp(500,3000,lambda:0)==dict(heat=0,destination=1,cost=0,meltdown=False)
assert model.emergency_warp(500,3000,lambda:.99)==dict(heat=31,destination=2971,cost=500,meltdown=True)
print('Verified 41 completed scanner/manual-warp controls, exact world/auxiliary chains, purchases, queue boundaries, arrival aftermath and 10 complete native byte observations.')
