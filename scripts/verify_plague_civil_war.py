"""Independently verify declared DOS event controls, semantics and native bytes."""
import argparse,gzip,hashlib,importlib.util,json,math,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--research',type=Path,default=ROOT/'research/yt-plague-civil-war');a=p.parse_args();D=a.research/'dos'
sha=lambda b:hashlib.sha256(b).hexdigest()


def get(data,r,o):
    raw=data[(r-1)*137+o:(r-1)*137+o+4];m=int.from_bytes(raw[:3],'little')
    return 0 if not raw[3]else(-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/2**23)*2.0**(raw[3]-129)


def put(data,r,o,v):
    raw=bytes(4)
    if v:
        f,e=math.frexp(abs(v));m=round((f*2-1)*2**23)
        if m==2**23:m=0;e+=1
        raw=(m|(0x800000 if v<0 else 0)).to_bytes(3,'little')+bytes([e+128])
    at=(r-1)*137+o;data[at:at+4]=raw


def close(v,w,label):assert math.isclose(v,w,rel_tol=2e-6,abs_tol=.02),(label,v,w)
def label(b,r):return b[(r-1)*137:(r-1)*137+int(get(b,r,85))].decode('cp437').strip()
def field(b,r):return {o:get(b,r,o)for o in range(41,130,4)}

def clock(d,date,time):
    assert date in(d/'DOSDATE.LOG').read_text(),'actual DOS date'
    m=re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)',(d/'DOSTIME.LOG').read_text());assert m,'actual DOS clock'
    h,mi,s,f=map(int,m.groups()[:4]);v=(h%12+(12 if m[5]=='pm'else 0))*3600+mi*60+s+f/100
    assert abs((v-int(time[:2])*3600+43200)%86400-43200)<=1,'DOS clock mismatch'

spec=importlib.util.spec_from_file_location('event_model',ROOT/'research/yt-plague-civil-war/recovered_rules.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model);model.check_model()
spec=importlib.util.spec_from_file_location('economy',ROOT/'archive/analysis/yt-maint/recovered_rules.py');economy=importlib.util.module_from_spec(spec);spec.loader.exec_module(economy)
source=ROOT/'archive/analysis/dos-validation/evidence'
base=bytearray(gzip.decompress((ROOT/'research/yt-xannor-lifecycle/dos/baseline.dat.gz').read_bytes()))
assert sha(base)=='efcdeff0b353c2965e0874501941ec5c7c59c25aebe8cb9856da45d872a0d205'
for r in range(3052,4052):
    for o,v in {45:298,49:10,53:10,57:10,61:1,65:1,69:1,73:-50,77:50,81:-50,89:0,97:0,101:0}.items():put(base,r,o,v)
for o,v in {41:298,45:1000,49:1000,53:1000,57:0,61:0,65:0,69:11,73:0,77:100,89:0,113:13,117:0,125:17,129:7}.items():put(base,4053,o,v)
put(base,53,93,2)
for sector in range(8,3001):
    for off in (41,45,49,53,57,61):put(base,51+sector,off,0)
assert sha(base)=='ad34a8f17e91395a5456f797f27fff4d4d636159b3257314ca4a2f4fa2f83ac7'
assert gzip.decompress((D/'baseline.dat.gz').read_bytes())==base
raw=(D/'recipe.json').read_bytes();assert sha(raw)=='38dc23bbf48d83e2da8e1271d31e5adae3e2ccb3a414fbb5b82aff2d6a45023b','frozen declarations'
recipe=json.loads(raw);specs={c['name']:c for c in recipe['scenarios']};assert len(specs)==56
manifest=json.loads((D/'results.json').read_text());assert manifest['recipe']==recipe['recipe']=='plague-civil-war-isolation-v1'
assert len(manifest['scenarios'])==56 and {c['name']for c in manifest['scenarios']}==set(specs)
bins={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in ('YTMAINT.EXE','BRUN30.EXE')}
assert [sha(b)for b in bins.values()]==['8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6','3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8']
worlds={};sides={};texts={};all_events={};port_counts={}
for c in manifest['scenarios']:
    n=c['name'];spec=specs[n];d=D/n
    assert c==json.loads((d/'result.json').read_text()) and all(c[k]==v for k,v in spec.items())
    assert c['recipe']==recipe['recipe']and c['baseline_sha256']==sha(base)
    assert c['complete']and not c['timed_out']and c['timeout_seconds']==45,(n,'normal completion')
    assert c['executable_sha256']==sha(bins['YTMAINT.EXE'])and c['runtime_sha256']==sha(bins['BRUN30.EXE'])
    assert set(c['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','sidefiles.json','side-before.json','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
    for f,h in c['files'].items():assert sha((d/f).read_bytes())==h,(n,f)
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
    assert len(before)==len(after)==4151*137 and sha(before)==c['before_sha256']and sha(after)==c['after_sha256']
    rebuilt=bytearray(worlds[spec['parent']][1]if spec.get('parent')else base)
    if not spec.get('parent'):
        minutes=int(spec.get('time','00:00:00')[:2])*60
        for r in range(3052,4052):put(rebuilt,r,101,minutes)
        for r in range(4052,4152):put(rebuilt,r,89,minutes)
    if spec.get('human'):
        rebuilt[137:274]=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()[137:274]
        for o,v in {41:297,45:0,57:1,85:2,89:0,109:0,125:0}.items():put(rebuilt,2,o,v)
    for r,name in spec.get('names',[]):
        rebuilt[(r-1)*137:(r-1)*137+41]=name.encode().ljust(41,b' ');put(rebuilt,r,85,len(name))
    for r,o,v in spec['patches']:put(rebuilt,r,o,v)
    assert before==rebuilt,(n,'undeclared setup or broken world chain')
    initial=sides[spec['parent']].copy()if spec.get('parent')else{f.name:f.read_bytes()for f in source.iterdir()if f.suffix.upper()in('.DAT','.ASC')and f.name!='YTDATA.DAT'}
    assert{k:bytes.fromhex(v)for k,v in json.loads((d/'side-before.json').read_text()).items()}==initial,(n,'auxiliary provenance/chain')
    final=initial.copy()
    for name,r in json.loads((d/'sidefiles.json').read_text()).items():
        assert name in initial and r['before_sha256']==sha(initial[name]);final[name]=bytes.fromhex(r['hex']);assert sha(final[name])==r['after_sha256']
    assert final['YTYNEWS.DAT']==initial['YTNEWS.DAT'],(n,'daily public journal rotation')
    sides[n]=final
    date=spec.get('date','10/25/2026');time=spec.get('time','00:00:00')
    assert c['date']==date and c['time']==time;clock(d,date,time)
    text=(d/'transcript.txt').read_text();texts[n]=text
    phases=['Running port maintenance','Running planet maintenance','Moving The Wanderer','Processing the Xannor','Mercenary Maintenance','Running Super Planet Lottery','Daily Maintenance Completed OK']
    positions=[text.index(t)for t in phases];assert positions==sorted(positions),(n,'phase order')
    public=' '.join(final['YTNEWS.DAT'].decode('cp437').split())
    # Inspect every ordinary port, including Earth. Draw-free gate is determined
    # from independently reconstructed post-growth/promoted production.
    count=0;selected=0
    for r in range(3052,4052):
        f=field(before,r);g=field(after,r);delta=model.elapsed(f[45],f[101],g[45],g[101])
        stocks,rates=model.port_growth([f[o]for o in (49,53,57)],[f[o]for o in (61,65,69)],delta)
        hit=model.s(model.s(rates[0]+rates[1])+rates[2])>1000000
        count+=hit;actual=[g[o]for o in (61,65,69)]
        for i,(old,new)in enumerate(zip(rates,actual)):
            if hit and old>500:assert 500-.02<=new<old+500+.02,(n,'port plague rate',r,i,old,new)
            else:close(new,old,(n,'port unchanged rate',r,i))
        want=[min(v,model.s(10*p))if hit else v for v,p in zip(stocks,actual)]
        for off,v in zip((49,53,57),want):close(g[off],v,(n,'port cargo cap/growth',r,off))
        chosen=4-int(g[41]);assert chosen in (1,2,3),(n,'port commodity type',r)
        greatest=max(want)
        if greatest<=0:assert chosen==selected,(n,'zero-stock stale selection',r)
        else:
            # Saved MBF cargo hides internal double distinctions near a tie.
            # Demand actual dominance beyond the documented rounding tolerance.
            assert greatest-want[chosen-1]<=max(.02,abs(greatest)*2e-6),(n,'port commodity selection',r)
            selected=chosen
        signs=[abs(f[o])if i==selected else-abs(f[o])for i,o in enumerate((73,77,81),1)]
        assert[g[o]for o in (73,77,81)]==signs,(n,'port commodity signs',r)
        assert g[97]==f[97]and g[89]==f[89],(n,'port title/treasury')
    observed=re.findall(r'(\d+) ports contracted the plague',text)
    assert observed==([str(count)]if count else[]),(n,'port public count',observed,count)
    if count:assert f'{count} ports contracted the plague'in public,(n,'missing public port count')
    port_counts[n]=count
    # Match each public event to its own active planet; no positional log guesses.
    segment=text[text.index('Running planet maintenance'):text.index('Moving The Wanderer')]
    headers=list(re.finditer(r'(A PLAGUE|CIVIL WAR) has struck planet (.*?) as a result of overcrowding!',segment))
    events={}
    for i,m in enumerate(headers):
        name=m[2].strip();assert name not in events
        events[name]=(m[1],segment[m.start():headers[i+1].start()if i+1<len(headers)else len(segment)])
    all_events[n]=events;spent_memory=0;visited=set()
    # Slots1/99/100 have later Wanderer/faction repairs; only the isolated
    # ordinary probes2/3/4 establish economic/event writeback here.
    for r in range(4053,4056):
        f=field(before,r);g=field(after,r)
        if not f[85]:
            # No named player can create a lottery planet in the inactive probe control.
            if n=='planet-inactive'and r==4053:assert before[(r-1)*137:r*137]==after[(r-1)*137:r*137],(n,'inactive planet changed')
            continue
        name=label(before,r)
        pre,delta=economy.update_planet(f,g[41],g[89]);rates=[model.s(pre[o])for o in (45,49,53)];ground=model.s(pre[77]);bank=model.s(pre[117])
        for off in (69,113,125,129):close(g[off],pre[off],(n,'event changed weapon stock',r,off))
        assert g[73]==f[73]and g[85]==f[85]and before[(r-1)*137:(r-1)*137+41]==after[(r-1)*137:(r-1)*137+41],(n,'event changed title/name',r)
        if name not in events:
            for off,v in zip((45,49,53),rates):close(g[off],v,(n,'unannounced rate change',r,off))
            close(g[77],ground,(n,'unannounced ground change',r));close(g[117],bank,(n,'unannounced bank change',r))
            for off in (57,61,65):close(g[off],pre[off],(n,'unannounced stock change',r,off))
            continue
        visited.add(name);kind,block=events[name]
        assert f'{kind} has struck planet {name} as a result of overcrowding!'in public,(n,'missing public planet event',name)
        if kind=='A PLAGUE':assert sum(rates)>100000,(n,'impossible plague gate')
        else:assert ground>1000000,(n,'impossible civil gate')
        new=[g[o]for o in (45,49,53)]
        for old,v in zip(rates,new):assert 0<=v<=old*(1+2e-6)+.02,(n,'planet damage range',r,old,v)
        assert 0<=g[77]<=ground*(1+2e-6)+.02,(n,'ground damage range',r)
        for off,v,rate in zip((57,61,65),[pre[o]for o in (57,61,65)],new):close(g[off],min(v,model.s(10*rate)),(n,'planet warehouse cap',r,off))
        if kind=='A PLAGUE':close(g[117],bank,(n,'plague bank debit',r))
        else:
            assert 0<=g[117]<=bank,(n,'civil bank bounds',r);spent_memory=bank-g[117]
        debit=re.findall(r'(\S+) credits were spent putting down the insurrection!',block)
        assert len(debit)==(1 if spent_memory else 0),(n,'insurrection report/reset',name)
        if debit:close(float(debit[0]),spent_memory,(n,'stale expenditure attribution',name))
        summary=re.search(r'Productivity reduced from\s*(\S+) units to\s*(\S+) units!',block);assert summary,(n,'productivity summary')
        close(float(summary[1]),sum(rates),(n,'pre-event productivity',r));close(float(summary[2]),sum(new),(n,'reported productivity',r))
        summary=re.search(r'Ground forces reduced from\s*(\S+) to\s*(\S+) units!',block)
        required=math.floor(ground)>0 and math.floor(ground)!=math.floor(g[77])
        assert bool(summary)==required,(n,'required ground report',r)
        if summary:
            close(float(summary[1]),math.floor(ground),(n,'reported original ground',r));close(float(summary[2]),math.floor(g[77]),(n,'reported remaining ground',r))
        assert ' '.join(block.split())in public,(n,'missing public event body',name)
    assert final['YTNEWS.DAT'].count(b'has struck planet')==len(events),(n,'current public event count')
    assert visited==set(events),(n,'event for inactive/unknown planet')
    # No private plague/civil message is produced even for the named human owner.
    radio=final['YTRMSG.DAT']
    assert not any(s in radio for s in (b'PLAGUE',b'CIVIL WAR',b'insurrection',b'Productivity')),(n,'unexpected private event')
    worlds[n]=before,after

assert port_counts['port-earth']==1 and port_counts['port-three']==3
assert port_counts['port-total-999999']==port_counts['port-total-1000000']==port_counts['port-cargo-only']==0
assert port_counts['port-total-1000001']==1
assert get(worlds['port-rate-499'][1],3053,61)==499 and get(worlds['port-rate-500'][1],3053,61)==500
assert get(worlds['port-rate-501'][1],3053,61)>501,'near-cutoff production increase'
assert sum(get(worlds['port-one-pass'][1],3053,o)for o in(61,65,69))>1000000 and port_counts['port-one-pass']==1,'single pass only'
for n,kind in [('port-selection-1',3),('port-selection-2',3),('port-selection-3',2),('port-selection-4',1)]:assert get(worlds[n][1],3053,41)==kind,(n,'captured commodity tie/winner')
assert get(worlds['port-zero-after-1'][1],3053,41)==3 and get(worlds['port-zero-after-3'][1],3053,41)==1,'stale zero-stock selector'
for hour in (0,4,8):
    assert all_events['planet-plague-clock-'+str(hour)]['Probe Planet'][0]=='A PLAGUE'
    assert all_events['planet-civil-clock-'+str(hour)]['Probe Planet'][0]=='CIVIL WAR','civil-only native control'
    assert all_events['planet-both-clock-'+str(hour)]['Probe Planet'][0]=='CIVIL WAR','civil override'
for n in ('planet-ground-0','planet-ground-1','planet-ground-999999','planet-ground-1000000','planet-ground-1000001','planet-rate-boundary','planet-inactive'):assert not all_events[n],(n,'negative native control')
for n in ['planet-owner-'+str(o)for o in(0,2,-1,-2)]+['planet-unprotected','planet-stock-cap']:assert all_events[n]['Probe Planet'][0]=='A PLAGUE',(n,'owner/protection native control')
for mode,kinds in [('direct',['CIVIL WAR','A PLAGUE']),('quiet',['CIVIL WAR','A PLAGUE']),('zero-civil',['CIVIL WAR','CIVIL WAR','A PLAGUE']),('reverse',['A PLAGUE','CIVIL WAR'])]:assert [kind for kind,_ in all_events['planet-order-'+mode].values()]==kinds,(mode,'native event order')
assert get(worlds['planet-owner-0'][1],4053,77)%1!=0,'fractional ground retained'
for n in ('planet-order-direct','planet-order-quiet'):
    assert get(worlds[n][1],4055,117)==12345 and texts[n].count('credits were spent putting down the insurrection!')==2,'stale report without second debit'
assert texts['planet-order-zero-civil'].count('credits were spent putting down the insurrection!')==1,'zero-bank civil resets stale expenditure'
assert 'Maintenance not needed!'in texts['planet-same-day']and worlds['planet-same-day'][0]!=worlds['planet-same-day'][1],'same-day fallthrough'
assert get(worlds['planet-civil-clock-8'][1],4053,89)<get(worlds['planet-civil-clock-8'][0],4053,89),'captured clock quantization'
assert get(worlds['planet-civil-clock-8'][1],4053,77)>get(worlds['planet-civil-clock-8'][0],4053,77),'post-growth versus input ground'

# Relocate original MZ bytes independently, then compare the complete retained ranges.
def image(exe):
    u=lambda off:struct.unpack_from('<H',exe,off)[0];out=bytearray(exe[u(8)*16:])
    for i in range(u(6)):
        off,seg=struct.unpack_from('<HH',exe,u(24)+i*4);at=seg*16+off
        struct.pack_into('<H',out,at,(struct.unpack_from('<H',out,at)[0]+0x1000)&65535)
    return out
ranges={'port-load-growth':(0x107b2,902),'port-plague-cap-selection':(0x10b38,1039),'port-public-count':(0x10f47,126),'planet-input':(0x10fc5,332),'planet-production-event-gates':(0x113cc,845),'planet-event-damage-bank':(0x11719,513),'planet-public-private-reports':(0x1191a,552),'planet-save':(0x11b42,382),'runtime-single-subtract':(0x1b359,65),'runtime-double-subtract':(0x1ad81,90),'runtime-comparison':(0x1a818,180),'runtime-floor':(0x1acb2,180),'runtime-multiply':(0x1b440,220),'runtime-sign-tests':(0x1ac1e,70),'runtime-single-stack':(0x11e5b,60),'runtime-array-load':(0x1c324,190),'port-constants':(0x18086,24),'phase-start':(0x10389,368)}
bundle=json.loads((a.research/'rea/target-paths.json').read_text());assert len(bundle['observations'])==len(ranges)==18 and{o['name']for o in bundle['observations']}==set(ranges)
for o in bundle['observations']:
    e=o['evidence'];r=e['normalized_result'];name=o['name'];address,length=ranges[name];exe=bins['BRUN30.EXE'if name.startswith('runtime-')else'YTMAINT.EXE']
    assert e['subject']['digest']['sha256']==sha(exe)and e['operation']=='read_bytes'
    assert r['complete']and int(r['address'],16)==address and r['requested_bytes']==r['returned_bytes']==length
    assert bytes.fromhex(r['bytes_hex'])==image(exe)[address-0x10000:address-0x10000+length],(name,'native bytes')
print('Verified 56 completed DOS controls, exact world/auxiliary chains, event/economic semantics, static boundaries and 18 complete native observations.')
