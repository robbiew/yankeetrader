"""Before-only replay of the four measured evolved clock/date profiles.

No captured child save, public transcript, probe or old RNG state is an input.
The original November 2 parent and both child worlds are independently modeled.
"""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import replay_maintenance_evolved_records as old
from replay_maintenance_evolved_records import ClockInputs,Inputs,inputs_from_observation,FILES,MODES,legacy_day,_watermark_and_inactive_ranks
from replay_maintenance_evolved_clock_ports import replay_ports
from replay_maintenance_evolved_clock_npcs import synthesize as npc_synthesize
from replay_maintenance_evolved_clock_aux import synthesize as aux_synthesize
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_maintenance_records import compare

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/evolved-clock-controls'
SHA=lambda b:hashlib.sha256(b).hexdigest()
DATE_PAIRS={'second-two':('2026-11-03','2026-11-04'),'noon':('2026-11-03','2026-11-04'),
            'catchup-eleven':('2026-11-13','2026-11-14'),'new-year':('2027-01-01','2027-01-02')}

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
    aux,aux_stats=aux_synthesize(before_files,work,clock.news_date,clock.news_clock,clock.score_date,clock.score_clock,created=npcs['created'],events=npcs['events'])
    return {'YTDATA.DAT':work,**aux},dict(ports=port_stats,npcs=npcs,auxiliary=aux_stats,final_day=day)


def synthesize_chain(initial_before,inputs):
    """Compute the old bootstrap and both selected children before comparisons."""
    if type(initial_before)is not dict or set(initial_before)!=set(FILES[:3])or any(type(b)is not bytes for b in initial_before.values()):
        raise ValueError('exact three initial raw before files required')
    for n,digest in zip(FILES[:3],(old.INITIAL_SHA,'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f','1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a')):
        if SHA(initial_before[n])!=digest:raise ValueError('unmeasured initial world rejected')
    if type(inputs)is not tuple or len(inputs)!=3 or any(type(v)is not Inputs or type(v.clock)is not ClockInputs for v in inputs):
        raise ValueError('three frozen source-day inputs required')
    first,child,second=inputs
    if first.clock.startup_date!=datetime.date(2026,11,2):raise ValueError('original measured convergence parent required')
    dates=(child.clock.startup_date,second.clock.startup_date)
    if dates not in tuple((datetime.date.fromisoformat(a),datetime.date.fromisoformat(b))for a,b in DATE_PAIRS.values()):
        raise ValueError('only four measured evolved clock/date pairs admitted')
    clocks=(child.clock.news_clock,second.clock.news_clock)
    if dates==(datetime.date(2026,11,3),datetime.date(2026,11,4)):
        if clocks not in(('00:00:02','00:00:00'),('12:00:00','00:00:00')):raise ValueError('measured second-two or noon clocks required')
    elif clocks!=('00:00:00','00:00:00'):raise ValueError('measured catchup/New Year midnight clocks required')
    work,row=old._synthesize_day(initial_before,first);outputs=[work];stats=[row]
    for values in(child,second):
        work,row=_synthesize_day(work,values)
        outputs.append(work);stats.append(row)
    return tuple(outputs),tuple(stats)


def compare_cases(directory=DEFAULT):
    root=Path(directory);before=old.initial_before();cases=[];statistics=[]
    for profile in DATE_PAIRS:
        for observed in('observed-a','observed-b','observed-c'):
            paths=(old.DEFAULT/'day-1'/observed/'host-time.json.gz',)+tuple(root/profile/f'child-{i}'/observed/'host-time.json.gz' for i in(1,2))
            observations=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in paths)
            outputs,stats=synthesize_chain(before,tuple(inputs_from_observation(ob)for ob in observations))
            # The whole chain exists before any target or child-before is opened.
            validate_rng_witnesses(observations[0],stats[0])
            for stage in(1,2):
                count=validate_rng_witnesses(observations[stage],stats[stage])
                statistics.append(dict(profile=profile,child=stage,observation=observed,rng_witness_checks=count,**stats[stage]))
                for target in MODES:
                    expected={n:gzip.decompress((root/profile/f'child-{stage}'/target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                    cases.append(dict(profile=profile,child=stage,observation=observed,target=target,**compare(expected,outputs[stage])))
    if len(cases)!=144 or len(statistics)!=24:raise ValueError('complete four-profile three-source comparison inventory required')
    return dict(recipe='bounded-evolved-clock-replay-v1',cases=cases,statistics=statistics)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_evolved_clocks import verify
    verify(a.root);report=compare_cases(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    failures=[r for r in report['cases']if r['byte_mismatches']]
    print(json.dumps(dict(comparisons=len(report['cases']),files=6*len(report['cases']),mismatches=len(failures))))
    if failures:raise SystemExit('at least one complete native comparison differs')

if __name__=='__main__':main()
