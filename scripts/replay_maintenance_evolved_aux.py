"""Before-only auxiliary publication for the bounded evolved maintenance chain.

The caller supplies an independently synthesized world and source text clocks.
Only original YTMAINT literals are read; no target, transcript or captured state
is opened here. The historical bootstrap/occupied formatters remain unchanged.
"""
import datetime
import math

from replay_maintenance_aux import (
    CRLF, EOF, _matrix_clock, field, literal, name, original_literals, scoreboard,
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


def _admit(before_files,world,created):
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
        if total!=10000:raise ValueError('exact physical force conservation required')
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


def _news(original,date,clock,created):
    lines=[clock.encode()+b' '+date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)')]
    if 'wanderer'in created:
        lines.extend([literal(original,b'  -  The Wanderer is missing or has been destroyed!'),literal(original,b'  -  The Wanderer regenerated with P.H.O.E.N.I.X. device!')])
    if 'xannoron'in created:
        lines.extend([literal(original,b'  -  The Xannor have made a Planet!'),literal(original,b'The Xannor home base now has a planet!')])
    lines.extend([literal(original,b'  -  Xannor report:'),literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.'),literal(original,b'  -  Mercenary Report:')])
    if 'base'in created:
        lines.append(literal(original,b'  -  The Mercenaries have built a home base using a captured Genesis Device!'))
    return CRLF.join(lines)+CRLF+EOF


def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,created=()):
    """Return five auxiliary files and audit data from before/modeled state.

    ``created`` is derived by the parent NPC path, then checked here against
    actual before-home presence. It cannot suppress an unsupported branch or
    publish restoration news for an existing home. Separate news/score clocks
    follow their original writers rather than a shared clock approximation.
    """
    if any(type(value)is not datetime.date for value in(news_date,score_date)):
        raise ValueError('separate explicit news and scoreboard calendar dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    before=_admit(before_files,after_world,created);original=original_literals()
    result={'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],'YTRMSG.DAT':b'',
            'YTNEWS.DAT':_news(original,news_date,news_clock,created),
            'YTSCORE.ASC':scoreboard(original,after_world,score_date,score_clock)}
    return result,dict(created=list(created),scores={-1:1000000,-2:0},physical_force=10000,
                       private_bytes=0,rotated_news_bytes=len(before_files['YTNEWS.DAT']))
