"""Source-derived neutral transfer and linked-mine scan with local reactivation."""
from replay_qb_graph import mbf
import replay_maintenance_stock_mercenary as core
from replay_maintenance_neutral_owner_stock_rules import admit_gateway


def pickup(world,sector,force):
    if type(world)is not bytearray or len(world)!=4151*137 or type(sector)is not int or sector!=3000 or type(force)is not int or not 1<=force<=97337:
        raise ValueError('measured incoming gateway force required')
    get=lambda r,o:mbf.get(world,r,o)
    friendly=get(3051,81);owner=get(3051,85);stock=get(4054,129);governor=get(4054,73)
    if (owner,friendly,stock) not in ((0,0,37),(0,1,0),(0,37,37),(0,37,.5),(-2,37,37)) or governor!=0 or (stock!=37 and force!=97337):
        raise ValueError('measured empty or friendly gateway and stock required')
    if bytes(world[4053*137+129:4053*137+133])!=mbf.enc(stock) or get(4054,85)!=13 or get(3051,93)!=3 or get(3051,129)!=0 or get(4054,117)!=0 or bytes(world[4053*137:4053*137+41])!=b'Gateway Cache'.ljust(41,b' '):
        raise ValueError('measured linked mine-free Gateway Cache required')
    amount=core.positive_single_floor(stock) if stock else 0
    combined=force+int(friendly);final=combined+amount
    if final>core.MAX_FORCE:raise ValueError('bounded final force required')
    world[4053*137+129:4053*137+133]=core._zero_literal()
    mbf.put(world,3051,81,final);mbf.put(world,3051,85,-2)
    return dict(kind='mercenary-pickup',sector=sector,planet_slot=3,planet_name='Gateway Cache',
                captured=friendly==0,neutral_transferred=int(friendly)if owner==0 else 0,incoming_force=force,entering_friendly_force=int(friendly),merged=int(friendly)if owner==-2 else 0,
                initial_force=combined,force=final,pickup=amount,raw_stock=stock,governor=int(governor),
                fractional_discard=stock-amount,conversion='bounded-positive-single-INT-floor')


def maintain(world,stream):
    if type(world)is not bytearray:raise ValueError('mutable modeled world required')
    friendly,_,_=admit_gateway(world)
    physical={s:int(mbf.get(world,51+s,81)) for s in range(1,3001) if mbf.get(world,51+s,81)>0 and mbf.get(world,51+s,85)==-2}
    expected={2368:97337}
    if mbf.get(world,3051,85)==-2:expected[3000]=friendly
    if physical!=expected:raise ValueError('two measured initial forces required')
    work=bytearray(world);result=core._maintain(work,stream,pickup_action=pickup,mine_action=mine_hit)
    acts=result['activations'];events=result['events']
    if not 1<=len(acts)<=3 or any(a['origin']!=2368 and a['force']!=37 for a in acts):raise ValueError('only measured incoming and local activations admitted')
    if len([e for e in events if e['kind']=='mercenary-pickup'])!=1 or any(e['kind']not in('mercenary-mine','mercenary-pickup')for e in events):raise ValueError('only gateway mine then pickup admitted')
    result['neutral_transferred']=sum(e.get('neutral_transferred',0)for e in events)
    world[:]=work
    return result


def mine_hit(world,stream,sector,force):
    """Original4a78..4c7a: count-two shrinking damage per INITIAL mine.

    The source helper count is two, unlike the four-draw allocation caller.
    All initial mines call it even after force zero. A mine is spent only for
    positive capped damage; canonical single subtraction writes exact zero.
    """
    if type(world)is not bytearray or len(world)!=4151*137 or type(sector)is not int or sector!=3000 or type(force)is not int or force!=97337:
        raise ValueError('bounded actual non-Union route force and sector required')
    rec=51+sector;mines=mbf.get(world,rec,129)
    if mines!=int(mines)or mines!=1 or mbf.get(world,rec,93)!=3 or mbf.get(world,rec,85)not in(-2,0):
        raise ValueError('one linked neutral/friendly gateway mine required')
    if mbf.get(world,4054,129)!=37 or mbf.get(world,4054,73)!=0 or mbf.get(world,rec,81)not in(0,37):raise ValueError('measured whole-stock linked mine context required')
    initial=int(mines);remaining=force;spent=0;rolls=[];old=stream.rng.state;draws=stream.rng.draws
    for _ in range(initial):
        stream.reseed('h2',0x4aa4)
        bound=10000
        for _ in range(2):bound=stream.rng.integer(bound)
        rolls.append(bound);damage=min(remaining,bound)
        if remaining>0 and damage>0:
            remaining-=damage;mines-=1;spent+=1
    # Commit once the initial-count helper loop completes, preserving exact
    # final source subtraction bytes while leaving rejects unmodified.
    mbf.put(world,rec,129,mines)
    return dict(kind='mercenary-mine',sector=sector,initial_force=force,force=remaining,
                losses=force-remaining,initial_mines=initial,mines=int(mines),mines_spent=spent,
                rolls=rolls,initial_rng_state=old,final_rng_state=stream.rng.state,
                rng_draws=stream.rng.draws-draws)
