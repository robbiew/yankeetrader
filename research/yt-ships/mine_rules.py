"""Static-derived mine burst model; exact integer scaling, not MBF/DOS RNG replay."""
from fractions import Fraction


def burst(player, count, draws):
    p = dict(player)
    p['Cargo'] = list(p['Cargo'])
    iterator = iter(draws)
    used = 0

    def sample(n):
        nonlocal used
        r = next(iterator)
        assert 0 <= r < 1
        used += 1
        value = Fraction.from_float(r) * n
        return value.numerator // value.denominator

    def nested(n):
        for _ in range(3):
            n = sample(n) + 1
        return n

    if p['Shields'] > 0:
        p['Shields'] = max(0, p['Shields']-sample(1001)*count)
    else:
        if p['Fighters']:
            p['Fighters'] -= min(p['Fighters'], nested(40000*count))
        if p['Cloak']:
            p['Cloak'] = max(0, p['Cloak']-sample(count*100)/100)
        for field in ('Missiles', 'Mines'):
            if p[field]:
                p[field] -= min(p[field], nested(p[field]*count))
        for i in range(3):
            if p['Cargo'][i]:
                p['Cargo'][i] -= min(p['Cargo'][i], nested(p['Cargo'][i]*count))
        empty = p['Holds']-sum(p['Cargo'])
        if empty:
            p['Holds'] -= min(empty, nested(empty)*count)
    return p, used
