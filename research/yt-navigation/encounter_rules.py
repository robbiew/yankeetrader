"""Readable research models, not Go gameplay or an exact BRUN30/MBF emulator.

RNG is injected so branch/accounting rules can be checked independently of the
original random sequence. See ENCOUNTERS.md for static and DOS evidence bounds.
"""
from math import floor


def disruption_sector(sector_count, random_value):
    """Interpret the independently generated session disruption locations."""
    if sector_count < 2:
        raise ValueError('fixture needs at least two sectors')
    return floor(random_value * (sector_count - 2)) + 2


def scanner_after_mine(installed, unshielded, remaining_shields, random_value):
    """Interpret scanner loss; the first shield-collapse branch bypasses its roll."""
    if not installed or unshielded:
        return False
    return not (remaining_shields > 0 and random_value > .95)


def automatic_mine_escape(remaining_holds, random_value):
    return remaining_holds < 10 and random_value > .8


def sensor_visibility(cached_cloak, random_value):
    """Return (visible, shimmer, next cached cloak); never mutate stored energy."""
    if cached_cloak <= 0:
        return True, False, cached_cloak
    if random_value > cached_cloak:
        return True, True, 0
    return False, False, cached_cloak


def emergency_warp(turns, sector_count, rng):
    """Interpret sub 1f42:9fc4..a400 using mathematical integer parts.

    Floating-point boundary equivalence to QuickBASIC remains unverified.
    The original consumes an additional random draw after choosing a destination;
    its >.95 branch writes a temporary later overwritten by recharge calculation.
    The saved destination has already been copied to a different temporary.
    """
    if turns <= 0 or sector_count <= 0:
        raise ValueError('warp needs positive turns and sector count')
    limit = 70 * (rng() + rng())
    heat = 0
    for _ in range(floor(limit)):
        if rng() > .75:
            heat += 1
        if heat >= 31:
            break
    destination = floor(rng() * sector_count) + 1
    rng()  # Original overwritten temporary branch; preserve draw ordering.
    recharge = min(turns, 4 * heat + floor(4 * rng()))
    meltdown = heat >= 31
    return {'heat': heat, 'destination': destination,
            'cost': turns if meltdown else recharge, 'meltdown': meltdown}
