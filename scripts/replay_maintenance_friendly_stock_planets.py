"""Before-only planet economy for the eight measured friendly-force/stock fixtures.

The profile admits three named home records and the exact neutral Gateway Cache,
bounded stocks and banks, and explicit midnight clock/calendar handoffs.
It preserves inherited reserved-slot bytes and rejects selected event damage.
No expected output, captured state or general MBF implementation is used.
"""
import math
from fractions import Fraction

from replay_qb_graph import mbf, F32


RECORDS = 4151
SIZE = 137
ACTIVE_SLOTS = (4052, 4054, 4150, 4151)
STOCKS = frozenset((Fraction(0),Fraction(1,2),Fraction(37),Fraction(3,2),Fraction(379057,2)))


def _admit(world, planet_clocks):
    if type(world) is not bytearray or len(world) != RECORDS * SIZE:
        raise ValueError('complete mutable default world required')
    if type(planet_clocks) is not tuple:
        raise ValueError('immutable explicit planet clocks required')
    from replay_maintenance_friendly_stock_rules import admit_gateway
    _,governor,_=admit_gateway(world)
    get = lambda record, offset: mbf.get(world, record, offset)
    if any(get(1, offset) != expected for offset, expected in
           ((53, 51), (57, 3051), (61, 4051), (93, 4151))):
        raise ValueError('default planet record geometry required')
    active = tuple(record for record in range(4052, 4152) if get(record, 85) != 0)
    before_day=get(1,81)
    if not planet_clocks:raise ValueError('explicit active-planet clocks required')
    first=planet_clocks[0]
    if type(first)is not tuple or len(first)!=3 or type(first[1])is not int:raise ValueError('typed first source clock row required')
    expected_day=first[1]
    if (before_day,expected_day)!=(308,309):
        raise ValueError('only the measured November4-to5 stock handoff is admitted')
    expected_active=ACTIVE_SLOTS
    if active != expected_active:
        raise ValueError('only measured gateway planet slots 1/3/99/100 are recovered')
    if len(planet_clocks) != len(active):
        raise ValueError('one explicit date/timer pair per active planet required')
    for record, row in zip(active, planet_clocks):
        if (type(row) is not tuple or len(row) != 3 or type(row[0]) is not int or
                type(row[1]) is not int or type(row[2]) is not bytes or len(row[2]) != 4):
            raise ValueError('typed immutable source planet clock row required')
        clock_record, day, minute_raw = row
        minute = mbf.dec(minute_raw)
        if (clock_record != record or day != expected_day or not math.isfinite(minute) or
                not 0<=minute<1):
            raise ValueError('ordered measured midnight planet clocks required')
        at = (record - 1) * SIZE
        length = get(record, 85)
        if (length != int(length) or not 1 <= length <= 41 or
                world[at:at + 41] != bytes(world[at:at + int(length)]).ljust(41, b' ') or
                any(not 32 <= b <= 126 for b in world[at:at + int(length)])):
            raise ValueError('active ASCII planet name required')
        expected_names={4052:b'The Wanderer',4054:b'Gateway Cache',4150:b'Mercenary Base',4151:b'Xannoron'}
        expected_owners={4052:0,4054:governor,4150:-2,4151:-1}
        if bytes(world[at:at+41])!=expected_names[record].ljust(41,b' ')or get(record,73)!=expected_owners[record]:
            raise ValueError('measured named home/ordinary ownership required')
        expected_last=before_day
        prior_minute=get(record,89)
        if (get(record,41)!=expected_last or not math.isfinite(prior_minute) or
                not 0<=prior_minute<1 or get(record,73)not in(-2,-1,0) or
                not 0<=get(record,77)<=600000 or not 0<=get(record,117)<=30000000 or
                any(not (0 if record==4054 else 1)<=get(record,offset)<=200000 for offset in(45,49,53))):
            raise ValueError('measured bounded evolved planet required')
        if any(not math.isfinite(get(record,o))or get(record,o)<0 or get(record,o)>10000000 for o in(57,61,65,69,113,125,129)):
            raise ValueError('bounded nonnegative resource stocks required')
        inherited={81:305,93:4151,97:0,101:5,105:300,109:0,121:1000,133:0}if record in(4052,4150,4151)else{offset:0 for offset in(81,93,97,101,105,109,121,133)}
        if any(get(record,o)!=value for o,value in inherited.items()):raise ValueError('unmodeled inherited planet field context')
        slot = record - 4051
        links = [sector for sector in range(1, 3001) if get(51 + sector, 93) == slot]
        if len(links) != 1:
            raise ValueError('each ordinary active planet requires one physical sector link')
        if record==4054:
            if links!=[3000] or get(record,117)!=0 or get(record,77)!=500000:
                raise ValueError('measured gateway link, empty bank and inherited ground required')
            expected_rate=0
            if any(get(record,o)!=expected_rate for o in(45,49,53)):
                raise ValueError('measured zero-initial or clamped gateway rates required')
            if Fraction.from_float(get(record,129))not in STOCKS:
                raise ValueError('exact jointly measured friendly stock required')
            if any(get(record,o)!=0 for o in(57,61,65,69,113,125)):
                raise ValueError('gateway starts with no cargo or weapons before each measured day')
    return active


def maintain(world, stream, planet_clocks):
    """Mutate independently modeled bytes and return derived source statistics.

    Rows are ``(physical_record, base_year_day, raw_TIMER_div_60_single)``. They
    contain no observed record, old RNG state or expected result. Caller supplies
    source-qualified clock observations in the same ascending active-record order
    used by the native planet loop. Unknown contexts fail before any mutation.
    """
    active = _admit(world, planet_clocks)
    if not hasattr(stream, 'rng') or not callable(getattr(stream.rng, 'rnd', None)):
        raise ValueError('explicit modeled RNG stream required')
    work = bytearray(world)
    get = lambda record, offset: mbf.get(work, record, offset)
    put = lambda record, offset, value: mbf.put(work, record, offset, value)
    rows = []
    old_state = stream.rng.state
    initial_draws = stream.rng.draws
    for record, day, minute_raw in planet_clocks:
        minutes = mbf.dec(minute_raw)
        # Main124b..12ac: TIMER/60 is saved to7b1c, then the entire elapsed
        # expression is assigned back to the single1858 cell. No whole-minute
        # truncation and no synchronization with the separate DATE call occurs.
        elapsed = F32(F32(day - get(record, 41)) +
                      F32(F32(minutes - get(record, 89)) / 1440))
        if elapsed<0 or elapsed>10:elapsed=10.0
        if not .999<=elapsed<=1.001:raise ValueError('bounded measured fractional/capped elapsed required')
        rates = [get(record, offset) for offset in (45, 49, 53)]
        total_rate = F32(F32(rates[0] + rates[1]) + rates[2])
        # Main104e..1246 constructs single rate arrays. INT truncates the
        # total fighter base as well as weapon bases before elapsed time.
        resource_rates = rates + [math.floor(total_rate), math.floor(total_rate / 2500),
                                  math.floor(total_rate / 25000)]
        stock_offsets = (57, 61, 65, 129, 69, 125)
        # Main13cc..1454 evaluates interest/ground expressions before the
        # single INT argument is rounded, then floors. Applying Python floor
        # to an unrounded .01-single product would incorrectly subtract one.
        old_bank = get(record, 117)
        old_ground = get(record, 77)
        put(record, 117, math.floor(F32(old_bank + old_bank * elapsed * F32(.01))))
        put(record, 77, math.floor(F32(old_ground + old_ground * elapsed * F32(.01) + F32(old_bank/10000)*elapsed)))
        # Main12e4..13c7 stores bank bonuses into single arrays before
        # Main1464..1571 stock assignments. Source TIMER bytes remain raw.
        bonuses=[F32(old_bank/10000),F32(old_bank/20000),F32(old_bank/30000),F32(old_bank/500),F32(old_bank*F32(.00001)),F32(old_bank*F32(.000004))]
        for offset,rate,bonus in zip(stock_offsets,resource_rates,bonuses):
            put(record,offset,F32(get(record,offset)+F32(F32(rate+bonus)*elapsed)))
        put(record, 113, F32(get(record, 113) +
                             F32(F32(math.floor(total_rate / 100000)+F32(old_bank/25000000)) * elapsed)))
        for offset, rate, stock_offset in zip((45, 49, 53), rates, (57, 61, 65)):
            if get(record,stock_offset)>F32(10*rate):rate=F32(get(record,stock_offset)/10)
            # Main1582..15bf rounds on array assignment, not by adding an
            # arbitrary after-target adjustment to the growth result.
            put(record, offset, F32(rate + F32(F32(rate * elapsed) * F32(.01))))
        # Main15e2..1649 clamps each rate below one only after first-day
        # stock production and rate growth. Do not grant day-one fighters.
        for offset in(45,49,53):
            if get(record,offset)<1:put(record,offset,1)
        # The three eager event draws occur even in these safe low-production
        # worlds. Evaluate their actual predicates instead of merely skipping
        # them because all retained outcomes happen to have no random event.
        production = F32(F32(get(record, 45) + get(record, 49)) + get(record, 53))
        first, second, third = (stream.rng.rnd() for _ in range(3))
        plague = F32(first * production) > F32(F32(second * 1000000) + 100000)
        civil = F32(third * get(record, 77)) > 1000000
        if plague or civil:
            raise ValueError('selected plague/civil-war damage remains outside this profile')
        # Main1b42..1ca4 writes the previously sampled date and TIMER minutes.
        put(record, 41, day)
        at = (record - 1) * SIZE + 89
        work[at:at + 4] = minute_raw
        rows.append(dict(record=record, day=day, timer_minutes=minute_raw.hex(),
                         elapsed=elapsed, event_draws=[first, second, third],
                         event_selected=False, ground=int(get(record, 77)),
                         cargo_rates=[get(record, offset) for offset in (45, 49, 53)]))
    world[:] = work
    return dict(planets=len(active), rows=rows, initial_rng_state=old_state,
                final_rng_state=stream.rng.state,
                rng_draws=stream.rng.draws - initial_draws)
