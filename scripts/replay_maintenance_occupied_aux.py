"""Before-only auxiliary writers for the bounded active-planet/route profile.

Only the immutable original executable is read. Events and final world bytes are
provided by the independent record synthesis, never parsed from target outputs.
"""
import datetime
from fractions import Fraction
import math

from replay_maintenance_aux import (
    CRLF, EOF, _matrix_clock, field, literal, name, news,
    original_literals, original_string, using,
)

RECORDS=4151
RECORD_SIZE=137
MAX_FORCE=110000


def whole(value,upper,label):
    if type(value)not in(int,float)or not math.isfinite(value)or value!=int(value)or not 0<=value<=upper:
        raise ValueError('bounded whole '+label+' required')
    return int(value)


def _events(events):
    if type(events)not in(list,tuple):raise ValueError('explicit modeled event sequence required')
    losses={-1:0,-2:0};previous=1;typed=[];dead=set()
    for event in events:
        if type(event)is not dict or event.get('kind')not in('planet','defense'):
            raise ValueError('unknown modeled public event')
        group=event.get('group');sector=event.get('sector')
        if type(group)is not int or group in dead or not previous<=group<=20 or group<2 or type(sector)is not int or not 8<=sector<=3000:
            raise ValueError('source-ordered bounded mobile event required')
        previous=group
        initial=whole(event.get('initial_force'),10000,'initial moving force')
        remaining=whole(event.get('force'),initial,'remaining moving force')
        if initial<1:raise ValueError('positive initial mobile force required')
        losses[-1]+=initial-remaining
        if event['kind']=='planet':
            if event.get('planet_name')!='Route Haven' or remaining!=0 or sector!=854:
                raise ValueError('only measured guarded neutral planet deaths are recovered')
        else:
            if event.get('owner')!=-2:raise ValueError('only Mercenary foreign defense events are recovered')
            defenders=whole(event.get('initial_defenders'),100000,'initial defenders')
            surviving=whole(event.get('defenders'),defenders,'remaining defenders')
            if defenders<1 or (remaining==0)==(surviving==0):
                raise ValueError('one surviving side required for retained defense battle')
            xd=whole(event.get('x_damage'),initial+5000,'raw Xannor damage counter')
            md=whole(event.get('defender_damage'),defenders+5000,'raw defender damage counter')
            if not initial-remaining<=xd<=initial-remaining+5000 or not defenders-surviving<=md<=defenders-surviving+5000:
                raise ValueError('raw battle counters must cover actual capped losses')
            losses[-2]+=defenders-surviving
        if remaining==0:dead.add(group)
        typed.append(event)
    if losses[-1]>10000 or losses[-2]>100000:raise ValueError('modeled casualties exceed initial inventory')
    return typed,losses


def _admit(before_files,world,losses,events):
    if type(before_files)is not dict or set(before_files)!={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'} or any(type(v)is not bytes for v in before_files.values())or type(world)is not bytes:
        raise ValueError('three raw before inputs and independently modeled world required')
    before=before_files['YTDATA.DAT']
    if len(before)!=RECORDS*RECORD_SIZE or len(world)!=len(before):raise ValueError('complete default worlds required')
    for data in(before,world):
        if any(field(data,1,o)!=n for o,n in((53,51),(57,3051),(61,4051),(93,4151))):raise ValueError('default record geometry required')
    if before[:11]!=b'YTSCORE.ASC'or field(before,1,41)!=11:raise ValueError('default scoreboard path required')
    for rec in range(2,52):
        for offset in range(41,137,4):
            if field(before,rec,offset)!=0 or field(world,rec,offset)!=(-1 if offset==109 else 0):
                raise ValueError('only inactive human assets/rank publication recovered')
    for slot in range(1,101):
        rec=4051+slot;active=field(before,rec,85)
        if active:
            if slot not in(2,3)or name(before,rec)not in(b'Occupied Haven',b'Second Haven',b'Route Haven')or field(before,rec,73)not in(-1,0):
                raise ValueError('only measured ordinary active planets recovered')
            if field(before,rec,41)!=305 or field(before,rec,77)!=500000 or any(field(before,rec,o)!=1000 for o in(45,49,53))or any(field(before,rec,o)!=0 for o in range(41,137,4)if o not in(41,45,49,53,73,77,85)):
                raise ValueError('only measured clean active-planet before assets recovered')
            if name(world,rec)!=name(before,rec)or field(world,rec,73)!=field(before,rec,73):
                raise ValueError('retained planets must survive with original title')
        elif slot not in(1,99,100)and field(world,rec,85)!=0:
            raise ValueError('new ordinary active planet is outside this profile')
    if any(field(before,r,89)!=0 for r in range(3052,4052)):
        raise ValueError('tax-funded hiring is outside this profile')
    totals=[]
    for data in(before,world):
        owners={-1:0,-2:0,0:0}
        for sector in range(1,3001):
            force=whole(field(data,51+sector,81),MAX_FORCE,'physical sector force');owner=field(data,51+sector,85)
            if owner not in owners:raise ValueError('unknown physical owner outside this profile')
            owners[owner]+=force
        if sum(owners.values())>MAX_FORCE:raise ValueError('physical force exceeds admitted inventory')
        totals.append(owners)
    if totals[0][-1]!=10000 or totals[0][-2]not in(0,37,100000)or totals[0][0]not in(0,37):
        raise ValueError('bounded retained initial force inventory required')
    if any(totals[1][owner]+losses.get(owner,0)!=totals[0][owner]for owner in(-1,-2,0)):
        raise ValueError('modeled public casualties must conserve each physical faction')
    for event in events:
        if event['kind']=='planet':
            slot=field(before,51+event['sector'],93)
            if slot!=2 or name(before,4053)!=b'Route Haven'or field(before,4053,73)!=0:
                raise ValueError('modeled attack requires actual neutral Route Haven context')
        elif field(before,51+event['sector'],85)!=-2:
            raise ValueError('modeled defense requires actual Mercenary before-context')
    return before,{owner:100*totals[1][owner]for owner in(-1,-2)},totals


def _scoreboard(original,date,clock,scores):
    leader=max(scores.values())
    if not 0<leader<=100*MAX_FORCE:raise ValueError('positive bounded NPC denominator required')
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


def _news(original,before,world,date,clock,events):
    lines=news(original,before,world,date,clock).removesuffix(EOF).split(CRLF)
    if lines[-1]!=b'':raise ValueError('original bootstrap news framing differs')
    lines.pop();extra=[]
    for event in events:
        if event['kind']=='planet':
            extra.extend([original_string(original,0x809e)+b' '+str(event['initial_force']).encode()+original_string(original,0x8b70)+b'"'+event['planet_name'].encode()+b'"',
                          original_string(original,0x8bac)+original_string(original,0x8bc4)])
        else:
            suffix=0x8cc8 if event['defenders']==0 else 0x8cdc
            extra.append(original_string(original,0x803e)+original_string(original,0x8cb2)+original_string(original,0x8afc)+b' '+str(event['x_damage']).encode()+original_string(original,0x8b06)+b' '+str(event['defender_damage']).encode()+original_string(original,0x8cc2)+original_string(original,suffix))
    lines[-2:-2]=extra
    return CRLF.join(lines)+CRLF+EOF


def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,events=()):
    if any(type(d)is not datetime.date for d in(news_date,score_date)):raise ValueError('explicit separate calendar dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    events,losses=_events(events);before,scores,totals=_admit(before_files,after_world,losses,events)
    original=original_literals();board,percentages=_scoreboard(original,score_date,score_clock,scores)
    result={'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],'YTRMSG.DAT':b'',
            'YTNEWS.DAT':_news(original,before,after_world,news_date,news_clock,events),'YTSCORE.ASC':board}
    return result,dict(scores=scores,percentages=percentages,physical=totals,modeled_losses=losses,public_events=len(events),private_bytes=0)
