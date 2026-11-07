"""Derive the linked negative-owner combat, preserving extinct-force continuation."""
from replay_qb_graph import mbf
from replay_maintenance_stock_mercenary import _maintain
from replay_maintenance_gateway_mercenary import attack

def marked_attack(world,stream,sector,force):
    stream.mark('battle-entry');result=attack(world,stream,sector,force);stream.mark('battle-exit');return result

def scan(world,stream):return _maintain(world,stream,attack_action=marked_attack)

def maintain(world,stream):
    if type(world)is not bytearray or len(world)!=4151*137:raise ValueError('complete mutable modeled world required')
    incoming=mbf.get(world,2419,81)
    physical={s:int(mbf.get(world,51+s,81))for s in range(1,3001)if mbf.get(world,51+s,81)>0 and mbf.get(world,51+s,85)==-2}
    if incoming not in(0,1,37)or physical!=({2368:int(incoming)}if incoming else {}):raise ValueError('one measured attacker or already extinct context required')
    if mbf.get(world,3051,85)!=-1 or mbf.get(world,3051,93)!=3 or mbf.get(world,3051,129)!=0:raise ValueError('linked mine-free defensive encounter required')
    work=bytearray(world);result=scan(work,stream)
    if incoming:
        if len(result['events'])!=1 or result['events'][0]['kind']!='mercenary-attack' or result['events'][0]['force']!=0 or result['events'][0]['defenders']<=0:raise ValueError('only measured fatal offense with surviving defenders admitted')
        if len(result['activations'])!=1 or result['activations'][0]['origin']!=2368 or result['activations'][0]['entered']!=[3000]:raise ValueError('one source-derived forced gateway entry required')
    elif result['events']or result['activations']:raise ValueError('no resurrected force or action allowed')
    if result['force'] or result['final_sectors'] or result['pickup']:raise ValueError('actual extinction and uncollected stock required')
    world[:]=work;return result
