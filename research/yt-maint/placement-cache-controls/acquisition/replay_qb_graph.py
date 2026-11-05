"""Research replay of DOS initializer warps with explicit QB3 LCG state.

No production profile is selected or written. Comparisons retain all six columns,
including holes and Earth's self-link. Limits below stop a research mistake from
hanging; they are not claims that DOS used finite retry policies.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qb_replay_mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
F32=lambda value:struct.unpack('<f',struct.pack('<f',value))[0]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
# Fixed observed target identities, independent of this replay's output.
WORLD_SHA256={
 'research/yt-warp-generation/dos/no-repair/before-maint.dat.gz':'c19362ee2f6dd8e0c2dc6d869daf9cbdafb27ca5247ba7a145e6ad2dfd44ab35',
 'research/yt-warp-generation/dos/repair-only/before-maint.dat.gz':'d59906b9538555eea408a16330a53bf33d72b9e3edeb42237f70ea92867627af',
 'research/yt-warp-generation/dos/original/before-maint.dat.gz':'0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
 'research/yt-port-generation/dos/later/before-maint.dat.gz':'b2db0e8bc4f0c1ababaaf46d4db7144e7c8fee7afa28c3b76e2c7328cc2ceb7f',
}


def native_seeds(trace_root=None):
    # Import the independent native artifact checker, never a capture writer.
    sys.path.insert(0,str(ROOT/'scripts'))
    from verify_rng_trace import verify
    trace_root=Path(trace_root)if trace_root else ROOT/'research/yt-rng-seeding/trace-dos'
    checked=verify(trace_root)
    selected={}
    for name in ('timer-midnight','timer-noon'):
        raw=(trace_root/name/'TRACE.BIN').read_bytes()
        state=int.from_bytes(raw[16:20],'little')
        assert state==checked[name]['seeded'],'raw seed differs from verified trace'
        selected[name]=dict(world_seed=state,
                            trace=str((trace_root/name/'TRACE.BIN').relative_to(ROOT))if(trace_root/name/'TRACE.BIN').is_relative_to(ROOT)else str(trace_root/name/'TRACE.BIN'),
                            trace_sha256=SHA(raw),fac=raw[8:12].hex(),negative_fac=raw[12:16].hex())
    return selected


class QB3:
    def __init__(self,state):
        self.state=state&0xffffff;self.draws=0
    def rnd(self):
        self.state=(214013*self.state+1744579)&0xffffff
        self.draws+=1
        return self.state/16777216
    def integer(self,bound):
        return math.floor(F32(self.rnd()*bound))+1


def replay(count=3000,state=0xc805,prefix_draws=1):
    rng=QB3(state)
    for _ in range(prefix_draws):rng.rnd()
    table=[[0]*6 for _ in range(count+1)]
    for column in range(6):
        table[1][column]=column+1
        table[column+1][column]=1
    for sector in range(1,count+1):
        attempts=0
        while True:
            attempts+=1
            if attempts>100000:raise RuntimeError('research row retry limit')
            for column in range(6):
                if rng.rnd()<=F32(.4) and column<5:
                    offset=rng.integer(10)
                    if sector>count-10:offset=-offset
                    to=sector+offset
                    if not 1<=to<=count:raise RuntimeError('original local index outside selected universe')
                    if table[sector][column]==0 and table[to][column]==0 and to not in table[sector] and sector not in table[to]:
                        table[sector][column]=to;table[to][column]=sector
                if column==5 and table[sector][5]==0:
                    retries=0
                    while True:
                        retries+=1
                        if retries>100000:raise RuntimeError('research self-target retry limit')
                        if rng.rnd()<F32(.985):break
                        to=rng.integer(count)
                        if to==sector:continue
                        if table[to][5]==0:
                            # Original lacks the modern cross-column duplicate check.
                            table[sector][5]=to;table[to][5]=sector
                        break
            if sector==1 or any(table[sector]):break
    return table,rng


def repair(table,rng):
    """Original rejection sampler and BFS order, without modern source pooling."""
    count=len(table)-1;seen=[False]*len(table);pairs=[]
    for target in range(2,count+1):
        if seen[target]:continue
        previous=[0]*len(table);previous[1]=-1
        queue=[1];head=0
        while head<len(queue) and previous[target]==0:
            current=queue[head]
            for neighbor in table[current]:
                if previous[neighbor]==0:
                    previous[neighbor]=current;queue.append(neighbor);seen[neighbor]=True
            head+=1
        if previous[target]!=0:continue
        for attempt in range(100000):
            source=rng.integer(target-1)
            if table[source][5]==0:break
        else:raise RuntimeError('research repair rejection limit')
        table[source][5]=target;table[target][5]=source
        pairs.append([target,source])
    return pairs


def shortcuts(table,rng):
    count=len(table)-1
    position=F32(8+F32(400*rng.rnd()));writes=[]
    for attempt in range(100000):
        if position>=count:return writes
        sector=math.floor(position+.5)
        if table[sector][5]==0:
            table[sector][5]=1;writes.append(sector)
        position=F32(position+F32(400*rng.rnd()))
    raise RuntimeError('research shortcut step limit')


def run_case(path,state,prefix_draws=1,phase='base',expected_world_sha=None):
    expected,digest=read_table(path,expected_sha=expected_world_sha)
    table,rng=replay(state=state,prefix_draws=prefix_draws)
    repair_pairs=[];shortcut_writes=[]
    if phase in ('repair','full'):repair_pairs=repair(table,rng)
    if phase=='full':shortcut_writes=shortcuts(table,rng)
    return dict(recipe='qb3-initializer-graph-replay-v1',
                world=str(path.relative_to(ROOT))if path.is_relative_to(ROOT)else str(path),
                world_sha256=digest,starting_state=hex(state),prefix_draws=prefix_draws,phase=phase,
                draws=rng.draws,final_state=hex(rng.state),repair_pairs=repair_pairs,shortcut_writes=shortcut_writes,
                **compare(expected,table),
                limitations=['Research only; no Go production profile or general exact seed-to-universe promise.',
                             'RNG state is supplied explicitly from separate retained startup probes.',
                             'Only selected fixed-clock initializer graphs are compared; port names/economy and later gameplay are outside this replay.',
                             'These graphs alone cannot distinguish zero versus one pregraph draw: an unused occupied-Earth-slot offset can resynchronize the stream; the HQ draw needs its separate native evidence.'])


def read_table(path,count=3000,expected_sha=None):
    path=Path(path)
    raw=gzip.decompress(path.read_bytes())
    if expected_sha is None and path.is_relative_to(ROOT):expected_sha=WORLD_SHA256.get(str(path.relative_to(ROOT)))
    if expected_sha is not None:assert SHA(raw)==expected_sha,'changed fixed observed target world'
    assert len(raw)==4151*137,'wrong world record coverage'
    table=[[0]*6]
    for sector in range(1,count+1):
        values=[mbf.get(raw,51+sector,offset)for offset in(41,45,49,53,57,61)]
        assert all(math.isfinite(v) and v==int(v) and 0<=v<=count for v in values),'invalid target warp cell'
        table.append(list(map(int,values)))
    return table,SHA(raw)


def compare(expected,actual):
    differences=[]
    for sector in range(1,len(expected)):
        for column in range(6):
            if expected[sector][column]!=actual[sector][column]:
                differences.append(dict(sector=sector,column=column,observed=expected[sector][column],replayed=actual[sector][column]))
    return dict(compared_cells=(len(expected)-1)*6,matching_cells=(len(expected)-1)*6-len(differences),
                mismatch_count=len(differences),first_difference=differences[0]if differences else None,
                first_differences=differences[:12])


def controlled_cases(trace_root=None):
    seeds=native_seeds(trace_root)
    specifications=[
      ('research/yt-warp-generation/dos/no-repair/before-maint.dat.gz','timer-midnight','base'),
      ('research/yt-warp-generation/dos/repair-only/before-maint.dat.gz','timer-midnight','repair'),
      ('research/yt-warp-generation/dos/original/before-maint.dat.gz','timer-midnight','full'),
      ('research/yt-port-generation/dos/later/before-maint.dat.gz','timer-noon','full'),
    ]
    results=[]
    for relative,trace_name,phase in specifications:
        path=ROOT/relative;origin=seeds[trace_name]
        case=run_case(path,origin['world_seed'],1,phase,WORLD_SHA256[relative])
        log=(path.parent/'INIT.LOG').read_bytes()
        observed_pairs=[[int(a),int(b)]for a,b in re.findall(r'Sector\s*(\d+)\s*has been linked to sector\s*(\d+)',log.decode('cp437'))]
        assert case['repair_pairs']==observed_pairs,'replay repair pairs differ from native log'
        case['native_init_log_sha256']=SHA(log)
        case['seed_trace']=origin
        results.append(case)
    return dict(recipe='qb3-fixed-clock-graph-comparison-v1',cases=results)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=lambda value:int(value,0),default=0xc805)
    parser.add_argument('--prefix-draws',type=int,default=1)
    parser.add_argument('--phase',choices=('base','repair','full'),default='base')
    parser.add_argument('--world',type=Path,default=ROOT/'research/yt-warp-generation/dos/no-repair/before-maint.dat.gz')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--all-controls',action='store_true')
    parser.add_argument('--check',action='store_true',help='fail unless every compared warp cell matches')
    args=parser.parse_args()
    if args.all_controls:
        result=controlled_cases()
    else:result=run_case(args.world,args.state,args.prefix_draws,args.phase)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if args.check:
        results=result['cases']if args.all_controls else [result]
        if any(case['mismatch_count']for case in results):raise SystemExit('research replay does not match retained DOS graph')

if __name__=='__main__':main()
