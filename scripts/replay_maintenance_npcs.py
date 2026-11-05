"""Research-only NPC record synthesis for the retained initial-maintenance world.

The synthesizer reads a pre-transition world, original executable constants and
measured TIMER inputs. It never reads a post-maintenance target or a target patch
list. Only the inactive-player, empty-planet baseline is admitted; production
maintenance, combat, arbitrary input worlds and general MBF are not implemented.
"""
from collections import deque
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import replay_qb_graph as qb

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
MAINT_SHA = '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
F32 = qb.F32


def constants():
    """Read preserved embedded-DS constants, including their zero residues."""
    raw = (ROOT / 'archive/dos-original/YTMAINT.EXE').read_bytes()
    assert SHA(raw) == MAINT_SHA, 'original maintenance identity'
    # Audited embedded mapping: DS7e60 -> source8e30; no target record is used.
    return {a: raw[a + 0xfd0:a + 0xfd4] for a in
            (0x82ac, 0x82b0, 0x82b4, 0x8386, 0x8134, 0x7f58,
             0x7ea0, 0x800e, 0x8742, 0x8746, 0x874a, 0x874e)}


class UnsupportedClockMatrixEncounter(AssertionError):
    """An unmodeled source branch with context from the modeled prefix only."""
    def __init__(self,message,context):
        super().__init__(message)
        self.context=context


class Stream:
    def __init__(self, h1_timers, h2_timers, state, expected_old_states=None, *, inventory=None):
        self.timers = {'h1': list(h1_timers), 'h2': list(h2_timers)}
        inventory={'h1':41,'h2':19}if inventory is None else inventory
        assert {k:len(v)for k,v in self.timers.items()}==inventory, 'bounded helper-input inventory'
        assert all(isinstance(t, bytes) and len(t) == 4 for ts in self.timers.values() for t in ts), 'raw TIMER inputs'
        self.rng = qb.QB3(state)
        self.calls = {'h1': 0, 'h2': 0}
        self.expected = expected_old_states
        self.seeds = []

    def reseed(self, helper):
        n = self.calls[helper]
        assert n < len(self.timers[helper]), 'helper input exhaustion'
        if self.expected is not None:
            assert self.rng.state == self.expected[helper][n], 'derived old RNG state before helper reseed'
        timer = self.timers[helper][n]
        old = self.rng.state
        self.rng.state = (old & 255) | ((timer[0] ^ timer[2]) << 8) | ((timer[1] ^ timer[3]) << 16)
        self.calls[helper] += 1
        self.seeds.append(dict(helper=helper, ordinal=n + 1, old_state=old,
                               timer_hex=timer.hex(), seeded_state=self.rng.state))

    def integer(self, bound):
        assert type(bound) is int and bound > 0, 'positive bounded integer draw'
        return self.rng.integer(bound)

    def one(self, bound):
        self.reseed('h1')
        return self.integer(bound)

    def shrinking(self, bound):
        self.reseed('h2')
        assert bound > 0, 'zero-bound stale-result defect is outside this fixture'
        for _ in range(4):
            bound = self.integer(bound)
        return bound

    def draws(self, count):
        for _ in range(count):
            self.rng.rnd()


def directed_path(warps, source, target):
    """Original column-order BFS, with a finite research guard."""
    previous = {source: -1}
    queue = deque([source])
    while queue and target not in previous:
        current = queue.popleft()
        for neighbor in warps[current]:
            if neighbor and neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)
    assert target in previous, 'bounded fixture has no directed route'
    route = [target]
    while route[-1] != source:
        route.append(previous[route[-1]])
        assert len(route) <= len(warps), 'research path guard'
    return route[::-1]


def _synthesize(before, h1_timers, h2_timers, day=306, *, xannoron_timer,
                initial_state=0xc805, expected_old_states=None, matrix_days=None):
    """Return world bytes and audit statistics; only NPC-owned fields change.

    ``before`` may already contain the independently synthesized port updates.
    TIMER input ``xannoron_timer`` is the raw value sampled at main2186 before
    division by60 and integer truncation. It is not a saved target timestamp.
    """
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
    assert all(get(51 + s, 81) == (10000 if s == hq else 0) and get(51 + s, 93) == 0
               for s in range(1, 3001)), 'empty initial sector hazards/planet links'
    assert all(get(51 + g, 105) == 0 for g in range(2, 21)), 'missing mobile slots'
    warps = {s: [get(51 + s, o) for o in range(41, 65, 4)] for s in range(1, 3001)}
    assert all(n == int(n) and 0 <= n <= 3000 for row in warps.values() for n in row), 'bounded original integer warps'
    warps = {s: [int(n) for n in row] for s, row in warps.items()}
    matrix=matrix_days is not None
    dates={'wanderer':day,'xannoron':day,'base':day}if not matrix else matrix_days
    assert set(dates)=={'wanderer','xannoron','base'}and all(type(v)is int and 1<=v<=732 for v in dates.values()), 'bounded phase calendar days'
    inventory={'h1':len(h1_timers),'h2':19}if matrix else {'h1':41,'h2':19}
    assert inventory['h1']in(41,42), 'matrix supports only one optional inactive-player lottery selection'
    stream = Stream(h1_timers, h2_timers, initial_state, expected_old_states,inventory=inventory)

    # Main1d9d..1f50 restores only explicit fields in the inherited slot1 record.
    wanderer = 4052
    title(wanderer, 'The Wanderer')
    put(wanderer, 41, dates['wanderer'] - 10)
    for off in (45, 49, 53):
        putraw(wanderer, off, const[0x82ac])
    for off in (57, 61, 65, 69, 77, 125):
        putraw(wanderer, off, const[0x82b0])
    putraw(wanderer, 117, const[0x82b4])
    wanderer_sector = stream.one(3000)
    assert get(51 + wanderer_sector, 93) <= 0, 'this retained fixture has no Wanderer rejection'
    put(51 + wanderer_sector, 93, 1)
    # Main2015..2024 unconditionally replaces the owner with canonical0.
    putraw(wanderer, 73, const[0x7f58])

    # Main2169..2398 creates Xannoron in reserved last slot; it is not a clean
    # record constructor, so unassigned bytes remain from the inherited slot.
    xannoron = 4151
    title(xannoron, 'Xannoron')
    put(xannoron, 41, dates['xannoron'])
    seconds=qb.mbf.dec(xannoron_timer)
    minutes = F32(seconds / 60)
    if matrix:
        assert 0<=seconds<86400 and 0<=minutes<1440, 'bounded daily initial-creation TIMER'
        if minutes>=1:
            truncated=bytearray(qb.mbf.enc(math.floor(minutes)))
        else:
            # Division of a zero FAC preserves its residue; INT zero only
            # clears its exponent. Positive sub-minute values retain theirs.
            truncated=bytearray(xannoron_timer if seconds==0 else qb.mbf.enc(minutes))
            truncated[3]=0
    else:
        assert 0 <= minutes < 1, 'selected sub-minute initial-creation TIMER'
        truncated = bytearray(qb.mbf.enc(minutes))
        truncated[3] = 0  # Historical admitted profile, unchanged.
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

    # There are no named stored scores. Top selection takes its ordinary
    # random8..N fallback, regeneration is0, and no HQ relocation occurs.
    top_fallback = stream.one(2993) + 7
    remaining = int(get(51 + hq, 81))
    putraw(51 + hq, 81, const[0x7f58])
    putraw(51 + hq, 85, const[0x7f58])
    groups = {1: dict(sector=hq, strength=remaining)}
    routes = []
    for group in range(2, 21):
        strength = stream.shrinking(remaining)
        remaining -= strength
        fallback = stream.one(3000)
        assert fallback != hq, 'selected fixture has no same-location fallback retry'
        candidate = stream.one(3000)
        assert get(51 + candidate, 81) <= 1 or get(51 + candidate, 85) == -1, 'no candidate foreign force'
        assert get(51 + candidate, 93) <= 1, 'no accepted candidate planet'
        # All50 cached inactive player positions are0. Every failed comparison
        # still consumes its eager cloak draw at3348.
        stream.draws(50)
        target = top_fallback if group == 20 else fallback
        route = directed_path(warps, hq, target)
        for sector in route[1:]:
            plain=get(51 + sector,93)==0 and get(51 + sector,89)==0
            if matrix and not plain:
                slot=int(get(51+sector,93))
                context=dict(evidence_type='before-only-model-prefix',group=group,sector=sector,
                             planet_slot=slot,sector_owner=get(51+sector,85),
                             sector_aux89=get(51+sector,89),sector_mines=get(51+sector,129),
                             group_strength=strength,rng_state=stream.rng.state,helper_calls=dict(stream.calls))
                if 1<=slot<=100:
                    at=(4050+slot)*137
                    context.update(planet_name=bytes(world[at:at+41]).rstrip(b' ').decode('ascii'),
                                   planet_owner=get(4051+slot,73))
                raise UnsupportedClockMatrixEncounter('no entered planet/mine action in selected fixture',context)
            assert plain, 'no entered planet/mine action in selected fixture'
            # The ordinary group20 interception is excluded, but its per-edge
            # player scans remain eager in this selected fixture. The separate
            # pre-step endpoint bypass is never reached here; the traversal
            # exits after the last entered sector has been scanned.
            stream.draws(50)
        groups[group] = dict(sector=target, strength=strength)
        routes.append(dict(group=group, strength=strength, fallback=fallback,
                           candidate=candidate, sector=target, route=route,
                           candidate_draws=50, interception_draws=50 * (len(route) - 1)))
    groups[1]['strength'] = remaining

    # Group20 increments the ordinary endpoint's field129 at3d6d..3dbb.
    put(51 + groups[20]['sector'], 129, F32(get(51 + groups[20]['sector'], 129) + 1))
    for group, item in groups.items():
        put(51 + group, 105, item['sector'])
        rec = 51 + item['sector']
        put(rec, 81, F32(get(rec, 81) + item['strength']))
        putraw(rec, 85, const[0x7ea0])

    # Main41c1..4473 restores reserved slot99, then chooses one empty planet link.
    base = 4150
    title(base, 'Mercenary Base')
    put(base, 41, dates['base'] - 10)
    for off in (45, 49, 53):
        putraw(base, off, const[0x8134])
    for off in (57, 61, 65, 69):
        putraw(base, off, const[0x8742])
    putraw(base, 73, const[0x800e])
    putraw(base, 77, const[0x8746])
    putraw(base, 117, const[0x874a])
    putraw(base, 125, const[0x874e])
    base_sector = stream.one(3000)
    assert get(51 + base_sector, 93) <= 0, 'selected fixture has no base placement rejection'
    put(51 + base_sector, 93, 99)

    # Treasury0 creates no hired groups. All20 positive Xannor defense sectors
    # consume desertion draws even though their ownership prevents conversion.
    positive_defenses = [s for s in range(1, 3001) if get(51 + s, 81) > 0]
    assert len(positive_defenses) == 20, 'selected fixture has20 nonmerged Xannor groups'
    for sector in positive_defenses:
        assert get(51 + sector, 85) == -1, 'no human desertion target'
        stream.rng.rnd()
    lottery = stream.rng.rnd()
    lottery_player=None
    if matrix and lottery>=.5:
        lottery_player=stream.one(50)+1
        assert get(lottery_player,85)==0, 'matrix lottery selects an inactive player and aborts'
    else:
        assert lottery < .5, 'selected lottery gate ends without a winner'
    assert stream.calls == inventory, 'all measured helper inputs consumed exactly once'
    statistics=dict(wanderer_sector=wanderer_sector, hq_sector=hq,
                             xannoron_ground=ground, xannoron_bank=bank,
                             xannoron_timer_hex=xannoron_timer.hex(),
                             top_fallback=top_fallback, mercenary_base_sector=base_sector,
                             hq_strength=remaining, groups=groups, routes=routes,
                             helper_calls=stream.calls, helper_seeds=stream.seeds,
                             candidate_draws=sum(r['candidate_draws'] for r in routes),
                             interception_draws=sum(r['interception_draws'] for r in routes),
                             desertion_draws=len(positive_defenses), lottery_draw=lottery,
                             total_draws=stream.rng.draws, final_rng_state=stream.rng.state)
    if matrix:statistics.update(calendar_days=dates,lottery_player=lottery_player)
    return bytes(world),statistics


def synthesize(before,h1_timers,h2_timers,day=306,*,xannoron_timer,initial_state=0xc805,expected_old_states=None):
    """Historical strict sub-minute,41/19-helper baseline profile, unchanged."""
    return _synthesize(before,h1_timers,h2_timers,day,xannoron_timer=xannoron_timer,initial_state=initial_state,expected_old_states=expected_old_states)


def synthesize_clock_matrix(before,h1_timers,h2_timers,calendar_days,*,xannoron_timer,initial_state):
    """Explicit clock/date matrix, with one optional inactive lottery draw.

    Calendar days are independently sampled per creation phase, relative to the
    saved base year. Other unmodeled encounter/rejection branches still fail.
    """
    return _synthesize(before,h1_timers,h2_timers,xannoron_timer=xannoron_timer,initial_state=initial_state,matrix_days=dict(calendar_days))


def measured_inputs():
    """Load raw prior probe inputs, not post-maintenance world bytes."""
    path = ROOT / 'research/yt-maint/sequence-controls'
    timers = {}
    old = {}
    for helper, count in [('h1', 41), ('h2', 19)]:
        timers[helper] = [(path / f'baseline--{helper}-timer-{n:03}' / 'TRACE.BIN').read_bytes()[-4:]
                          for n in range(1, count + 1)]
        old[helper] = [int.from_bytes((path / f'baseline--{helper}-old-{n:03}' / 'TRACE.BIN').read_bytes()[-4:], 'little')
                       for n in range(1, count + 1)]
    return timers, old


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before', type=Path, default=ROOT / 'research/yt-maint/initial-controls/baseline-split/before-YTDATA.DAT.gz')
    p.add_argument('--xannoron-timer-hex', required=True, help='raw four-byte2186 TIMER input, not saved time89')
    p.add_argument('--compare', type=Path, help='verification only; never used as a synthesis input')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    raw = a.before.read_bytes()
    before = gzip.decompress(raw) if a.before.suffix == '.gz' else raw
    timers, old = measured_inputs()
    result, stats = synthesize(before, timers['h1'], timers['h2'],
                               xannoron_timer=bytes.fromhex(a.xannoron_timer_hex), expected_old_states=old)
    if a.output:
        a.output.write_bytes(result)
    if a.compare:
        raw = a.compare.read_bytes()
        observed = gzip.decompress(raw) if a.compare.suffix == '.gz' else raw
        report = {}
        for name, start, end in [('sectors', 51, 3051), ('planets', 4051, 4151)]:
            left, right = observed[start * 137:end * 137], result[start * 137:end * 137]
            diffs = [(i, x, y) for i, (x, y) in enumerate(zip(left, right)) if x != y]
            report[name] = dict(compared_bytes=len(left), byte_mismatches=len(diffs),
                                observed_sha256=SHA(left), replayed_sha256=SHA(right),
                                first_differences=[dict(record=start + i // 137 + 1, offset=i % 137,
                                                        observed=x, replayed=y) for i, x, y in diffs[:20]])
        stats['comparison'] = report
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()
