"""Before-only public files and force ledgers for the composed hiring controls."""
import datetime
from replay_maintenance_aux import field,name,original_literals,original_string,literal,CRLF,EOF,_matrix_clock
from replay_maintenance_occupied_aux import _scoreboard
from replay_maintenance_survivor_aux import _physical,_links
from replay_maintenance_tax_hiring_rules import admit_treasuries
from replay_qb_graph import mbf

FILES={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}


def _admit(before_files,world,events,mercenary,taxation,hiring):
    if type(before_files)is not dict or set(before_files)!=FILES or any(type(v)is not bytes for v in before_files.values())or type(world)is not bytes or len(world)!=4151*137:
        raise ValueError('six immutable before files and full modeled world required')
    before=before_files['YTDATA.DAT'];admit_treasuries(before);admit_treasuries(world)
    if before_files['YTRMSG.DAT']or(field(before,1,81),field(world,1,81))not in((308,309),(309,310)):
        raise ValueError('measured empty inbox and two evolved day pairs required')
    for data in(before,world):
        if any(field(data,1,o)!=n for o,n in((53,51),(57,3051),(61,4051),(93,4151))):raise ValueError('default geometry required')
        for rec,title,owner in((4052,b'The Wanderer',0),(4150,b'Mercenary Base',-2),(4151,b'Xannoron',-1)):
            if name(data,rec)!=title or field(data,rec,73)!=owner or len(_links(data,rec-4051))!=1:raise ValueError('unique existing original homes required')
        if any(field(data,r,85)for r in range(4052,4152)if r not in(4052,4150,4151)):raise ValueError('new ordinary planets excluded')
        if any(field(data,r,85)for r in range(2,52)):raise ValueError('active human players excluded')
    tax=sum(int(field(before,r,89)//10)for r in range(3053,4052))
    if type(taxation)is not dict or taxation.get('tax')!=tax:raise ValueError('tax ledger must bind before-state debit')
    for r in range(3053,4052):
        at=(r-1)*137+89;balance=field(before,r,89)
        expected=mbf.enc(balance-int(balance//10))if balance else before[at:at+4]
        if world[at:at+4]!=expected:raise ValueError('exact saved treasury debit or raw zero residue differs')
    n=tax//10;groups=0 if n==0 else 1 if n<10 else 10;size=0 if n==0 else n if n<10 else n//10
    if type(hiring)is not dict or(hiring.get('groups'),hiring.get('group_size'),hiring.get('hired'))!=(groups,size,groups*size):raise ValueError('tax-funded group allocation differs')
    placements=hiring.get('placements')
    if type(placements)is not list or len(placements)!=groups or len({p['sector']for p in placements})!=groups:raise ValueError('complete unique hiring placement ledger required')
    for p in placements:
        if p['force']!=size or not 2<=p['sector']<=3000 or not p['attempts']or p['attempts'][-1]!=p['sector']:raise ValueError('source-derived hiring placements required')
    losses={-1:0,-2:0,0:0}
    for e in events:
        if e['kind']=='mine':
            if e['force']!=0 or e['losses']!=e['initial_force']:raise ValueError('only fatal Xannor mine branch admitted')
            losses[-1]+=e['losses']
        elif e['kind']=='defense':
            if e['force']!=max(0,e['initial_force']-e['x_damage'])or e['defenders']!=max(0,e['initial_defenders']-e['defender_damage']):raise ValueError('capped actual defense casualties required')
            losses[-1]+=e['initial_force']-e['force'];losses[-2]+=e['initial_defenders']-e['defenders']
        else:raise ValueError('unmeasured Xannor event')
    for e in mercenary['events']:
        if e['kind']=='mercenary-mine':
            if e['force']!=0 or e['losses']!=e['initial_force']:raise ValueError('only fatal Mercenary mine admitted')
            losses[-2]+=e['losses']
        elif e['kind']=='mercenary-attack':
            if e['owner']!=-1 or e['defender_name']!='The Xannor' or e['losses']!=e['initial_force']-e['force']or e['defender_losses']!=e['initial_defenders']-e['defenders']:raise ValueError('actual capped Mercenary offense casualties required')
            losses[-2]+=e['losses'];losses[-1]+=e['defender_losses']
        elif e['kind']!='mercenary-merge':raise ValueError('unmeasured Mercenary event')
    totals=[_physical(before),_physical(world)]
    for owner in totals[0]:
        if totals[1][owner]+losses[owner]!=totals[0][owner]+(hiring['hired']if owner==-2 else 0):raise ValueError('physical force must reconcile hiring and actual losses')
    if mercenary['force']!=totals[1][-2]:raise ValueError('published physical Mercenary force differs')
    return totals,losses


def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,created=(),events=(),mercenary=None,taxation=None,hiring=None,rng_audit=None,rng_source=None,rng_contexts=None):
    if created!=()or any(type(d)is not datetime.date for d in(news_date,score_date)):raise ValueError('retained homes and typed source dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    from replay_maintenance_tax_hiring_rng import verify,verify_hiring
    verify(rng_audit,rng_source,rng_contexts,tuple(events)+tuple(e for e in mercenary['events']if e['kind']!='mercenary-merge'))
    verify_hiring(rng_audit,hiring)
    totals,losses=_admit(before_files,after_world,events,mercenary,taxation,hiring)
    if news_date!=datetime.date(2026,1,1)+datetime.timedelta(days=field(after_world,1,81)-1)or score_date!=news_date:raise ValueError('source publication day differs')
    original=original_literals();s=lambda ds:original_string(original,ds);num=lambda n:str(n).encode()
    lines=[news_clock.encode()+b' '+news_date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)'),literal(original,b'  -  Xannor report:'),literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.')]
    for e in events:
        if e['kind']=='mine':
            lines.extend([s(0x809e)+b' '+num(e['initial_force'])+literal(original,b' Xannor hit sector mines in sector')+b' '+num(e['sector'])+s(0x8008),s(0x8c92)])
        else:
            lines.append(s(0x803e)+s(0x8cb2)+s(0x8afc)+b' '+num(e['x_damage'])+s(0x8b06)+b' '+num(e['defender_damage'])+s(0x8cc2)+literal(original,b'Plyr ftrs dstrd)'))
    if taxation['tax']:lines.append(s(0x8630)+b' '+num(taxation['tax'])+s(0x8654))
    lines.append(literal(original,b'  -  Mercenary Report:'))
    if hiring['hired']:lines.append(s(0x8752)+b' '+num(hiring['hired'])+s(0x8774))
    for e in mercenary['events']:
        if e['kind']=='mercenary-mine':lines.extend([s(0x809e)+b' '+num(e['initial_force'])+s(0x8804)+b' '+num(e['sector'])+s(0x8008),s(0x8830)])
        elif e['kind']=='mercenary-attack':lines.extend([s(0x809e)+b' '+num(e['initial_force'])+s(0x88e2)+b' '+num(e['initial_defenders'])+s(0x88fc)+e['defender_name'].encode()+b'!',s(0x8934)+s(0x8922 if e['force']else 0x892a)])
    scores={o:100*totals[1][o]for o in(-1,-2)};board,percentages=_scoreboard(original,score_date,score_clock,scores)
    return _result(before_files,lines,board,scores,percentages,totals,losses)


def _result(before,lines,board,scores,percentages,totals,losses):
    return {'YTNAME.DAT':before['YTNAME.DAT'],'YTYNEWS.DAT':before['YTNEWS.DAT'],'YTRMSG.DAT':b'','YTNEWS.DAT':CRLF.join(lines)+CRLF+EOF,'YTSCORE.ASC':board},dict(scores=scores,percentages=percentages,physical=totals,modeled_losses=losses)
