"""Source-derived descending scan with held or departed gateway garrison."""
from replay_qb_graph import mbf
import replay_maintenance_stock_mercenary as core
from replay_maintenance_departed_stock_rules import admit_gateway


def pickup(world,sector,force):
    if type(world)is not bytearray or len(world)!=4151*137 or type(sector)is not int or sector!=3000 or type(force)is not int or force!=97337:
        raise ValueError('measured incoming gateway force required')
    get=lambda r,o:mbf.get(world,r,o)
    friendly=get(3051,81);owner=get(3051,85);stock=get(4054,129);governor=get(4054,73)
    if friendly not in (0,37) or owner not in (0,-2) or (friendly and owner!=-2) or (governor,stock) not in ((0,0),(0,.5),(0,37),(-2,37)):
        raise ValueError('measured empty or friendly gateway and stock required')
    if bytes(world[4053*137+129:4053*137+133])!=mbf.enc(stock) or get(4054,85)!=13 or get(3051,93)!=3 or get(3051,129)!=0 or get(4054,117)!=0 or bytes(world[4053*137:4053*137+41])!=b'Gateway Cache'.ljust(41,b' '):
        raise ValueError('measured linked mine-free Gateway Cache required')
    amount=core.positive_single_floor(stock) if stock else 0
    combined=force+int(friendly);final=combined+amount
    if final>core.MAX_FORCE:raise ValueError('bounded final force required')
    world[4053*137+129:4053*137+133]=core._zero_literal()
    mbf.put(world,3051,81,final);mbf.put(world,3051,85,-2)
    return dict(kind='mercenary-pickup',sector=sector,planet_slot=3,planet_name='Gateway Cache',
                captured=friendly==0,incoming_force=force,entering_friendly_force=int(friendly),merged=int(friendly),
                initial_force=combined,force=final,pickup=amount,raw_stock=stock,governor=int(governor),
                fractional_discard=stock-amount,conversion='bounded-positive-single-INT-floor')


def maintain(world,stream):
    if type(world)is not bytearray:raise ValueError('mutable modeled world required')
    friendly,_,_=admit_gateway(world)
    physical={s:int(mbf.get(world,51+s,81)) for s in range(1,3001) if mbf.get(world,51+s,81)>0 and mbf.get(world,51+s,85)==-2}
    if physical!={2368:97337,3000:friendly}:raise ValueError('two measured initial forces required')
    work=bytearray(world);result=core._maintain(work,stream,pickup_action=pickup)
    acts=result['activations'];events=result['events']
    if not acts or acts[0]['origin']!=3000 or acts[0]['force']!=37:
        raise ValueError('descending local activation required')
    if len(events)!=1 or events[0]['kind']!='mercenary-pickup' or result['losses']!=0:
        raise ValueError('only loss-free single gateway pickup admitted')
    if any(a['origin']!=2368 and a['force']!=37 for a in acts):raise ValueError('only local group may reactivate')
    world[:]=work
    return result
