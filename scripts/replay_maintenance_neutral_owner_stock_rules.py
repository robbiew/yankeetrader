"""Six explicitly measured owner/mine/stock contexts; no capture/model imports."""
from fractions import Fraction
from replay_qb_graph import mbf
CASES={'neutral-one-empty':(1,0,Fraction(0)), 'neutral-whole':(37,0,Fraction(37)),
       'neutral-half':(37,0,Fraction(1,2)), 'neutral-mine-whole':(37,0,Fraction(37)),
       'friendly-mine-second-two':(37,0,Fraction(37)), 'friendly-mine-second-four':(37,0,Fraction(37))}
OWNERS={name:(-2 if name.startswith('friendly-')else 0) for name in CASES}
MINES={name:int('mine' in name) for name in CASES}
SECONDS={name:(4 if name.endswith('-four')else 2)for name in CASES}

def admit_gateway(world):
    if type(world)not in(bytes,bytearray)or len(world)!=4151*137:raise ValueError('complete default immutable/mutable world required')
    get=lambda r,o:mbf.get(world,r,o)
    context=(get(3051,81),get(3051,85),Fraction.from_float(get(4054,129)),get(3051,129))
    allowed={(v[0],OWNERS[c],v[2],MINES[c])for c,v in CASES.items()}
    if context not in allowed or get(3051,93)!=3:raise ValueError('one of six declared linked owner/mine/stock contexts required')
    at=4053*137
    if bytes(world[at:at+41])!=b'Gateway Cache'.ljust(41,b' ')or get(4054,85)!=13 or get(4054,73)!=0 or get(4054,117)!=0:
        raise ValueError('neutral zero-bank Gateway Cache required')
    if bytes(world[at+129:at+133])!=mbf.enc(float(context[2])):raise ValueError('canonical declared input stock required')
    return int(context[0]),0,float(context[2])
