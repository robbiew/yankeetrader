"""Independent evolved clock/date provenance, inheritance and output audit.

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

import verify_maintenance_placement as placement
import verify_maintenance_clock_matrix as clocks
from verify_rng_clock import read_date,read_time

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/evolved-clock-controls'
PINS_SHA='c6fc45c0d1adf29bf2104574d1e341791f9f9fa15d2059c52a04ecd917beb826'
PARENT=ROOT/'research/yt-maint/convergence-chain-controls'
PARENT_PINS='164cc9d62bef6b213226ca8e125e39d282e6b851a9b6ffaf048e933a290d1f8c'
SHA=lambda b:hashlib.sha256(b).hexdigest()
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
PROFILES={
 'second-two':(('11/03/2026','00:00:02'),('11/04/2026','00:00:00')),
 'noon':(('11/03/2026','12:00:00'),('11/04/2026','00:00:00')),
 'catchup-eleven':(('11/13/2026','00:00:00'),('11/14/2026','00:00:00')),
 'new-year':(('01/01/2027','00:00:00'),('01/02/2027','00:00:00')),
}
STAGES=('child-1','child-2')
SOURCES={'recover_maintenance_evolved_clocks.py','verify_maintenance_clock_neutral.py','capture_maintenance_clock_neutral.mjs','observe_maintenance_placement.js'}
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


def parent_inputs(mode):
    assert mode in MODES,'declared parent mode'
    raw=(PARENT/'pins.json').read_bytes();assert SHA(raw)==PARENT_PINS,'immutable prior parent corpus manifest'
    pins=json.loads(raw)['files'];result={}
    for name in FILES:
        relative='day-1/'+mode+'/after-'+name+'.gz';compressed=(PARENT/relative).read_bytes()
        assert SHA(compressed)==pins[relative],'immutable per-mode original parent file'
        result[name]=gzip.decompress(compressed)
    return result


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
    for role in('news','score'):assert roles[('date',role)]==roles[('time',role)]==1,'unique source text clock pairs'
    header=(texts['news'][0]+' '+date.strftime('%m-%d-%Y')+': Maintenance Program Ran (Revision 03/14/94)\r\n').encode()
    assert outputs['YTNEWS.DAT'].startswith(header),'actual public header agrees with its own source clocks'
    header=('Last updated at: '+date.strftime('%m-%d-%Y')+' '+texts['score'][0]+'\r\n').encode()
    assert outputs['YTSCORE.ASC'].count(header)==1,'actual score header agrees with its own source clocks'
    return dict(helper1=roles[('timer','helper1')],helper2=roles[('timer','helper2')],active_planets=len(active),events=len(observation['events']),source_day=source_day(date))


def physical(world):
    assert len(world)==4151*137,'complete world extent'
    totals={-1:0,-2:0,0:0}
    for sector in range(1,3001):
        force=field(world,51+sector,81);owner=field(world,51+sector,85)
        assert force.denominator==1 and 0<=force<=10000,'bounded whole saved physical force'
        if force:assert owner in totals,'retained physical owner';totals[owner]+=int(force)
    return totals


def verify_semantics(profile,stage,before,outputs):
    date,_=schedule(profile,stage);world=outputs['YTDATA.DAT'];totals=physical(world);initial=physical(before['YTDATA.DAT'])
    assert sum(totals.values())<=sum(initial.values())<=10000,'no physical force invention in measured evolved controls'
    assert all(field(world,r,85)==field(before['YTDATA.DAT'],r,85)==0 for r in range(2,52)),'all human slots remain inactive'
    assert outputs['YTNAME.DAT']==before['YTNAME.DAT']and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT'],'exact names and public-journal rotation'
    assert outputs['YTRMSG.DAT']==before['YTRMSG.DAT']==b'','no invented private notices in inactive-player controls'
    assert field(world,1,81)==source_day(date),'actual base-year maintenance watermark'
    assert field(world,1,45)==26,'retained base year is unchanged across New Year'
    assert initial[-2]==initial[0]==totals[-2]==totals[0]==0,'no unexplained foreign or neutral physical force'
    lines=outputs['YTNEWS.DAT'].split(b'\r\n');loss=0;attacks=collections.Counter();mine_events=[];index=0
    while index<len(lines):
        line=lines[index]
        if not line.startswith(b' *** '):index+=1;continue
        planet=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "(The Wanderer|Mercenary Base)"',line)
        mine=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor hit sector mines in sector ([1-9][0-9]*)!',line)
        if planet:
            assert index+1<len(lines)and lines[index+1]==b' *** Xannor fighters destroyed!','exact fatal planetary public pair'
            amount=int(planet[1]);loss+=amount;attacks[planet[2].decode()]+=1
        elif mine:
            assert index+1<len(lines)and lines[index+1]==b' *** The Xannor were killed!','exact fatal mine public pair'
            amount,sector=map(int,mine.groups());assert 1<=sector<=3000,'bounded public mine sector'
            old=field(before['YTDATA.DAT'],51+sector,129);new=field(world,51+sector,129)
            assert old.denominator==new.denominator==1 and 0<=new<old,'claimed fatal mine event consumes a saved original mine'
            loss+=amount;mine_events.append(dict(sector=sector,force=amount,spent_mines=int(old-new)))
        else:raise AssertionError('unknown public battle outcome must not be guessed')
        index+=2
    assert initial[-1]-totals[-1]==loss,'exact public fatal casualties reconcile actual physical Xannor losses'
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1 and tuple(int(x.replace(b',',b''))for x in rows[0])==(100*totals[-1],100*totals[-2]),'actual NPC scoreboard columns agree with physical ownership'
    return dict(physical=totals,prior_physical=initial,source_day=source_day(date),public_xannor_losses=loss,planet_deaths=dict(attacks),fatal_mines=mine_events)


def verify_case(folder,profile,stage,mode,observer,parent_outputs=None):
    folder=Path(folder);date,clock=PROFILES[profile][STAGES.index(stage)]
    assert mode in MODES,'declared actual capture mode'
    meta=json.loads((folder/'capture.json').read_text());parent='convergence-day-1'if stage=='child-1'else'child-1'
    assert set(meta)=={'recipe','profile','stage','mode','parent','parent_mode','parent_pins','date','clock','cycles','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'},'exact evolved clock metadata schema'
    assert(meta['recipe'],meta['profile'],meta['stage'],meta['mode'],meta['parent'],meta['parent_mode'],meta['parent_pins'])==('maintenance-evolved-clock-controls-v1',profile,stage,mode,parent,mode,PARENT_PINS),'actual independently declared profile/stage/parent identity'
    assert(meta['date'],meta['clock'],meta['cycles'])==(date,clock,200000),'complete declared date/clock/CPU recipe'
    assert meta['host_sha256']==clocks.neutral.HOST_SHA and 0<meta['elapsed_seconds']<40,'pinned host and bounded capture'
    assert meta['guests']==clocks.GUESTS,'unchanged original full-run guests'
    for guest,digest in clocks.GUESTS.items():assert SHA((ROOT/'archive/dos-original'/guest).read_bytes())==digest,'immutable original guest identity'
    names=COMMON|{'before-'+n+'.gz'for n in FILES}|{'after-'+n+'.gz'for n in FILES}
    if MODES[mode]!='unobserved':names|={'host-time.json.gz','loaded-observer.js'}
    assert set(meta['files'])==names and{p.name for p in folder.iterdir()}==names|{'capture.json'},'complete exact raw capture inventory'
    for name in names:assert SHA((folder/name).read_bytes())==meta['files'][name],'declared raw file hash '+name
    before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in FILES};outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in FILES}
    assert meta['inputs']=={n:SHA(b)for n,b in before.items()}and meta['outputs']=={n:SHA(b)for n,b in outputs.items()},'complete decompressed input/output identities'
    if stage=='child-1':parent_outputs=parent_inputs(mode)
    assert parent_outputs is not None,'actual same-mode previous child outputs required'
    verify_inheritance(before,parent_outputs)
    mount=verify_launch(folder,meta,profile,stage,mode)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','natural DOS completion witnesses'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'],'actual lifecycle metadata'
    observation=None;obraw=None;clock_stats=None
    if MODES[mode]!='unobserved':
        obraw=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(obraw)
        config=dict(observe=MODES[mode]=='observed',output=str(mount/'host-time.json'))
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'actual loaded observer source/config'
        if config['observe']:clock_stats=verify_observation(observation,profile,stage,before,outputs)
        else:
            assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}and observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is False and observation['exit_code']==0 and observation['events']==observation['errors']==[]and observation['dropped']==0,'attach-only has no hooks/events/losses'
            clocks.neutral.verify_module(observation['module'])
    clocks.neutral.verify_controller(controller,MODES[mode],observation,obraw)
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n')and trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'),'complete unchanged original maintenance transcript'
    stats=verify_semantics(profile,stage,before,outputs)
    return dict(before=before,outputs=outputs,stats=stats,clocks=clock_stats)


def paired_outputs(results):
    assert set(results)==set(MODES),'six independent complete modes required'
    reference=results['unobserved-a']['outputs'];assert set(reference)==set(FILES),'complete six-file reference output'
    differences={mode:[name for name in FILES if result['outputs'][name]!=reference[name]]for mode,result in results.items()}
    return dict(equal=not any(differences.values()),differences=differences)


def verify(directory=DEFAULT):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'immutable evolved-clock corpus manifest'
    pins=json.loads(raw);assert set(pins)=={'files'},'exact independent manifest schema'
    actual={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert actual==set(pins['files']),'complete pinned corpus inventory'
    for name,digest in pins['files'].items():assert SHA((root/name).read_bytes())==digest,'immutable raw corpus artifact '+name
    assert {p.name for p in root.iterdir()}==set(PROFILES)|{'pins.json','recipe.json','acquisition'},'exact four-profile corpus inventory'
    assert {p.name for p in(root/'acquisition').iterdir()}==SOURCES,'complete frozen acquisition sources'
    assert json.loads((root/'recipe.json').read_text())=={'recipe':'maintenance-evolved-clock-controls-v1','profiles':{name:[list(row)for row in rows]for name,rows in PROFILES.items()},'parent_pins':PARENT_PINS},'independently declared profile and parent recipe'
    observer=(root/'acquisition/observe_maintenance_placement.js').read_text();summary={}
    for profile in PROFILES:
        assert {p.name for p in(root/profile).iterdir()}==set(STAGES),'both declared child stages'
        previous=None;stages={}
        for stage in STAGES:
            assert {p.name for p in(root/profile/stage).iterdir()}==set(MODES),'six independent modes per child'
            results={mode:verify_case(root/profile/stage/mode,profile,stage,mode,observer,None if previous is None else previous[mode]['outputs'])for mode in MODES}
            stages[stage]=dict(**results['unobserved-a']['stats'],paired=paired_outputs(results),observed_clocks=results['observed-a']['clocks']);previous=results
        summary[profile]=stages
    return dict(profiles=4,full_runs=48,output_files=288,inherited_file_links=288,stages=summary)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT);a=p.parse_args()
    print('Evolved-clock evidence verified:',verify(a.directory))
