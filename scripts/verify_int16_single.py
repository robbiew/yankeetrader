"""Independent identity, provenance, rational rounding and overflow audit."""
import hashlib, json, shlex, struct
from fractions import Fraction
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-int16/native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_int16_single.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='270c99c7a6e7110a1668bbbe04ea69192f3004b2762c43554e05d9559c405a52'
RAWS=('00000000', '0000007f', '0000807f', 'ffff7f7f', 'ffffff7f', '00000080', '00008080', '01000080', '01008080', '00004080', '0000c080', '00000081', '00008081', '00004081', '0000c081', 'ffff1f82', 'ffff9f82', '00002082', '0000a082', '01002082', '0100a082', '00006082', '0000e082', '00fe7f8f', '00feff8f', '80fe7f8f', '80feff8f', 'fffe7f8f', 'fffeff8f', '00ff7f8f', '00ffff8f', '01ff7f8f', '01ffff8f', '00000090', '00008090', '80000090', '80008090', '81000090', '81008090', '00010090', '00018090', '00000091', '00008091', 'ffff7f00', 'ffffff00', '12345600', 'ffff7fff', 'ffffffff')
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}
CASES={f'op{op:02x}-{i:02d}':dict(op=op,raw=raw,initial=5) for op in (0x75,0x77) for i,raw in enumerate(RAWS)}


def expected_payload(case):
    def assign(at,raw):
        return b''.join(b'\xc7\x06'+struct.pack('<HH',at+2*i,word) for i,word in enumerate(struct.unpack('<HH',raw)))
    def output(at,size): return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    prefix=assign(0x1856,b'C16!')+output(0x1856,4)+output(0x234,4)+assign(0x1a,bytes.fromhex(case['raw']))+output(0x1a,4)+output(0x1f,1)
    call=(bytes.fromhex('be1a00') if case['op']==0x75 else b'')+bytes([0xcd,0x3f,case['op'],0x90,0x90])
    suffix=bytes.fromhex('891e5c18')+output(0x185c,2)+output(0x1a,4)+output(0x234,4)+output(0x1f,1)+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')
    return prefix+call+suffix


def expected_integer(raw):
    if not raw[3]: return 0
    mantissa=(int.from_bytes(raw[:3],'little')&0x7fffff)|(1<<23)
    value=mantissa*Fraction(2)**(raw[3]-152)
    rounded=(value+Fraction(1,2)).numerator//(value+Fraction(1,2)).denominator
    if raw[2]&128: rounded=-rounded
    return rounded if -32768<=rounded<=32767 else None


def verify_trace(trace,case):
    raw=bytes.fromhex(case['raw']); prefix=b'C16!'+struct.pack('<I',case['initial'])+raw+b'\x00'
    assert trace[:13]==prefix,'exact input, RNG and measured default mode'
    want=expected_integer(raw)
    if want is None:
        address='00C1' if case['op']==0x75 else '00BE'
        message=('\r\nOverflow in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace==prefix+message,'complete native overflow; no fabricated result or return frame'
    else:
        assert len(trace)==28 and trace[-4:]==b'END!','complete successful conversion frame'
        assert struct.unpack('<h',trace[13:15])[0]==want,'exact signed16 rounded native result'
        assert trace[15:19]==struct.pack('<h',want)+raw[2:],'FAC low word replaced, high word retained'
        assert trace[19:23]==struct.pack('<I',case['initial']) and trace[23]==0,'RNG and mode preserved on return'
    return want


def verify_static(runtime):
    for name,pin,address,size,file_offset in [
        ('int16-handler.json','9c7ca3fd3d4c66c49f5b302845a1a258c31849a854efeb47f926f661ecd8299d','0x1a8c8',208,0xaac8),
        ('int16-dispatch.json','abc959a26ecdfeea2d256c8b5bc06701a76be1a4e017a57842c6b182b9bcef36','0x10477',6,0x677)]:
        packet=(ROOT/'research/yt-mbf-int16/rea'/name).read_bytes(); assert SHA(packet)==pin,'immutable REA packet'
        envelope=json.loads(packet); assert envelope['ok'] is True
        evidence=envelope['data']; result=evidence['normalized_result']
        assert evidence['subject']['digest']['sha256']==RUNTIME_SHA and evidence['provider']['id']=='ghidra','original runtime REA identity'
        assert result['address']==address and result['complete'] is True and result['requested_bytes']==result['returned_bytes']==size,'complete mapped native byte range'
        assert bytes.fromhex(result['bytes_hex'])==runtime[file_offset:file_offset+size],'original MZ/header mapping'
    assert runtime[0x677:0x67d]==bytes.fromhex('c8a8d5a811a9'),'INT3F/75 and /77 native dispatch'


def verify(directory=DEFAULT,fixture=FIXTURE):
    root=Path(directory); manifest=(root/'pins.json').read_bytes(); assert SHA(manifest)==PINS_SHA,'fixed native manifest'
    pins=json.loads(manifest)['files']
    assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}==set(pins),'complete artifact inventory'
    for name,digest in pins.items(): assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert (SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original executable identity'
    verify_static(runtime)
    source=root/'sources/recover_int16_single.py'; recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe='brun30-int16-single-v1',cases=CASES,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'frozen prelaunch acquisition source and recipe'
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
    document=dict(format='qb-native-int16-single-v1',cases=portable)
    if fixture is not None: assert json.loads(Path(fixture).read_text())==document,'portable fixture equals whole native corpus'
    return document

if __name__=='__main__':
    doc=verify(); print('Verified',len(doc['cases']),'native conversions,',sum(c['value'] is None for c in doc['cases']),'native overflow outcomes')
