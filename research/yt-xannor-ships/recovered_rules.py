"""Static-derived whole-unit branches, not a DOS RNG/MBF emulator or Go gameplay."""


def batch(a, b):
    if min(a, b) < 500:
        return 1
    return 5000 if min(a, b) > 5000 else 500


def detected(cached_cloak, roll):
    # Normal route interception. The special group-20 hunt is a different gate.
    return roll > cached_cloak - .33


def battle(group, fighters, shields, rng, limit=100000):
    """Expose computed versus DOS-persisted shields when the victim dies."""
    initial_shields = shields
    group_lost = human_lost = rounds = 0
    while group > 0 and fighters > 0:
        amount = batch(group, fighters)
        if rng() > .5:
            group -= amount; group_lost += amount
        else:
            fighters -= amount; human_lost += amount
        rounds += 1
        if rounds > limit: raise RuntimeError('diagnostic model round limit')
    while group > 0 and shields > 0:
        amount = batch(group, shields)
        if rng() >= .5:
            shields -= amount
        else:
            group -= amount; group_lost += amount
        rounds += 1
        if rounds > limit: raise RuntimeError('diagnostic model round limit')
    killed = fighters < 1 and shields < 1
    return dict(group=group, fighters=fighters, computed_shields=shields,
                stored_shields=shields if shields > 0 else initial_shields,
                group_lost=group_lost, human_lost=human_lost,
                killed=killed, rounds=rounds)
