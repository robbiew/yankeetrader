"""Before-only public files for the bounded evolved occupied-combat children.

Only immutable original YTMAINT literals are opened. World bytes, fatal Xannor
assault events and Mercenary activation/combat results come from record synthesis.
Printed initial force and actual capped casualties are deliberately separate.
"""
import datetime
import math
from replay_maintenance_aux import CRLF,EOF,_matrix_clock,field,literal,name,original_literals,original_string
from replay_maintenance_occupied_aux import _scoreboard

FILES={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}
SIZE=137
HOMES=((4052,b'The Wanderer',0),(4150,b'Mercenary Base',-2),(4151,b'Xannoron',-1))


def _whole(value,upper,label):
    if type(value)not in(int,float)or not math.isfinite(value)or value!=int(value)or not 0<=value<=upper:
        raise ValueError('bounded whole '+label+' required')
    return int(value)


def _physical(world):
    totals={-1:0,-2:0,0:0}
    for sector in range(1,3001):
        n=_whole(field(world,51+sector,81),100000,'physical sector force')
        owner=field(world,51+sector,85)
        if owner not in totals:raise ValueError('unknown physical sector owner')
        totals[owner]+=n
    if totals[-1]>10000 or totals[-2]>100000 or totals[0]>37:raise ValueError('unmeasured faction inventory')
    return totals


def _links(world,slot):
    return [s for s in range(1,3001)if field(world,51+s,93)==slot]


def _admit(before_files,world,events,mercenary):
    if type(before_files)is not dict or set(before_files)!=FILES or any(type(v)is not bytes for v in before_files.values())or type(world)is not bytes:
        raise ValueError('six immutable evolved before files and modeled world required')
    b=before_files['YTDATA.DAT']
    if len(b)!=4151*SIZE or len(world)!=len(b)or before_files['YTRMSG.DAT']:
        raise ValueError('complete worlds and empty private before stream required')
    if(field(b,1,81),field(world,1,81))not in((306,307),(307,308)):raise ValueError('measured evolved combat day pair required')
    for data in(b,world):
        if any(field(data,1,o)!=v for o,v in((53,51),(57,3051),(61,4051),(93,4151))):raise ValueError('default record geometry required')
        if data[:11]!=b'YTSCORE.ASC'or field(data,1,41)!=11:raise ValueError('default scoreboard path required')
        for r,title,owner in HOMES:
            if name(data,r)!=title or field(data,r,73)!=owner or len(_links(data,r-4051))!=1:raise ValueError('existing named home and unique link required')
        if field(data,4053,85):
            if name(data,4053)!=b'Route Haven'or field(data,4053,73)!=0 or _links(data,2)!=[854]:raise ValueError('neutral Route Haven context required')
        elif _links(data,2):raise ValueError('inactive ordinary slot retains link')
        if any(field(data,r,85)!=0 for r in range(4052,4152)if r not in(4052,4053,4150,4151)):raise ValueError('unmodeled active ordinary planet')
        if any(field(data,r,89)!=0 for r in range(3052,4052)):raise ValueError('tax-funded hiring remains excluded')
    if bool(field(b,4053,85))!=bool(field(world,4053,85)):raise ValueError('ordinary planet creation/destruction remains excluded')
    for r in range(2,52):
        for o in range(41,137,4):
            if field(b,r,o)not in((0,-1)if o==109 else(0,))or field(world,r,o)!=(-1 if o==109 else 0):raise ValueError('inactive human ranks required')
    if type(events)not in(tuple,list)or type(mercenary)is not dict:raise ValueError('modeled Xannor events and Mercenary result required')
    previous=1;dead=set();losses={-1:0,-2:0,0:0}
    for e in events:
        if type(e)is not dict or e.get('kind')!='planet':raise ValueError('only measured fatal Route Haven assaults admitted')
        g=e.get('group');s=e.get('sector');n=_whole(e.get('initial_force'),10000,'Xannor initial force')
        if type(g)is not int or g in dead or not previous<=g<=20 or g<2 or s!=854 or n==0 or e.get('force')!=0:raise ValueError('source-ordered fatal Xannor group required')
        if e.get('planet_name')!='Route Haven'or e.get('planet_slot')!=2 or name(world,4053)!=b'Route Haven'or field(world,4053,73)!=0 or _links(world,2)!=[854]:raise ValueError('actual neutral assault title/link required')
        ground=_whole(e.get('ground'),600000,'remaining ground');initial=_whole(e.get('initial_ground'),600000,'initial ground')
        if not 0<ground<initial or e.get('ground_spent')!=initial-ground:raise ValueError('positive actual ground spending required')
        previous=g;dead.add(g);losses[-1]+=n
    mevents=mercenary.get('events',());activations=mercenary.get('activations',())
    if type(mevents)not in(tuple,list)or type(activations)not in(tuple,list):raise ValueError('explicit Mercenary events and activations required')
    for e in mevents:
        if type(e)is not dict or e.get('kind')!='mercenary-attack'or e.get('owner')!=-1 or e.get('defender_name')!='The Xannor':raise ValueError('only measured Mercenary offense against Xannor admitted')
        n=_whole(e.get('initial_force'),100000,'initial Mercenaries');x=_whole(e.get('initial_defenders'),10000,'initial Xannor defenders')
        m=_whole(e.get('force'),n,'remaining Mercenaries');d=_whole(e.get('defenders'),x,'remaining Xannor defenders');s=e.get('sector')
        if not n or not x or not m or d!=0 or type(s)is not int or not 8<=s<=3000:raise ValueError('bounded Mercenary victory required')
        if e.get('losses')!=n-m or e.get('defender_losses')!=x:raise ValueError('actual capped casualties must differ from public initial counts')
        losses[-1]+=x;losses[-2]+=n-m
    for a in activations:
        if type(a)is not dict:raise ValueError('modeled activation row required')
        origin=a.get('origin');target=a.get('target')
        if a.get('held')is True:
            if type(origin)is not int or not 8<=origin<=3000:raise ValueError('bounded held activation origin required')
            _whole(a.get('force'),100000,'held activation force')
            continue
        if type(origin)is not int or not 8<=origin<=3000 or type(target)is not int or not 8<=target<=3000:raise ValueError('bounded activation origin/target required')
        _whole(a.get('force'),100000,'activation force');_whole(a.get('final_force'),100000,'activation final force')
    totals=[_physical(b),_physical(world)]
    final=[s for s in range(1,3001)if field(world,51+s,81)>0 and field(world,51+s,85)==-2]
    if mercenary.get('final_sectors',final)!=final or mercenary.get('force',totals[1][-2])!=totals[1][-2]:raise ValueError('modeled final Mercenary publication differs from physical world')
    if any(totals[1][o]+losses[o]!=totals[0][o]for o in totals[0]):raise ValueError('modeled events must conserve physical faction force')
    return totals,losses,tuple(mevents)


def _news(original,date,clock,events,mercenary_events):
    lines=[clock.encode()+b' '+date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)'),literal(original,b'  -  Xannor report:'),literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.')]
    for e in events:
        lines.extend([original_string(original,0x809e)+b' '+str(e['initial_force']).encode()+original_string(original,0x8b70)+b'"'+e['planet_name'].encode()+b'"',original_string(original,0x8bac)+original_string(original,0x8bc4)])
    lines.append(literal(original,b'  -  Mercenary Report:'))
    for e in mercenary_events:
        lines.extend([original_string(original,0x809e)+b' '+str(e['initial_force']).encode()+original_string(original,0x88e2)+b' '+str(e['initial_defenders']).encode()+original_string(original,0x88fc)+e['defender_name'].encode()+b'!',original_string(original,0x8934)+original_string(original,0x8922)])
    return CRLF.join(lines)+CRLF+EOF


def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,created=(),events=(),mercenary=None):
    """Publish derived physical scores, public events and bounded empty inbox."""
    if created!=():raise ValueError('evolved combat children retain all homes')
    if any(type(d)is not datetime.date for d in(news_date,score_date)):raise ValueError('separate source text dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    if mercenary is None:mercenary={'events':(),'activations':()}
    totals,losses,mevents=_admit(before_files,after_world,events,mercenary)
    serial=field(after_world,1,81)
    if news_date!=datetime.date(2026,1,1)+datetime.timedelta(days=serial-1)or score_date!=news_date:raise ValueError('measured source publication calendar required')
    original=original_literals();scores={o:100*totals[1][o]for o in(-1,-2)}
    board,percentages=_scoreboard(original,score_date,score_clock,scores)
    result={'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],'YTRMSG.DAT':b'','YTNEWS.DAT':_news(original,news_date,news_clock,events,mevents),'YTSCORE.ASC':board}
    return result,dict(created=[],scores=scores,percentages=percentages,physical=totals,modeled_losses=losses,public_events=len(events)+len(mevents),private_bytes=0)
