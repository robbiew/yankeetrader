"""Before-only zero-tax Mercenary tail for bounded collision-replay fixtures.

The caller restores/places the missing Base first. This routine then follows
original464b..535a: eager desertion rolls and a descending, mutable-sector scan.
Only the retained zero-human, zero-mine, empty-route37-fighter branch is admitted;
it does not claim general Mercenary combat or planet stock pickup.
"""
import hashlib
import math
from pathlib import Path

from replay_qb_graph import mbf, F32
from replay_maintenance_npcs import directed_path, MAINT_SHA

ROOT=Path(__file__).resolve().parents[1]


def maintain(world, stream):
    """Mutate source-owned sector fields and return derived audit statistics.

    ``world`` is an independently synthesized bytearray, never an after-target.
    ``stream`` derives all RNG state from startup plus explicit TIMER inputs;
    its source-labelled ``one`` call must not infer branches from observations.
    """
    if type(world)is not bytearray or len(world)!=4151*137:
        raise ValueError('complete mutable modeled default world required')
    get=lambda rec,off:mbf.get(world,rec,off)
    if any(get(1,o)!=n for o,n in ((53,51),(57,3051),(61,4051),(93,4151))):
        raise ValueError('default geometry required for bounded Mercenary tail')
    if any(get(r,85)!=0 for r in range(2,52)):
        raise ValueError('only all-inactive human-player fixtures are recovered')
    if any(get(r,89)!=0 for r in range(3052,4052)):
        raise ValueError('tax-funded Mercenary hiring is outside this profile')
    # Preserve the original source-specific exponent-zero residue, rather than
    # replacing it with the distinct cache/cleanup zeros8472 or7f58.
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    if hashlib.sha256(original).hexdigest()!=MAINT_SHA:
        raise ValueError('original maintenance identity differs')
    cleared=original[0x859e+0xfd0:0x859e+0xfd4]
    if cleared!=bytes.fromhex('00002800'):
        raise ValueError('original Mercenary departure zero differs')
    def putraw(rec,off,value):
        at=(rec-1)*137+off;world[at:at+4]=value
    def put(rec,off,value):putraw(rec,off,mbf.enc(value))

    physical=[];mercenary_total=0
    for sector in range(1,3001):
        force=get(51+sector,81);owner=get(51+sector,85)
        if not math.isfinite(force)or force!=int(force)or not 0<=force<=1000000:
            raise ValueError('bounded whole sector force required')
        if force:
            if owner not in(-2,-1,0):
                raise ValueError('human desertion and unknown sector owners are outside this profile')
            physical.append(sector)
            if owner==-2:mercenary_total+=int(force)
    if mercenary_total not in(0,37):
        raise ValueError('only absent or one retained37-fighter Mercenary force is recovered')
    #4664..47c6 evaluates the draw even though owner>1 is false for all admitted
    # owners. No conversion or public desertion message is invented.
    for sector in physical:stream.rng.rnd()

    warps={s:[get(51+s,off)for off in range(41,65,4)]for s in range(1,3001)}
    if any(n!=int(n)or not 0<=n<=3000 for row in warps.values()for n in row):
        raise ValueError('bounded original integer graph required')
    warps={s:list(map(int,row))for s,row in warps.items()}
    activations=[];movement_draws=0;target_draws=0
    #47e7/5318 scans descending and rereads mutable records. An arrival at a
    #lower sector can therefore move again later in the same maintenance.
    for origin in range(3000,0,-1):
        record=51+origin;force=int(get(record,81))
        if force<=0 or get(record,85)!=-2:continue
        if force!=37:
            raise ValueError('merged or changed Mercenary force is outside this profile')
        if len(activations)>=16:
            raise ValueError('bounded Mercenary reactivation guard')
        gate=stream.rng.rnd();movement_draws+=1
        link=get(record,93)
        if link>0 and gate<F32(.66):
            activations.append(dict(origin=origin,force=force,gate=gate,held=True))
            continue
        if link>0:
            raise ValueError('departing an occupied origin is outside the retained empty-route profile')
        #4876..48a6 clears both origin fields before target selection. Helpers
        #reseed on each same-origin rejection at48f9, not one continuous stream.
        putraw(record,81,cleared);putraw(record,85,cleared)
        candidates=[]
        for _ in range(64):
            target=stream.one(3000,caller=0x48cf);target_draws+=1;candidates.append(target)
            if target!=origin:break
        else:raise ValueError('bounded same-origin target rejection guard')
        route=directed_path(warps,origin,target)
        if len(route)<2:raise ValueError('nonempty source route required')
        for sector in route[1:]:
            rec=51+sector
            if get(rec,129)!=0:
                raise ValueError('Mercenary mine damage is outside this retained profile')
            if get(rec,81)!=0:
                raise ValueError('Mercenary merge/defense combat is outside this retained profile')
            if get(rec,93)>0:
                raise ValueError('Mercenary planet stock pickup is outside this retained profile')
        #495f..49cc reaches an empty successor at the endpoint and saves the
        #surviving whole force/title. Intermediate empty sectors are only read.
        put(51+target,81,force);put(51+target,85,-2)
        activations.append(dict(origin=origin,force=force,gate=gate,held=False,
                                candidates=candidates,target=target,route=route))
    final=[s for s in range(1,3001)if get(51+s,81)>0 and get(51+s,85)==-2]
    if sum(int(get(51+s,81))for s in final)!=mercenary_total:
        raise ValueError('bounded Mercenary conservation failed')
    return dict(desertion_draws=len(physical),desertion_sectors=physical,
                movement_gate_draws=movement_draws,target_draws=target_draws,
                activations=activations,final_sectors=final,force=mercenary_total,
                events=[])
