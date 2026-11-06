"""Complete before-only six-file replay for the ten measured active-planet/foreign-route fixtures.

Only explicit clock/date observations become synthesis inputs. Captured old RNG
states, cache probes, expected outputs and masks are excluded from this API.
"""
import argparse
from dataclasses import dataclass
import copy
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import replay_maintenance_clock_matrix as matrix
from replay_maintenance_ports import replay_capped_initial_ports
from replay_maintenance_occupied_npcs import synthesize as npcs
from replay_maintenance_occupied_aux import synthesize as auxiliary
from replay_maintenance_records import compare
from replay_maintenance_collision_records import validate_rng_witnesses

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/occupied-route-controls'
FILES=matrix.FILES
SHA=lambda b:hashlib.sha256(b).hexdigest()
ADMITTED_INPUTS={'f3791778af7ec503dd98e34b030c328c66c4a9e0431fc43dffa5eb1d12816a4c': 'wanderer-occupied',
 '70e270190c2a4bb9dc246a0d53d5cb270a9df04805a7b70d4fd452d509e8ab2b': 'wanderer-two-occupied',
 '5f758fc6559124ed665fa4d523bf08bb08f99dca71d2047fca11cefa0a13e8a2': 'base-occupied',
 '1522c4e0ebc60b6678825289ba7128174a0e72add90f538f89c63a1f6ebbc008': 'route-planet-friendly',
 'f545d697b28d93910407cfeb7baac96666062ebe3cb5ac3334d6a3e85f5e45b7': 'route-planet-neutral',
 '40947d888c7bd9192acfc12d2531d6414fe6392c9c815ead42ea4d28ef6325bf': 'route-mercenary-37',
 '0e5d8934af1be3debc72708ecdd3e2825a2c4000398253fc8b793340907669a6': 'route-mercenary-100000',
 '277c3cadeea74b02596c3d832566ff7de5b39a7a5a1b8edbd9a2ac563edd31b6': 'route-neutral-37',
 '9d5dcb72ff9fb127e45d3449704af5edbab6abc519af2c707c702df1625db14a': 'wanderer-active-rejection',
 'fae728912fae47d5bc9a64dfc4a6cd1c47a5a25fe022ceca2962f87370088c8a': 'base-active-rejection'}


@dataclass(frozen=True)
class Inputs:
    clock:matrix.Inputs
    schedule:tuple
    planet_clocks:tuple


def inputs_from_observation(observation):
    """Source-qualified TIMER/date inputs; discard every captured RNG state."""
    raw=copy.deepcopy(observation)
    if raw.get('recipe')=='host-dos-placement-cache-observer-v1':
        # This value is never copied into Inputs or used to seed the model.
        # The independent evidence verifier authenticates its contents.
        raw['recipe']='host-dos-clock-matrix-observer-v1'
        for event in raw['events']:
            for side in('before','after'):event[side].pop('rng_raw')
    clock=matrix.inputs_from_observation(raw)
    from verify_maintenance_clock_matrix import model_inputs
    typed=model_inputs(raw)
    entries=sorted(typed['timer_entries']['helper1']+typed['timer_entries']['helper2'],key=lambda row:row['ordinal'])
    schedule=tuple(('h1'if row['role']=='helper1'else'h2',row['nested_return_ip'],row['seconds'])for row in entries)
    dates=typed['planet_dates'];timers=typed['planet_timers']
    if len(dates)!=len(timers)or len(dates)>2:raise ValueError('complete bounded active-planet source clocks required')
    rows=[]
    for index,(date,timer)in enumerate(zip(dates,timers)):
        if date['ordinal']>=timer['ordinal']:raise ValueError('planet calendar must precede its own TIMER')
        day=(date['date']-datetime.date(2026,1,1)).days+1
        rows.append((4053+index,day,timer['minutes']))
    return Inputs(clock,schedule,tuple(rows))


def synthesize(before_files,inputs):
    if type(inputs)is not Inputs or type(inputs.clock)is not matrix.Inputs or type(inputs.schedule)is not tuple or type(inputs.planet_clocks)is not tuple:
        raise ValueError('explicit immutable source clock inputs required')
    if type(before_files)is not dict or set(before_files)!=set(FILES[:3])or any(type(b)is not bytes for b in before_files.values()):
        raise ValueError('three raw before-input files required')
    before=before_files['YTDATA.DAT']
    if SHA(before)not in ADMITTED_INPUTS:raise ValueError('unmeasured before-world rejected by occupied profile')
    if SHA(before_files['YTNAME.DAT'])!='af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f'or SHA(before_files['YTNEWS.DAT'])!='1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a':
        raise ValueError('unmeasured side-file before-inputs rejected')
    clock=inputs.clock
    if type(clock.initial_state)is not int or not 0<=clock.initial_state<2**24:raise ValueError('24bit startup seed required')
    if len(clock.port_dates)!=1000 or len(clock.port_timer_minutes)!=1000:raise ValueError('complete per-port source clock inputs required')
    if any(type(values)is not tuple for values in (clock.port_dates,clock.port_timer_minutes,clock.h1_timers,clock.h2_timers)):
        raise ValueError('immutable source clock arrays required')
    if any(type(row)is not tuple or len(row)!=3 or row[0]not in('h1','h2')or type(row[1])is not int or type(row[2])is not bytes or len(row[2])!=4 for row in inputs.schedule):
        raise ValueError('typed source-labelled helper schedule required')
    if tuple(row[2]for row in inputs.schedule if row[0]=='h1')!=clock.h1_timers or tuple(row[2]for row in inputs.schedule if row[0]=='h2')!=clock.h2_timers:
        raise ValueError('helper clock arrays and chronological schedule must agree')
    active=tuple(r for r in range(4052,4152)if matrix.graph.mbf.get(before,r,85)>0)
    if tuple(row[0]for row in inputs.planet_clocks if type(row)is tuple and len(row)==3)!=active:
        raise ValueError('complete source clocks in ascending active-record order required')
    if any(type(row)is not tuple or len(row)!=3 or type(row[0])is not int or type(row[1])is not int or type(row[2])is not bytes or len(row[2])!=4 for row in inputs.planet_clocks):
        raise ValueError('typed immutable active-planet source clock rows required')
    port_days=tuple(matrix.legacy_day(before,date)for date in clock.port_dates)
    phase_days={name:matrix.legacy_day(before,date)for name,date in [('wanderer',clock.wanderer_date),('xannoron',clock.xannoron_date),('base',clock.base_date)]}
    final=matrix.legacy_day(before,clock.final_date)
    chronology=[matrix.legacy_day(before,clock.startup_date),*port_days,*(row[1]for row in inputs.planet_clocks),*phase_days.values(),final]
    if chronology!=sorted(chronology):raise ValueError('backward phase calendar excluded')
    block,port_stats=replay_capped_initial_ports(before,port_days,clock.port_timer_minutes)
    work=before[:3051*137]+block+before[4051*137:]
    work,npc_stats=npcs(work,SimpleNamespace(clock=clock,schedule=inputs.schedule,phase_days=phase_days,final_day=final,planet_clocks=inputs.planet_clocks))
    work=matrix._watermark_and_inactive_ranks(work,final)
    aux,aux_stats=auxiliary(before_files,work,clock.news_date,clock.news_clock,clock.score_date,clock.score_clock,
                            events=npc_stats['events'])
    result={'YTDATA.DAT':work,**aux}
    if set(result)!=set(FILES):raise ValueError('complete six-file synthesis required')
    return result,dict(ports=port_stats,npcs=npc_stats,auxiliary=aux_stats,final_day=final)


def before_inputs(case,directory=DEFAULT):
    """Comparison-side fixture loader; core synthesis never opens this recipe."""
    if case not in ADMITTED_INPUTS.values():raise ValueError('unknown retained occupied case')
    base=ROOT/'research/yt-maint/initial-controls/baseline-split'
    files={n:gzip.decompress((base/('before-'+n+'.gz')).read_bytes())for n in FILES[:3]}
    recipe=json.loads((Path(directory)/'recipe.json').read_text())['cases'][case]
    work=bytearray(files['YTDATA.DAT']);mbf=matrix.graph.mbf
    def put(rec,off,value):
        at=(rec-1)*137+off;work[at:at+4]=mbf.enc(value)
    for sector,slot,name,owner,ground in recipe['planets']:
        rec=4051+slot;at=(rec-1)*137
        work[at:at+137]=name.encode('ascii').ljust(41,b' ')+bytes(96)
        for off,value in [(41,305),(45,1000),(49,1000),(53,1000),(73,owner),(77,ground),(85,len(name))]:put(rec,off,value)
        put(51+sector,93,slot)
    for sector,force,owner in recipe['forces']:
        put(51+sector,81,force);put(51+sector,85,owner)
    files['YTDATA.DAT']=bytes(work)
    if ADMITTED_INPUTS.get(SHA(files['YTDATA.DAT']))!=case:raise ValueError('retained input fingerprint differs')
    return files


def compare_cases(directory=DEFAULT):
    root=Path(directory);recipe=json.loads((root/'recipe.json').read_text());rows=[];statistics=[]
    if set(recipe.get('cases',{}))!=set(ADMITTED_INPUTS.values()):raise ValueError('complete ten-case input inventory required')
    modes={'unobserved-a','unobserved-b','attach-only','observed-a','observed-b','observed-c'}
    for case in recipe['cases']:
        before=before_inputs(case,root)
        if {p.name for p in(root/case).iterdir()}!=modes:raise ValueError('complete six-mode source corpus required')
        for observed in ('observed-a','observed-b','observed-c'):
            ob=json.loads(gzip.decompress((root/case/observed/'host-time.json.gz').read_bytes()))
            actual,stats=synthesize(before,inputs_from_observation(ob))
            witness_checks=validate_rng_witnesses(ob,stats)
            statistics.append(dict(case=case,observation=observed,rng_witness_checks=witness_checks,**stats))
            for target in sorted(modes):
                expected={n:gzip.decompress((root/case/target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                rows.append(dict(case=case,observation=observed,target=target,**compare(expected,actual)))
    if len(rows)!=180 or len(statistics)!=30:raise ValueError('complete ten-case comparison inventory required')
    return dict(recipe='bounded-occupied-record-replay-v1',cases=rows,statistics=statistics)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_occupied import verify
    verify(a.root);report=compare_cases(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    failures=[r for r in report['cases']if r['byte_mismatches']]
    print(json.dumps(dict(comparisons=len(report['cases']),files=6*len(report['cases']),mismatches=len(failures))))
    if failures:raise SystemExit('at least one complete native comparison differs')

if __name__=='__main__':main()
