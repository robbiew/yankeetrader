"""Before-only auxiliary publication for the bounded evolved clock/date children.

The caller supplies an independently synthesized world and source text clocks.
Only original YTMAINT literals are read; no target, transcript or captured state
is opened here. The historical bootstrap/occupied formatters remain unchanged.
"""
import datetime
import math

from replay_maintenance_aux import (
    CRLF, EOF, _matrix_clock, field, literal, name, original_literals, original_string,
)

FILES={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}
INITIAL={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'}
HOMES=(('wanderer',1,b'The Wanderer',0),('xannoron',100,b'Xannoron',-1),('base',99,b'Mercenary Base',-2))
CREATED=tuple(row[0]for row in HOMES)
SIZE=137


def _links(world):
    links={1:[],2:[],99:[],100:[]}
    for sector in range(1,3001):
        slot=field(world,51+sector,93)
        if slot!=int(slot)or slot<0 or (slot and slot not in links):
            raise ValueError('only measured active-planet sector references are recovered')
        if slot:links[int(slot)].append(sector)
    return links


def _admit(before_files,world,created,events):
    if (type(before_files)is not dict or set(before_files)not in(INITIAL,FILES)or
            any(type(value)is not bytes for value in before_files.values())or type(world)is not bytes):
        raise ValueError('three initial or six evolved raw before files and modeled world required')
    if type(created)is not tuple or created not in((),CREATED):
        raise ValueError('explicit measured source-ordered creation mask required')
    if before_files.get('YTRMSG.DAT',b''):
        raise ValueError('nonempty private-message compression is outside this chain')
    before=before_files['YTDATA.DAT']
    if len(before)!=4151*SIZE or len(world)!=len(before):
        raise ValueError('complete default before and independently modeled worlds required')
    for data in(before,world):
        if any(field(data,1,o)!=v for o,v in((53,51),(57,3051),(61,4051),(93,4151))):
            raise ValueError('default physical record geometry required')
        if data[:11]!=b'YTSCORE.ASC'or field(data,1,41)!=11:
            raise ValueError('fixed unaliased original scoreboard path required')
    for record in range(2,52):
        for offset in range(41,137,4):
            old=field(before,record,offset);new=field(world,record,offset)
            if old not in((0,-1)if offset==109 else(0,))or new!=(-1 if offset==109 else 0):
                raise ValueError('only inactive humans and exact rank publication are recovered')
    totals=[]
    for data in(before,world):
        if any(field(data,record,89)!=0 for record in range(3052,4052)):
            raise ValueError('tax-funded hiring/news is outside this chain')
        total=0
        for sector in range(1,3001):
            force=field(data,51+sector,81);owner=field(data,51+sector,85)
            if not math.isfinite(force)or force!=int(force)or not 0<=force<=10000:
                raise ValueError('bounded whole physical Xannor force required')
            if owner not in(0,-1,-2)or(force and owner!=-1):
                raise ValueError('only measured physical Xannor deployments are recovered')
            total+=int(force)
        if not 0<total<=10000:raise ValueError('bounded positive physical force required')
        totals.append(total)
    if totals[1]+sum(e['initial_force'] for e in events)!=totals[0]:
        raise ValueError('modeled fatal losses must conserve physical force')
    before_links=_links(before);after_links=_links(world)
    expected=[]
    for key,slot,text,owner in HOMES:
        record=4051+slot;was_active=field(before,record,85)!=0
        if was_active:
            if name(before,record)!=text or field(before,record,73)!=owner or len(before_links[slot])!=1:
                raise ValueError('existing named home requires actual title and unique source link')
        else:
            if before_links[slot]:raise ValueError('missing home cannot retain a stale sector link')
            expected.append(key)
        if name(world,record)!=text or field(world,record,73)!=owner or len(after_links[slot])!=1:
            raise ValueError('modeled home must have its actual name, owner and unique link')
    if tuple(expected)!=created:
        raise ValueError('creation mask must follow actual missing before-home predicates')
    if bool(created)!=(set(before_files)==INITIAL):
        raise ValueError('measured bootstrap/evolved file inventory and home context must agree')
    for data in(before,world):
        record=4053
        if name(data,record)!=b'Convergence Haven'or field(data,record,73)!=-1 or len(_links(data)[2])!=1:
            raise ValueError('actual named friendly convergence planet must survive')
        if any(field(data,4051+slot,85)!=0 for slot in range(1,101)if slot not in(1,2,99,100)):
            raise ValueError('additional active planets are outside this chain')
    return before


def _news(original,date,clock,created,events):
    lines=[clock.encode()+b' '+date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)')]
    if 'wanderer'in created:
        lines.extend([literal(original,b'  -  The Wanderer is missing or has been destroyed!'),literal(original,b'  -  The Wanderer regenerated with P.H.O.E.N.I.X. device!')])
    if 'xannoron'in created:
        lines.extend([literal(original,b'  -  The Xannor have made a Planet!'),literal(original,b'The Xannor home base now has a planet!')])
    lines.extend([literal(original,b'  -  Xannor report:'),literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.'),literal(original,b'  -  Mercenary Report:')])
    if 'base'in created:
        lines.append(literal(original,b'  -  The Mercenaries have built a home base using a captured Genesis Device!'))
    extra=[]
    for e in events:
        if e['kind']=='planet':
            extra.extend([original_string(original,0x809e)+b' '+str(e['initial_force']).encode()+original_string(original,0x8b70)+b'"'+e['planet_name'].encode()+b'"',
                          original_string(original,0x8bac)+original_string(original,0x8bc4)])
        else:
            extra.extend([original_string(original,0x809e)+b' '+str(e['initial_force']).encode()+original_string(original,0x8c6c)+b' '+str(e['sector']).encode()+original_string(original,0x8008),
                          original_string(original,0x8c92)])
    lines[-1:-1]=extra
    return CRLF.join(lines)+CRLF+EOF


def _events(events,world):
    if type(events)not in(tuple,list):raise ValueError('explicit modeled event sequence required')
    previous=1;dead=set()
    for e in events:
        if type(e)is not dict or e.get('kind')not in('planet','mine'):raise ValueError('unknown modeled public event')
        group=e.get('group');sector=e.get('sector');force=e.get('initial_force')
        if type(group)is not int or group in dead or not previous<=group<=20 or group<2:
            raise ValueError('source-ordered unique fatal group events required')
        if type(sector)is not int or not 8<=sector<=3000 or type(force)is not int or not 1<=force<=10000 or e.get('force')!=0:
            raise ValueError('bounded fatal event required')
        previous=group;dead.add(group)
        if e['kind']=='planet':
            slot=e.get('planet_slot');title=e.get('planet_name')
            if (slot,title)not in((1,'The Wanderer'),(99,'Mercenary Base')):
                raise ValueError('only measured positive-ground home assaults admitted')
            rec=4051+slot
            if field(world,51+sector,93)!=slot or name(world,rec)!=title.encode() or field(world,rec,73)!=(0 if slot==1 else -2):
                raise ValueError('actual surviving home title and link required')
            if not 0<e.get('ground',0)<e.get('initial_ground',0):raise ValueError('fatal assault must spend positive ground')
        elif e.get('initial_mines')!=1 or e.get('mines')!=0 or field(world,51+sector,129)!=0:
            raise ValueError('only measured consumed single-mine fatal event admitted')
    return tuple(events)


def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,created=(),events=()):
    """Publish from actual modeled casualties and surviving physical force only."""
    if created!=():raise ValueError('clock children retain all existing homes')
    if any(type(value)is not datetime.date for value in(news_date,score_date)):
        raise ValueError('separate explicit news and scoreboard calendar dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    events=_events(events,after_world)
    _admit(before_files,after_world,created,events)
    original=original_literals()
    from replay_maintenance_occupied_aux import _scoreboard
    force=sum(int(field(after_world,51+s,81))for s in range(1,3001))
    scores={-1:100*force,-2:0}
    board,percentages=_scoreboard(original,score_date,score_clock,scores)
    result={'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],'YTRMSG.DAT':b'',
            'YTNEWS.DAT':_news(original,news_date,news_clock,created,events),'YTSCORE.ASC':board}
    return result,dict(created=[],scores=scores,physical_force=force,modeled_losses=sum(e['initial_force']for e in events),
                       public_events=len(events),private_bytes=0,rotated_news_bytes=len(before_files['YTNEWS.DAT']))
