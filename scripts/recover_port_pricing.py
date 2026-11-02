"""Probe DOS startup reference prices using declared disposable port coefficients."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pricing_capture', ROOT/'scripts/recover_broadcast_lifetime.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.SOURCE = ROOT/'archive/analysis/yt-combat/experiments/fixture-trade-high'
engine.RECIPE = 'startup-reference-pricing-v1'


def cases():
    # Stocks equal ten production days, so docking does not alter S/P=10 even
    # after fractional elapsed production raises P to S/10. Every coefficient
    # probe is explicitly synthetic; -10000 is not a naturally generated port.
    common = [(2,57,100),(2,81,1000000),(2,65,1000),(2,69,0),(2,73,0),(2,77,0),
              (151,65,2),(3053,93,100),(3053,97,0)]
    common += [(3053,offset,value) for offset,value in
               [(45,297),(49,1000),(53,1000),(57,1000),(61,100),(65,100),(69,100)]]
    result=[]
    def add(name, coefficient, at='00:00:00', actor='TESTER'):
        result.append(dict(name=name, command='P;0;0;0', patches=common+[(3053,o,coefficient) for o in (73,77,81)],
                           coefficient=coefficient, time=at, actor=actor))
    add('zero-midnight',0)
    add('normal-midnight',-50)
    add('amplified-midnight',-10000)
    add('amplified-noon',-10000,'12:00:00')
    add('amplified-late',-10000,'23:45:00')
    # Second actor uses the same port and holdings gates, with only identity
    # mapping changed. The engine's baseline enemy is player record3.
    add('amplified-other-actor',-10000,'00:00:00','ENEMY')
    result[-1]['patches'] += [(3,57,100),(3,65,1000),(3,69,0),(3,73,0),(3,77,0),(3,81,1000000)]
    result.append(dict(name='amplified-reload',parent='amplified-midnight',command='\r~~~~P;0;0;0',patches=[],coefficient=-10000,time='00:10:00'))
    return result


def verify(destination, *, require_full=True):
    spec=importlib.util.spec_from_file_location('pricing_verifier',ROOT/'scripts/verify_port_pricing.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    outcomes=checker.verify(destination,require_full=require_full)
    print(json.dumps(outcomes,indent=2))
    return outcomes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    parser.add_argument('--only',nargs='+')
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    selected=cases()
    if args.only:
        if set(args.only)-{c['name'] for c in selected}:parser.error('unknown case')
        selected=[c for c in selected if c['name']in args.only]
    if not args.verify_only:engine.capture(args.destination.resolve(),selected,args.workers)
    outcomes=verify(args.destination.resolve(),require_full=not bool(args.only))
    if not args.verify_only:
        (args.destination/'observed-prices.json').write_text(json.dumps(outcomes,indent=2)+'\n')

if __name__=='__main__':main()
