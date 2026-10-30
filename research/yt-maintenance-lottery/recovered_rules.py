"""Executable static model; injected draws are not reconstructed native RNG state."""
from math import floor
from struct import pack, unpack
single=lambda v:unpack("<f",pack("<f",v))[0]


def inactivity(named, last_day, death_marker, cloak, current_day, delay):
    if not named:
        return dict(cloak=cloak, expired=False, delete=False)
    normalized = 1 if cloak < 0 else cloak
    after = max(0, single(single(normalized) - single(.05))) if normalized > 0 else 0
    expired = normalized > 0 and after == 0
    return dict(cloak=after, expired=bool(named and expired),
                delete=bool(named and not expired and last_day <= current_day-delay and death_marker != 0))


def lottery(draw, player_names, planet_names, sector_planets):
    """Standard 50-player/100-planet/3000-sector layout, one draw per stage."""
    if draw() < .5:
        return None
    player = floor(draw()*50)+2
    if not player_names.get(player):
        return None
    planet = floor(draw()*100)+1
    if planet_names.get(planet):
        return None
    sector = floor(draw()*3000)+1
    if sector_planets.get(sector, 0) > 0:
        return None
    rates = [draw()*draw()*3000 for _ in range(3)]
    return dict(player=player, planet=planet, sector=sector, rates=rates,
                ground=floor(draw()*100+1), bank=draw()*1000000)


def check_model():
    for dead in (1, -1):
        assert inactivity(True, 284, dead, 0, 298, 14)['delete']
        assert not inactivity(True, 285, dead, 0, 298, 14)['delete']
    assert not inactivity(True, 1, 0, 0, 298, 14)['delete']
    assert not inactivity(False, 1, 1, 0, 298, 14)['delete']
    for cloak in (.1,-1):
        assert inactivity(False,1,1,cloak,298,14)==dict(cloak=cloak,expired=False,delete=False)
    assert not inactivity(True, 284, 1, .01, 298, 14)['delete']
    assert inactivity(True, 284, 1, .1, 298, 14)['delete']
    assert inactivity(True, 298, 1, 0, 298, 0)['delete']
    assert inactivity(True, 298, 1, -1, 298, 0)['delete']
    # Lazy gates terminate with exactly these model draw counts; no retries.
    for seq,names,planets,sectors,count in [
        ([.499],{}, {}, {},1),([.5,0],{}, {}, {},2),
        ([.5,0,0],{2:'A'},{1:'occupied'}, {},3),
        ([.5,0,0,0],{2:'A'},{},{1:1},4)]:
        used=[]
        def draw():used.append(1);return seq[len(used)-1]
        assert lottery(draw,names,planets,sectors) is None and len(used)==count
    for ref in (0,-1):
        seq=iter([.5,0,0,0]+[.5]*6+[0,.25])
        win=lottery(lambda:next(seq),{2:'A'},{},{1:ref})
        assert win==dict(player=2,planet=1,sector=1,rates=[750]*3,ground=1,bank=250000)
    # Last legal indices and upper ground endpoint; protected/reserved slots
    # are permitted by this legacy local predicate, not a modern safety policy.
    seq=iter([.999999]*12)
    win=lottery(lambda:next(seq),{51:'Z'},{},{})
    assert (win['player'],win['planet'],win['sector'],win['ground'])==(51,100,3000,100)


if __name__=='__main__':
    check_model()
    print('Verified lottery gates, one-shot bounds and inactivity/cloak boundaries.')
