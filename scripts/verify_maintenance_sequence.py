"""Independently verify bounded nth-hit maintenance evidence without DOSBox.

This checker never imports the acquisition script. Its patch reconstruction,
immutable raw pins, return classification and arithmetic constraints are separate
from the runner. Instrumented main-body return is not untouched DOS completion.
"""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

from verify_initial_maintenance import PINS as INITIAL_PINS
from verify_maintenance_rng import MAINT_BANNER, mbf, verify_launch
from verify_rng_clock import read_date, read_time
from verify_rng_native import image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'research/yt-maint/sequence-controls'
PINS_FILE = ROOT/'research/yt-maint/sequence-pins.json'
PINS_SHA = '04a1a7b6861d0cd8932c7da5869e000fc2f5981d1f6508bcfb5ee20973d9d112'
NATIVE = ROOT/'research/yt-maint/sequence-native/rea.json'
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINARIES = {
    'YTMAINT.EXE':'8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
    'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
}
META_KEYS = {'recipe','name','site','nth','source','clock','occupied','patches','binaries',
             'copied_sha256','inputs','complete','files'}
COMMON = {'TRACE.BIN','ERROR.LOG','OK.LOG','RETURN.LOG','DOSDATE.LOG','DOSTIME.LOG',
          'ENDDATE.LOG','ENDTIME.LOG','COMMANDS.TXT','dosbox.log'}
DATA_FILES = {'after-'+n+'.gz' for n in ('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT',
                                      'YTRMSG.DAT','YTSCORE.ASC','YTYNEWS.DAT')}
RND_SITES = {int(x,16) for x in '''0ba5 0be0 0c1c 16a9 16bb 16e5 1719 173a 1758
17a1 17b2 18cc 2237 226c 2363 25a0 260e 2c56 3348 3c0e 46af 485a 4fbf 50b4
537e 5513 551e 5541 554c 5570 557b 55f5 5622 5a25 5bed 61b2 632e 6351 6383
63ae 7656 7908 7989'''.split()}


def reconstructed_probe(raw, site, nth, source):
    assert type(site) is int and 0x73 <= site < len(raw)-517, 'site extent'
    assert type(nth) is int and 1 <= nth <= 65535, 'finite counter threshold'
    assert source=='caller' or type(source) is int and 0 <= source <= 65532, 'selected read extent'
    displaced = raw[512+site:517+site]
    assert len(displaced)==5, 'displaced instruction extent'
    # DS/CS return path, decrement preserving flags, selected DS read, DOS exit,
    # then exact displaced instruction and original continuation. Counter storage
    # is part of the dead return-path bytes, never runtime/fixture storage.
    if source=='caller':
        prefix=bytes.fromhex('0e1fba7000eb0d9c2eff0e70007514161f8d5602')
    else:
        prefix=bytes.fromhex('0e1fba6e00eb0b9c2eff0e6e007512ba')+struct.pack('<H',source)
    prefix += bytes.fromhex('bb0100b90400b440cd21b8004ccd219d')
    diagnostic = prefix + displaced + b'\xe9' + struct.pack('<H',(site+5-(0x70 if source=='caller'else 0x6e))&65535)
    diagnostic += struct.pack('<H',nth) + (b''if source=='caller'else b'C!')
    assert len(diagnostic)==46, 'diagnostic extent'
    output = bytearray(raw)
    output[0x244:0x272] = diagnostic
    output[512+site:517+site] = b'\xe9' + struct.pack('<H',(0x4b-site-3)&65535) + b'\x90\x90'
    assert len(output)==len(raw) and output[:512]==raw[:512], 'same-size/header patch'
    return bytes(output)


def verify_native(path, original):
    records=json.loads(Path(path).read_text())['records']
    wanted={'0x178f3':240,'0x11f51':120,'0x13311':187,'0x13b94':252}
    assert len(records)==len(wanted), 'native coverage'
    seen=set(); loaded=image(original)
    for r in records:
        v=r['normalized_result']; address=v['address']
        assert r['operation']=='read_bytes', 'native operation'
        assert r['subject']['name']=='YTMAINT.EXE', 'native subject'
        assert r['subject']['digest']=={'sha256':BINARIES['YTMAINT.EXE']}, 'native identity'
        assert address in wanted and address not in seen, 'native address'
        size=wanted[address]
        assert r['parameters']=={'address':address,'length':size}, 'native parameters'
        assert v['complete'] is True and v['requested_bytes']==v['returned_bytes']==size, 'native truncation'
        offset=int(address,16)-0x10000
        assert bytes.fromhex(v['bytes_hex'])==loaded[offset:offset+size], 'native relocated bytes'
        seen.add(address)
    assert seen==set(wanted), 'native completeness'


def expected_inputs(occupied):
    assert type(occupied) is list and occupied==sorted(set(occupied)), 'unique ordered occupied sectors'
    assert all(type(s) is int and 1<=s<=3000 for s in occupied), 'occupied sector range'
    inputs={}; patches=[]
    for n in ('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'):
        original=gzip.decompress((ROOT/'research/yt-maint/initial-controls/baseline-split'/('before-'+n+'.gz')).read_bytes())
        assert SHA(original)==INITIAL_PINS['baseline-split']['before-'+n+'.gz'], 'original fixture pin'
        data=bytearray(original)
        if n=='YTDATA.DAT':
            for sector in occupied:
                at=(50+sector)*137+93
                patches.append({'offset':at,'before':bytes(data[at:at+4]).hex(),'after':'00000082'})
                data[at:at+4]=bytes.fromhex('00000082')
        inputs[n]=SHA(data)
    return inputs,patches


def commands(clock):
    assert clock in ('00:00:00','00:00:02'), 'clock case'
    return ['date 11/02/2026','time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG',
            'ytmaint > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG',
            'if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROGRAM_RETURNED > RETURN.LOG',
            'date > ENDDATE.LOG','time > ENDTIME.LOG']


def classify_trace(trace, meta):
    """Classify the actual return boundary, not the mutable `complete` flag."""
    assert trace.startswith(MAINT_BANNER), 'maintenance output identity'
    if meta['site'] is None:
        assert trace.count(b'Daily Maintenance Completed OK')==1, 'untouched normal completion'
        assert trace.endswith(b'Daily Maintenance Completed OK\r\n'), 'untouched completion suffix'
        assert meta['complete'] is True, 'untouched return claim'
        return {'kind':'untouched'}
    assert b'Daily Maintenance Completed OK' not in trace, 'instrumented cleanup is bypassed'
    assert len(trace)>=len(MAINT_BANNER)+4, 'diagnostic extent'
    sample=trace[-4:]
    ended=sample[2:]==(bytes.fromhex('57cd')if meta['source']=='caller'else b'C!')
    assert type(meta['complete']) is bool and meta['complete']==ended, 'main-body-end claim'
    if ended:
        remaining=int.from_bytes(sample[:2],'little')
        assert 0<remaining<=meta['nth'], 'remaining finite counter'
        assert b'Generating Updated Scoreboard...' in trace[:-4], 'main-body end scoreboard witness'
        assert b'N o n  -  H u m a n   P l a y e r s' in trace[:-4], 'main-body end final phase witness'
        return {'kind':'body-end','count':meta['nth']-remaining}
    if meta['source']=='caller':
        return {'kind':'nth-hit','raw':sample,'caller_ip':int.from_bytes(sample[:2],'little'),'caller_cs':int.from_bytes(sample[2:],'little')}
    if meta['source']==0x234:
        state=int.from_bytes(sample,'little')
        assert state<2**24, '24-bit runtime state'
        return {'kind':'nth-hit','state':state,'raw':sample}
    return {'kind':'nth-hit','raw':sample}


def verify_control(folder, pin, original):
    folder=Path(folder); raw_meta=(folder/'result.json').read_bytes(); m=json.loads(raw_meta)
    assert set(m)==META_KEYS, 'metadata schema'
    assert m['recipe']=='maintenance-nth-site-v1' and m['name']==folder.name, 'control identity'
    assert m['binaries']==BINARIES, 'original binary identities'
    assert m['site'] is None or type(m['site']) is int, 'site type'
    assert m['site'] is None or m['site'] in RND_SITES|{0x7900,0x7946,0x7910,0x7991,0x794e}, 'selected known runtime boundary'
    assert m['source'] in (0x234,0x1a,0x7ea4,'caller'), 'selected state/FAC/argument source'
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


def expected_matrix():
    """Independent finite experiment identities, not acquisition-script imports."""
    out={}
    def add(name,site=None,nth=65535,source=0x234):out[name]=(site,nth,source)
    selected={0x2237,0x226c,0x2363,0x3348,0x3c0e,0x46af,0x537e,0x7900,0x7908,0x7946,0x7989}
    for group in ('baseline','repeat','shift','occupied'):
        add(group+'--untouched')
        for site in ((RND_SITES|{0x7900,0x7946})if group=='baseline'else selected):
            add(f'{group}--count-{site:04x}',site)
    for n in range(1,42):
        for label,site,source in [('old',0x7900,0x234),('timer',0x7900,0x1a),('seed',0x7908,0x234),('draw',0x7910,0x234)]:
            add(f'baseline--h1-{label}-{n:03}',site,n,source)
    for n in range(1,20):
        for label,site,source in [('old',0x7946,0x234),('timer',0x7946,0x1a),('seed',0x794e,0x234)]:
            add(f'baseline--h2-{label}-{n:03}',site,n,source)
    for n in range(1,77):add(f'baseline--h2-draw-{n:03}',0x7991,n)
    for n in (1,2,3,4,5,8,75,76):add(f'baseline--h2-fac-{n:03}',0x7991,n,0x1a)
    for n in range(1,5):
        for label,site,source in [('old',0x7900,0x234),('timer',0x7900,0x1a),('seed',0x7908,0x234),('draw',0x7910,0x234)]:
            add(f'occupied--h1-{label}-{n:03}',site,n,source)
    for helper,count,site in [('h1',41,0x7900),('h2',19,0x7946)]:
        for n in range(1,count+1):add(f'baseline--{helper}-caller-{n:03}',site,n,'caller')
    assert len(out)==463
    return out


def verify_semantics(observations):
    groups={}
    for name,row in observations.items():
        m=row['metadata']
        if row['kind']=='body-end':
            assert m['nth']==65535, 'complete counter threshold'
            key=name.split('--',1)[0]
            groups.setdefault(key,{})[m['site']]=row['count']
    for group, sites in groups.items():
        if 0x7900 in sites and 0x7908 in sites:assert sites[0x7900]==sites[0x7908], 'helper1 one seed/draw per invocation'
        if 0x7946 in sites and 0x7989 in sites:assert 4*sites[0x7946]==sites[0x7989], 'fixture helper2 four-draw loop'
    positive={0x2237:1,0x226c:1,0x2363:1,0x3348:950,0x3c0e:24800,0x46af:20,0x537e:1,0x7908:41,0x7989:76}
    expected_counts={site:positive.get(site,0)for site in RND_SITES}|{0x7900:41,0x7946:19}
    assert groups['baseline']==expected_counts, 'bounded literal-site count inventory'
    assert sum(groups['baseline'][site]for site in RND_SITES)==25891, 'bounded literal-site count total'
    for group in ('baseline','repeat','shift','occupied'):
        oracle=observations[group+'--untouched']
        for name,row in observations.items():
            if name.startswith(group+'--count-'):
                assert row['kind']=='body-end', 'finite complete site counter'
                assert row['outputs']==oracle['outputs'], (name,'instrumented body equals untouched all DAT/ASC outputs')
    assert observations['baseline--untouched']['outputs']==observations['repeat--untouched']['outputs'], 'untouched fixed-clock repeat'
    assert all(groups['baseline'][site]==count for site,count in groups['repeat'].items()), 'all selected repeat site counts'
    assert groups['baseline'][0x7900]==41 and groups['baseline'][0x7946]==19, 'bounded observed helper inventory'
    state=lambda name:observations[name]['state']
    raw=lambda name:observations[name]['raw']
    # The occupied fixture changes exactly one sector's planet-link gate. The
    # first generated candidate remains1095 but is rejected, preserving the
    # consumed draw's low byte for a new seed and accepting candidate1792 next.
    candidate=lambda value:1+3000*value//2**24
    first=state('baseline--h1-draw-001')
    rejected=state('occupied--h1-draw-001')
    accepted=state('occupied--h1-draw-002')
    assert candidate(first)==candidate(rejected)==1095, 'unchanged first occupied candidate'
    assert state('occupied--h1-old-002')==rejected, 'rejected candidate state flows into second reseed'
    assert candidate(accepted)==1792, 'second occupied-fixture candidate'
    assert groups['baseline'][0x7908]==41 and groups['occupied'][0x7908]==42, 'one additional occupied-candidate helper call'
    for group,wanted,receipts in [('baseline',1095,1),('occupied',1792,2)]:
        oracle=observations[group+'--untouched']; world=oracle['world']
        links=[sector for sector in range(1,3001)if mbf(world[(50+sector)*137+93:(50+sector)*137+97])==1]
        assert links==[wanted], (group,'only accepted candidate links Wanderer planet1')
        assert oracle['trace'].count(b'Wanderer has successfully warped!\r\n')==receipts, (group,'optimistic success receipt precedes occupancy validation')
    for group,helper,total in [('baseline','h1',41),('baseline','h2',19),('occupied','h1',4)]:
        for n in range(1,total+1):
            key=f'{group}--{helper}'
            old=state(f'{key}-old-{n:03}'); timer=raw(f'{key}-timer-{n:03}')
            seed=state(f'{key}-seed-{n:03}')
            expected=(old&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)
            assert seed==expected, (key,n,'RANDOMIZE retains old low byte and uses sampled TIMER')
            if helper=='h1':
                assert state(f'{key}-draw-{n:03}')==(214013*seed+1744579)%2**24, (key,n,'one exact helper1 LCG draw')
    for n in range(1,77):
        before=state(f'baseline--h2-seed-{(n-1)//4+1:03}')if n%4==1 else state(f'baseline--h2-draw-{n-1:03}')
        assert state(f'baseline--h2-draw-{n:03}')==(214013*before+1744579)%2**24, (n,'four-draw helper2 recurrence')
    for n in (1,2,3,4,5,8,75,76):
        assert mbf(raw(f'baseline--h2-fac-{n:03}'))==state(f'baseline--h2-draw-{n:03}')/2**24, (n,'helper2 returned RND FAC')
    caller_segments=set()
    for helper,count,allowed in [('h1',41,{0x1f88,0x26a8,0x2de4,0x320a,0x3284,0x437a,0x4546,0x48cf,0x53b4,0x5442,0x549f,0x7312}),('h2',19,{0x31a3,0x4aa4})]:
        for n in range(1,count+1):
            row=observations[f'baseline--{helper}-caller-{n:03}']
            assert row['caller_ip']in allowed and row['caller_cs']>0, (helper,n,'actual far-call return identity')
            caller_segments.add(row['caller_cs'])
    assert len(caller_segments)==1, 'shared observed caller code segment'
    assert [observations[f'baseline--h1-caller-{n:03}']['caller_ip']for n in range(1,42)]==[0x1f88,0x26a8]+[0x320a,0x3284]*19+[0x437a], 'bounded helper1 phase caller sequence'
    assert [observations[f'baseline--h2-caller-{n:03}']['caller_ip']for n in range(1,20)]==[0x31a3]*19, 'bounded helper2 phase caller sequence'
    return groups


def verify(directory=DEFAULT,pins_path=PINS_FILE,native=NATIVE):
    directory=Path(directory); raw=Path(pins_path).read_bytes()
    assert SHA(raw)==PINS_SHA, 'immutable independent manifest'
    pins=json.loads(raw)
    assert set(pins)=={'controls','native_sha256'}, 'manifest schema'
    names={p.name for p in directory.iterdir()}
    assert names==set(pins['controls'])==set(expected_matrix()), 'complete retained matrix'
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    for n,h in BINARIES.items():assert SHA((ROOT/'archive/dos-original'/n).read_bytes())==h, 'original binary pin'
    inventory={i-512 for i in range(512,len(original)-4)if original[i:i+5]in(bytes.fromhex('cd3d339090'),bytes.fromhex('cd3d349090'))}
    assert inventory==RND_SITES, '43-site literal inventory'
    assert SHA(Path(native).read_bytes())==pins['native_sha256'], 'immutable native bundle'
    verify_native(native,original)
    observed={n:verify_control(directory/n,pins['controls'][n],original)for n in sorted(names)}
    for name,row in observed.items():
        m=row['metadata']; group=name.split('--',1)[0]
        assert (m['site'],m['nth'],m['source'])==expected_matrix()[name], 'independent named boundary identity'
        assert m['clock']==('00:00:02'if group=='shift'else'00:00:00'), 'named clock case'
        assert m['occupied']==([1095]if group=='occupied'else[]), 'named occupancy case'
    verify_semantics(observed)
    return {'controls':len(observed),'untouched':sum(r['kind']=='untouched'for r in observed.values()),
            'body_end':sum(r['kind']=='body-end'for r in observed.values()),
            'nth_hits':sum(r['kind']=='nth-hit'for r in observed.values()),'native_reads':4}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT)
    a=p.parse_args();print('Maintenance sequence evidence verified:',verify(a.directory))
