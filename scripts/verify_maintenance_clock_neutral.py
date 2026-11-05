"""Verify host-observed DOS time inputs and clock-neutral maintenance outputs.

Portable verification never launches DOSBox or Frida and never substitutes
expected after-file timestamps for observed DOS registers. The selected clock
converter uses independent exact-rational single rounding; zero residue is
selected only for an actual zero DOS centisecond input.
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

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/clock-neutral-controls'
PINS_FILE=ROOT/'research/yt-maint/clock-neutral-pins.json'
PINS_SHA='f89824872153c78042b5311644740049d8b519b1cacfdd2c486079f8bf78d553'
SHA=lambda b:hashlib.sha256(b).hexdigest()
HOST_SHA='781d61c874271a315d672c597697cf0fb3aa0f6a727934bce4d2a9ad34057de5'
HOST_UUID='31CDF62F-E9EE-39ED-A05A-10E4072BD15E'
HOST_VERSION='0.83.0'
HOST_SOURCE_COMMIT='7b40053b7ac580843d0461eba8c36a47a990e66c'
GUESTS={'YTMAINT.EXE':'8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
        'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'}
ZERO=bytes.fromhex('00004800')


def _pow2(exponent):
    return Fraction(1<<exponent)if exponent>=0 else Fraction(1,1<<-exponent)


def _single_positive(value):
    """Round a positive rational once to the 24-bit normalized MBF significand."""
    assert isinstance(value,Fraction) and value>0, 'positive rational single input'
    exponent=value.numerator.bit_length()-value.denominator.bit_length()
    if value<_pow2(exponent):exponent-=1
    scaled=value*_pow2(23-exponent)
    whole,remainder=divmod(scaled.numerator,scaled.denominator)
    twice=2*remainder
    if twice>scaled.denominator or(twice==scaled.denominator and whole&1):whole+=1
    if whole==1<<24:
        whole>>=1;exponent+=1
    assert 1<<23<=whole<1<<24 and 1<=exponent+129<=255, 'bounded normalized MBF single'
    raw=(whole-(1<<23)).to_bytes(3,'little')+bytes([exponent+129])
    exact=Fraction(whole,1<<23)*_pow2(exponent)
    return raw,exact


def mbf_fraction(raw):
    assert isinstance(raw,bytes)and len(raw)==4, 'four raw MBF bytes'
    if raw[3]==0:return Fraction(0)
    mantissa=int.from_bytes(raw[:3],'little')
    sign=-1 if mantissa&0x800000 else 1
    return sign*Fraction((1<<23)+(mantissa&0x7fffff),1<<23)*_pow2(raw[3]-129)


def clock_to_raw(cx,dx):
    """DOS CH:CL:DH:DL -> original TIMER seconds and port minutes FAC bytes."""
    assert type(cx)is int and type(dx)is int and 0<=cx<=65535 and 0<=dx<=65535, 'DOS time register widths'
    hour,minute,second,hundredth=cx>>8,cx&255,dx>>8,dx&255
    assert hour<24 and minute<60 and second<60 and hundredth<100, 'valid returned DOS time fields'
    centiseconds=((hour*60+minute)*60+second)*100+hundredth
    assert 0<=centiseconds<1<<24, 'exact integer centisecond arithmetic'
    if centiseconds==0:return ZERO,ZERO
    seconds,exact=_single_positive(Fraction(centiseconds,100))
    minutes,_=_single_positive(exact/60)
    assert seconds[3]and minutes[3], 'positive DOS time cannot be mapped to zero'
    return seconds,minutes


def event_pair(event,ordinal,*,cycle_refills=None):
    """Authenticate one complete native entry/leave pair before reading clocks."""
    assert event['ordinal']==ordinal and type(event['ordinal'])is int, 'contiguous paired event ordinal'
    assert set(event)=={'ordinal','before','after'}, 'exact paired event schema'
    before,after=event['before'],event['after']
    registers=('ax','cx','dx','ds','ss','cs','sp','ip')
    fields=set(registers)|{'pic','cycles','runtime_signature','application_call','ds_phys','ss_phys','stack','port_raw'}
    for row in (before,after):
        assert set(row)==fields, 'exact guest snapshot schema'
        assert type(row['ds_phys'])is int and type(row['ss_phys'])is int and row['ds_phys']==16*row['ds'] and row['ss_phys']==16*row['ss'], 'real-mode segment cache matches observed segment values'
        for field in registers:assert type(row[field])is int and 0<=row[field]<=65535, 'guest register width'
        assert type(row['pic'])is int and row['pic']>=0, 'observed PIC ticks'
        assert type(row['cycles'])is int, 'observed CPU cycles'
        assert isinstance(row['stack'],str)and re.fullmatch('[0-9a-f]{80}',row['stack']), 'bounded raw interrupt stack'
        assert isinstance(row['port_raw'],str)and re.fullmatch('[0-9a-f]{8}',row['port_raw']), 'four-byte raw port index'
    assert before['ax']>>8==0x2c and after['ax']==0x2c00, 'actual DOS GetSystemTime entry/return'
    for field in ('ds','ss','cs','sp','stack','port_raw','pic','ds_phys','ss_phys','runtime_signature','application_call'):
        assert before[field]==after[field], 'paired unchanged guest context: '+field
    assert before['cs']==0xf000 and before['ip']==0x13e5 and after['ip']==0x13e7, 'selected DOS callback return boundary'
    if cycle_refills is not None and ordinal in cycle_refills:
        assert before['cycles']==0 and after['cycles']==cycle_refills[ordinal], 'pinned zero-budget recursive CPU refill'
    else:
        assert after['cycles']==before['cycles']-5, 'original DOS time overhead is preserved'
    seconds,minutes=clock_to_raw(after['cx'],after['dx'])
    words=struct.unpack('<20H',bytes.fromhex(before['stack']))
    if words[0]==0xc137:
        assert before['runtime_signature']=='50535152b42ccd21', 'original BRUN TIMER instruction signature'
        assert before['application_call']==(b'\x9a'+struct.pack('<HH',0xc12f,words[1])).hex(), 'original runtime far-call fixup matches observed segment'
    else:
        assert before['runtime_signature'] is None and before['application_call'] is None, 'unqualified DOS calls have no forged guest attribution'
    return dict(seconds=seconds,minutes=minutes,words=words,before=before,after=after)


def port_events(observation,*,helper_counts=(41,19),cycle_refills=None):
    """Recover only direct original maintenance-port TIMER returns, in order."""
    assert observation['errors']==[] and type(observation['dropped'])is int and observation['dropped']==0, 'complete error-free host observation'
    assert len(observation['events'])==1006+sum(helper_counts), 'complete bounded DOS time-call inventory'
    ports=[];runtime_segments=set();main_segments=set();data_segments=set()
    for ordinal,event in enumerate(observation['events'],1):
        pair=event_pair(event,ordinal,cycle_refills=cycle_refills);words=pair['words']
        if words[0]!=0xc137 or words[7]!=0x0927:continue
        assert words[1]>0 and words[8]>0 and words[1]!=words[8], 'distinct observed runtime/main code segments'
        runtime_segments.add(words[1]);main_segments.add(words[8]);data_segments.add(pair['before']['ds'])
        raw=bytes.fromhex(pair['before']['port_raw']);value=mbf_fraction(raw)
        assert value.denominator==1 and 1<=value<=1000, 'integer port identity in observed DS7ad6'
        port=int(value)
        assert port==len(ports)+1, 'all1000 port calls occur once in original order'
        ports.append(dict(port=port,ordinal=ordinal,seconds=pair['seconds'],minutes=pair['minutes'],
                          cx=pair['after']['cx'],dx=pair['after']['dx'],runtime_cs=words[1],main_cs=words[8],ds=pair['before']['ds']))
    assert len(ports)==1000 and len(runtime_segments)==len(main_segments)==len(data_segments)==1, 'complete stable port attribution'
    return ports


def model_inputs(observation,*,helper_counts=(41,19),cycle_refills=None):
    """Derive every qualified model clock input from one paired DOS return log.

    No world, expected timestamp table, after-file digest or prior terminating
    guest probe is read by this function. Unknown BRUN TIMER callers fail closed.
    """
    assert helper_counts in ((41,19),(42,19)), 'measured helper inventory profiles only'
    refills=cycle_refills or {}
    assert isinstance(refills,dict) and all(type(k)is int and type(v)is int and 0<v<200000 for k,v in refills.items()), 'explicit bounded refill witnesses'
    actual_refills={e['ordinal'] for e in observation['events']
                    if e['after']['cycles']!=e['before']['cycles']-5}
    assert actual_refills==set(refills), 'original DOS time overhead is preserved: exact declared refill inventory'
    ports=port_events(observation,helper_counts=helper_counts,cycle_refills=cycle_refills)
    entries={'startup':[],'helper1':[],'helper2':[],'xannoron':[],'port':[]}
    caller={0x007d:'startup',0x78fd:'helper1',0x7943:'helper2',0x218b:'xannoron',0x0927:'port'}
    runtime=set();main=set();data=set();unclassified=[]
    for ordinal,event in enumerate(observation['events'],1):
        pair=event_pair(event,ordinal,cycle_refills=cycle_refills);words=pair['words']
        if words[0]!=0xc137:
            unclassified.append(ordinal);continue
        assert words[7]in caller, 'all BRUN TIMER callers have explicit source attribution'
        label=caller[words[7]]
        assert words[1]>0 and words[8]>0 and words[1]!=words[8], 'qualified runtime/application segment identity'
        runtime.add(words[1]);main.add(words[8]);data.add(pair['before']['ds'])
        entries[label].append(dict(ordinal=ordinal,seconds=pair['seconds'],minutes=pair['minutes'],
                                   cx=pair['after']['cx'],dx=pair['after']['dx'],return_ip=words[7],
                                   runtime_cs=words[1],main_cs=words[8],ds=pair['before']['ds']))
    assert {k:len(v)for k,v in entries.items()}=={'startup':1,'helper1':helper_counts[0],'helper2':helper_counts[1],'xannoron':1,'port':1000}, 'complete source-qualified clock input inventory'
    assert len(unclassified)==4 and len(runtime)==len(main)==len(data)==1, '1062 stable qualified clocks and four excluded DOS calls'
    # The port extractor additionally authenticates each raw DS index1..1000.
    assert [r['ordinal']for r in ports]==[r['ordinal']for r in entries['port']], 'port identities agree with caller-qualified clocks'
    return dict(port_seconds=[r['seconds']for r in entries['port']],port_minutes=[r['minutes']for r in entries['port']],
                helper1=[r['seconds']for r in entries['helper1']],helper2=[r['seconds']for r in entries['helper2']],
                startup=entries['startup'][0]['seconds'],xannoron=entries['xannoron'][0]['seconds'],
                qualified=sum(len(v)for v in entries.values()),unclassified=unclassified,entries=entries,
                runtime_cs=next(iter(runtime)),main_cs=next(iter(main)),ds=next(iter(data)))


HOST_DIR=ROOT/'research/yt-maint/clock-neutral-host'
OBSERVER=ROOT/'scripts/observe_maintenance_clock.js'
CAPTURE_SCRIPTS=('scripts/observe_maintenance_clock.js','scripts/capture_maintenance_clock_neutral.mjs','scripts/recover_maintenance_clock_neutral.py')
CASES={'unobserved-a':'unobserved','unobserved-b':'unobserved','attach-only':'attach-only',
       'observed-a':'observed','observed-b':'observed','observed-c':'observed'}
OUTPUTS={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}
COMMON={'COMMANDS.TXT','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG','TRACE.BIN',
        'controller.json','dosbox.stderr','dosbox.stdout','launch.json'}
PROLOGUE='fc6fbaa9fa6701a9f85f02a9f65703a9f44f04a9fd7b05a9fd430191ffc314d1'
HOST_PATH='/opt/homebrew/Cellar/dosbox-staging/0.83.0/bin/dosbox'


def verify_module(module):
    assert set(module)=={'name','path','base','size','arch','platform','uuid','prologue'}, 'observed host module schema'
    assert (module['name'],module['path'],module['size'],module['arch'],module['platform'],module['uuid'],module['prologue'])==(
        'dosbox',HOST_PATH,4505600,'arm64','darwin',HOST_UUID,PROLOGUE), 'observed pinned native host identity'
    assert isinstance(module['base'],str)and re.fullmatch(r'0x[0-9a-f]+',module['base']), 'observed native image base encoding'
    address=int(module['base'],16)
    assert 1<<32<=address<1<<48 and address%4096==0, 'observed native image base bounds'


def verify_observation(observation,observe=True,*,helper_counts=(41,19),cycle_refills=None):
    assert set(observation)=={'recipe','observe','module','exit_code','events','errors','dropped'}, 'exact host observation schema'
    assert observation['recipe']=='host-dos-time-observer-v1' and observation['observe'] is observe, 'declared DOS hook mode'
    assert type(observation['exit_code'])is int and observation['exit_code']==0, 'natural observed process exit code'
    assert observation['errors']==[] and type(observation['dropped'])is int and observation['dropped']==0, 'complete observed flush without errors/drop'
    verify_module(observation['module'])
    if not observe:
        assert observation['events']==[], 'attach-only control has no DOS hook events'
        return None
    return model_inputs(observation,helper_counts=helper_counts,cycle_refills=cycle_refills)


def verify_host_packet(directory,pins):
    directory=Path(directory)
    assert {p.name for p in directory.iterdir()}==set(pins), 'complete retained host evidence inventory'
    for name,digest in pins.items():assert SHA((directory/name).read_bytes())==digest, 'immutable host evidence: '+name
    package=json.loads((directory/'packet-sha256.json').read_text())
    for name,digest in package.items():assert SHA((directory/name).read_bytes())==digest, 'independent host source packet hash'
    installed=json.loads((directory/'installed-host.json').read_text())
    assert installed['target_path']==HOST_PATH and installed['sha256']==HOST_SHA and installed['size']==22872608 and installed['architecture']=='arm64', 'installed native host file identity'
    symbols=installed['symbols']
    for name,address in {'DOS_21Handler':'0x1000db990','cpu_regs':'0x101396d60','Segs':'0x101396e78','MemBase':'0x1023abb90'}.items():
        assert symbols[name]==address, 'original host observer symbol binding'
    entry=installed['selected_native_bytes']['entry']
    assert entry['address']=='0x1000db990' and entry['length']==64 and entry['bytes_hex'].startswith(PROLOGUE), 'original host prologue before attachment'
    assert SHA(bytes.fromhex(entry['bytes_hex']))==entry['sha256'], 'native entry byte digest'
    source=json.loads((directory/'sources.json').read_text())
    assert source['commit']==HOST_SOURCE_COMMIT, 'exact original host source commit'
    ref=json.loads((directory/'tag-ref.json').read_text())
    assert ref['ref']=='refs/tags/v0.83.0' and ref['object']=={'sha':HOST_SOURCE_COMMIT,'type':'commit','url':'https://api.github.com/repos/dosbox-staging/dosbox-staging/git/commits/'+HOST_SOURCE_COMMIT}, 'official host release tag commit'
    seen=set()
    for row in source['files']:
        path=row['path'];assert path not in seen and path.startswith('src/'), 'unique host source path'
        raw=(directory/path.replace('/','--')).read_bytes()
        assert SHA(raw)==row['sha256'] and len(raw)==row['bytes'], 'retained primary host source bytes'
        assert row['url']=='https://raw.githubusercontent.com/dosbox-staging/dosbox-staging/v0.83.0/'+path, 'declared primary source URL'
        seen.add(path)
    assert len(seen)==14 and {p.name for p in directory.glob('src--*')}=={p.replace('/','--')for p in seen}, 'complete selected primary-source inventory'


def verify_guest_contracts(zero_trace_sha,host_dir=HOST_DIR):
    from verify_rng_native import image
    from verify_rng_trace import verify_trace
    for name,digest in GUESTS.items():assert SHA((ROOT/'archive/dos-original'/name).read_bytes())==digest, 'immutable original guest identity'
    main=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    for return_ip in (0x007d,0x0927,0x218b,0x78fd,0x7943):
        assert main[512+return_ip-5:512+return_ip]==bytes.fromhex('cd3d439090'), 'original source-qualified TIMER dispatch'
    runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    code=Path(host_dir,'brun-TIMER.bin').read_bytes()
    assert len(code)==133 and code==image(runtime)[0xc12f:0xc12f+133] and code[:8].hex()=='50535152b42ccd21', 'original BRUN TIMER handler bytes'
    trace=(ROOT/'research/yt-rng-seeding/trace-dos/timer-midnight/TRACE.BIN').read_bytes()
    assert SHA(trace)==zero_trace_sha, 'independent historical zero TIMER contract pin'
    result=verify_trace(trace,'timer',5,None)
    assert result['timer_or_input_fac']==ZERO.hex(), 'original zero residue comes from native TIMER evidence'


def launch_commands():
    return ['date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','ytmaint > TRACE.BIN',
            'if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG',
            'echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']


def verify_launch(folder,meta):
    argv=json.loads((folder/'launch.json').read_text())
    assert argv==meta['argv'] and isinstance(argv,list)and Path(argv[0]).name=='dosbox-staging', 'recorded executable launch'
    assert len(argv)>9 and argv[8].startswith('mount c '), 'isolated disposable DOS mount'
    mount=argv[8];mounted=Path(mount[len('mount c '):])
    assert mounted.is_absolute()and mounted.name.endswith(meta['name']), 'actual mounted case identity'
    commands=launch_commands()
    expected=['--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']
    expected += [v for command in [mount,'c:']+commands+['exit']for v in ('-c',command)]
    assert argv[1:]==expected, 'complete untuned DOS launch recipe'
    assert (folder/'COMMANDS.TXT').read_text()=='\n'.join(commands)+'\n', 'explicit DOS command recipe'
    messages=[line.split(' | ',1)[1]for line in(folder/'dosbox.stderr').read_text().splitlines()if' | 'in line]
    launches=[m[len('arguments: '):]for m in messages if m.startswith('arguments: ')]
    assert len(launches)==1 and shlex.split(launches[0])==argv, 'actual process launch agrees with manifest'
    assert messages.count('dosbox-staging version 0.83.0 ()')==1, 'actual emulator version'
    cpu=[m for m in messages if m.startswith('CPU:')]
    video=[m for m in messages if m.startswith('SDL:')and'video initialised'in m]
    sound=[m for m in messages if m.startswith('MIXER: Sound output')]
    assert len(cpu)==1 and cpu[0].startswith('CPU: Setting fixed 200000 cycles.'), 'actual fixed CPU cycles'
    assert video==['SDL: dummy video initialised'] and sound==["MIXER: Sound output disabled ('nosound' mode)"], 'actual dummy video and disabled audio'
    assert (folder/'dosbox.stdout').read_bytes()==b'', 'captured host stdout is complete and empty'
    return mounted


def before_input_bytes():
    from verify_initial_maintenance import PINS as OLD_PINS
    root=ROOT/'research/yt-maint/initial-controls/baseline-split'
    result={}
    for name in ('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'):
        raw=gzip.decompress((root/('before-'+name+'.gz')).read_bytes())
        assert SHA(raw)==OLD_PINS['baseline-split']['before-'+name+'.gz'], 'independent raw before-input identity'
        result[name]=raw
    return result


def verify_controller(controller,mode,observation=None,observation_bytes=None):
    assert controller['mode']==mode and controller['success'] is True and controller['forced'] is False and controller['process_exited'] is True, 'natural successful owned-process cleanup'
    assert type(controller['pid'])is int and controller['pid']>0 and type(controller['exit_code'])is int and controller['exit_code']==0, 'owned process PID and natural zero exit'
    if mode=='unobserved':
        assert set(controller)=={'mode','success','exit_code','forced','process_exited','pid'}, 'unobserved process controller schema'
        return
    assert controller['ready'] is True and controller['detached_reason']=='process-terminated', 'observer ready before natural termination'
    assert re.fullmatch(r'v\d+\.\d+\.\d+',controller['node_version']), 'actual Node controller version'
    start=datetime.datetime.fromisoformat(controller['started'].replace('Z','+00:00'))
    end=datetime.datetime.fromisoformat(controller['finished'].replace('Z','+00:00'))
    assert datetime.timedelta(0)<end-start<datetime.timedelta(seconds=40), 'bounded owned process observation lifecycle'
    messages=controller['messages']
    assert len(messages)==2 and all(set(m)=={'type','payload'}and m['type']=='send'for m in messages), 'complete ready/flush observer messages without errors'
    ready,flushed=[m['payload']for m in messages]
    assert ready=={'kind':'ready','module':observation['module'],'observe':mode=='observed'}, 'same observed module and hook mode at readiness'
    assert flushed=={'kind':'flushed','exit_code':0,'bytes':len(observation_bytes),'expected_bytes':len(observation_bytes),
                      'events':len(observation['events']),'errors':0,'dropped':0}, 'one complete exact-byte trace flush'
    # The controller records the operator-supplied existing Frida module identity.
    frida=controller['frida']
    assert set(frida)=={'version','module','module_sha256','package_sha256'}and frida['version']=='17.23.2', 'actual compatible Frida package version'
    assert Path(frida['module']).is_absolute()and frida['module'].endswith('/frida/build/src/frida.js'), 'actual Frida module path'
    assert frida['module_sha256']=='408959cd8daa899370884ea4c7d763916b1ea2960ef4ce8118956870a600bda9'and frida['package_sha256']=='7efb59d2050b7b6304e1617f463c4eb7b2f7cb7e3e80e677976825a76ee31e8d', 'actual Frida package/module digest'


def verify_port_timestamps(world,inputs):
    assert len(world)==4151*137 and len(inputs['port_minutes'])==1000, 'complete observed port timestamp comparison'
    for port,raw in enumerate(inputs['port_minutes'],1):
        at=(3050+port)*137+101
        assert world[at:at+4]==raw, (port,'saved port timestamp matches independently converted DOS time without any gap mask')


def verify_case(folder,pin,observer):
    from verify_rng_clock import read_date,read_time
    folder=Path(folder);raw_meta=(folder/'capture.json').read_bytes();meta=json.loads(raw_meta)
    keys={'recipe','date','clock','name','mode','argv','host','guest_before','guest_after','inputs','before','after',
          'elapsed_seconds','controller','environment','source_input','files'}
    assert set(meta)==keys and meta['recipe']=='maintenance-clock-neutral-v1', 'exact clock-neutral capture schema'
    assert meta['name']==folder.name and CASES.get(folder.name)==meta['mode'], 'fixed six-control capture matrix identity'
    assert meta['date']=='11/02/2026'and meta['clock']=='00:00:00', 'unchanged baseline DOS clock recipe'
    assert meta['host']=={'path':HOST_PATH,'sha256':HOST_SHA,'size':22872608,'version':HOST_VERSION,'architecture':'arm64','uuid':HOST_UUID,'source_commit':HOST_SOURCE_COMMIT}, 'original native host binary/version/source identity'
    assert meta['guest_before']==meta['guest_after']==GUESTS, 'original guest executables remain byte-identical'
    before=before_input_bytes();expected_inputs={n:SHA(b)for n,b in before.items()}
    assert meta['before']==meta['inputs']==expected_inputs and meta['source_input']=='research/yt-maint/initial-controls/baseline-split', 'unaltered original before inputs'
    assert meta['environment']=={'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}, 'declared capture environment'
    assert type(meta['elapsed_seconds'])in(int,float)and 0<meta['elapsed_seconds']<40, 'bounded capture elapsed time'
    files=COMMON|{'after-'+n+'.gz'for n in OUTPUTS}
    if meta['mode']!='unobserved':files|={'loaded-observer.js','host-time.json.gz'}
    assert set(meta['files'])==files and {p.name for p in folder.iterdir()}==files|{'capture.json'}, 'complete retained capture inventory'
    for name,digest in meta['files'].items():assert SHA((folder/name).read_bytes())==digest, 'declared retained artifact hash: '+name
    mounted=verify_launch(folder,meta)
    assert (folder/'ERROR.LOG').read_bytes()==b''and(folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n', 'actual normal DOS program status'
    assert(folder/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n', 'DOS shell returned normally'
    trace=(folder/'TRACE.BIN').read_bytes()
    assert trace.startswith(b'\r\nYankee Trader Maintenance program\r\n')and trace.count(b'Daily Maintenance Completed OK')==1 and trace.endswith(b'Daily Maintenance Completed OK\r\n'), 'untouched normal maintenance completion'
    date=datetime.date(2026,11,2)
    expected_date=('Current date: '+date.strftime('%a %m/%d/%Y')+'\r\n').encode()+b'Run \x1b[33;1mdate MM/DD/YYYY\x1b[0m to change the current date.\r\n'
    for name in ('DOSDATE.LOG','ENDDATE.LOG'):
        raw=(folder/name).read_bytes();assert read_date(raw)==date and raw==expected_date, 'actual unchanged DOS date witness'
    for name in ('DOSTIME.LOG','ENDTIME.LOG'):
        assert re.fullmatch(rb'Current time: \d{1,2}:\d{2}:\d{2}\.\d{2}(am|pm)\r\nRun \x1b\[33;1mtime hh:mm:ss\x1b\[0m to change the current time.\r\n',(folder/name).read_bytes()), 'complete DOS time witness'
    start,end=[read_time((folder/name).read_bytes())for name in ('DOSTIME.LOG','ENDTIME.LOG')]
    assert start==0 and start<end<30, 'actual bounded advancing baseline clock'
    controller=json.loads((folder/'controller.json').read_text())
    assert controller==meta['controller'], 'same retained actual lifecycle controller'
    inputs=None
    if meta['mode']=='unobserved':verify_controller(controller,meta['mode'])
    else:
        raw_observation=gzip.decompress((folder/'host-time.json.gz').read_bytes());observation=json.loads(raw_observation)
        config={'observe':meta['mode']=='observed','output':str(mounted/'host-time.json')}
        expected_script='const CONFIG='+json.dumps(config,separators=(',',':'))+';\n'+observer
        assert(folder/'loaded-observer.js').read_text()==expected_script, 'exact read-only guest observer template and declared output'
        inputs=verify_observation(observation,config['observe'])
        verify_controller(controller,meta['mode'],observation,raw_observation)
    outputs={name:gzip.decompress((folder/('after-'+name+'.gz')).read_bytes())for name in OUTPUTS}
    assert meta['after']=={name:SHA(raw)for name,raw in outputs.items()}, 'all six complete output hashes'
    assert len(outputs['YTDATA.DAT'])==4151*137 and sum(map(len,outputs.values()))==570059, 'complete world and auxiliary byte inventory'
    if inputs is not None:verify_port_timestamps(outputs['YTDATA.DAT'],inputs)
    assert set(pin)=={'capture_sha256','raw'}, 'independent case pin schema'
    assert SHA(raw_meta)==pin['capture_sha256'], 'immutable captured provenance'
    assert set(pin['raw'])==files, 'complete independent raw artifact pins'
    for name,digest in pin['raw'].items():
        raw=(folder/name).read_bytes();assert SHA(gzip.decompress(raw)if name.endswith('.gz')else raw)==digest, 'immutable raw capture pin: '+name
    return dict(metadata=meta,outputs=outputs,inputs=inputs)


def verify_equivalence(cases):
    from verify_initial_maintenance import PINS as OLD_PINS
    reference={}
    for name in OUTPUTS:
        raw=gzip.decompress((ROOT/'research/yt-maint/initial-controls/baseline-split'/('after-'+name+'.gz')).read_bytes())
        assert SHA(raw)==OLD_PINS['baseline-split']['after-'+name+'.gz'], 'immutable untouched historical output'
        reference[name]=raw
    import verify_maintenance_record_inputs as prior
    historical_raw=prior.PINS_FILE.read_bytes()
    assert SHA(historical_raw)==prior.PINS_SHA, 'immutable prior replay-control manifest'
    historical_pins=json.loads(historical_raw)['controls']
    original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    historical={}
    for name in ('entry/untouched','entry/untouched-repeat','port-default/untouched','port-readonly/untouched'):
        group=name.split('/',1)[0]
        row=prior.verify_control(prior.DEFAULT/name,historical_pins[name],original,group)
        assert row['kind']=='untouched', 'historical comparison is a genuinely untouched control'
        historical[name]={n:row['outputs']['after-'+n+'.gz']for n in OUTPUTS}
        assert historical[name]==reference, 'all four historical untouched six-file baselines agree'
    assert set(cases)==set(CASES), 'complete paired clock-neutral experiment matrix'
    for label,row in cases.items():
        assert row['outputs']==cases['unobserved-a']['outputs']==cases['unobserved-b']['outputs']==reference and all(row['outputs']==old for old in historical.values()), (label,'all six complete files equal fresh paired controls and historical untouched baseline')
    observed=[cases[n]['inputs']for n in ('observed-a','observed-b','observed-c')]
    for key in ('port_seconds','port_minutes','helper1','helper2','startup','xannoron'):
        assert observed[0][key]==observed[1][key]==observed[2][key], 'repeatable source-qualified model clock inputs: '+key


def verify(directory=DEFAULT,pins_path=PINS_FILE,host_directory=HOST_DIR):
    directory=Path(directory);raw=Path(pins_path).read_bytes()
    assert SHA(raw)==PINS_SHA, 'immutable clock-neutral evidence manifest'
    pins=json.loads(raw)
    assert set(pins)=={'cases','host','scripts','zero_trace_sha256'}, 'independent full evidence pin schema'
    assert {p.name for p in directory.iterdir()}==set(pins['cases'])==set(CASES), 'complete six-case corpus'
    assert set(pins['scripts'])==set(CAPTURE_SCRIPTS), 'complete declared acquisition source inventory'
    for path,digest in pins['scripts'].items():
        # Preserve the exact controller that acquired the immutable corpus.
        actual = ('research/yt-maint/clock-neutral-acquisition/capture_maintenance_clock_neutral.mjs'
                  if path == 'scripts/capture_maintenance_clock_neutral.mjs' else path)
        assert SHA((ROOT/actual).read_bytes())==digest, 'immutable audited acquisition source: '+path
    verify_host_packet(host_directory,pins['host'])
    verify_guest_contracts(pins['zero_trace_sha256'],host_directory)
    observer=OBSERVER.read_text()
    cases={name:verify_case(directory/name,pins['cases'][name],observer)for name in sorted(CASES)}
    verify_equivalence(cases)
    return {'runs':6,'unobserved':2,'attach_only':1,'observed':3,'events_per_observed_run':1066,
            'qualified_inputs_per_observed_run':1062,'port_timers_per_observed_run':1000,
            'compared_files_per_run':6,'compared_bytes_per_run':570059,'historical_controls':4,'byte_mismatches':0}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',nargs='?',type=Path,default=DEFAULT)
    args=p.parse_args();print('Clock-neutral maintenance evidence verified:',verify(args.directory))
