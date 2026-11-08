"""Before-only two-day tax-funded continuation of recovered NPC branches."""
import math
from replay_maintenance_npcs import constants,directed_path,F32
from replay_maintenance_placement import cache
import replay_qb_graph as qb


from replay_maintenance_tax_hiring_rng import SourceStream as Stream
from replay_maintenance_tax_hiring_rules import admit_treasuries,tax_ports,hire


def synthesize(before,inputs):
    clock=inputs.clock;initial_state=clock.initial_state;xannoron_timer=clock.xannoron_timer
    matrix_days=inputs.phase_days;day=inputs.final_day
    assert isinstance(before, bytes) and len(before) == 4151 * 137, 'default world extent'
    assert xannoron_timer is None or(type(xannoron_timer)is bytes and len(xannoron_timer)==4), 'explicit optional Xannoron TIMER'
    world = bytearray(before)
    const = constants()

    def raw(rec, off):
        at = (rec - 1) * 137 + off
        return bytes(world[at:at + 4])

    def get(rec, off):
        return qb.mbf.dec(raw(rec, off))

    def putraw(rec, off, value):
        assert len(value) == 4
        at = (rec - 1) * 137 + off
        world[at:at + 4] = value

    def put(rec, off, value):
        putraw(rec, off, qb.mbf.enc(value))

    def title(rec, text):
        at = (rec - 1) * 137
        world[at:at + 41] = text.encode('ascii').ljust(41, b' ')
        put(rec, 85, len(text))

    assert(get(1,81),day)in((308,309),(309,310)), 'only measured tax-funded next-day handoffs admitted'
    assert get(1, 53) == 51 and get(1, 57) == 3051 and get(1, 93) == 4151, 'default record boundaries'
    assert all(get(rec, 85) == 0 for rec in range(2, 52)), 'inactive player fixture only'
    assert all(get(rec,85)==0 for rec in range(4052,4152)if rec not in(4052,4053,4150,4151)), 'only measured ordinary active slots admitted'
    admit_treasuries(before)
    hq = int(get(1, 117))
    assert 7 < hq <= 3000 and get(52, 105) == hq, 'configured tracked HQ'
    assert get(51+hq,85)==-1 and 0<get(51+hq,81)<=10000, 'bounded tracked HQ force'
    initial_physical=sum(get(51+s,81)for s in range(1,3001))
    assert 0<initial_physical<=110000,'bounded actual before physical force'
    assert all(not get(51+s,81)or(0<=get(51+s,81)<=100000 and get(51+s,81)==int(get(51+s,81))and get(51+s,85)in(-2,-1,0))for s in range(1,3001)),'bounded actual Xannor, Mercenary or neutral physical force'
    assert sum(get(51+s,81)for s in range(1,3001)if get(51+s,85)==-1)<=10000,'bounded actual Xannor total'
    assert sum(get(51+s,81)for s in range(1,3001)if get(51+s,85)==-2)<=100000,'bounded actual Mercenary total'
    assert all(get(51+s,81)in(0,37)for s in range(1,3001)if get(51+s,85)==0),'only retained neutral37 physical force'
    warps = {s: [get(51 + s, o) for o in range(41, 65, 4)] for s in range(1, 3001)}
    assert all(n == int(n) and 0 <= n <= 3000 for row in warps.values() for n in row), 'bounded original integer warps'
    warps = {s: [int(n) for n in row] for s, row in warps.items()}
    matrix=matrix_days is not None
    dates={'wanderer':day,'xannoron':day,'base':day}if not matrix else matrix_days
    assert set(dates)=={'wanderer','xannoron','base'}and all(v is None or(type(v)is int and 306<=v<=367)for v in dates.values()), 'bounded phase calendar days'
    stream = Stream(inputs.schedule,initial_state)
    from replay_maintenance_survivor_planets import maintain as active_planets
    planet_stats=active_planets(world,stream,inputs.planet_clocks)

    # Source1d07..1d9a unlinks the first actual slot1 reference before search.
    created=[];wanderer=4052
    old_links=[s for s in range(1,3001)if get(51+s,93)==1]
    if old_links:
        if len(old_links)!=1 or dates['wanderer']is not None:raise ValueError('one existing Wanderer and no restoration clock required')
        putraw(51+old_links[0],93,const[0x7f58])
    else:
        if dates['wanderer']is None:raise ValueError('missing Wanderer requires explicit creation date')
        created.append('wanderer')
        title(wanderer, 'The Wanderer')
        put(wanderer, 41, dates['wanderer'] - 10)
        for off in (45, 49, 53):
            putraw(wanderer, off, const[0x82ac])
        for off in (57, 61, 65, 69, 77, 125):
            putraw(wanderer, off, const[0x82b0])
        putraw(wanderer, 117, const[0x82b4])
    wanderer_attempts=[]
    for _ in range(64):
        wanderer_sector=stream.one(3000,caller=0x1f88)
        wanderer_attempts.append(wanderer_sector)
        if get(51+wanderer_sector,93)<=0:break
    else:raise ValueError('bounded Wanderer placement exhausted')
    put(51 + wanderer_sector, 93, 1)
    # Main2015..2024 unconditionally replaces the owner with canonical0.
    putraw(wanderer,73,const[0x7f58])
    if get(wanderer,117)==0:putraw(wanderer,117,const[0x82b4])

    xannoron=4151
    if get(51+hq,93)!=100:
        if dates['xannoron']is None or xannoron_timer is None:raise ValueError('missing Xannoron requires explicit creation clocks')
        created.append('xannoron')
        xannoron = 4151
        title(xannoron, 'Xannoron')
        put(xannoron, 41, dates['xannoron'])
        seconds=qb.mbf.dec(xannoron_timer)
        minutes=F32(seconds/60)
        assert 0<=seconds<86400 and 0<=minutes<1440, 'bounded initial-creation TIMER'
        if minutes>=1:
            truncated=bytearray(qb.mbf.enc(math.floor(minutes)))
        else:
            # Preserve each admitted profile's original INT-zero FAC behavior.
            value=xannoron_timer if matrix and seconds==0 else qb.mbf.enc(minutes)
            truncated=bytearray(value)
            truncated[3]=0
        putraw(xannoron, 89, bytes(truncated))
        for off in (45, 49, 53):
            putraw(xannoron, off, const[0x8134])
        for off in (57, 61, 65, 69):
            putraw(xannoron, off, const[0x8386])
        putraw(xannoron, 73, const[0x7ea0])
        ground = math.floor(F32(stream.rng.rnd() * 250))
        bank = F32(F32(stream.rng.rnd() * 10000000) + 100000)
        put(xannoron,77,ground)
        put(xannoron,117,bank)
        putraw(xannoron,125,const[0x7f58])
        put(51+hq,93,100)
    elif dates['xannoron']is not None or xannoron_timer is not None:
        raise ValueError('existing Xannoron must not consume creation clocks')
    # Source2331..2398 always adds ground, including an already existing home.
    put(xannoron,77,get(xannoron,77)+math.floor(F32(stream.rng.rnd()*25)))
    putraw(xannoron,73,const[0x7ea0])
    if get(xannoron,117)==0:put(xannoron,117,1000000)

    top_fallback=stream.one(2993,caller=0x26a8)+7
    normalized=cache(before)
    for g in range(1,21):put(51+g,105,0)
    for sector,zero in normalized['cleared_sectors'].items():
        putraw(51+sector,81,zero);putraw(51+sector,85,zero)
    groups={g:dict(sector=normalized['locations'][g],strength=normalized['forces'][g])for g in range(1,21)}
    remaining=groups[1]['strength'];routes=[];encounters=[];events=[];preferred=0
    for group in range(2,21):
        strength=groups[group]['strength'];origin=groups[group]['sector']
        if strength<1 or origin<1:
            strength=stream.shrinking(remaining,caller=0x31a3);remaining-=strength;origin=hq
        for activity in range(64):
            for _ in range(64):
                fallback=stream.one(3000,caller=0x320a)
                if fallback!=origin:break
            else:raise ValueError('bounded fallback rejection exhausted')
            candidate=stream.one(3000,caller=0x3284)
            if (get(51+candidate,81)>1 and get(51+candidate,85)!=-1)or get(51+candidate,93)>1:
                preferred=candidate
            candidate_scans=0 if preferred else 50
            stream.draws(candidate_scans)
            target=top_fallback if group==20 else(preferred if preferred>7 else fallback)
            route=directed_path(warps,origin,target);entered=[];scans=0
            for sector in route[1:]:
                entered.append(sector)
                if get(51+sector,129)!=0:
                    event=stream.action('mine',mine_hit,world,group,sector,strength)
                    events.append(event);strength=event['force']
                    # 7485..74c2 clears the dead group, not shared pursuit.
                    if not strength:break
                if get(51+sector,81)>0 and get(51+sector,85)not in(0,-1):
                    event=stream.action('defense',defense,world,group,sector,strength)
                    events.append(event);strength=event['force']
                    if event['defenders']==0:preferred=0
                    # Original fatal defense pursues its actual encounter sector
                    # for later groups, as in the recovered occupied caller.
                    if not strength:
                        preferred=sector;break
                link=get(51+sector,93)
                if link>0:
                    slot=int(round(link));record=4051+slot
                    if not 0<=slot<=100:raise ValueError('bounded source planet index required')
                    if get(record,85)!=0 and get(record,73)!=-1:
                        event=ground_assault(world,stream,group,sector,strength)
                        encounters.append(event);events.append(event);strength=event['force']
                        preferred=sector
                        if not strength:break
                stream.draws(50);scans+=50
            final_sector=target if strength else 0
            routes.append(dict(group=group,origin=origin,target=target,fallback=fallback,candidate=candidate,preferred=preferred,candidate_draws=candidate_scans,interception_draws=scans,route=route,entered=entered,strength=strength))
            origin=final_sector
            if not(0<origin<8 and strength>0):break
        else:raise ValueError('bounded protected-sector retry exhausted')
        groups[group]=dict(sector=final_sector,strength=strength)
    groups[1]['strength']=remaining
    # 39d4..3a00 skips directly to3dc0 when BFS has no successor. The
    # group20 mine increment at3d1d..3dbb only executes after actual travel.
    if groups[20]['strength'] and any(r['group']==20 and r['entered']for r in routes):
        endpoint=51+groups[20]['sector'];put(endpoint,129,F32(get(endpoint,129)+1))
    for group,item in groups.items():
        put(51+group,105,item['sector'])
        if item['strength']:
            rec=51+item['sector'];put(rec,81,F32(get(rec,81)+item['strength']));putraw(rec,85,const[0x7ea0])

    taxation=tax_ports(world)
    base=4150;base_links=[s for s in range(1,3001)if get(51+s,93)==99]
    base_attempts=[]
    if not base_links:
        if dates['base']is None:raise ValueError('missing Base requires explicit creation date')
        created.append('base')
        base=4150;title(base,'Mercenary Base');put(base,41,dates['base']-10)
        for off in(45,49,53):putraw(base,off,const[0x8134])
        for off in(57,61,65,69):putraw(base,off,const[0x8742])
        putraw(base,73,const[0x800e]);putraw(base,77,const[0x8746]);putraw(base,117,const[0x874a]);putraw(base,125,const[0x874e])
        base_attempts=[]
        for _ in range(64):
            base_sector=stream.one(3000,caller=0x437a);base_attempts.append(base_sector)
            if get(51+base_sector,93)<=0:break
        else:raise ValueError('bounded Base placement exhausted')
        put(51+base_sector,93,99)
    else:
        if len(base_links)!=1 or dates['base']is not None:raise ValueError('existing Base must not consume creation clock')
        base_sector=base_links[0]
    from replay_maintenance_tax_hiring_mercenary import maintain
    hiring=hire(world,stream,taxation['tax'])
    mercenary=maintain(world,stream)
    lottery=stream.rng.rnd();lottery_player=None
    if lottery>=.5:
        lottery_player=stream.one(50,caller=0x53b4)+1
        if get(lottery_player,85)!=0:raise ValueError('named lottery candidate remains excluded')
    if stream.index!=len(stream.schedule):raise ValueError('unconsumed source helper clocks')
    return bytes(world),dict(groups=groups,routes=routes,encounters=encounters,normalized_total=normalized['total'],
         wanderer_sector=wanderer_sector,wanderer_attempts=wanderer_attempts,base_sector=base_sector,base_attempts=base_attempts,
         taxation=taxation,hiring=hiring,rng_audit=stream.audit(),rng_contexts=tuple(stream.contexts),rng_source=(initial_state,inputs.schedule,tuple((s['family'],s['caller'],s['old_state'],s['timer'],s['seeded_state'])for s in stream.seeds),stream.rng.state,stream.rng.draws),initial_physical_force=initial_physical,final_physical_force=sum(get(51+s,81)for s in range(1,3001)),created=tuple(created),cache_locations=normalized['locations'],cache_forces=normalized['forces'],active_planets=planet_stats,events=events,mercenary=mercenary,lottery=lottery,lottery_player=lottery_player,helper_seeds=stream.seeds,
         helper_calls=stream.calls,total_draws=stream.rng.draws,final_rng_state=stream.rng.state)


def mine_hit(world,stream,group,sector,force):
    """Original72f6..74c2 fatal-mine slice, including bounded FAC-zero residue.

    Every initial mine draws through source7312, even after the group dies. A
    mine is consumed only when a positive effective hit damages positive force.
    Surviving-mine receipts and mixed hazards stay outside this explicit profile.
    """
    if type(world)is not bytearray or len(world)!=4151*137:raise ValueError('complete mutable modeled world required')
    if type(group)is not int or not 2<=group<=20 or type(sector)is not int or not 8<=sector<=3000 or type(force)is not int or not 1<=force<=10000:
        raise ValueError('bounded actual ordinary group and non-Union sector required')
    rec=51+sector;get=lambda off:qb.mbf.get(world,rec,off)
    mines=get(129)
    if mines!=int(mines)or not 1<=mines<=3 or get(81)!=0 or get(93)!=0:
        raise ValueError('only bounded unscreened nonplanet mine encounter recovered')
    initial_mines=int(mines);remaining=force;spent=0;rolls=[];old=stream.rng.state;draws=stream.rng.draws
    for _ in range(initial_mines):
        roll=stream.one(1000,caller=0x7312);rolls.append(roll)
        effective=min(remaining,roll)
        if effective>0 and remaining>0:
            remaining-=effective;mines-=1;spent+=1
    if remaining>0:raise ValueError('surviving mine-route aftermath remains outside this profile')
    at=(rec-1)*137+129
    if mines:
        raw=qb.mbf.enc(mines)
    else:
        # 7372..7390 first evaluates sector+51 as FAC for record I/O. The
        # 7395..73a2 one+minus-one single-add cancellation clears only exponent
        # and retains that previous FAC mantissa (same bounded runtime behavior
        # as the initializer's recovered January1 cancellation). Derive the
        # residue from the computed physical record, never from an after-file.
        raw=bytearray(qb.mbf.enc(rec));raw[3]=0;raw=bytes(raw)
    world[at:at+4]=raw
    return dict(kind='mine',group=group,sector=sector,initial_force=force,force=remaining,
                losses=force-remaining,initial_mines=initial_mines,mines=int(mines),mines_spent=spent,
                rolls=rolls,initial_rng_state=old,final_rng_state=stream.rng.state,rng_draws=stream.rng.draws-draws)


def ground_assault(world,stream,group,sector,force):
    """Original6152..61dd bounded positive-ground fatal planet defense slice."""
    if type(world)is not bytearray or len(world)!=4151*137:raise ValueError('complete mutable modeled world required')
    if type(group)is not int or not 2<=group<=20 or type(sector)is not int or not 8<=sector<=3000 or type(force)is not int or not 1<=force<=10000:
        raise ValueError('bounded actual ordinary group and non-Union planet sector required')
    get=lambda rec,off:qb.mbf.get(world,rec,off)
    slot=get(51+sector,93)
    if slot not in(1,2,99)or get(51+sector,81)!=0 or get(51+sector,129)!=0:
        raise ValueError('only unscreened actual measured planet ground branch recovered')
    rec=4051+int(slot);at=(rec-1)*137
    name,owner={1:(b'The Wanderer',0),2:(b'Route Haven',0),99:(b'Mercenary Base',-2)}[slot]
    ground=get(rec,77)
    if bytes(world[at:at+41])!=name.ljust(41,b' ')or get(rec,85)!=len(name)or get(rec,73)!=owner or ground!=int(ground)or not 1<=ground<=600000:
        raise ValueError('measured named foreign home with positive whole ground required')
    initial_ground=int(ground);ground=int(ground);remaining=force;old=stream.rng.state;draws=stream.rng.draws;rolls=[]
    for _ in range(10000):
        if remaining<=0:break
        if ground<=0:raise ValueError('production/deletion assault remains outside this profile')
        ground-=1;roll=math.floor(F32(stream.rng.rnd()*1000))+1;rolls.append(roll);remaining-=roll
    else:raise ValueError('bounded positive-ground encounter guard')
    if ground<=0:raise ValueError('zero-ground owner/deletion aftermath remains outside this profile')
    world[at+77:at+81]=qb.mbf.enc(ground)
    return dict(kind='planet',group=group,sector=sector,planet_name=name.decode('ascii'),planet_slot=int(slot),
                initial_force=force,raw_force=remaining,force=0,initial_ground=initial_ground,ground=ground,
                ground_spent=initial_ground-ground,rolls=rolls,
                initial_rng_state=old,final_rng_state=stream.rng.state,rng_draws=stream.rng.draws-draws)


def defense(world,stream,group,sector,force):
    """Original7580..788c whole-fighter foreign defense at an actual route hop."""
    get=lambda rec,off:qb.mbf.get(world,rec,off)
    rec=51+sector;defenders=get(rec,81);owner=get(rec,85)
    if type(world)is not bytearray or len(world)!=4151*137 or type(force)is not int or not 1<=force<=10000 or owner!=-2 or defenders!=int(defenders)or not 1<=defenders<=100000:
        raise ValueError('bounded actual Mercenary defense branch required')
    if get(rec,129)!=0 or get(rec,93)!=0:raise ValueError('mixed defense hazards outside profile')
    defenders=int(defenders);x_damage=defender_damage=0;draws=stream.rng.draws;old=stream.rng.state
    for _ in range(200000):
        left=force-x_damage;right=defenders-defender_damage
        if left<=0 or right<=0:break
        batch=5000 if min(left,right)>5000 else 500
        if min(left,right)<500:batch=1
        if stream.rng.rnd()>.5:x_damage+=batch
        else:defender_damage+=batch
    else:raise ValueError('bounded defense round guard')
    surviving=max(0,force-x_damage);remaining=max(0,defenders-defender_damage)
    def put(off,value):
        at=(rec-1)*137+off;world[at:at+4]=qb.mbf.enc(value)
    if remaining==0:put(81,0);put(85,0)
    else:put(81,remaining)
    return dict(kind='defense',group=group,sector=sector,initial_force=force,force=surviving,
                initial_defenders=defenders,defenders=remaining,owner=owner,x_damage=x_damage,defender_damage=defender_damage,
                initial_rng_state=old,final_rng_state=stream.rng.state,rng_draws=stream.rng.draws-draws)
