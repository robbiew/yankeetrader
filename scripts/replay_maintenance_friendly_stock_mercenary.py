"""Compose held friendly garrison and source stock pickup without target reads."""
from replay_qb_graph import mbf
import replay_maintenance_stock_mercenary as core
from replay_maintenance_friendly_stock_rules import admit_gateway


def pickup(world,sector,force):
    if type(world)is not bytearray or sector!=3000 or type(sector)is not int or type(force)is not int or force!=97337:
        raise ValueError('measured incoming gateway force required')
    friendly,governor,stock=admit_gateway(world)
    amount=core.positive_single_floor(stock)if stock else 0
    combined=force+friendly;final=combined+amount
    if final>core.MAX_FORCE:raise ValueError('bounded combined post-pickup force required')
    # Cached entering friendly force is added before stock; receipt actor is combined.
    zero=core._zero_literal();at=4053*137
    world[at+129:at+133]=zero
    mbf.put(world,3051,81,final);mbf.put(world,3051,85,-2)
    return dict(kind='mercenary-pickup',sector=sector,planet_slot=3,planet_name='Gateway Cache',
                captured=False,incoming_force=force,entering_friendly_force=friendly,merged=friendly,
                initial_force=combined,force=final,pickup=amount,raw_stock=stock,
                governor=governor,fractional_discard=stock-amount,conversion='bounded-positive-single-INT-floor')


def maintain(world,stream):
    if type(world)is not bytearray:raise ValueError('mutable modeled world required')
    friendly,_,_=admit_gateway(world)
    get=lambda r,o:mbf.get(world,r,o)
    physical={s:int(get(51+s,81))for s in range(1,3001)if get(51+s,81)>0 and get(51+s,85)==-2}
    if physical!={2368:97337,3000:friendly}or any(get(2419,o)!=0 for o in(93,129)):
        raise ValueError('exact two-force friendly-stock entry required')
    work=bytearray(world);result=core._maintain(work,stream,pickup_action=pickup)
    acts=result['activations'];events=result['events']
    if len(acts)!=2 or acts[0]['origin']!=3000 or acts[0]['force']!=friendly or acts[0]['held']is not True:
        raise ValueError('measured earlier garrison must hold before incoming force')
    if acts[1]['origin']!=2368 or acts[1]['held']is not False or acts[1]['final_sector']!=3000:
        raise ValueError('measured incoming force stops at gateway')
    if len(events)!=1 or events[0]['kind']!='mercenary-pickup'or events[0]['captured']is not False:
        raise ValueError('only silent friendly/planet-stock composition admitted')
    if result['losses']!=0 or result['merged']!=friendly or result['final_sectors']!=[3000]:
        raise ValueError('exact loss-free held-garrison pickup required')
    world[:]=work
    return result
