"""Readable production phase, injected draws; not bit-exact DOS MBF/RNG replay."""

def bombard(missiles, production, stocks, rng):
    rates=list(production)
    # 1a48 is ore production cached by the lazy updater. Unlike the other two
    # terms, the loop does not read its changing value from the damage array.
    ore_at_entry=rates[0]
    spent=0
    while spent<missiles and (ore_at_entry>0 or rates[1]>0 or rates[2]>0):
        rates=[rate-rng()*2000 for rate in rates]
        spent+=1
    rates=[max(0,rate) for rate in rates]
    cargo=[min(stock,10*rate) for stock,rate in zip(stocks,rates)]
    return dict(production=rates,stocks=cargo,spent=spent,destroyed=all(rate==0 for rate in rates))
