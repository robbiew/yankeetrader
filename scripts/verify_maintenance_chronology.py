"""Verify the bounded initial-maintenance phase chronology without running DOS.

The acquisition runner is never imported. Original sequence anchors are first
verified against their immutable pins; fresh nth-hit boundaries then close the
measured literal-RND gaps. Counts describe eager player scans, not route hops.
"""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re

import verify_maintenance_sequence as sequence
from verify_initial_maintenance import PINS as INITIAL_PINS
from verify_maintenance_rng import MAINT_BANNER, mbf, verify_launch
from verify_rng_clock import read_date, read_time
from verify_rng_native import image

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/chronology-controls'
PINS_FILE=ROOT/'research/yt-maint/chronology-pins.json'
PINS_SHA='809056a6a97c44c92861ab59e89cd0dc9fc26f3f82b747bfd36a648b518fc3b3'
NATIVE=ROOT/'research/yt-maint/chronology-native/rea.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
BINARIES=sequence.BINARIES
META_KEYS=sequence.META_KEYS
COMMON=sequence.COMMON
DATA_FILES=sequence.DATA_FILES
# Reuse previously independently reviewed lower-level witness/patch contracts.
# This milestone supplies its own matrix, site/source attribution and semantics.
reconstructed_probe=sequence.reconstructed_probe
expected_inputs=sequence.expected_inputs
commands=sequence.commands
classify_trace=sequence.classify_trace
DISTANCES=(1500,1100,1150,1800,1950,1550,1250,1050,2050,1300,1200,1150,1300,1750,1100,700,1350,1800,700)
BLOCKS=tuple((n-50)//50 for n in DISTANCES)
assert sum(DISTANCES)==25750 and sum(BLOCKS)==496


def expected_matrix():
    out={'untouched':(None,65535,0x234)}
    for site in (0x3348,0x3c0e,0x7900,0x7946):out[f'count-{site:04x}']=(site,65535,0x234)
    scan_sources={'state':0x234,'group':0x7b8c,'player':0x7bf0,'prestep':0x7b68,'destination':0x7bc4}
    consumed=0
    for phase,blocks in enumerate(BLOCKS,1):
        for edge,nth in [('first',consumed+1),('last',consumed+50*blocks)]:
            for label,source in scan_sources.items():out[f'scan-{phase:02}-{edge}-{label}']=(0x3c0e,nth,source)
        for edge,nth in [('first',50*(phase-1)+1),('last',50*phase)]:
            for label,source in [('state',0x234),('group',0x7b8c),('player',0x7bc0)]:
                out[f'candidate-{phase:02}-{edge}-{label}']=(0x3348,nth,source)
        consumed+=50*blocks
    for n in range(1,21):out[f'desertion-{n:02}-before']=(0x46af,n,0x234)
    out.update({'desertion-last-after':(0x46b7,20,0x234),'lottery-before':(0x537e,1,0x234),'lottery-after':(0x5386,1,0x234)})
    assert len(out)==332 and consumed==24800
    return out


def verify_native(path,original):
    records=json.loads(Path(path).read_text())['records']
    wanted={'0x13113':529,'0x139d4':1116,'0x171af':188}
    assert len(records)==len(wanted), 'native coverage'
    loaded=image(original);seen=set()
    for r in records:
        v=r['normalized_result'];address=v['address']
        assert r['operation']=='read_bytes' and r['subject']['name']=='YTMAINT.EXE', 'native operation/subject'
        assert r['subject']['digest']=={'sha256':BINARIES['YTMAINT.EXE']}, 'native identity'
        assert address in wanted and address not in seen, 'native address'
        size=wanted[address]
        assert r['parameters']=={'address':address,'length':size}, 'native parameters'
        assert v['complete'] is True and v['requested_bytes']==v['returned_bytes']==size, 'native truncation'
        at=int(address,16)-0x10000
        assert bytes.fromhex(v['bytes_hex'])==loaded[at:at+size], 'native relocated bytes'
        seen.add(address)
    assert seen==set(wanted), 'native completeness'


def verify_control(folder, pin, original):
    folder=Path(folder); raw_meta=(folder/'result.json').read_bytes(); m=json.loads(raw_meta)
    assert set(m)==META_KEYS, 'metadata schema'
    assert m['recipe']=='maintenance-nth-site-v1' and m['name']==folder.name, 'control identity'
    assert m['binaries']==BINARIES, 'original binary identities'
    assert m['site'] is None or type(m['site']) is int, 'site type'
    assert m['site'] is None or m['site'] in {0x3348,0x3c0e,0x7900,0x7946,0x46af,0x46b7,0x537e,0x5386}, 'selected known runtime boundary'
    assert m['source'] in (0x234,0x7b8c,0x7bf0,0x7b68,0x7bc0,0x7bc4), 'selected state/FAC/argument source'
    inputs,patches=expected_inputs(m['occupied'])
    assert m['inputs']==inputs and m['patches']==patches, 'declared synthetic occupancy fixture'
    if m['site'] is None:
        assert m['nth']==65535 and m['source']==0x234, 'untouched metadata'
        copied=original
    else:
        copied=reconstructed_probe(original,m['site'],m['nth'],m['source'])
    assert SHA(copied)==m['copied_sha256'], 'independent patch reconstruction'
    data_files=set(m['files'])-COMMON
    assert {'after-'+n+'.gz'for n in ('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT')}<=data_files<=DATA_FILES, 'known complete DAT/ASC artifact set'
    files=COMMON|data_files
    assert set(m['files'])==files and {p.name for p in folder.iterdir()}==files|{'result.json'}, 'retained inventory'
    for n,h in m['files'].items():assert SHA((folder/n).read_bytes())==h, 'mutable file hash: '+n
    wanted=commands(m['clock'])
    assert (folder/'COMMANDS.TXT').read_text()=='\n'.join(wanted)+'\n', 'complete command recipe'
    verify_launch(folder,wanted)
    assert (folder/'ERROR.LOG').read_bytes()==b'', 'no DOS error witness'
    assert (folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n', 'DOS zero-status witness'
    assert (folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n', 'shell return witness'
    date=datetime.date(2026,11,2)
    date_text=('Current date: '+date.strftime('%a %m/%d/%Y')+'\r\n').encode()+b'Run \x1b[33;1mdate MM/DD/YYYY\x1b[0m to change the current date.\r\n'
    for n in ('DOSDATE.LOG','ENDDATE.LOG'):
        assert read_date((folder/n).read_bytes())==date and (folder/n).read_bytes()==date_text, 'observed complete date'
    for n in ('DOSTIME.LOG','ENDTIME.LOG'):
        assert re.fullmatch(rb'Current time: \d{1,2}:\d{2}:\d{2}\.\d{2}(am|pm)\r\nRun \x1b\[33;1mtime hh:mm:ss\x1b\[0m to change the current time.\r\n',(folder/n).read_bytes()), 'complete time witness'
    start,end=[read_time((folder/n).read_bytes())for n in ('DOSTIME.LOG','ENDTIME.LOG')]
    assert start=={'00:00:00':0,'00:00:02':1.97}[m['clock']] and start<=end<start+30, 'observed bounded clock'
    trace=(folder/'TRACE.BIN').read_bytes(); result=classify_trace(trace,m)
    world=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
    assert len(world)==4151*137, 'world extent'
    # Pin metadata and every raw decoded artifact independently of mutable hashes.
    assert set(pin)=={'metadata_sha256','raw'}, 'pin schema'
    assert SHA(raw_meta)==pin['metadata_sha256'], 'immutable control metadata'
    assert set(pin['raw'])==files, 'complete raw pin inventory'
    for n,h in pin['raw'].items():
        b=(folder/n).read_bytes()
        assert SHA(gzip.decompress(b)if n.endswith('.gz')else b)==h, 'immutable raw pin: '+n
    return dict(result,metadata=m,world=world,trace=trace,outputs={n:SHA(gzip.decompress((folder/n).read_bytes()))for n in data_files})


def advance(state,count):
    assert type(state)is int and 0<=state<2**24 and type(count)is int and count>=0
    for _ in range(count):state=(214013*state+1744579)%2**24
    return state


def integer(raw,low,high,label):
    value=mbf(raw)
    assert low<=value<=high and value==int(value), label+' is a bounded MBF integer'
    return int(value)


def old_anchors():
    """Verify prior immutable evidence before using any of its runtime samples."""
    sequence.verify()
    names=set()
    for helper,total in [('h1',41),('h2',19)]:
        for n in range(1,total+1):
            for label in ('old','seed','draw')if helper=='h1'else('old','seed'):
                names.add(f'baseline--{helper}-{label}-{n:03}')
    names|={f'baseline--h2-draw-{n:03}'for n in range(1,77)}
    return {name:int.from_bytes((sequence.DEFAULT/name/'TRACE.BIN').read_bytes()[-4:],'little')for name in names}


def initial_graph():
    packed=ROOT/'research/yt-maint/initial-controls/baseline-split/before-YTDATA.DAT.gz'
    world=gzip.decompress(packed.read_bytes())
    assert SHA(world)==INITIAL_PINS['baseline-split']['before-YTDATA.DAT.gz'], 'immutable pre-maintenance graph'
    graph={}
    for sector in range(1,3001):
        base=(50+sector)*137
        destinations=[mbf(world[base+offset:base+offset+4])for offset in range(41,65,4)]
        assert all(value==int(value)and 0<=value<=3000 for value in destinations), 'native graph bounds'
        graph[sector]={int(value)for value in destinations if value}
    return graph


def verify_semantics(rows,anchors,graph=None):
    graph=initial_graph()if graph is None else graph
    for site,count in [(0x3348,950),(0x3c0e,24800),(0x7900,41),(0x7946,19)]:
        row=rows[f'count-{site:04x}']
        assert row['kind']=='body-end' and row['count']==count, 'fresh complete phase counter'
        assert row['outputs']==rows['untouched']['outputs'], 'complete counter DAT/ASC outputs equal fresh untouched'
    old_output={p.name:SHA(gzip.decompress(p.read_bytes()))for p in(sequence.DEFAULT/'baseline--untouched').glob('after-*.gz')}
    assert rows['untouched']['outputs']==old_output, 'fresh untouched all DAT/ASC outputs match prior pinned baseline'
    state=lambda key:rows[key]['state']
    old=lambda key:anchors['baseline--'+key]
    assert old('h1-old-001')==0x00c805, 'measured midnight startup-to-first-helper state'
    assert advance(old('h1-draw-001'),3)==old('h1-old-002'), 'three Wanderer draws bridge first two helpers'
    assert old('h1-draw-002')==old('h2-old-001'), 'first mobile allocator entry follows fallback draw'
    for phase,blocks in enumerate(BLOCKS,1):
        # The four shrinking-bound helper draws were independently validated in
        # the prior milestone. The new boundaries join their surrounding calls.
        assert old(f'h2-draw-{phase*4:03}')==old(f'h1-old-{phase*2+1:03}'), (phase,'allocator final draw to fallback reseed')
        assert old(f'h1-draw-{phase*2+1:03}')==old(f'h1-old-{phase*2+2:03}'), (phase,'fallback draw to candidate reseed')
        begin=old(f'h1-draw-{phase*2+2:03}')
        first=state(f'candidate-{phase:02}-first-state')
        last=state(f'candidate-{phase:02}-last-state')
        assert first==begin, (phase,'candidate scan starts at preceding helper output')
        assert last==advance(first,49), (phase,'candidate fifty-player draw boundary')
        scan_first=state(f'scan-{phase:02}-first-state')
        scan_last=state(f'scan-{phase:02}-last-state')
        assert scan_first==advance(last,1), (phase,'candidate scan joins interception scan')
        assert scan_last==advance(scan_first,blocks*50-1), (phase,'interception complete fifty-player blocks')
        target=old(f'h2-old-{phase+1:03}')if phase<19 else old('h1-old-041')
        assert advance(scan_last,1)==target, (phase,'scan end reaches next reseed without missing literal draws')
        assert advance(begin,DISTANCES[phase-1])==target, (phase,'measured inter-reseed LCG distance')
        for family in ('candidate','scan'):
            for edge,player in [('first',2),('last',51)]:
                prefix=f'{family}-{phase:02}-{edge}'
                assert integer(rows[prefix+'-group']['raw'],2,20,'group')==phase+1, (phase,family,edge,'decoded active group identity')
                assert integer(rows[prefix+'-player']['raw'],2,51,'cached player')==player, (phase,family,edge,'decoded first/last cached player slot')
        for edge in ('first','last'):
            prefix=f'scan-{phase:02}-{edge}'
            source=integer(rows[prefix+'-prestep']['raw'],1,3000,'pre-step sector')
            destination=integer(rows[prefix+'-destination']['raw'],1,3000,'destination sector')
            assert destination in graph[source], (phase,edge,'measured route arguments form a directed original warp edge')
            if edge=='last':
                world=rows['untouched']['world'];base=(50+destination)*137
                force=mbf(world[base+81:base+85]);owner=mbf(world[base+85:base+89])
                assert force>0 and owner==-1, (phase,'last sampled destination retains positive Xannor sector force')
    tail=old('h1-draw-041')
    for n in range(1,21):
        assert state(f'desertion-{n:02}-before')==advance(tail,n-1), (n,'twenty consecutive eager desertion draws')
    assert state('desertion-last-after')==advance(tail,20), 'last desertion post-draw boundary'
    assert state('lottery-before')==state('desertion-last-after'), 'desertion to lottery gate boundary'
    assert state('lottery-after')==advance(state('lottery-before'),1), 'single lottery post-draw boundary'
    assert 41+76+3+950+24800+20+1==25891, 'known literal-RND family accounting'


def verify(directory=DEFAULT,pins_path=PINS_FILE,native=NATIVE):
    directory=Path(directory);raw=Path(pins_path).read_bytes()
    assert SHA(raw)==PINS_SHA, 'immutable chronology manifest'
    pins=json.loads(raw)
    assert set(pins)=={'controls','native_sha256'}, 'chronology pin schema'
    matrix=expected_matrix();names={p.name for p in directory.iterdir()}
    assert names==set(matrix)==set(pins['controls']), 'complete 332-control boundary matrix'
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    for name,digest in BINARIES.items():assert SHA((ROOT/'archive/dos-original'/name).read_bytes())==digest, 'original binary identity'
    assert SHA(Path(native).read_bytes())==pins['native_sha256'], 'immutable chronology native bundle'
    verify_native(native,original)
    anchors=old_anchors()
    rows={name:verify_control(directory/name,pins['controls'][name],original)for name in sorted(names)}
    for name,row in rows.items():
        m=row['metadata']
        assert (m['site'],m['nth'],m['source'])==matrix[name], 'independent named phase boundary'
        assert m['clock']=='00:00:00' and m['occupied']==[] and m['patches']==[], 'unmodified baseline clock/input fixture'
        assert row['kind']==('untouched'if name=='untouched'else'body-end'if name.startswith('count-')else'nth-hit'), 'actual boundary classification'
    verify_semantics(rows,anchors)
    return {'controls':len(rows),'untouched':1,'body_end':4,'nth_hits':len(rows)-5,'native_reads':3,'mobile_groups':19,'literal_rng_draws':25891}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT)
    a=p.parse_args();print('Maintenance chronology verified:',verify(a.directory))
