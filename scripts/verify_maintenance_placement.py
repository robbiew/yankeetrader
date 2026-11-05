"""Independent placement/cache evidence checks, without importing a writer/model.

The cache probe is an explicitly patched early exit, never an untouched complete
maintenance run. Full outputs are paired by all six independent capture modes.
"""
import argparse
import copy
import datetime
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import struct

import verify_maintenance_clock_matrix as clocks
from verify_rng_clock import read_date,read_time
from verify_rng_native import image

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/placement-cache-controls'
PINS_SHA='3bf82e8911e2895c525dfc77a398aba58bdc915572b949696cac200cbe202bf0'
SHA=lambda b:hashlib.sha256(b).hexdigest()
MODES={'unobserved-a':'unobserved','unobserved-b':'unobserved','attach-only':'attach-only','observed-a':'observed','observed-b':'observed','observed-c':'observed','cache-probe':'unobserved'}
CASES={
 'wanderer-reject-two':[[1146,93,2],[1843,93,2]],
 'wanderer-reject-three':[[1146,93,2],[1843,93,2],[1346,93,2]],
 'wanderer-positive-fraction':[[1146,93,.25]],
 'wanderer-negative-link':[[1146,93,-1]],
 'wanderer-zero-residue':[[1146,93,'00004800']],
 'base-positive-fraction':[[2649,93,.25]],
 'duplicate-hq':[[53,105,849]],
 'duplicate-hq-chain':[[53,105,849],[54,105,849],[71,105,849]],
 'duplicate-mobile':[[53,105,1000],[54,105,1000],[1051,81,37],[1051,85,-1]],
 'pointer-neutral-sector':[[53,105,3000],[3051,81,37],[3051,85,0]],
 'pointer-mercenary-sector':[[53,105,3000],[3051,81,37],[3051,85,-2]],
 'unpointed-friendly-merge':[[1599,81,37],[1599,85,-1]],
}
SOURCES={'recover_maintenance_placement.py','observe_maintenance_placement.js','capture_maintenance_clock_neutral.mjs','recover_maintenance_sequence.py','replay_qb_graph.py','verify_maintenance_clock_neutral.py'}
COMMON={'COMMANDS.TXT','launch.json','controller.json','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','TRACE.BIN','OK.LOG','ERROR.LOG','RETURN.LOG','dosbox.stdout','dosbox.stderr'}
OUTPUTS=set(clocks.neutral.OUTPUTS)


def encode(value):
    """Exact bounded dyadic encoder for independently declared fixture values."""
    if not value:return bytes(4)
    sign=0x800000 if value<0 else 0
    absolute=Fraction(abs(value));exponent=absolute.numerator.bit_length()-absolute.denominator.bit_length()
    if absolute<Fraction(2)**exponent:exponent-=1
    mantissa=absolute*Fraction(2)**(23-exponent)
    assert mantissa.denominator==1 and 0<=exponent+129<=255,'fixture requires exact bounded MBF'
    return ((int(mantissa)-(1<<23))|sign).to_bytes(3,'little')+bytes([exponent+129])


def field(world,record,offset):
    start=(record-1)*137+offset
    return clocks.neutral.mbf_fraction(world[start:start+4])


def rawfield(world,record,offset):
    start=(record-1)*137+offset;return world[start:start+4]


def before_inputs(case):
    assert case in CASES,'independent case inventory'
    result=clocks.neutral.before_input_bytes();world=bytearray(result['YTDATA.DAT'])
    for record,offset,value in CASES[case]:
        start=(record-1)*137+offset
        world[start:start+4]=bytes.fromhex(value)if type(value)is str else encode(value)
    result['YTDATA.DAT']=bytes(world)
    return result


def expected_cache(before):
    """Pack the40 source-owned cells; the two unused cells are unspecified."""
    assert len(before)==4151*137,'complete before-world cache input'
    locations=[0]+[int(field(before,51+g,105))for g in range(1,21)]
    assert all(0<=s<=3000 for s in locations),'bounded original cache pointer'
    forces=[0]*21;consumed=set()
    for group in range(1,21):
        sector=locations[group]
        if sector>0 and sector not in consumed and field(before,51+sector,85)==-1:
            force=field(before,51+sector,81)
            assert force.denominator==1 and 0<=force<=1000000,'whole bounded cache force'
            forces[group]=int(force);consumed.add(sector)
    for first in range(1,20):
        for second in range(first+1,21):
            if locations[first]==locations[second]:
                locations[second]=0;forces[first]+=forces[second];forces[second]=0
    for group in range(1,21):
        if locations[group]<1 or forces[group]<1:locations[group]=forces[group]=0
    payload=b''.join(encode(n)for n in locations+forces)
    assert len(payload)==168,'complete source array extent'
    return payload,consumed


def patched_original(original):
    """Independent fixed29b7/1c52 probe, widened from4 to168 output bytes."""
    site=0x29b7
    assert original[512+site:514+site]==b'\xcd\x3f','declared whole original dispatch boundary'
    code=bytearray.fromhex('0e1fba6e00eb0b9c2eff0e6e007512ba521cbb0100b9a800b440cd21b8004ccd219d')
    code.extend(original[512+site:517+site])
    code.extend(b'\xe9'+struct.pack('<H',(site+5-0x6e)&65535));code.extend(b'\x01\x00C!')
    assert len(code)==46,'fixed probe extent'
    result=bytearray(original);result[0x244:0x272]=code
    result[512+site:517+site]=b'\xe9'+struct.pack('<H',(0x4b-site-3)&65535)+b'\x90\x90'
    return bytes(result)


def verify_cache(before,after,trace):
    payload,consumed=expected_cache(before)
    boundary=b'Locating Top Player... (For Groups 16 - 20 to Pick on!)\r\n'
    assert trace.count(boundary)==1,'unique source-qualified cache boundary'
    offset=trace.index(boundary)+len(boundary)
    assert len(trace)-offset==168,'exact declared168byte cache snapshot'
    actual=trace[offset:]
    for index in (*range(1,21),*range(22,42)):
        assert actual[4*index:4*index+4]==payload[4*index:4*index+4],'forty source-owned cache fields match before-only normalization'
    assert b'Daily Maintenance Completed OK'not in trace,'early cache exit is not full maintenance'
    assert len(after)==len(before)==4151*137,'complete early cache world'
    for group in range(1,21):
        assert rawfield(after,51+group,105)==bytes(4),'all stored group pointers cleared before normalization'
    for sector in range(1,3001):
        if sector in consumed:
            for off in(81,85):assert rawfield(after,51+sector,off)==bytes.fromhex('00008000'),'native consumed-sector raw zero'
        else:
            for off in(81,85):assert rawfield(after,51+sector,off)==rawfield(before,51+sector,off),'cache does not consume foreign/unpointed sector force/title'
    return dict(cache_force=sum(int(clocks.neutral.mbf_fraction(payload[n:n+4]))for n in range(88,168,4)),consumed=len(consumed))


def verify_observation(observation):
    """Authenticate every new RNG read before using original source clock parser."""
    assert observation.get('recipe')=='host-dos-placement-cache-observer-v1','placement source observation identity'
    standard=copy.deepcopy(observation);standard['recipe']='host-dos-clock-matrix-observer-v1'
    witnesses=[]
    for ordinal,(source,event)in enumerate(zip(observation['events'],standard['events']),1):
        states=[]
        for side in('before','after'):
            raw=event[side].pop('rng_raw')
            assert type(raw)is str and re.fullmatch('[0-9a-f]{8}',raw),'four complete raw RNG bytes'
            state=int.from_bytes(bytes.fromhex(raw),'little')
            assert state<2**24,'actual24bit RNG state'
            states.append(state)
        assert states[0]==states[1],'DOS callback preserves RNG state'
        pair=clocks.event_pair(event,ordinal)
        if pair.get('kind')=='timer'and pair.get('role')=='helper1'and pair['nested_return_ip']in(0x1f88,0x437a):
            witnesses.append(dict(role='wanderer'if pair['nested_return_ip']==0x1f88 else'base',ordinal=ordinal,old_state=states[0],timer=pair['seconds']))
    inputs=clocks.model_inputs(standard)
    assert inputs['cycles']==200000,'fixed observed CPU budget'
    startup=bytearray(inputs['startup']);startup[2]^=128
    seeded=5|((startup[0]^startup[2])<<8)|((startup[1]^startup[3])<<16)
    assert witnesses and witnesses[0]['role']=='wanderer'and witnesses[0]['old_state']==seeded,'first source helper preserves actual startup seed before any draw'
    return witnesses,inputs


def verify_placements(before,outputs,trace,witnesses):
    assert len(witnesses)>=2,'both placement source phases observed'
    links={s:field(before,51+s,93)for s in range(1,3001)}
    accepted={};attempts={'wanderer':0,'base':0};previous=None
    for row in witnesses:
        assert set(row)=={'role','ordinal','old_state','timer'},'exact independent placement witness'
        role=row['role'];old=row['old_state'];timer=row['timer']
        assert role in attempts and role not in accepted,'no placement draws after acceptance'
        assert type(old)is int and 0<=old<2**24 and type(timer)is bytes and len(timer)==4,'bounded raw placement state/timer'
        assert role!='base'or 'wanderer'in accepted,'original placement phase order'
        assert type(row['ordinal'])is int and row['ordinal']>0 and(previous is None or row['ordinal']>previous['ordinal']),'ordered unique placement source events'
        if previous is not None and previous['role']==role:assert old==previous['result'],'rejection continues prior helper state'
        seed=(old&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)
        state=(214013*seed+1744579)&0xffffff
        product=struct.unpack('<f',struct.pack('<f',state*3000/16777216))[0]
        candidate=math.floor(product)+1;attempts[role]+=1
        assert 1<=candidate<=3000,'bounded original candidate'
        if links[candidate]<=0:
            accepted[role]=candidate;links[candidate]=1 if role=='wanderer'else 99
            if role=='wanderer':links[int(field(before,1,117))]=100
        previous=dict(role=role,result=state,ordinal=row['ordinal'])
    assert set(accepted)=={'wanderer','base'},'complete successful placement phases'
    world=outputs['YTDATA.DAT'];assert len(world)==4151*137,'complete accepted world'
    for role,slot in [('wanderer',1),('base',99)]:
        actual=[s for s in range(1,3001)if field(world,51+s,93)==slot]
        assert actual==[accepted[role]],'actual accepted placement agrees with source RNG/strict-positive gate'
    assert trace.count(b'Wanderer has successfully warped!')==attempts['wanderer'],'public optimistic receipt printed per attempt, not per acceptance'
    assert outputs['YTNEWS.DAT'].count(b'The Wanderer regenerated with P.H.O.E.N.I.X. device!')==1,'single actual restored-planet news'
    assert outputs['YTNEWS.DAT'].count(b'  -  The Mercenaries have built a home base using a captured Genesis Device!')==1,'single actual restored-Base news'
    assert outputs['YTRMSG.DAT']==b'','no invented private placement message'
    return dict(accepted=accepted,attempts=attempts)


def verify_force_accounting(before,outputs,case):
    """Independent saved-force/news accounting, not a combat-stream prediction."""
    assert set(outputs)==OUTPUTS,'all six complete output files'
    world=outputs['YTDATA.DAT'];assert len(world)==4151*137,'complete force accounting world'
    initial=sum(field(before,51+s,81)for s in range(1,3001))
    current=[];scores={-1:0,-2:0}
    for sector in range(1,3001):
        force=field(world,51+sector,81);owner=field(world,51+sector,85)
        assert force.denominator==1 and 0<=force<=1000000,'bounded nonnegative saved sector force'
        current.append(force)
        if owner in scores:scores[owner]+=int(force)*100
    lines=outputs['YTNEWS.DAT'].split(b'\r\n');losses=0
    for index,line in enumerate(lines):
        if b'Xannor attacked the planet'in line:
            match=re.fullmatch(rb' \*\*\* ([1-9][0-9]*) Xannor attacked the planet "The Wanderer"',line)
            assert match and lines[index+1]==b' *** Xannor fighters destroyed!','exact public casualty outcome'
            losses+=int(match[1])
    assert sum(current)+losses==initial,'public casualties reconcile with unique physical before/saved forces'
    rows=re.findall(rb'^ *([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% +([0-9][0-9,]*) +[0-9]+\.[0-9]{2}% *\r?$',outputs['YTSCORE.ASC'],re.M)
    assert len(rows)==1,'one actual NPC numeric scoreboard row'
    reported=tuple(int(value.replace(b',',b''))for value in rows[0])
    assert reported==(scores[-1],scores[-2]),'both NPC scoreboard columns reflect actual faction force'
    if case=='unpointed-friendly-merge':
        original=field(before,1599,81)
        assert original==37 and field(world,1599,81)>original and field(world,1599,85)==-1,'unpointed friendly deployment combines only at final destination'
        assert any(field(world,51+g,105)==1548 for g in range(1,21)),'cached mobile actually ends at merge sector'
    return dict(initial=int(initial),survivors=int(sum(current)),reported_losses=losses)


def commands():
    return ['date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']


def verify_launch(folder,meta):
    argv=json.loads((folder/'launch.json').read_text())
    assert argv==meta['argv']and argv[0]=='/opt/homebrew/bin/dosbox-staging','actual declared host launch'
    assert len(argv)>8 and argv[8].startswith('mount c /private/tmp/'),'fresh disposable mount'
    expected=[argv[0],'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']
    expected += [value for command in [argv[8],'c:']+commands()+['exit']for value in('-c',command)]
    assert argv==expected and (folder/'COMMANDS.TXT').read_text()=='\n'.join(commands())+'\n','fixed complete DOS command inventory'
    messages=[line.split(' | ',1)[1]for line in(folder/'dosbox.stderr').read_text().splitlines()if' | 'in line]
    args=[shlex.split(m[11:])for m in messages if m.startswith('arguments: ')]
    assert args==[argv],'actual host launch witness'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1,'actual host version'
    assert len([m for m in messages if m.startswith('CPU: Setting fixed 200000 cycles.')])==1,'actual fixed CPU budget'
    assert 'SDL: dummy video initialised'in messages and "MIXER: Sound output disabled ('nosound' mode)"in messages,'actual dummy video/audio'
    assert (folder/'dosbox.stdout').read_bytes()==b'','complete empty stdout'
    assert read_date((folder/'DOSDATE.LOG').read_bytes())==datetime.date(2026,11,2),'actual initial DOS date'
    assert read_time((folder/'DOSTIME.LOG').read_bytes())==0,'actual initial DOS midnight'
    enddate=read_date((folder/'ENDDATE.LOG').read_bytes());endtime=read_time((folder/'ENDTIME.LOG').read_bytes())
    elapsed=(enddate-datetime.date(2026,11,2)).days*86400+endtime
    assert 0<elapsed<40,'actual bounded advancing DOS time'
    return Path(argv[8][8:])


def verify_case(folder,case,mode,observer):
    folder=Path(folder);meta=json.loads((folder/'capture.json').read_text())
    assert set(meta)=={'recipe','case','mode','date','clock','cycles','patches','argv','host_sha256','guests','inputs','outputs','controller','elapsed_seconds','files'},'exact placement metadata schema'
    assert case in CASES and mode in MODES and (meta['recipe'],meta['case'],meta['mode'])==('maintenance-placement-cache-v1',case,mode),'independent case/mode identity'
    assert (meta['date'],meta['clock'],meta['cycles'])==('11/02/2026','00:00:00',200000)and meta['patches']==CASES[case],'independent a-priori fixture declaration'
    assert meta['host_sha256']==clocks.neutral.HOST_SHA and 0<meta['elapsed_seconds']<40,'pinned host and bounded capture'
    before=before_inputs(case);assert meta['inputs']=={n:SHA(b)for n,b in before.items()},'independently reconstructed three before-inputs'
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    assert SHA(original)==clocks.GUESTS['YTMAINT.EXE'],'immutable original maintenance'
    guests=dict(clocks.GUESTS)
    if mode=='cache-probe':guests['YTMAINT.EXE']=SHA(patched_original(original))
    assert meta['guests']==guests,'unmodified full-run guests or exact declared early cache probe'
    names=COMMON|{'after-'+n+'.gz'for n in(OUTPUTS if mode!='cache-probe'else OUTPUTS-{'YTSCORE.ASC'})}
    if MODES[mode]!='unobserved':names|={'host-time.json.gz','loaded-observer.js'}
    assert set(meta['files'])==names and {p.name for p in folder.iterdir()}==names|{'capture.json'},'complete exact capture artifact inventory'
    for name in names:assert SHA((folder/name).read_bytes())==meta['files'][name],'declared raw capture file hash '+name
    mounted=verify_launch(folder,meta)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n','natural DOS return witnesses'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'],'actual lifecycle metadata'
    trace=(folder/'TRACE.BIN').read_bytes();assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n'),'original maintenance transcript header'
    observation=None;witnesses=None
    if MODES[mode]!='unobserved':
        obraw=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(obraw)
        config=dict(observe=MODES[mode]=='observed',output=str(mounted/'host-time.json'))
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer,'exact actual observer source/config'
        if config['observe']:witnesses,_=verify_observation(observation)
        else:
            assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}and observation['recipe']=='host-dos-placement-cache-observer-v1'and observation['observe']is False and observation['events']==observation['errors']==[]and observation['exit_code']==observation['dropped']==0,'attach-only has no hooks/events'
            clocks.neutral.verify_module(observation['module'])
        clocks.neutral.verify_controller(controller,MODES[mode],observation,obraw)
    else:clocks.neutral.verify_controller(controller,'unobserved')
    outputs={name:gzip.decompress((folder/('after-'+name+'.gz')).read_bytes())for name in(OUTPUTS if mode!='cache-probe'else OUTPUTS-{'YTSCORE.ASC'})}
    assert meta['outputs']=={n:SHA(b)for n,b in outputs.items()},'complete raw output identity'
    if mode=='cache-probe':verify_cache(before['YTDATA.DAT'],outputs['YTDATA.DAT'],trace)
    else:
        assert trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'),'complete untouched maintenance footer'
        assert len(outputs['YTDATA.DAT'])==4151*137,'complete full-run world'
        verify_force_accounting(before['YTDATA.DAT'],outputs,case)
        if witnesses is not None:verify_placements(before['YTDATA.DAT'],outputs,trace,witnesses)
    return dict(before=before,outputs=outputs,witnesses=witnesses,trace=trace)


def verify_native(root):
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    assert SHA(original)==clocks.GUESTS['YTMAINT.EXE'],'original native identity'
    loaded=image(original);records=json.loads((root/'native/rea.json').read_text())['records']
    assert len(records)==4,'four complete original native reads'
    ranges={(0x126c9,744),(0x13e30,323),(0x11f50,256),(0x14355,148)}
    observed=set()
    for record in records:
        params=record['parameters'];key=(int(params['address'],16),params['length']);observed.add(key)
        assert key in ranges and record['operation']=='read_bytes'and record['subject']['name']=='YTMAINT.EXE'and record['subject']['digest']['sha256']==clocks.GUESTS['YTMAINT.EXE'],'original native subject/range'
        result=record['normalized_result'];data=bytes.fromhex(result['bytes_hex']);address,length=key
        assert result['complete']is True and result['requested_bytes']==result['returned_bytes']==len(data)==length,'complete independent native extent'
        assert data==loaded[address-0x10000:address-0x10000+length],'native bytes match independently relocated original'
    assert observed==ranges,'exact four distinct native ranges'


def verify(directory=DEFAULT):
    directory=Path(directory);raw=(directory/'pins.json').read_bytes()
    assert SHA(raw)==PINS_SHA,'immutable placement/cache corpus manifest'
    pins=json.loads(raw);assert set(pins)=={'files'},'exact independent manifest schema'
    actual={str(p.relative_to(directory))for p in directory.rglob('*')if p.is_file()and p.name!='pins.json'}
    assert actual==set(pins['files']),'complete pinned artifact inventory'
    for name,digest in pins['files'].items():assert SHA((directory/name).read_bytes())==digest,'immutable artifact '+name
    assert json.loads((directory/'recipe.json').read_text())=={'recipe':'maintenance-placement-cache-v1','cases':CASES},'independent complete fixture recipe'
    assert {p.name for p in(directory/'acquisition').iterdir()}==SOURCES,'complete frozen acquisition source inventory'
    assert {p.name for p in directory.iterdir()}==set(CASES)|{'pins.json','recipe.json','native','acquisition'},'twelve-case corpus inventory'
    verify_native(directory)
    observer=(directory/'acquisition/observe_maintenance_placement.js').read_text()
    accepted={}
    for case in CASES:
        assert {p.name for p in(directory/case).iterdir()}==set(MODES),'all seven modes including early cache probe'
        cases={mode:verify_case(directory/case/mode,case,mode,observer)for mode in MODES}
        reference=cases['unobserved-a']['outputs']
        for mode,result in cases.items():
            if mode!='cache-probe':assert result['outputs']==reference,'all six complete outputs equal both unobserved controls'
        for mode in('observed-a','observed-b','observed-c'):
            values=verify_placements(cases[mode]['before']['YTDATA.DAT'],reference,cases[mode]['trace'],cases[mode]['witnesses'])
            if case in accepted:assert values==accepted[case],'repeat source-qualified placement outcomes'
            accepted[case]=values
    return dict(cases=12,full_runs=72,cache_probes=12,paired_files=432,native_reads=4,placements=accepted)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT);a=p.parse_args()
    print('Placement/cache evidence verified:',verify(a.directory))
