"""Before-only three-stage replay of the measured evolved combat chains.

Only the original occupied three-file world and source-qualified clock inputs
enter synthesis. Both complete children inherit the preceding modeled six files.
"""
import argparse
import collections
import copy
from dataclasses import fields
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import replay_maintenance_occupied_records as old
import replay_maintenance_clock_matrix as matrix
from replay_maintenance_evolved_records import ClockInputs,Inputs,FILES,MODES,legacy_day,_watermark_and_inactive_ranks
from replay_maintenance_evolved_clock_ports import replay_ports
from replay_maintenance_evolved_combat_npcs import synthesize as npc_synthesize
from replay_maintenance_evolved_combat_aux import synthesize as aux_synthesize
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_maintenance_records import compare
import verify_maintenance_clock_matrix as clocks
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/evolved-combat-controls'
PARENT=old.DEFAULT
CASES=('route-mercenary-37','route-mercenary-100000','route-neutral-37','route-planet-neutral')
SHA=lambda b:hashlib.sha256(b).hexdigest()

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
    if len(calendar['planet'])!=len(timers['planet'])or len(timers['planet'])not in(0,1,3,4):
        raise ValueError('complete measured active-planet clocks required')
    slots=tuple(index(t)for t in timers['planet'])
    if slots not in((),(2,),(1,99,100),(1,2,99,100))or tuple(index(d)for d in calendar['planet'])!=slots:
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
        raise ValueError('only measured same-date source phases admitted')
    block,port_stats=replay_ports(before,port_days,clock.port_timer_minutes)
    work=before[:3051*137]+block+before[4051*137:]
    work,npcs=npc_synthesize(work,SimpleNamespace(clock=clock,schedule=inputs.schedule,phase_days=phases,final_day=day,planet_clocks=inputs.planet_clocks))
    work=_watermark_and_inactive_ranks(work,day)
    aux,aux_stats=aux_synthesize(before_files,work,clock.news_date,clock.news_clock,clock.score_date,clock.score_clock,created=npcs['created'],events=npcs['events'],mercenary=npcs['mercenary'])
    return {'YTDATA.DAT':work,**aux},dict(ports=port_stats,npcs=npcs,auxiliary=aux_stats,final_day=day)


def synthesize_chain(initial_before,inputs):
    """Predict the occupied parent plus both children before target comparison."""
    if type(initial_before)is not dict or set(initial_before)!=set(FILES[:3])or any(type(b)is not bytes for b in initial_before.values()):
        raise ValueError('three original occupied before files required')
    if old.ADMITTED_INPUTS.get(SHA(initial_before['YTDATA.DAT']))not in CASES:
        raise ValueError('only four measured occupied initial worlds admitted')
    if SHA(initial_before['YTNAME.DAT'])!='af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f'or SHA(initial_before['YTNEWS.DAT'])!='1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a':
        raise ValueError('unmeasured initial side files rejected')
    if type(inputs)is not tuple or len(inputs)!=3 or any(type(i)is not Inputs or type(i.clock)is not ClockInputs for i in inputs):
        raise ValueError('three immutable source-day inputs required')
    if tuple(i.clock.startup_date for i in inputs)!=tuple(datetime.date(2026,11,d)for d in(2,3,4)):
        raise ValueError('only measured occupied November2/3/4 chronology admitted')
    if any((i.clock.news_clock,i.clock.score_clock)!=('00:00:00','00:00:00')for i in inputs[1:]):
        raise ValueError('only measured midnight child publication clocks admitted')
    first=inputs[0]
    parent_clock=matrix.Inputs(**{f.name:getattr(first.clock,f.name)for f in fields(matrix.Inputs)})
    work,row=old.synthesize(initial_before,old.Inputs(parent_clock,first.schedule,first.planet_clocks))
    outputs=[work];stats=[row]
    for i in inputs[1:]:
        work,row=_synthesize_day(work,i)
        if set(work)!=set(FILES):raise ValueError('complete modeled six-file handoff required')
        outputs.append(work);stats.append(row)
    return tuple(outputs),tuple(stats)


def initial_before(case,directory=PARENT):
    """Comparison-only original fixture loader; synthesis does not call it."""
    if case not in CASES:raise ValueError('unknown original occupied case')
    return old.before_inputs(case,directory)


def compare_cases(directory=DEFAULT):
    root=Path(directory);cases=[];statistics=[]
    for case in CASES:
        before=initial_before(case)
        for observed in('observed-a','observed-b','observed-c'):
            paths=(PARENT/case/observed/'host-time.json.gz',)+tuple(root/case/f'child-{i}'/observed/'host-time.json.gz'for i in(1,2))
            observations=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in paths)
            outputs,stats=synthesize_chain(before,tuple(inputs_from_observation(ob)for ob in observations))
            validate_rng_witnesses(observations[0],stats[0])
            for stage in(1,2):
                count=validate_rng_witnesses(observations[stage],stats[stage])
                statistics.append(dict(case=case,child=stage,observation=observed,rng_witness_checks=count,**stats[stage]))
                for target in MODES:
                    expected={n:gzip.decompress((root/case/f'child-{stage}'/target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                    cases.append(dict(case=case,child=stage,observation=observed,target=target,**compare(expected,outputs[stage])))
    if len(cases)!=144 or len(statistics)!=24:raise ValueError('complete four-chain three-source comparison inventory required')
    return dict(recipe='bounded-evolved-combat-replay-v1',cases=cases,statistics=statistics)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_evolved_combat import verify
    verify(a.root);r=compare_cases(a.root)
    if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n')
    failures=[c for c in r['cases']if c['byte_mismatches']]
    print(json.dumps(dict(comparisons=len(r['cases']),files=6*len(r['cases']),mismatches=len(failures))))
    if failures:raise SystemExit('at least one complete native comparison differs')

if __name__=='__main__':main()
