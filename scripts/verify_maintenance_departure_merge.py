"""Independent departure fixture, exact handoff and friendly-force evidence audit.

No capture writer or maintenance replay model is imported. Raw captured clocks
are authenticated individually; changed outputs remain observations, not repairs.
"""
import argparse
import collections
import copy
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import shlex
import math
import struct

import verify_maintenance_placement as placement
import verify_maintenance_clock_matrix as clocks
from verify_rng_clock import read_date,read_time

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/departure-merge-controls'
PINS_SHA='7a54595bfed7291f09e0f249a87023bce449fd1d16bcd30f77b3fca1cea1c129'
PARENT_SOURCE=dict(corpus='evolved-combat-controls',profile='route-mercenary-100000',stage='child-2',pins='fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5')
CASES={
 'vacant-origin':dict(occupied=False,friendly=0,clock='00:00:00'),
 'friendly-merge':dict(occupied=False,friendly=37,clock='00:00:00'),
 'occupied-midnight':dict(occupied=True,friendly=0,clock='00:00:00'),
 'occupied-second-two':dict(occupied=True,friendly=0,clock='00:00:02'),
 'occupied-second-four':dict(occupied=True,friendly=0,clock='00:00:04'),
 'occupied-friendly-midnight':dict(occupied=True,friendly=37,clock='00:00:00'),
 'occupied-friendly-second-two':dict(occupied=True,friendly=37,clock='00:00:02'),
 'occupied-friendly-second-four':dict(occupied=True,friendly=37,clock='00:00:04'),
}
SHA=lambda b:hashlib.sha256(b).hexdigest()
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
PROFILES={name:(('11/05/2026',case['clock']),('11/06/2026',case['clock']))for name,case in CASES.items()}
GATEWAY=dict(origin=3000,successor=2368,slot=3,name='Departure Cache',redirects=[[2996,45],[2998,49],[2999,53]],day=308,minute=0,ground=500000,rates=[0,0,0],bank=0,stock=37,backlink_offset=45)
STAGES=('child-1','child-2')
SOURCES={'recover_maintenance_departure_merge.py','recover_maintenance_departure_merge_flush.py','verify_maintenance_clock_neutral.py','capture_maintenance_clock_neutral.mjs','observe_maintenance_placement.js','capture_maintenance_departure.mjs','observe_maintenance_departure.js'}
RECEIPT_PROFILE='occupied-friendly-second-four'
DIAGNOSTICS=ROOT/'research/yt-maint/departure-merge-diagnostics'
DIAGNOSTICS_SHA='0bc0e2d64b84741e0821fab41fbe553dc29861677ab22b24082828ed7db0306e'
COMMON=placement.COMMON
field=placement.field
rawfield=placement.rawfield
encode=placement.encode


def schedule(profile,stage):
    assert profile in PROFILES and stage in STAGES,'independent declared profile/stage'
    date,clock=PROFILES[profile][STAGES.index(stage)]
    return datetime.datetime.strptime(date,'%m/%d/%Y').date(),clock


def source_day(date):
    assert type(date)is datetime.date and 2026<=date.year<=2027,'bounded retained source calendar'
    return(date-datetime.date(2026,1,1)).days+1


def parent_inputs(profile,mode):
    assert profile in CASES and mode in MODES,'independently declared fixture/mode'
    parent=PARENT_SOURCE;root=ROOT/'research/yt-maint'/parent['corpus']
    raw=(root/'pins.json').read_bytes();assert SHA(raw)==parent['pins'],'immutable parent corpus manifest'
    pins=json.loads(raw)['files'];result={}
    for name in FILES:
        relative=parent['profile']+'/'+parent['stage']+'/'+mode+'/after-'+name+'.gz';compressed=(root/relative).read_bytes()
        assert SHA(compressed)==pins[relative],'immutable per-mode original parent file'
        result[name]=gzip.decompress(compressed)
    return result


def fixture_inputs(profile,mode):
    """Reconstruct the complete one-time intervention without writer imports."""
    result=parent_inputs(profile,mode);world=bytearray(result['YTDATA.DAT']);case=CASES[profile]
    def put(record,offset,value):
        at=(record-1)*137+offset;world[at:at+4]=encode(value)
    for offset in range(41,65,4):put(3051,offset,2368)
    for sector,offset in((2996,45),(2998,49),(2999,53)):put(51+sector,offset,2368)
    put(2419,45,3000)
    put(2419,81,case['friendly']);put(2419,85,-2 if case['friendly']else 0)
    put(3051,81,97337);put(3051,85,-2)
    record=4054;at=(record-1)*137;world[at:at+137]=b'Departure Cache'.ljust(41,b' ')+bytes(96)
    for offset,value in((41,308),(73,0),(77,500000),(85,15),(89,0),(117,0),(129,37)):put(record,offset,value)
    put(3051 if case['occupied']else 3050,93,3)
    graph_world=bytes(world)
    graph={sector:[int(field(graph_world,51+sector,off))for off in range(41,65,4)if field(graph_world,51+sector,off)>0]for sector in range(1,3001)}
    assert set(graph[3000])=={2368},'source departure has one forced first successor'
    assert {sector for sector,targets in graph.items()if 3000 in targets}=={2368},'only source predecessor reaches sector3000'
    reverse={sector:[]for sector in graph}
    for sector,targets in graph.items():
        for target in targets:assert 1<=target<=3000,'bounded departure graph';reverse[target].append(sector)
    for network in(graph,reverse):
        seen={3000};queue=[3000]
        for sector in queue:
            for target in network[sector]:
                if target not in seen:seen.add(target);queue.append(target)
        assert len(seen)==3000,'declared departure graph remains strongly connected'
    result['YTDATA.DAT']=bytes(world);return result


def verify_fixture(before,profile,mode,edits):
    parent=parent_inputs(profile,mode);expected=fixture_inputs(profile,mode)
    assert before==expected,'exact independently reconstructed one-time fixture world and unchanged five side files'
    assert type(edits)is list and edits,'explicit first-stage data intervention ledger required'
    plan=[(3051,off,4)for off in range(41,65,4)]+[(51+sector,off,4)for sector,off in((2996,45),(2998,49),(2999,53))]+[(2419,45,4),(2419,81,4),(2419,85,4),(3051,81,4),(3051,85,4),(4054,0,137),(3051 if CASES[profile]['occupied']else 3050,93,4)]
    assert [(r.get('record'),r.get('offset'),len(bytes.fromhex(r.get('after',''))))for r in edits]==plan,'exact independently declared 16-edit plan including no-op writes'
    world=bytearray(parent['YTDATA.DAT']);written=set()
    for row in edits:
        assert type(row)is dict and set(row)=={'record','offset','before','after'},'exact record/offset/before/after edit schema'
        record,offset,old,new=(row[k]for k in('record','offset','before','after'))
        assert type(record)is int and 1<=record<=4151 and type(offset)is int and 0<=offset<137,'bounded explicit record edit'
        assert type(old)is type(new)is str and re.fullmatch('[0-9a-f]+',old)and re.fullmatch('[0-9a-f]+',new),'complete original raw edit bytes'
        old,new=bytes.fromhex(old),bytes.fromhex(new)
        assert len(old)==len(new)>0 and offset+len(old)<=137,'edit remains within one original record'
        at=(record-1)*137+offset
        assert world[at:at+len(old)]==old,'edit before-bytes bind the actual preceding fixture state'
        world[at:at+len(new)]=new;written.update(range(at,at+len(new)))
    assert bytes(world)==expected['YTDATA.DAT'],'edit ledger exactly reconstructs the independently declared fixture'
    actual={i for i,(old,new)in enumerate(zip(parent['YTDATA.DAT'],world))if old!=new}
    assert actual<=written,'all actual changes are explicitly audited'
    return dict(unchanged_links=5,transformed_links=1,changed_bytes=len(actual),edits=len(edits))


def commands(date,clock):
    return['date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']


def verify_launch(folder,meta,profile,stage,mode):
    date,clock=schedule(profile,stage);date_text=date.strftime('%m/%d/%Y')
    argv=json.loads((folder/'launch.json').read_text())
    assert argv==meta['argv']and argv[0]=='/opt/homebrew/bin/dosbox-staging','actual pinned host launch'
    assert len(argv)>8 and argv[8].startswith('mount c /private/tmp/'),'fresh disposable mount'
    mount=Path(argv[8][8:]);assert mount.parts[-3:]==(profile,stage,mode),'actual profile/stage/mode mount'
    expected=[argv[0],'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']
    expected += [v for c in[argv[8],'c:']+commands(date_text,clock)+['exit']for v in('-c',c)]
    assert argv==expected and(folder/'COMMANDS.TXT').read_text()=='\n'.join(commands(date_text,clock))+'\n','complete independently declared commands'
    messages=[line.split(' | ',1)[1]for line in(folder/'dosbox.stderr').read_text().splitlines()if' | 'in line]
    args=[shlex.split(m[11:])for m in messages if m.startswith('arguments: ')]
    assert args==[argv],'actual process launch agrees with declaration'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1,'actual pinned host version'
    assert len([m for m in messages if m.startswith('CPU: Setting fixed 200000 cycles.')])==1,'actual fixed CPU budget'
    assert 'SDL: dummy video initialised'in messages and "MIXER: Sound output disabled ('nosound' mode)"in messages,'actual dummy video/audio'
    assert(folder/'dosbox.stdout').read_bytes()==b'','complete empty host stdout'
    assert read_date((folder/'DOSDATE.LOG').read_bytes())==date,'actual initial DOS calendar'
    requested=sum(int(part)*unit for part,unit in zip(clock.split(':'),(3600,60,1)))
    actual=read_time((folder/'DOSTIME.LOG').read_bytes())
    assert abs(actual-requested)<=1,'actual shell clock must match declared request within BIOS quantization'
    elapsed=(read_date((folder/'ENDDATE.LOG').read_bytes())-date).days*86400+read_time((folder/'ENDTIME.LOG').read_bytes())-actual
    assert 0<elapsed<40,'bounded advancing actual DOS time'
    return mount


def verify_inheritance(before,parent):
    assert set(before)==set(parent)==set(FILES),'all six input identities retained'
    assert before==parent,'all six child inputs equal exact corresponding parent outputs without patches'


def verify_observation(observation,profile,stage,before,outputs):
    assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'},'exact raw observation schema'
    assert observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is True and type(observation['exit_code'])is int and observation['exit_code']==0,'actual observed source/exit identity'
    assert observation['errors']==[]and type(observation['dropped'])is int and observation['dropped']==0,'complete raw observation without loss'
    clocks.neutral.verify_module(observation['module'])
    date,_=schedule(profile,stage);ports=[];port_dates=[];planet_timers=[];planet_dates=[];segments=set();external=collections.Counter();roles=collections.Counter();texts={'news':[],'score':[]};mine_helpers=[]
    assert 1<=len(observation['events'])<=16384,'bounded complete source observation'
    for ordinal,event in enumerate(observation['events'],1):
        row=copy.deepcopy(event);states=[]
        for side in('before','after'):
            raw=row[side].pop('rng_raw')
            assert type(raw)is str and re.fullmatch('[0-9a-f]{8}',raw),'four raw RNG witness bytes'
            n=int.from_bytes(bytes.fromhex(raw),'little');assert n<2**24,'actual24bit RNG state';states.append(n)
        assert states[0]==states[1],'clock callback preserves raw RNG'
        pair=clocks.event_pair(row,ordinal)
        assert pair['before']['cycle_max']==200000,'fixed observed CPU budget'
        roles[(pair['kind'],pair.get('role'))]+=1
        if pair['kind']=='timer'and pair.get('role')=='helper2'and pair['nested_return_ip']==0x4aa4:mine_helpers.append(dict(ordinal=ordinal,old_state=states[0],timer=pair['seconds'].hex()))
        if pair['kind']=='unqualified':external[pair['function']]+=1;continue
        segments.add((pair['runtime_cs'],pair['main_cs'],pair['ds']))
        if pair['kind']=='date':assert pair['date']==date,'source-qualified actual stage calendar'
        if pair['kind']=='time'and pair['role']in texts:texts[pair['role']].append(clocks.native_time_text(pair['after']['cx'],pair['after']['dx']))
        if pair['kind']=='timer'and pair['role']in('port','planet'):
            ident=clocks.mbf_fraction(bytes.fromhex(pair['before']['port_raw']));assert ident.denominator==1,'whole actual source loop index'
            (ports if pair['role']=='port'else planet_timers).append((int(ident),pair['minutes']))
        if pair['kind']=='date'and pair['role']=='calendar':
            nested=clocks.CALENDAR_CALLERS[pair['nested_return_ip']]
            if nested in('port','planet'):
                ident=clocks.mbf_fraction(bytes.fromhex(pair['before']['port_raw']));assert ident.denominator==1,'whole source calendar loop index'
                (port_dates if nested=='port'else planet_dates).append((int(ident),pair['date']))
    assert len(segments)==1 and external=={0x2a:2,0x2c:2},'stable identities and exact external shell clock inventory'
    assert roles[('timer','startup')]==1,'unique startup TIMER'
    assert[i for i,_ in ports]==[i for i,_ in port_dates]==list(range(1,1001)),'all source-qualified port date/time indices occur once in order'
    active=[r-4051 for r in range(4052,4152)if field(before['YTDATA.DAT'],r,85)>0]
    assert[i for i,_ in planet_timers]==[i for i,_ in planet_dates]==active,'actual active-planet date/time source indices'
    for ident,minutes in ports:
        assert rawfield(outputs['YTDATA.DAT'],3051+ident,101)==minutes,'saved raw port time equals actual source TIMER conversion'
        assert field(outputs['YTDATA.DAT'],3051+ident,45)==source_day(date),'saved port day agrees with actual source date'
    for ident,minutes in planet_timers:
        assert rawfield(outputs['YTDATA.DAT'],4051+ident,89)==minutes,'saved active-planet time agrees with actual source TIMER'
        assert field(outputs['YTDATA.DAT'],4051+ident,41)==source_day(date),'saved active-planet day agrees with actual source date'
    for role in('news','score'):assert roles[('date',role)]==roles[('time',role)]==1,'unique source text clock pairs'
    header=(texts['news'][0]+' '+date.strftime('%m-%d-%Y')+': Maintenance Program Ran (Revision 03/14/94)\r\n').encode()
    assert outputs['YTNEWS.DAT'].startswith(header),'actual public header agrees with its own source clocks'
    header=('Last updated at: '+date.strftime('%m-%d-%Y')+' '+texts['score'][0]+'\r\n').encode()
    assert outputs['YTSCORE.ASC'].count(header)==1,'actual score header agrees with its own source clocks'
    return dict(helper1=roles[('timer','helper1')],helper2=roles[('timer','helper2')],active_planets=len(active),events=len(observation['events']),source_day=source_day(date),publication_clocks={role:texts[role][0]for role in('news','score')},gateway_timer=next(raw.hex()for slot,raw in planet_timers if slot==3),planet_timers={slot:raw.hex()for slot,raw in planet_timers},mine_helper_calls=mine_helpers)


def physical(world):
    assert len(world)==4151*137,'complete world extent'
    totals={-1:0,-2:0,0:0}
    for sector in range(1,3001):
        force=field(world,51+sector,81);owner=field(world,51+sector,85)
        assert force.denominator==1 and 0<=force<=1000000,'bounded whole saved physical force'
        if force:assert owner in totals,'retained physical owner';totals[owner]+=int(force)
    return totals


def stock_after_economy(before_world,date,timer,record=4054):
    """Original source single arithmetic from before stock/rates/bank only."""
    f32=lambda n:struct.unpack('<f',struct.pack('<f',n))[0]
    day=source_day(date);minute=float(clocks.mbf_fraction(timer))
    oldminute=float(field(before_world,record,89));last=float(field(before_world,record,41))
    elapsed=f32(f32(day-last)+f32(f32(minute-oldminute)/1440))
    if elapsed<0 or elapsed>10:elapsed=10
    rates=[float(field(before_world,record,o))for o in(45,49,53)];bank=float(field(before_world,record,117))
    assert all(0<=n<=200000 for n in rates)and 0<=bank<=30000000,'bounded source production and bank'
    base=math.floor(f32(f32(rates[0]+rates[1])+rates[2]))
    bonus=f32(bank/500)
    return f32(float(field(before_world,record,129))+f32(f32(base+bonus)*elapsed))


def ground_after_economy(before_world,date,timer):
    """Independent source ground expression for the zero-bank controlled planet."""
    f32=lambda n:struct.unpack('<f',struct.pack('<f',n))[0]
    minute=float(clocks.mbf_fraction(timer));prior=float(field(before_world,4054,89))
    elapsed=f32(f32(source_day(date)-float(field(before_world,4054,41)))+f32(f32(minute-prior)/1440))
    if elapsed<0 or elapsed>10:elapsed=10
    assert field(before_world,4054,117)==0,'zero-bank ground calculation scope'
    ground=float(field(before_world,4054,77))
    return math.floor(f32(ground+ground*elapsed*f32(.01)))


def verify_semantics(profile,stage,before,outputs,trace,source_timer=None,planet_timers=None):
    date,_=schedule(profile,stage);old=before['YTDATA.DAT'];world=outputs['YTDATA.DAT'];initial=physical(old);final=physical(world)
    assert world[137:51*137]==old[137:51*137],'inactive human records unchanged'
    assert outputs['YTNAME.DAT']==before['YTNAME.DAT']and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT']and outputs['YTRMSG.DAT']==before['YTRMSG.DAT']==b'','exact names, journal rotation and empty private messages'
    assert field(world,1,81)==source_day(date)and field(world,1,45)==26,'source calendar watermark'
    at=(4054-1)*137
    assert old[at:at+41]==world[at:at+41]==b'Departure Cache'.ljust(41,b' ')and field(old,4054,73)==field(world,4054,73)==0,'pickup does not retitle the controlled ordinary planet'
    planet_links=lambda data:[sector for sector in range(1,3001)if field(data,51+sector,93)==3]
    links=planet_links(old);assert links==planet_links(world)==([3000]if CASES[profile]['occupied']else[2999]) and field(world,4054,77)>0,'actual surviving departure planet/link/ground'
    timer=rawfield(world,4054,89)if source_timer is None else bytes.fromhex(source_timer)
    produced=stock_after_economy(old,date,timer)
    stock=field(world,4054,129);assert stock>=0,'nonnegative actual saved gateway stock'
    assert field(world,4054,117)==0,'gateway bank remains empty'
    lines=trace.split(b'\r\n');marker=lines.index(b'Mercenary Maintenance...');xlines=lines[:marker];mlines=lines[marker:]
    regen=[int(m[1])for line in xlines if(m:=re.fullmatch(rb'Calculated Dynamic Xannor Regeneration is ([0-9]+) fighters\.',line))]
    assert len(regen)==1,'one source Xannor regeneration declaration'
    xloss=defense_mloss=0;gateway_attacked=False;i=0
    while i<len(xlines):
        line=xlines[i]
        if not line.startswith(b' *** '):i+=1;continue
        foreign=re.fullmatch(rb' \*\*\* Mercenaries: lost ([0-9]+), dstrd ([0-9]+) \((Xannor|Plyr) ftrs dstrd\)',line)
        planet=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "(The Wanderer|Mercenary Base|Departure Cache)"',line)
        mine=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor hit sector mines in sector ([1-9][0-9]*)!',line)
        if foreign:xloss+=int(foreign[1]);defense_mloss+=int(foreign[2]);i+=1
        elif planet:
            assert xlines[i+1]==b' *** Xannor fighters destroyed!','complete exact planetary fatal pair';xloss+=int(planet[1]);gateway_attacked|=planet[2]==b'Departure Cache';i+=2
        elif mine:
            assert xlines[i+1]==b' *** The Xannor were killed!','complete exact Xannor mine fatal pair';xloss+=int(mine[1]);i+=2
        else:raise AssertionError('unknown Xannor phase outcome: '+repr(line))
    available=initial[-2]-defense_mloss;current=available;reserve=0;started=False;pending=False;offenses=[];mine_losses=offense_losses=pickup=0;captures=[];mine_events=[];activations=[];merges=[];pickups={};i=0
    def stamp(amount):
        nonlocal current,pending,offense_losses,reserve
        if pending:
            assert 0<amount<=current,'declared offensive winner must survive without invented force';offense_losses+=current-amount;pending=False
        elif amount>current:
            added=amount-current;assert added<=reserve,'unprinted force increase must use actual remaining friendly reserve'
            merges.append(added);reserve-=added
        else:assert current==amount,'source force stamp agrees with all preceding phase actions'
        current=amount
    while i<len(mlines):
        line=mlines[i]
        move=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries moving from sector ([1-9][0-9]*) *',line)
        mine=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) mercenaries hit sector mines in sector ([1-9][0-9]*)!',line)
        attack=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Mercenaries attacking ([1-9][0-9]*) fighters beloning to The Xannor!',line)
        capture=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries captured planet (Departure Cache|The Wanderer|Mercenary Base)!',line)
        taking=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries taking ([0-9]+) fighters from planet (Departure Cache|The Wanderer|Mercenary Base)!',line)
        if move:
            if not started:
                amount=int(move[1]);assert 0<amount<=available,'first moving component is within actual post-Xannor inventory';current=amount;reserve=available-amount;started=True
            stamp(int(move[1]));activations.append(dict(force=current,sector=int(move[2])));i+=1
        elif mine:
            stamp(int(mine[1]));sector=int(mine[2]);assert 1<=sector<=3000,'bounded actual mine encounter sector'
            nextline=mlines[i+1];loss=re.fullmatch(rb' \*\*\* Lost a total of ([1-9][0-9]*) fighters!',nextline)
            if nextline==b' *** The mercenariers were killed!':amount=current
            else:assert loss,'unknown Mercenary mine result';amount=int(loss[1])
            assert 0<amount<=current,'bounded printed/capped Mercenary mine damage'
            oldmines=field(old,51+sector,129);newmines=field(world,51+sector,129)
            assert 0<=newmines<oldmines,'real saved mine expenditure'
            current-=amount;mine_losses+=amount;mine_events.append(dict(sector=sector,loss=amount,before=int(oldmines),after=int(newmines)));i+=2
        elif attack:
            stamp(int(attack[1]));assert mlines[i+1]==b' *** The Mercenaries Won!','only witnessed surviving offensive winner admitted'
            xloss+=int(attack[2]);offenses.append(dict(attacker=int(attack[1]),defenders=int(attack[2])));pending=True;i+=2
        elif capture:stamp(int(capture[1]));captures.append((current,capture[2]));i+=1
        elif taking:
            stamp(int(taking[1]));assert captures and captures[-1]==(current,taking[3]),'stock taking follows its exact captured title and force stamp'
            amount=int(taking[2]);assert amount>0,'positive actual taking receipt';pickup+=amount;current+=amount;pickups[taking[3]]=pickups.get(taking[3],0)+amount;i+=1
        elif line.startswith(b' *** ')or(b'Mercenaries captured planet'in line)or(b'Mercenaries taking'in line):raise AssertionError('unknown Mercenary phase outcome: '+repr(line))
        else:i+=1
    stamp(final[-2]-reserve)
    origins=[sector for sector in range(1,3001)if field(old,51+sector,81)>0 and field(old,51+sector,85)==-2]
    if activations:
        assert activations[0]['sector']in origins,'first Mercenary activation starts at an actual inherited physical source'
        assert all(a['sector']>b['sector']for a,b in zip(activations,activations[1:])),'Mercenary reactivations follow actual descending scan order'
    titles={b'Departure Cache':4054,b'The Wanderer':4052,b'Mercenary Base':4150};discarded_fractions={}
    for title,record in titles.items():
        clock=rawfield(world,record,89)if planet_timers is None else bytes.fromhex(planet_timers[record-4051])
        produced_title=stock_after_economy(old,date,clock,record);taken=pickups.get(title,0)
        if title in pickups:
            assert 0<=produced_title-taken<1 and rawfield(world,record,129)==bytes.fromhex('00008000'),'observed whole pickup uses exact source clear of complete source-grown stock'
            discarded_fractions[title.decode()]=produced_title-taken
        else:assert field(world,record,129)==produced_title,'source-grown uncollected title stock remains saved'
    for amount,title in captures:
        slot=titles[title]-4051;sectors=[s for s in range(1,3001)if field(world,51+s,93)==slot]
        assert len(sectors)==1 and field(world,51+sectors[0],85)==-2,'captured title binds its actual surviving linked force'
    if merges:
        assert stage=='child-1'and CASES[profile]['friendly']>0 and activations[0]==dict(force=97337,sector=3000),'observed merge starts at the declared uninjured source force'
        assert sum(merges)==CASES[profile]['friendly']-defense_mloss and reserve==0,'merge adds the actual surviving stationary friendly inventory exactly once'
        assert rawfield(world,2419,81)==rawfield(world,2419,85)==bytes.fromhex('00008000'),'actual friendly merge clears successor force and owner with source8472'
    if stage=='child-1'and any(a['sector']==3000 for a in activations)and field(world,3051,81)==0:
        assert rawfield(world,3051,81)==rawfield(world,3051,85)==bytes.fromhex('00002800'),'actual departure keeps source859e raw zero in both origin fields'
    if not gateway_attacked:assert field(world,4054,77)==ground_after_economy(old,date,timer),'pickup does not debit independently grown gateway ground'
    assert initial[-1]+regen[0]-xloss==final[-1]and initial[0]==final[0],'actual physical Xannor and neutral totals reconcile'
    assert initial[-2]-defense_mloss-mine_losses-offense_losses+pickup==final[-2],'all Mercenary force sources/losses reconcile'
    assert produced-pickups.get(b'Departure Cache',0)==stock,'independent departure-stock economy minus its own printed debit equals saved stock'
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1 and tuple(int(n.replace(b',',b''))for n in rows[0])==(100*final[-1],100*final[-2]),'scores bind actual physical survivors'
    relevant=lambda data:tuple(line for line in data.split(b'\r\n')if line.startswith(b' *** ')or b'Mercenaries captured planet'in line or b'Mercenaries taking'in line)
    assert relevant(outputs['YTNEWS.DAT'])==relevant(trace),'complete literal newspaper/console outcome agreement'
    return dict(physical=final,prior_physical=initial,observed_discarded_pickup_fractions=discarded_fractions,observed_friendly_merge_increments=merges,unmoved_friendly_reserve=reserve,pickup_by_title={k.decode():v for k,v in pickups.items()},occupied_origin_departure=bool(stage=='child-1'and CASES[profile]['occupied']and any(a['sector']==3000 for a in activations)),occupied_origin_held=bool(stage=='child-1'and CASES[profile]['occupied']and not any(a['sector']==3000 for a in activations)and field(world,3051,85)==-2 and field(world,3051,81)>0),friendly_force_survives_earlier_phase=bool(stage=='child-1'and CASES[profile]['friendly']>defense_mloss),xannor_losses=xloss,earlier_defense_mercenary_losses=defense_mloss,mine_losses=mine_losses,observed_offensive_losses=offense_losses,pickup=pickup,captured=len(captures),mine_events=mine_events,activations=activations,pre_pickup_stock=produced,saved_stock=str(stock),stock_clock_provenance='authenticated source callback'if source_timer is not None else'saved timestamp only; corroboration requires equal source-observed outputs',selection=dict(capture=bool(captures),pickup=bool(pickup),mine=bool(mine_events),offense=bool(offenses)),offenses=offenses)


def verify_receipt_controller(controller,mode,observation,body,receipt_body):
    """Independently verify the persisted exit receipt, not inferred delivery."""
    assert mode in('observed','attach-only'),'receipt applies to an actual attached process'
    expected_keys={'mode','frida','node_version','started','detached_reason','pid','forced','process_exited','exit_code','success','flush_receipt','flush_acknowledged','ready','finished','messages'}
    assert set(controller)==expected_keys,'complete persisted-receipt controller schema'
    assert controller['mode']==mode and controller['success']is True and controller['forced']is False and controller['process_exited']is True and controller['ready']is True,'natural successful attached process'
    assert type(controller['pid'])is int and controller['pid']>0 and type(controller['exit_code'])is int and controller['exit_code']==0 and controller['detached_reason']=='process-terminated','natural actual owned-process zero exit'
    assert re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+',controller['node_version']),'actual Node controller version'
    start=datetime.datetime.fromisoformat(controller['started'].replace('Z','+00:00'));end=datetime.datetime.fromisoformat(controller['finished'].replace('Z','+00:00'))
    assert datetime.timedelta(0)<end-start<datetime.timedelta(seconds=40),'bounded initialized attached-process lifecycle'
    assert body==(json.dumps(observation,separators=(',',':'),ensure_ascii=False)+'\n').encode(),'complete canonical UTF8 trace file'
    receipt=json.loads(receipt_body)
    assert receipt_body==(json.dumps(receipt,separators=(',',':'),ensure_ascii=False)+'\n').encode(),'complete canonical UTF8 receipt file'
    expected=dict(recipe='departure-exit-flush-receipt-v1',exit_code=0,bytes=len(body),expected_bytes=len(body),events=len(observation['events']),errors=0,dropped=0)
    assert set(receipt)==set(expected)and all(type(receipt[key])is int for key in expected if key!='recipe')and receipt==expected,'persisted receipt binds exact actual trace bytes and complete counts'
    assert controller['flush_receipt']==receipt and type(controller['flush_acknowledged'])is bool,'controller retains actual persisted receipt and delivery classification'
    messages=controller['messages'];assert type(messages)is list and len(messages)in(1,2)and all(type(m)is dict and set(m)=={'type','payload'}and m['type']=='send'for m in messages),'only complete ready and optional flush messages'
    assert messages[0]['payload']==dict(kind='ready',module=observation['module'],observe=mode=='observed'),'same actual module and hook mode was ready before execution'
    acknowledged=len(messages)==2
    if acknowledged:
        assert messages[1]['payload']==dict(kind='flushed',**{key:value for key,value in expected.items()if key!='recipe'}),'actual delivered acknowledgement agrees with persisted receipt'
    assert controller['flush_acknowledged']is acknowledged,'delivery flag reflects actual acknowledgement inventory'
    frida=controller['frida']
    assert set(frida)=={'version','module','module_sha256','package_sha256'}and frida['version']=='17.23.2','compatible actual Frida identity'
    assert Path(frida['module']).is_absolute()and frida['module'].endswith('/frida/build/src/frida.js'),'actual supplied Frida module path'
    assert frida['module_sha256']=='408959cd8daa899370884ea4c7d763916b1ea2960ef4ce8118956870a600bda9'and frida['package_sha256']=='7efb59d2050b7b6304e1617f463c4eb7b2f7cb7e3e80e677976825a76ee31e8d','retained Frida module/package digests'
    return dict(persisted=True,acknowledged=acknowledged,bytes=len(body))


def verify_case(folder,profile,stage,mode,observer,parent_outputs=None,*,protocol=None):
    folder=Path(folder);date,clock=PROFILES[profile][STAGES.index(stage)]
    protocol=('persisted_exit_receipt'if profile==RECEIPT_PROFILE else'legacy')if protocol is None else protocol
    assert protocol in('legacy','persisted_exit_receipt'),'explicit retained delivery protocol'
    assert mode in MODES,'declared actual capture mode'
    meta=json.loads((folder/'capture.json').read_text());parent='fixture-parent'if stage=='child-1'else'child-1'
    assert set(meta)=={'recipe','profile','stage','mode','parent','parent_mode','parent_pins','parent_source','applied_fixture','fixture_edits','date','clock','cycles','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'},'exact gateway-hazard metadata schema'
    recipe='maintenance-departure-merge-controls-v1'
    assert(meta['recipe'],meta['profile'],meta['stage'],meta['mode'],meta['parent'],meta['parent_mode'],meta['parent_pins'])==(recipe,profile,stage,mode,parent,mode,PARENT_SOURCE['pins']),'actual independently declared profile/stage/parent identity'
    assert meta['parent_source']==PARENT_SOURCE,'independently declared original survivor lineage'
    assert(meta['date'],meta['clock'],meta['cycles'])==(date,clock,200000),'complete declared date/clock/CPU recipe'
    assert meta['host_sha256']==clocks.neutral.HOST_SHA and 0<meta['elapsed_seconds']<40,'pinned host and bounded capture'
    assert meta['guests']==clocks.GUESTS,'unchanged original full-run guests'
    for guest,digest in clocks.GUESTS.items():assert SHA((ROOT/'archive/dos-original'/guest).read_bytes())==digest,'immutable original guest identity'
    names=COMMON|{'before-'+n+'.gz'for n in FILES}|{'after-'+n+'.gz'for n in FILES}
    if MODES[mode]!='unobserved':
        names|={'host-time.json.gz','loaded-observer.js'}
        if protocol=='persisted_exit_receipt':names.add('host-flush.json')
    assert set(meta['files'])==names and{p.name for p in folder.iterdir()}==names|{'capture.json'},'complete exact raw capture inventory'
    for name in names:assert SHA((folder/name).read_bytes())==meta['files'][name],'declared raw file hash '+name
    before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in FILES};outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in FILES}
    assert meta['inputs']=={n:SHA(b)for n,b in before.items()}and meta['outputs']=={n:SHA(b)for n,b in outputs.items()},'complete decompressed input/output identities'
    if stage=='child-1':
        assert meta['applied_fixture']is True,'one-time fixture is explicit, never claimed as exact initial data inheritance'
        links=verify_fixture(before,profile,mode,meta['fixture_edits'])
    else:
        assert meta['applied_fixture']is False and meta['fixture_edits']==[],'no second-stage repair or intervention allowed'
        assert parent_outputs is not None,'actual same-mode preceding child outputs required'
        verify_inheritance(before,parent_outputs);links=dict(unchanged_links=6,transformed_links=0)
    mount=verify_launch(folder,meta,profile,stage,mode)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','natural DOS completion witnesses'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'],'actual lifecycle metadata'
    observation=None;obraw=None;clock_stats=None
    if MODES[mode]!='unobserved':
        obraw=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(obraw)
        config=dict(observe=MODES[mode]=='observed',output=str(mount/'host-time.json'))
        if protocol=='persisted_exit_receipt':config['flush_output']=str(mount/'host-flush.json')
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'actual loaded observer source/config'
        if config['observe']:clock_stats=verify_observation(observation,profile,stage,before,outputs)
        else:
            assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}and observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is False and observation['exit_code']==0 and observation['events']==observation['errors']==[]and observation['dropped']==0,'attach-only has no hooks/events/losses'
            clocks.neutral.verify_module(observation['module'])
    receipt=None
    if protocol=='persisted_exit_receipt'and MODES[mode]!='unobserved':receipt=verify_receipt_controller(controller,MODES[mode],observation,obraw,(folder/'host-flush.json').read_bytes())
    else:clocks.neutral.verify_controller(controller,MODES[mode],observation,obraw)
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n')and trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'),'complete unchanged original maintenance transcript'
    stats=verify_semantics(profile,stage,before,outputs,trace,None if clock_stats is None else clock_stats['gateway_timer'],None if clock_stats is None else clock_stats['planet_timers']);stats['lineage']=links
    return dict(before=before,outputs=outputs,stats=stats,clocks=clock_stats,exit_receipt=receipt)


def paired_outputs(results):
    """Compare every byte; clock-correlated differences remain real differences."""
    assert set(results)==set(MODES),'six independent complete modes required'
    reference=results['unobserved-a']['outputs'];assert set(reference)==set(FILES),'complete six-file reference output'
    differences={mode:[name for name in FILES if result['outputs'][name]!=reference[name]]for mode,result in results.items()}
    counts={mode:{name:sum(a!=b for a,b in zip(reference[name],result['outputs'][name]))+abs(len(reference[name])-len(result['outputs'][name]))for name in differences[mode]}for mode,result in results.items()}
    rows={}
    for mode,result in results.items():
        fields=[];actual=result['outputs']['YTDATA.DAT'];before=reference['YTDATA.DAT']
        if actual!=before:
            assert len(actual)==len(before)==4151*137,'complete unequal worlds retain original extent'
            for record in range(1,4152):
                for offset in range(41,137,4):
                    at=(record-1)*137+offset
                    if before[at:at+4]!=actual[at:at+4]:fields.append(dict(record=record,offset=offset,reference=before[at:at+4].hex(),actual=actual[at:at+4].hex()))
        rows[mode]=fields
    return dict(equal=not any(differences.values()),differences=differences,byte_differences=counts,world_fields=rows)


def verify_mode_classification(profile,stage,results,paired):
    if profile!='occupied-friendly-second-two':
        assert paired['equal'],'all other canonical profile stages must retain exact six-mode outputs'
        return dict(classification='six-mode equal',normalized_bytes=0)
    assert paired['equal']is False,'the actual clock-correlated nonneutral profile must never be reported as equal'
    observed=('observed-a','observed-b','observed-c');unobserved=('unobserved-a','unobserved-b','attach-only')
    for modes in(observed,unobserved):
        assert all(results[m]['outputs']==results[modes[0]]['outputs']for m in modes),'each actual observation cohort agrees internally'
    expected_count=89 if stage=='child-1'else 94
    for mode in observed:
        assert paired['differences'][mode]==['YTDATA.DAT']and paired['byte_differences'][mode]=={'YTDATA.DAT':expected_count},'retain exact observed raw clock-correlated difference count'
        fields=paired['world_fields'][mode]
        assert fields and all(3583<=row['record']<=(3594 if stage=='child-1'else 3597)and row['offset']in(49,53,57,61,65,69,101)for row in fields),'differences remain in the actual port clock and derived supply writer fields'
        allowed={i for row in fields for i in range((row['record']-1)*137+row['offset'],(row['record']-1)*137+row['offset']+4)}
        a=results['unobserved-a']['outputs']['YTDATA.DAT'];b=results[mode]['outputs']['YTDATA.DAT']
        assert all(i in allowed for i,(x,y)in enumerate(zip(a,b))if x!=y),'no world bytes outside the disclosed raw numeric fields differ'
    for mode in unobserved:assert paired['differences'][mode]==[],'unobserved/attach-only outputs remain exactly equal'
    return dict(classification='clock-correlated nonneutral port outputs',normalized_bytes=0,observed_difference_bytes=expected_count,other_five_files_equal=True)


def verify_failed_observer(folder,observer):
    """Retain a natural DOS run with invalid observer delivery as diagnostic only."""
    folder=Path(folder);names=COMMON|{'after-'+n+'.gz'for n in FILES}|{'host-time.json.gz','loaded-observer.js'}
    assert {p.name for p in folder.iterdir()}==names,'complete failed-observer diagnostic inventory'
    argv=json.loads((folder/'launch.json').read_text());mount=verify_launch(folder,dict(argv=argv),RECEIPT_PROFILE,'child-1','observed-b')
    config=dict(observe=True,output=str(mount/'host-time.json'))
    assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'failed diagnostic retains original observer/config'
    controller=json.loads((folder/'controller.json').read_text())
    assert controller['mode']=='observed'and controller['success']is False and controller['forced']is False and controller['process_exited']is True and controller['ready']is True,'failed acknowledgement did not force or hang the owned process'
    assert type(controller['pid'])is int and controller['pid']>0 and type(controller['exit_code'])is int and controller['exit_code']==0 and controller['detached_reason']=='process-terminated','actual natural zero-exit process is not a valid observer acknowledgement'
    assert folder.name in('failed-attempt-a','failed-attempt-b'),'exact retained diagnostic attempt'
    acknowledged=folder.name=='failed-attempt-b'
    expected_error='Error: capture did not exit naturally and cleanly'if acknowledged else'Error: incomplete trace flush'
    assert controller['error']==expected_error and 'cleanup_error'not in controller,'exact original delivery or post-detach liveness failure'
    body=gzip.decompress((folder/'host-time.json.gz').read_bytes());ob=json.loads(body)
    assert ob['exit_code']==0 and ob['errors']==[]and ob['dropped']==0,'retained trace body is complete but lacks required delivery acknowledgement'
    clocks.neutral.verify_module(ob['module'])
    expected_messages=[dict(type='send',payload=dict(kind='ready',module=ob['module'],observe=True))]
    if acknowledged:expected_messages.append(dict(type='send',payload=dict(kind='flushed',exit_code=0,bytes=len(body),expected_bytes=len(body),events=len(ob['events']),errors=0,dropped=0)))
    assert controller['messages']==expected_messages,'actual failed attempt retains its distinct delivered acknowledgement inventory'
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','DOS itself naturally returned successfully'
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.endswith(b'Daily Maintenance Completed OK\r\n'),'retained DOS completion is separate from observer completion'
    try:clocks.neutral.verify_controller(controller,'observed',ob,body)
    except AssertionError:pass
    else:raise AssertionError('failed delivery must never qualify as a complete observed control')
    for name in FILES:assert gzip.decompress((folder/('after-'+name+'.gz')).read_bytes())is not None,'all diagnostic after-files retained'
    return dict(classification='post-detach liveness diagnostic'if acknowledged else'invalid observer delivery diagnostic',full_control=False,natural_dos_exit=True,acknowledgement_delivered=acknowledged)


def verify_diagnostics(primary=DEFAULT,directory=DIAGNOSTICS):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==DIAGNOSTICS_SHA,'immutable failed-attempt/supplementary manifest'
    pins=json.loads(raw);assert set(pins)=={'files'},'exact diagnostics manifest schema'
    files={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert files==set(pins['files']),'complete retained diagnostics file inventory'
    for name,digest in pins['files'].items():assert SHA((root/name).read_bytes())==digest,'immutable diagnostic artifact '+name
    assert {p.name for p in root.iterdir()}=={'acquisition','classification.json','attempt-a.log','attempt-b.log','partial-attempt-a','partial-attempt-b','failed-attempt-a','failed-attempt-b','pins.json'},'complete separate failed-attempt classification packet'
    old_sources={'recover_maintenance_departure_merge.py','verify_maintenance_clock_neutral.py','capture_maintenance_clock_neutral.mjs','observe_maintenance_placement.js'}
    assert {p.name for p in(root/'acquisition').iterdir()}==old_sources,'exact original failed-attempt acquisition source snapshots'
    expected=dict(recipe='departure-observer-flush-diagnostics-v1',profile=RECEIPT_PROFILE,stage='child-1',valid_partial_modes=['unobserved-a','observed-a','attach-only'],attempts=['attempt-a','attempt-b'],completed_supplementary_runs=6,invalid_observer_runs=2,failed_mode='observed-b',full_control=False,reason='Attempt-a lacks its required asynchronous flush acknowledgement. Attempt-b has a valid flush acknowledgement but fails the immediate post-detach liveness check; its final metadata records exited=true without forced termination. Both are retained diagnostics, not completed observed controls. The entire affected case is recaptured separately with a persisted exit receipt; that protocol fixes acknowledgement persistence, not a claimed general liveness-race repair.',failed_controller_errors={'attempt-a':'Error: incomplete trace flush','attempt-b':'Error: capture did not exit naturally and cleanly'})
    assert json.loads((root/'classification.json').read_text())==expected,'diagnostics cannot be relabeled as completed full controls'
    observer=(root/'acquisition/observe_maintenance_placement.js').read_text();comparisons=0;failed=[]
    for attempt in('a','b'):
        base=root/('partial-attempt-'+attempt)
        assert {p.name for p in base.iterdir()}=={'unobserved-a','observed-a','attach-only'},'only three valid supplementary modes were completed'
        for mode in('unobserved-a','observed-a','attach-only'):
            result=verify_case(base/mode,RECEIPT_PROFILE,'child-1',mode,observer,protocol='legacy')
            canonical=Path(primary)/RECEIPT_PROFILE/'child-1'/mode
            for name in FILES:
                assert result['outputs'][name]==gzip.decompress((canonical/('after-'+name+'.gz')).read_bytes()),'all valid supplementary outputs equal the separately recaptured canonical case'
                comparisons+=1
        failed.append(verify_failed_observer(root/('failed-attempt-'+attempt),observer))
    assert comparisons==36,'all six supplementary runs compare all six outputs'
    return dict(completed_supplementary_runs=6,invalid_observer_runs=2,supplementary_file_comparisons=comparisons,failed=failed)


def verify(directory=DEFAULT,diagnostics=DIAGNOSTICS):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'immutable independent departure corpus manifest'
    pins=json.loads(raw);assert set(pins)=={'files'},'exact independent manifest schema'
    actual={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert actual==set(pins['files']),'complete pinned corpus inventory'
    for name,digest in pins['files'].items():assert SHA((root/name).read_bytes())==digest,'immutable raw corpus artifact '+name
    assert {p.name for p in root.iterdir()}==set(PROFILES)|{'pins.json','recipe.json','acquisition'},'exact independently declared eight-case corpus inventory'
    assert {p.name for p in(root/'acquisition').iterdir()}==SOURCES,'complete frozen acquisition sources'
    assert json.loads((root/'recipe.json').read_text())=={'recipe':'maintenance-departure-merge-controls-v1','profiles':{name:[list(row)for row in rows]for name,rows in PROFILES.items()},'parent':PARENT_SOURCE,'cases':CASES,'gateway':GATEWAY,'protocols':{'legacy':[name for name in CASES if name!=RECEIPT_PROFILE],'persisted_exit_receipt':[RECEIPT_PROFILE]},'diagnostics':{'path':'departure-merge-diagnostics','pins':DIAGNOSTICS_SHA}},'independently declared profile and parent recipe'
    legacy_observer=(root/'acquisition/observe_maintenance_placement.js').read_text();receipt_observer=(root/'acquisition/observe_maintenance_departure.js').read_text();summary={}
    for profile in PROFILES:
        observer=receipt_observer if profile==RECEIPT_PROFILE else legacy_observer
        assert {p.name for p in(root/profile).iterdir()}==set(STAGES),'both declared child stages'
        previous=None;stages={}
        for stage in STAGES:
            assert {p.name for p in(root/profile/stage).iterdir()}==set(MODES),'six independent modes per child'
            results={mode:verify_case(root/profile/stage/mode,profile,stage,mode,observer,None if previous is None else previous[mode]['outputs'])for mode in MODES}
            paired=paired_outputs(results);classification=verify_mode_classification(profile,stage,results,paired)
            stages[stage]=dict(**results['unobserved-a']['stats'],paired=paired,mode_classification=classification,observed_clocks=results['observed-a']['clocks']);previous=results
        summary[profile]=stages
    return dict(profiles=8,full_runs=96,output_files=576,unchanged_file_links=528,transformed_file_links=48,first_stage_unchanged_links=240,second_stage_exact_links=288,stages=summary,diagnostics=verify_diagnostics(root,diagnostics))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT);p.add_argument('--diagnostics',type=Path,default=DIAGNOSTICS);a=p.parse_args()
    print('Departure-merge evidence verified:',verify(a.directory,a.diagnostics))
