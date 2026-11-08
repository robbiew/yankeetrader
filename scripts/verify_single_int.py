"""Independent native SINGLE INT identity, probe, dispatch and raw-byte audit."""
import hashlib,json,shlex,struct
from pathlib import Path
from verify_rng_trace import INIT_SHA,RUNTIME_SHA,decode_single
from verify_rng_clock import read_date,read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-int/native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_int_single.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='17613c08a4cf75f2e23f0495d5b694fa77c24fe809bcac88dab633c352d7dd2b'
CASES={'zero-canonical': (5, ('00000000',)), 'zero-residues': (5, ('ffff7f00', 'ffffff00', '00008000', '12345600')), 'positive-subunit': (5, ('00000001', 'ffff7f7f', '00000080', '00004080')), 'negative-subunit': (5, ('00008001', 'ffffff7f', '00008080', '0000c080')), 'positive-near-one': (5, ('ffff7f80', '00000081', '01000081', 'ffff7f81')), 'negative-near-one': (5, ('ffffff80', '00008081', '01008081', 'ffffff81')), 'positive-fractions': (5, ('00004081', '00002082', '00003e85', '00807f88')), 'negative-fractions': (5, ('0000c081', '0000a082', '0000be85', '0080ff88')), 'positive-byte-boundaries': (5, ('00807f88', '00400089', '80ff7f90', '40000091')), 'negative-byte-boundaries': (5, ('0080ff88', '00408089', '80ffff90', '40008091')), 'positive-precision-boundaries': (5, ('ffff7f97', '00000098', 'ffff7f98', '00000099')), 'negative-precision-boundaries': (5, ('ffffff97', '00008098', 'ffffff98', '00008099')), 'positive-large': (5, ('01000099', 'ffff7fff', '000000ff', 'fffffffe')), 'negative-large': (5, ('01008099', 'ffffffff', '000080ff', 'ffff80fe')), 'mixed-history': (5, ('00003e85', '12345600', '0000c080', 'ffff7f00')), 'mixed-max-rng': (16777215, ('0080ff88', '00004080', 'ffffff00', '00000099'))}
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload(arguments):
    def assign(at,raw):
        words=struct.unpack('<HH',raw)
        return b''.join(b'\xc7\x06'+struct.pack('<HH',at+2*i,value)for i,value in enumerate(words))
    def output(at):return b'\xbb\x01\x00\xb9\x04\x00\xba'+struct.pack('<H',at)+b'\xb4\x40\xcd\x21'
    prefix=assign(0x1856,b'INT2')+output(0x1856)+output(0x234)+b'\xb9'+struct.pack('<H',64//len(arguments))
    body=b'\x51'
    for raw in arguments:body+=assign(0x1a,bytes.fromhex(raw))+output(0x1a)+bytes.fromhex('bb1a00cd3d039090')+output(0x234)+output(0x1a)
    body+=bytes.fromhex('59497403e9');body+=struct.pack('<h',-len(body)-2)
    return prefix+body+assign(0x1856,b'END!')+output(0x1856)+bytes.fromhex('b8004ccd21')


def expected_int(raw):
    from fractions import Fraction
    if raw[3]==0:return raw
    negative=bool(raw[2]&128);mantissa=(int.from_bytes(raw[:3],'little')&0x7fffff)|(1<<23)
    value=mantissa*Fraction(2)**(raw[3]-152)
    if negative:value=-value
    integer=value.numerator//value.denominator
    if not integer:return raw[:3]+b'\x00'
    magnitude=abs(integer);length=magnitude.bit_length();exponent=128+length
    # Native SINGLE values with exponent >=152 are integral, so no integer
    # here requires precision beyond the representable 24 significant bits.
    shift=24-length
    normalized=(magnitude<<shift)if shift>=0 else(magnitude>>(-shift))
    bits=(normalized&0x7fffff)|(0x800000 if integer<0 else 0)
    return bits.to_bytes(3,'little')+bytes([exponent])


def verify_trace(trace,initial,arguments):
    assert type(trace)is bytes and len(trace)==780 and trace[:4]==b'INT2'and trace[-4:]==b'END!','exact diagnostic framing'
    assert int.from_bytes(trace[4:8],'little')==initial,'explicit initial RNG state'
    for index in range(64):
        at=8+12*index;raw=trace[at:at+4];after=trace[at+8:at+12]
        assert raw.hex()==arguments[index%len(arguments)],'declared raw input sequence'
        assert int.from_bytes(trace[at+4:at+8],'little')==initial,'INT must preserve unrelated RNG state'
        assert after==expected_int(raw),('exact native floor FAC bytes',index,raw.hex(),after.hex())
    return initial


def verify(directory=DEFAULT,fixture=FIXTURE):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'immutable argument corpus manifest'
    pins=json.loads(raw)['files'];assert{str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='pins.json'}==set(pins),'complete corpus inventory'
    for name,digest in pins.items():assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert(SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original target identity'
    from verify_maintenance_stock_conversion_native import verify as verify_existing_paths
    verify_existing_paths() # Authenticates the four retained original byte reads.
    assert runtime[0x377:0x379]==bytes.fromhex('b2ac'),'INT3D/03 dispatch'
    source=root/'sources/recover_single_int.py';recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe='brun30-single-int-v1',cases={k:[state,list(args)]for k,(state,args)in CASES.items()},samples=64,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'fixed prelaunch recipe and executed source'
    assert{p.name for p in root.iterdir()}==set(CASES)|{'pins.json','recipe.json','sources'}and{p.name for p in source.parent.iterdir()}=={source.name},'fixed case/source coverage'
    portable=[]
    for name,(state,args)in CASES.items():
        d=root/name;meta=json.loads((d/'result.json').read_text());stub=expected_payload(args)
        patched=bytearray(original);patched[0x23a:0x23f]=bytes.fromhex('e930009090');patched[0x26d:0x26d+len(stub)]=stub
        copied=bytearray(runtime);struct.pack_into('<I',copied,0x10234,state)
        assert set(meta)=={'recipe','case','initial_state','arguments','exit_code','completed','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'capture schema'
        assert(meta['recipe'],meta['case'],meta['initial_state'],meta['arguments'],meta['exit_code'])==('brun30-single-int-v1',name,state,list(args),0),'declared diagnostic case'
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
        trace=(d/'TRACE.BIN').read_bytes();final=verify_trace(trace,state,args)
        portable.append(dict(name=name,initial=state,arguments=list(args),trace_hex=trace.hex(),source_trace_sha256=SHA(trace),final=final))
    document=dict(format='qb-native-int-single-v1',samples_per_case=64,cases=portable)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==document,'portable fixture equals full native corpus'
    return document

if __name__=='__main__':
    result=verify();print('Verified',len(result['cases']),'native INT controls / 1024 raw input-output pairs')
