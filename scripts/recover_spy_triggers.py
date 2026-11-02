"""Recover spy command triggers and notification chains in copied DOS worlds."""
import argparse
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('radio_capture', ROOT/'scripts/recover_broadcast_lifetime.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.RECIPE = 'spy-triggers-v1'
engine.GRAPH = {1:[100,2],2:[3],3:[2],100:[1,101],101:[102],102:[103],103:[101],200:[201],201:[200]}
ROOT_PATCHES = [(2,81,2000000),(2,61,1000),(2,53,10000),(3,57,200),(3,125,1),(152,129,7),(153,93,0),(152,65,0)]
HIRE = 'P;9;1;101\r~~~~\r~~0;'
LIST = 'C;15;1'


def cases():
    result=[]
    def root(name, action, patches=(), prefix=None):
        result.append(dict(name=name,command=(HIRE+LIST+';' if prefix is None else prefix)+action+';'+LIST,patches=ROOT_PATCHES+list(patches)))
    root('list-only',LIST)
    root('ship-info','I')
    root('sensors','S')
    root('help','?')
    root('port-report','C;2;1;1')
    root('planet-report-foreign','C;9;101;1',[(152,93,2),(4053,73,3),(4053,77,12)])
    root('planet-report-own','C;9;101;1',[(152,93,2),(4053,73,2),(4053,77,12)])
    root('move','M;100')
    root('dock','P;0')
    root('no-port-dock','P;0',prefix=HIRE+LIST+';M;100;'+LIST+';')
    root('fighters-zero','F;0',prefix=HIRE+LIST+';M;100;'+LIST+';')
    root('fighters-five','F;5',prefix=HIRE+LIST+';M;100;'+LIST+';')
    root('fighters-over-stock','F;1001',prefix=HIRE+LIST+';M;100;'+LIST+';')
    root('missile-zero','!;100;0')
    root('missile-one','!;100;1')
    root('plasma-zero','+;100;0')
    root('planet-report-protected','C;9;101;1',[(152,93,2),(4053,73,3),(4053,77,12),(152,81,42),(152,85,3)])
    root('planet-report-empty','C;9;100;1')
    root('alternating-findings','M;100;'+LIST+';M;1;'+LIST+';M;100;'+LIST+';M;1',[(153,129,8)])
    root('plasma-one','+;2;1',[(4,57,2),(4,53,3000000),(4,61,0),(4,125,0)])
    root('plasma-unreachable','+;200;1')
    root('missile-over-stock','!;100;8')
    root('missile-negative','!;100;-1')
    root('mine-drop','D;1',prefix=HIRE+LIST+';M;100;'+LIST+';')
    root('repeat-last-report','M;100;'+LIST+';M;1;'+LIST+';M;100;'+LIST+';M;1')
    root('three-spies','M;100',prefix='P;9;3;101;101;101\r~~~~\r~~0;'+LIST+';')
    for name,cloak in [('partial-reveal',.5),('full-hidden',1),('uncloaked',0)]:
        root(name,'M;100;'+LIST+';S',[(3,57,101),(3,125,cloak),(152,129,0)])
        result.append(dict(name=name+'-target',command='\r~~~~C;6;1;I',patches=[],parent=name,actor='ENEMY'))
    for name,cloak,hire in [('partial-spy-attack',.5,True),('partial-no-spy-attack',.5,False),('full-hidden-attack',1,True)]:
        root(name,'M;100;'+(LIST+';' if hire else '')+'M;101;A;N',[(3,57,101),(3,125,cloak),(152,129,0)],prefix=None if hire else '')
    root('sensor-only-partial','M;100;S',[(3,57,101),(3,125,.5),(152,129,0)],prefix='')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination',type=Path)
    p.add_argument('--only',nargs='+')
    p.add_argument('--workers',type=int,default=4)
    a=p.parse_args(); selected=cases()
    if a.only:
        unknown=set(a.only)-{c['name']for c in selected}
        if unknown:p.error('unknown cases: '+str(unknown))
        selected=[c for c in selected if c['name']in a.only]
        if any(c.get('parent') and c['parent']not in a.only for c in selected):p.error('select required parent too')
    if a.workers < 1 or a.workers > 8:p.error("workers must be 1–8")
    engine.capture(a.destination.resolve(),selected,a.workers)


if __name__=='__main__':main()
