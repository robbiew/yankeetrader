"""Recovered non-event planet update, checked against unmodified YTMAINT.EXE.

Uses Python arithmetic for clarity; not a bit-exact MBF implementation.
Input/output maps use zero-based offsets in a 137-byte planet record.
NPC actions and plague/civil-war damage occur afterward and are excluded.
"""
import math

def update_planet(before, now_day, now_minute):
    f={int(k):v for k,v in before.items()}
    elapsed=(now_day-f[41])+(now_minute-f[89])/1440
    # Original behavior: clock rollback also awards ten days of catch-up.
    d=10 if elapsed<0 or elapsed>10 else elapsed
    bank=f[117];ground=f[77];p=[f[45],f[49],f[53]];s=sum(p)
    rates=p+[s,math.floor(s/2500),math.floor(s/25000),0,0,math.floor(s/100000)]
    bonuses=[bank/10000,bank/20000,bank/30000,bank/500,bank/100000,bank/250000,0,0,bank/25000000]
    out=dict(f)
    out[117]=math.floor(bank+bank*.01*d)
    out[77]=math.floor(ground+ground*.01*d+(bank/10000)*d)
    for i,offset in enumerate([57,61,65,129,69,125]):out[offset]=f[offset]+(rates[i]+bonuses[i])*d
    out[113]=f[113]+(rates[8]+bonuses[8])*d
    for i,off in enumerate([45,49,53]):
        rate=p[i]
        if out[[57,61,65][i]]>10*rate:rate=out[[57,61,65][i]]/10
        out[off]=max(1,rate*(1+.01*d))
    out[41]=now_day;out[89]=now_minute
    return out,d

def tax(treasury,port_number):
    return 0 if port_number==1 else math.floor(treasury/10)

def xannor_regeneration(top_stored_score,existing_group_strength):
    return 0 if existing_group_strength>math.floor(top_stored_score/100) else math.floor(top_stored_score/500)
