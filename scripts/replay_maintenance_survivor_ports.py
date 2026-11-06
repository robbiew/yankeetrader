"""Before-only port writer for the bounded November5/6 survivor children.

The two-child survivor schedules are explicit research scope.
No target, source-clock capture or after-record is opened by this module.
"""
import math
from replay_qb_graph import mbf, F32


def replay_ports(before,days,timer_minutes):
    """Return the complete port block from before bytes and source clocks only."""
    if type(before)is not bytes or len(before)!=4151*137:
        raise ValueError('complete immutable default before-world required')
    if type(days)is not tuple or len(days)!=1000 or any(type(d)is not int or d not in(309,310)for d in days)or len(set(days))!=1:
        raise ValueError('complete single-day evolved-clock port calendars required')
    if type(timer_minutes)is not tuple or len(timer_minutes)!=1000 or any(type(t)is not bytes or len(t)!=4 for t in timer_minutes):
        raise ValueError('1000 immutable raw source port TIMER minutes required')
    minutes=[mbf.dec(t)for t in timer_minutes]
    if any(not math.isfinite(v)or not(0<=v<1)for v in minutes)or minutes!=sorted(minutes):
        raise ValueError('bounded measured midnight source port clocks required')
    getworld=lambda r,o:mbf.get(before,r,o)
    if any(getworld(1,o)!=v for o,v in((53,51),(57,3051),(61,4051),(93,4151))):
        raise ValueError('default port record geometry required')
    records=[];classes=[0,0,0];elapsed_values=[];promotions=0
    for ident in range(1,1001):
        start=(3050+ident)*137;record=bytearray(before[start:start+137])
        get=lambda off:mbf.dec(bytes(record[off:off+4]))
        day=days[ident-1];last=get(45);last_minute=get(101)
        if (last,day)not in((308,309),(309,310))or not math.isfinite(last_minute)or not(0<=last_minute<1):
            raise ValueError('only measured evolved-clock date handoffs recovered')
        if any(get(off)!=0 for off in(89,97)):
            raise ValueError('nonzero treasury/asking-price branch outside convergence profile')
        rates=[get(o)for o in(61,65,69)];stocks=[get(o)for o in(49,53,57)];coeff=[get(o)for o in(73,77,81)]
        if any(not math.isfinite(v)or not 1000<=v<=70000 for v in rates):raise ValueError('bounded retained cargo rates required')
        if any(v!=int(v)or not 1<=abs(v)<=100 for v in coeff):raise ValueError('bounded original coefficient magnitudes required')
        if any(not math.isfinite(c)or abs(c-10*p)>max(1,c)*2**-22 for c,p in zip(stocks,rates)):
            raise ValueError('only measured full-stock evolved port inputs recovered')
        elapsed=F32(F32(day-last)+F32(F32(minutes[ident-1]-last_minute)/1440))
        if elapsed<0 or elapsed>10:elapsed=10
        if not .999<=elapsed<=1.001:raise ValueError('bounded measured one-day elapsed interval required')
        # 09ae..09ed keeps the cargo sum in the wider array. The rate*elapsed
        # product is single; stock conversion occurs only in the record writer.
        stocks=[c+F32(p*elapsed)for c,p in zip(stocks,rates)]
        for i,(c,p)in enumerate(zip(stocks,rates)):
            if c>10*p:
                rates[i]=F32(c/10);promotions+=1
        # The measured small-rate port gate is draw-free; no RNG is supplied.
        if F32(F32(rates[0]+rates[1])+rates[2])>1000000:
            raise ValueError('selected port plague remains outside this profile')
        maximum=0;selected=None
        for i,c in enumerate(stocks):
            if c>maximum:maximum=F32(c);selected=i
        if selected is None:raise ValueError('positive cargo maximum required')
        trade_class=3-selected;classes[trade_class-1]+=1
        for off,value in[(41,trade_class),(45,day),*zip((49,53,57),stocks),*zip((61,65,69),rates)]:
            record[off:off+4]=mbf.enc(value)
        for i,(off,value)in enumerate(zip((73,77,81),coeff)):
            record[off:off+4]=mbf.enc(abs(value)if i==selected else-abs(value))
        record[101:105]=timer_minutes[ident-1]
        records.append(bytes(record));elapsed_values.append(elapsed)
    return b''.join(records),dict(ports=1000,bytes=137000,day=days[0],class_counts=classes,
                                  rate_promotions=promotions,elapsed_min=min(elapsed_values),elapsed_max=max(elapsed_values),rng_draws=0)
