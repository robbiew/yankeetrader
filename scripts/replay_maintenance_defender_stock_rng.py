"""Source-operation RNG audit; clock inputs and markers are separate from events."""
from dataclasses import dataclass
from replay_qb_graph import QB3
from replay_maintenance_collision_npcs import Stream

@dataclass(frozen=True)
class Audit:
    initial_state:int
    schedule:tuple
    operations:tuple
    final_state:int
    total_draws:int

class TracedRandom(QB3):
    def __init__(self,state,operations):super().__init__(state);self.operations=operations
    def rnd(self):
        if self.operations and self.operations[-1][0]=='draw':self.operations[-1]=('draw',self.operations[-1][1]+1)
        else:self.operations.append(('draw',1))
        return super().rnd()

class SourceStream(Stream):
    def __init__(self,schedule,state):
        super().__init__(schedule,state);self.operations=[];self.initial_state=state;self.rng=TracedRandom(state,self.operations)
    def reseed(self,family,caller):
        self.operations.append(('seed',family,caller));super().reseed(family,caller)
    def mark(self,name):self.operations.append(('mark',name))
    def audit(self):return Audit(self.initial_state,self.schedule,tuple(self.operations),self.rng.state,self.rng.draws)

def seeded(rng,row):
    family,caller,timer=row
    if family!='h1' or caller!=0x48cf or type(timer)is not bytes or len(timer)!=4:raise ValueError('source Mercenary target helper clock required')
    rng.state=(rng.state&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)

def verify(audit,source=None):
    if type(audit)is not Audit or type(audit.initial_state)is not int or not 0<=audit.initial_state<2**24 or type(audit.schedule)is not tuple or type(audit.operations)is not tuple:raise ValueError('frozen source-only RNG audit required')
    if type(source)is not tuple or len(source)!=5 or (audit.initial_state,audit.schedule,audit.final_state,audit.total_draws)!=(source[0],source[1],source[3],source[4]):raise ValueError('audit must agree with separate source-clock and final-stream checkpoints')
    rng=QB3(audit.initial_state);index=0;marks={};seeds=[]
    for op in audit.operations:
        if type(op)is not tuple:raise ValueError('typed source operation required')
        if len(op)==2 and op[0]=='draw':
            if type(op[1])is not int or not 1<=op[1]<=200000 or rng.draws+op[1]>200000:raise ValueError('bounded exact source draw count required')
            for _ in range(op[1]):rng.rnd()
        elif len(op)==3 and op[0]=='seed':
            if index>=len(audit.schedule):raise ValueError('helper clock exhaustion')
            row=audit.schedule[index]
            if type(row)is not tuple or len(row)!=3 or row[:2]!=op[1:] or type(row[2])is not bytes or len(row[2])!=4:raise ValueError('source-clock/helper chronology must agree')
            raw=row[2];old=rng.state;rng.state=(old&255)|((raw[0]^raw[2])<<8)|((raw[1]^raw[3])<<16);index+=1
            seeds.append((row[0],row[1],old,raw.hex(),rng.state))
        elif len(op)==2 and op[0]=='mark':
            if op[1]not in('mercenary-start','battle-entry','battle-exit','mercenary-end')or op[1]in marks:raise ValueError('unique actual source-phase marker required')
            marks[op[1]]=(rng.state,rng.draws,index)
        else:raise ValueError('unknown source RNG operation')
    if index!=len(audit.schedule)or (rng.state,rng.draws)!=(audit.final_state,audit.total_draws):raise ValueError('whole source RNG audit must reconcile final stream and clocks')
    if tuple(seeds)!=source[2]:raise ValueError('derived helper entry/exit states must agree with surrounding source progression')
    return marks
