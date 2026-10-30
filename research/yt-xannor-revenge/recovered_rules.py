"""Executable branch documentation, not a BRUN/MBF or maintenance emulator."""

def cloak_after_loading(value):
    if value < 0:
        value = 1
    return max(0, value - .05) if value > 0 else 0


def revenge_setup(pointer, live_positions, cached_positions):
    # Native code only guards pointer>0 before GET; malformed GETs are unknown.
    if pointer <= 0:
        return dict(pointer=pointer, flag=0, preferred=0)
    live = live_positions[pointer]
    return dict(pointer=0, flag=live if live > 7 else 0,
                preferred=cached_positions.get(pointer, 0) if live > 7 else 0)


def top_player(players):
    chosen, score = 0, 0
    for player in sorted(players):
        p = players[player]
        if p['named'] and p['score'] > score:
            chosen, score = player, p['score']
    return chosen, score


def top_target(player, score, live, cached, cloak, sectors, rng):
    target, identity = live, player
    if player:
        detect = rng()  # eager even below score threshold
        if score < 2500000 or detect < cloak - .33:
            target, identity = 0, 0
        elif rng() > .25:
            target = cached
    if not identity or target < 8 or target > sectors:
        target, identity = int(rng() * (sectors - 7)) + 8, 0
    return target, identity


def fallback(current, sectors, rng, diagnostic_limit=10000):
    # Original has no retry cap. The diagnostic cap prevents a model test hang.
    for _ in range(diagnostic_limit):
        target = int(rng() * sectors) + 1
        if target != current:
            return target
    raise RuntimeError('diagnostic limit; original rejection loop is unbounded')


def candidate_search(sectors, sector_data, players, boundary, preferred, revenge, rng):
    attempts = 0
    for _ in range(25 if revenge else 1):
        attempts += 1
        sector = int(rng() * sectors) + 1
        d = sector_data.get(sector, {})
        if (d.get('fighters', 0) > 1 and d.get('owner', 0) != -1) or d.get('planet', 0) > 1:
            preferred = sector
        # Shared state short-circuits scanning even for an unqualified candidate.
        if preferred:
            break
        for player in range(2, boundary + 1):
            p = players.get(player, {})
            roll = rng()  # before position comparison and revenge bypass
            if p.get('sector', 0) == sector and (roll > p.get('cloak', 0) or revenge):
                preferred = sector
                break
        if preferred:
            break
    return preferred, attempts


def destination(group, fallback_sector, preferred, top_sector, revenge, hq_force, score, hq):
    target = preferred if preferred > 7 else fallback_sector
    if (revenge and group > 15 and top_sector != 0) or group == 20:
        target = top_sector
    if hq_force * 2000 < score:
        target = hq
    return target


def intercept(roll, cached_cloak):
    return roll >= cached_cloak - .33
