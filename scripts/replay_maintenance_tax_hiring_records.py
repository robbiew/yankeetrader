"""Before-only five-day tax-funded hiring replay from an original occupied world.

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
from replay_maintenance_evolved_records import ClockInputs,Inputs,FILES,MODES,legacy_day,_watermark_and_inactive_ranks
from replay_maintenance_evolved_combat_records import inputs_from_observation
from replay_maintenance_tax_hiring_ports import replay_ports
from replay_maintenance_tax_hiring_npcs import synthesize as npc_synthesize
from replay_maintenance_tax_hiring_aux import synthesize as aux_synthesize
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_maintenance_records import compare
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/tax-hiring-controls'
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
    aux,aux_stats=aux_synthesize(before_files,work,clock.news_date,clock.news_clock,clock.score_date,clock.score_clock,created=npcs['created'],events=npcs['events'],mercenary=npcs['mercenary'],taxation=npcs['taxation'],hiring=npcs['hiring'],rng_audit=npcs['rng_audit'],rng_source=npcs['rng_source'],rng_contexts=npcs['rng_contexts'])
    return {'YTDATA.DAT':work,**aux},dict(ports=port_stats,npcs=npcs,auxiliary=aux_stats,final_day=day)


CASES={'one-group':100,'ten-groups':1000}
PARENT_CASE='route-mercenary-100000'

def apply_fixture(files,case):
    if type(files)is not dict or set(files)!=set(FILES)or any(type(b)is not bytes for b in files.values())or case not in CASES:
        raise ValueError('complete modeled parent and declared treasury case required')
    world=files['YTDATA.DAT']
    if any(mbf.get(world,r,89)!=0 for r in range(3052,4052))or mbf.get(world,1,81)!=308:
        raise ValueError('unmodified November4 zero-treasury parent required')
    out=dict(files);work=bytearray(world);mbf.put(work,3053,89,CASES[case]);out['YTDATA.DAT']=bytes(work);return out


def synthesize_chain(initial_before,case,inputs):
    """All five days are modeled before any comparison target is loaded."""
    if case not in CASES:raise ValueError('declared positive treasury fixture required')
    if type(initial_before)is not dict or set(initial_before)!=set(FILES[:3])or any(type(b)is not bytes for b in initial_before.values()):
        raise ValueError('three immutable original before files required')
    if combat.old.ADMITTED_INPUTS.get(SHA(initial_before['YTDATA.DAT']))!=PARENT_CASE:
        raise ValueError('measured original occupied prefix required')
    if type(inputs)is not tuple or len(inputs)!=5 or any(type(i)is not Inputs or type(i.clock)is not ClockInputs for i in inputs):
        raise ValueError('five immutable source-day inputs required')
    if tuple(i.clock.startup_date for i in inputs)!=tuple(datetime.date(2026,11,d)for d in range(2,7)):
        raise ValueError('only measured November2-through6 chronology admitted')
    for index,i in enumerate(inputs[3:],3):
        expected_score='00:00:02'if case=='one-group'and index==3 else'00:00:03'
        if(i.clock.news_clock,i.clock.score_clock)!=('00:00:02',expected_score):raise ValueError('measured source publication clocks required')
    prefix,stats=combat.synthesize_chain(initial_before,inputs[:3]);outputs=list(prefix);rows=list(stats)
    work=apply_fixture(outputs[-1],case)
    for values in inputs[3:]:
        work,row=_synthesize_day(work,values);outputs.append(work);rows.append(row)
    return tuple(outputs),tuple(rows)


def initial_before():return combat.initial_before(PARENT_CASE)


def observation_paths(case,observed,root=DEFAULT):
    if case not in CASES or observed not in('observed-a','observed-b','observed-c'):raise ValueError('measured case and observed mode required')
    return (combat.PARENT/PARENT_CASE/observed/'host-time.json.gz',)+tuple(combat.DEFAULT/PARENT_CASE/f'child-{i}'/observed/'host-time.json.gz'for i in(1,2))+tuple(Path(root)/case/f'child-{i}'/observed/'host-time.json.gz'for i in(1,2))


def compare_cases(directory=DEFAULT):
    root=Path(directory);cases=[];statistics=[]
    for profile in CASES:
        before=initial_before()
        for observed in('observed-a','observed-b','observed-c'):
            observations=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in observation_paths(profile,observed,root))
            outputs,stats=synthesize_chain(before,profile,tuple(inputs_from_observation(o)for o in observations))
            # Every modeled day exists before target/child files are first opened.
            for ob,row in zip(observations[:3],stats[:3]):validate_rng_witnesses(ob,row)
            for stage,index in((1,3),(2,4)):
                count=validate_rng_witnesses(observations[index],stats[index])
                statistics.append(dict(profile=profile,child=stage,observation=observed,rng_witness_checks=count,**stats[index]))
                for target in MODES:
                    expected={n:gzip.decompress((root/profile/f'child-{stage}'/target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                    cases.append(dict(profile=profile,child=stage,observation=observed,target=target,**compare(expected,outputs[index])))
    if len(cases)!=72 or len(statistics)!=12:raise ValueError('complete two-case three-source new-child inventory required')
    return dict(recipe='bounded-tax-hiring-five-day-replay-v1',cases=cases,statistics=statistics)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_tax_hiring import verify
    verify(a.root);report=compare_cases(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2,default=lambda v:v.hex()if type(v)is bytes else v.__dict__)+'\n')
    failures=[c for c in report['cases']if c['byte_mismatches']]
    print(json.dumps(dict(comparisons=len(report['cases']),files=6*len(report['cases']),mismatches=len(failures))))
    if failures:raise SystemExit('at least one complete native comparison differs')

if __name__=='__main__':main()
