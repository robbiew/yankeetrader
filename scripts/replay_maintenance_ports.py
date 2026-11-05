"""Bounded original initial-maintenance port record synthesis.

The model reads pre-maintenance records and an independently measured raw
TIMER/60 schedule. It never opens an after-world or uses record patch tables.
This is the ten-day initial-fixture slice, not general port economy/MBF replay.
"""
import math
from replay_qb_ports import graph


def _replay_ports(before,days,timer_minutes,*,strict_day):
    """Return (137000-byte port block, statistics) for the bounded fixture.

    ``timer_minutes`` must contain1000 raw four-byte MBF FAC observations from
    TIMER/60. Noncanonical numeric-zero mantissas are significant and preserved.
    The caller authenticates the independent clock evidence; this function only
    enforces finite/range/order constraints. No target output is accepted.
    """
    if len(before)!=4151*137:raise ValueError('expected full initial4151record world')
    if len(days)!=1000 or any(type(day)is not int or not 1<=day<=732 for day in days):
        raise ValueError('1000 bounded base-year calendar days required')
    if len(timer_minutes)!=1000 or any(type(t)is not bytes or len(t)!=4 for t in timer_minutes):
        raise ValueError('exactly1000raw MBF timer observations required')
    numbers=[graph.mbf.dec(t)for t in timer_minutes]
    if any(not math.isfinite(n)or not 0<=n<1440 for n in numbers):
        raise ValueError('bounded raw timer schedule required')
    if strict_day:
        if numbers!=sorted(numbers):raise ValueError('bounded monotonically observed timer schedule required')
    else:
        if list(days)!=sorted(days)or max(days)-min(days)>1:
            raise ValueError('matrix port calendar must advance by at most one day')
        drops=[i for i in range(1,len(numbers))if numbers[i]<numbers[i-1]]
        if len(drops)>1 or any(not(numbers[i-1]>1439 and numbers[i]<1)for i in drops):
            raise ValueError('only one midnight timer wrap is admitted')
        # DATE and TIMER are separate source calls: their rollover may straddle
        # one record. Do not rewrite an old date paired with new-day minutes.

    records=[];classes=[0,0,0]
    for ident in range(1,1001):
        start=(3050+ident)*137
        rec=bytearray(before[start:start+137])
        get=lambda off:graph.mbf.dec(bytes(rec[off:off+4]))
        day=days[ident-1]
        eligible=get(45)==day-10 if strict_day else get(45)<=day-10
        if not eligible or any(get(o)!=0 for o in (49,53,57,89,97,101)):
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
    stats=dict(ports=1000,bytes=137000,day=days[0]if len(set(days))==1 else None,elapsed_days=10,class_counts=classes)
    if not strict_day:stats['calendar_days']=list(days)
    return b''.join(records),stats


def replay_ports(before,day,timer_minutes):
    """Historical strict ten-day, single-calendar-day profile, unchanged."""
    if type(day)is not int or not 1<=day<=366:raise ValueError('bounded calendar day')
    return _replay_ports(before,(day,)*1000,timer_minutes,strict_day=True)


def replay_capped_initial_ports(before,days,timer_minutes):
    """Explicit matrix profile: every clean initial port has elapsed at least10days.

    Per-port base-year days are independently observed before TIMER. Clock
    rollback is rejected except one bounded midnight wrap. DATE and TIMER may
    sample opposite sides of that boundary in one record.
    Stocks/classes remain the same exact ten-day capped writer; no rate/event
    or arbitrary populated-port production branch is added.
    """
    return _replay_ports(before,tuple(days),timer_minutes,strict_day=False)


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
