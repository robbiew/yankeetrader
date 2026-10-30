"""Recovered positive MBF-single reward path, plus explicitly modern policy probes."""
from fractions import Fraction
import math


def single(value):
    """Round a finite nonnegative rational to 24 significant bits, ties to even.

    Only normal positive values used by this corpus are covered; this is not a
    general MBF interpreter or a model of every QuickBASIC arithmetic operation.
    """
    value=Fraction(value)
    assert value>=0
    if not value:return 0.0
    exponent=value.numerator.bit_length()-value.denominator.bit_length()
    power=Fraction(2)**exponent
    if value<power:exponent-=1
    step=Fraction(2)**(exponent-23)
    scaled=value/step;whole,rem=divmod(scaled.numerator,scaled.denominator)
    if 2*rem>scaled.denominator or(2*rem==scaled.denominator and whole%2):whole+=1
    return float(whole*step)


def legacy_reward(balance):
    return single(math.floor(single(Fraction(balance)+1000000)))


def eligible(weapon,initial,remaining,prior_owner,encounter,hq,attempted=True):
    return attempted and initial>0 and remaining==0 and encounter==hq and(weapon=='plasma'or weapon in('fighter','missile')and prior_owner==-1)


def proposed_modern_reward(balance,limit=9000000000000000):
    """Analyst-proposed integer cap; not recovered DOS behavior or Go gameplay."""
    assert 0<=balance<=limit
    amount=min(1000000,limit-balance)
    return balance+amount,amount


def check_model():
    assert legacy_reward(1005)==1001005
    assert legacy_reward(1005.75)==1001005
    assert legacy_reward(2**30)-(2**30)==999936
    assert legacy_reward(2**30+128)-(2**30+128)==1000064
    assert legacy_reward(2**43)-(2**43)==1048576
    assert legacy_reward(2**44)==2**44
    assert eligible('plasma',1,0,-2,101,101)
    assert not eligible('missile',1,0,-2,101,101)
    assert not eligible('fighter',0,0,-1,100,100)
    for b,want in [(0,(1000000,1000000)),(8999999999999999,(9000000000000000,1)),(9000000000000000,(9000000000000000,0))]:
        assert proposed_modern_reward(b)==want
