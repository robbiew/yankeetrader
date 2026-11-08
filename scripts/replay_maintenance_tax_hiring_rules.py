"""Bounded original 3f73..40d6 taxation and 4478..464a hiring.

Only modeled before bytes, the computed tax total and chronological TIMER inputs
enter these routines. No native output or acquisition writer is imported.
"""
import math
from replay_qb_graph import mbf,F32


def admit_treasuries(world):
    if type(world)not in(bytes,bytearray)or len(world)!=4151*137:raise ValueError('complete default world required')
    for record in range(3052,4052):
        value=mbf.get(world,record,89)
        if not math.isfinite(value)or value!=int(value)or not 0<=value<=1000 or(record!=3053 and value!=0):
            raise ValueError('only bounded whole port2 treasury admitted')
    if any(mbf.get(world,r,97)!=0 for r in range(3052,4052)):raise ValueError('asking prices remain excluded')


def tax_ports(world):
    if type(world)is not bytearray:raise ValueError('mutable modeled world required')
    admit_treasuries(world);total=0;debits=[]
    for record in range(3053,4052):
        balance=mbf.get(world,record,89)
        if not balance:continue # actual source skips exponent-zero fields
        tax=math.floor(F32(balance/10));remaining=F32(balance-tax)
        mbf.put(world,record,89,remaining);total=F32(total+tax)
        debits.append(dict(record=record,before=int(balance),tax=tax,after=int(remaining)))
    return dict(tax=int(total),debits=debits)


def hire(world,stream,tax):
    if type(world)is not bytearray or len(world)!=4151*137 or type(tax)is not int or not 0<=tax<=100:
        raise ValueError('bounded modeled world and computed whole tax required')
    n=math.floor(F32(tax/10));groups=0 if n<1 else 1 if n<10 else 10;size=n if n<10 else math.floor(F32(n/10))
    placements=[]
    for _ in range(groups):
        attempts=[]
        for _ in range(64):
            sector=stream.one(2999,caller=0x4546)+1;attempts.append(sector)
            if mbf.get(world,51+sector,81)<=0:break
        else:raise ValueError('bounded placement rejection exhausted; no capacity policy invented')
        mbf.put(world,51+sector,85,-2);mbf.put(world,51+sector,81,size)
        placements.append(dict(sector=sector,force=size,attempts=attempts))
    return dict(groups=groups,group_size=size if groups else 0,hired=groups*size,placements=placements)
