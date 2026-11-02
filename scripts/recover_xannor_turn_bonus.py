"""Capture Xannor direct-fighter turn awards in disposable original DOS worlds."""
import argparse,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('turn_capture',ROOT/'scripts/recover_broadcast_lifetime.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.RECIPE='xannor-turn-bonus-v1'

def cases():
 out=[]
 def add(name,count,turns=100,owner=-1,force=10000,shields=10000,command=None):
  out.append(dict(name=name,command=command or f'A;{force}\r~~~~C;8;T\r~~1',patches=[(2,49,turns),(2,57,100),(2,61,force),(2,53,shields),(2,125,0),(151,81,count),(151,85,owner)],count=count,turns=turns,owner=owner))
 for n in [199,200,399,400]:add('kills-'+str(n),n)
 add('cap-one',1000,499);add('at-cap',1000,500)
 add('mercenary',400,owner=-2);add('player-defense',400,owner=3,command='A;10000\r~~~~N\r~~~~C;8;T\r~~1')
 add('partial-escape',100000,force=1000,shields=100000)
 add('missiles',400,command='!;101;100\r~~~~C;8;T\r~~1')
 out[-1]['patches'] += [(151,81,0),(151,85,0),(152,81,400),(152,85,-1),(2,97,100)]
 add('plasma',400,command='+;101;1\r~~~~C;8;T\r~~1')
 out[-1]['patches'] += [(151,81,0),(151,85,0),(152,81,400),(152,85,-1),(2,113,1)]
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');a=p.parse_args();selected=cases()
 if a.only:selected=[c for c in selected if c['name'] in a.only]
 engine.capture(a.destination.resolve(),selected,4)
