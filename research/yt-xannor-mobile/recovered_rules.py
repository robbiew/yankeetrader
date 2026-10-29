"""Readable static-derived branches, not a DOS RNG/MBF emulator or Go gameplay."""
import math


def allocate(hq, score, rng, stale=0):
    if hq < score / 2000:
        return hq, 0
    amount = stale
    if hq:
        amount = hq
        for _ in range(4):
            amount = math.floor(rng() * amount) + 1
    return hq - amount, amount


def preferred_candidate(fighters, owner, planet, player_cloak=None, roll=0, revenge=False):
    return ((fighters > 1 and owner != -1) or planet > 1 or
            (player_cloak is not None and (roll > player_cloak or revenge)))


def destination(group, fallback, preferred, top_sector, revenge, hq_force, score, hq):
    target = preferred if preferred > 7 else fallback
    if (revenge and group > 15 and top_sector != 0) or group == 20:
        target = top_sector
    if hq_force < score / 2000:
        target = hq
    return target


def hunting(score, cached_cloak, roll):
    # The exact equality is static-derived; DOS controls sample, not pin, RND.
    return score >= 2500000 and cached_cloak - .33 <= roll


def mine_pass(force, mines, rng):
    lost = used = 0
    for _ in range(mines):
        hit = min(force, math.floor(rng() * 1000) + 1)
        if force > 0 and hit > 0:
            force -= hit
            lost += hit
            used += 1
    return force, mines - used, lost


def defense_batch(attackers, defenders):
    if min(attackers, defenders) < 500:
        return 1
    return 5000 if min(attackers, defenders) > 5000 else 500


def defense_battle(attackers, defenders, rng):
    rounds = 0
    while attackers > 0 and defenders > 0:
        batch = defense_batch(attackers, defenders)
        if rng() <= .5:
            defenders -= batch
        else:
            attackers -= batch
        rounds += 1
    return attackers, defenders, rounds
