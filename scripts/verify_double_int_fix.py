"""Independent native DOUBLE INT/FIX identity, probe, dispatch and raw-byte audit."""
import hashlib,json,shlex,struct
from pathlib import Path
from verify_rng_trace import INIT_SHA,RUNTIME_SHA
from verify_rng_clock import read_date,read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-double/native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_int_fix_double.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='b5d81a322d78bdb18fd9b478b2b2dbee97429039b7afdb12f21408e269dfc5cc'
CASES={'int-zero-aliases': ('int', 5, ('0000000000000000', 'ffffffffffff7f00', 'ffffffffffffff00', '123456789abcde00')), 'int-positive-subunit': ('int', 5, ('0000000000000080', '0000000000004080', 'ffffffffffff7f80', '0000000000000001')), 'int-negative-subunit': ('int', 5, ('0000000000008080', '000000000000c080', 'ffffffffffffff80', '0000000000008001')), 'int-positive-fractions': ('int', 5, ('0000000000004081', '0000000000002082', '0000000000003e85', '0000000000807f88')), 'int-negative-fractions': ('int', 5, ('000000000000c081', '000000000000a082', '000000000000be85', '000000000080ff88')), 'int-positive-byte-boundaries': ('int', 5, ('0000000000807f88', '0000000000400089', '0000000080ff7f90', '0000000040000091')), 'int-negative-byte-boundaries': ('int', 5, ('000000000080ff88', '0000000000408089', '0000000080ffff90', '0000000040008091')), 'int-positive-precision': ('int', 5, ('fcffffffffff7fb5', '02000000000000b6', 'ffffffffffff7fb7', 'ffffffffffff7fb8')), 'int-negative-precision': ('int', 5, ('fcffffffffffffb5', '02000000000080b6', 'ffffffffffffffb7', 'ffffffffffffffb8')), 'int-positive-large': ('int', 5, ('00000000000000b9', '01000000000000d1', 'ffffffffffff7fff', '01000000000000ff')), 'int-negative-large': ('int', 5, ('00000000000080b9', '01000000000080d1', 'ffffffffffffffff', '01000000000080ff')), 'int-mixed-history': ('int', 16777215, ('000000000080ff88', '0000000000004080', '123456789abcde00', '02000000000000b6')), 'fix-zero-aliases': ('fix', 5, ('0000000000000000', 'ffffffffffff7f00', 'ffffffffffffff00', '123456789abcde00')), 'fix-positive-subunit': ('fix', 5, ('0000000000000080', '0000000000004080', 'ffffffffffff7f80', '0000000000000001')), 'fix-negative-subunit': ('fix', 5, ('0000000000008080', '000000000000c080', 'ffffffffffffff80', '0000000000008001')), 'fix-positive-fractions': ('fix', 5, ('0000000000004081', '0000000000002082', '0000000000003e85', '0000000000807f88')), 'fix-negative-fractions': ('fix', 5, ('000000000000c081', '000000000000a082', '000000000000be85', '000000000080ff88')), 'fix-positive-byte-boundaries': ('fix', 5, ('0000000000807f88', '0000000000400089', '0000000080ff7f90', '0000000040000091')), 'fix-negative-byte-boundaries': ('fix', 5, ('000000000080ff88', '0000000000408089', '0000000080ffff90', '0000000040008091')), 'fix-positive-precision': ('fix', 5, ('fcffffffffff7fb5', '02000000000000b6', 'ffffffffffff7fb7', 'ffffffffffff7fb8')), 'fix-negative-precision': ('fix', 5, ('fcffffffffffffb5', '02000000000080b6', 'ffffffffffffffb7', 'ffffffffffffffb8')), 'fix-positive-large': ('fix', 5, ('00000000000000b9', '01000000000000d1', 'ffffffffffff7fff', '01000000000000ff')), 'fix-negative-large': ('fix', 5, ('00000000000080b9', '01000000000080d1', 'ffffffffffffffff', '01000000000080ff')), 'fix-mixed-history': ('fix', 16777215, ('000000000080ff88', '0000000000004080', '123456789abcde00', '02000000000000b6'))}
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload(operation,arguments):
    def assign(at,raw):
        words=struct.unpack('<'+'H'*(len(raw)//2),raw)
        return b''.join(b'\xc7\x06'+struct.pack('<HH',at+2*i,value)for i,value in enumerate(words))
    def output(at,count=4):return b'\xbb\x01\x00\xb9'+struct.pack('<H',count)+b'\xba'+struct.pack('<H',at)+b'\xb4\x40\xcd\x21'
    prefix=assign(0x1856,b'DINT'if operation=='int'else b'DFIX')+output(0x1856)+output(0x234)+b'\xb9'+struct.pack('<H',64//len(arguments))
    body=b'\x51'
    for raw in arguments:body+=assign(0x16,bytes.fromhex(raw))+output(0x16,8)+bytes.fromhex('bb1600cd3d'+('04'if operation=='int'else'02')+'9090')+output(0x234)+output(0x16,8)
    body+=bytes.fromhex('59497403e9');body+=struct.pack('<h',-len(body)-2)
    return prefix+body+assign(0x1856,b'END!')+output(0x1856)+bytes.fromhex('b8004ccd21')


def expected_double(raw,operation):
    from fractions import Fraction
    assert type(raw)is bytes and len(raw)==8 and operation in('int','fix'),'typed raw DOUBLE operation'
    if raw[7]==0:return raw
    mantissa=(int.from_bytes(raw[:7],'little')&((1<<55)-1))|(1<<55)
    value=mantissa*Fraction(2)**(raw[7]-184)
    if raw[6]&128:value=-value
    if operation=='int':integer=value.numerator//value.denominator
    else:
        integer=abs(value.numerator)//value.denominator
        if value<0:integer=-integer
    if not integer:return raw[:7]+b'\x00'
    magnitude=abs(integer);length=magnitude.bit_length()
    normalized=magnitude*Fraction(2)**(56-length)
    assert normalized.denominator==1,'integer is exactly representable in DOUBLE precision'
    bits=(int(normalized)&((1<<55)-1))|((1<<55)if integer<0 else 0)
    return bits.to_bytes(7,'little')+bytes([128+length])


def verify_trace(trace,operation,initial,arguments):
    assert type(trace)is bytes and len(trace)==1292 and trace[:4]==(b'DINT'if operation=='int'else b'DFIX')and trace[-4:]==b'END!','exact operation-specific diagnostic framing'
    assert int.from_bytes(trace[4:8],'little')==initial,'explicit initial RNG state'
    for index in range(64):
        at=8+20*index;raw=trace[at:at+8];after=trace[at+12:at+20]
        assert raw.hex()==arguments[index%len(arguments)],'declared raw DOUBLE input sequence'
        assert int.from_bytes(trace[at+8:at+12],'little')==initial,'numeric operations preserve unrelated RNG state'
        assert after==expected_double(raw,operation),('exact native DOUBLE FAC bytes',index,raw.hex(),after.hex())
    return initial


def verify(directory=DEFAULT,fixture=FIXTURE):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'immutable argument corpus manifest'
    pins=json.loads(raw)['files'];assert{str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}==set(pins),'complete corpus inventory'
    for name,digest in pins.items():assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert(SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original target identity'
    from verify_maintenance_stock_conversion_native import verify as verify_existing_paths
    verify_existing_paths() # Authenticates the four retained original byte reads.
    assert runtime[0x375:0x37b]==bytes.fromhex('a2acb2ac0aad'),'DOUBLE FIX02 and INT04 dispatch'
    assert runtime[0xaea2:0xaeb2]==bytes.fromhex('87f3e8cd0087f351b90600e8670059cb'),'DOUBLE FIX load, count-six mask and return'
    assert runtime[0xaf0a:0xaf17]==bytes.fromhex('87f3e8650087f351b90600ebaa'),'DOUBLE INT load, count-six and shared sign path'
    source=root/'sources/recover_double_int_fix.py';recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe='brun30-double-int-fix-v1',cases={k:[op,state,list(args)]for k,(op,state,args)in CASES.items()},samples=64,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'fixed prelaunch recipe and executed source'
    assert{p.name for p in root.iterdir()}==set(CASES)|{'pins.json','recipe.json','sources'}and{p.name for p in source.parent.iterdir()}=={source.name},'fixed case/source coverage'
    portable=[]
    for name,(operation,state,args)in CASES.items():
        d=root/name;meta=json.loads((d/'result.json').read_text());stub=expected_payload(operation,args)
        patched=bytearray(original);patched[0x23a:0x23f]=bytes.fromhex('e930009090');patched[0x26d:0x26d+len(stub)]=stub
        copied=bytearray(runtime);struct.pack_into('<I',copied,0x10234,state)
        assert set(meta)=={'recipe','case','operation','initial_state','arguments','exit_code','completed','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'capture schema'
        assert(meta['recipe'],meta['case'],meta['operation'],meta['initial_state'],meta['arguments'],meta['exit_code'])==('brun30-double-int-fix-v1',name,operation,state,list(args),0),'declared diagnostic case'
        assert meta['completed']is True,'complete normal diagnostic outcome'
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
        trace=(d/'TRACE.BIN').read_bytes();final=verify_trace(trace,operation,state,args)
        portable.append(dict(name=name,operation=operation,initial=state,arguments=list(args),trace_hex=trace.hex(),source_trace_sha256=SHA(trace),final=final))
    document=dict(format='qb-native-int-fix-double-v1',samples_per_case=64,cases=portable)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==document,'portable fixture equals full native corpus'
    return document

if __name__=='__main__':
    result=verify();print('Verified',len(result['cases']),'native DOUBLE controls / 1536 raw input-output pairs')
