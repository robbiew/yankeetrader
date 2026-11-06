"""Complete before-only six-file replay for the twelve initial collision fixtures.

Only explicit clock/date observations become synthesis inputs. Captured old RNG
states, cache probes, expected outputs and masks are excluded from this API.
"""
import argparse
from dataclasses import dataclass
import copy
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import replay_maintenance_clock_matrix as matrix
from replay_maintenance_ports import replay_capped_initial_ports
from replay_maintenance_collision_npcs import synthesize as npcs
from replay_maintenance_collision_aux import synthesize as auxiliary
from replay_maintenance_records import compare
from replay_maintenance_placement import before_from_recipe

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/placement-cache-controls'
FILES=matrix.FILES
SHA=lambda b:hashlib.sha256(b).hexdigest()
ADMITTED_INPUTS={'08a5f821fc48f26123ce6397a5f53e0855c834d7b4cee0ae68a517cfa3d2276d': 'wanderer-reject-two',
 '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d': 'historical-baseline',
 '1a7b9de132309145dbead87e1c42e81ad8b6360978d555519cc6a49a28136dde': 'wanderer-positive-fraction',
 '29cb96e5e4f8b61d1149119a96c8e78f02b3820aef2738462b5c231cd16062ab': 'pointer-mercenary-sector',
 '2d57896febbb3e2017f053d78bab702956fdc6039f0d06fbdf21706b97d65881': 'wanderer-reject-three',
 '5314cea88c2270efd020a6774fd82dcfff1ad7a0e606fd673272ce7297de37bf': 'pointer-neutral-sector',
 '63cb645fc375f5f2c184f307bede0097440307d9ec9f1d4349476ad46c3a1521': 'wanderer-negative-link',
 '649e23706682f67ed8d878594caf17deefd949b8b6593fc6a72799a650704437': 'duplicate-mobile',
 '7c5298bcf453fb4c23b099260535391e14e9a06064e88cde5a36cbdb2f9f2f2a': 'duplicate-hq',
 '84cfee8fb5ce001fe9b1a14c8eb0e3ee3ccf37e7ed18b88e25b3ce3df55dc861': 'wanderer-zero-residue',
 'b35f0f7397c66818a327ef59e310a315e809b1daad91a10f9bd32aa1726252a6': 'base-positive-fraction',
 'd22dc06ff1f778692c0ef30a226e61cfc0a3b92be7d6c4c46306bf7930c6675a': 'duplicate-hq-chain',
 'e6013d8d5a5ff778dcac5c5c663147616b1a59a1c229a5ce2207131d516bce30': 'unpointed-friendly-merge'}


@dataclass(frozen=True)
class Inputs:
    clock:matrix.Inputs
    schedule:tuple


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
    return Inputs(clock,schedule)


def synthesize(before_files,inputs):
    if type(inputs)is not Inputs or type(inputs.clock)is not matrix.Inputs or type(inputs.schedule)is not tuple:
        raise ValueError('explicit immutable source clock inputs required')
    if type(before_files)is not dict or set(before_files)!=set(FILES[:3])or any(type(b)is not bytes for b in before_files.values()):
        raise ValueError('three raw before-input files required')
    before=before_files['YTDATA.DAT']
    if SHA(before)not in ADMITTED_INPUTS:raise ValueError('unmeasured before-world rejected by collision profile')
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
    port_days=tuple(matrix.legacy_day(before,date)for date in clock.port_dates)
    phase_days={name:matrix.legacy_day(before,date)for name,date in [('wanderer',clock.wanderer_date),('xannoron',clock.xannoron_date),('base',clock.base_date)]}
    final=matrix.legacy_day(before,clock.final_date)
    chronology=[matrix.legacy_day(before,clock.startup_date),*port_days,*phase_days.values(),final]
    if chronology!=sorted(chronology):raise ValueError('backward phase calendar excluded')
    block,port_stats=replay_capped_initial_ports(before,port_days,clock.port_timer_minutes)
    work=before[:3051*137]+block+before[4051*137:]
    work,npc_stats=npcs(work,SimpleNamespace(clock=clock,schedule=inputs.schedule,phase_days=phase_days,final_day=final))
    work=matrix._watermark_and_inactive_ranks(work,final)
    aux,aux_stats=auxiliary(before_files,work,clock.news_date,clock.news_clock,clock.score_date,clock.score_clock,
                            encounters=npc_stats['encounters'],events=npc_stats['mercenary']['events'])
    result={'YTDATA.DAT':work,**aux}
    if set(result)!=set(FILES):raise ValueError('complete six-file synthesis required')
    return result,dict(ports=port_stats,npcs=npc_stats,auxiliary=aux_stats,final_day=final)


def compare_cases(directory=DEFAULT):
    root=Path(directory);recipe=json.loads((root/'recipe.json').read_text());rows=[];statistics=[]
    if len(recipe.get('cases',{}))!=12:raise ValueError('complete twelve-case retained recipe required')
    base=ROOT/'research/yt-maint/initial-controls/baseline-split'
    files={n:gzip.decompress((base/('before-'+n+'.gz')).read_bytes())for n in FILES[:3]}
    for case in recipe['cases']:
        before={**files,'YTDATA.DAT':before_from_recipe(recipe,case)}
        if ADMITTED_INPUTS.get(SHA(before['YTDATA.DAT']))!=case:
            raise ValueError('complete admitted case/input identity required')
        if {p.name for p in(root/case).iterdir()}!={'unobserved-a','unobserved-b','attach-only','observed-a','observed-b','observed-c','cache-probe'}:
            raise ValueError('complete seven-mode source corpus required')
        for observed in ('observed-a','observed-b','observed-c'):
            ob=json.loads(gzip.decompress((root/case/observed/'host-time.json.gz').read_bytes()))
            actual,stats=synthesize(before,inputs_from_observation(ob))
            witness_checks=validate_rng_witnesses(ob,stats)
            statistics.append(dict(case=case,observation=observed,rng_witness_checks=witness_checks,**stats))
            for target in ('unobserved-a','unobserved-b','attach-only','observed-a','observed-b','observed-c'):
                expected={n:gzip.decompress((root/case/target/('after-'+n+'.gz')).read_bytes())for n in FILES}
                rows.append(dict(case=case,observation=observed,target=target,**compare(expected,actual)))
    if len(rows)!=216 or len(statistics)!=36:raise ValueError('complete twelve-case comparison inventory required')
    return dict(recipe='bounded-collision-record-replay-v1',cases=rows,statistics=statistics)


def validate_rng_witnesses(observation,statistics):
    """Comparison only: assert modeled states, never feed them back into replay."""
    from verify_maintenance_clock_matrix import event_pair
    if observation.get('recipe')!='host-dos-placement-cache-observer-v1':
        raise ValueError('independent raw RNG witness observer required')
    seeds=iter(statistics['npcs']['helper_seeds']);count=0;final=[]
    for event in observation['events']:
        row=copy.deepcopy(event);states=[]
        for side in('before','after'):
            raw=row[side].pop('rng_raw')
            if type(raw)is not str or len(raw)!=8:raise ValueError('four-byte RNG witness required')
            value=int.from_bytes(bytes.fromhex(raw),'little')
            if value>=2**24:raise ValueError('24bit RNG witness required')
            states.append(value)
        if states[0]!=states[1]:raise ValueError('DOS callback changed RNG witness')
        pair=event_pair(row,row['ordinal'])
        if pair.get('kind')=='timer'and pair.get('role')in('helper1','helper2'):
            modeled=next(seeds,None)
            family='h1'if pair['role']=='helper1'else'h2'
            if modeled is None or modeled['family']!=family or modeled['caller']!=pair['nested_return_ip']or modeled['timer']!=pair['seconds'].hex()or modeled['old_state']!=states[0]:
                raise ValueError('derived helper state/chronology differs from independent witness')
            count+=1
        if pair.get('role')=='score':final.append(states[0])
    if next(seeds,None)is not None or count==0 or len(final)!=2 or any(v!=statistics['npcs']['final_rng_state']for v in final):
        raise ValueError('complete helper inventory and final scoreboard RNG state must agree')
    return count+len(final)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_placement import verify
    verify(a.root);report=compare_cases(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    failures=[r for r in report['cases']if r['byte_mismatches']]
    print(json.dumps(dict(comparisons=len(report['cases']),files=6*len(report['cases']),mismatches=len(failures))))
    if failures:raise SystemExit('at least one complete native comparison differs')

if __name__=='__main__':main()
