"""Before-only ordinary planet economy for the ten retained active-world fixtures.

Only the clean, prior-day, zero-bank ordinary-slot contexts are admitted. Every
written numeric field follows the original single-array writer; this is not a
general MBF, event, inhabited-world or planet-maintenance implementation.
"""
import math

from replay_qb_graph import mbf, F32


RECORDS = 4151
SIZE = 137
ACTIVE_SLOTS = (4053, 4054)


def _admit(world, planet_clocks):
    if type(world) is not bytearray or len(world) != RECORDS * SIZE:
        raise ValueError('complete mutable default world required')
    if type(planet_clocks) is not tuple:
        raise ValueError('immutable explicit planet clocks required')
    get = lambda record, offset: mbf.get(world, record, offset)
    if any(get(1, offset) != expected for offset, expected in
           ((53, 51), (57, 3051), (61, 4051), (93, 4151))):
        raise ValueError('default planet record geometry required')
    active = tuple(record for record in range(4052, 4152) if get(record, 85) != 0)
    if not set(active) <= set(ACTIVE_SLOTS) or len(active) > 2:
        raise ValueError('only measured ordinary active slots 2 and 3 are recovered')
    if len(planet_clocks) != len(active):
        raise ValueError('one explicit date/timer pair per active planet required')
    for record, row in zip(active, planet_clocks):
        if (type(row) is not tuple or len(row) != 3 or type(row[0]) is not int or
                type(row[1]) is not int or type(row[2]) is not bytes or len(row[2]) != 4):
            raise ValueError('typed immutable source planet clock row required')
        clock_record, day, minute_raw = row
        minute = mbf.dec(minute_raw)
        if (clock_record != record or day != 306 or not math.isfinite(minute) or
                not 0 <= minute < 1):
            raise ValueError('ordered measured day306 midnight planet clocks required')
        at = (record - 1) * SIZE
        length = get(record, 85)
        if (length != int(length) or not 1 <= length <= 41 or
                world[at:at + 41] != bytes(world[at:at + int(length)]).ljust(41, b' ') or
                any(not 32 <= b <= 126 for b in world[at:at + int(length)])):
            raise ValueError('ordinary active ASCII planet name required')
        if (get(record, 41) != 305 or get(record, 73) not in (-1, 0) or
                get(record, 77) != 500000 or
                any(get(record, offset) != 1000 for offset in (45, 49, 53))):
            raise ValueError('only clean prior-day 1000-rate 500000-ground planets are recovered')
        if any(get(record, offset) != 0 for offset in range(41, 137, 4)
               if offset not in (41, 45, 49, 53, 73, 77, 85)):
            raise ValueError('only empty zero-bank, zero-stock planet context is recovered')
        slot = record - 4051
        links = [sector for sector in range(1, 3001) if get(51 + sector, 93) == slot]
        if len(links) != 1:
            raise ValueError('each ordinary active planet requires one physical sector link')
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
        if not 1 <= elapsed < 1.001:
            raise ValueError('only measured one-day fractional elapsed update is recovered')
        rates = [get(record, offset) for offset in (45, 49, 53)]
        total_rate = F32(F32(rates[0] + rates[1]) + rates[2])
        # Main104e..1246 constructs rate arrays; bank bonuses vanish for this
        # admitted zero-bank input. Weapon rates are truncated before elapsed.
        resource_rates = rates + [total_rate, math.floor(total_rate / 2500),
                                  math.floor(total_rate / 25000)]
        stock_offsets = (57, 61, 65, 129, 69, 125)
        # Main13cc..1454 floors interest and ground only after its full wider
        # expression. For these whole/zero inputs the admitted integer values
        # are far from a rounding boundary.
        old_bank = get(record, 117)
        old_ground = get(record, 77)
        put(record, 117, math.floor(old_bank + old_bank * elapsed * F32(.01)))
        put(record, 77, math.floor(old_ground + old_ground * elapsed * F32(.01)))
        # Main1464..1571 single-array assignments; zero stock arithmetic yields
        # canonical zero here, whereas source raw TIMER zero is copied intact.
        for offset, rate in zip(stock_offsets, resource_rates):
            put(record, offset, F32(get(record, offset) + F32(rate * elapsed)))
        put(record, 113, F32(get(record, 113) +
                             F32(math.floor(total_rate / 100000) * elapsed)))
        for offset, rate, stock_offset in zip((45, 49, 53), rates, (57, 61, 65)):
            if get(record, stock_offset) > F32(10 * rate):
                raise ValueError('surplus rate replacement is outside the admitted context')
            # Main1582..15bf rounds on array assignment, not by adding an
            # arbitrary after-target adjustment to the growth result.
            put(record, offset, F32(rate + F32(F32(rate * elapsed) * F32(.01))))
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
