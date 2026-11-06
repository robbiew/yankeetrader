"""Before-only bounded occupied-origin departures, friendly merges and home pickup.

The source descending scan acts on modeled records and explicit source clocks.
No captured state or output file is opened. Historical profile APIs are unchanged.
"""
import hashlib
import math
from pathlib import Path

from replay_qb_graph import mbf, F32
from replay_maintenance_npcs import directed_path, MAINT_SHA

ROOT=Path(__file__).resolve().parents[1]


MAX_FORCE=400000


def maintain(world,stream):
    """Commit modeled source writes only after the complete admitted tail succeeds."""
    if type(world)is not bytearray or len(world)!=4151*137:
        raise ValueError('complete mutable modeled default world required')
    work=bytearray(world)
    result=_maintain(work,stream)
    world[:]=work
    return result


def _maintain(world, stream):
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
        if not math.isfinite(force)or force!=int(force)or not 0<=force<=MAX_FORCE:
            raise ValueError('bounded whole sector force required')
        if force:
            if owner not in(-2,-1,0):
                raise ValueError('human desertion and unknown sector owners are outside this profile')
            physical.append(sector)
            if owner==-2:mercenary_total+=int(force)
    if not 0<=mercenary_total<=MAX_FORCE:
        raise ValueError('bounded surviving Mercenary force required')
    #4664..47c6 evaluates the draw even though owner>1 is false for all admitted
    # owners. No conversion or public desertion message is invented.
    for sector in physical:stream.rng.rnd()

    warps={s:[get(51+s,off)for off in range(41,65,4)]for s in range(1,3001)}
    if any(n!=int(n)or not 0<=n<=3000 for row in warps.values()for n in row):
        raise ValueError('bounded original integer graph required')
    warps={s:list(map(int,row))for s,row in warps.items()}
    activations=[];events=[];movement_draws=0;target_draws=0
    #47e7/5318 scans descending and rereads mutable records. An arrival at a
    #lower sector can therefore move again later in the same maintenance.
    for origin in range(3000,0,-1):
        record=51+origin;force=int(get(record,81))
        if force<=0 or get(record,85)!=-2:continue
        if not 1<=force<=MAX_FORCE:
            raise ValueError('bounded whole surviving Mercenary force required')
        if len(activations)>=16:
            raise ValueError('bounded Mercenary reactivation guard')
        gate=stream.rng.rnd();movement_draws+=1
        link=get(record,93)
        if link>0 and gate<F32(.66):
            activations.append(dict(origin=origin,force=force,gate=gate,held=True))
            continue
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
        initial_force=force;stopped=False;entered=[]
        for sector in route[1:]:
            entered.append(sector);rec=51+sector
            if get(rec,129)!=0:
                event=mine_hit(world,stream,sector,force)
                events.append(event);force=event['force']
                if not force:break
            # Source4c7f tests the cached entering owner/link BEFORE foreign
            # defense. A victory does not fall through into pickup on this pass.
            if get(rec,93)>0 and get(rec,85)in(0,-2):
                event=pickup(world,sector,force)
                events.append(event);force=event['force'];stopped=True;break
            if get(rec,81)>0 and get(rec,85)==-2:
                event=merge(world,sector,force)
                events.append(event);force=event['force']
                continue
            if get(rec,81)!=0:
                event=attack(world,stream,sector,force)
                events.append(event);force=event['force']
                if not force:break
        # Pickup saves immediately at its actual encounter; ordinary empty
        # routes save at their computed endpoint. Fatal mines save no force.
        destination=sector if stopped else target
        if force and not stopped:put(51+destination,81,force);put(51+destination,85,-2)
        activations.append(dict(origin=origin,force=initial_force,gate=gate,held=False,
                                candidates=candidates,target=target,route=route,entered=entered,
                                stopped_for_pickup=stopped,final_sector=destination if force else None,final_force=force))
    final=[s for s in range(1,3001)if get(51+s,81)>0 and get(51+s,85)==-2]
    final_force=sum(int(get(51+s,81))for s in final)
    pickup_total=sum(e.get('pickup',0)for e in events)
    actual_losses=sum(e.get('losses',0)for e in events)
    if final_force+actual_losses!=mercenary_total+pickup_total:
        raise ValueError('bounded Mercenary conservation failed')
    return dict(desertion_draws=len(physical),desertion_sectors=physical,
                movement_gate_draws=movement_draws,target_draws=target_draws,
                activations=activations,final_sectors=final,force=final_force,initial_force=mercenary_total,losses=actual_losses,pickup=pickup_total,merged=sum(e.get('merged',0)for e in events),
                events=events)


def attack(world,stream,sector,force):
    """Original4ec3..51e3: source-selected negative Xannor owner attack.

    The ordinary .95 branch draw is eager even for the negative owner whose
    sign independently forces combat. This draw does not reseed a helper.
    Both sides above original DOUBLE200 use150 casualties; otherwise one.
    """
    if type(world)is not bytearray or len(world)!=4151*137 or type(sector)is not int or not 8<=sector<=3000 or type(force)is not int or not 1<=force<=MAX_FORCE:
        raise ValueError('bounded mutable world, route sector and attacking force required')
    get=lambda off:mbf.get(world,51+sector,off)
    defenders=get(81);owner=get(85)
    if owner!=-1 or defenders!=int(defenders)or not 1<=defenders<=10000 or get(93)!=0 or get(129)!=0:
        raise ValueError('only actual whole Xannor defense after mine damage admitted')
    # Original data8916..891d is a DOUBLE operand, not its misleading first
    # four-byte zero. Bind both literals directly to the immutable binary.
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    if hashlib.sha256(original).hexdigest()!=MAINT_SHA:raise ValueError('original maintenance identity differs')
    threshold_raw=original[0x8916+0xfd0:0x891e+0xfd0]
    if threshold_raw!=bytes.fromhex('0000000000004888'):raise ValueError('original double combat threshold differs')
    threshold=200 # exact MBF DOUBLE above; no after-world supplies this value
    batch_raw=original[0x891e+0xfd0:0x8922+0xfd0];batch=int(mbf.dec(batch_raw))
    if batch!=150:raise ValueError('original casualty batch differs')
    initial=force;initial_defenders=int(defenders);remaining=int(defenders);old=stream.rng.state;draws=stream.rng.draws
    gate=stream.rng.rnd();rounds=0
    for _ in range(200000):
        if force<=0 or remaining<=0:break
        damage=batch if min(force,remaining)>threshold else 1
        if stream.rng.rnd()<.5:remaining=max(0,remaining-damage)
        else:force=max(0,force-damage)
        rounds+=1
    else:raise ValueError('bounded Mercenary combat round guard')
    at=(50+sector)*137
    # Source5196..51b4 canonical zeroes the defeated force and owner. It never
    # visits the group-pointer cache, whose deployment pointer can remain stale.
    world[at+81:at+85]=mbf.enc(remaining)
    if not remaining:world[at+85:at+89]=mbf.enc(0)
    return dict(kind='mercenary-attack',sector=sector,owner=owner,defender_name='The Xannor',
                initial_force=initial,initial_defenders=initial_defenders,force=force,defenders=remaining,
                losses=initial-force,defender_losses=initial_defenders-remaining,gate=gate,rounds=rounds,
                initial_rng_state=old,final_rng_state=stream.rng.state,rng_draws=stream.rng.draws-draws)


def mine_hit(world,stream,sector,force):
    """Original4a78..4c7a: count-two shrinking damage per INITIAL mine.

    The source helper count is two, unlike the four-draw allocation caller.
    All initial mines call it even after force zero. A mine is spent only for
    positive capped damage; canonical single subtraction writes exact zero.
    """
    if type(world)is not bytearray or len(world)!=4151*137 or type(sector)is not int or not 8<=sector<=3000 or type(force)is not int or not 1<=force<=MAX_FORCE:
        raise ValueError('bounded actual non-Union route force and sector required')
    rec=51+sector;mines=mbf.get(world,rec,129)
    if mines!=int(mines)or not 1<=mines<=3 or mbf.get(world,rec,93)!=0 or mbf.get(world,rec,85)not in(-1,0):
        raise ValueError('one through three actual nonplanet mines before neutral/Xannor defense required')
    initial=int(mines);remaining=force;spent=0;rolls=[];old=stream.rng.state;draws=stream.rng.draws
    for _ in range(initial):
        stream.reseed('h2',0x4aa4)
        bound=10000
        for _ in range(2):bound=stream.rng.integer(bound)
        rolls.append(bound);damage=min(remaining,bound)
        if remaining>0 and damage>0:
            remaining-=damage;mines-=1;spent+=1
    # Commit once the initial-count helper loop completes, preserving exact
    # final source subtraction bytes while leaving rejects unmodified.
    mbf.put(world,rec,129,mines)
    return dict(kind='mercenary-mine',sector=sector,initial_force=force,force=remaining,
                losses=force-remaining,initial_mines=initial,mines=int(mines),mines_spent=spent,
                rolls=rolls,initial_rng_state=old,final_rng_state=stream.rng.state,
                rng_draws=stream.rng.draws-draws)



def _zero_literal():
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    if hashlib.sha256(original).hexdigest()!=MAINT_SHA:raise ValueError('original maintenance identity differs')
    zero=original[0x8472+0xfd0:0x8476+0xfd0]
    if zero!=bytes.fromhex('00008000'):raise ValueError('source pickup/merge zero differs')
    return zero


def merge(world,sector,force):
    """Original4ef7..4f5f: absorb friendly force, clear it and continue silently."""
    if type(world)is not bytearray or len(world)!=4151*137 or type(sector)is not int or not 8<=sector<=3000 or type(force)is not int or not 1<=force<=MAX_FORCE:
        raise ValueError('bounded actual friendly encounter required')
    rec=51+sector;get=lambda off:mbf.get(world,rec,off)
    defenders=get(81)
    if get(85)!=-2 or defenders!=int(defenders)or not 1<=defenders<=MAX_FORCE or get(93)!=0 or get(129)!=0:
        raise ValueError('positive whole friendly nonplanet nonmine force required')
    final=force+int(defenders)
    if final>MAX_FORCE:raise ValueError('bounded merged force required before source clear')
    zero=_zero_literal();at=(rec-1)*137
    world[at+81:at+85]=zero;world[at+85:at+89]=zero
    return dict(kind='mercenary-merge',sector=sector,initial_force=force,initial_defenders=int(defenders),
                force=final,defenders=0,owner=-2,merged=int(defenders),losses=0)


def pickup(world,sector,force):
    """Bounded original4c7f..4ec0 home pickup without title/ground transfer.

    The measured Wanderer stock has a positive subhalf fraction. Both positive
    floor and nearest conversion agree in this admitted slice; larger fractions
    remain rejected pending general runtime qualification. Full raw stock is
    cleared even though only the derived whole count joins physical force.
    """
    if type(world)is not bytearray or len(world)!=4151*137 or type(sector)is not int or not 8<=sector<=3000 or type(force)is not int or not 1<=force<=MAX_FORCE:
        raise ValueError('bounded positive route pickup force required')
    rec=51+sector;get=lambda r,o:mbf.get(world,r,o);slot=get(rec,93)
    if slot not in(1,3)or get(rec,85)not in(0,-2)or get(rec,81)!=0 or get(rec,129)!=0:
        raise ValueError('only clear neutral measured home pickup admitted')
    planet=4051+int(slot);at=(planet-1)*137
    title=b'The Wanderer'if slot==1 else b'Departure Cache'
    if bytes(world[at:at+41])!=title.ljust(41,b' ')or get(planet,85)!=len(title)or get(planet,73)!=0:
        raise ValueError('actual neutral measured planet identity required')
    if slot==3 and sector not in(2999,3000):raise ValueError('declared Departure Cache physical link required')
    stock=get(planet,129)
    if not math.isfinite(stock)or not 0<=stock<=300000:raise ValueError('bounded nonnegative measured home stock required')
    whole=math.floor(stock);fraction=stock-whole
    if fraction>=.5:raise ValueError('unqualified positive half-or-greater stock conversion excluded')
    if slot==3 and(stock!=int(stock)or stock>40):raise ValueError('whole measured Departure Cache stock required')
    final=force+whole
    if final>MAX_FORCE:raise ValueError('bounded post-pickup whole force required before any write')
    zero=_zero_literal()
    world[at+129:at+133]=zero
    mbf.put(world,rec,81,final);mbf.put(world,rec,85,-2)
    return dict(kind='mercenary-pickup',sector=sector,planet_slot=int(slot),planet_name=title.decode('ascii'),
                captured=True,initial_force=force,force=final,pickup=whole,raw_stock=stock,
                fractional_discard=fraction,conversion='bounded-positive-subhalf-whole')
