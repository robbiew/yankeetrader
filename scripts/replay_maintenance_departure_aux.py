"""Before-only public files for bounded occupied-origin and friendly-merge chains.

Only immutable original YTMAINT literal descriptors are read. Physical ledgers,
source-ordered modeled actions and before-only economy determine every amount;
no captured transcript, handoff world or after-target supplies publication text.
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
HOMES=((4052,b'The Wanderer',0),(4150,b'Mercenary Base',-2),(4151,b'Xannoron',-1),(4054,b'Departure Cache',0))


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
        raise ValueError('six immutable departure before files and modeled world required')
    b=before_files['YTDATA.DAT']
    if len(b)!=4151*SIZE or len(world)!=len(b)or before_files['YTRMSG.DAT']:
        raise ValueError('complete worlds and empty private before stream required')
    pair=field(b,1,81),field(world,1,81)
    if pair not in((308,309),(309,310)):raise ValueError('measured departure day pair required')
    for data in(b,world):
        if any(field(data,1,o)!=v for o,v in((53,51),(57,3051),(61,4051),(93,4151))):raise ValueError('default record geometry required')
        if data[:11]!=b'YTSCORE.ASC'or field(data,1,41)!=11:raise ValueError('default scoreboard path required')
        for r,title,owner in HOMES:
            if name(data,r)!=title or field(data,r,73)!=owner or len(_links(data,r-4051))!=1:raise ValueError('existing named home/cache and unique link required')
        if _links(data,3)not in([2999],[3000])or field(data,4054,117)!=0 or not 0<field(data,4054,77)<=600000:raise ValueError('neutral zero-bank positive-ground Departure Cache required')
        if any(field(data,r,85)!=0 for r in range(4052,4152)if r not in(4052,4054,4150,4151)):raise ValueError('unmodeled active ordinary planet')
        if any(field(data,r,89)!=0 for r in range(3052,4052)):raise ValueError('tax-funded hiring remains excluded')
    if _links(b,3)!=_links(world,3):raise ValueError('Departure Cache physical link must survive unchanged')
    for r in range(2,52):
        for o in range(41,137,4):
            if field(b,r,o)not in((0,-1)if o==109 else(0,))or field(world,r,o)!=(-1 if o==109 else 0):raise ValueError('inactive human ranks required')
    if type(events)not in(tuple,list)or type(mercenary)is not dict:raise ValueError('modeled Xannor events and Mercenary result required')
    totals=[_physical(b),_physical(world)];physical=_mercenary_map(b);losses={-1:0,-2:0,0:0};pickup=0;discard=0.0
    previous=1;dead=set();group_force={};grounds={r:_ground(b,world,r)for r in(4052,4054,4150)}
    for e in events:
        if type(e)is not dict or e.get('kind')not in('planet','defense'):raise ValueError('only measured home assaults and Mercenary defense admitted')
        g=e.get('group');sector=e.get('sector');n=_whole(e.get('initial_force'),10000,'initial Xannor force');x=_whole(e.get('force'),n,'remaining Xannor force')
        if type(g)is not int or g in dead or not previous<=g<=20 or g<2 or type(sector)is not int or not 8<=sector<=3000 or n==0:raise ValueError('source-ordered actual Xannor group required')
        if g in group_force and group_force[g]!=n:raise ValueError('continuing Xannor force must follow its actual prior outcome')
        if e['kind']=='planet':
            slot=e.get('planet_slot');title=e.get('planet_name')
            if(slot,title)not in((1,'The Wanderer'),(99,'Mercenary Base'))or x!=0:raise ValueError('only measured fatal positive-ground home defense admitted')
            record=4051+slot;owner=0 if slot==1 else-2
            if name(world,record)!=title.encode()or field(world,record,73)!=owner or _links(world,slot)!=[sector]:raise ValueError('actual surviving home title and unique link required')
            ground=_whole(e.get('ground'),600000,'remaining ground');initial=_whole(e.get('initial_ground'),600000,'initial ground')
            if not 0<ground<initial or e.get('ground_spent')!=initial-ground or initial!=grounds[record]:raise ValueError('source-ordered actual home ground spending required')
            grounds[record]=ground
        else:
            if e.get('owner')!=-2:raise ValueError('only actual Mercenary foreign defense admitted')
            initial=_whole(e.get('initial_defenders'),LIMIT,'initial Mercenary defenders');remaining=_whole(e.get('defenders'),initial,'remaining Mercenary defenders')
            if not initial or physical.get(sector)!=initial or bool(x)==bool(remaining):raise ValueError('exact actual defended force and one positive winner required')
            xd=_whole(e.get('x_damage'),n+5000,'raw Xannor damage');md=_whole(e.get('defender_damage'),initial+5000,'raw Mercenary damage')
            if x:
                if xd!=n-x or not initial<=md<=initial+5000:raise ValueError('surviving attacker raw damage must equal actual losses')
            elif md!=initial-remaining or not n<=xd<=n+5000:raise ValueError('surviving defender raw damage must equal actual losses')
            if remaining:physical[sector]=remaining
            else:physical.pop(sector)
            losses[-2]+=initial-remaining
        previous=g;group_force[g]=x
        if not x:dead.add(g)
        losses[-1]+=n-x
    if any(field(world,r,77)!=v for r,v in grounds.items()):raise ValueError('modeled home/cache ground must equal production less actual assault spending')
    mevents=mercenary.get('events');activations=mercenary.get('activations')
    if type(mevents)not in(tuple,list)or type(activations)not in(tuple,list)or not activations or len(mevents)>16:raise ValueError('explicit bounded Mercenary events and activations required')
    available=sum(physical.values())
    if mercenary.get('initial_force')!=available:raise ValueError('Mercenary phase initial total must follow actual earlier defense losses')
    event_index=0;pickup_records=set();merge_count=0;previous_origin=3001
    for a in activations:
        if type(a)is not dict:raise ValueError('modeled activation row required')
        origin=a.get('origin');force=_whole(a.get('force'),LIMIT,'activation force');gate=a.get('gate')
        if type(origin)is not int or not 8<=origin<previous_origin or not force or physical.get(origin)!=force or type(gate)not in(int,float)or not 0<=gate<1:raise ValueError('actual descending physical Mercenary activation required')
        previous_origin=origin;link=field(world,51+origin,93)
        if a.get('held')is True:
            if not link>0 or not gate<F32(.66):raise ValueError('held occupied origin requires its eager source gate below SINGLE .66')
            continue
        if a.get('held')is not False or(link>0 and gate<F32(.66)):raise ValueError('departing occupied origin requires its actual source gate')
        entered=a.get('entered');route=a.get('route');target=a.get('target')
        if type(entered)not in(tuple,list)or type(route)not in(tuple,list)or len(route)<2 or route[0]!=origin or route[-1]!=target or list(entered)!=list(route[1:1+len(entered)])or type(target)is not int or not 8<=target<=3000 or not entered or any(type(s)is not int or not 1<=s<=3000 for s in route):raise ValueError('actual entered prefix of the computed nonempty route required')
        physical.pop(origin);stopped=False
        for sector in entered:
            while event_index<len(mevents)and mevents[event_index].get('sector')==sector:
                e=mevents[event_index];event_index+=1
                n=_whole(e.get('initial_force'),LIMIT,'event initial force');m=_whole(e.get('force'),LIMIT,'event remaining force')
                if not n or n!=force or not 8<=sector<=3000:raise ValueError('Mercenary event stamp must follow preceding local force at a measured ordinary encounter')
                kind=e.get('kind')
                if kind=='mercenary-mine':
                    loss=_whole(e.get('losses'),n,'actual mine casualty');old=_whole(e.get('initial_mines'),3,'initial mines');remaining=_whole(e.get('mines'),old,'remaining mines')
                    if sector!=2356 or not loss or not m or n-m!=loss or not old or not remaining<old or e.get('mines_spent')!=old-remaining or field(b,51+sector,129)!=old or field(world,51+sector,129)!=remaining:raise ValueError('actual bounded surviving mine loss and residue required')
                    losses[-2]+=loss
                elif kind=='mercenary-attack':
                    defenders=_whole(e.get('initial_defenders'),10000,'actual Xannor defenders')
                    if e.get('owner')!=-1 or e.get('defender_name')!='The Xannor'or not defenders or not m or not m<=n or e.get('defenders')!=0 or e.get('losses')!=n-m or e.get('defender_losses')!=defenders:raise ValueError('actual positive Mercenary offensive winner and exact casualties required')
                    if field(world,51+sector,85)==-1 and field(world,51+sector,81)>0:raise ValueError('defeated Xannor defenders cannot remain physically present')
                    losses[-1]+=defenders;losses[-2]+=n-m
                elif kind=='mercenary-merge':
                    merged=_whole(e.get('merged'),37,'friendly merge increment')
                    if sector!=2368 or not merged or physical.get(sector)!=merged or e.get('initial_defenders')!=merged or e.get('defenders')!=0 or e.get('owner')!=-2 or e.get('losses')!=0 or m!=n+merged:raise ValueError('silent friendly merge uses actual remaining friendly force exactly once')
                    physical.pop(sector);merge_count+=1
                    at=(51+sector-1)*SIZE
                    if world[at+81:at+89]!=bytes.fromhex('0000800000008000'):raise ValueError('friendly merge preserves source8472 force/owner clears')
                elif kind=='mercenary-pickup':
                    record=4052;amount=_whole(e.get('pickup'),LIMIT,'whole source stock pickup');raw=e.get('raw_stock');fraction=e.get('fractional_discard')
                    if e.get('captured')is not True or e.get('planet_slot')!=1 or e.get('planet_name')!='The Wanderer'or sector!=_links(world,1)[0]or record in pickup_records:raise ValueError('only actual later Wanderer encounter pickup admitted; origin stock stays untouched')
                    produced=_stock(b,world,record)
                    if type(raw)not in(int,float)or raw!=produced or math.floor(raw)!=amount or type(fraction)not in(int,float)or fraction!=raw-amount or not 0<=fraction<.5 or m!=n+amount:raise ValueError('whole pickup, bounded fractional discard and force addition must derive from grown stock')
                    at=(record-1)*SIZE
                    if world[at+129:at+133]!=bytes.fromhex('00008000'):raise ValueError('complete source stock must clear with literal8472')
                    pickup_records.add(record);pickup+=amount;discard+=fraction;stopped=True
                else:raise ValueError('unmeasured Mercenary outcome')
                force=m
                if stopped and(event_index<len(mevents)and mevents[event_index].get('sector')==sector):raise ValueError('pickup stops the source route before further actions')
            if stopped:break
        destination=a.get('final_sector');end_force=_whole(a.get('final_force'),LIMIT,'activation final force')
        if end_force!=force or destination!=(sector if stopped else target)or a.get('stopped_for_pickup')is not stopped:raise ValueError('activation endpoint must follow actual local actions')
        if stopped and entered[-1]!=sector:raise ValueError('entered route ends at actual pickup')
        if destination in physical:raise ValueError('unrecorded friendly merge at activation endpoint')
        physical[destination]=force
    if event_index!=len(mevents):raise ValueError('every event must occur on an actual entered route in source order')
    final=_mercenary_map(world)
    if physical!=final or mercenary.get('final_sectors')!=sorted(final)or mercenary.get('force')!=sum(final.values()):raise ValueError('final Mercenary fields must equal the complete modeled phase ledger')
    if any(totals[1][o]+losses[o]-(pickup if o==-2 else 0)!=totals[0][o]for o in totals[0]):raise ValueError('all actual physical losses and stock transfers must conserve faction totals')
    for record in(4052,4054,4150):
        if record not in pickup_records and field(world,record,129)!=_stock(b,world,record):raise ValueError('uncollected source-grown title stock must remain saved')
    return totals,losses,tuple(mevents),pickup,discard,merge_count


def _news(original,date,clock,events,mercenary_events):
    lines=[clock.encode()+b' '+date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)'),literal(original,b'  -  Xannor report:'),literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.')]
    for e in events:
        if e['kind']=='planet':
            lines.extend([original_string(original,0x809e)+b' '+str(e['initial_force']).encode()+original_string(original,0x8b70)+b'"'+e['planet_name'].encode()+b'"',original_string(original,0x8bac)+original_string(original,0x8bc4)])
        else:
            suffix=0x8cdc if e['force']==0 else 0x8cc8
            lines.append(original_string(original,0x803e)+original_string(original,0x8cb2)+original_string(original,0x8afc)+b' '+str(e['x_damage']).encode()+original_string(original,0x8b06)+b' '+str(e['defender_damage']).encode()+original_string(original,0x8cc2)+original_string(original,suffix))
    lines.append(literal(original,b'  -  Mercenary Report:'))
    for e in mercenary_events:
        n=str(e['initial_force']).encode();kind=e['kind']
        if kind=='mercenary-merge':continue
        if kind=='mercenary-attack':
            lines.extend([original_string(original,0x809e)+b' '+n+original_string(original,0x88e2)+b' '+str(e['initial_defenders']).encode()+original_string(original,0x88fc)+e['defender_name'].encode()+b'!',original_string(original,0x8934)+original_string(original,0x8922)])
        elif kind=='mercenary-mine':
            lines.append(original_string(original,0x809e)+b' '+n+original_string(original,0x8804)+b' '+str(e['sector']).encode()+original_string(original,0x8008))
            lines.append(original_string(original,0x8830)if not e['force']else original_string(original,0x8856)+b' '+str(e['losses']).encode()+original_string(original,0x886e))
        else:
            title=e['planet_name'].encode();prefix=original_string(original,0x81fe)+b' '+n
            lines.append(prefix+original_string(original,0x887c)+title+original_string(original,0x8008))
            if e['pickup']:lines.append(prefix+original_string(original,0x889e)+b' '+str(e['pickup']).encode()+original_string(original,0x88b6)+title+original_string(original,0x8008))
    return CRLF.join(lines)+CRLF+EOF


def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,created=(),events=(),mercenary=None):
    """Publish derived physical scores, exact original text and empty private mail."""
    if created!=():raise ValueError('departure children retain all homes')
    if any(type(d)is not datetime.date for d in(news_date,score_date)):raise ValueError('separate source text dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    if mercenary is None:raise ValueError('explicit modeled Mercenary result required')
    totals,losses,mevents,pickup,discard,merges=_admit(before_files,after_world,events,mercenary)
    serial=field(after_world,1,81)
    if news_date!=datetime.date(2026,1,1)+datetime.timedelta(days=serial-1)or score_date!=news_date:raise ValueError('measured source publication calendar required')
    original=original_literals();scores={o:100*totals[1][o]for o in(-1,-2)}
    board,percentages=_scoreboard(original,score_date,score_clock,scores)
    result={'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],'YTRMSG.DAT':b'','YTNEWS.DAT':_news(original,news_date,news_clock,events,mevents),'YTSCORE.ASC':board}
    return result,dict(created=[],scores=scores,percentages=percentages,physical=totals,modeled_losses=losses,stock_pickup=pickup,fractional_discard=discard,silent_merges=merges,public_events=len(events)+sum(e['kind']!='mercenary-merge'for e in mevents),private_bytes=0)
