"""Explicit initial collision-fixture NPC replay; historical strict APIs unchanged."""
import math
from replay_maintenance_npcs import constants,directed_path,F32,UnsupportedClockMatrixEncounter
from replay_maintenance_placement import cache
import replay_qb_graph as qb


class Stream:
    """Consume measured TIMERs only at source-derived chronological helper calls."""
    def __init__(self,schedule,state):
        if type(schedule)is not tuple or not 1<=len(schedule)<=256:raise ValueError('bounded typed clock schedule required')
        if type(state)is not int or not 0<=state<2**24:raise ValueError('24bit startup state required')
        if any(type(row)is not tuple or len(row)!=3 or row[0]not in('h1','h2')or type(row[1])is not int or type(row[2])is not bytes or len(row[2])!=4 for row in schedule):
            raise ValueError('typed source-labelled raw helper clocks required')
        self.schedule=schedule;self.index=0;self.rng=qb.QB3(state);self.calls={'h1':0,'h2':0};self.seeds=[]
    def reseed(self,family,caller):
        if self.index>=len(self.schedule):raise ValueError('source helper clock exhaustion')
        actual,site,timer=self.schedule[self.index]
        if actual!=family or site!=caller:raise ValueError(f'computed helper chronology differs: {family}/{caller:04x}, observed {actual}/{site:04x}')
        if type(timer)is not bytes or len(timer)!=4:raise ValueError('raw measured helper TIMER required')
        old=self.rng.state;self.rng.state=(old&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)
        self.index+=1;self.calls[family]+=1
        self.seeds.append(dict(family=family,caller=caller,old_state=old,timer=timer.hex(),seeded_state=self.rng.state))
    def one(self,bound,*,caller):
        if type(bound)is not int or not 1<=bound<=3000:raise ValueError('bounded positive single-range argument required')
        self.reseed('h1',caller);return self.rng.integer(bound)
    def shrinking(self,bound,*,caller):
        if type(bound)is not int or not 1<=bound<=10037:raise ValueError('zero-bound/oversized shrinking argument remains excluded')
        self.reseed('h2',caller)
        for _ in range(4):bound=self.rng.integer(bound)
        return bound
    def draws(self,count):
        for _ in range(count):self.rng.rnd()


def synthesize(before,inputs):
    clock=inputs.clock;initial_state=clock.initial_state;xannoron_timer=clock.xannoron_timer
    matrix_days=inputs.phase_days;day=inputs.final_day
    assert isinstance(before, bytes) and len(before) == 4151 * 137, 'default world extent'
    assert isinstance(xannoron_timer, bytes) and len(xannoron_timer) == 4, 'measured Xannoron TIMER'
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

    assert get(1, 53) == 51 and get(1, 57) == 3051 and get(1, 93) == 4151, 'default record boundaries'
    assert all(get(rec, 85) == 0 for rec in range(2, 52)), 'inactive player fixture only'
    assert all(get(rec, 85) == 0 for rec in range(4052, 4152)), 'inactive planet fixture only'
    assert all(get(rec, 89) == 0 for rec in range(3052, 4052)), 'no tax-funded hiring in selected fixture'
    hq = int(get(1, 117))
    assert 7 < hq <= 3000 and get(52, 105) == hq, 'configured tracked HQ'
    assert get(51 + hq, 85) == -1 and get(51 + hq, 81) == 10000, 'initial Xannor force'
    warps = {s: [get(51 + s, o) for o in range(41, 65, 4)] for s in range(1, 3001)}
    assert all(n == int(n) and 0 <= n <= 3000 for row in warps.values() for n in row), 'bounded original integer warps'
    warps = {s: [int(n) for n in row] for s, row in warps.items()}
    matrix=matrix_days is not None
    dates={'wanderer':day,'xannoron':day,'base':day}if not matrix else matrix_days
    assert set(dates)=={'wanderer','xannoron','base'}and all(type(v)is int and 1<=v<=732 for v in dates.values()), 'bounded phase calendar days'
    stream = Stream(inputs.schedule,initial_state)

    # Main1d9d..1f50 restores only explicit fields in the inherited slot1 record.
    wanderer = 4052
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
    putraw(wanderer, 73, const[0x7f58])

    # Main2169..2398 creates Xannoron in reserved last slot; it is not a clean
    # record constructor, so unassigned bytes remain from the inherited slot.
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
    ground += math.floor(F32(stream.rng.rnd() * 25))
    put(xannoron, 77, ground)
    put(xannoron, 117, bank)
    putraw(xannoron, 125, const[0x7f58])
    put(51 + hq, 93, 100)

    top_fallback=stream.one(2993,caller=0x26a8)+7
    normalized=cache(before)
    for g in range(1,21):put(51+g,105,0)
    for sector,zero in normalized['cleared_sectors'].items():
        putraw(51+sector,81,zero);putraw(51+sector,85,zero)
    groups={g:dict(sector=normalized['locations'][g],strength=normalized['forces'][g])for g in range(1,21)}
    remaining=groups[1]['strength'];routes=[];encounters=[];preferred=0
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
                if get(51+sector,129)!=0:raise ValueError('new Xannor mine encounters remain excluded')
                if get(51+sector,81)>0 and get(51+sector,85)not in(0,-1):raise ValueError('new foreign Xannor defense battle remains excluded')
                link=get(51+sector,93)
                if link>0:
                    slot=int(round(link));record=4051+slot
                    if not 0<=slot<=100:raise ValueError('bounded source planet index required')
                    if get(record,85)!=0 and get(record,73)!=-1:
                        from replay_maintenance_wanderer import assault
                        event=assault(world,stream,group,sector,strength,wanderer_sector)
                        encounters.append(event);strength=event['force'];preferred=sector
                        if not strength:break
                stream.draws(50);scans+=50
            final_sector=target if strength else 0
            routes.append(dict(group=group,origin=origin,target=target,fallback=fallback,candidate=candidate,preferred=preferred,candidate_draws=candidate_scans,interception_draws=scans,route=route,entered=entered,strength=strength))
            origin=final_sector
            if not(0<origin<8 and strength>0):break
        else:raise ValueError('bounded protected-sector retry exhausted')
        groups[group]=dict(sector=final_sector,strength=strength)
    groups[1]['strength']=remaining
    if groups[20]['strength']:
        endpoint=51+groups[20]['sector'];put(endpoint,129,F32(get(endpoint,129)+1))
    for group,item in groups.items():
        put(51+group,105,item['sector'])
        if item['strength']:
            rec=51+item['sector'];put(rec,81,F32(get(rec,81)+item['strength']));putraw(rec,85,const[0x7ea0])

    # Existing Base restoration: no active planet, no taxes in this profile.
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
    from replay_maintenance_collision_mercenary import maintain
    mercenary=maintain(world,stream)
    lottery=stream.rng.rnd();lottery_player=None
    if lottery>=.5:
        lottery_player=stream.one(50,caller=0x53b4)+1
        if get(lottery_player,85)!=0:raise ValueError('named lottery candidate remains excluded')
    if stream.index!=len(stream.schedule):raise ValueError('unconsumed source helper clocks')
    return bytes(world),dict(groups=groups,routes=routes,encounters=encounters,normalized_total=normalized['total'],
         wanderer_sector=wanderer_sector,wanderer_attempts=wanderer_attempts,base_sector=base_sector,base_attempts=base_attempts,
         mercenary=mercenary,lottery=lottery,lottery_player=lottery_player,helper_seeds=stream.seeds,
         helper_calls=stream.calls,total_draws=stream.rng.draws,final_rng_state=stream.rng.state)
