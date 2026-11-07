"""Before-only public files for the twelve measured positive stock conversions.

Only original YTMAINT literals are opened. Source-grown stock, whole transfer,
fractional discard and physical ledgers determine receipts; captured outputs do
not enter synthesis. Historical gateway/departure publishers remain unchanged.
"""
import datetime
import math
from fractions import Fraction
from replay_qb_graph import F32
from replay_maintenance_aux import CRLF,EOF,_matrix_clock,field,literal,name,original_literals,original_string,using
from replay_maintenance_evolved_combat_aux import _whole,_links

FILES={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}
SIZE=137
LIMIT=400000
HOMES=((4052,b'The Wanderer',0),(4150,b'Mercenary Base',-2),(4151,b'Xannoron',-1),(4054,b'Gateway Cache',0))

def _scoreboard(original,date,clock,scores):
    leader=max(scores.values())
    if not 0<leader<=100*LIMIT:raise ValueError('positive bounded NPC denominator required')
    percentages=[]
    for owner in(-1,-2):
        exact=Fraction(100*scores[owner],leader)
        if (100*exact).denominator==2:raise ValueError('halfway percentage formatting is outside this profile')
        percentages.append(float(exact))
    row=using(literal(original,b'  ###,###,###,###  ####.##%'),[scores[-1],percentages[0],scores[-2],percentages[1]])
    lines=[b'',literal(original,b'Y a n k e e   T r a d e r   S c o r e b o a r d'),b'',
      literal(original,b'Last updated at: ')+date.strftime('%m-%d-%Y').encode()+b' '+clock.encode(),b'',
      literal(original,b'Rank  Rank%        Score        Team   Ports   Player'),
      literal(original,b'==== ======= ================= ====== ======= ================================'),b'',
      literal(original,b'T e a m   R a n k i n g s'),b'',literal(original,b'Rank  Rank%        Score        Team   Team Name'),
      literal(original,b'==== ======= ================= ====== ========================================'),b'',
      literal(original,b'N o n  -  H u m a n   P l a y e r s'),b'',literal(original,b'    The Xannor       Rank%     The Mercenaries'),
      literal(original,b'================== =========  ================='),row,b'']
    return CRLF.join(lines)+CRLF+EOF,percentages


def _physical(world):
    totals={-1:0,-2:0,0:0}
    for sector in range(1,3001):
        n=_whole(field(world,51+sector,81),LIMIT,'physical sector force');owner=field(world,51+sector,85)
        if owner not in totals:raise ValueError('unknown physical sector owner')
        totals[owner]+=n
    if totals[-1]>10000 or totals[-2]>LIMIT or totals[0]>37:raise ValueError('unmeasured faction inventory')
    return totals


def _mercenary_map(world):
    return {s:int(field(world,51+s,81))for s in range(1,3001)if field(world,51+s,81)>0 and field(world,51+s,85)==-2}


def _elapsed(before,world,record):
    minutes=field(world,record,89);prior=field(before,record,89)
    if any(not math.isfinite(v)or not 0<=v<1 for v in(minutes,prior)):raise ValueError('bounded explicit midnight/second-two/second-four planet clocks required')
    elapsed=F32(F32(field(world,record,41)-field(before,record,41))+F32(F32(minutes-prior)/1440))
    if not .999<=elapsed<=1.001:raise ValueError('measured one-day source economy required')
    return elapsed


def _stock(before,world,record):
    """Source single stock assignment from before rates/bank and modeled clocks."""
    rates=[field(before,record,o)for o in(45,49,53)];bank=field(before,record,117);stock=field(before,record,129)
    if any(not math.isfinite(v)or not 0<=v<=200000 for v in rates)or not 0<=bank<=30000000 or not 0<=stock<=10000000:
        raise ValueError('bounded source fighter-stock context required')
    base=math.floor(F32(F32(rates[0]+rates[1])+rates[2]));bonus=F32(bank/500)
    return F32(stock+F32(F32(base+bonus)*_elapsed(before,world,record)))


def _ground(before,world,record):
    ground=field(before,record,77);bank=field(before,record,117);elapsed=_elapsed(before,world,record)
    if not 0<=ground<=600000 or not 0<=bank<=30000000:raise ValueError('bounded source ground context required')
    return math.floor(F32(ground+ground*elapsed*F32(.01)+F32(bank/10000)*elapsed))


def _admit(before_files,world,events,mercenary):
    if type(before_files)is not dict or set(before_files)!=FILES or any(type(v)is not bytes for v in before_files.values())or type(world)is not bytes:
        raise ValueError('six immutable modeled stock before files and world required')
    before=before_files['YTDATA.DAT']
    if len(before)!=4151*SIZE or len(world)!=len(before)or before_files['YTRMSG.DAT']:
        raise ValueError('complete worlds and empty private before stream required')
    if(field(before,1,81),field(world,1,81))!=(308,309):raise ValueError('only measured November4-to5 stock continuation admitted')
    for data in(before,world):
        if any(field(data,1,o)!=v for o,v in((53,51),(57,3051),(61,4051),(93,4151))):raise ValueError('default record geometry required')
        if data[:11]!=b'YTSCORE.ASC'or field(data,1,41)!=11:raise ValueError('default scoreboard path required')
        for record,title,owner in HOMES:
            if name(data,record)!=title or field(data,record,73)!=owner or len(_links(data,record-4051))!=1:raise ValueError('existing named home/gateway and unique physical link required')
        if _links(data,3)!=[3000]or field(data,4054,117)!=0 or not 0<field(data,4054,77)<=600000:raise ValueError('neutral zero-bank positive-ground Gateway Cache required')
        if any(field(data,r,85)!=0 for r in range(4052,4152)if r not in(4052,4054,4150,4151)):raise ValueError('unmodeled active ordinary planet')
        if any(field(data,r,89)!=0 for r in range(3052,4052)):raise ValueError('tax-funded hiring remains excluded')
    for record in range(2,52):
        for offset in range(41,137,4):
            if field(before,record,offset)not in((0,-1)if offset==109 else(0,))or field(world,record,offset)!=(-1 if offset==109 else 0):raise ValueError('inactive human ranks required')
    if type(events)not in(tuple,list)or type(mercenary)is not dict:raise ValueError('explicit modeled Xannor and Mercenary action ledgers required')
    totals=[_physical(before),_physical(world)];initial_map=_mercenary_map(before)
    if initial_map!={2368:97337}:raise ValueError('single measured 97337 Mercenary origin at2368 required')
    losses={-1:0,-2:0,0:0};grounds={record:_ground(before,world,record)for record in(4052,4054,4150)};previous=1;dead=set()
    for event in events:
        if type(event)is not dict or event.get('kind')!='planet':raise ValueError('only measured fatal Xannor home assaults admitted')
        group=event.get('group');sector=event.get('sector');force=_whole(event.get('initial_force'),10000,'initial Xannor force')
        if type(group)is not int or group in dead or not previous<=group<=20 or group<2 or type(sector)is not int or not 8<=sector<=3000 or not force or event.get('force')!=0:raise ValueError('source-ordered fatal Xannor group required')
        slot=event.get('planet_slot');title=event.get('planet_name')
        if(slot,title)not in((1,'The Wanderer'),(99,'Mercenary Base')):raise ValueError('only actual named home defense admitted')
        record=4051+slot
        if _links(world,slot)!=[sector]or name(world,record)!=title.encode():raise ValueError('home assault binds its actual surviving title/link')
        initial=_whole(event.get('initial_ground'),600000,'initial ground');ground=_whole(event.get('ground'),initial,'remaining ground')
        if not 0<ground<initial or initial!=grounds[record]or event.get('ground_spent')!=initial-ground:raise ValueError('home ground must follow production and preceding assaults')
        grounds[record]=ground;losses[-1]+=force;previous=group;dead.add(group)
    if any(field(world,r,77)!=ground for r,ground in grounds.items()):raise ValueError('pickup cannot debit independently produced home/gateway ground')
    mevents=mercenary.get('events');activations=mercenary.get('activations')
    if type(mevents)not in(tuple,list)or len(mevents)!=1 or type(mevents[0])is not dict or type(activations)not in(tuple,list)or len(activations)!=1 or type(activations[0])is not dict:raise ValueError('one actual source activation and stock pickup required')
    event=mevents[0];activation=activations[0]
    n=_whole(event.get('initial_force'),LIMIT,'initial Mercenary force');m=_whole(event.get('force'),LIMIT,'remaining Mercenary force');amount=_whole(event.get('pickup'),LIMIT,'whole fighter pickup')
    if event.get('kind')!='mercenary-pickup'or event.get('captured')is not True or event.get('sector')!=3000 or event.get('planet_slot')!=3 or event.get('planet_name')!='Gateway Cache'or event.get('conversion')!='bounded-positive-single-INT-floor':raise ValueError('actual source-qualified Gateway Cache pickup required')
    produced=_stock(before,world,4054);raw=event.get('raw_stock');fraction=event.get('fractional_discard')
    if type(raw)not in(int,float)or raw!=produced or not 0<raw<=LIMIT or math.floor(raw)!=amount or type(fraction)not in(int,float)or fraction!=raw-amount or not 0<=fraction<1:raise ValueError('whole pickup and discarded fraction must derive from complete source-grown positive stock')
    if n!=97337 or m!=n+amount:raise ValueError('converted stock must add exactly to the measured pre-pickup force')
    if mercenary.get('initial_force')!=n or mercenary.get('force')!=m or mercenary.get('pickup')!=amount or mercenary.get('losses')!=0 or mercenary.get('final_sectors')!=[3000]:raise ValueError('Mercenary summary must equal its exact pickup ledger')
    route=activation.get('route');entered=activation.get('entered');target=activation.get('target');gate=activation.get('gate')
    if activation.get('origin')!=2368 or activation.get('force')!=n or activation.get('held')is not False or type(gate)not in(int,float)or not 0<=gate<1:raise ValueError('actual unheld source activation and eager gate required')
    if type(route)not in(tuple,list)or len(route)<2 or route[0]!=2368 or route[1]!=3000 or type(target)is not int or not 8<=target<=3000 or route[-1]!=target or any(type(s)is not int or not 1<=s<=3000 for s in route)or list(entered if type(entered)in(tuple,list)else())!=[3000]:raise ValueError('one forced entered gateway hop on the computed route required')
    if activation.get('final_sector')!=3000 or activation.get('final_force')!=m or activation.get('stopped_for_pickup')is not True:raise ValueError('pickup must stop at and save its actual gateway encounter')
    if _mercenary_map(world)!={3000:m}:raise ValueError('saved physical Mercenaries must equal the transferred whole fighters')
    at=(4054-1)*SIZE
    if world[at+129:at+133]!=bytes.fromhex('00008000'):raise ValueError('entire original stock clears using exact source8472 raw zero')
    at=(2419-1)*SIZE
    if world[at+81:at+89]!=bytes.fromhex('0000280000002800'):raise ValueError('departed origin retains source859e force/owner zeros')
    if any(totals[1][owner]+losses[owner]-(amount if owner==-2 else 0)!=totals[0][owner]for owner in totals[0]):raise ValueError('physical casualties and transferred stock must conserve faction forces')
    for record in(4052,4150):
        if field(world,record,129)!=_stock(before,world,record):raise ValueError('uncollected source-grown home stock remains saved')
    return totals,losses,event,amount,fraction


def _news(original,date,clock,events,pickup):
    lines=[clock.encode()+b' '+date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)'),literal(original,b'  -  Xannor report:'),literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.')]
    for event in events:
        lines.extend([original_string(original,0x809e)+b' '+str(event['initial_force']).encode()+original_string(original,0x8b70)+b'"'+event['planet_name'].encode()+b'"',original_string(original,0x8bac)+original_string(original,0x8bc4)])
    lines.append(literal(original,b'  -  Mercenary Report:'))
    prefix=original_string(original,0x81fe)+b' '+str(pickup['initial_force']).encode();title=pickup['planet_name'].encode()
    lines.append(prefix+original_string(original,0x887c)+title+original_string(original,0x8008))
    if pickup['pickup']:
        lines.append(prefix+original_string(original,0x889e)+b' '+str(pickup['pickup']).encode()+original_string(original,0x88b6)+title+original_string(original,0x8008))
    return CRLF.join(lines)+CRLF+EOF


def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,created=(),events=(),mercenary=None):
    """Publish all five auxiliary files from modeled source state and actions."""
    if created!=():raise ValueError('stock continuation retains all existing homes')
    if any(type(d)is not datetime.date for d in(news_date,score_date)):raise ValueError('separate source publication dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    if mercenary is None:raise ValueError('explicit modeled Mercenary result required')
    totals,losses,event,pickup,fraction=_admit(before_files,after_world,events,mercenary)
    serial=field(after_world,1,81)
    if news_date!=datetime.date(2026,1,1)+datetime.timedelta(days=serial-1)or score_date!=news_date:raise ValueError('measured November5 publication dates required')
    original=original_literals();scores={owner:100*totals[1][owner]for owner in(-1,-2)}
    board,percentages=_scoreboard(original,score_date,score_clock,scores)
    output={'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],'YTRMSG.DAT':b'','YTNEWS.DAT':_news(original,news_date,news_clock,events,event),'YTSCORE.ASC':board}
    return output,dict(created=[],scores=scores,percentages=percentages,physical=totals,modeled_losses=losses,stock_pickup=pickup,fractional_discard=fraction,public_events=len(events)+1,private_bytes=0)
