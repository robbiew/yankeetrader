"""Independent provenance, exact-chain and cache-normalization evidence audit.

No capture writer or replay model is imported. Patched early-cache observations
are checked separately from unchanged complete maintenance runs.
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
DEFAULT=ROOT/'research/yt-maint/convergence-chain-controls'
PINS_SHA='164cc9d62bef6b213226ca8e125e39d282e6b851a9b6ffaf048e933a290d1f8c'
SHA=lambda b:hashlib.sha256(b).hexdigest()
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES={'unobserved-a':'unobserved','observed-a':'observed','attach-only':'attach-only','observed-b':'observed','unobserved-b':'unobserved','observed-c':'observed'}
DAYS={'day-1':('11/02/2026',None),'day-2':('11/03/2026','day-1'),'day-3':('11/04/2026','day-2')}
SOURCES={'recover_maintenance_convergence.py','recover_maintenance_sequence.py','replay_qb_graph.py','verify_maintenance_clock_neutral.py','capture_maintenance_clock_neutral.mjs','observe_maintenance_placement.js'}
COMMON=placement.COMMON
field=placement.field
rawfield=placement.rawfield
encode=placement.encode


def initial_inputs():
    result=clocks.neutral.before_input_bytes();world=bytearray(result['YTDATA.DAT']);record=4053;at=(record-1)*137
    world[at:at+137]=b'Convergence Haven'.ljust(41,b' ')+bytes(96)
    for offset,value in [(41,305),(45,1000),(49,1000),(53,1000),(73,-1),(77,500000),(85,17)]:
        pos=at+offset;world[pos:pos+4]=encode(value)
    pos=(2853-1)*137+93;world[pos:pos+4]=encode(2)
    result['YTDATA.DAT']=bytes(world);return result


def commands(date):
    return ['date '+date,'time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']


def verify_launch(folder,meta,day,mode):
    date,_=DAYS[day];actual_date=datetime.datetime.strptime(date,'%m/%d/%Y').date()
    argv=json.loads((folder/'launch.json').read_text())
    assert argv==meta['argv']and argv[0]=='/opt/homebrew/bin/dosbox-staging','actual pinned host launch'
    assert len(argv)>8 and argv[8].startswith('mount c /private/tmp/'),'fresh disposable mount'
    mount=Path(argv[8][8:]);assert mount.parts[-2:]==(day,mode),'actual declared stage/mode mount'
    expected=[argv[0],'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']
    expected += [v for c in [argv[8],'c:']+commands(date)+['exit']for v in('-c',c)]
    assert argv==expected and(folder/'COMMANDS.TXT').read_text()=='\n'.join(commands(date))+'\n','complete independently declared commands'
    messages=[line.split(' | ',1)[1]for line in(folder/'dosbox.stderr').read_text().splitlines()if' | 'in line]
    args=[shlex.split(m[11:])for m in messages if m.startswith('arguments: ')]
    assert args==[argv],'actual process launch agrees with declaration'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1,'actual pinned host version'
    assert len([m for m in messages if m.startswith('CPU: Setting fixed 200000 cycles.')])==1,'actual fixed CPU profile'
    assert 'SDL: dummy video initialised'in messages and "MIXER: Sound output disabled ('nosound' mode)"in messages,'actual dummy video/audio'
    assert(folder/'dosbox.stdout').read_bytes()==b'','complete empty host stdout'
    assert read_date((folder/'DOSDATE.LOG').read_bytes())==actual_date and read_time((folder/'DOSTIME.LOG').read_bytes())==0,'actual initial DOS calendar/midnight'
    elapsed=(read_date((folder/'ENDDATE.LOG').read_bytes())-actual_date).days*86400+read_time((folder/'ENDTIME.LOG').read_bytes())
    assert 0<elapsed<40,'bounded advancing actual DOS clock'
    return mount


def verify_observation(observation,day,before,outputs):
    assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'},'exact raw observation schema'
    assert observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is True and observation['exit_code']==0,'actual declared observer mode/exit'
    assert observation['errors']==[]and observation['dropped']==0,'complete raw observation without losses'
    clocks.neutral.verify_module(observation['module'])
    actual_date=datetime.datetime.strptime(DAYS[day][0],'%m/%d/%Y').date();ports=[];roles=collections.Counter();segments=set();external=collections.Counter();texts={'news':[],'score':[]}
    assert observation['events'],'complete original source observations required'
    for ordinal,event in enumerate(observation['events'],1):
        row=copy.deepcopy(event);states=[]
        for side in('before','after'):
            raw=row[side].pop('rng_raw')
            assert type(raw)is str and re.fullmatch('[0-9a-f]{8}',raw),'four complete raw RNG witness bytes'
            state=int.from_bytes(bytes.fromhex(raw),'little');assert state<2**24,'bounded actual RNG state';states.append(state)
        assert states[0]==states[1],'clock callback preserves raw RNG state'
        pair=clocks.event_pair(row,ordinal);roles[(pair['kind'],pair.get('role'))]+=1
        if pair['kind']=='unqualified':
            external[pair['function']]+=1;continue
        assert pair['before']['cycle_max']==200000,'fixed observed CPU budget'
        segments.add((pair['runtime_cs'],pair['main_cs'],pair['ds']))
        if pair['kind']=='date':assert pair['date']==actual_date,'source-qualified actual stage calendar'
        if pair['kind']=='time'and pair['role']in texts:
            texts[pair['role']].append(clocks.native_time_text(pair['after']['cx'],pair['after']['dx']))
        if pair['kind']=='timer'and pair['role']=='port':
            ident=clocks.neutral.mbf_fraction(bytes.fromhex(pair['before']['port_raw']))
            assert ident.denominator==1,'whole original port index'
            ports.append((int(ident),pair['minutes']))
    assert len(segments)==1,'stable original load identities throughout observation'
    assert roles[('unqualified',None)]==4 and external=={0x2a:2,0x2c:2},'exact two external shell date and two time reads'
    assert roles[('timer','startup')]==1,'one source startup TIMER'
    for role in('news','score'):
        assert roles[('date',role)]==roles[('time',role)]==1,'unique source text clock pair'
    expected_helpers={'day-1':(42,19),'day-2':(41,17),'day-3':(42,0)}[day]
    assert(roles[('timer','helper1')],roles[('timer','helper2')])==expected_helpers,'complete retained source-helper inventory'
    assert roles[('timer','xannoron')]==(1 if day=='day-1'else 0),'only initial missing-Xannoron creation samples TIMER'
    news_prefix=(texts['news'][0]+' '+actual_date.strftime('%m-%d-%Y')+': Maintenance Program Ran (Revision 03/14/94)\r\n').encode('ascii')
    assert outputs['YTNEWS.DAT'].startswith(news_prefix),'actual news header agrees with its own source text clocks'
    score_header=('Last updated at: '+actual_date.strftime('%m-%d-%Y')+' '+texts['score'][0]+'\r\n').encode('ascii')
    assert outputs['YTSCORE.ASC'].count(score_header)==1,'actual score header agrees with its own source text clocks'
    active=sum(field(before['YTDATA.DAT'],r,85)>0 for r in range(4052,4152))
    assert roles[('timer','planet')]==active,'one source TIMER for each actual active before-planet'
    assert [p for p,_ in ports]==list(range(1,1001)),'all original per-port TIMER inputs in order'
    for ident,minutes in ports:
        assert rawfield(outputs['YTDATA.DAT'],3051+ident,101)==minutes,'saved raw port time equals actual source TIMER conversion'
    return dict(helper1=roles[('timer','helper1')],helper2=roles[('timer','helper2')],active_planets=active,events=len(observation['events']))


def verify_inheritance(before,parent):
    assert set(before)==set(parent)==set(FILES),'all six parent/child file identities retained'
    assert before==parent,'all six child before-files equal exact parent outputs without patches'


def physical(world):
    assert len(world)==4151*137,'complete world extent'
    total=0
    for sector in range(1,3001):
        force=field(world,51+sector,81);owner=field(world,51+sector,85)
        assert force.denominator==1 and 0<=force<=10000,'bounded whole physical sector force'
        assert not force or owner==-1,'only retained physical Xannor force'
        total+=int(force)
    return total


def verify_semantics(day,before,outputs):
    world=outputs['YTDATA.DAT'];assert physical(world)==physical(before['YTDATA.DAT'])==10000,'unique physical force conserved across complete run'
    assert outputs['YTNAME.DAT']==before['YTNAME.DAT']and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT'],'actual name retention and public-news rotation'
    assert outputs['YTRMSG.DAT']==b'','no invented private mail in inactive-player chain'
    pointers=collections.defaultdict(list)
    for group in range(1,21):
        sector=field(world,51+group,105)
        assert sector.denominator==1 and 1<=sector<=3000,'twenty bounded surviving group pointers'
        pointers[int(sector)].append(group)
    if day=='day-1':
        assert dict(pointers)=={849:[1],2802:list(range(2,20)),1169:[20]},'actual eighteen-group final-pointer convergence'
        assert field(world,2853,81)==6552 and field(world,2853,85)==-1,'one combined physical force at converged endpoint'
    else:assert len(pointers)==20,'evolved chain restores twenty distinct final pointers'
    assert field(world,1,81)==305+int(day[-1]),'actual completed maintenance watermark'
    assert field(world,2853,93)==2 and world[(4053-1)*137:(4053-1)*137+41]==b'Convergence Haven'.ljust(41,b' ')and field(world,4053,85)==17,'named linked convergence planet survives'
    assert b'Xannor fighters destroyed!'not in outputs['YTNEWS.DAT']and b'ftrs dstrd'not in outputs['YTNEWS.DAT'],'no invented public combat losses'
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1 and tuple(int(x.replace(b',',b''))for x in rows[0])==(1000000,0),'actual NPC scores follow physical force'
    return dict(physical_force=10000,unique_positive_pointers=len(pointers),max_pointer_multiplicity=max(map(len,pointers.values())))


def verify_case(folder,day,mode,observer,parent_outputs=None):
    folder=Path(folder);date,parent=DAYS[day];probe=mode.startswith('cache-');base_mode=mode[6:]if probe else mode
    assert base_mode in MODES and(not probe or parent is not None),'declared stage/mode/probe inventory'
    meta=json.loads((folder/'capture.json').read_text())
    assert set(meta)=={'recipe','day','mode','parent','parent_mode','probe','date','clock','cycles','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'},'exact chain metadata schema'
    assert(meta['recipe'],meta['day'],meta['mode'],meta['parent'],meta['parent_mode'],meta['probe'])==('maintenance-convergence-chain-v1',day,mode,parent,base_mode if parent else None,probe),'actual independently declared chain identity'
    assert(meta['date'],meta['clock'],meta['cycles'])==(date,'00:00:00',200000),'unchanged stage date/clock/CPU recipe'
    assert meta['host_sha256']==clocks.neutral.HOST_SHA and 0<meta['elapsed_seconds']<40,'pinned host and bounded capture'
    input_names=FILES[:3]if parent is None else FILES
    before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in input_names}
    assert meta['inputs']=={n:SHA(b)for n,b in before.items()},'complete saved before-input identities'
    if parent is None:assert before==initial_inputs(),'independently reconstructed complete initial fixture'
    else:verify_inheritance(before,parent_outputs)
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();assert SHA(original)==clocks.GUESTS['YTMAINT.EXE'],'immutable original maintenance'
    guests=dict(clocks.GUESTS)
    if probe:guests['YTMAINT.EXE']=SHA(placement.patched_original(original))
    assert meta['guests']==guests,'unchanged original full-run guests or exact declared cache probe'
    names=COMMON|{'before-'+n+'.gz'for n in input_names}|{'after-'+n+'.gz'for n in FILES}
    actual='unobserved'if probe else MODES[base_mode]
    if actual!='unobserved':names|={'host-time.json.gz','loaded-observer.js'}
    assert set(meta['files'])==names and {p.name for p in folder.iterdir()}==names|{'capture.json'},'complete exact raw artifact inventory'
    for name in names:assert SHA((folder/name).read_bytes())==meta['files'][name],'declared raw capture hash '+name
    mount=verify_launch(folder,meta,day,mode)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','natural original DOS return witnesses'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'],'actual lifecycle metadata'
    outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in FILES}
    assert meta['outputs']=={n:SHA(b)for n,b in outputs.items()},'complete raw output identities'
    observation=None;obraw=None;clock_stats=None
    if actual!='unobserved':
        obraw=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(obraw)
        config=dict(observe=actual=='observed',output=str(mount/'host-time.json'))
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'exact actual loaded source/config'
        if actual=='observed':clock_stats=verify_observation(observation,day,before,outputs)
        else:
            assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}and observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is False and observation['exit_code']==0 and observation['events']==observation['errors']==[]and observation['dropped']==0,'attach-only has no hooks, events or losses'
            clocks.neutral.verify_module(observation['module'])
    clocks.neutral.verify_controller(controller,actual,observation,obraw)
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n'),'original maintenance transcript header'
    if probe:
        stats=placement.verify_cache(before['YTDATA.DAT'],outputs['YTDATA.DAT'],trace)
        assert stats['cache_force']==physical(before['YTDATA.DAT'])==10000,'cache consumes physical force once without multiplying duplicate pointers'
        assert outputs['YTSCORE.ASC']==before['YTSCORE.ASC'],'early probe retains inherited old scoreboard, not a completed writer'
        assert outputs['YTNAME.DAT']==before['YTNAME.DAT']and outputs['YTYNEWS.DAT']==before['YTNEWS.DAT']and outputs['YTRMSG.DAT']==b'','early probe side-file phase boundaries'
        assert stats['consumed']==(3 if day=='day-2'else 20),'actual source cache sector inventory'
    else:
        assert trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'),'complete unchanged maintenance footer'
        stats=verify_semantics(day,before,outputs)
    return dict(before=before,outputs=outputs,stats=stats,clocks=clock_stats)


def verify_paired_outputs(results):
    assert set(results)==set(MODES),'six independent complete modes required'
    reference=results['unobserved-a']['outputs']
    assert set(reference)==set(FILES),'complete six-file reference output'
    assert all(r['outputs']==reference for r in results.values()),'all six complete outputs equal both unobserved controls'


def verify(directory=DEFAULT):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'immutable convergence-chain manifest'
    pins=json.loads(raw);assert set(pins)=={'files'},'exact independent manifest schema'
    actual={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert actual==set(pins['files']),'complete pinned artifact inventory'
    for name,digest in pins['files'].items():assert SHA((root/name).read_bytes())==digest,'immutable artifact '+name
    assert {p.name for p in root.iterdir()}==set(DAYS)|{'recipe.json','pins.json','acquisition'},'exact three-stage corpus inventory'
    assert {p.name for p in(root/'acquisition').iterdir()}==SOURCES,'complete frozen acquisition source inventory'
    recipe=json.loads((root/'recipe.json').read_text())
    assert recipe=={'recipe':'maintenance-convergence-chain-v1','days':{day:list(v)for day,v in DAYS.items()},'initial':{'planet':[2802,2,'Convergence Haven',-1,500000],'timestamp':305,'rates':[1000,1000,1000]}},'independent stage/date/parent recipe'
    observer=(root/'acquisition/observe_maintenance_placement.js').read_text();all_results={};summary={}
    for day,(_,parent)in DAYS.items():
        expected=set(MODES)|({'cache-'+mode for mode in MODES}if parent else set())
        assert {p.name for p in(root/day).iterdir()}==expected,'exact stage modes and separately labelled probes'
        full={mode:verify_case(root/day/mode,day,mode,observer,None if parent is None else all_results[parent][mode]['outputs'])for mode in MODES}
        verify_paired_outputs(full);all_results[day]=full
        probes={}
        if parent:
            probes={mode:verify_case(root/day/('cache-'+mode),day,'cache-'+mode,observer,all_results[parent][mode]['outputs'])for mode in MODES}
        summary[day]=dict(**full['unobserved-a']['stats'],cache_probes=len(probes),cache_consumed=None if not probes else probes['unobserved-a']['stats']['consumed'],observed_clocks=full['observed-a']['clocks'])
    return dict(days=3,full_runs=18,cache_probes=12,full_output_files=108,stages=summary)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT);a=p.parse_args()
    print('Convergence-chain evidence verified:',verify(a.directory))
