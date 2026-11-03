"""Bounded complete pre-maintenance YT-INIT world replay for retained controls.

Synthesis reads original DATA and audited writer rules, never target templates.
This research model does not create production worlds or implement general MBF.
"""
import argparse
import datetime
import gzip
import json
import math
from pathlib import Path
import replay_qb_ports as ports

graph=ports.graph
ROOT=ports.ROOT
SHA=ports.SHA


def put(record,offset,value):record[offset:offset+4]=graph.mbf.enc(value)


def config_record(seed,date,scoreboard):
    if date.timetuple().tm_yday==10:raise ValueError('January 10 port-date residue is not verified')
    encoded=scoreboard.encode('ascii')
    if not 1<=len(encoded)<=41:raise ValueError('research scoreboard length must be 1..41 ASCII bytes')
    if not 2026<=date.year<=2028:raise ValueError('research date range is 2026..2028')
    rng=graph.QB3(seed)
    hq=math.floor(graph.F32(graph.F32(rng.rnd()*2993)+1))
    record=bytearray(137);record[:41]=encoded.ljust(41,b' ')
    values={41:len(encoded),45:date.year%100,49:500,53:51,57:3051,61:4051,65:25,69:1005,
            73:10,77:14,81:date.timetuple().tm_yday-1,85:-1,93:4151,101:5,105:300,
            117:hq,121:1000,125:6324}
    for offset,value in values.items():put(record,offset,value)
    if date.timetuple().tm_yday==1:
        # Calendar helper's last numeric FAC is INT((year MOD100)*.25).
        # Exact cancellation of DOY1 +(-1) clears only its exponent, preserving
        # this mantissa; do not encode the numeric result as canonical zero.
        residue=bytearray(graph.mbf.enc((date.year%100)//4));residue[3]=0
        record[81:85]=residue
    return bytes(record),hq


def sector_record(sector,warps):
    record=bytearray(137);record[:41]=b' '*41
    # Integer conversion 3f75 writes the low FAC word; the upper word still
    # holds the preceding sector+51 record-position expression. 3f57 on zero
    # clears only the exponent; each following zero keeps that FAC mantissa.
    fac=bytearray(graph.mbf.enc(sector+51));fac[:2]=sector.to_bytes(2,'little')
    for column,destination in enumerate(warps):
        if destination:fac[:]=graph.mbf.enc(destination)
        else:fac[3]=0
        record[41+4*column:45+4*column]=fac
    return record


def synthesize(seed,date,scoreboard='YTSCORE.ASC'):
    if isinstance(date,str):date=datetime.date.fromisoformat(date)
    config,hq=config_record(seed,date,scoreboard)
    records=[config]+[b' '*41+bytes(96)for _ in range(50)]
    table,rng=graph.replay(state=seed)
    pairs=graph.repair(table,rng);shortcuts=graph.shortcuts(table,rng)
    sectors=[sector_record(i,table[i])for i in range(1,3001)]
    statistics={};generated=ports.replay_ports(rng,statistics=statistics)
    for port in generated:put(sectors[port['sector']-1],65,port['id'])
    # Final Xannor pass changes only these fields after all ordinary writers.
    put(sectors[hq-1],81,10000);put(sectors[hq-1],85,-1)
    put(sectors[0],105,hq)
    records.extend(bytes(record)for record in sectors)
    records.extend(ports.port_bytes(port,date.timetuple().tm_yday-10,hq)for port in generated)
    # Planet phase GETs configuration into the shared FIELD buffer, clears
    # only field85 for each inactive slot, and PUTs that inherited record.
    inactive_planet=bytearray(config);put(inactive_planet,85,0)
    records.extend(bytes(inactive_planet)for _ in range(100))
    assert len(records)==4151 and all(len(record)==137 for record in records)
    return b''.join(records),dict(hq_sector=hq,repair_pairs=len(pairs),shortcut_writes=len(shortcuts),
                                  final_state=hex(rng.state),draws=rng.draws,**statistics)


def compare(observed,replayed):
    assert len(observed)==len(replayed)==4151*137,'complete world length'
    blocks={};differences=[]
    for name,start,end in (('configuration',0,1),('players',1,51),('sectors',51,3051),('ports',3051,4051),('planets',4051,4151)):
        a=observed[start*137:end*137];b=replayed[start*137:end*137]
        count=sum(left!=right for left,right in zip(a,b))
        blocks[name]=dict(records=end-start,bytes=len(a),matching_bytes=len(a)-count,byte_mismatches=count,
                          observed_sha256=SHA(a),replayed_sha256=SHA(b))
    for i,(a,b)in enumerate(zip(observed,replayed)):
        if a!=b:
            if len(differences)<12:differences.append(dict(record=i//137+1,offset=i%137,observed=a,replayed=b))
    return dict(compared_records=4151,compared_bytes=len(observed),matching_bytes=sum(b['matching_bytes']for b in blocks.values()),
                byte_mismatches=sum(b['byte_mismatches']for b in blocks.values()),blocks=blocks,first_differences=differences)


def controlled_cases():
    port_report=ports.controlled_cases() # independently verifies raw seeds and native state hooks
    from verify_rng_clock import verify as verify_clocks
    verify_clocks(ROOT/'research/yt-rng-seeding/clock-dos')
    cases=[]
    for port_case in port_report['cases']:
        clock=port_case['clock_case'];path=ROOT/port_case['world']
        metadata=json.loads((path.parent/'result.json').read_text())
        date=datetime.datetime.strptime(metadata['date'],'%m/%d/%Y').date()
        observed=gzip.decompress(path.read_bytes())
        assert SHA(observed)==ports.WORLD_HASHES[clock],'fixed observed target identity'
        replayed,statistics=synthesize(port_case['seed_trace']['world_seed'],date)
        assert statistics['final_state']==port_case['final_state'] and statistics['draws']==port_case['draws']
        cases.append(dict(clock_case=clock,date=date.isoformat(),scoreboard='YTSCORE.ASC',world=port_case['world'],
                          observed_world_sha256=SHA(observed),replayed_world_sha256=SHA(replayed),
                          seed_trace=port_case['seed_trace'],statistics=statistics,**compare(observed,replayed)))
    from verify_initializer_controls import verify as verify_fresh
    for name,control in verify_fresh().items():
        scoreboard=control['scoreboard']or'YTSCORE.ASC'
        replayed,statistics=synthesize(control['seed'],control['date'],scoreboard)
        observed=control['world']
        cases.append(dict(clock_case='fresh-'+name,date=control['date'].isoformat(),scoreboard=scoreboard,
                          world='research/yt-initializer-replay/controls/world-dos/'+name+'/before-maint.dat.gz',
                          observed_world_sha256=SHA(observed),replayed_world_sha256=SHA(replayed),
                          seed_trace=dict(world_seed=control['seed'],trace_sha256=control['seed_trace_sha256']),
                          statistics=statistics,**compare(observed,replayed)))
    return dict(recipe='qb3-complete-initializer-replay-v1',cases=cases,
                limitations=['Research only; no production profile, DOS save interoperability or general MBF implementation.',
                             'Complete pre-maintenance YTDATA.DAT only; auxiliary files and maintenance are separate.',
                             'Bounded default counts, ASCII scoreboard <=41 bytes and selected 2026..2028 dates.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();result=controlled_cases()
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if args.check and any(case['byte_mismatches']for case in result['cases']):raise SystemExit('initializer replay differs from retained worlds')

if __name__=='__main__':main()
