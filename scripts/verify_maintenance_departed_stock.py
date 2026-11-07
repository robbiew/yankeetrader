"""Independent departed-garrison/stock fixture, capture and composition audit.

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
CASES={'second-two-whole': {'friendly': 37, 'governor': 0, 'stock': [37, 1], 'clock': '00:00:02'}, 'second-four-whole': {'friendly': 37, 'governor': 0, 'stock': [37, 1], 'clock': '00:00:04'}, 'second-six-whole': {'friendly': 37, 'governor': 0, 'stock': [37, 1], 'clock': '00:00:06'}, 'second-eight-whole': {'friendly': 37, 'governor': 0, 'stock': [37, 1], 'clock': '00:00:08'}, 'second-two-half': {'friendly': 37, 'governor': 0, 'stock': [1, 2], 'clock': '00:00:02'}, 'second-four-owned': {'friendly': 37, 'governor': -2, 'stock': [37, 1], 'clock': '00:00:04'}, 'second-four-empty': {'friendly': 37, 'governor': 0, 'stock': [0, 1], 'clock': '00:00:04'}, 'second-four-half': {'friendly': 37, 'governor': 0, 'stock': [1, 2], 'clock': '00:00:04'}}
PROFILES={name:(('11/05/2026',case['clock']),) for name,case in CASES.items()}
STAGES=('child-1',)
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
    for offset,value in((81,CASES[profile]['friendly']),(85,-2),(93,3),(129,0)):put(3051,offset,value)
    put(2419,81,97337)
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


def verify_launch(folder,meta,profile,mode):
    folder=Path(folder);argv=json.loads((folder/'launch.json').read_text());assert argv==meta['argv']and argv[0]=='/opt/homebrew/bin/dosbox-staging','actual original host launch'
    assert len(argv)>8 and argv[8].startswith(('mount c /private/tmp/','mount c /tmp/')),'disposable copied mount'
    mount=Path(argv[8][8:]);assert mount.parts[-3:]==(profile,'child-1',mode),'actual fixture/stage/mode mount identity'
    commands=gateway.commands('11/05/2026',CASES[profile]['clock'])
    expected=[argv[0],'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for command in[argv[8],'c:']+commands+['exit']for v in('-c',command)]
    assert argv==expected and(folder/'COMMANDS.TXT').read_text()=='\n'.join(commands)+'\n','exact predeclared launch/CPU/commands'
    messages=[line.split(' | ',1)[1]for line in(folder/'dosbox.stderr').read_text().splitlines()if' | 'in line]
    assert[shlex.split(m[11:])for m in messages if m.startswith('arguments: ')]==[argv],'actual process arguments corroborate metadata'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1 and len([m for m in messages if m.startswith('CPU: Setting fixed 200000 cycles.')])==1,'actual host version and fixed CPU'
    assert'SDL: dummy video initialised'in messages and "MIXER: Sound output disabled ('nosound' mode)"in messages,'actual dummy output setup'
    assert(folder/'dosbox.stdout').read_bytes()==b'','complete empty host stdout'
    date=datetime.date(2026,11,5);assert gateway.read_date((folder/'DOSDATE.LOG').read_bytes())==date,'actual original date'
    start=gateway.read_time((folder/'DOSTIME.LOG').read_bytes());expected_start=int(CASES[profile]['clock'][-2:]);assert expected_start-0.06<=start<=expected_start+1,'declared shell time within BIOS quantization'
    elapsed=(gateway.read_date((folder/'ENDDATE.LOG').read_bytes())-date).days*86400+gateway.read_time((folder/'ENDTIME.LOG').read_bytes())-start
    assert 0<elapsed<40,'naturally advancing bounded DOS execution'
    return mount


def verify_observation(observation,profile,before,outputs):
    # The reused utility qualifies runtime source identities and all clocks for
    # this same November5, active1/3/99/100 context; its old pickup recipe name
    # is only a selector for the identical fixed date, never a stock outcome.
    assert profile in CASES,'declared rational stock case'
    return gateway.verify_observation(observation,'pickup','child-1',before,outputs)


def verify_controller(controller,mode,observation=None,body=None,receipt=None):
    if mode=='unobserved':gateway.clocks.neutral.verify_controller(controller,mode);return None
    base=dict(controller);wait=base.pop('natural_exit_wait',None)
    assert type(wait)is dict and set(wait)=={'checks','elapsed_ms'},'recorded bounded post-detach natural-exit wait'
    assert type(wait['checks'])is int and 1<=wait['checks']<=100000,'actual finite positive liveness probe count'
    assert type(wait['elapsed_ms'])in(int,float)and math.isfinite(wait['elapsed_ms'])and 0<=wait['elapsed_ms']<=2000,'natural disappearance within the unchanged finite wait budget'
    return departure.verify_receipt_controller(base,mode,observation,body,receipt)


def verify_semantics(profile,before,outputs,trace,source_timer=None):
    """Measure actual force/stock outcomes before qualifying a source rule."""
    old=before['YTDATA.DAT'];world=outputs['YTDATA.DAT'];initial=departure.physical(old);final=departure.physical(world)
    case=CASES[profile];stock=Fraction(*case['stock']);assert field(old,4054,129)==stock and field(old,4054,73)==case['governor'],'exact rational stock and declared planetary governor'
    assert field(old,3051,81)==case['friendly']and field(old,3051,85)==-2 and field(old,2419,81)==97337 and field(old,2419,85)==-2,'both actual pre-maintenance friendly physical forces'
    assert world[137:51*137]==old[137:51*137],'inactive human records remain unchanged'
    assert outputs['YTNAME.DAT']==before['YTNAME.DAT']and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT']and outputs['YTRMSG.DAT']==before['YTRMSG.DAT']==b'','unchanged names, actual yesterday rotation and empty private inbox'
    assert field(world,1,81)==309 and field(world,1,45)==26,'actual calendar/base watermark'
    assert world[(4054-1)*137:(4054-1)*137+41]==b'Gateway Cache'.ljust(41,b' ')and field(world,4054,85)==13 and field(world,3051,93)==3,'actual surviving Cache title/link'
    assert field(world,4054,73)==case['governor']and rawfield(world,4054,73)==rawfield(old,4054,73)and field(world,4054,117)==0,'pickup preserves exact government bytes and empty bank'
    timer=rawfield(world,4054,89)if source_timer is None else bytes.fromhex(source_timer)
    assert gateway.stock_after_economy(old,datetime.date(2026,11,5),timer)==float(stock),'zero-rate/bank production preserves exact pre-pickup stock'
    assert field(world,4054,77)==gateway.ground_after_economy(old,datetime.date(2026,11,5),timer),'Cache ground follows independent economy, not invented capture damage'
    assert[field(world,4054,o)for o in(45,49,53)]==[1,1,1],'source minimum rates remain distinct from pickup'
    lines=trace.split(b'\r\n');marker=lines.index(b'Mercenary Maintenance...');xlines=lines[:marker];mlines=lines[marker:]
    xloss=earlier_mloss=0;earlier=[];i=0
    while i<len(xlines):
        line=xlines[i]
        if not line.startswith(b' *** '):i+=1;continue
        planet=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "(The Wanderer|Mercenary Base)"',line)
        defense=re.fullmatch(rb' \*\*\* Mercenaries: lost ([0-9]+), dstrd ([0-9]+) \((Xannor|Plyr) ftrs dstrd\)',line)
        if planet:
            assert xlines[i+1]==b' *** Xannor fighters destroyed!','complete earlier fatal home attack';xloss+=int(planet[1]);earlier.append(dict(kind='planet',xannor_loss=int(planet[1]),name=planet[2].decode()));i+=2
        else:
            assert defense,'unknown earlier Xannor event must not disappear into an inferred merge'
            xloss+=int(defense[1]);earlier_mloss+=int(defense[2]);earlier.append(dict(kind='foreign-defense',xannor_loss=int(defense[1]),mercenary_loss=int(defense[2])));i+=1
    moves=[];captures=[];takings=[];mines=[];attacks=[];i=0
    while i<len(mlines):
        line=mlines[i]
        move=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries moving from sector ([1-9][0-9]*) *',line)
        capture=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries captured planet (Gateway Cache|The Wanderer|Mercenary Base)!',line)
        take=re.fullmatch(rb'  -  ([1-9][0-9]*) Mercenaries taking ([0-9]+) fighters from planet (Gateway Cache|The Wanderer|Mercenary Base)!',line)
        mine=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) mercenaries hit sector mines in sector ([1-9][0-9]*)!',line)
        attack=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Mercenaries attacking ([1-9][0-9]*) fighters beloning to The Xannor!',line)
        if move:moves.append(dict(actor=int(move[1]),origin=int(move[2]),ordinal=i));i+=1
        elif capture:captures.append(dict(actor=int(capture[1]),title=capture[2].decode(),ordinal=i));i+=1
        elif take:
            assert int(take[2])>0,'zero taking receipt is not an original positive-amount publication'
            takings.append(dict(actor=int(take[1]),amount=int(take[2]),title=take[3].decode(),ordinal=i));i+=1
        elif mine:
            loss=re.fullmatch(rb' \*\*\* Lost a total of ([1-9][0-9]*) fighters!',mlines[i+1]);fatal=mlines[i+1]==b' *** The mercenariers were killed!'
            assert loss or fatal,'complete exact later mine result'
            mines.append(dict(actor=int(mine[1]),sector=int(mine[2]),loss=int(mine[1])if fatal else int(loss[1]),fatal=fatal,ordinal=i));i+=2
        elif attack:
            assert mlines[i+1]in(b' *** The Mercenaries Won!',b' *** The Mercenaries were killed!'),'exact observed offensive battle result'
            attacks.append(dict(actor=int(attack[1]),defenders=int(attack[2]),won=mlines[i+1]==b' *** The Mercenaries Won!',ordinal=i));i+=2
        elif line.startswith(b' *** ')or b'Mercenaries captured planet'in line or b'Mercenaries taking'in line:raise AssertionError('unknown Mercenary outcome '+repr(line))
        else:i+=1
    assert moves,'at least one actual departure selected in this gateway route control'
    assert moves[0]['origin']in(2368,3000),'first departure binds an original physical source'
    assert all(1<=row['origin']<=3000 and 0<row['actor']<=1000000 for row in moves),'bounded actual physical departure stamps'
    relevant=lambda data:tuple(line for line in data.split(b'\r\n')if line.startswith(b' *** ')or b'Mercenaries captured planet'in line or b'Mercenaries taking'in line)
    assert relevant(outputs['YTNEWS.DAT'])==relevant(trace),'all public/console outcomes retain exact literal identity and order'
    assert initial[-1]-xloss-sum(a['defenders']for a in attacks if a['won'])==final[-1]and initial[0]==final[0]==0,'actual Xannor casualties and physical totals reconcile'
    public_lines=outputs['YTNEWS.DAT'].split(b'\r\n')
    assert len(public_lines)>=5 and re.fullmatch(rb'[0-9]{2}:[0-9]{2}:[0-9]{2} 11-05-2026: Maintenance Program Ran \(Revision 03/14/94\)',public_lines[0])and public_lines[1:3]==[b'  -  Xannor report:',b'Calculated Dynamic Xannor Regeneration is 0 fighters.'],'exact original public phase headers'
    allowed=set(relevant(trace))|{b'  -  Mercenary Report:',b'\x1a'}
    assert all(line in allowed for line in public_lines[3:]),'no undocumented friendly-merge or alternate public message may be ignored'
    public_pickup=sum(row['amount']for row in takings);quantified_mine_losses=sum(row['loss']for row in mines)
    difference=initial[-2]-earlier_mloss-quantified_mine_losses+public_pickup-final[-2]
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1 and tuple(int(n.replace(b',',b''))for n in rows[0])==(100*final[-1],100*final[-2]),'scores bind all actual saved physical inventory'
    cleared=rawfield(world,4054,129)==bytes.fromhex('00008000')
    assert cleared or field(world,4054,129)==stock,'Cache stock is either actually fully cleared or remains the independently produced amount'
    return dict(stock_numerator=stock.numerator,stock_denominator=stock.denominator,stock_raw=rawfield(old,4054,129).hex(),initial_friendly=case['friendly'],governor=case['governor'],initial_physical=initial,final_physical=final,earlier_xannor_events=earlier,xannor_losses=xloss,earlier_mercenary_losses=earlier_mloss,mercenary_moves=moves,captures=captures,taking_receipts=takings,public_pickup=public_pickup,quantified_mine_losses=quantified_mine_losses,offensive_battles=attacks,observed_unexplained_inventory_difference=difference,stock_cleared=cleared,final_mercenary_sectors=[sector for sector in range(1,3001)if field(world,51+sector,85)==-2 and field(world,51+sector,81)>0],source_departure_force_raw=rawfield(world,2419,81).hex(),source_departure_owner_raw=rawfield(world,2419,85).hex(),stock_clock_provenance='authenticated source callback'if source_timer is not None else'saved timestamp corroborated by equal source-observed outputs')


def qualify_composition(profile,stats):
    case=CASES[profile];whole=Fraction(*case['stock']).__floor__()
    moves=stats['mercenary_moves'];departed=case['clock'] in ('00:00:04','00:00:08')
    assert stats['observed_unexplained_inventory_difference']==0,'all actual inventory reconciles'
    assert stats['stock_cleared'],'native complete stock clear'
    if departed:
        expected_moves=[(37,3000),(97337,2368)]+([(37,2082),(37,1622)] if case['clock']=='00:00:08' else [(37,13)])
        assert [(m['actor'],m['origin']) for m in moves]==expected_moves,'departed garrison and later same-scan reactivation'
        actor=97337
        assert stats['captures']==[dict(actor=97337,title='Gateway Cache',ordinal=5)],'empty physical arrival emits capture even with Mercenary governor'
        assert stats['final_mercenary_sectors']==([2862,3000] if case['clock']=='00:00:08' else [1810,3000]),'separate departed and arriving groups survive'
    else:
        assert [(m['actor'],m['origin']) for m in moves]==[(97337,2368)],'held counter-control'
        actor=97374
        assert stats['captures']==[] and stats['final_mercenary_sectors']==[3000],'held force suppresses capture'
    assert [(r['actor'],r['amount']) for r in stats['taking_receipts']]==([] if not whole else [(actor,whole)]),'receipt excludes departed garrison'
    assert stats['earlier_mercenary_losses']==0 and not stats['quantified_mine_losses'] and stats['offensive_battles']==[],'no concealed combat loss'
    assert stats['final_physical'][-2]==97374+whole,'stock adds once to total physical inventory'
    return dict(departed=departed,receipt_actor=actor,whole_stock_added=whole)


def verify_case(folder,profile,mode,observer):
    folder=Path(folder);assert profile in CASES and mode in MODES,'declared exact fractional profile/mode'
    meta=json.loads((folder/'capture.json').read_text())
    keys={'recipe','profile','stage','mode','parent','parent_mode','parent_pins','parent_source','applied_fixture','fixture_edits','date','clock','cycles','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'}
    assert set(meta)==keys,'exact capture metadata schema'
    assert(meta['recipe'],meta['profile'],meta['stage'],meta['mode'],meta['parent'],meta['parent_mode'])==(RECIPES[CORPUS][0]['recipe'],profile,'child-1',mode,'fixture-parent',mode),'actual capture recipe and independently declared identity'
    assert meta['parent_source']==PARENT_SOURCE and meta['parent_pins']==PARENT_SOURCE['pins'],'actual original evolved-world lineage'
    assert(meta['date'],meta['clock'],meta['cycles'])==('11/05/2026',CASES[profile]['clock'],200000),'actual calendar/clock/fixed CPU recipe'
    assert meta['host_sha256']==gateway.clocks.neutral.HOST_SHA and type(meta['elapsed_seconds'])in(int,float)and 0<meta['elapsed_seconds']<40,'actual pinned host and bounded lifecycle'
    assert meta['guests']==gateway.clocks.GUESTS,'unchanged original guests'
    for name,digest in gateway.clocks.GUESTS.items():assert SHA((ROOT/'archive/dos-original'/name).read_bytes())==digest,'immutable original executable bytes'
    names=gateway.COMMON|{'before-'+n+'.gz'for n in FILES}|{'after-'+n+'.gz'for n in FILES}
    if MODES[mode]!='unobserved':names|={'host-time.json.gz','host-flush.json','loaded-observer.js'}
    assert set(meta['files'])==names and {p.name for p in folder.iterdir()}==names|{'capture.json'},'complete retained artifact inventory'
    for name in names:assert SHA((folder/name).read_bytes())==meta['files'][name],'actual artifact digest '+name
    before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in FILES};outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in FILES}
    assert meta['inputs']=={n:SHA(b)for n,b in before.items()}and meta['outputs']=={n:SHA(b)for n,b in outputs.items()},'all six decompressed file identities'
    assert meta['applied_fixture']is True,'declared one-time fixture intervention is never unchanged inheritance'
    lineage=verify_fixture(before,profile,mode,meta['fixture_edits']);mount=verify_launch(folder,meta,profile,mode)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','DOS itself completed and returned naturally'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'],'exact retained process controller'
    observation=None;body=None;clocks=None;receipt=None
    if MODES[mode]!='unobserved':
        body=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(body)
        config=dict(observe=MODES[mode]=='observed',output=str(mount/'host-time.json'),flush_output=str(mount/'host-flush.json'))
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'actual frozen observer and configured receipt paths'
        if MODES[mode]=='observed':clocks=verify_observation(observation,profile,before,outputs)
        else:
            assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}and observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is False and observation['exit_code']==0 and observation['events']==observation['errors']==[]and observation['dropped']==0,'attach-only has no DOS hooks, events or losses'
            gateway.clocks.neutral.verify_module(observation['module'])
        receipt=(folder/'host-flush.json').read_bytes()
    lifecycle=verify_controller(controller,MODES[mode],observation,body,receipt)
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n')and trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'),'complete original maintenance transcript'
    stats=verify_semantics(profile,before,outputs,trace,None if clocks is None else clocks['gateway_timer'])
    stats['composition']=qualify_composition(profile,stats)
    world=outputs['YTDATA.DAT'];departed=stats['composition']['departed'];whole=stats['composition']['whole_stock_added']
    assert field(world,3051,81)==(97337 if departed else 97374)+whole,'exact gateway inventory excludes departed force'
    if departed:
        sector=2862 if CASES[profile]['clock']=='00:00:08' else 1810
        assert field(world,51+sector,81)==37,'departed force survives separately without overwrite'

    return dict(before=before,outputs=outputs,stats=stats,clocks=clocks,lineage=lineage,lifecycle=lifecycle)


RECIPES={'departed-stock-controls': ({'recipe': 'maintenance-departed-stock-controls-v1', 'cases': {'second-two-whole': {'friendly': 37, 'governor': 0, 'stock': [37, 1], 'clock': '00:00:02'}, 'second-four-whole': {'friendly': 37, 'governor': 0, 'stock': [37, 1], 'clock': '00:00:04'}, 'second-six-whole': {'friendly': 37, 'governor': 0, 'stock': [37, 1], 'clock': '00:00:06'}, 'second-eight-whole': {'friendly': 37, 'governor': 0, 'stock': [37, 1], 'clock': '00:00:08'}, 'second-two-half': {'friendly': 37, 'governor': 0, 'stock': [1, 2], 'clock': '00:00:02'}, 'second-four-owned': {'friendly': 37, 'governor': -2, 'stock': [37, 1], 'clock': '00:00:04'}}, 'profiles': {'second-two-whole': [['11/05/2026', '00:00:02']], 'second-four-whole': [['11/05/2026', '00:00:04']], 'second-six-whole': [['11/05/2026', '00:00:06']], 'second-eight-whole': [['11/05/2026', '00:00:08']], 'second-two-half': [['11/05/2026', '00:00:02']], 'second-four-owned': [['11/05/2026', '00:00:04']]}, 'stages': ['child-1'], 'parent_source': {'corpus': 'evolved-combat-controls', 'profile': 'route-mercenary-100000', 'stage': 'child-2', 'pins': 'fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5'}, 'gateway': {'origin': 2368, 'sector': 3000, 'slot': 3, 'name': 'Gateway Cache', 'redirects': [[2996, 45], [2998, 49], [2999, 53]], 'day': 308, 'minute': 0, 'ground': 500000, 'rates': [0, 0, 0], 'bank': 0}, 'modes': {'unobserved-a': 'unobserved', 'observed-a': 'observed', 'attach-only': 'attach-only', 'observed-b': 'observed', 'unobserved-b': 'unobserved', 'observed-c': 'observed'}, 'sources': {'capture_maintenance_stock_conversion.mjs': 'a9a66df50fc201897f3f4ed8e9822e866358c1511d65c5f4e5cb0de95821da10', 'observe_maintenance_departure.js': '9bb0aa586c603a3a14693fd621ea4f81996d4f41c8735be5b20e99f14b283d03', 'recover_maintenance_departed_stock.py': '786517bc2e93a94dc4b3515108e98090969342b7a0ed50ba3d3f5e45a7a9c4ab', 'verify_maintenance_clock_neutral.py': '9efae1ecd4dce4a8619b43bfba8bde59a6aa00c52fc48fa464622e81cd6d1143'}}, '5890dcf2502518a8574ecdd01e0c1668957fa757a1d2ecff8abb901aa4f0503d'), 'departed-stock-zero-controls': ({'recipe': 'maintenance-departed-stock-zero-controls-v1', 'cases': {'second-four-empty': {'friendly': 37, 'governor': 0, 'stock': [0, 1], 'clock': '00:00:04'}, 'second-four-half': {'friendly': 37, 'governor': 0, 'stock': [1, 2], 'clock': '00:00:04'}}, 'profiles': {'second-four-empty': [['11/05/2026', '00:00:04']], 'second-four-half': [['11/05/2026', '00:00:04']]}, 'stages': ['child-1'], 'parent_source': {'corpus': 'evolved-combat-controls', 'profile': 'route-mercenary-100000', 'stage': 'child-2', 'pins': 'fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5'}, 'gateway': {'origin': 2368, 'sector': 3000, 'slot': 3, 'name': 'Gateway Cache', 'redirects': [[2996, 45], [2998, 49], [2999, 53]], 'day': 308, 'minute': 0, 'ground': 500000, 'rates': [0, 0, 0], 'bank': 0}, 'modes': {'unobserved-a': 'unobserved', 'observed-a': 'observed', 'attach-only': 'attach-only', 'observed-b': 'observed', 'unobserved-b': 'unobserved', 'observed-c': 'observed'}, 'sources': {'capture_maintenance_stock_conversion.mjs': 'a9a66df50fc201897f3f4ed8e9822e866358c1511d65c5f4e5cb0de95821da10', 'observe_maintenance_departure.js': '9bb0aa586c603a3a14693fd621ea4f81996d4f41c8735be5b20e99f14b283d03', 'recover_maintenance_departed_stock_zero.py': '19cbd4a2323addb825ba74ef8f0acb42d2fc2360c7947ddf57208f7e6c3fbb63', 'verify_maintenance_clock_neutral.py': '9efae1ecd4dce4a8619b43bfba8bde59a6aa00c52fc48fa464622e81cd6d1143'}}, '63a975bdc83749d9800b2d01656c9fdc865ebdd776a4f339a3182c61efa8b193')}
CORPUS='departed-stock-controls'

def verify(directory=None):
    global CORPUS
    root=Path(directory) if directory is not None else ROOT/'research/yt-maint/departed-stock-controls'
    CORPUS=root.name
    recipe,pin=RECIPES[CORPUS]
    assert SHA((root/'pins.json').read_bytes())==pin,'immutable native corpus manifest'
    pins=json.loads((root/'pins.json').read_text())['files']
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}
    assert actual==set(pins),'complete native inventory'
    for name,digest in pins.items():assert SHA((root/name).read_bytes())==digest,'immutable artifact '+name
    assert json.loads((root/'recipe.json').read_text())==recipe,'predeclared frozen recipe'
    assert {p.name for p in root.iterdir()}==set(recipe['cases'])|{'pins.json','recipe.json','sources'},'exact case inventory'
    assert {p.name for p in (root/'sources').iterdir()}==set(recipe['sources']),'exact frozen acquisition sources'
    for name,digest in recipe['sources'].items():assert SHA((root/'sources'/name).read_bytes())==digest,'executed source identity'
    observer=(root/'sources/observe_maintenance_departure.js').read_text()
    summary={}
    for profile in recipe['cases']:
        folder=root/profile/'child-1'
        assert {p.name for p in (root/profile).iterdir()}=={'child-1'} and {p.name for p in folder.iterdir()}==set(MODES),'complete six-mode matrix'
        rows={mode:verify_case(folder/mode,profile,mode,observer) for mode in MODES}
        paired=departure.paired_outputs(rows)
        assert paired['equal'],'six-mode complete output equality'
        summary[profile]=rows['unobserved-a']['stats']
    return summary

if __name__=='__main__':
    for name in RECIPES:
        result=verify(ROOT/'research/yt-maint'/name)
        print(name, {k:v['composition'] for k,v in result.items()})
