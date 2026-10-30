"""Static rule model; injected draws are not reconstructed native RNG state.

Host single rounding describes ordinary MBF normal values; this is not a complete
bit-exact MBF arithmetic/runtime emulator. Native evidence remains authoritative.
"""
import math,struct
s=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]


def elapsed(last_day,last_minute,now_day,now_minute):
    d=s(s(now_day-last_day)+s(s(now_minute-last_minute)/1440))
    return 10 if d<0 or d>10 else d


def port_growth(stocks,rates,d):
    stocks=[c+s(p*d)for c,p in zip(stocks,rates)]
    return stocks,[max(p,s(c/10))for c,p in zip(stocks,rates)]


def port_event(stocks,rates,draw):
    hit=s(s(rates[0]+rates[1])+rates[2])>1000000
    if not hit:return list(stocks),list(rates),False
    rates=[s(s(draw()*p)+500)if p>500 else p for p in rates]
    return [min(c,s(10*p))for c,p in zip(stocks,rates)],rates,True


def planet_event(stocks,rates,ground,bank,draw):
    total=s(s(rates[0]+rates[1])+rates[2])
    left=s(draw()*total);right=s(s(draw()*1000000)+100000)
    event='plague'if left>right else None
    if s(draw()*ground)>1000000:event='civil'
    if event is None:return dict(event=None,rates=list(rates),stocks=list(stocks),ground=ground,bank=bank,spent=0)
    rates=[s(p*draw())for p in rates]
    if ground>0:ground=s(ground-s(s(ground*draw())*draw()))
    stocks=[min(c,s(10*p))for c,p in zip(stocks,rates)]
    spent=math.floor(s(bank*draw()))if event=='civil'else 0
    return dict(event=event,rates=rates,stocks=stocks,ground=ground,bank=s(bank-spent),spent=spent)


def check_model():
    def sequence(values):
        seq=iter(values);used=[]
        def draw():used.append(1);return next(seq)
        return draw,used
    # Port gate is strict, draw-free, and rates ==500 do not draw.
    for total in (999999,1000000):
        draw,used=sequence([]);_,_,hit=port_event([1]*3,[total-2,1,1],draw);assert not hit and not used
    draw,used=sequence([.5]);_,rates,hit=port_event([1]*3,[499,500,1000001],draw)
    assert hit and len(used)==1 and rates==[499,500,500500.5]
    draw,used=sequence([.5,.5]);_,rates,hit=port_event([1]*3,[500,501,1000001],draw)
    assert hit and len(used)==2 and rates[1]>501,'near-cutoff rate can increase'
    draw,used=sequence([.9]*3);_,rates,hit=port_event([1]*3,[1000000]*3,draw)
    assert hit and sum(rates)>1000000 and len(used)==3,'no repeat-until-cured loop'
    stocks,rates=port_growth([1000001,0,0],[1,1,1],0)
    assert rates[0]==s(100000.1)and sum(rates)<1000000
    # Exact-equality gates use legal draws and do not fire.
    draw,used=sequence([.5,.1,.5]);out=planet_event([1]*3,[100000,100000,200000],2000000,0,draw)
    assert out['event']is None and len(used)==3
    draw,used=sequence([.9,0,.9]+[.5]*6)
    out=planet_event([10000]*3,[1000000]*3,3000000,1000,draw)
    assert out['event']=='civil'and out['rates']==[500000]*3 and out['ground']==2250000 and out['bank']==500 and out['spent']==500 and len(used)==9
    draw,used=sequence([.9,0,0]+[0,0,0])
    out=planet_event([10]*3,[1000000]*3,0,99,draw)
    assert out['event']=='plague'and out['rates']==[0]*3 and out['stocks']==[0]*3 and out['bank']==99 and len(used)==6
    draw,used=sequence([.9,0,0]+[.5]*5)
    out=planet_event([1000000]*3,[1000000]*3,1,99,draw)
    assert out['event']=='plague'and out['ground']==.75 and len(used)==8
    assert elapsed(298,480,298,479.9993591308594)==10
    assert elapsed(298,240,298,240.0001678466797)>0


if __name__=='__main__':
    check_model();print('Verified static gate equality, draw counts, damage, caps and rollback boundaries.')
