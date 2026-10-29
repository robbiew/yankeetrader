"""Readable derived rules; illustrative [0,1) RNG, not bit-exact QuickBASIC."""
import math

def hire_plan(tax):
    if not isinstance(tax,int) or tax<0:raise ValueError('nonnegative integer tax required')
    budget=tax//10
    if budget<1:return ()
    if budget<10:return (budget,)
    return (budget//10,)*10

def draw(rng):
    r=rng()
    if not math.isfinite(r) or not 0<=r<1:raise ValueError('RNG must return [0,1)')
    return r

def mine_loss(force,mines,rng):
    if force<0 or mines<0:raise ValueError('nonnegative force/field required')
    lost=spent=0
    while force>0 and spent<mines:
        bound=10000
        for _ in range(2):bound=math.floor(draw(rng)*bound)+1
        damage=min(force,bound)
        force-=damage;lost+=damage;spent+=1
    return force,lost,spent

def defense_battle(mercenaries,defenders,rng):
    if mercenaries<0 or defenders<0:raise ValueError('nonnegative forces required')
    rounds=0
    while mercenaries>0 and defenders>0:
        batch=150 if mercenaries>200 and defenders>200 else 1
        if draw(rng)<.5:defenders-=batch
        else:mercenaries-=batch
        rounds+=1
    return mercenaries,defenders,rounds
