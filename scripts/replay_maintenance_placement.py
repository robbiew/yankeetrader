"""Bounded source-qualified placement and before-only group-cache primitives.

These primitives do not claim full evolved-world maintenance replay. The cache
model reads only before-world fields. Placement consumes declared original
helper TIMER/old-state witnesses; it never reads an expected after-world.
"""
import copy
import math
import struct

from replay_qb_graph import mbf,QB3
import verify_maintenance_clock_matrix as clocks


def cache(before):
    if type(before)is not bytes or len(before)!=4151*137:raise ValueError('complete default before-world required')
    get=lambda r,o:mbf.get(before,r,o)
    if any(get(1,o)!=n for o,n in ((53,51),(57,3051),(61,4051),(93,4151))):raise ValueError('default geometry required')
    locations={g:get(51+g,105)for g in range(1,21)};forces={g:0 for g in locations};cleared={}
    for g,where in locations.items():
        if not math.isfinite(where)or where!=int(where)or not 0<=where<=3000:raise ValueError('bounded integral group pointers required')
        locations[g]=int(where)
    # Physical consumption precedes pair normalization; a second pointer cannot
    # re-read a force/title already cleared by an earlier pointer.
    for g,where in locations.items():
        if where and where not in cleared and get(51+where,85)==-1:
            force=get(51+where,81)
            if not math.isfinite(force)or force!=int(force)or not 0<=force<=1000000:raise ValueError('bounded integer Xannor force required')
            forces[g]=int(force);cleared[where]=bytes.fromhex('00008000')
    for i in range(1,20):
        for j in range(i+1,21):
            if locations[i]==locations[j]:
                locations[j]=0;forces[i]+=forces[j];forces[j]=0
    for g in locations:
        if locations[g]<1 or forces[g]<1:locations[g]=forces[g]=0
    return dict(locations=locations,forces=forces,cleared_sectors=cleared,total=sum(forces.values()))


def observations(raw):
    if raw.get('recipe')!='host-dos-placement-cache-observer-v1':raise ValueError('explicit placement observer required')
    standard=copy.deepcopy(raw);standard['recipe']='host-dos-clock-matrix-observer-v1'
    states=[]
    for original,event in zip(raw['events'],standard['events']):
        before=event['before'].pop('rng_raw');after=event['after'].pop('rng_raw')
        if before!=after or not isinstance(before,str)or len(before)!=8:raise ValueError('stable exact raw RNG read during DOS callback required')
        state=int.from_bytes(bytes.fromhex(before),'little')
        if not 0<=state<2**24:raise ValueError('24bit raw RNG state required')
        pair=clocks.event_pair(event,event['ordinal'])
        if pair['kind']=='timer'and pair['role']=='helper1'and pair['nested_return_ip']in(0x1f88,0x437a):
            states.append(dict(role='wanderer'if pair['nested_return_ip']==0x1f88 else'base',ordinal=pair['ordinal'],old_state=state,timer=pair['seconds']))
    # Authenticate the complete source/clock inventory as well, not just selected
    # helper rows. New state fields are validated before stripping for this API.
    clocks.model_inputs(standard)
    return states


def placements(before,witnesses):
    if type(before)is not bytes or len(before)!=4151*137:raise ValueError('complete default before-world required')
    if any(mbf.get(before,1,o)!=n for o,n in ((53,51),(57,3051),(61,4051),(93,4151))):
        raise ValueError('default placement geometry required')
    links={s:mbf.get(before,51+s,93)for s in range(1,3001)}
    if any(not math.isfinite(v)or not -1<=v<=100 for v in links.values()):raise ValueError('bounded initial link gates required')
    if any(v in (1,99,100)for v in links.values()):
        raise ValueError('preexisting special-planet links are outside the missing-NPC profile')
    hq=mbf.get(before,1,117)
    if hq!=int(hq)or not 8<=hq<=3000:raise ValueError('bounded tracked HQ required')
    if any(mbf.get(before,r,85)!=0 for r in range(4052,4152)):raise ValueError('only missing-NPC inactive-planet fixture required')
    attempts=[];accepted={};previous=None
    if not 2<=len(witnesses)<=64:raise ValueError('bounded complete placement witness inventory required')
    for row in witnesses:
        if set(row)!= {'role','ordinal','old_state','timer'}:raise ValueError('exact typed placement witness required')
        role=row['role'];timer=row['timer'];old=row['old_state']
        if role not in ('wanderer','base')or role in accepted:raise ValueError('no witnesses after acceptance')
        if role=='base'and 'wanderer'not in accepted:raise ValueError('source placement phase order required')
        if type(old)is not int or not 0<=old<2**24 or type(timer)is not bytes or len(timer)!=4:raise ValueError('raw TIMER and24bit old state required')
        if type(row['ordinal'])is not int or row['ordinal']<=0 or(previous is not None and row['ordinal']<=previous['ordinal']):raise ValueError('ordered unique source witnesses required')
        # Consecutive rejected attempts have no intervening RND. Across the
        # intervening Xannor phase, the Base old state is a measured explicit
        # input, not a claimed reconstruction of unmodeled movement/combat.
        if previous is not None and role==previous['role']and old!=previous['result_state']:
            raise ValueError('rejected selection retains prior RND low/state witness')
        seed=(old&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)
        rng=QB3(seed);candidate=rng.integer(3000);link=links[candidate]
        result=dict(**row,seeded_state=seed,result_state=rng.state,candidate=candidate,link=link,rejected=link>0)
        attempts.append(result);previous=result
        if link<=0:
            accepted[role]=candidate;links[candidate]=1 if role=='wanderer'else 99
            if role=='wanderer':links[int(hq)]=100
    if set(accepted)!={'wanderer','base'}:raise ValueError('both source placement phases must accept')
    return dict(attempts=attempts,accepted=accepted)


def before_from_recipe(recipe,case):
    """Comparison-side loader of declared before-inputs; no outputs are read."""
    import gzip
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    before=bytearray(gzip.decompress((root/'research/yt-maint/initial-controls/baseline-split/before-YTDATA.DAT.gz').read_bytes()))
    if recipe.get('recipe')!='maintenance-placement-cache-v1'or case not in recipe.get('cases',{}):raise ValueError('explicit before recipe required')
    seen=set()
    for rec,off,value in recipe['cases'][case]:
        if type(rec)is not int or not 52<=rec<=3051 or off not in(81,85,93,105)or(rec,off)in seen:raise ValueError('declared distinct sector-field overrides required')
        seen.add((rec,off));raw=bytes.fromhex(value)if type(value)is str else mbf.enc(value)
        if len(raw)!=4:raise ValueError('four-byte before field required')
        at=(rec-1)*137+off;before[at:at+4]=raw
    return bytes(before)


def compare(directory):
    """Read targets only after each bounded primitive has produced its result."""
    import gzip,json
    from pathlib import Path
    root=Path(directory);recipe=json.loads((root/'recipe.json').read_text());results=[]
    expected_modes={'unobserved-a','unobserved-b','attach-only','observed-a','observed-b','observed-c','cache-probe'}
    if not recipe.get('cases'):raise ValueError('nonempty declared recipe inventory required')
    for case in recipe['cases']:
        if {p.name for p in(root/case).iterdir()}!=expected_modes:raise ValueError('complete six-mode plus cache-probe inventory required')
        before=before_from_recipe(recipe,case);c=cache(before)
        # First comparison is a separately stopped source-stage diagnostic,
        # not a claim about the final world's later movement/ownership.
        probe=root/case/'cache-probe';data=(probe/'TRACE.BIN').read_bytes()[-168:]
        if len(data)!=168:raise ValueError('complete source-stage cache packet required')
        for g in range(1,21):
            if data[4*g:4*g+4]!=mbf.enc(c['locations'][g])or data[4*(g+21):4*(g+21)+4]!=mbf.enc(c['forces'][g]):
                raise ValueError('before-only cache fields differ from source-stage probe')
        placements_by_mode=[]
        for mode in ('observed-a','observed-b','observed-c'):
            raw=json.loads(gzip.decompress((root/case/mode/'host-time.json.gz').read_bytes()))
            prediction=placements(before,observations(raw))
            for target in expected_modes-{'cache-probe'}:
                world=gzip.decompress((root/case/target/'after-YTDATA.DAT.gz').read_bytes())
                for role,sector in prediction['accepted'].items():
                    slot=1 if role=='wanderer'else 99
                    if mbf.get(world,51+sector,93)!=slot:raise ValueError('predicted accepted placement differs from complete target')
            serial=[{**row,'timer':row['timer'].hex()}for row in prediction['attempts']]
            placements_by_mode.append(dict(mode=mode,accepted=prediction['accepted'],attempts=serial))
        results.append(dict(case=case,cache_fields=40,cache_total=c['total'],locations=c['locations'],forces=c['forces'],placements=placements_by_mode))
    return dict(recipe='bounded-placement-cache-primitives-v1',cases=results,
                cache_field_comparisons=40*len(results),placement_target_checks=36*len(results),
                limitations=['Source-qualified old RNG/TIMER inputs, not full maintenance-stream synthesis.',
                             'Only declared initial-world cache/placement branches; evolved worlds and live gameplay are separate.'])


def main():
    import argparse,json
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]/'research/yt-maint/placement-cache-controls');p.add_argument('--output',type=Path);a=p.parse_args()
    from verify_maintenance_placement import verify
    verify(a.root)
    report=compare(a.root)
    if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k!='cases'}))

if __name__=='__main__':main()
