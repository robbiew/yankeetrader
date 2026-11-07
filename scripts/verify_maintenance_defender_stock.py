"""Independent fatal-offense and surviving-defender stock-continuation audit.

No acquisition writer or replay model is imported. No force-conservation policy is an input: native inventories and receipts are
audited first, retaining any actual overwrite, loss or absorption explicitly.
"""
import argparse
import copy
import datetime
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import struct

import verify_maintenance_gateway_hazards as gateway
import verify_maintenance_departure_merge as departure

ROOT=Path(__file__).resolve().parents[1]
PARENT_SOURCE=dict(corpus='evolved-combat-controls',profile='route-mercenary-100000',stage='child-2',pins='fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5')
# 'friendly' is the frozen writer's inherited physical-force key; owner -1
# identifies the Xannor defender here, not a friendly Mercenary garrison.
CASES={
 'one-versus-37-whole':dict(friendly=37,owner=-1,governor=0,stock=[37,1],mines=0,clock='00:00:02',mercenaries=1),
 'one-versus-37-empty':dict(friendly=37,owner=-1,governor=0,stock=[0,1],mines=0,clock='00:00:02',mercenaries=1),
 '37-versus-1000-whole':dict(friendly=1000,owner=-1,governor=0,stock=[37,1],mines=0,clock='00:00:02',mercenaries=37),
 'balanced-37-whole':dict(friendly=37,owner=-1,governor=0,stock=[37,1],mines=0,clock='00:00:02',mercenaries=37),
}

PROFILES={name:(('11/05/2026',case['clock']),('11/06/2026',case['clock'])) for name,case in CASES.items()}
STAGES=('child-1','child-2')
GATEWAY=dict(origin=2368,sector=3000,slot=3,name='Gateway Cache',redirects=[[2996,45],[2998,49],[2999,53]],day=308,minute=0,ground=500000,rates=[0,0,0],bank=0)
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
SHA=lambda b:hashlib.sha256(b).hexdigest()
field=gateway.field
rawfield=gateway.rawfield


def encode(value):
    """Independent IEEE-single bit mapping; all declared rationals are exact."""
    assert type(value)in(int,Fraction),'only exact fixture integers or rationals'
    value=Fraction(value)
    if value==0:return bytes(4)
    ieee=int.from_bytes(struct.pack('<f',float(value)),'little')
    exponent=(ieee>>23)&255;assert 1<=exponent<=253,'normal finite jointly representable IEEE/MBF exponent'
    mantissa=(ieee&0x7fffff)|((ieee>>8)&0x800000)
    result=mantissa.to_bytes(3,'little')+bytes([exponent+2])
    bits=int.from_bytes(result[:3],'little');decoded=(-1 if bits&0x800000 else 1)*Fraction((bits&0x7fffff)|(1<<23))*Fraction(2)**(result[3]-152)
    assert decoded==value,'no rounded fixture is admitted by the independent encoder'
    return result


def parent_inputs(profile,mode):
    assert profile in CASES and mode in MODES,'independently declared fractional fixture/mode'
    root=ROOT/'research/yt-maint'/PARENT_SOURCE['corpus'];raw=(root/'pins.json').read_bytes()
    assert SHA(raw)==PARENT_SOURCE['pins'],'immutable original parent manifest'
    pins=json.loads(raw)['files'];out={}
    for name in FILES:
        relative=PARENT_SOURCE['profile']+'/'+PARENT_SOURCE['stage']+'/'+mode+'/after-'+name+'.gz';compressed=(root/relative).read_bytes()
        assert SHA(compressed)==pins[relative],'actual per-mode parent artifact'
        out[name]=gzip.decompress(compressed)
    return out


def fixture_inputs(profile,mode):
    before=parent_inputs(profile,mode);world=bytearray(before['YTDATA.DAT'])
    def put(record,offset,value):
        at=(record-1)*137+offset;world[at:at+4]=encode(value)
    for offset in range(41,65,4):put(2419,offset,3000)
    for sector,offset in((2996,45),(2998,49),(2999,53)):put(51+sector,offset,2368)
    at=(4054-1)*137;world[at:at+137]=b'Gateway Cache'.ljust(41,b' ')+bytes(96)
    for offset,value in((41,308),(73,CASES[profile]['governor']),(77,500000),(85,13),(89,0),(117,0),(129,Fraction(*CASES[profile]['stock']))):put(4054,offset,value)
    for offset,value in((81,CASES[profile]['friendly']),(85,CASES[profile]['owner']),(93,3),(129,CASES[profile]['mines'])):put(3051,offset,value)
    put(2419,81,CASES[profile]['mercenaries'])
    graph_world=bytes(world)
    graph={s:[int(field(graph_world,51+s,o))for o in range(41,65,4)if field(graph_world,51+s,o)>0]for s in range(1,3001)}
    assert set(graph[2368])=={3000}and{s for s,vs in graph.items()if 3000 in vs}=={2368},'declared compulsory first hop and sole gateway predecessor'
    reverse={s:[]for s in graph}
    for source,targets in graph.items():
        for target in targets:assert 1<=target<=3000,'bounded declared graph';reverse[target].append(source)
    for network in(graph,reverse):
        seen={3000};todo=[3000]
        for source in todo:
            for target in network[source]:
                if target not in seen:seen.add(target);todo.append(target)
        assert len(seen)==3000,'fixture preserves both directions of full graph reachability'
    before['YTDATA.DAT']=bytes(world);return before


def verify_fixture(before,profile,mode,edits):
    parent=parent_inputs(profile,mode);expected=fixture_inputs(profile,mode)
    assert before==expected,'independent exact fractional fixture plus unchanged five side files'
    plan=[(2419,o,4)for o in range(41,65,4)]+[(51+s,o,4)for s,o in((2996,45),(2998,49),(2999,53))]+[(4054,0,137)]+[(3051,o,4)for o in(81,85,93,129)]+[(2419,81,4)]
    assert type(edits)is list and[(r.get('record'),r.get('offset'),len(bytes.fromhex(r.get('after',''))))for r in edits]==plan,'complete ordered fifteen-edit plan including final redundant source assignment'
    world=bytearray(parent['YTDATA.DAT'])
    for row in edits:
        assert type(row)is dict and set(row)=={'record','offset','before','after'},'exact explicit edit schema'
        record,offset=row['record'],row['offset'];assert type(record)is int and type(offset)is int and 1<=record<=4151 and 0<=offset<137,'bounded declared write'
        assert all(type(row[k])is str and re.fullmatch('[0-9a-f]+',row[k])for k in('before','after')),'complete lowercase raw edit bytes'
        old,new=bytes.fromhex(row['before']),bytes.fromhex(row['after']);assert len(old)==len(new)>0 and offset+len(old)<=137,'edit stays within one record'
        at=(record-1)*137+offset;assert world[at:at+len(old)]==old,'edit binds actual prior bytes';world[at:at+len(new)]=new
    assert bytes(world)==expected['YTDATA.DAT'],'all fixture bytes are explained without undeclared cleanup'
    return dict(unchanged_links=5,transformed_links=1,edits=15)


def verify_launch(folder,meta,profile,mode,stage):
    folder=Path(folder);argv=json.loads((folder/'launch.json').read_text());assert argv==meta['argv']and argv[0]=='/opt/homebrew/bin/dosbox-staging','actual original host launch'
    assert len(argv)>8 and argv[8].startswith(('mount c /private/tmp/','mount c /tmp/')),'disposable copied mount'
    mount=Path(argv[8][8:]);assert mount.parts[-3:]==(profile,stage,mode),'actual fixture/stage/mode mount identity'
    date_text,clock=PROFILES[profile][STAGES.index(stage)];commands=gateway.commands(date_text,clock)
    expected=[argv[0],'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for command in[argv[8],'c:']+commands+['exit']for v in('-c',command)]
    assert argv==expected and(folder/'COMMANDS.TXT').read_text()=='\n'.join(commands)+'\n','exact predeclared launch/CPU/commands'
    messages=[line.split(' | ',1)[1]for line in(folder/'dosbox.stderr').read_text().splitlines()if' | 'in line]
    assert[shlex.split(m[11:])for m in messages if m.startswith('arguments: ')]==[argv],'actual process arguments corroborate metadata'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1 and len([m for m in messages if m.startswith('CPU: Setting fixed 200000 cycles.')])==1,'actual host version and fixed CPU'
    assert'SDL: dummy video initialised'in messages and "MIXER: Sound output disabled ('nosound' mode)"in messages,'actual dummy output setup'
    assert(folder/'dosbox.stdout').read_bytes()==b'','complete empty host stdout'
    date=datetime.datetime.strptime(date_text,'%m/%d/%Y').date();assert gateway.read_date((folder/'DOSDATE.LOG').read_bytes())==date,'actual original date'
    start=gateway.read_time((folder/'DOSTIME.LOG').read_bytes());expected_start=int(CASES[profile]['clock'][-2:]);assert expected_start-0.06<=start<=expected_start+1,'declared shell time within BIOS quantization'
    elapsed=(gateway.read_date((folder/'ENDDATE.LOG').read_bytes())-date).days*86400+gateway.read_time((folder/'ENDTIME.LOG').read_bytes())-start
    assert 0<elapsed<40,'naturally advancing bounded DOS execution'
    return mount


def verify_observation(observation,profile,stage,before,outputs):
    # The reused utility qualifies runtime source identities and all clocks for
    # this same November5, active1/3/99/100 context; its old pickup recipe name
    # is only a selector for the identical fixed date, never a stock outcome.
    assert profile in CASES,'declared rational stock case'
    return gateway.verify_observation(observation,'pickup',stage,before,outputs)


def verify_controller(controller,mode,observation=None,body=None,receipt=None):
    if mode=='unobserved':gateway.clocks.neutral.verify_controller(controller,mode);return None
    base=dict(controller);wait=base.pop('natural_exit_wait',None)
    assert type(wait)is dict and set(wait)=={'checks','elapsed_ms'},'recorded bounded post-detach natural-exit wait'
    assert type(wait['checks'])is int and 1<=wait['checks']<=100000,'actual finite positive liveness probe count'
    assert type(wait['elapsed_ms'])in(int,float)and math.isfinite(wait['elapsed_ms'])and 0<=wait['elapsed_ms']<=2000,'natural disappearance within the unchanged finite wait budget'
    return departure.verify_receipt_controller(base,mode,observation,body,receipt)


def verify_semantics(profile,stage,before,outputs,trace,source_timer=None):
    date=datetime.datetime.strptime(PROFILES[profile][STAGES.index(stage)][0],'%m/%d/%Y').date();old=before['YTDATA.DAT'];world=outputs['YTDATA.DAT'];initial=departure.physical(old);final=departure.physical(world)
    assert world[137:51*137]==old[137:51*137],'inactive human records unchanged'
    assert outputs['YTNAME.DAT']==before['YTNAME.DAT']and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT']and outputs['YTRMSG.DAT']==before['YTRMSG.DAT']==b'','exact names, journal rotation and empty private messages'
    assert field(world,1,81)==gateway.source_day(date)and field(world,1,45)==26,'source calendar watermark'
    at=(4054-1)*137
    assert old[at:at+41]==world[at:at+41]==b'Gateway Cache'.ljust(41,b' ')and field(old,4054,73)==field(world,4054,73)==0,'pickup does not retitle the controlled ordinary planet'
    assert field(world,3051,93)==field(old,3051,93)==3 and field(world,4054,77)>0,'actual surviving gateway planet/link/ground'
    timer=rawfield(world,4054,89)if source_timer is None else bytes.fromhex(source_timer)
    produced=gateway.stock_after_economy(old,date,timer)
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
        planet=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "(The Wanderer|Mercenary Base|Gateway Cache)"',line)
        mine=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor hit sector mines in sector ([1-9][0-9]*)!',line)
        if foreign:xloss+=int(foreign[1]);defense_mloss+=int(foreign[2]);i+=1
        elif planet:
            assert xlines[i+1]==b' *** Xannor fighters destroyed!','complete exact planetary fatal pair';xloss+=int(planet[1]);gateway_attacked|=planet[2]==b'Gateway Cache';i+=2
        elif mine:
            assert xlines[i+1]==b' *** The Xannor were killed!','complete exact Xannor mine fatal pair';xloss+=int(mine[1]);i+=2
        else:raise AssertionError('unknown Xannor phase outcome: '+repr(line))
    current=initial[-2]-defense_mloss;pending=False;offenses=[];mine_losses=offense_losses=pickup=0;captures=[];mine_events=[];activations=[];i=0
    def stamp(amount):
        nonlocal current,pending,offense_losses
        if pending:
            assert 0<amount<=current,'declared offensive winner must survive without invented force';offense_losses+=current-amount;pending=False
        else:assert current==amount,'source force stamp agrees with all preceding phase actions'
        current=amount
    while i<len(mlines):
        line=mlines[i]
        move=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries moving from sector ([1-9][0-9]*) *',line)
        mine=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) mercenaries hit sector mines in sector ([1-9][0-9]*)!',line)
        attack=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Mercenaries attacking ([1-9][0-9]*) fighters beloning to The Xannor!',line)
        capture=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries captured planet Gateway Cache!',line)
        taking=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries taking ([0-9]+) fighters from planet Gateway Cache!',line)
        if move:stamp(int(move[1]));activations.append(dict(force=current,sector=int(move[2])));i+=1
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
            stamp(int(attack[1]));result=mlines[i+1]
            assert result in (b' *** The Mercenaries Won!',b' *** The Mercenaries Lost!'),'exact original offensive result receipt'
            won=result==b' *** The Mercenaries Won!'
            if won:xloss+=int(attack[2]);pending=True
            else:
                surviving=field(world,3051,81)
                assert field(world,3051,85)==-1 and 0<surviving<=int(attack[2]),'actual surviving Xannor defenders'
                xloss+=int(attack[2])-int(surviving);offense_losses+=current;current=0;pending=False
            offenses.append(dict(attacker=int(attack[1]),defenders=int(attack[2]),won=won));i+=2
        elif capture:stamp(int(capture[1]));captures.append(current);i+=1
        elif taking:
            stamp(int(taking[1]));assert captures and captures[-1]==current,'stock taking follows its captured-planet force stamp'
            amount=int(taking[2]);assert amount>0,'positive actual taking receipt';pickup+=amount;current+=amount;i+=1
        elif line.startswith(b' *** ')or(b'Mercenaries captured planet'in line)or(b'Mercenaries taking'in line):raise AssertionError('unknown Mercenary phase outcome: '+repr(line))
        else:i+=1
    stamp(final[-2])
    origins=[sector for sector in range(1,3001)if field(old,51+sector,81)>0 and field(old,51+sector,85)==-2]
    if activations:
        assert len(origins)==1 and activations[0]['sector']==origins[0],'first Mercenary activation starts at its actual inherited physical source'
        assert all(a['sector']>b['sector']for a,b in zip(activations,activations[1:])),'Mercenary reactivations follow actual descending scan order'
    if captures and final[-2]:assert field(world,3051,81)==final[-2]and field(world,3051,85)==-2,'gateway capture terminates at its actual physical sector'
    if not gateway_attacked:assert field(world,4054,77)==gateway.ground_after_economy(old,date,timer),'pickup does not debit independently grown gateway ground'
    assert initial[-1]+regen[0]-xloss==final[-1]and initial[0]==final[0],'actual physical Xannor and neutral totals reconcile'
    assert initial[-2]-defense_mloss-mine_losses-offense_losses+pickup==final[-2],'all Mercenary force sources/losses reconcile'
    assert produced-pickup==stock,'independent pre-pickup economy minus exact printed debit equals saved stock'
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1 and tuple(int(n.replace(b',',b''))for n in rows[0])==(100*final[-1],100*final[-2]),'scores bind actual physical survivors'
    relevant=lambda data:tuple(line for line in data.split(b'\r\n')if line.startswith(b' *** ')or b'Mercenaries captured planet'in line or b'Mercenaries taking'in line)
    assert relevant(outputs['YTNEWS.DAT'])==relevant(trace),'complete literal newspaper/console outcome agreement'
    return dict(physical=final,prior_physical=initial,xannor_losses=xloss,earlier_defense_mercenary_losses=defense_mloss,mine_losses=mine_losses,observed_offensive_losses=offense_losses,pickup=pickup,captured=len(captures),mine_events=mine_events,activations=activations,pre_pickup_stock=produced,saved_stock=str(stock),stock_clock_provenance='authenticated source callback'if source_timer is not None else'saved timestamp only; corroboration requires equal source-observed outputs',selection=dict(capture=bool(captures),pickup=bool(pickup),mine=bool(mine_events),offense=bool(offenses)),offenses=offenses)


def qualify(profile,stage,stats,before,outputs,trace):
    case=CASES[profile];world=outputs['YTDATA.DAT'];old=before['YTDATA.DAT']
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    assert SHA(original)==gateway.clocks.GUESTS['YTMAINT.EXE'] and original[0x98fe:0x9903]==b'Lost!' and original[0x9908:0x991d]==b' *** The Mercenaries ','exact loss literal belongs to pinned original'
    assert stats['physical'][-2]==0 and stats['physical'][0]==0,'actual extinct Mercenary and absent neutral physical inventory'
    assert stats['pickup']==stats['captured']==stats['mine_losses']==0 and stats['mine_events']==[],'defeat never enters pickup or invented mine branch'
    assert rawfield(world,4054,73)==rawfield(old,4054,73)==bytes(4),'governor bytes remain unchanged'
    assert rawfield(world,4054,129)==encode(int(stats['pre_pickup_stock'])),'stock retains exact produced bytes instead of pickup-clear residue'
    expected_defenders=case['friendly']-(0 if case['mercenaries']==1 else 36)
    assert stats['gateway_defenders']==expected_defenders and field(world,3051,85)==-1,'actual surviving defensive force and owner'
    if stage=='child-1':
        assert stats['offenses']==[dict(attacker=case['mercenaries'],defenders=case['friendly'],won=False)],'one selected fatal Mercenary offense'
        assert stats['activations']==[dict(force=case['mercenaries'],sector=2368)] and stats['observed_offensive_losses']==case['mercenaries'],'attacker clears on its actual first route'
        assert trace.count(b' *** The Mercenaries Lost!')==1 and b' *** The Mercenaries Won!' not in trace,'exact losing receipt'
        assert rawfield(world,2419,81)==rawfield(world,2419,85)==bytes.fromhex('00002800'),'original source859e departure residue'
    else:
        assert stats['offenses']==stats['activations']==[] and stats['observed_offensive_losses']==0,'no invented extinct-force activity on unchanged next-day handoff'
        assert stats['physical']==stats['prior_physical'],'selected next day preserves actual surviving inventories'
    return dict(attacker_extinct=True,defenders=expected_defenders,stock_uncollected=True)


def verify_case(folder,profile,mode,observer,stage,parent_outputs=None):
    folder=Path(folder);assert profile in CASES and mode in MODES,'declared exact fractional profile/mode'
    meta=json.loads((folder/'capture.json').read_text())
    keys={'recipe','profile','stage','mode','parent','parent_mode','parent_pins','parent_source','applied_fixture','fixture_edits','date','clock','cycles','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'}
    assert set(meta)==keys,'exact capture metadata schema'
    assert(meta['recipe'],meta['profile'],meta['stage'],meta['mode'],meta['parent'],meta['parent_mode'])==('maintenance-defender-stock-controls-v1',profile,stage,mode,'fixture-parent' if stage=='child-1' else 'child-1',mode),'actual capture recipe and independently declared identity'
    assert meta['parent_source']==PARENT_SOURCE and meta['parent_pins']==PARENT_SOURCE['pins'],'actual original evolved-world lineage'
    assert(meta['date'],meta['clock'],meta['cycles'])==(*PROFILES[profile][STAGES.index(stage)],200000),'actual calendar/clock/fixed CPU recipe'
    assert meta['host_sha256']==gateway.clocks.neutral.HOST_SHA and type(meta['elapsed_seconds'])in(int,float)and 0<meta['elapsed_seconds']<40,'actual pinned host and bounded lifecycle'
    assert meta['guests']==gateway.clocks.GUESTS,'unchanged original guests'
    for name,digest in gateway.clocks.GUESTS.items():assert SHA((ROOT/'archive/dos-original'/name).read_bytes())==digest,'immutable original executable bytes'
    names=gateway.COMMON|{'before-'+n+'.gz'for n in FILES}|{'after-'+n+'.gz'for n in FILES}
    if MODES[mode]!='unobserved':names|={'host-time.json.gz','host-flush.json','loaded-observer.js'}
    assert set(meta['files'])==names and {p.name for p in folder.iterdir()}==names|{'capture.json'},'complete retained artifact inventory'
    for name in names:assert SHA((folder/name).read_bytes())==meta['files'][name],'actual artifact digest '+name
    before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in FILES};outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in FILES}
    assert meta['inputs']=={n:SHA(b)for n,b in before.items()}and meta['outputs']=={n:SHA(b)for n,b in outputs.items()},'all six decompressed file identities'
    if stage=='child-1':
        assert meta['applied_fixture']is True,'first-stage intervention explicit'
        lineage=verify_fixture(before,profile,mode,meta['fixture_edits'])
    else:
        assert meta['applied_fixture']is False and meta['fixture_edits']==[] and before==parent_outputs,'unchanged exact six-file same-mode handoff'
        lineage=dict(unchanged_links=6,transformed_links=0)
    mount=verify_launch(folder,meta,profile,mode,stage)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','DOS itself completed and returned naturally'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'],'exact retained process controller'
    observation=None;body=None;clocks=None;receipt=None
    if MODES[mode]!='unobserved':
        body=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(body)
        config=dict(observe=MODES[mode]=='observed',output=str(mount/'host-time.json'),flush_output=str(mount/'host-flush.json'))
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'actual frozen observer and configured receipt paths'
        if MODES[mode]=='observed':clocks=verify_observation(observation,profile,stage,before,outputs)
        else:
            assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}and observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is False and observation['exit_code']==0 and observation['events']==observation['errors']==[]and observation['dropped']==0,'attach-only has no DOS hooks, events or losses'
            gateway.clocks.neutral.verify_module(observation['module'])
        receipt=(folder/'host-flush.json').read_bytes()
    lifecycle=verify_controller(controller,MODES[mode],observation,body,receipt)
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n')and trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'),'complete original maintenance transcript'
    stats=verify_semantics(profile,stage,before,outputs,trace,None if clocks is None else clocks['gateway_timer'])
    stats['gateway_defenders']=int(field(outputs['YTDATA.DAT'],3051,81))
    stats['qualification']=qualify(profile,stage,stats,before,outputs,trace)
    return dict(before=before,outputs=outputs,stats=stats,clocks=clocks,lineage=lineage,lifecycle=lifecycle)


DEFAULT=ROOT/'research/yt-maint/defender-stock-controls'
PINS_SHA='43d78b16ca827a08c30707fdd7e947b10f454d489995f9302482d6525f8fc54a'
SOURCES={'recover_maintenance_defender_stock.py','verify_maintenance_clock_neutral.py','capture_maintenance_stock_conversion.mjs','observe_maintenance_departure.js'}

def verify(directory=DEFAULT):
    root=Path(directory)
    assert SHA((root/'pins.json').read_bytes())==PINS_SHA,'immutable native corpus manifest'
    pins=json.loads((root/'pins.json').read_text())['files']
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}
    assert actual==set(pins),'complete native inventory'
    for name,digest in pins.items():assert SHA((root/name).read_bytes())==digest,'immutable artifact '+name
    recipe=json.loads((root/'recipe.json').read_text())
    expected=dict(recipe='maintenance-defender-stock-controls-v1',cases=CASES,
        profiles={name:[list(row) for row in rows] for name,rows in PROFILES.items()},
        stages=list(STAGES),parent_source=PARENT_SOURCE,gateway=GATEWAY,modes=MODES,
        sources={name:SHA((root/'sources'/name).read_bytes()) for name in SOURCES})
    assert recipe==expected,'independently declared prelaunch recipe'
    assert {p.name for p in root.iterdir()}==set(CASES)|{'pins.json','recipe.json','sources'},'exact retained case inventory'
    assert {p.name for p in (root/'sources').iterdir()}==SOURCES,'exact executed acquisition sources'
    observer=(root/'sources/observe_maintenance_departure.js').read_text();summary={}
    for profile in CASES:
        assert {p.name for p in (root/profile).iterdir()}==set(STAGES),'both declared stages retained'
        previous=None;rows_by_stage={}
        for stage in STAGES:
            folder=root/profile/stage
            assert {p.name for p in folder.iterdir()}==set(MODES),'complete six-mode matrix'
            rows={mode:verify_case(folder/mode,profile,mode,observer,stage,None if previous is None else previous[mode]['outputs']) for mode in MODES}
            paired=departure.paired_outputs(rows);assert paired['equal'],'complete six-mode native neutrality'
            rows_by_stage[stage]=dict(**rows['unobserved-a']['stats'],paired=paired,observed_clocks=rows['observed-a']['clocks'])
            previous=rows
        summary[profile]=rows_by_stage
    return summary

if __name__=='__main__':
    result=verify()
    for case,stats in result.items():
        print(case,{stage:row['qualification'] for stage,row in stats.items()})
