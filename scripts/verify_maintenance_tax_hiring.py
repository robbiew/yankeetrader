"""Independent supplemental full-world tax-funded hiring acquisition audit.

No acquisition writer or replay model is imported. No force-conservation policy is an input: native inventories and receipts are
audited first, retaining any actual overwrite, loss or absorption explicitly.
"""
import argparse
import collections
import verify_maintenance_clock_matrix as clocks
from verify_rng_clock import read_date,read_time
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
CASES={'one-group':dict(treasury=100,clock='00:00:02'),'ten-groups':dict(treasury=1000,clock='00:00:02')}

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
    assert all(field(bytes(world),r,89)==0 for r in range(3052,4052)),'zero inherited treasuries'
    at=(3053-1)*137+89;world[at:at+4]=encode(CASES[profile]['treasury'])
    before['YTDATA.DAT']=bytes(world);return before


def verify_fixture(before,profile,mode,edits):
    parent=parent_inputs(profile,mode);expected=fixture_inputs(profile,mode);at=(3053-1)*137+89
    assert before==expected,'one treasury edit and five exact side files'
    assert edits==[dict(record=3053,offset=89,before=parent['YTDATA.DAT'][at:at+4].hex(),after=expected['YTDATA.DAT'][at:at+4].hex())],'exact single-edit ledger'
    return dict(unchanged_links=5,transformed_links=1,edits=1)


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


def schedule(profile,stage):
    date,clock=PROFILES[profile][STAGES.index(stage)]
    return datetime.datetime.strptime(date,'%m/%d/%Y').date(),clock


def source_day(date):return (date-datetime.date(2026,1,1)).days+1


def verify_observation(observation,profile,stage,before,outputs):
    assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'},'exact raw observation schema'
    assert observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is True and type(observation['exit_code'])is int and observation['exit_code']==0,'actual observed source/exit identity'
    assert observation['errors']==[]and type(observation['dropped'])is int and observation['dropped']==0,'complete raw observation without loss'
    clocks.neutral.verify_module(observation['module'])
    date,_=schedule(profile,stage);ports=[];port_dates=[];planet_timers=[];planet_dates=[];segments=set();external=collections.Counter();roles=collections.Counter();texts={'news':[],'score':[]}
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
    return dict(helper1=roles[('timer','helper1')],helper2=roles[('timer','helper2')],active_planets=len(active),events=len(observation['events']),source_day=source_day(date),publication_clocks={role:texts[role][0]for role in('news','score')})


def verify_controller(controller,mode,observation=None,body=None,receipt=None):
    if mode=='unobserved':gateway.clocks.neutral.verify_controller(controller,mode);return None
    base=dict(controller);wait=base.pop('natural_exit_wait',None)
    assert type(wait)is dict and set(wait)=={'checks','elapsed_ms'},'recorded bounded post-detach natural-exit wait'
    assert type(wait['checks'])is int and 1<=wait['checks']<=100000,'actual finite positive liveness probe count'
    assert type(wait['elapsed_ms'])in(int,float)and math.isfinite(wait['elapsed_ms'])and 0<=wait['elapsed_ms']<=2000,'natural disappearance within the unchanged finite wait budget'
    return departure.verify_receipt_controller(base,mode,observation,body,receipt)


def verify_semantics(profile,stage,before,outputs,trace):
    old=before['YTDATA.DAT'];world=outputs['YTDATA.DAT']
    tax=sum(int(field(old,r,89)//10) for r in range(3053,4052))
    for r in range(3053,4052):
        assert rawfield(world,r,89)==(encode(field(old,r,89)-field(old,r,89)//10) if field(old,r,89) else rawfield(old,r,89)),'exact taxed port treasury'
    assert rawfield(world,3052,89)==rawfield(old,3052,89),'Earth excluded'
    assert trace.count(('  -  The goverment has collected %d credits tax from the ports.'%tax).encode())==1,'literal collected tax receipt'
    n=tax//10;groups=0 if n==0 else 1 if n<10 else 10;size=0 if n==0 else n if n<10 else n//10
    hired=groups*size
    receipts=re.findall(rb'The government has hired ([0-9]+) mercenaries to help Fight the Xannor!',trace)
    assert receipts==([str(hired).encode()] if hired else []),'literal hiring receipt binds independently computed debit'
    assert outputs['YTNAME.DAT']==before['YTNAME.DAT'] and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT'],'names and exact prior journal rotation'
    return dict(tax=tax,groups=groups,group_size=size,hired=hired,treasury=int(field(world,3053,89)),physical=departure.physical(world),qualification='bounded composed hiring; later physical actions retained')


def verify_case(folder,profile,mode,observer,stage,parent_outputs=None):
    folder=Path(folder);assert profile in CASES and mode in MODES,'declared exact fractional profile/mode'
    meta=json.loads((folder/'capture.json').read_text())
    keys={'recipe','profile','stage','mode','parent','parent_mode','parent_pins','parent_source','applied_fixture','fixture_edits','date','clock','cycles','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'}
    assert set(meta)==keys,'exact capture metadata schema'
    assert(meta['recipe'],meta['profile'],meta['stage'],meta['mode'],meta['parent'],meta['parent_mode'])==('maintenance-tax-hiring-controls-v1',profile,stage,mode,'fixture-parent' if stage=='child-1' else 'child-1',mode),'actual capture recipe and independently declared identity'
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
    stats=verify_semantics(profile,stage,before,outputs,trace)
    return dict(before=before,outputs=outputs,stats=stats,clocks=clocks,lineage=lineage,lifecycle=lifecycle)


DEFAULT=ROOT/'research/yt-maint/tax-hiring-controls'
PINS_SHA='11544ecf8865290d25da17a8f8eeb68ab8406d262baf944fd04eaa5aa0d550f4'
SOURCES={'recover_maintenance_tax_hiring.py','verify_maintenance_clock_neutral.py','capture_maintenance_stock_conversion.mjs','observe_maintenance_departure.js'}

def verify(directory=DEFAULT):
    root=Path(directory)
    assert SHA((root/'pins.json').read_bytes())==PINS_SHA,'immutable native corpus manifest'
    pins=json.loads((root/'pins.json').read_text())['files']
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}
    assert actual==set(pins),'complete native inventory'
    for name,digest in pins.items():assert SHA((root/name).read_bytes())==digest,'immutable artifact '+name
    recipe=json.loads((root/'recipe.json').read_text())
    expected=dict(recipe='maintenance-tax-hiring-controls-v1',cases=CASES,
        profiles={name:[list(row) for row in rows] for name,rows in PROFILES.items()},
        stages=list(STAGES),parent_source=PARENT_SOURCE,modes=MODES,
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
