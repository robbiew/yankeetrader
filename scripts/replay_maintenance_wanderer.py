"""Before-only extension for the measured initial Xannor/Wanderer encounter.

Historical clock-matrix synthesis remains strict by default. This explicit
profile admits only a freshly restored, neutral, zero-ground Wanderer with empty
warehouses and rates above 500 throughout the selected encounter. General
planet combat, deletion, populated players and evolved worlds remain rejected.
"""
import argparse
import gzip
import json
from pathlib import Path
import math

import replay_qb_graph as qb


def assault(world, stream, group, sector, force, wanderer_sector):
    """Follow original5efd production branch; receive no expected output bytes."""
    from replay_maintenance_npcs import UnsupportedClockMatrixEncounter, constants
    get=lambda rec,off:qb.mbf.get(world,rec,off)
    record=4052
    context=dict(group=group,sector=sector,planet_slot=get(51+sector,93),rng_state=stream.rng.state)
    def require(condition,message):
        if not condition:raise UnsupportedClockMatrixEncounter(message,context)
    require(sector==wanderer_sector and context['planet_slot']==1,'only the restored Wanderer encounter is recovered')
    require(world[(record-1)*137:(record-1)*137+12]==b'The Wanderer'and get(record,85)==12,
            'only the named active Wanderer is recovered')
    require(get(record,73)==0 and get(record,77)==0,'only neutral zero-ground Wanderer assault is recovered')
    require(get(51+sector,81)==0 and get(51+sector,89)==0,'only unscreened Wanderer assault is recovered')
    require(all(get(record,o)==0 for o in (57,61,65)),'only empty Wanderer warehouses are recovered')
    require(type(force)is int and 1<=force<=10000 and 2<=group<=19,'only bounded ordinary moving groups are recovered')
    rates=[get(record,o)for o in (45,49,53)]
    require(all(math.isfinite(r)and r>500 for r in rates),'only positive large-batch Wanderer rates are recovered')
    old=stream.rng.state;draws=stream.rng.draws;rounds=[];initial_force=force
    # Existing planetary research establishes the location-subscript defect:
    # positive group location selects450 even when force<450. Keep it in this
    # research oracle, not in modern Go gameplay. Each arithmetic operation is
    # rounded to the native single-precision array type before assignment.
    for _ in range(4096):
        if force<=0:break
        require(all(r>500 for r in rates),'small-rate/deletion paths are outside this encounter profile')
        gate=stream.rng.rnd()
        if gate<.5:
            damage=[stream.rng.rnd()for _ in rates]
            rates=[qb.F32(r-qb.F32(qb.F32(d*450)/3))for r,d in zip(rates,damage)]
            rounds.append(dict(gate=gate,damage=damage,force=force,rates=list(rates)))
        else:
            force-=450;rounds.append(dict(gate=gate,force=force,rates=list(rates)))
    else:raise UnsupportedClockMatrixEncounter('research encounter round limit',context)
    require(all(r>500 for r in rates),'small-rate/deletion aftermath is outside this encounter profile')
    for off,value in zip((45,49,53),rates):
        at=(record-1)*137+off;world[at:at+4]=qb.mbf.enc(value)
    # Zero ground is never canonicalized: only owner is rewritten by655b..6586.
    at=(record-1)*137+73;world[at:at+4]=constants()[0x8b98]
    return dict(group=group,sector=sector,planet_slot=1,planet_name='The Wanderer',
                initial_force=initial_force,
                raw_force=force,force=0,initial_rng_state=old,final_rng_state=stream.rng.state,
                rng_draws=stream.rng.draws-draws,rounds=rounds,final_rates=rates)


def synthesize(before_files,inputs):
    from replay_maintenance_clock_matrix import synthesize as matrix
    return matrix(before_files,inputs,wanderer_encounters=True)


def compare_cases(root=None):
    import replay_maintenance_clock_matrix as matrix
    from replay_maintenance_records import compare
    root=matrix.DEFAULT if root is None else Path(root)
    from verify_maintenance_clock_matrix import PROFILES,MODES
    profiles={p.name for p in root.iterdir()}
    if profiles not in ({'late'},set(PROFILES)):
        raise ValueError('complete eight-profile matrix or six-run late corpus required')
    for recipe in root.iterdir():
        if not recipe.is_dir()or {p.name for p in recipe.iterdir()}!=set(MODES):
            raise ValueError('all six untouched/attach-only/observed controls required')
        for mode in MODES:
            if mode!='unobserved-a'and mode!='unobserved-b'and not(recipe/mode/'host-time.json.gz').is_file():
                raise ValueError('complete source-qualified observer inventory required')
    source=matrix.ROOT/'research/yt-maint/initial-controls/baseline-split'
    before={n:gzip.decompress((source/('before-'+n+'.gz')).read_bytes())for n in matrix.FILES[:3]}
    rows=[];stats=[]
    for recipe in sorted(p for p in root.iterdir()if p.is_dir()):
        controls=sorted(p for p in recipe.iterdir()if p.is_dir())
        for observed in controls:
            path=observed/'host-time.json.gz'
            if not path.exists():continue
            ob=json.loads(gzip.decompress(path.read_bytes()))
            if ob.get('observe')is not observed.name.startswith('observed-'):
                raise ValueError('actual observer mode must match complete corpus inventory')
            if not ob['observe']:continue
            actual,item=synthesize(before,matrix.inputs_from_observation(ob))
            stats.append(dict(recipe=recipe.name,observation=observed.name,**item))
            for target in controls:
                expected={n:gzip.decompress((target/('after-'+n+'.gz')).read_bytes())for n in matrix.FILES}
                rows.append(dict(recipe=recipe.name,observation=observed.name,target=target.name,**compare(expected,actual)))
    if len(rows)!=len(profiles)*18 or len(stats)!=len(profiles)*3:
        raise ValueError('complete observed/target comparison inventory required')
    return dict(recipe='initial-wanderer-encounter-replay-v1',cases=rows,statistics=stats)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    report=compare_cases(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    failures=[r for r in report['cases']if r['byte_mismatches']]
    print(json.dumps(dict(comparisons=len(report['cases']),file_comparisons=6*len(report['cases']),mismatches=len(failures))))
    if failures:raise SystemExit('replay differs from original outputs; inspect report')

if __name__=='__main__':main()
