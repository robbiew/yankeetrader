"""Before-only public files for the six measured gateway hazard fixtures.

The publisher opens only immutable original YTMAINT for literal descriptors.
All amounts, casualty accounting and pre-pickup stamps come from modeled events
and physical worlds. It never reads a captured world or target transcript.
"""
import datetime
import math
from replay_qb_graph import F32
from replay_maintenance_aux import CRLF,EOF,_matrix_clock,field,literal,name,original_literals,original_string
from replay_maintenance_occupied_aux import _scoreboard
from replay_maintenance_evolved_combat_aux import _whole,_physical,_links

FILES={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}
SIZE=137
HOMES=((4052,b'The Wanderer',0),(4150,b'Mercenary Base',-2),(4151,b'Xannoron',-1),(4054,b'Gateway Cache',0))


def _admit(before_files,world,events,mercenary):
    if type(before_files)is not dict or set(before_files)!=FILES or any(type(v)is not bytes for v in before_files.values())or type(world)is not bytes:
        raise ValueError('six immutable gateway before files and modeled world required')
    b=before_files['YTDATA.DAT']
    if len(b)!=4151*SIZE or len(world)!=len(b)or before_files['YTRMSG.DAT']:
        raise ValueError('complete worlds and empty private before stream required')
    pair=field(b,1,81),field(world,1,81)
    if pair not in((308,309),(309,310)):raise ValueError('measured gateway day pair required')
    for data in(b,world):
        if any(field(data,1,o)!=v for o,v in((53,51),(57,3051),(61,4051),(93,4151))):raise ValueError('default record geometry required')
        if data[:11]!=b'YTSCORE.ASC'or field(data,1,41)!=11:raise ValueError('default scoreboard path required')
        for r,title,owner in HOMES:
            if name(data,r)!=title or field(data,r,73)!=owner or len(_links(data,r-4051))!=1:raise ValueError('existing named home/gateway and unique link required')
        if _links(data,3)!=[3000]or field(data,4054,117)!=0 or not 0<field(data,4054,77)<=600000:raise ValueError('neutral zero-bank positive-ground gateway context required')
        if any(field(data,r,85)!=0 for r in range(4052,4152)if r not in(4052,4054,4150,4151)):raise ValueError('unmodeled active ordinary planet')
        if any(field(data,r,89)!=0 for r in range(3052,4052)):raise ValueError('tax-funded hiring remains excluded')
    for r in range(2,52):
        for o in range(41,137,4):
            if field(b,r,o)not in((0,-1)if o==109 else(0,))or field(world,r,o)!=(-1 if o==109 else 0):raise ValueError('inactive human ranks required')
    if type(events)not in(tuple,list)or type(mercenary)is not dict:raise ValueError('modeled Xannor events and Mercenary result required')
    previous=1;dead=set();losses={-1:0,-2:0,0:0};pickup=0
    for e in events:
        if type(e)is not dict or e.get('kind')!='planet':raise ValueError('only measured fatal home assaults admitted')
        g=e.get('group');sector=e.get('sector');n=_whole(e.get('initial_force'),10000,'Xannor initial force')
        if type(g)is not int or g in dead or not previous<=g<=20 or g<2 or type(sector)is not int or not 8<=sector<=3000 or n==0 or e.get('force')!=0:raise ValueError('source-ordered fatal Xannor group required')
        slot=e.get('planet_slot');title=e.get('planet_name')
        if(slot,title)not in((1,'The Wanderer'),(99,'Mercenary Base')):raise ValueError('measured home defense title required')
        record=4051+slot;owner=0 if slot==1 else-2
        if name(world,record)!=title.encode()or field(world,record,73)!=owner or _links(world,slot)!=[sector]:raise ValueError('actual surviving home title and unique link required')
        ground=_whole(e.get('ground'),600000,'remaining ground');initial=_whole(e.get('initial_ground'),600000,'initial ground')
        if not 0<ground<initial or e.get('ground_spent')!=initial-ground:raise ValueError('positive actual ground spending required')
        previous=g;dead.add(g);losses[-1]+=n
    mevents=mercenary.get('events',());activations=mercenary.get('activations',())
    if type(mevents)not in(tuple,list)or type(activations)not in(tuple,list):raise ValueError('explicit Mercenary events and activations required')
    totals=[_physical(b),_physical(world)];current=totals[0][-2];visited=set();prior_kind=None
    for e in mevents:
        if type(e)is not dict:raise ValueError('modeled Mercenary event required')
        kind=e.get('kind');n=_whole(e.get('initial_force'),100000,'initial Mercenaries');m=_whole(e.get('force'),100000,'remaining Mercenaries');sector=e.get('sector')
        if not n or n!=current or sector!=3000:raise ValueError('gateway event pre-force follows actual phase ledger')
        if kind=='mercenary-mine':
            if kind in visited or prior_kind is not None:raise ValueError('mine action must precede gateway pickup or combat')
            loss=_whole(e.get('losses'),n,'actual mine casualty')
            old=_whole(e.get('initial_mines'),3,'initial gateway mines');remaining=_whole(e.get('mines'),old,'remaining gateway mines')
            if not loss or n-m!=loss or not old or not remaining<old or e.get('mines_spent')!=old-remaining:raise ValueError('actual bounded mine loss/expenditure required')
            if field(b,3051,129)!=old or field(world,3051,129)!=remaining:raise ValueError('mine receipts bind actual saved residue')
            losses[-2]+=loss
        elif kind=='mercenary-attack':
            x=_whole(e.get('initial_defenders'),10000,'initial Xannor defenders');d=_whole(e.get('defenders'),x,'remaining Xannor defenders')
            if kind in visited or prior_kind not in(None,'mercenary-mine')or e.get('owner')!=-1 or e.get('defender_name')!='The Xannor' or not x or not m or d!=0 or not m<=n:raise ValueError('bounded surviving Mercenary offense before any pickup required')
            if e.get('losses')!=n-m or e.get('defender_losses')!=x or field(b,3051,81)!=x or field(b,3051,85)!=-1:raise ValueError('actual capped offense casualties required')
            losses[-1]+=x;losses[-2]+=n-m
        elif kind=='mercenary-pickup':
            amount=_whole(e.get('pickup'),37,'actual gateway stock pickup')
            if kind in visited or prior_kind not in(None,'mercenary-mine')or e.get('captured')is not True or e.get('planet_slot')!=3 or e.get('planet_name')!='Gateway Cache' or m!=n+amount:raise ValueError('one actual neutral capture and exact fighter pickup required')
            if field(b,3051,81)!=0 or field(world,4054,129)!=0 or field(world,3051,81)!=m or field(world,3051,85)!=-2:raise ValueError('pickup terminates at actual gateway and clears stock')
            pickup+=amount
        else:raise ValueError('unmeasured Mercenary outcome')
        current=m;visited.add(kind);prior_kind=kind
    for a in activations:
        if type(a)is not dict:raise ValueError('modeled activation row required')
        origin=a.get('origin');target=a.get('target')
        if a.get('held')is True:
            if type(origin)is not int or not 8<=origin<=3000:raise ValueError('bounded held activation origin required')
            _whole(a.get('force'),100000,'held activation force');continue
        if type(origin)is not int or not 8<=origin<=3000 or type(target)is not int or not 8<=target<=3000:raise ValueError('bounded activation origin/target required')
        _whole(a.get('force'),100000,'activation force');_whole(a.get('final_force'),100000,'activation final force')
    final=[s for s in range(1,3001)if field(world,51+s,81)>0 and field(world,51+s,85)==-2]
    if mercenary.get('final_sectors')!=final or mercenary.get('force')!=totals[1][-2] or current!=totals[1][-2]:raise ValueError('modeled final Mercenaries differ from physical world')
    if any(totals[1][o]+losses[o]-(pickup if o==-2 else 0)!=totals[0][o]for o in totals[0]):raise ValueError('modeled events must conserve physical faction force plus stock pickup')
    rates=[field(b,4054,o)for o in(45,49,53)]
    if any(not math.isfinite(v)or not 0<=v<=10 for v in rates):raise ValueError('bounded gateway rates required')
    elapsed=F32(F32(field(world,4054,41)-field(b,4054,41))+F32(F32(field(world,4054,89)-field(b,4054,89))/1440))
    if not .999<=elapsed<=1.001:raise ValueError('measured one-day gateway production clock required')
    rate=math.floor(F32(F32(rates[0]+rates[1])+rates[2]))
    produced=F32(field(b,4054,129)+F32(F32(rate)*elapsed))
    if produced-pickup!=field(world,4054,129):raise ValueError('stock production and exact pickup debit must reconcile')
    if pair==(309,310)and mevents:raise ValueError('only measured held/empty second-day gateway actions admitted')
    return totals,losses,tuple(mevents),pickup


def _news(original,date,clock,events,mercenary_events):
    lines=[clock.encode()+b' '+date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)'),literal(original,b'  -  Xannor report:'),literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.')]
    for e in events:
        lines.extend([original_string(original,0x809e)+b' '+str(e['initial_force']).encode()+original_string(original,0x8b70)+b'"'+e['planet_name'].encode()+b'"',original_string(original,0x8bac)+original_string(original,0x8bc4)])
    lines.append(literal(original,b'  -  Mercenary Report:'))
    for e in mercenary_events:
        n=str(e['initial_force']).encode();kind=e['kind']
        if kind=='mercenary-attack':
            lines.extend([original_string(original,0x809e)+b' '+n+original_string(original,0x88e2)+b' '+str(e['initial_defenders']).encode()+original_string(original,0x88fc)+e['defender_name'].encode()+b'!',original_string(original,0x8934)+original_string(original,0x8922)])
        elif kind=='mercenary-mine':
            lines.append(original_string(original,0x809e)+b' '+n+original_string(original,0x8804)+b' '+str(e['sector']).encode()+original_string(original,0x8008))
            lines.append(original_string(original,0x8830)if not e['force']else original_string(original,0x8856)+b' '+str(e['losses']).encode()+original_string(original,0x886e))
        else:
            title=e['planet_name'].encode();prefix=original_string(original,0x81fe)+b' '+n
            lines.append(prefix+original_string(original,0x887c)+title+original_string(original,0x8008))
            if e['pickup']:
                lines.append(prefix+original_string(original,0x889e)+b' '+str(e['pickup']).encode()+original_string(original,0x88b6)+title+original_string(original,0x8008))
    return CRLF.join(lines)+CRLF+EOF


def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,created=(),events=(),mercenary=None):
    """Publish derived physical scores, ordered public outcomes and empty inbox."""
    if created!=():raise ValueError('gateway children retain all homes')
    if any(type(d)is not datetime.date for d in(news_date,score_date)):raise ValueError('separate source text dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    if mercenary is None:raise ValueError('explicit modeled Mercenary result required')
    totals,losses,mevents,pickup=_admit(before_files,after_world,events,mercenary)
    serial=field(after_world,1,81)
    if news_date!=datetime.date(2026,1,1)+datetime.timedelta(days=serial-1)or score_date!=news_date:raise ValueError('measured source publication calendar required')
    original=original_literals();scores={o:100*totals[1][o]for o in(-1,-2)}
    board,percentages=_scoreboard(original,score_date,score_clock,scores)
    result={'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],'YTRMSG.DAT':b'','YTNEWS.DAT':_news(original,news_date,news_clock,events,mevents),'YTSCORE.ASC':board}
    return result,dict(created=[],scores=scores,percentages=percentages,physical=totals,modeled_losses=losses,stock_pickup=pickup,public_events=len(events)+len(mevents),private_bytes=0)
