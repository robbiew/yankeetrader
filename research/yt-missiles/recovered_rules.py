"""Selected YT.EXE rules, injected RNG; not a bit-exact MBF/BRUN emulator."""
from math import floor

def sector_fighters(missiles, defenders, rng):
    killed=0;spent=0
    while spent<missiles:
        killed=floor(killed+rng()*5000);spent+=1
        if killed>=defenders:return defenders,spent
    return killed,spent

def ship(missiles,fighters,shields,rng):
    killed=damage=0
    for spent in range(1,missiles+1):
        # Mine-dropping check also consumes RNG in the real game.
        rng()
        killed=floor(killed+rng()*4001)
        if rng()*fighters<killed:damage+=floor(rng()*1001)
        if killed>=fighters and damage>=shields:break
    return min(killed,fighters),min(damage,shields),spent

def planet_ground(missiles,defenders,rng):
    spent=0
    while missiles>spent and defenders>0:
        defenders-=rng()*25;spent+=1
    return max(0,floor(defenders)),spent

def planet_production(missiles,production,rng):
    """Positive, uncapped categories only; no stocks or destruction handling."""
    p=list(production)
    for _ in range(missiles):p=[v-rng()*2000 for v in p]
    return [max(0,v) for v in p]

def assault(attackers,defenders,rng):
    trace=[]
    while attackers>0 and defenders>0:
        if rng()>.4:
            attackers=max(0,floor(attackers-rng()*defenders));trace.append(('A',attackers))
        else:
            defenders=max(0,floor(defenders-rng()*attackers));trace.append(('D',defenders))
    return attackers,defenders,trace
