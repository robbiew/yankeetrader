"""Before-only full six-file replay of the measured three-day maintenance chain.

The public chain API accepts one original before-world and explicit source clock
inputs. Each next day receives the previous *modeled* six files. No native child
before/after file, cache probe or observed RNG state is a synthesis input.
"""
import argparse
import collections
import copy
from dataclasses import dataclass
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from replay_maintenance_clock_matrix import legacy_day,_watermark_and_inactive_ranks
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_maintenance_evolved_ports import replay_ports
from replay_maintenance_evolved_npcs import synthesize as npc_synthesize
from replay_maintenance_evolved_aux import synthesize as aux_synthesize
from replay_maintenance_records import compare
import verify_maintenance_clock_matrix as clocks
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/convergence-chain-controls'
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES=('unobserved-a','unobserved-b','attach-only','observed-a','observed-b','observed-c')
SHA=lambda b:hashlib.sha256(b).hexdigest()
INITIAL_SHA='7e470653aabe81d1d3402d8810aca8e2c745e800d0295abcf575d5d7e2a309d3'


@dataclass(frozen=True)
class ClockInputs:
    startup_date:datetime.date
    final_date:datetime.date
    port_dates:tuple
    wanderer_date:datetime.date|None
    xannoron_date:datetime.date|None
    base_date:datetime.date|None
    news_date:datetime.date
    news_clock:str
    score_date:datetime.date
    score_clock:str
    port_timer_minutes:tuple
    h1_timers:tuple
    h2_timers:tuple
    xannoron_timer:bytes|None
    initial_state:int


@dataclass(frozen=True)
class Inputs:
    clock:ClockInputs
    schedule:tuple
    planet_clocks:tuple


def inputs_from_observation(observation):
    """Authenticate only original clock contexts, discarding captured RNG bytes."""
    raw=copy.deepcopy(observation)
    if type(raw)is not dict or raw.get('recipe')!='host-dos-placement-cache-observer-v1' or raw.get('observe')is not True:
        raise ValueError('complete original observed source clocks required')
    if type(raw.get('exit_code'))is not int or type(raw.get('dropped'))is not int or raw.get('exit_code')!=0 or raw.get('errors')!=[] or raw.get('dropped')!=0 or not 1<=len(raw.get('events',[]))<=16384:
        raise ValueError('complete natural zero-exit observation required')
    clocks.neutral.verify_module(raw['module'])
    timers=collections.defaultdict(list);calendar=collections.defaultdict(list)
    dates=collections.defaultdict(list);texts=collections.defaultdict(list);schedule=[];external=[];segments=set()
    for ordinal,event in enumerate(raw['events'],1):
        for side in('before','after'):event[side].pop('rng_raw')
        pair=clocks.event_pair(event,ordinal)
        if pair['before']['cycle_max']!=200000:raise ValueError('measured fixed CPU profile required')
        if pair['kind']=='unqualified':external.append(pair['function']);continue
        segments.add((pair['runtime_cs'],pair['main_cs'],pair['ds']))
        kind,role=pair['kind'],pair['role']
        if kind=='timer':
            timers[role].append(pair)
            if role in('helper1','helper2'):schedule.append(('h1'if role=='helper1'else'h2',pair['nested_return_ip'],pair['seconds']))
        elif kind=='date':
            dates[role].append(pair)
            if role=='calendar':calendar[clocks.CALENDAR_CALLERS[pair['nested_return_ip']]].append(pair)
        else:texts[role].append(pair)
    if len(segments)!=1 or external.count(0x2a)!=2 or external.count(0x2c)!=2:
        raise ValueError('stable source identity and exact shell clock inventory required')
    def one(rows,label):
        if len(rows)!=1:raise ValueError('unique source clock required: '+label)
        return rows[0]
    def index(row):
        n=clocks.mbf_fraction(bytes.fromhex(row['before']['port_raw']))
        if n.denominator!=1:return None
        return int(n)
    if [index(r)for r in timers['port']]!=list(range(1,1001))or[index(r)for r in calendar['port']]!=list(range(1,1001)):
        raise ValueError('complete source-qualified ordered port clocks required')
    if any(d['ordinal']>=t['ordinal']for d,t in zip(calendar['port'],timers['port'])):
        raise ValueError('port DATE must precede its own TIMER')
    for role in('wanderer','xannoron','base'):
        if len(calendar[role])>1:raise ValueError('optional creation calendar must be unique')
    if len(timers['xannoron'])>1:raise ValueError('optional creation TIMER must be unique')
    if len(calendar['planet'])!=len(timers['planet'])or len(timers['planet'])not in(1,4):
        raise ValueError('complete measured active-planet clocks required')
    slots=tuple(index(t)for t in timers['planet'])
    if slots not in((2,),(1,2,99,100))or tuple(index(d)for d in calendar['planet'])!=slots:
        raise ValueError('actual source planet indices must bind each date/TIMER pair')
    planets=[]
    for slot,d,t in zip(slots,calendar['planet'],timers['planet']):
        record=4051+slot
        if d['ordinal']>=t['ordinal']:raise ValueError('planet DATE must precede its own TIMER')
        day=(d['date']-datetime.date(2026,1,1)).days+1
        planets.append((record,day,t['minutes']))
    startup=bytearray(one(timers['startup'],'startup TIMER')['seconds']);startup[2]^=128
    seed=5|((startup[0]^startup[2])<<8)|((startup[1]^startup[3])<<16)
    phase=lambda role:calendar[role][0]['date']if calendar[role]else None
    clock=ClockInputs(startup_date=one(calendar['startup'],'startup DATE')['date'],final_date=one(calendar['final'],'final DATE')['date'],
      port_dates=tuple(r['date']for r in calendar['port']),wanderer_date=phase('wanderer'),xannoron_date=phase('xannoron'),base_date=phase('base'),
      news_date=one(dates['news'],'news DATE')['date'],news_clock=clocks.native_time_text(one(texts['news'],'news TIME')['after']['cx'],texts['news'][0]['after']['dx']),
      score_date=one(dates['score'],'score DATE')['date'],score_clock=clocks.native_time_text(one(texts['score'],'score TIME')['after']['cx'],texts['score'][0]['after']['dx']),
      port_timer_minutes=tuple(r['minutes']for r in timers['port']),h1_timers=tuple(r['seconds']for r in timers['helper1']),h2_timers=tuple(r['seconds']for r in timers['helper2']),
      xannoron_timer=timers['xannoron'][0]['seconds']if timers['xannoron']else None,initial_state=seed)
    return Inputs(clock,tuple(schedule),tuple(planets))


def _synthesize_day(before_files,inputs):
    if type(inputs)is not Inputs or type(inputs.clock)is not ClockInputs or type(inputs.schedule)is not tuple or type(inputs.planet_clocks)is not tuple:
        raise ValueError('frozen typed source inputs required')
    if type(before_files)is not dict or set(before_files)not in(set(FILES[:3]),set(FILES))or any(type(b)is not bytes for b in before_files.values()):
        raise ValueError('raw initial three or modeled six-file handoff required')
    before=before_files['YTDATA.DAT'];clock=inputs.clock
    if type(clock.initial_state)is not int or not 0<=clock.initial_state<2**24:raise ValueError('24bit startup state required')
    if clock.xannoron_timer is not None and(type(clock.xannoron_timer)is not bytes or len(clock.xannoron_timer)!=4):
        raise ValueError('typed optional raw Xannoron creation TIMER required')
    if any(type(v)is not tuple for v in(clock.port_dates,clock.port_timer_minutes,clock.h1_timers,clock.h2_timers)):
        raise ValueError('immutable source clock arrays required')
    if len(clock.port_dates)!=1000 or len(clock.port_timer_minutes)!=1000:raise ValueError('complete port clocks required')
    if any(type(r)is not tuple or len(r)!=3 or r[0]not in('h1','h2')or type(r[1])is not int or type(r[2])is not bytes or len(r[2])!=4 for r in inputs.schedule):
        raise ValueError('typed chronological helper TIMER schedule required')
    if tuple(r[2]for r in inputs.schedule if r[0]=='h1')!=clock.h1_timers or tuple(r[2]for r in inputs.schedule if r[0]=='h2')!=clock.h2_timers:
        raise ValueError('helper clocks must agree with chronological schedule')
    if any(type(r)is not tuple or len(r)!=3 or type(r[0])is not int or type(r[1])is not int or type(r[2])is not bytes or len(r[2])!=4 for r in inputs.planet_clocks):
        raise ValueError('typed ordered planet clock rows required')
    port_days=tuple(legacy_day(before,d)for d in clock.port_dates)
    phases={n:None if getattr(clock,n+'_date')is None else legacy_day(before,getattr(clock,n+'_date'))for n in('wanderer','xannoron','base')}
    day=legacy_day(before,clock.final_date)
    chronology=[legacy_day(before,clock.startup_date),*port_days,*(r[1]for r in inputs.planet_clocks),*(v for v in phases.values()if v is not None),day]
    if chronology!=sorted(chronology):raise ValueError('backward source calendar excluded')
    if any(d!=day for d in chronology)or clock.news_date!=clock.startup_date or clock.score_date!=clock.startup_date:
        raise ValueError('only measured same-date midnight source phases admitted')
    block,port_stats=replay_ports(before,port_days,clock.port_timer_minutes)
    work=before[:3051*137]+block+before[4051*137:]
    work,npcs=npc_synthesize(work,SimpleNamespace(clock=clock,schedule=inputs.schedule,phase_days=phases,final_day=day,planet_clocks=inputs.planet_clocks))
    work=_watermark_and_inactive_ranks(work,day)
    aux,aux_stats=aux_synthesize(before_files,work,clock.news_date,clock.news_clock,clock.score_date,clock.score_clock,created=npcs['created'])
    return {'YTDATA.DAT':work,**aux},dict(ports=port_stats,npcs=npcs,auxiliary=aux_stats,final_day=day)


def synthesize_chain(initial_before,inputs):
    """Return three complete predictions; modeled handoffs are the only children."""
    if type(initial_before)is not dict or set(initial_before)!=set(FILES[:3])or any(type(b)is not bytes for b in initial_before.values()):
        raise ValueError('exact three initial raw before files required')
    if SHA(initial_before['YTDATA.DAT'])!=INITIAL_SHA or SHA(initial_before['YTNAME.DAT'])!='af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f'or SHA(initial_before['YTNEWS.DAT'])!='1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a':
        raise ValueError('unmeasured initial chain input rejected')
    if type(inputs)is not tuple or len(inputs)!=3 or any(type(v)is not Inputs or type(v.clock)is not ClockInputs for v in inputs):
        raise ValueError('three frozen source-day inputs required')
    work=dict(initial_before);outputs=[];stats=[]
    for index,values in enumerate(inputs):
        if values.clock.startup_date!=datetime.date(2026,11,2)+datetime.timedelta(days=index):raise ValueError('only measured consecutive three-day chain admitted')
        work,row=_synthesize_day(work,values)
        if set(work)!=set(FILES):raise ValueError('complete modeled six-file handoff required')
        outputs.append(work);stats.append(row)
    return tuple(outputs),tuple(stats)


def initial_before(directory=DEFAULT):
    """Comparison-side initial input loader, never called from synthesis."""
    return {n:gzip.decompress((Path(directory)/'day-1/observed-a'/('before-'+n+'.gz')).read_bytes())for n in FILES[:3]}


def compare_cases(directory=DEFAULT):
    root=Path(directory);rows=[];statistics=[];cache_checks=[];before=initial_before(root)
    for observed in('observed-a','observed-b','observed-c'):
        raw=tuple(json.loads(gzip.decompress((root/f'day-{i}'/observed/'host-time.json.gz').read_bytes()))for i in(1,2,3))
        outputs,stats=synthesize_chain(before,tuple(inputs_from_observation(ob)for ob in raw))
        # Expected files are first opened only after the entire chain is computed.
        for index,(actual,modeled,ob)in enumerate(zip(outputs,stats,raw),1):
            count=validate_rng_witnesses(ob,modeled);day=f'day-{index}'
            if index>1:
                # Compare only after all modeled children exist. These payloads
                # never enter synthesis or replace a computed parent/cache.
                for parent_mode in MODES:
                    trace=(root/day/('cache-'+parent_mode)/'TRACE.BIN').read_bytes()
                    marker=b'Locating Top Player... (For Groups 16 - 20 to Pick on!)\r\n'
                    if trace.count(marker)!=1:raise ValueError('one source-qualified cache probe boundary required')
                    payload=trace[trace.index(marker)+len(marker):]
                    if len(payload)!=168:raise ValueError('complete declared cache probe required')
                    n=modeled['npcs']
                    for group in range(1,21):
                        for cell,value in((group,n['cache_locations'][group]),(group+21,n['cache_forces'][group])):
                            if payload[4*cell:4*cell+4]!=mbf.enc(value):raise ValueError('modeled prior world cache differs from independent probe')
                    cache_checks.append(dict(day=day,observation=observed,target='cache-'+parent_mode,fields=40))
            statistics.append(dict(day=day,observation=observed,rng_witness_checks=count,**modeled))
            for target in MODES:
                expected={n:gzip.decompress((root/day/target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                rows.append(dict(day=day,observation=observed,target=target,**compare(expected,actual)))
    if len(rows)!=54 or len(statistics)!=9:raise ValueError('complete three-source-chain comparison inventory required')
    return dict(recipe='bounded-evolved-chain-replay-v1',cases=rows,statistics=statistics,cache_checks=cache_checks)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_convergence import verify
    verify(a.root);report=compare_cases(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    failures=[r for r in report['cases']if r['byte_mismatches']]
    print(json.dumps(dict(comparisons=len(report['cases']),files=6*len(report['cases']),mismatches=len(failures))))
    if failures:raise SystemExit('at least one complete native comparison differs')

if __name__=='__main__':main()
