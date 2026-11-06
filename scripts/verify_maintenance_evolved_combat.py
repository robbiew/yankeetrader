"""Independent evolved-combat provenance, inheritance and public outcome audit.

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
DEFAULT=ROOT/'research/yt-maint/evolved-combat-controls'
PINS_SHA='fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5'
PARENT=ROOT/'research/yt-maint/occupied-route-controls'
PARENT_PINS='7c01a0ef401f3df96f413e4aefd046c7f8a57499a1dfa537c83ea950d0dc7a3a'
SHA=lambda b:hashlib.sha256(b).hexdigest()
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
PROFILES={name:(('11/03/2026','00:00:00'),('11/04/2026','00:00:00'))for name in ('route-mercenary-37','route-mercenary-100000','route-neutral-37','route-planet-neutral')}
STAGES=('child-1','child-2')
SOURCES={'recover_maintenance_evolved_combat.py','verify_maintenance_clock_neutral.py','capture_maintenance_clock_neutral.mjs','observe_maintenance_placement.js'}
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
    assert profile in PROFILES and mode in MODES,'independently declared parent profile/mode'
    raw=(PARENT/'pins.json').read_bytes();assert SHA(raw)==PARENT_PINS,'immutable prior parent corpus manifest'
    pins=json.loads(raw)['files'];result={}
    for name in FILES:
        relative=profile+'/'+mode+'/after-'+name+'.gz';compressed=(PARENT/relative).read_bytes()
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
    for ident,minutes in planet_timers:
        assert rawfield(outputs['YTDATA.DAT'],4051+ident,89)==minutes,'saved active-planet time agrees with actual source TIMER'
        assert field(outputs['YTDATA.DAT'],4051+ident,41)==source_day(date),'saved active-planet day agrees with actual source date'
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
        assert force.denominator==1 and 0<=force<=110000,'bounded whole saved physical force'
        if force:assert owner in totals,'retained physical owner';totals[owner]+=int(force)
    return totals


def verify_semantics(profile,stage,before,outputs):
    date,_=schedule(profile,stage);world=outputs['YTDATA.DAT'];totals=physical(world);initial=physical(before['YTDATA.DAT'])
    assert sum(initial.values())<=110000 and sum(totals.values())<=110000,'bounded admitted combined physical forces'
    assert all(field(world,r,85)==field(before['YTDATA.DAT'],r,85)==0 for r in range(2,52)),'all human slots remain inactive'
    assert outputs['YTNAME.DAT']==before['YTNAME.DAT']and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT'],'exact names and public-journal rotation'
    assert outputs['YTRMSG.DAT']==before['YTRMSG.DAT']==b'','no invented private notices in inactive-player controls'
    assert field(world,1,81)==source_day(date),'actual base-year maintenance watermark'
    assert field(world,1,45)==26,'retained source base year'
    expected_slots={1,2,99,100}if profile=='route-planet-neutral'else{1,99,100}
    active=lambda w:{r-4051 for r in range(4052,4152)if field(w,r,85)>0}
    assert active(before['YTDATA.DAT'])==active(world)==expected_slots,'actual inherited homes and strong ordinary planet survive'
    planet_ground={}
    for slot in expected_slots:
        record=4051+slot;at=(record-1)*137
        assert world[at:at+41]==before['YTDATA.DAT'][at:at+41]and field(world,record,73)==field(before['YTDATA.DAT'],record,73),'surviving actual planet title and owner'
        assert sum(field(world,51+sector,93)==slot for sector in range(1,3001))==1,'surviving active planet has exactly one current physical link'
        ground=field(world,record,77);old_ground=field(before['YTDATA.DAT'],record,77)
        assert ground.denominator==old_ground.denominator==1 and 0<ground<=600000 and 0<=old_ground<=600000,'bounded observed positive surviving ground'
        planet_ground[slot]=dict(before=int(old_ground),after=int(ground))
    neutral=lambda w:{sector:int(field(w,51+sector,81))for sector in range(1,3001)if field(w,51+sector,81)>0 and field(w,51+sector,85)==0}
    assert neutral(world)==neutral(before['YTDATA.DAT']),'negative defense gate preserves actual neutral locations and force'
    news=outputs['YTNEWS.DAT'];lines=news.split(b'\r\n')
    # CR belongs to CRLF; use exact split lines for this original public literal.
    regeneration=[int(m[1])for line in lines if(m:=re.fullmatch(rb'Calculated Dynamic Xannor Regeneration is ([0-9]+) fighters\.',line))]
    assert len(regeneration)==1 and 0<=regeneration[0]<=10000,'one bounded actual public regeneration summary'
    xloss=mloss=0;attacks=collections.Counter();mine_events=[];foreign=[];mercenary_attacks=[];index=0
    while index<len(lines):
        line=lines[index]
        if not line.startswith(b' *** '):index+=1;continue
        planet=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "(The Wanderer|Mercenary Base|Route Haven)"',line)
        mine=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor hit sector mines in sector ([1-9][0-9]*)!',line)
        mercenary=re.fullmatch(rb' \*\*\* Mercenaries: lost ([1-9][0-9]*), dstrd ([1-9][0-9]*) \((Xannor|Plyr) ftrs dstrd\)',line)
        mercenary_attack=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Mercenaries attacking ([1-9][0-9]*) fighters beloning to The Xannor!',line)
        if planet:
            assert index+1<len(lines)and lines[index+1]==b' *** Xannor fighters destroyed!','exact fatal planetary public pair'
            xloss+=int(planet[1]);attacks[planet[2].decode()]+=1;index+=2
        elif mine:
            assert index+1<len(lines)and lines[index+1]==b' *** The Xannor were killed!','exact fatal mine public pair'
            amount,sector=map(int,mine.groups());assert 1<=sector<=3000,'bounded public mine sector'
            old=field(before['YTDATA.DAT'],51+sector,129);new=field(world,51+sector,129)
            assert old.denominator==new.denominator==1 and 0<=new<old,'claimed fatal mine event consumes saved original mines'
            xloss+=amount;mine_events.append(dict(sector=sector,force=amount,spent_mines=int(old-new)));index+=2
        elif mercenary:
            first,second,tag=int(mercenary[1]),int(mercenary[2]),mercenary[3].decode()
            foreign.append(dict(first=first,second=second,tag=tag));xloss+=first;mloss+=second;index+=1
        elif mercenary_attack:
            assert index+1<len(lines)and lines[index+1]==b' *** The Mercenaries Won!','exact surviving Mercenary attack/winner pair'
            assert lines.index(b'  -  Mercenary Report:')<index,'Mercenary offensive receipt belongs to its own report phase'
            attacker,target=map(int,mercenary_attack.groups())
            mercenary_attacks.append(dict(attacker=attacker,target=target));xloss+=target;index+=2
        else:raise AssertionError('unknown public battle outcome must not be guessed: '+repr(line))
    assert initial[-1]+regeneration[0]-totals[-1]==xloss,'literal reported Xannor casualties reconcile actual physical delta'
    public_summary_mercenary_losses=mloss
    if mercenary_attacks:
        assert len(mercenary_attacks)==1,'only measured single surviving Mercenary offense admitted'
        attack=mercenary_attacks[0]
        assert attack['attacker']==initial[-2]-mloss,'declared offensive starting force equals actual prior physical survivors'
        assert 0<totals[-2]<attack['attacker'],'actual surviving Mercenary offense spends force'
        positions=[sector for sector in range(1,3001)if field(world,51+sector,81)>0 and field(world,51+sector,85)==-2]
        assert len(positions)==1,'actual surviving offensive force has one physical location'
        attack.update(survivors=totals[-2],losses=attack['attacker']-totals[-2],sector=positions[0])
        mloss+=attack['losses']
    assert initial[-2]-totals[-2]==mloss,'literal foreign casualties reconcile actual Mercenary physical delta'
    assert initial[0]==totals[0],'negative neutral-defense gate preserves neutral physical force'
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1 and tuple(int(x.replace(b',',b''))for x in rows[0])==(100*totals[-1],100*totals[-2]),'actual NPC scoreboard columns agree with physical survivors'
    return dict(physical=totals,prior_physical=initial,source_day=source_day(date),regeneration=regeneration[0],public_xannor_losses=xloss,public_summary_mercenary_losses=public_summary_mercenary_losses,observed_mercenary_losses=mloss,planet_deaths=dict(attacks),fatal_mines=mine_events,foreign_summaries=foreign,mercenary_attacks=mercenary_attacks,observed_planet_ground=planet_ground)


def verify_survivor_trace(profile,stage,before,outputs,trace):
    """Bind observed descending Mercenary reactivation without replaying RNG."""
    battle=lambda raw:tuple(line for line in raw.split(b'\r\n')if line.startswith(b' *** '))
    assert battle(trace)==battle(outputs['YTNEWS.DAT']),'actual console/public combat literals agree in source order'
    rows=[dict(force=int(force),sector=int(sector))for force,sector in re.findall(rb'^  -  ([0-9]+) Mercenaries moving from sector ([0-9]+) *\r?$',trace,re.M)]
    world=outputs['YTDATA.DAT'];old=before['YTDATA.DAT']
    locations=lambda w:[(sector,int(field(w,51+sector,81)))for sector in range(1,3001)if field(w,51+sector,81)>0 and field(w,51+sector,85)==-2]
    initial,final=locations(old),locations(world)
    if profile=='route-mercenary-100000':
        assert len(initial)==len(final)==1 and len(rows)==2,'two measured descending-scan activations retain one physical Mercenary force'
        assert(rows[0]['sector'],rows[0]['force'])==initial[0],'first console activation binds actual inherited physical force'
        assert rows[-1]['force']==final[0][1] and rows[-1]['sector']<rows[0]['sector'] and final[0][0]>rows[-1]['sector'],'actual descending reactivation and later final write'
    else:assert rows==[]and initial==final==[],'non-Mercenary controls invent no console activations'
    stale=None
    if(profile,stage)==('route-mercenary-100000','child-2'):
        assert field(old,51+8,105)==673 and field(old,51+673,81)==182,'actual inherited victim group pointer and physical force'
        assert field(world,51+8,105)==109 and field(world,51+109,81)==0,'actual stale pointer survives same-day Mercenary victim removal'
        stale=dict(group=8,before=673,after=109,after_physical=0)
    return dict(activations=rows,final_location=final[0][0]if final else None,stale_victim_pointer=stale)


def verify_case(folder,profile,stage,mode,observer,parent_outputs=None):
    folder=Path(folder);date,clock=PROFILES[profile][STAGES.index(stage)]
    assert mode in MODES,'declared actual capture mode'
    meta=json.loads((folder/'capture.json').read_text());parent='occupied-parent'if stage=='child-1'else'child-1'
    assert set(meta)=={'recipe','profile','stage','mode','parent','parent_mode','parent_pins','date','clock','cycles','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'},'exact evolved clock metadata schema'
    assert(meta['recipe'],meta['profile'],meta['stage'],meta['mode'],meta['parent'],meta['parent_mode'],meta['parent_pins'])==('maintenance-evolved-combat-controls-v1',profile,stage,mode,parent,mode,PARENT_PINS),'actual independently declared profile/stage/parent identity'
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
    if stage=='child-1':parent_outputs=parent_inputs(profile,mode)
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
    stats['survivor_trace']=verify_survivor_trace(profile,stage,before,outputs,trace)
    return dict(before=before,outputs=outputs,stats=stats,clocks=clock_stats)


def paired_outputs(results):
    assert set(results)==set(MODES),'six independent complete modes required'
    reference=results['unobserved-a']['outputs'];assert set(reference)==set(FILES),'complete six-file reference output'
    differences={mode:[name for name in FILES if result['outputs'][name]!=reference[name]]for mode,result in results.items()}
    return dict(equal=not any(differences.values()),differences=differences)


def verify(directory=DEFAULT):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'immutable evolved-combat corpus manifest'
    pins=json.loads(raw);assert set(pins)=={'files'},'exact independent manifest schema'
    actual={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert actual==set(pins['files']),'complete pinned corpus inventory'
    for name,digest in pins['files'].items():assert SHA((root/name).read_bytes())==digest,'immutable raw corpus artifact '+name
    assert {p.name for p in root.iterdir()}==set(PROFILES)|{'pins.json','recipe.json','acquisition'},'exact four-profile corpus inventory'
    assert {p.name for p in(root/'acquisition').iterdir()}==SOURCES,'complete frozen acquisition sources'
    assert json.loads((root/'recipe.json').read_text())=={'recipe':'maintenance-evolved-combat-controls-v1','profiles':{name:[list(row)for row in rows]for name,rows in PROFILES.items()},'parent_pins':PARENT_PINS},'independently declared profile and parent recipe'
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
    print('Evolved-combat evidence verified:',verify(a.directory))
