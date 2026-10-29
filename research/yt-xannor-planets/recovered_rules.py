"""Static-derived helper branches, not a full DOS maintenance/RNG/MBF emulator."""
import math


def ground_battle(force, ground, rng):
    rounds=0
    while ground > 0 and force > 0:
        ground -= 1
        force -= math.floor(rng()*1000)+1
        rounds += 1
    return force,max(0,ground),rounds


def production_batch(rates, location):
    # The original mistakenly reads the group's location row, not its force.
    return 450 if int(location)!=0 and any(x>500 for x in rates) else 1


def production_battle(force, rates, rng, location=101, limit=100000):
    rates=list(rates);rounds=0
    while force > 0 and any(x>0 for x in rates):
        amount=production_batch(rates,location)
        if rng()<.5:
            rates=[x-rng()*amount/3 for x in rates]
        else:
            force-=amount
        rounds+=1
        if rounds>limit:raise RuntimeError('diagnostic model round limit')
    return force,[max(0,x)for x in rates],rounds


def assault(force, ground, rates, stocks, owner, rng, location=101):
    force,ground,g_rounds=ground_battle(force,ground,rng)
    force,rates,p_rounds=production_battle(force,rates,rng,location)
    stocks=[min(stock,10*rate)for stock,rate in zip(stocks,rates)]
    if ground==0:owner=0
    destroyed=all(x==0 for x in rates)
    # The original negative cache is cleared during final group writeback.
    return dict(raw_force=force,force=max(0,force),ground=ground,rates=rates,
                stocks=stocks,owner=owner,destroyed=destroyed,
                message='Xannor fighters destroyed'if force<1 else'Planet destroyed',
                ground_rounds=g_rounds,production_rounds=p_rounds)
