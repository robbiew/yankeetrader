"""Before-only departure replay: three modeled prefix days, declared fixture, two children.

Synthesis accepts original bytes, a case name and source clocks only. Target and
observation loaders are comparison-side APIs and never enter the core.
"""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import replay_maintenance_evolved_combat_records as combat
import verify_maintenance_clock_matrix as clocks
from replay_maintenance_evolved_records import ClockInputs,Inputs,FILES,MODES,legacy_day,_watermark_and_inactive_ranks
from replay_maintenance_departure_ports import replay_ports
from replay_maintenance_departure_npcs import synthesize as npc_synthesize
from replay_maintenance_departure_aux import synthesize as aux_synthesize
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_maintenance_records import compare
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/departure-merge-controls'
PARENT_CASE='route-mercenary-100000'
CASES={
 'vacant-origin':(False,0,'00:00:00'),
 'friendly-merge':(False,37,'00:00:00'),
 'occupied-midnight':(True,0,'00:00:00'),
 'occupied-second-two':(True,0,'00:00:02'),
 'occupied-second-four':(True,0,'00:00:04'),
 'occupied-friendly-midnight':(True,37,'00:00:00'),
 'occupied-friendly-second-two':(True,37,'00:00:02'),
 'occupied-friendly-second-four':(True,37,'00:00:04'),
}
SHA=lambda b:hashlib.sha256(b).hexdigest()

from replay_maintenance_gateway_records import inputs_from_observation

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
    seconds=[mbf.dec(r[2])for r in inputs.schedule]
    if any(not 0<=value<60 for value in seconds)or seconds!=sorted(seconds):
        raise ValueError('measured first-minute chronological helper clocks required')
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


def apply_fixture(modeled_parent,case):
    """Pure declared data edits over the actual modeled November4 six-file object."""
    if type(case)is not str or case not in CASES:raise ValueError('one of eight declared departure fixtures required')
    if type(modeled_parent)is not dict or set(modeled_parent)!=set(FILES)or any(type(b)is not bytes for b in modeled_parent.values()):
        raise ValueError('complete immutable modeled parent required')
    world=bytearray(modeled_parent['YTDATA.DAT'])
    if len(world)!=4151*137:raise ValueError('complete default modeled world required')
    get=lambda r,o:mbf.get(world,r,o)
    if get(1,81)!=308 or get(2419,81)!=97337 or get(2419,85)!=-2:
        raise ValueError('measured modeled November4 Mercenary origin required')
    if any(get(3051,o)!=0 for o in(81,85,93,129))or get(4054,85)!=0 or get(3050,93)!=0:
        raise ValueError('gateway sector and slot must be initially vacant')
    edits=[]
    def putraw(r,o,b):
        at=(r-1)*137+o;edits.append(dict(record=r,offset=o,before=bytes(world[at:at+len(b)]).hex(),after=b.hex()));world[at:at+len(b)]=b
    def put(r,o,n):putraw(r,o,mbf.enc(n))
    occupied,friendly,_=CASES[case]
    for o in range(41,65,4):put(3051,o,2368)
    for sector,o in((2996,45),(2998,49),(2999,53)):put(51+sector,o,2368)
    put(2419,45,3000)
    for o,n in((81,friendly),(85,-2 if friendly else 0)):put(2419,o,n)
    for o,n in((81,97337),(85,-2)):put(3051,o,n)
    planet=bytearray(b'Departure Cache'.ljust(41,b' ')+bytes(96))
    for o,n in((41,308),(73,0),(77,500000),(85,15),(89,0),(117,0),(129,37)):planet[o:o+4]=mbf.enc(n)
    putraw(4054,0,bytes(planet))
    put(3051 if occupied else 3050,93,3)
    return {**modeled_parent,'YTDATA.DAT':bytes(world)},tuple(edits)


def synthesize_chain(initial_before,inputs,case):
    """Finish all five modeled days before a comparison may read native targets."""
    if type(case)is not str or case not in CASES:raise ValueError('declared departure case required')
    if type(initial_before)is not dict or set(initial_before)!=set(FILES[:3])or any(type(b)is not bytes for b in initial_before.values()):
        raise ValueError('three original immutable before files required')
    if combat.old.ADMITTED_INPUTS.get(SHA(initial_before['YTDATA.DAT']))!=PARENT_CASE:
        raise ValueError('only measured original Mercenary100000 world admitted')
    if type(inputs)is not tuple or len(inputs)!=5 or any(type(i)is not Inputs or type(i.clock)is not ClockInputs for i in inputs):
        raise ValueError('five immutable source-day inputs required')
    if tuple(i.clock.startup_date for i in inputs)!=tuple(datetime.date(2026,11,d)for d in range(2,7)):
        raise ValueError('only measured November2-through6 chronology admitted')
    for index,i in enumerate(inputs[3:],3):
        text=CASES[case][2]
        score='00:00:01'if index==3 and case=='vacant-origin'else text
        if(i.clock.news_clock,i.clock.score_clock)!=(text,score):
            raise ValueError('separate explicit measured departure publication clocks required')
    prefix,stats=combat.synthesize_chain(initial_before,inputs[:3])
    work,edits=apply_fixture(prefix[-1],case)
    outputs=list(prefix);rows=list(stats)
    for i,values in enumerate(inputs[3:]):
        work,row=_synthesize_day(work,values)
        if set(work)!=set(FILES):raise ValueError('complete modeled child required')
        row['fixture_edits']=edits if i==0 else()
        outputs.append(work);rows.append(row)
    return tuple(outputs),tuple(rows)


def initial_before():
    """Comparison-only initial loader; never called by synthesis."""
    return combat.initial_before(PARENT_CASE)


def observation_paths(case,observed,root=DEFAULT):
    if type(case)is not str or case not in CASES or observed not in('observed-a','observed-b','observed-c'):
        raise ValueError('declared case and observed source mode required')
    return (combat.PARENT/PARENT_CASE/observed/'host-time.json.gz',)+tuple(combat.DEFAULT/PARENT_CASE/f'child-{i}'/observed/'host-time.json.gz'for i in(1,2))+tuple(Path(root)/case/f'child-{i}'/observed/'host-time.json.gz'for i in(1,2))


def compare_cases(directory=DEFAULT):
    root=Path(directory);cases=[];statistics=[];before=initial_before()
    for case in CASES:
        for observed in('observed-a','observed-b','observed-c'):
            observations=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in observation_paths(case,observed,root))
            values=tuple((combat.inputs_from_observation if i<3 else inputs_from_observation)(o)for i,o in enumerate(observations))
            outputs,stats=synthesize_chain(before,values,case)
            for ob,row in zip(observations[:3],stats[:3]):validate_rng_witnesses(ob,row)
            for stage,index in((1,3),(2,4)):
                count=validate_rng_witnesses(observations[index],stats[index])
                statistics.append(dict(case=case,child=stage,observation=observed,rng_witness_checks=count,**stats[index]))
                for target in MODES:
                    expected={n:gzip.decompress((root/case/f'child-{stage}'/target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                    result=compare(expected,outputs[index])
                    result['raw_differences']=[dict(file=n,offset=offset,observed=a,replayed=b)for n in FILES for offset,(a,b)in enumerate(zip(expected[n],outputs[index][n]))if a!=b]if result['byte_mismatches']else[]
                    cases.append(dict(case=case,child=stage,observation=observed,target=target,**result))
    if len(cases)!=288 or len(statistics)!=48:raise ValueError('complete eight-case three-source comparison inventory required')
    return dict(recipe='bounded-departure-five-day-replay-v1',cases=cases,statistics=statistics)



def assert_comparisons(report):
    rows=report['cases']
    matrix={(case,child,observed,target)for case in CASES for child in(1,2)for observed in('observed-a','observed-b','observed-c')for target in MODES}
    if len(rows)!=288 or {(r['case'],r['child'],r['observation'],r['target'])for r in rows}!=matrix:
        raise ValueError('complete unique comparison matrix required')
    for r in rows:
        if set(r['files'])!=set(FILES)or sum(v['byte_mismatches']for v in r['files'].values())!=r['byte_mismatches']or len(r['raw_differences'])!=r['byte_mismatches']:
            raise ValueError('complete unmasked file and byte inventories required')
        if len({(d['file'],d['offset'])for d in r['raw_differences']})!=len(r['raw_differences']):raise ValueError('each differing raw byte appears once')
    failures=[row for row in rows if row['byte_mismatches']]
    expected={(case,child,observed,target)for case in('occupied-friendly-second-two',)for child in(1,2)for observed in('observed-a','observed-b','observed-c')for target in('unobserved-a','unobserved-b','attach-only')}
    actual={(r['case'],r['child'],r['observation'],r['target'])for r in failures}
    if actual!=expected:raise ValueError('unexpected mismatch inventory; no source-clock or world normalization allowed')
    for r in failures:
        expected_bytes=89 if r['child']==1 else 94
        if r['byte_mismatches']!=expected_bytes or len(r['raw_differences'])!=expected_bytes:raise ValueError('disclosed raw difference count changed')
        if any(v['byte_mismatches']for n,v in r['files'].items()if n!='YTDATA.DAT'):raise ValueError('nonworld comparison changed')
        end=3594 if r['child']==1 else 3597
        for difference in r['raw_differences']:
            record,offset=divmod(difference['offset'],137)
            if difference['file']!='YTDATA.DAT'or not 3583<=record+1<=end or offset not in set(range(49,73))|set(range(101,105)):
                raise ValueError('difference outside disclosed raw port clock/supply writer fields')
    return dict(exact_comparisons=len(report['cases'])-len(failures),disclosed_unequal_comparisons=len(failures),normalized_bytes=0)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_departure_merge import verify
    report=compare_cases(a.root);verify(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    failures=[c for c in report['cases']if c['byte_mismatches']]
    audit=assert_comparisons(report)
    print(json.dumps(dict(comparisons=len(report['cases']),files=6*len(report['cases']),rng_witness_checks=sum(s['rng_witness_checks']for s in report['statistics']),**audit)))

if __name__=='__main__':main()
