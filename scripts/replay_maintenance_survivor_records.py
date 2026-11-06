"""Before-only five-day replay of the measured longer survivor chains.

One original three-file world and five source-clock inputs suffice. The modeled
November4 prefix supplies both new complete children without native handoff saves.
"""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import replay_maintenance_evolved_combat_records as combat
import replay_maintenance_evolved_clock_records as clock_prefix
from replay_maintenance_evolved_records import ClockInputs,Inputs,FILES,MODES,legacy_day,_watermark_and_inactive_ranks
from replay_maintenance_evolved_combat_records import inputs_from_observation
from replay_maintenance_survivor_ports import replay_ports
from replay_maintenance_survivor_npcs import synthesize as npc_synthesize
from replay_maintenance_survivor_aux import synthesize as aux_synthesize
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_maintenance_records import compare

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/survivor-chain-controls'
PROFILES=('mercenary-survivor','planet-survivor','neutral-survivor','mine-survivor')
COMBAT_CASES={'mercenary-survivor':'route-mercenary-100000','planet-survivor':'route-planet-neutral','neutral-survivor':'route-neutral-37'}
SHA=lambda b:hashlib.sha256(b).hexdigest()

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


def profile_for(initial_before):
    if type(initial_before)is not dict or set(initial_before)!=set(FILES[:3])or any(type(b)is not bytes for b in initial_before.values()):
        raise ValueError('three original immutable before files required')
    digest=SHA(initial_before['YTDATA.DAT'])
    if digest==clock_prefix.old.INITIAL_SHA:profile='mine-survivor'
    else:
        case=combat.old.ADMITTED_INPUTS.get(digest)
        inverse={v:k for k,v in COMBAT_CASES.items()}
        if case not in inverse:raise ValueError('only four measured original survivor worlds admitted')
        profile=inverse[case]
    if SHA(initial_before['YTNAME.DAT'])!='af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f'or SHA(initial_before['YTNEWS.DAT'])!='1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a':
        raise ValueError('unmeasured original side files rejected')
    return profile


def synthesize_chain(initial_before,inputs):
    """Predict all five complete days before any expected file can be opened."""
    profile=profile_for(initial_before)
    if type(inputs)is not tuple or len(inputs)!=5 or any(type(i)is not Inputs or type(i.clock)is not ClockInputs for i in inputs):
        raise ValueError('five immutable source-day inputs required')
    if tuple(i.clock.startup_date for i in inputs)!=tuple(datetime.date(2026,11,d)for d in range(2,7)):
        raise ValueError('only measured November2-through6 five-day chronology admitted')
    for index,i in enumerate(inputs[3:],3):
        expected_score='00:00:01'if profile=='neutral-survivor'and index==3 else'00:00:00'
        if(i.clock.news_clock,i.clock.score_clock)!=('00:00:00',expected_score):
            raise ValueError('explicit measured survivor publication clocks required')
    if profile=='mine-survivor':
        if(inputs[1].clock.news_clock,inputs[1].clock.score_clock)!=('00:00:02','00:00:02'):
            raise ValueError('measured second-two prefix required for mine survivor')
        prefix,stats=clock_prefix.synthesize_chain(initial_before,inputs[:3])
    else:prefix,stats=combat.synthesize_chain(initial_before,inputs[:3])
    outputs=list(prefix);rows=list(stats);work=outputs[-1]
    for values in inputs[3:]:
        work,row=_synthesize_day(work,values)
        if set(work)!=set(FILES):raise ValueError('complete modeled six-file child required')
        outputs.append(work);rows.append(row)
    return tuple(outputs),tuple(rows)


def initial_before(profile):
    """Comparison-only initial loader; core synthesis never calls it."""
    if profile not in PROFILES:raise ValueError('unknown retained survivor profile')
    return clock_prefix.old.initial_before()if profile=='mine-survivor'else combat.initial_before(COMBAT_CASES[profile])


def observation_paths(profile,observed,root=DEFAULT):
    """Comparison-only clock provenance paths, not synthesis inputs or targets."""
    if profile not in PROFILES or observed not in('observed-a','observed-b','observed-c'):raise ValueError('retained profile and observed mode required')
    if profile=='mine-survivor':
        prefix=(clock_prefix.old.DEFAULT/'day-1'/observed/'host-time.json.gz',)+tuple(clock_prefix.DEFAULT/'second-two'/f'child-{i}'/observed/'host-time.json.gz'for i in(1,2))
    else:
        case=COMBAT_CASES[profile]
        prefix=(combat.PARENT/case/observed/'host-time.json.gz',)+tuple(combat.DEFAULT/case/f'child-{i}'/observed/'host-time.json.gz'for i in(1,2))
    return prefix+tuple(Path(root)/profile/f'child-{i}'/observed/'host-time.json.gz'for i in(1,2))


def compare_cases(directory=DEFAULT):
    root=Path(directory);cases=[];statistics=[]
    for profile in PROFILES:
        before=initial_before(profile)
        for observed in('observed-a','observed-b','observed-c'):
            observations=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in observation_paths(profile,observed,root))
            outputs,stats=synthesize_chain(before,tuple(inputs_from_observation(o)for o in observations))
            # Every modeled day exists before target/child files are first opened.
            for ob,row in zip(observations[:3],stats[:3]):validate_rng_witnesses(ob,row)
            for stage,index in((1,3),(2,4)):
                count=validate_rng_witnesses(observations[index],stats[index])
                statistics.append(dict(profile=profile,child=stage,observation=observed,rng_witness_checks=count,**stats[index]))
                for target in MODES:
                    expected={n:gzip.decompress((root/profile/f'child-{stage}'/target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                    cases.append(dict(profile=profile,child=stage,observation=observed,target=target,**compare(expected,outputs[index])))
    if len(cases)!=144 or len(statistics)!=24:raise ValueError('complete four-profile three-source new-child inventory required')
    return dict(recipe='bounded-survivor-five-day-replay-v1',cases=cases,statistics=statistics)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_survivor_chains import verify
    verify(a.root);report=compare_cases(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    failures=[c for c in report['cases']if c['byte_mismatches']]
    print(json.dumps(dict(comparisons=len(report['cases']),files=6*len(report['cases']),mismatches=len(failures))))
    if failures:raise SystemExit('at least one complete native comparison differs')

if __name__=='__main__':main()
