"""Readable derived Xannor rules, not bit-exact QuickBASIC RNG/MBF emulation."""
import math


def regeneration(top_stored_score, cached_strength):
    return 0 if cached_strength > math.floor(top_stored_score/100) else math.floor(top_stored_score/500)


def creates_xannoron(hq_planet_reference, last_planet=100):
    return hq_planet_reference != last_planet and hq_planet_reference == 0


def attempts_reclaim(owner, defenders):
    return (owner < -1 or owner > 1) and defenders > 0


def relocates(attempted, remaining_hq, regen):
    return (not attempted and remaining_hq == regen) or (attempted and remaining_hq > 0)


def candidate_allowed(fighters, owner, planet_reference):
    return not (fighters > 1 and owner != -1) and not planet_reference > 1


def _draw(rng):
    r=rng()
    if not math.isfinite(r) or not 0 <= r < 1:raise ValueError('RNG must return [0,1)')
    return r


def reclaim_battle(hq, defenders, rng, max_rounds=10000):
    """The analysis step cap is ours; DOS has no such cap in this battle loop."""
    if hq < 0 or defenders < 0:raise ValueError('nonnegative forces required')
    rounds=0
    while hq > 0 and defenders > 0:
        if rounds == max_rounds:raise ValueError('analysis step budget exhausted')
        batch=250 if hq > 250 and defenders > 250 else 1
        if _draw(rng) <= .5:defenders-=batch
        else:hq-=batch
        rounds+=1
    return hq,defenders,rounds


def shrinking_roll(bound, count, rng, previous_result):
    # Faithfully expose the recovered stale-output behavior rather than silently
    # fixing it in the research model. Production code should return zero here.
    if bound == 0 or count == 0:return previous_result
    result=previous_result
    for _ in range(count):
        result=math.floor(_draw(rng)*bound)+1
        bound=result
    return result
