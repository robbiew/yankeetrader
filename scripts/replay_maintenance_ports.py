"""Bounded original initial-maintenance port record synthesis.

The model reads pre-maintenance records and an independently measured raw
TIMER/60 schedule. It never opens an after-world or uses record patch tables.
This is the ten-day initial-fixture slice, not general port economy/MBF replay.
"""
import math
from replay_qb_ports import graph


def replay_ports(before,day,timer_minutes):
    """Return (137000-byte port block, statistics) for the bounded fixture.

    ``timer_minutes`` must contain1000 raw four-byte MBF FAC observations from
    TIMER/60. Noncanonical numeric-zero mantissas are significant and preserved.
    The caller authenticates the independent clock evidence; this function only
    enforces finite/range/order constraints. No target output is accepted.
    """
    if len(before)!=4151*137:raise ValueError('expected full initial4151record world')
    if type(day)is not int or not 1<=day<=366:raise ValueError('bounded calendar day')
    if len(timer_minutes)!=1000 or any(type(t)is not bytes or len(t)!=4 for t in timer_minutes):
        raise ValueError('exactly1000raw MBF timer observations required')
    numbers=[graph.mbf.dec(t)for t in timer_minutes]
    if any(not math.isfinite(n)or not 0<=n<1440 for n in numbers)or numbers!=sorted(numbers):
        raise ValueError('bounded monotonically observed timer schedule required')
    records=[];classes=[0,0,0]
    for ident in range(1,1001):
        start=(3050+ident)*137
        rec=bytearray(before[start:start+137])
        get=lambda off:graph.mbf.dec(bytes(rec[off:off+4]))
        if get(45)!=day-10 or any(get(o)!=0 for o in (49,53,57,89,97,101)):
            raise ValueError('only clean ten-day initial port fixture is supported')
        rates=[get(o)for o in (61,65,69)]
        if any(x!=int(x)or not 1000<=x<=32766 for x in rates):raise ValueError('initial rate bounds')
        coefficients=[get(o)for o in (73,77,81)]
        if any(x!=int(x)or not 1<=abs(x)<=100 for x in coefficients):raise ValueError('initial coefficient bounds')
        stocks=[int(rate)*10 for rate in rates]
        # Native loop records a new maximum only on strict greater-than.
        selected=max(range(3),key=lambda i:stocks[i])
        trade_class=3-selected
        classes[trade_class-1]+=1
        for offset,value in [(41,trade_class),(45,day)]+list(zip((49,53,57),stocks)):
            rec[offset:offset+4]=graph.mbf.enc(value)
        for i,(offset,value)in enumerate(zip((73,77,81),coefficients)):
            rec[offset:offset+4]=graph.mbf.enc(abs(value)if i==selected else-abs(value))
        rec[101:105]=timer_minutes[ident-1]
        records.append(bytes(rec))
    return b''.join(records),dict(ports=1000,bytes=137000,day=day,elapsed_days=10,class_counts=classes)


def timer_epochs(epochs,count=1000):
    """Expand independently measured 1-based start/raw-FAC epochs, not targets."""
    if not epochs or epochs[0][0]!=1:raise ValueError('first timer epoch muststartatport1')
    starts=[p for p,_ in epochs]
    if starts!=sorted(set(starts))or any(type(p)is not int or not 1<=p<=count for p in starts):
        raise ValueError('unique bounded timer epoch starts')
    out=[]
    for i,(start,raw)in enumerate(epochs):
        value=bytes.fromhex(raw)if isinstance(raw,str)else raw
        if type(value)is not bytes or len(value)!=4:raise ValueError('rawfourbyte timer FAC')
        end=starts[i+1]if i+1<len(starts)else count+1
        out.extend([value]*(end-start))
    return out
