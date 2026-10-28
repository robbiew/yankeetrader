"""Independent modern integer interpretation; not exact DOS RNG/MBF replay."""
from fractions import Fraction


def ship(missiles, fighters, shields, draws):
    index = 0

    def sample(n):
        nonlocal index
        r = draws[index % len(draws)]
        index += 1
        assert 0 <= r < 1
        fraction = Fraction.from_float(r)*n
        return fraction.numerator//fraction.denominator

    killed = damage = 0
    for spent in range(1, missiles+1):
        sample(1)  # Scanner-check RNG; no scanner equipment exists in Go yet.
        killed += sample(4001)
        if sample(fighters) < killed:
            damage += sample(1001)
        if killed >= fighters and damage >= shields:
            break
    return dict(Spent=spent,Fighters=min(killed,fighters),Shields=min(damage,shields))
