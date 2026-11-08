"""Independent DOUBLE conversion identity, precision, provenance and overflow audit."""
import hashlib, json, shlex, struct
from fractions import Fraction
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-int16-double/native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_int16_double.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='28e635276fa1306fb672885e08e8d9ac43e6d1e764be55aead8b210ca58130cd'
RAWS=('0000000000000000', '000000000000007f', '000000000000807f', 'ffffffffffff7f7f', 'ffffffffffffff7f', '0000000000000080', '0000000000008080', '0100000000000080', '0100000000008080', '0000000000004080', '000000000000c080', '0000000000000081', '0000000000008081', '0000000000004081', '000000000000c081', 'ffffffffffff1f82', 'ffffffffffff9f82', '0000000000002082', '000000000000a082', '0100000000002082', '010000000000a082', '0000000000006082', '000000000000e082', '0000000000fe7f8f', '0000000000feff8f', '0000000080fe7f8f', '0000000080feff8f', 'fffffffffffe7f8f', 'fffffffffffeff8f', '0000000000ff7f8f', '0000000000ffff8f', '0100000000ff7f8f', '0100000000ffff8f', '0000000000000090', '0000000000008090', '0000000040000090', '0000000040008090', 'ffffffff7f000090', 'ffffffff7f008090', '0000000080000090', '0000000080008090', '0100000080000090', '0100000080008090', '0000000000010090', '0000000000018090', '0000000000000091', '0000000000008091', 'ffffffffffff7f00', 'ffffffffffffff00', '123456789abcde00', 'ffffffffffff7fff', 'ffffffffffffffff')
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}
CASES={f'op{op:02x}-{i:02d}':dict(op=op,raw=raw,initial=5) for op in (0x76,0x78) for i,raw in enumerate(RAWS)}


def expected_payload(case):
    def assign(at,raw):
        return b''.join(b'\xc7\x06'+struct.pack('<HH',at+2*i,word) for i,word in enumerate(struct.unpack('<'+'H'*(len(raw)//2),raw)))
    def output(at,size): return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    prefix=assign(0x1856,b'D16!')+output(0x1856,4)+output(0x234,4)+assign(0x16,bytes.fromhex(case['raw']))+output(0x16,8)+output(0x1f,1)
    call=(bytes.fromhex('be1600') if case['op']==0x76 else b'')+bytes([0xcd,0x3f,case['op'],0x90,0x90])
    suffix=bytes.fromhex('891e5c18')+output(0x185c,2)+output(0x16,8)+output(0x234,4)+output(0x1f,1)+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')
    return prefix+call+suffix


def expected_integer(raw):
    if not raw[7]: return 0
    mantissa=(int.from_bytes(raw[:7],'little')&0x7fffffffffffff)|(1<<55)
    value=mantissa*Fraction(2)**(raw[7]-184)
    rounded=(value+Fraction(1,2)).numerator//(value+Fraction(1,2)).denominator
    if raw[6]&128: rounded=-rounded
    return rounded if -32768<=rounded<=32767 else None


def verify_trace(trace,case):
    raw=bytes.fromhex(case['raw']); prefix=b'D16!'+struct.pack('<I',case['initial'])+raw+b'\x00'
    assert trace[:17]==prefix,'exact input, RNG and measured default mode'
    want=expected_integer(raw)
    if want is None:
        address='00CD' if case['op']==0x76 else '00CA'
        message=('\r\nOverflow in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace==prefix+message,'complete native overflow; no fabricated result or return frame'
    else:
        assert len(trace)==36 and trace[-4:]==b'END!','complete successful conversion frame'
        assert struct.unpack('<h',trace[17:19])[0]==want,'exact signed16 rounded native result'
        assert trace[19:27]==raw[:4]+struct.pack('<h',want)+raw[6:],'FAC result word replaced, lower four and upper two bytes retained'
        assert trace[27:31]==struct.pack('<I',case['initial']) and trace[31]==0,'RNG and mode preserved on return'
    return want


def verify_static(runtime):
    from verify_int16_single import verify_static as verify_shared_kernel
    verify_shared_kernel(runtime) # Reuse the immutable shared entry/kernel observations.
    for name,pin,address,size,file_offset in [
        ('double-helper.json','9cc34d68a3d46be660e242576e01ee4bcc464a5cfde4283f6083f4be36d0804f','0x1a9bc',17,0xabbc),
        ('double-dispatch.json','6b58066246300921f45b54c3e4e27f8e4246146abcad93d35f4822bfc727decc','0x10479',6,0x679)]:
        packet=(ROOT/'research/yt-mbf-int16-double/rea'/name).read_bytes(); assert SHA(packet)==pin,'immutable DOUBLE REA packet'
        envelope=json.loads(packet); assert envelope['ok'] is True
        evidence=envelope['data']; result=evidence['normalized_result']
        assert evidence['subject']['digest']['sha256']==RUNTIME_SHA and evidence['provider']['id']=='ghidra','original runtime REA identity'
        assert result['address']==address and result['complete'] is True and result['requested_bytes']==result['returned_bytes']==size,'complete mapped original range'
        assert bytes.fromhex(result['bytes_hex'])==runtime[file_offset:file_offset+size],'original MZ/header mapping'
    assert runtime[0x679:0x67f]==bytes.fromhex('d5a811a9e0a8'),'INT3F/76 and /78 original dispatch'
    assert runtime[0xabbc:0xabcd]==bytes.fromhex('8b44068b0c0b4c027403b901000b4c04c3'),'DOUBLE low words compressed to sticky bit, not IEEE rounding'


def verify(directory=DEFAULT,fixture=FIXTURE):
    root=Path(directory); manifest=(root/'pins.json').read_bytes(); assert SHA(manifest)==PINS_SHA,'fixed native manifest'
    pins=json.loads(manifest)['files']
    assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}==set(pins),'complete artifact inventory'
    for name,digest in pins.items(): assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert (SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original executable identity'
    verify_static(runtime)
    source=root/'sources/recover_int16_double.py'; recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe='brun30-int16-double-v1',cases=CASES,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'frozen prelaunch acquisition source and recipe'
    assert {p.name for p in root.iterdir()}==set(CASES)|{'pins.json','recipe.json','sources'} and {p.name for p in source.parent.iterdir()}=={source.name},'fixed case/source coverage'
    portable=[]
    for name,case in CASES.items():
        folder=root/name; meta=json.loads((folder/'result.json').read_text()); stub=expected_payload(case)
        patched=bytearray(original); assert patched[0x23a:0x23f]==bytes.fromhex('cd3d439090'); patched[0x23a:0x23f]=bytes.fromhex('e930009090'); patched[0x26d:0x26d+len(stub)]=stub
        copied=bytearray(runtime); struct.pack_into('<I',copied,0x10234,case['initial'])
        assert set(meta)=={'recipe','case','op','raw','initial','exit_code','timeout','missing','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'fixed result schema'
        assert {k:meta[k] for k in case}==case and meta['recipe']==recipe['recipe'] and meta['case']==name,'declared actual case'
        assert meta['exit_code']==0 and meta['timeout'] is False and meta['missing']==[],'normal emulator completion with all outcomes retained'
        assert meta['payload_hex']==stub.hex() and meta['copied_initializer_sha256']==SHA(patched) and meta['copied_runtime_sha256']==SHA(copied),'full copied image reconstruction'
        assert set(meta['files'])==FILES and {p.name for p in folder.iterdir()}==FILES|{'result.json'},'exact case inventory'
        for file,digest in meta['files'].items(): assert SHA((folder/file).read_bytes())==digest,'captured case digest'
        commands=(folder/'COMMANDS.TXT').read_text().splitlines()
        assert len(commands)==11 and commands[0].startswith(('mount c /tmp/','mount c /private/tmp/')) and Path(commands[0][8:]).name==name,'disposable case mount'
        assert commands[1:]==['c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit'],'complete actual commands'
        argv=['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in ('-c',c)]
        assert json.loads((folder/'launch.json').read_text())==argv,'pinned actual launch'
        messages=[line.split(' | ',1)[1] for line in (folder/'dosbox.stderr').read_text().splitlines() if ' | ' in line]
        assert [shlex.split(m[11:]) for m in messages if m.startswith('arguments: ')]==[argv] and messages.count('dosbox-staging version 0.83.0 ()')==1,'actual host/version'
        assert 'SDL: dummy video initialised' in messages and "MIXER: Sound output disabled ('nosound' mode)" in messages and any(m.startswith('CPU: Setting fixed 200000 cycles.') for m in messages),'fixed headless host controls'
        assert (folder/'dosbox.stdout').read_bytes()==b'' and (folder/'ERROR.LOG').read_bytes()==b'' and (folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n' and (folder/'RETURN.LOG').read_bytes()==b'PROBE_RETURNED\r\n','native shell return; ERRORLEVEL alone does not prove conversion success'
        assert read_date((folder/'DOSDATE.LOG').read_bytes()).isoformat()=='2026-11-02' and abs(read_time((folder/'DOSTIME.LOG').read_bytes()))<=.1,'raw date/time controls'
        trace=(folder/'TRACE.BIN').read_bytes(); want=verify_trace(trace,case)
        portable.append(dict(name=name,**case,value=want,trace_hex=trace.hex(),source_trace_sha256=SHA(trace)))
    document=dict(format='qb-native-int16-double-v1',cases=portable)
    if fixture is not None: assert json.loads(Path(fixture).read_text())==document,'portable fixture equals whole native corpus'
    return document

if __name__=='__main__':
    doc=verify(); print('Verified',len(doc['cases']),'native conversions,',sum(c['value'] is None for c in doc['cases']),'native overflow outcomes')
