"""Research-only original initializer port replay; never writes production worlds."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import replay_qb_graph as graph

ROOT=graph.ROOT
F32=graph.F32
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def syllables():
    raw=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes()
    assert SHA(raw)=='601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
    rows=re.findall(rb'[\x06-\x49]\x26 ([^\x00]+)\x00',raw[0x33a0:0x4720])
    tokens=b','.join(row for row in rows if row!=b'"***"').split(b',')
    assert len(tokens)==908 and SHA(b','.join(tokens))=='8a59a909d232084d89a82db77339f680475c3187aef96ef0ce6444bd0b4002b7'
    return [token.decode('ascii')for token in tokens]


def name(rng,pool):
    first=rng.rnd()
    chunks=math.floor(F32(F32(first*rng.rnd())*3))+2
    parts=[]
    for _ in range(chunks):
        token=pool[rng.integer(len(pool))-1]
        parts.append(' '+token[0].upper()+token[1:]if len(token)>4 else token)
    result=''.join(parts).removeprefix(' ')
    return result[0].upper()+result[1:]


def replay_ports(rng,count=1000,sectors=3000,statistics=None):
    placement_start=rng.draws
    locations=[1,3,5,7]
    occupied={1,2,3,4} # Original defect: does not initially protect sectors 5/7.
    retries=0
    while len(locations)<count:
        sector=rng.integer(sectors-1)+1
        if sector in occupied:
            retries+=1
            if retries>100000:raise RuntimeError('research placement retry limit')
            continue
        locations.append(sector);occupied.add(sector)
    if statistics is not None:
        statistics.update(placement_draws=rng.draws-placement_start,placement_rejections=retries,
                          placement_final_state=hex(rng.state),placement_total_draws=rng.draws)
    pool=syllables();ports=[]
    for ident,sector in enumerate(locations,1):
        rates=[rng.integer(31767)+999 for _ in range(3)]
        coefficients=[-rng.integer(100)for _ in range(3)]
        title='Earth'if ident==1 else name(rng,pool)
        trade_class=rng.integer(3)
        coefficients[3-trade_class]*=-1
        ports.append(dict(id=ident,sector=sector,name=title,trade_class=trade_class,
                          production=rates,coefficients=coefficients,supply=[0,0,0]))
    return ports


def observed_ports(raw):
    ports=[]
    for ident in range(1,1001):
        rec=3051+ident;at=(rec-1)*137
        get=lambda offset:graph.mbf.get(raw,rec,offset)
        ports.append(dict(id=ident,sector=get(93),name=raw[at:at+41].rstrip(b' ').decode('ascii'),
                          trade_class=get(41),production=[get(o)for o in(61,65,69)],
                          coefficients=[get(o)for o in(73,77,81)],supply=[get(o)for o in(49,53,57)]))
    return ports


def port_bytes(port,production_day,hq_sector):
    record=bytearray(137)
    encoded=port['name'].encode('ascii')
    assert len(encoded)<=41,'name exceeds native FIELD'
    record[:41]=encoded.ljust(41,b' ')
    def put(offset,value):record[offset:offset+4]=graph.mbf.enc(value)
    for offset in (49,53,57,89,97,101,105,109,129):record[offset:offset+4]=bytes.fromhex('0000a000')
    put(41,port['trade_class']);put(45,production_day);put(85,len(encoded));put(93,port['sector'])
    if production_day==0:
        index=7-port['trade_class']
        residue=bytearray(graph.mbf.enc(index));residue[:2]=index.to_bytes(2,'little');residue[3]=0
        record[45:49]=residue
    for start,field in ((61,'production'),(73,'coefficients')):
        for i,value in enumerate(port[field]):put(start+4*i,value)
    if port['id']==1:
        put(117,hq_sector);put(121,1000);put(125,6324)
    return bytes(record)


def run_case(path,seed,production_day=296,expected_sha=None):
    raw=gzip.decompress(path.read_bytes())
    if expected_sha is None:expected_sha=graph.WORLD_SHA256[str(path.relative_to(ROOT))]
    assert SHA(raw)==expected_sha,'changed observed world'
    table,rng=graph.replay(state=seed)
    graph.repair(table,rng);graph.shortcuts(table,rng)
    graph_state=hex(rng.state);graph_draws=rng.draws
    expected_graph=[[0]*6]+[[int(graph.mbf.get(raw,51+sector,offset))for offset in(41,45,49,53,57,61)]for sector in range(1,3001)]
    graph_comparison=graph.compare(expected_graph,table)
    statistics={}
    actual=replay_ports(rng,statistics=statistics);expected=observed_ports(raw)
    hq_rng=graph.QB3(seed);hq_sector=math.floor(F32(F32(hq_rng.rnd()*2993)+1))
    synthesized=b''.join(port_bytes(port,production_day,hq_sector)for port in actual)
    observed_block=raw[3051*137:4051*137]
    byte_differences=[dict(port=i//137+1,offset=i%137,observed=a,replayed=b)
                      for i,(a,b)in enumerate(zip(observed_block,synthesized))if a!=b]
    differences=[]
    for observed,replayed in zip(expected,actual):
        for field in observed:
            if observed[field]!=replayed[field]:
                differences.append(dict(port=observed['id'],field=field,observed=observed[field],replayed=replayed[field]))
    links={};collisions=[]
    for port in actual:
        if port['sector']in links:collisions.append(dict(sector=port['sector'],overwritten=links[port['sector']],winner=port['id']))
        links[port['sector']]=port['id']
    link_differences=[dict(sector=s,observed=graph.mbf.get(raw,51+s,65),replayed=links.get(s,0))
                      for s in range(1,3001)if graph.mbf.get(raw,51+s,65)!=links.get(s,0)]
    return dict(world=str(path.relative_to(ROOT))if path.is_relative_to(ROOT)else str(path),world_sha256=SHA(raw),seed=hex(seed),
                graph_final_state=graph_state,graph_draws=graph_draws,final_state=hex(rng.state),draws=rng.draws,
                economy_draws=rng.draws-statistics['placement_total_draws'],**statistics,
                compared_port_bytes=137000,matching_port_bytes=137000-len(byte_differences),
                observed_port_block_sha256=SHA(observed_block),replayed_port_block_sha256=SHA(synthesized),
                byte_mismatches=len(byte_differences),first_byte_differences=byte_differences[:12],
                graph_comparison=graph_comparison,collisions=collisions,distinct_locations=len(links),compared_ports=1000,matching_ports=sum(a==b for a,b in zip(actual,expected)),
                mismatch_fields=len(differences),first_differences=differences[:12],
                sector_link_mismatches=len(link_differences),first_link_differences=link_differences[:4])


WORLD_HASHES={
    'midnight':'0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
    'repeat':'0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
    'second-one':'6cccb3fe676d40016b553e3ee7ea6d1a0d44dff0f029550602f44e88ecfda5db',
    'second-two':'6fce61a33be6090dfa681c97f0873b1de926215f727dac1d87be4279c02e2fd7',
    'later':'b2db0e8bc4f0c1ababaaf46d4db7144e7c8fee7afa28c3b76e2c7328cc2ceb7f',
    'next-date':'042fdce8f48d40c5292eebc676a11b7f9f9725537fc98066a178aa394bef1b0c',
}


def controlled_cases():
    from verify_rng_trace import verify
    from verify_port_replay_seed import verify as verify_extra_seed
    trace_root=ROOT/'research/yt-rng-seeding/trace-dos'
    checked=verify(trace_root)
    extra_root=ROOT/'research/yt-port-replay/seed-dos'
    extra=verify_extra_seed(extra_root)
    from verify_port_rng_states import verify as verify_states
    state_root=ROOT/'research/yt-port-replay/state-dos'
    states=verify_states(state_root)
    cases=[]
    for clock,trace in (('midnight','timer-midnight'),('repeat','timer-repeat'),
                        ('second-one','timer-plus-one'),('second-two','timer-plus-two'),
                        ('later','timer-noon'),('next-date','timer-next-date')):
        directory=(extra_root if clock=='second-two'else trace_root)/trace
        raw=(directory/'TRACE.BIN').read_bytes()
        seed=int.from_bytes(raw[16:20],'little')
        verified=extra if clock=='second-two'else checked[trace]
        assert seed==verified['seeded']
        path=ROOT/'research/yt-rng-seeding/clock-dos'/clock/'before-maint.dat.gz'
        result=run_case(path,seed,297 if clock=='next-date'else 296,WORLD_HASHES[clock])
        result['clock_case']=clock
        result['seed_trace']=dict(trace=str((directory/'TRACE.BIN').relative_to(ROOT)),trace_sha256=SHA(raw),
                                  fac=raw[8:12].hex(),negative_fac=raw[12:16].hex(),world_seed=seed)
        if clock in ('midnight','second-one','second-two','later'):
            result['native_state_checks']={}
            for phase,field in (('graph-end','graph_final_state'),('placement-end','placement_final_state'),('ports-end','final_state')):
                key=clock+'-'+phase
                assert int(result[field],16)==states[key],'native phase state differs from replay'
                log=state_root/key/'INIT.LOG'
                result['native_state_checks'][phase]=dict(state=hex(states[key]),log=str(log.relative_to(ROOT)),log_sha256=SHA(log.read_bytes()))
        cases.append(result)
    return dict(recipe='qb3-fixed-clock-port-replay-v1',cases=cases,
                limitations=['Research model only; no production profile or full MBF implementation.',
                             'Original occupancy initialization defect intentionally preserved.',
                             'Three phase-end states independently observed at four clock points; repeat/next-date have no separate state hooks.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();result=controlled_cases()
    cases=result['cases']
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if args.check and any(case['graph_comparison']['mismatch_count']or case['byte_mismatches']or case['mismatch_fields']or case['sector_link_mismatches']for case in cases):
        raise SystemExit('port replay differs from retained DOS worlds')

if __name__=='__main__':main()
