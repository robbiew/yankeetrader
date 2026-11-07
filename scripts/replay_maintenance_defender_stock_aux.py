"""Independent publication audit for fatal offense and untouched-stock handoffs."""
import datetime
from replay_qb_graph import mbf,QB3
from replay_maintenance_aux import field,name,original_literals,original_string,literal,CRLF,EOF,_matrix_clock
from replay_maintenance_neutral_owner_stock_aux import _physical,_scoreboard,_stock,_ground
from replay_maintenance_npcs import directed_path
from replay_maintenance_defender_stock_rules import admit_world
from replay_maintenance_defender_stock_rng import verify as verify_rng,seeded
FILES={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}
SIZE=137

def _admit(before_files,world,mercenary,events,rng_audit,rng_source):
    if type(before_files)is not dict or set(before_files)!=FILES or any(type(b)is not bytes for b in before_files.values())or type(world)is not bytes:raise ValueError('six immutable before files and modeled world required')
    b=before_files['YTDATA.DAT'];admit_world(b)
    if len(world)!=len(b)or before_files['YTRMSG.DAT'] or events not in ([],()):raise ValueError('complete selected worlds, empty inbox and no unmeasured earlier Xannor combat required')
    if(field(b,1,81),field(world,1,81))not in((308,309),(309,310)):raise ValueError('declared source day pair required')
    for data in(b,world):
        if any(field(data,1,o)!=n for o,n in((53,51),(57,3051),(61,4051),(93,4151))):raise ValueError('default geometry required')
        if data[:11]!=b'YTSCORE.ASC' or field(data,1,41)!=11:raise ValueError('original score path required')
        if name(data,4054)!=b'Gateway Cache' or field(data,3051,93)!=3 or field(data,4054,117)!=0:raise ValueError('same linked zero-bank Cache required')
    for r in range(2,52):
        if any(field(world,r,o)!=(-1 if o==109 else 0)for o in range(41,137,4)):raise ValueError('inactive human output ranks required')
    at=4053*SIZE
    if world[at:at+41]!=b[at:at+41]or world[at+73:at+77]!=b[at+73:at+77]:raise ValueError('raw title and governor preserved')
    produced=_stock(b,world,4054)
    if world[at+129:at+133]!=mbf.enc(produced):raise ValueError('exact source-produced uncollected stock required')
    for r in(4052,4054,4150):
        if field(world,r,77)!=_ground(b,world,r):raise ValueError('ground follows independent production without invented damage')
    if type(mercenary)is not dict:raise ValueError('explicit modeled combat ledger required')
    es=mercenary.get('events');acts=mercenary.get('activations');incoming=int(field(b,2419,81));defense=int(field(b,3051,81))
    totals=[_physical(b),_physical(world)];losses={-1:0,-2:0,0:0}
    marks=verify_rng(rng_audit,rng_source)
    required={'mercenary-start','mercenary-end'}|({'battle-entry','battle-exit'}if incoming else set())
    if set(marks)!=required:raise ValueError('complete actual source-phase boundaries required')
    start,start_draws,start_helper=marks['mercenary-start'];scan_rng=QB3(start)
    physical_count=sum(field(world,51+s,81)>0 for s in range(1,3001))+bool(incoming)
    for _ in range(physical_count):scan_rng.rnd()
    if incoming:
        if type(es)is not list or len(es)!=1 or type(acts)is not list or len(acts)!=1:raise ValueError('one complete fatal activation and battle required')
        e=es[0];a=acts[0]
        if e.get('kind')!='mercenary-attack' or e.get('sector')!=3000 or e.get('owner')!=-1 or e.get('defender_name')!='The Xannor' or e.get('initial_force')!=incoming or e.get('initial_defenders')!=defense:raise ValueError('combat binds actual original attacker/defender')
        movement_gate=scan_rng.rnd();helper=start_helper
        for candidate in a.get('candidates',[]):
            if helper>=len(rng_audit.schedule):raise ValueError('target helper exhausted')
            seeded(scan_rng,rng_audit.schedule[helper]);helper+=1
            if scan_rng.integer(3000)!=candidate:raise ValueError('source target RNG progression differs')
        expected=(scan_rng.state,start_draws+scan_rng.draws,helper)
        if marks['battle-entry']!=expected or a.get('gate')!=movement_gate or e.get('initial_rng_state')!=scan_rng.state:raise ValueError('battle entry must derive from surrounding source clock/helper progression')
        state=scan_rng.state
        if type(state)is not int or not 0<=state<2**24:raise ValueError('modeled bounded battle-entry RNG required')
        rng=QB3(state);gate=rng.rnd();left=incoming;remaining=defense;rounds=0
        while left and remaining:
            if rng.rnd()<.5:remaining-=1
            else:left-=1
            rounds+=1
            if rounds>1100:raise ValueError('bounded unit-casualty battle required')
        if left!=0 or remaining<=0 or any(e.get(k)!=v for k,v in dict(force=left,defenders=remaining,losses=incoming,defender_losses=defense-remaining,gate=gate,rounds=rounds,rng_draws=rng.draws,final_rng_state=rng.state).items()):raise ValueError('fatal battle ledger must agree with independent unit-damage RNG walk')
        if marks['battle-exit']!=(rng.state,expected[1]+rng.draws,helper)or marks['mercenary-end']!=marks['battle-exit']:raise ValueError('battle exit must reconcile surrounding source stream')
        warps={s:[int(field(b,51+s,o))for o in range(41,65,4)]for s in range(1,3001)}
        target=a.get('target');candidates=a.get('candidates')
        if type(target)is not int or not 8<=target<=3000 or target==2368 or type(candidates)is not list or not candidates or candidates[-1]!=target or any(n!=2368 for n in candidates[:-1]):raise ValueError('source same-origin rejection and endpoint required')
        if a.get('origin')!=2368 or a.get('force')!=incoming or a.get('held')is not False or a.get('route')!=directed_path(warps,2368,target)or a.get('entered')!=[3000]or a.get('final_sector')is not None or a.get('final_force')!=0 or a.get('stopped_for_pickup')is not False:raise ValueError('derived route terminates in fatal defense without pickup')
        if not a['route'][1:2]==[3000] or type(a.get('gate'))not in(int,float)or not 0<=a['gate']<1:raise ValueError('actual forced hop and eager movement gate required')
        losses[-1]=defense-remaining;losses[-2]=incoming
        if world[2418*SIZE+81:2418*SIZE+89]!=bytes.fromhex('0000280000002800'):raise ValueError('exact departed-origin raw zero pair required')
    else:
        if es!=[]or acts!=[]:raise ValueError('extinct next day must have no action')
        if marks['mercenary-end']!=(scan_rng.state,start_draws+scan_rng.draws,start_helper):raise ValueError('extinct scan RNG progression must reconcile')
        if world[2418*SIZE+81:2418*SIZE+89]!=b[2418*SIZE+81:2418*SIZE+89]:raise ValueError('extinct output must preserve inherited raw departure pair')
        remaining=defense
    if field(world,3051,85)!=-1 or world[3050*SIZE+81:3050*SIZE+85]!=mbf.enc(remaining):raise ValueError('raw surviving defensive force and owner required')
    if any(totals[1][owner]+losses[owner]!=totals[0][owner]for owner in totals[0]):raise ValueError('actual defensive casualties and extinction reconcile')
    if any(mercenary.get(k)!=v for k,v in dict(force=0,initial_force=incoming,losses=incoming,pickup=0,final_sectors=[]).items()):raise ValueError('summary agrees with complete extinct-force ledger')
    return totals,losses,es,produced

def synthesize(before_files,after_world,news_date,news_clock,score_date,score_clock,*,created=(),events=(),mercenary=None,rng_audit=None,rng_source=None):
    if created!=()or any(type(d)is not datetime.date for d in(news_date,score_date)):raise ValueError('retained homes and typed source dates required')
    _matrix_clock(news_clock);_matrix_clock(score_clock)
    totals,losses,es,stock=_admit(before_files,after_world,mercenary,events,rng_audit,rng_source)
    serial=field(after_world,1,81)
    if news_date!=datetime.date(2026,1,1)+datetime.timedelta(days=serial-1)or score_date!=news_date:raise ValueError('exact source publication calendar required')
    original=original_literals();scores={o:100*totals[1][o]for o in(-1,-2)};board,percentages=_scoreboard(original,score_date,score_clock,scores)
    lines=[news_clock.encode()+b' '+news_date.strftime('%m-%d-%Y').encode()+literal(original,b': Maintenance Program Ran ')+literal(original,b'(Revision 03/14/94)'),literal(original,b'  -  Xannor report:'),literal(original,b'Calculated Dynamic Xannor Regeneration is')+b' 0'+literal(original,b' fighters.'),literal(original,b'  -  Mercenary Report:')]
    for e in es:
        lines.append(original_string(original,0x809e)+b' '+str(e['initial_force']).encode()+original_string(original,0x88e2)+b' '+str(e['initial_defenders']).encode()+original_string(original,0x88fc)+e['defender_name'].encode()+b'!')
        lines.append(original_string(original,0x8934)+original_string(original,0x892a))
    output={'YTNAME.DAT':before_files['YTNAME.DAT'],'YTYNEWS.DAT':before_files['YTNEWS.DAT'],'YTRMSG.DAT':b'','YTNEWS.DAT':CRLF.join(lines)+CRLF+EOF,'YTSCORE.ASC':board}
    return output,dict(scores=scores,percentages=percentages,physical=totals,modeled_losses=losses,stock_uncollected=stock,public_events=len(es),private_bytes=0)
