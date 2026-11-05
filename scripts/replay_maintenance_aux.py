"""Pure bounded synthesis of initial-maintenance DOS auxiliary files.

The model reads before-inputs, a separately modeled post-maintenance world and
calendar/clock inputs. It does not load completed target files or transcripts.
Literal messages and PRINT USING masks come from the immutable original binary,
not an after-file template. Only the recovered all-inactive-player bootstrap
branch is admitted; general rankings, message compression and event news are not
implemented here.
"""
import datetime
import hashlib
from pathlib import Path
import re
import struct

from verify_maintenance_rng import mbf

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_SHA='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
RECORD_SIZE=137
CRLF=b'\r\n'
EOF=b'\x1a'


def original_literals():
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:raise ValueError('immutable original YTMAINT identity differs')
    return original


def literal(original,needle):
    """Recover a unique native length-prefixed string using a descriptive seed."""
    at=original.find(needle)
    if at<4 or original.count(needle)!=1:raise ValueError('missing or ambiguous original literal')
    length=struct.unpack_from('<H',original,at-4)[0]
    value=original[at:at+length]
    if not len(needle)<=length<=512 or len(value)!=length or not value.startswith(needle):
        raise ValueError('native literal descriptor differs')
    return value


def field(world,record,offset):
    start=(record-1)*RECORD_SIZE+offset
    return mbf(world[start:start+4])


def name(world,record):
    start=(record-1)*RECORD_SIZE
    length=field(world,record,85)
    if length!=int(length)or not 0<=length<=41:raise ValueError('bounded name length differs')
    return world[start:start+int(length)]


def using(mask,values):
    """The nonnegative integer/two-decimal subset used by this bootstrap board."""
    fields=list(re.finditer(rb'[#,.]+',mask))
    if len(fields)!=len(values):raise ValueError('unsupported native PRINT USING mask')
    result=bytearray();last=0
    for match,value in zip(fields,values):
        pattern=match.group();width=len(pattern)
        if value<0:raise ValueError('negative PRINT USING values are outside this model')
        if b'.'in pattern:
            places=len(pattern.rsplit(b'.',1)[1]);text=f'{value:.{places}f}'.encode('ascii')
        else:
            if value!=int(value):raise ValueError('fractional score is outside this model')
            text=(f'{int(value):,}'if b','in pattern else str(int(value))).encode('ascii')
        if len(text)>width:raise ValueError('PRINT USING overflow is outside this model')
        result.extend(mask[last:match.start()]);result.extend(text.rjust(width,b' '));last=match.end()
    result.extend(mask[last:]);return bytes(result)


def npc_scores(world):
    scores={-1:0,-2:0}
    for sector in range(1,3001):
        record=51+sector;force=field(world,record,81);owner=field(world,record,85)
        if force<0 or force!=int(force):raise ValueError('noninteger/negative sector force is outside this model')
        if owner in scores:scores[owner]+=100*int(force)
    # The all-inactive bootstrap reference has exactly10000 Xannor fighters and
    # no Mercenary deployment. Do not claim general NPC normalization/MBF parity.
    if scores!={-1:1000000,-2:0}:raise ValueError('only the recovered bootstrap NPC scoreboard is supported')
    return scores[-1],scores[-2]


def scoreboard(original,world,date,clock):
    xannor,mercenary=npc_scores(world)
    # Native855d..8596 selects an NPC denominator when the human leader is zero;
    # here Xannor is the sole positive NPC score, so the fractions are exact.
    leader=max(xannor,mercenary)
    mask=literal(original,b'  ###,###,###,###  ####.##%')
    row=using(mask,[xannor,100*xannor/leader,mercenary,100*mercenary/leader])
    lines=[b'',literal(original,b'Y a n k e e   T r a d e r   S c o r e b o a r d'),b'',
           literal(original,b'Last updated at: ')+date.strftime('%m-%d-%Y').encode()+b' '+clock.encode(),b'',
           literal(original,b'Rank  Rank%        Score        Team   Ports   Player'),
           literal(original,b'==== ======= ================= ====== ======= ================================'),b'',
           literal(original,b'T e a m   R a n k i n g s'),b'',
           literal(original,b'Rank  Rank%        Score        Team   Team Name'),
           literal(original,b'==== ======= ================= ====== ========================================'),b'',
           literal(original,b'N o n  -  H u m a n   P l a y e r s'),b'',
           literal(original,b'    The Xannor       Rank%     The Mercenaries'),
           literal(original,b'================== =========  ================='),row,b'']
    return CRLF.join(lines)+CRLF+EOF


def news(original,before,after,date,clock):
    lines=[clock.encode()+b' '+date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)')]
    for slot,expected in [(1,b'The Wanderer'),(99,b'Mercenary Base'),(100,b'Xannoron')]:
        record=4051+slot
        if field(before,record,85)!=0 or name(after,record)!=expected:
            raise ValueError('only the missing-NPC bootstrap news branches are supported')
    lines.extend([literal(original,b'  -  The Wanderer is missing or has been destroyed!'),
                  literal(original,b'  -  The Wanderer regenerated with P.H.O.E.N.I.X. device!'),
                  literal(original,b'  -  The Xannor have made a Planet!'),
                  literal(original,b'The Xannor home base now has a planet!'),
                  literal(original,b'  -  Xannor report:'),
                  literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.'),
                  literal(original,b'  -  Mercenary Report:'),
                  literal(original,b'  -  The Mercenaries have built a home base using a captured Genesis Device!')])
    return CRLF.join(lines)+CRLF+EOF


def synthesize(before_files,after_world,date,clock='00:00:00',*,score_clock=None):
    """Return five synthesized auxiliary files; never consult after-target bytes.

    `after_world` must be the caller's independently modeled world, not an oracle
    loaded here. The caller retains responsibility for proving that world model.
    News and scoreboard clocks are explicit because the original samples them at
    different phases. Only the zero-player first-maintenance branch is supported.
    """
    if isinstance(date,str):date=datetime.date.fromisoformat(date)
    if not isinstance(date,datetime.date):raise ValueError('a calendar date is required')
    score_clock=clock if score_clock is None else score_clock
    for value in (clock,score_clock):
        if not re.fullmatch(r'\d{2}:\d{2}:\d{2}',value):raise ValueError('an exact HH:MM:SS clock is required')
        datetime.time.fromisoformat(value)
    if not {'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'}<=set(before_files):raise ValueError('three original before-inputs are required')
    if before_files.get('YTRMSG.DAT',b''):raise ValueError('nonempty message compression is outside this model')
    before=before_files['YTDATA.DAT']
    if len(before)!=4151*RECORD_SIZE or len(after_world)!=len(before):raise ValueError('4151 native records are required')
    for record in range(2,52):
        if field(before,record,85)!=0 or field(after_world,record,85)!=0:
            raise ValueError('active-player rankings/events are outside this model')
        for offset in range(41,137,4):
            if field(before,record,offset)!=0:
                raise ValueError('populated inactive-player assets are outside this model')
            value=field(after_world,record,offset)
            if value not in ((0,-1)if offset==109 else(0,)):
                raise ValueError('unexpected inactive-player asset changes are outside this model')
    for slot in range(1,101):
        record=4051+slot
        if field(before,record,85)!=0:
            raise ValueError('pre-existing active planets are outside this bootstrap model')
        if slot not in (1,99,100)and field(after_world,record,85)!=0:
            raise ValueError('additional active planets are outside this bootstrap model')
    for world in (before,after_world):
        for sector in range(1,3001):
            if field(world,51+sector,81)>0 and field(world,51+sector,85)!=-1:
                raise ValueError('non-Xannor deployments are outside this bootstrap model')
    length=field(before,1,41)
    if length!=int(length)or not 1<=length<=41:raise ValueError('scoreboard path length differs')
    path=before[:int(length)].decode('ascii')
    if path.upper() in {'YTNEWS.DAT','YTYNEWS.DAT','YTNAME.DAT','YTRMSG.DAT','YTDATA.DAT'}:
        raise ValueError('aliased scoreboard path is outside this model')
    original=original_literals()
    return {'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],
            'YTRMSG.DAT':b'','YTNEWS.DAT':news(original,before,after_world,date,clock),
            path:scoreboard(original,after_world,date,score_clock)}
