"""Recovered salvage shape with injected RNG; not DOS RNG or MBF emulation."""
from math import floor, isfinite


def salvage(holds, credits, missiles, plasma, ground, mines, cargo,
            winner_holds, rng, maximum_holds=1000):
    """Sample new holds, money and weapons, then cargo without replacement.

    This research model uses exact Python integers after floor. DOS's MBF32
    rounding, combat RNG consumption, mine aftermath and estate work are separate.
    """
    values = [holds, credits, missiles, plasma, ground, mines, winner_holds, maximum_holds, *cargo]
    if len(cargo) != 3 or any(not isinstance(v, int) or v < 0 for v in values):
        raise ValueError('nonnegative integer inventories required')
    if sum(cargo) > holds or winner_holds > maximum_holds:
        raise ValueError('cargo/holds exceed capacity')

    def draw():
        value = rng()
        if not isfinite(value) or not 0 <= value < 1:
            raise ValueError('RNG must return [0,1)')
        return value

    # The original samples all six values in this order, even for zero stocks.
    sampled = [floor(draw()*quantity) for quantity in (holds, credits, missiles, plasma, ground, mines)]
    recovered_holds = min(sampled[0], maximum_holds-winner_holds)
    remaining_holds = holds
    remaining = list(cargo)
    recovered_cargo = [0, 0, 0]
    for _ in range(recovered_holds):
        index = floor(draw()*remaining_holds)
        boundary = 0
        for good in range(3):
            boundary += remaining[good]
            if index < boundary:
                remaining[good] -= 1
                recovered_cargo[good] += 1
                break
        remaining_holds -= 1
    return dict(holds=recovered_holds, credits=sampled[1], missiles=sampled[2],
                plasma=sampled[3], ground=sampled[4], mines=sampled[5], cargo=recovered_cargo)
