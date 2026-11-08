"""Independent RNG walk for every random combat event and hiring placement.

Entry checkpoints are derived from the complete source operation stream, never
from mutable public-event seeds or native witness bytes.
"""
from replay_maintenance_defender_stock_rng import SourceStream as Base,Audit
from replay_qb_graph import QB3,mbf


class SourceStream(Base):
    def __init__(self,schedule,state):super().__init__(schedule,state);self.contexts=[]
    def action(self,kind,fn,world,*args):
        sector,force=args[-2:];record=51+sector
        context=(kind,sector,args[0]if kind in('mine','defense')else None,force,int(mbf.get(world,record,81)),int(mbf.get(world,record,129)))
        index=len(self.contexts);self.contexts.append(context)
        self.mark(('entry',index));event=fn(world,self,*args);self.mark(('exit',index));return event


def verify(audit,source,contexts,events):
    if type(audit)is not Audit or type(source)is not tuple or len(source)!=5 or(audit.initial_state,audit.schedule,audit.final_state,audit.total_draws)!=(source[0],source[1],source[3],source[4]):raise ValueError('typed source operation audit and separate clock checkpoints required')
    rng=QB3(audit.initial_state);index=0;marks={};seeds=[]
    for op in audit.operations:
        if type(op)is not tuple:raise ValueError('immutable source operation required')
        if len(op)==2 and op[0]=='draw':
            if type(op[1])is not int or not 1<=op[1]<=200000 or rng.draws+op[1]>200000:raise ValueError('bounded source draw block required')
            for _ in range(op[1]):rng.rnd()
        elif len(op)==3 and op[0]=='seed':
            if index>=len(audit.schedule)or audit.schedule[index][:2]!=op[1:]:raise ValueError('derived helper chronology differs')
            family,caller,timer=audit.schedule[index];old=rng.state
            if type(timer)is not bytes or len(timer)!=4:raise ValueError('four source TIMER bytes required')
            rng.state=(old&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16);index+=1
            seeds.append((family,caller,old,timer.hex(),rng.state))
        elif len(op)==2 and op[0]=='mark':
            marker=op[1]
            if type(marker)is not tuple or len(marker)!=2 or marker[0]not in('entry','exit')or type(marker[1])is not int or not 0<=marker[1]<len(contexts)or marker in marks:raise ValueError('unique derived action checkpoint required')
            marks[marker]=(rng.state,rng.draws,index)
        else:raise ValueError('unknown source operation')
    if index!=len(audit.schedule)or(rng.state,rng.draws)!=(audit.final_state,audit.total_draws)or tuple(seeds)!=source[2]:raise ValueError('full source helper/final checkpoint mismatch')
    if type(contexts)is not tuple or len(contexts)!=len(events)or len(marks)!=2*len(events):raise ValueError('complete source contexts and event inventory required')
    for i,(context,event)in enumerate(zip(contexts,events)):
        kind,sector,group,force,defenders,mines=context;entry=marks[('entry',i)];exit=marks[('exit',i)];r=QB3(entry[0]);helper_index=entry[2]
        if event['kind']!=kind or event['sector']!=sector or(group is not None and event['group']!=group)or event['initial_force']!=force or event['initial_rng_state']!=entry[0]:raise ValueError('event must bind independent source entry')
        def one(bound,family,caller,count=1):
            nonlocal helper_index
            row=audit.schedule[helper_index];helper_index+=1
            if row[:2]!=(family,caller):raise ValueError('actual action helper chronology differs')
            timer=row[2];r.state=(r.state&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)
            for _ in range(count):bound=r.integer(bound)
            return bound
        if kind=='mercenary-attack':
            if event['initial_defenders']!=defenders:raise ValueError('source defensive force differs')
            gate=r.rnd();left=force;right=defenders;rounds=0
            while left>0 and right>0:
                damage=150 if min(left,right)>200 else 1
                if r.rnd()<.5:right=max(0,right-damage)
                else:left=max(0,left-damage)
                rounds+=1
            if(event['force'],event['defenders'],event['gate'],event['rounds'])!=(left,right,gate,rounds):raise ValueError('source offense RNG/casualties differ')
        elif kind=='defense':
            if event['initial_defenders']!=defenders:raise ValueError('source defensive force differs')
            xd=md=0
            while force-xd>0 and defenders-md>0:
                n=min(force-xd,defenders-md);batch=5000 if n>5000 else 500 if n>=500 else 1
                if r.rnd()>.5:xd+=batch
                else:md+=batch
            if(event['x_damage'],event['defender_damage'],event['force'],event['defenders'])!=(xd,md,max(0,force-xd),max(0,defenders-md)):raise ValueError('source defensive RNG/casualties differ')
        elif kind in('mine','mercenary-mine'):
            left=force;rolls=[];spent=0
            for _ in range(mines):
                roll=one(1000,'h1',0x7312)if kind=='mine'else one(10000,'h2',0x4aa4,2)
                rolls.append(roll);damage=min(left,roll)
                if damage>0:left-=damage;spent+=1
            if(event['force'],event['rolls'],event['mines_spent'],event['initial_mines'],event['mines'])!=(left,rolls,spent,mines,mines-spent):raise ValueError('source mine RNG/debit differs')
        else:raise ValueError('unmodeled random action')
        if(r.state,entry[1]+r.draws,helper_index)!=exit or(event['final_rng_state'],event['rng_draws'])!=(r.state,r.draws):raise ValueError('event exit must bind derived source continuation')
    return len(seeds)+2+2*len(events)


def verify_hiring(audit,hiring):
    rows=[s for s in audit.schedule if s[:2]==('h1',0x4546)]
    attempts=[sector for p in hiring['placements']for sector in p['attempts']]
    # Follow the complete derived operation walk to obtain the seeded low byte;
    # it is not safe to seed a placement from its mutable public event.
    rng=QB3(audit.initial_state);index=0;derived=[]
    for op in audit.operations:
        if op[0]=='draw':
            for _ in range(op[1]):rng.rnd()
        elif op[0]=='seed':
            family,caller,timer=audit.schedule[index];index+=1
            rng.state=(rng.state&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)
            if(family,caller)==('h1',0x4546):derived.append(QB3(rng.state).integer(2999)+1)
    if len(rows)!=len(attempts)or attempts!=derived:raise ValueError('hiring placements must bind independently derived source RNG')
