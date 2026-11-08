"""Independent native RND(argument) identity, probe, dispatch and value audit."""
import hashlib,json,shlex,struct
from pathlib import Path
from verify_rng_trace import INIT_SHA,RUNTIME_SHA,decode_single
from verify_rng_clock import read_date,read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-rng-seeding/argument-dos'
FIXTURE=ROOT/'internal/qbrng/testdata/native_rng_arguments.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='4e7a649528ab9f2dae90ee005ffb104ad577046baa2cd099f2109d220df048c9'
STATIC_SHA='29646e1df14794b8c05f84bb5416c76c5c30bdca988023e4a9e5b666061c2aa1'
CASES={
 'zero-state-zero':(0,('00000000',)), 'zero-state-five':(5,('00000000',)),
 'zero-state-max':(0xffffff,('00000000',)), 'residual-zero':(0x1234ab,('ffff7f00',)),
 'negative-zero':(0x1234ab,('fffffe00',)), 'positive-one':(5,('00000081',)),
 'positive-half':(5,('00000080',)), 'positive-large':(0xffffff,('00004987',)),
 'negative-one':(5,('00008081',)), 'negative-one-old-state':(0x1234ab,('00008081',)),
 'negative-half':(5,('00008080',)), 'negative-large':(5,('0000c987',)),
 'negative-low-carry':(5,('ffff8081',)), 'negative-wrap':(5,('ffffffff',)),
 'mixed':(5,('00000000','00000081','00008081','fffffe00')),
 'mixed-old-state':(0x1234ab,('00004987','0000c987','00000000','00000081')),
}
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload(arguments):
    def assign(at,raw):
        words=struct.unpack('<HH',raw)
        return b''.join(b'\xc7\x06'+struct.pack('<HH',at+2*i,value)for i,value in enumerate(words))
    def output(at):return b'\xbb\x01\x00\xb9\x04\x00\xba'+struct.pack('<H',at)+b'\xb4\x40\xcd\x21'
    prefix=assign(0x1856,b'RND2')+output(0x1856)+output(0x234)+b'\xb9'+struct.pack('<H',64//len(arguments))
    body=b'\x51'
    for raw in arguments:body+=assign(0x1a,bytes.fromhex(raw))+output(0x1a)+bytes.fromhex('bb1a00cd3d339090')+output(0x234)+output(0x1a)
    body+=bytes.fromhex('59497403e9');body+=struct.pack('<h',-len(body)-2)
    return prefix+body+assign(0x1856,b'END!')+output(0x1856)+bytes.fromhex('b8004ccd21')


def verify_trace(trace,initial,arguments):
    assert type(trace)is bytes and len(trace)==780 and trace[:4]==b'RND2'and trace[-4:]==b'END!','exact diagnostic framing'
    assert int.from_bytes(trace[4:8],'little')==initial,'explicit initial raw state'
    state=initial
    for index in range(64):
        at=8+12*index;raw=trace[at:at+4]
        assert raw.hex()==arguments[index%len(arguments)],'declared input sequence'
        if raw[3]!=0:
            if raw[2]&128:
                # Original b316..b32b adds exponent into low mantissa byte,
                # propagating carry through the other two state bytes.
                state=(raw[0]+(raw[1]<<8)+(raw[2]<<16)+raw[3])%(1<<24)
            state=(214013*state+1744579)%(1<<24)
        assert int.from_bytes(trace[at+4:at+8],'little')==state,('native state',index)
        assert decode_single(trace[at+8:at+12])==state/(1<<24),('native numeric FAC',index)
    return state


def verify(directory=DEFAULT,fixture=FIXTURE):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'immutable argument corpus manifest'
    pins=json.loads(raw)['files'];assert{str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}==set(pins),'complete corpus inventory'
    for name,digest in pins.items():assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert(SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original target identity'
    assert runtime[0x3d7:0x3db]==bytes.fromhex('c7b2c2b2'),'RND argument slot33 and argumentless slot34 dispatch'
    native=(ROOT/'research/yt-port-generation/runtime-rea.json').read_bytes();assert SHA(native)==STATIC_SHA,'reuse immutable original native byte packet'
    records=json.loads(native)['records'];record=next(r for r in records if r['evidence_id']=='ev_e8f581f65736b7d492e44136bf3abf1ba826a4339027ca4743411df652ee2884');n=record['normalized_result']
    assert record['subject']['digest']['sha256']==RUNTIME_SHA and n['address']=='0x1b2c2'and n['complete']is True and n['requested_bytes']==n['returned_bytes']==110,'complete original handler observation'
    assert bytes.fromhex(n['bytes_hex'])==runtime[0xb4c2:0xb4c2+110],'native loaded address binds original file bytes'
    source=root/'sources/recover_rng_arguments.py';recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe='brun30-rnd-arguments-v1',cases={k:[state,list(args)]for k,(state,args)in CASES.items()},samples=64,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'fixed prelaunch recipe and executed source'
    assert{p.name for p in root.iterdir()}==set(CASES)|{'pins.json','recipe.json','sources'}and{p.name for p in source.parent.iterdir()}=={source.name},'fixed case/source coverage'
    portable=[]
    for name,(state,args)in CASES.items():
        d=root/name;meta=json.loads((d/'result.json').read_text());stub=expected_payload(args)
        patched=bytearray(original);patched[0x23a:0x23f]=bytes.fromhex('e930009090');patched[0x26d:0x26d+len(stub)]=stub
        copied=bytearray(runtime);struct.pack_into('<I',copied,0x10234,state)
        assert set(meta)=={'recipe','case','initial_state','arguments','exit_code','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'capture schema'
        assert(meta['recipe'],meta['case'],meta['initial_state'],meta['arguments'],meta['exit_code'])==('brun30-rnd-arguments-v1',name,state,list(args),0),'declared diagnostic case'
        assert meta['payload_hex']==stub.hex()and meta['copied_initializer_sha256']==SHA(patched)and meta['copied_runtime_sha256']==SHA(copied),'complete copied executable reconstruction'
        assert set(meta['files'])==FILES and{p.name for p in d.iterdir()}==FILES|{'result.json'},'exact artifacts'
        for file,digest in meta['files'].items():assert SHA((d/file).read_bytes())==digest,'captured file digest'
        commands=(d/'COMMANDS.TXT').read_text().splitlines();assert len(commands)==11 and commands[0].startswith(('mount c /tmp/','mount c /private/tmp/')),'disposable mount'
        assert Path(commands[0][8:]).name==name,'actual corresponding case mount'
        assert commands[1:]==['c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit'],'complete diagnostic commands'
        argv=['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in('-c',c)]
        assert json.loads((d/'launch.json').read_text())==argv,'pinned actual launch'
        messages=[line.split(' | ',1)[1]for line in(d/'dosbox.stderr').read_text().splitlines()if' | 'in line]
        assert[shlex.split(m[11:])for m in messages if m.startswith('arguments: ')]==[argv]and messages.count('dosbox-staging version 0.83.0 ()')==1,'actual host launch/version'
        assert 'SDL: dummy video initialised'in messages and "MIXER: Sound output disabled ('nosound' mode)"in messages and any(m.startswith('CPU: Setting fixed 200000 cycles.')for m in messages),'fixed headless host controls'
        assert(d/'dosbox.stdout').read_bytes()==b''and(d/'ERROR.LOG').read_bytes()==b''and(d/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n'and(d/'RETURN.LOG').read_bytes()==b'PROBE_RETURNED\r\n','zero-exit diagnostic and shell return'
        assert read_date((d/'DOSDATE.LOG').read_bytes()).isoformat()=='2026-11-02'and abs(read_time((d/'DOSTIME.LOG').read_bytes()))<=.1,'raw shell date/time control'
        trace=(d/'TRACE.BIN').read_bytes();final=verify_trace(trace,state,args)
        portable.append(dict(name=name,initial=state,arguments=list(args),trace_hex=trace.hex(),source_trace_sha256=SHA(trace),final=final))
    document=dict(format='qb-native-rnd-arguments-v1',samples_per_case=64,cases=portable)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==document,'portable fixture equals full native corpus'
    return document

if __name__=='__main__':
    result=verify();print('Verified',len(result['cases']),'native argumented-RND controls / 1024 state-value pairs')
