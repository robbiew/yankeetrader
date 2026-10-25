"""Readable reconstruction of selected YT 3.6 combat operations.

Uses an injected RNG for reproducible research. This is not a bit-exact BRUN30
emulator: MBF32 intermediate rounding and the original RNG are not reproduced.
The DOS evidence verifier is separate; model checks are not DOS runs.
"""
from math import floor


def surrender(attackers, defenders, cloak, rng, accept=True, owner=3):
    lost = killed = 0
    offered = False
    while attackers-lost > 0 and defenders-killed > 0:
        a, d = attackers-lost, defenders-killed
        step = max(1, floor(min(a, d)/20))
        if a/d > 10 and not offered:
            offered = True
            if owner > 1 and accept:
                return dict(lost=lost, killed=killed, joined=d, offered=True)
        if rng() + cloak/10 < 0.45:
            lost += step
        else:
            killed += step
    return dict(lost=lost, killed=killed, joined=0, offered=offered)


def plasma_energy(bolts, hops=1):
    initial = bolts * 2500000
    return max(0, initial-(max(1, hops)-1)*initial/50)


def plasma_absorb(energy, available, kind, rng):
    """Sector/ship fighters, sector mines, or ship shields, in isolation."""
    damage = 0
    while energy > 0 and damage < available:
        if kind == 'fighters': increment = floor(energy/5000)+1
        elif kind == 'shields': increment = floor(energy/10000)+1
        elif kind == 'mines': increment = floor(energy*0.000001)+1
        else: raise ValueError(kind)
        damage += increment
        energy -= rng()*25000
    return min(damage, available), max(energy, 0)


def plasma_planet_unclamped(energy, rng):
    """Damage per production category and before ground-force integer conversion.

Only the positive, sufficiently defended case; not planet destruction, stock
limits, lazy updates, or the ore-only loop condition noted in RECOVERY.md.
"""
    damage = 0
    while energy > 0:
        damage += energy*0.000004
        energy -= rng()*25000
    return damage
