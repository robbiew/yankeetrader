"""Independent source-qualified parsing of shifted maintenance clock observations.

This parser takes raw host-observed DOS returns only. It reads no after-world,
expected timestamp table or previous guest-probe timing arrays. TIMER, DATE$ and
TIME$ are separate native paths; display time is not a synchronized timestamp.
"""
import argparse
import datetime
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import re
import shlex
import struct

import verify_maintenance_clock_neutral as neutral

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/clock-matrix-controls'
PINS_FILE=ROOT/'research/yt-maint/clock-matrix-pins.json'
PINS_SHA='6156ee078a8a00edbfe6ad89e44fa8fe592295f025b9285582fdc65b3b7310f7'
SHA=lambda b:hashlib.sha256(b).hexdigest()
clock_to_raw=neutral.clock_to_raw
mbf_fraction=neutral.mbf_fraction
GUESTS=neutral.GUESTS
# Selected original BRUN entry/INT-return contexts. TIMER's window includes one
# MZ far-call segment word, fixed up to the observed runtime segment at byte29.
CONTEXTS={
    0xc137:('timer',0x2c,0xc12f,7,'50535152b42ccd21','e8d500e936ffeb8150535152b42ccd21b03cf6e532ed03c18bd89a80a80000b8'),
    0xc07f:('date',0x2a,0xc06b,9,'8926080a50515256','50515256bb0a00e812e05352b42acd215b8ac6e87a01b02de881018ac2e87001'),
    0xc0f7:('time',0x2c,0xc0e3,9,'8926080a50515256','50515256bb0800e89adf5352b42ccd2180fa327214fec680fe3c720db600fec1'),
}
TIMER_CALLERS={0x007d:'startup',0x0927:'port',0x125b:'planet',0x218b:'xannoron',0x78fd:'helper1',0x7943:'helper2'}
DATE_CALLERS={0x04ad:'news',0x06ad:'cloak_notice',0x79ed:'calendar',0x85f9:'score'}
TIME_CALLERS={0x049c:'news',0x0694:'cloak_notice',0x8612:'score'}
CALENDAR_CALLERS={0x033a:'startup',0x083e:'port',0x104b:'planet',0x1daf:'wanderer',0x20fc:'xannoron',0x41d3:'base',0x5785:'final'}
HELPER_CALLERS={
    'helper1':{0x1f88,0x26a8,0x2de4,0x320a,0x3284,0x437a,0x4546,0x48cf,0x53b4,0x5442,0x549f,0x7312},
    'helper2':{0x31a3,0x4aa4},
}


def dos_date(cx,dx,ax):
    assert all(type(x)is int and 0<=x<=65535 for x in(cx,dx,ax)), 'DOS date register widths'
    value=datetime.date(cx,dx>>8,dx&255)
    assert 1900<=value.year<=2099, 'bounded native DATE$ formatting century'
    assert ax==0x2a00+(value.weekday()+1)%7, 'actual DOS date weekday and function return'
    return value


def native_time_text(cx,dx):
    clock_to_raw(cx,dx) # independently validate all returned DOS time fields
    hour,minute,second,hundredth=cx>>8,cx&255,dx>>8,dx&255
    if hundredth>=50:
        second+=1
        if second==60:
            second=0;minute+=1
            if minute==60:minute=0;hour+=1
    # Original TIME$ does not wrap carried hour24 or synchronize a DATE$ call.
    assert 0<=hour<=24 and(hour!=24 or minute==second==0), 'native carried display clock'
    return f'{hour:02}:{minute:02}:{second:02}'


def _port(raw):
    value=mbf_fraction(bytes.fromhex(raw))
    assert value.denominator==1 and 1<=value<=1000, 'bounded source-qualified port index'
    return int(value)


def _nested(before,words,entry,main_cs,allowed):
    frame=bytes.fromhex(before['bp_frame']);bpwords=struct.unpack('<32H',frame)
    returned,segment=bpwords[1],bpwords[2]
    assert returned in allowed and segment==main_cs, 'source-qualified QB helper far-caller identity'
    assert before['nested_application_call']==(b'\x9a'+struct.pack('<HH',entry,main_cs)).hex(), 'original QB helper caller fixup'
    displacement=before['bp']-before['sp']
    assert 0<=displacement<=58, 'captured BP frame overlaps actual interrupt stack'
    stack=bytes.fromhex(before['stack']);overlap=min(64-displacement,64)
    assert stack[displacement:displacement+overlap]==frame[:overlap], 'independent BP and SP raw frame agreement'
    return returned


def event_pair(event,ordinal):
    assert set(event)=={'ordinal','function','before','after'}, 'exact matrix event schema'
    assert type(event['ordinal'])is int and event['ordinal']==ordinal, 'contiguous complete matrix event pairs'
    function=event['function'];assert type(function)is int and function in(0x2a,0x2c), 'declared observed DOS function'
    before,after=event['before'],event['after']
    regs={'ax','cx','dx','ds','ss','cs','sp','ip','bp'}
    fields=regs|{'pic','cycles','cycle_left','cycle_max','auto_adjust','runtime_signature','application_call','caller_code',
                 'nested_application_call','bp_frame','ds_phys','ss_phys','stack','port_raw'}
    for row in(before,after):
        assert set(row)==fields, 'complete matrix guest snapshot schema'
        assert all(type(row[k])is int and 0<=row[k]<=65535 for k in regs), '16-bit actual guest registers'
        for key in('cycles','cycle_left','cycle_max','pic','auto_adjust'):
            assert type(row[key])is int, 'actual host scheduler field type'
        assert row['cycle_max']in(10000,100000,200000)and row['auto_adjust']==0, 'declared fixed CPU profile without auto adjustment'
        assert 0<=row['cycles']<=row['cycle_max'] and 0<=row['cycle_left']<=row['cycle_max'] and row['cycles']+row['cycle_left']<=row['cycle_max'], 'bounded actual remaining CPU budget'
        assert row['pic']>=0 and row['ds_phys']==16*row['ds'] and row['ss_phys']==16*row['ss'], 'actual real-mode segment cache'
        for key,length in [('stack',128),('bp_frame',128),('caller_code',64),('port_raw',8)]:
            assert isinstance(row[key],str)and re.fullmatch('[0-9a-f]{'+str(length)+'}',row[key]), 'bounded raw context: '+key
    assert before['ax']>>8==function and after['ax']>>8==function, 'actual DOS entry/return function pairing'
    for key in('ds','ss','cs','sp','bp','ds_phys','ss_phys','stack','bp_frame','port_raw','runtime_signature','application_call','caller_code','nested_application_call','cycle_max','auto_adjust'):
        assert before[key]==after[key], 'unchanged paired guest/code context: '+key
    assert before['cs']==0xf000 and before['ip']==0x13e5 and after['ip']==before['ip']+(2 if function==0x2c else 0), 'distinct original DOS date/time callback return behavior'
    ticks=after['pic']-before['pic'];assert ticks in(0,1), 'bounded nested BIOS scheduler tick transition'
    delta=after['cycles']+after['cycle_left']-before['cycles']-before['cycle_left']-ticks*before['cycle_max']
    assert delta in(-5,-6), 'five-instruction BIOS budget with at most one failed core loop check'
    if delta==-6:assert before['cycles']<5, 'extra exhausted-core decrement has a genuinely exhausted initial slice'
    if before['cycles']<5 and delta==-5:assert ticks==1, 'lost exhausted-check cycle requires actual PIC tick reset'
    if function==0x2c:
        assert after['ax']==0x2c00, 'original DOS time return AL zero'
        seconds,minutes=clock_to_raw(after['cx'],after['dx']);date=None
    else:date=dos_date(after['cx'],after['dx'],after['ax']);seconds=minutes=None
    words=struct.unpack('<32H',bytes.fromhex(before['stack']))
    result=dict(function=function,before=before,after=after,words=words,seconds=seconds,minutes=minutes,date=date,ordinal=ordinal)
    if words[0]not in CONTEXTS:
        assert before['runtime_signature']is None and before['application_call']is None and before['nested_application_call']is None, 'unqualified DOS event has no forged BRUN attribution'
        assert words[0]==0x20c8 and words[1]==0xf000, 'selected external DOS shell clock caller'
        result['kind']='unqualified';return result
    kind,expected_function,entry,index,signature,window=CONTEXTS[words[0]]
    assert function==expected_function, 'original BRUN handler agrees with DOS operation'
    runtime_cs=words[1];main_cs=words[index+1];returned=words[index]
    assert runtime_cs>0 and main_cs>0 and runtime_cs!=main_cs, 'actual separate runtime/application load segments'
    assert before['runtime_signature']==signature, 'original complete BRUN clock entry signature'
    expected=bytearray.fromhex(window)
    if kind=='timer':struct.pack_into('<H',expected,29,runtime_cs)
    assert before['caller_code']==expected.hex(), 'original complete DOS interrupt caller window with correct relocation'
    assert before['application_call']==(b'\x9a'+struct.pack('<HH',entry,runtime_cs)).hex(), 'original application clock dispatch fixup'
    callers={'timer':TIMER_CALLERS,'date':DATE_CALLERS,'time':TIME_CALLERS}[kind]
    assert returned in callers, 'all qualified clock applications have an explicit original source site'
    role=callers[returned];nested=None
    if kind=='date'and role=='calendar':nested=_nested(before,words,0x79e3,main_cs,set(CALENDAR_CALLERS))
    elif kind=='timer'and role in('helper1','helper2'):
        nested=_nested(before,words,0x78f3 if role=='helper1'else 0x7939,main_cs,HELPER_CALLERS[role])
    else:assert before['nested_application_call']is None, 'no fabricated nested caller for a direct main clock site'
    result.update(kind=kind,role=role,return_ip=returned,nested_return_ip=nested,runtime_cs=runtime_cs,main_cs=main_cs,ds=before['ds'])
    return result


def model_inputs(observation):
    """Return dynamic typed clock inputs using only authenticated raw records."""
    assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}, 'exact matrix observation schema'
    assert observation['recipe']=='host-dos-clock-matrix-observer-v1'and observation['observe']is True, 'actual matrix DOS date/time hook mode'
    neutral.verify_module(observation['module'])
    assert observation['exit_code']==0 and type(observation['exit_code'])is int and observation['errors']==[] and observation['dropped']==0 and type(observation['dropped'])is int, 'complete zero-exit matrix observation without dropped/error events'
    assert 1<=len(observation['events'])<=16384, 'bounded complete dynamic clock inventory'
    timers={role:[]for role in TIMER_CALLERS.values()};dates={role:[]for role in DATE_CALLERS.values()};texts={role:[]for role in TIME_CALLERS.values()}
    calendar={role:[]for role in CALENDAR_CALLERS.values()};entries=[];unqualified=[];segments=set();cycles=set()
    for ordinal,event in enumerate(observation['events'],1):
        pair=event_pair(event,ordinal);cycles.add(pair['before']['cycle_max'])
        if pair['kind']=='unqualified':unqualified.append(pair);continue
        segments.add((pair['runtime_cs'],pair['main_cs'],pair['ds']))
        row={k:pair[k]for k in('ordinal','function','kind','role','return_ip','nested_return_ip','runtime_cs','main_cs','ds')}
        row.update(cx=pair['after']['cx'],dx=pair['after']['dx'],port=None)
        if pair['kind']=='timer':
            row.update(seconds=pair['seconds'],minutes=pair['minutes'])
            if pair['role']=='port':row['port']=_port(pair['before']['port_raw'])
            timers[pair['role']].append(row)
        elif pair['kind']=='date':
            row.update(date=pair['date'],date_text=pair['date'].strftime('%m-%d-%Y'))
            if pair['role']=='calendar':
                nested_role=CALENDAR_CALLERS[pair['nested_return_ip']];row['calendar_role']=nested_role
                if nested_role=='port':row['port']=_port(pair['before']['port_raw'])
                calendar[nested_role].append(row)
            dates[pair['role']].append(row)
        else:row['text']=native_time_text(row['cx'],row['dx']);texts[pair['role']].append(row)
        entries.append(row)
    assert len(segments)==1 and len(cycles)==1, 'stable guest load identities and declared CPU profile throughout capture'
    assert [r['function']for r in unqualified].count(0x2a)==[r['function']for r in unqualified].count(0x2c)==2, 'exact four excluded external DOS shell clock reads'
    assert [r['port']for r in timers['port']]==list(range(1,1001)), 'all1000 original port TIMER inputs occur in order'
    assert [r['port']for r in calendar['port']]==list(range(1,1001)), 'all1000 original per-port DATE inputs occur in order'
    assert len(timers['startup'])==len(timers['xannoron'])==1, 'unique startup and missing-Xannoron timer inputs'
    assert 1<=len(timers['helper1'])<=1000 and len(timers['helper2'])<=1000, 'bounded dynamic reseeding helper inventory'
    for role in('startup','final','wanderer','xannoron','base'):assert len(calendar[role])==1, 'unique observed calendar phase: '+role
    for role in('news','score'):assert len(dates[role])==len(texts[role])==1, 'unique observed text-clock context: '+role
    for date,timer in zip(calendar['port'],timers['port']):assert date['ordinal']<timer['ordinal'], 'port day is sampled before its own numeric TIMER'
    assert len(dates['cloak_notice'])==len(texts['cloak_notice']), 'paired optional cloak-notice text-clock contexts'
    runtime_cs,main_cs,ds=next(iter(segments))
    return dict(port_seconds=[r['seconds']for r in timers['port']],port_minutes=[r['minutes']for r in timers['port']],
                helper1=[r['seconds']for r in timers['helper1']],helper2=[r['seconds']for r in timers['helper2']],
                startup=timers['startup'][0]['seconds'],xannoron=timers['xannoron'][0]['seconds'],planet_timers=timers['planet'],
                port_dates=[r['date']for r in calendar['port']],startup_date=calendar['startup'][0]['date'],final_date=calendar['final'][0]['date'],
                wanderer_date=calendar['wanderer'][0]['date'],xannoron_date=calendar['xannoron'][0]['date'],base_date=calendar['base'][0]['date'],
                news_date=dates['news'][0]['date'],news_clock=texts['news'][0]['text'],score_date=dates['score'][0]['date'],score_clock=texts['score'][0]['text'],
                calendar_entries=dates['calendar'],planet_dates=calendar['planet'],cloak_notice_dates=dates['cloak_notice'],cloak_notice_times=texts['cloak_notice'],
                entries=entries,timer_entries=timers,date_entries=dates,time_entries=texts,qualified=len(entries),unclassified=[r['ordinal']for r in unqualified],
                runtime_cs=runtime_cs,main_cs=main_cs,ds=ds,cycles=next(iter(cycles)))

PROFILES={
 'shift-two':('11/02/2026','00:00:02',200000),'noon':('11/02/2026','12:00:00',200000),
 'late':('11/02/2026','23:59:59',200000),'near-midnight-100k':('11/02/2026','23:59:59',100000),
 'rollover':('11/02/2026','23:59:59',10000),'next-day':('11/03/2026','00:00:00',200000),
 'eleven-days':('11/13/2026','00:00:00',200000),'next-year':('01/01/2027','00:00:00',200000)}
MODES={'unobserved-a':'unobserved','unobserved-b':'unobserved','attach-only':'attach-only',
       'observed-a':'observed','observed-b':'observed','observed-c':'observed'}
SCRIPTS=('scripts/observe_maintenance_clock_matrix.js','scripts/recover_maintenance_clock_matrix.py','scripts/capture_maintenance_clock_neutral.mjs')
NATIVE=ROOT/'research/yt-maint/clock-matrix-native'


def verify_launch(folder,meta):
    date,clock,cycles=PROFILES[meta['profile']]
    assert (meta['date'],meta['clock'],meta['cycles'])==(date,clock,cycles), 'independent launch profile metadata'
    argv=json.loads((folder/'launch.json').read_text())
    assert argv==meta['argv']and Path(argv[0]).name=='dosbox-staging', 'actual executable launch'
    mount=argv[8];assert mount.startswith('mount c '), 'disposable mount'
    mounted=Path(mount[8:]);assert mounted.is_absolute()and mounted.parts[-2:]==(meta['profile'],meta['name']), 'actual profile/mode mount'
    commands=neutral.launch_commands();commands[0]='date '+date;commands[1]='time '+clock
    expected=['--noprimaryconf','--nolocalconf','--set','cpu_cycles='+str(cycles),'--set','nosound=true']
    expected += [v for command in [mount,'c:']+commands+['exit']for v in('-c',command)]
    assert argv[1:]==expected, 'complete independently fixed CPU/date/clock recipe'
    assert(folder/'COMMANDS.TXT').read_text()=='\n'.join(commands)+'\n', 'actual DOS command inventory'
    messages=[l.split(' | ',1)[1]for l in(folder/'dosbox.stderr').read_text().splitlines()if' | 'in l]
    launches=[m[11:]for m in messages if m.startswith('arguments: ')]
    assert len(launches)==1 and shlex.split(launches[0])==argv, 'actual host argument witness'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1, 'actual fixed host version'
    cpu=[m for m in messages if m.startswith('CPU:')]
    assert (cpu==[] if cycles==10000 else len(cpu)==1 and cpu[0].startswith('CPU: Setting fixed '+str(cycles)+' cycles.')), 'actual fixed CPU witness (default10000 emits no change notice)'
    assert [m for m in messages if m.startswith('SDL:')and'video initialised'in m]==['SDL: dummy video initialised'], 'actual dummy video'
    assert [m for m in messages if m.startswith('MIXER: Sound output')]==["MIXER: Sound output disabled ('nosound' mode)"], 'actual disabled audio'
    assert(folder/'dosbox.stdout').read_bytes()==b'', 'complete empty stdout'
    return mounted


def verify_case(folder,pin,observer):
    from verify_rng_clock import read_date,read_time
    folder=Path(folder);raw=(folder/'capture.json').read_bytes();meta=json.loads(raw)
    assert set(meta)=={'recipe','profile','date','clock','cycles','name','mode','argv','host','guest_before','guest_after','inputs','after','elapsed_seconds','controller','environment','source_input','files'}, 'exact matrix metadata schema'
    profile=folder.parent.name;name=folder.name
    assert profile in PROFILES and name in MODES and meta['profile']==profile and meta['name']==name and meta['mode']==MODES[name], 'independent fixed48-case matrix identity'
    assert(meta['date'],meta['clock'],meta['cycles'])==PROFILES[profile]and meta['recipe']=='maintenance-clock-matrix-v1', 'a priori profile declaration'
    assert meta['host']==dict(path=neutral.HOST_PATH,sha256=neutral.HOST_SHA,size=22872608,version=neutral.HOST_VERSION,architecture='arm64',uuid=neutral.HOST_UUID,source_commit=neutral.HOST_SOURCE_COMMIT), 'immutable native host identity'
    assert meta['guest_before']==meta['guest_after']==GUESTS, 'unchanged original guests'
    assert meta['inputs']=={n:SHA(b)for n,b in neutral.before_input_bytes().items()}and meta['source_input']=='research/yt-maint/initial-controls/baseline-split', 'original before-only input identity'
    assert meta['environment']==dict(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')and 0<meta['elapsed_seconds']<40, 'bounded declared environment'
    files=neutral.COMMON|{'after-'+n+'.gz'for n in neutral.OUTPUTS}
    if meta['mode']!='unobserved':files|={'loaded-observer.js','host-time.json.gz'}
    assert set(meta['files'])==files and {p.name for p in folder.iterdir()}==files|{'capture.json'}, 'complete artifact inventory'
    assert set(pin)=={'capture_sha256','raw'}and set(pin['raw'])==files and SHA(raw)==pin['capture_sha256'], 'immutable capture provenance'
    for n in files:
        data=(folder/n).read_bytes()
        assert SHA(data)==meta['files'][n], 'declared artifact hash: '+n
        assert SHA(gzip.decompress(data)if n.endswith('.gz')else data)==pin['raw'][n], 'immutable raw artifact: '+n
    mounted=verify_launch(folder,meta)
    assert(folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n', 'natural successful DOS completion'
    trace=(folder/'TRACE.BIN').read_bytes()
    assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n')and trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'), 'untouched maintenance completion'
    startdate,enddate=[read_date((folder/n).read_bytes())for n in('DOSDATE.LOG','ENDDATE.LOG')]
    start,end=[read_time((folder/n).read_bytes())for n in('DOSTIME.LOG','ENDTIME.LOG')]
    assert startdate==datetime.datetime.strptime(meta['date'],'%m/%d/%Y').date(), 'actual initial shell date'
    elapsed=(enddate-startdate).days*86400+end-start
    assert 0<elapsed<40, 'actual advancing bounded clock including rollover'
    controller=json.loads((folder/'controller.json').read_text());assert controller==meta['controller'], 'actual process lifecycle metadata'
    inputs=None
    if meta['mode']=='unobserved':neutral.verify_controller(controller,meta['mode'])
    else:
        obraw=gzip.decompress((folder/'host-time.json.gz').read_bytes());ob=json.loads(obraw)
        config=dict(observe=meta['mode']=='observed',output=str(mounted/'host-time.json'))
        assert(folder/'loaded-observer.js').read_text()=='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer, 'exact audited observer source/config'
        if config['observe']:
            inputs=model_inputs(ob);assert inputs['cycles']==meta['cycles'], 'observed CPU matches a priori profile'
        else:
            assert set(ob)=={'recipe','observe','module','exit_code','events','errors','dropped'}and ob['recipe']=='host-dos-clock-matrix-observer-v1'and ob['observe']is False and ob['exit_code']==0 and ob['events']==ob['errors']==[]and ob['dropped']==0, 'attach-only no-hook control'
            neutral.verify_module(ob['module'])
        neutral.verify_controller(controller,meta['mode'],ob,obraw)
    outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in neutral.OUTPUTS}
    assert meta['after']=={n:SHA(b)for n,b in outputs.items()}and len(outputs['YTDATA.DAT'])==4151*137, 'complete six-file output identity'
    if inputs is not None:neutral.verify_port_timestamps(outputs['YTDATA.DAT'],inputs)
    return dict(metadata=meta,outputs=outputs,inputs=inputs)


def verify_equivalence(cases):
    assert set(cases)=={p+'/'+n for p in PROFILES for n in MODES}, 'all48controls including unsupported model profiles'
    for profile in PROFILES:
        reference=cases[profile+'/unobserved-a']['outputs']
        for mode in MODES:assert cases[profile+'/'+mode]['outputs']==reference, (profile,mode,'all six complete outputs equal both fresh paired unobserved controls')
        observations=[cases[profile+'/'+n]['inputs']for n in('observed-a','observed-b','observed-c')]
        for key in('port_seconds','port_minutes','port_dates','helper1','helper2','startup','xannoron','news_date','news_clock','score_date','score_clock'):
            assert observations[0][key]==observations[1][key]==observations[2][key], (profile,'repeated source-qualified inputs',key)


def verify_native(pins):
    from verify_rng_native import image
    assert {p.name for p in NATIVE.iterdir()}==set(pins), 'complete independent native packet inventory'
    for n,digest in pins.items():assert SHA((NATIVE/n).read_bytes())==digest, 'immutable native evidence '+n
    records=json.loads((NATIVE/'rea.json').read_text())['records']
    assert len(records)==2, 'two fresh complete static original reads'
    for record,(name,address,length)in zip(records,[('BRUN30.EXE',0x1c06b,196),('YTMAINT.EXE',0x179e3,805)]):
        assert record['subject']['name']==name and record['subject']['digest']['sha256']==GUESTS[name]and record['parameters']==dict(address=hex(address),length=length), 'original native subject/range'
        result=record['normalized_result'];data=bytes.fromhex(result['bytes_hex'])
        assert result['complete']is True and result['requested_bytes']==result['returned_bytes']==len(data)==length and data==image((ROOT/'archive/dos-original'/name).read_bytes())[address-0x10000:address-0x10000+length], 'complete static bytes independently reconstructed from original MZ'
    main=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()[512:]
    for callers,signature in[(TIMER_CALLERS,'cd3d439090'),(DATE_CALLERS,'cd3d239090'),(TIME_CALLERS,'cd3d249090')]:
        expected={ret-5 for ret in callers};raw=bytes.fromhex(signature)
        assert {m.start()for m in re.finditer(re.escape(raw),main)}==expected, 'complete original dispatch-site inventory'
    source=json.loads((NATIVE/'bios-source.json').read_text())
    assert source['commit']==neutral.HOST_SOURCE_COMMIT and source['sha256']=='e85868def4b5c0367a2a27f4a131f64c989479c3a3e3a645944135a1cb3e9cd4'and SHA((NATIVE/source['path']).read_bytes())==source['sha256'], 'primary BIOS scheduling source'


def verify(directory=DEFAULT,pins_path=PINS_FILE):
    raw=Path(pins_path).read_bytes();assert SHA(raw)==PINS_SHA, 'immutable clock-matrix manifest'
    pins=json.loads(raw);assert set(pins)=={'cases','native','scripts'}, 'complete independent matrix manifest schema'
    assert set(pins['scripts'])==set(SCRIPTS), 'exact acquisition source inventory'
    for n,digest in pins['scripts'].items():
        # Both retained corpora were acquired with the original controller.
        # The live controller was later hardened; preserve the measured source
        # identity rather than assigning its new bytes to old observations.
        actual=('research/yt-maint/clock-neutral-acquisition/capture_maintenance_clock_neutral.mjs'
                if n=='scripts/capture_maintenance_clock_neutral.mjs' else n)
        assert SHA((ROOT/actual).read_bytes())==digest, 'immutable acquisition script '+n
    old=json.loads(neutral.PINS_FILE.read_text());assert SHA(neutral.PINS_FILE.read_bytes())==neutral.PINS_SHA, 'unchanged prior native/host identity manifest'
    neutral.verify_host_packet(neutral.HOST_DIR,old['host']);neutral.verify_guest_contracts(old['zero_trace_sha256'])
    verify_native(pins['native']);directory=Path(directory)
    assert {p.name for p in directory.iterdir()}==set(PROFILES), 'complete fixed profile inventory'
    for profile in PROFILES:assert {p.name for p in(directory/profile).iterdir()}==set(MODES), 'complete fixed mode inventory'
    assert set(pins['cases'])=={p+'/'+n for p in PROFILES for n in MODES}, 'complete48casepins'
    observer=(ROOT/SCRIPTS[0]).read_text()
    cases={key:verify_case(directory/key,pins['cases'][key],observer)for key in sorted(pins['cases'])}
    verify_equivalence(cases)
    return dict(runs=48,profiles=8,observed=24,paired_files=288,source_qualified=sum(r['inputs']['qualified']for r in cases.values()if r['inputs']),byte_mismatches=0)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',nargs='?',type=Path,default=DEFAULT)
    args=parser.parse_args();print('Clock matrix evidence verified:',verify(args.directory))
