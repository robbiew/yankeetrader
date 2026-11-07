"""Explicit jointly measured held-garrison/stock profile, independent of acquisition."""
from fractions import Fraction
from replay_qb_graph import mbf
CASES={
 'friendly-one-empty':(1,0,Fraction(0)),
 'friendly-empty':(37,0,Fraction(0)),
 'friendly-half':(37,0,Fraction(1,2)),
 'friendly-whole':(37,0,Fraction(37)),
 'friendly-odd-half':(37,0,Fraction(3,2)),
 'friendly-large':(37,0,Fraction(379057,2)),
 'friendly-owned-whole':(37,-2,Fraction(37)),
 'friendly-large-force':(97337,0,Fraction(37)),
}


def admit_gateway(world):
    if type(world)not in(bytes,bytearray)or len(world)!=4151*137:raise ValueError('complete default friendly-stock world required')
    get=lambda r,o:mbf.get(world,r,o)
    values=(get(3051,81),get(4054,73),Fraction.from_float(get(4054,129)))
    raw_stock=bytes(world[4053*137+129:4053*137+133])
    if raw_stock!=mbf.enc(float(values[2])):raise ValueError('canonical exact declared source stock required')
    if values not in CASES.values():raise ValueError('only the eight jointly measured friendly-stock contexts admitted')
    if (get(3051,85),get(3051,93),get(3051,129))!=(-2,3,0):raise ValueError('positive friendly linked mine-free gateway required')
    at=4053*137
    if bytes(world[at:at+41])!=b'Gateway Cache'.ljust(41,b' ')or get(4054,85)!=13 or get(4054,117)!=0:
        raise ValueError('actual zero-bank Gateway Cache identity required')
    return int(values[0]),int(values[1]),float(values[2])
