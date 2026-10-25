"""Selected direct combat rules. Injected RNG; not bit-exact MBF emulation."""
from math import floor

def fighter_duel(attackers, defenders, cloak, rng):
    lost=killed=0
    while lost<attackers and killed<defenders:
        batch=max(1,floor(min(attackers-lost,defenders-killed)/20))
        if rng()+cloak/10<.45:lost+=batch
        else:killed+=batch
    return attackers-lost,defenders-killed,lost,killed

def shield_duel(fighters,shields,rng):
    while fighters>0 and shields>0:
        batch=100 if fighters>100 and shields>100 else 1
        if rng()>=.5:fighters-=batch
        else:shields-=batch
    return fighters,shields

def retaliation_volley(attacker_stored_score,available,rng):
    if available<1:return 0
    n=floor(attacker_stored_score*.00001)+1 if attacker_stored_score>0 else 0
    if n==0 or n>available:n=floor(rng()*available)+1
    return n

def cloak_tick(cloak,turns_remaining):
    return max(0,cloak-.01) if turns_remaining%25==0 else cloak
