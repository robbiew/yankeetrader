"""Independent DOUBLE subtraction entry-state, prior-FAC and provenance audit."""
import hashlib, json, shlex, struct
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-subtract-double/native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_subtract_double.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='0e8e95b322ce3640d18cc93f22026e920ce185da4708fa175b11bf85d9602651'
INVENTORY_SHA='611adf045ab48ffc2766d58eab866eaade6573a763652942a7787ece572cf89c'
DIRECT_COUNT=21
INLINE_COUNT=0
BASE_CASES={'both-zero': {'left': '0000000000000000', 'right': '0000000000008000', 'initial': 5},
 'aliases': {'left': '123456789abcde00', 'right': 'ffffffffffff7f00', 'initial': 5},
 'left-zero': {'left': '123456789abcde00', 'right': '0000000000000081', 'initial': 5},
 'right-zero': {'left': '0000000000000081', 'right': '123456789abc5e00', 'initial': 5},
 'max-zero': {'left': 'ffffffffffff7fff', 'right': '123456789abc5e00', 'initial': 5},
 'zero-max': {'left': '123456789abcde00', 'right': 'ffffffffffff7fff', 'initial': 5},
 'one': {'left': '0000000000000081', 'right': '0000000000008081', 'initial': 5},
 'one-negative': {'left': '0000000000008081', 'right': '0000000000000081', 'initial': 5},
 'fraction': {'left': '0000000000004081', 'right': '000000000000c081', 'initial': 5},
 'cancel': {'left': '0000000000004081', 'right': '0000000000004081', 'initial': 5},
 'cancel-reverse': {'left': '000000000000c081', 'right': '000000000000c081', 'initial': 5},
 'sign-cross': {'left': '0000000000002081', 'right': '0000000000004081', 'initial': 5},
 'raw': {'left': 'cdab896745230181', 'right': '436587a9cbedef81', 'initial': 5},
 'raw-reversed': {'left': '436587a9cbed6f81', 'right': 'cdab896745238181', 'initial': 5},
 'minimum-one-bit': {'left': '0100000000000001', 'right': '0000000000000001', 'initial': 5},
 'minimum-cancel': {'left': '0100000000000001', 'right': '0100000000000001', 'initial': 5},
 'minimum-binade': {'left': 'ffffffffffff7f01', 'right': '0000000000008001', 'initial': 5},
 'max-min': {'left': 'ffffffffffff7fff', 'right': '0000000000008001', 'initial': 5},
 'overflow': {'left': 'ffffffffffff7fff', 'right': 'ffffffffffffffff', 'initial': 5},
 'negative-overflow': {'left': 'ffffffffffffffff', 'right': 'ffffffffffff7fff', 'initial': 5},
 'overflow-round': {'left': 'ffffffffffff7fff', 'right': '00000000000080c7', 'initial': 5},
 'max-in-range': {'left': 'ffffffffffff7fff', 'right': '00000000000080c6', 'initial': 5},
 'high-cancel': {'left': 'ffffffffffff7fff', 'right': 'ffffffffffff7fff', 'initial': 5},
 'half-odd0-tail0': {'left': '0000000000000081', 'right': '0000000000008049', 'initial': 5},
 'half-odd0-tail1': {'left': '0000000000000081', 'right': '0100000000008049', 'initial': 5},
 'half-odd0-tail36028797018963967': {'left': '0000000000000081',
                                     'right': 'ffffffffffffff49',
                                     'initial': 5},
 'half-odd1-tail0': {'left': '0100000000000081', 'right': '0000000000008049', 'initial': 5},
 'half-odd1-tail1': {'left': '0100000000000081', 'right': '0100000000008049', 'initial': 5},
 'half-odd1-tail36028797018963967': {'left': '0100000000000081',
                                     'right': 'ffffffffffffff49',
                                     'initial': 5},
 'same-gap0': {'left': 'cdab896745230181', 'right': '436587a9cbedef81', 'initial': 5},
 'opposite-gap0': {'left': 'cdab896745230181', 'right': '436587a9cbed6f81', 'initial': 5},
 'same-gap1': {'left': 'cdab896745230181', 'right': '436587a9cbedef80', 'initial': 5},
 'opposite-gap1': {'left': 'cdab896745230181', 'right': '436587a9cbed6f80', 'initial': 5},
 'same-gap5': {'left': 'cdab896745230181', 'right': '436587a9cbedef7c', 'initial': 5},
 'opposite-gap5': {'left': 'cdab896745230181', 'right': '436587a9cbed6f7c', 'initial': 5},
 'same-gap6': {'left': 'cdab896745230181', 'right': '436587a9cbedef7b', 'initial': 5},
 'opposite-gap6': {'left': 'cdab896745230181', 'right': '436587a9cbed6f7b', 'initial': 5},
 'same-gap7': {'left': 'cdab896745230181', 'right': '436587a9cbedef7a', 'initial': 5},
 'opposite-gap7': {'left': 'cdab896745230181', 'right': '436587a9cbed6f7a', 'initial': 5},
 'same-gap8': {'left': 'cdab896745230181', 'right': '436587a9cbedef79', 'initial': 5},
 'opposite-gap8': {'left': 'cdab896745230181', 'right': '436587a9cbed6f79', 'initial': 5},
 'same-gap13': {'left': 'cdab896745230181', 'right': '436587a9cbedef74', 'initial': 5},
 'opposite-gap13': {'left': 'cdab896745230181', 'right': '436587a9cbed6f74', 'initial': 5},
 'same-gap14': {'left': 'cdab896745230181', 'right': '436587a9cbedef73', 'initial': 5},
 'opposite-gap14': {'left': 'cdab896745230181', 'right': '436587a9cbed6f73', 'initial': 5},
 'same-gap15': {'left': 'cdab896745230181', 'right': '436587a9cbedef72', 'initial': 5},
 'opposite-gap15': {'left': 'cdab896745230181', 'right': '436587a9cbed6f72', 'initial': 5},
 'same-gap16': {'left': 'cdab896745230181', 'right': '436587a9cbedef71', 'initial': 5},
 'opposite-gap16': {'left': 'cdab896745230181', 'right': '436587a9cbed6f71', 'initial': 5},
 'same-gap17': {'left': 'cdab896745230181', 'right': '436587a9cbedef70', 'initial': 5},
 'opposite-gap17': {'left': 'cdab896745230181', 'right': '436587a9cbed6f70', 'initial': 5},
 'same-gap31': {'left': 'cdab896745230181', 'right': '436587a9cbedef62', 'initial': 5},
 'opposite-gap31': {'left': 'cdab896745230181', 'right': '436587a9cbed6f62', 'initial': 5},
 'same-gap32': {'left': 'cdab896745230181', 'right': '436587a9cbedef61', 'initial': 5},
 'opposite-gap32': {'left': 'cdab896745230181', 'right': '436587a9cbed6f61', 'initial': 5},
 'same-gap33': {'left': 'cdab896745230181', 'right': '436587a9cbedef60', 'initial': 5},
 'opposite-gap33': {'left': 'cdab896745230181', 'right': '436587a9cbed6f60', 'initial': 5},
 'same-gap47': {'left': 'cdab896745230181', 'right': '436587a9cbedef52', 'initial': 5},
 'opposite-gap47': {'left': 'cdab896745230181', 'right': '436587a9cbed6f52', 'initial': 5},
 'same-gap48': {'left': 'cdab896745230181', 'right': '436587a9cbedef51', 'initial': 5},
 'opposite-gap48': {'left': 'cdab896745230181', 'right': '436587a9cbed6f51', 'initial': 5},
 'same-gap49': {'left': 'cdab896745230181', 'right': '436587a9cbedef50', 'initial': 5},
 'opposite-gap49': {'left': 'cdab896745230181', 'right': '436587a9cbed6f50', 'initial': 5},
 'same-gap53': {'left': 'cdab896745230181', 'right': '436587a9cbedef4c', 'initial': 5},
 'opposite-gap53': {'left': 'cdab896745230181', 'right': '436587a9cbed6f4c', 'initial': 5},
 'same-gap54': {'left': 'cdab896745230181', 'right': '436587a9cbedef4b', 'initial': 5},
 'opposite-gap54': {'left': 'cdab896745230181', 'right': '436587a9cbed6f4b', 'initial': 5},
 'same-gap55': {'left': 'cdab896745230181', 'right': '436587a9cbedef4a', 'initial': 5},
 'opposite-gap55': {'left': 'cdab896745230181', 'right': '436587a9cbed6f4a', 'initial': 5},
 'same-gap56': {'left': 'cdab896745230181', 'right': '436587a9cbedef49', 'initial': 5},
 'opposite-gap56': {'left': 'cdab896745230181', 'right': '436587a9cbed6f49', 'initial': 5},
 'same-gap57': {'left': 'cdab896745230181', 'right': '436587a9cbedef48', 'initial': 5},
 'opposite-gap57': {'left': 'cdab896745230181', 'right': '436587a9cbed6f48', 'initial': 5},
 'same-gap58': {'left': 'cdab896745230181', 'right': '436587a9cbedef47', 'initial': 5},
 'opposite-gap58': {'left': 'cdab896745230181', 'right': '436587a9cbed6f47', 'initial': 5},
 'boundary-opposite-gap55': {'left': '0000000000000081', 'right': '000000000000404a', 'initial': 5},
 'boundary-negative-gap55': {'left': '0000000000008081', 'right': '000000000000c04a', 'initial': 5},
 'boundary-reverse-gap55': {'left': '000000000000c04a', 'right': '0000000000008081', 'initial': 5},
 'boundary-opposite-gap56': {'left': '0000000000000081', 'right': '0000000000004049', 'initial': 5},
 'boundary-negative-gap56': {'left': '0000000000008081', 'right': '000000000000c049', 'initial': 5},
 'boundary-reverse-gap56': {'left': '000000000000c049', 'right': '0000000000008081', 'initial': 5},
 'boundary-opposite-gap57': {'left': '0000000000000081', 'right': '0000000000004048', 'initial': 5},
 'boundary-negative-gap57': {'left': '0000000000008081', 'right': '000000000000c048', 'initial': 5},
 'boundary-reverse-gap57': {'left': '000000000000c048', 'right': '0000000000008081', 'initial': 5},
 'boundary-opposite-gap58': {'left': '0000000000000081', 'right': '0000000000004047', 'initial': 5},
 'boundary-negative-gap58': {'left': '0000000000008081', 'right': '000000000000c047', 'initial': 5},
 'boundary-reverse-gap58': {'left': '000000000000c047', 'right': '0000000000008081', 'initial': 5},
 'max-rng-cancel': {'left': '0100000000000081', 'right': '0100000000000081', 'initial': 16777215},
 'max-rng-half': {'left': '0100000000000081', 'right': '0100000000008049', 'initial': 16777215},
 'reverse-aliases': {'left': 'ffffffffffffff00', 'right': '123456789abcde00', 'initial': 5},
 'sub-one-three': {'left': '0000000000000081', 'right': '0000000000004082', 'initial': 5},
 'sub-three-one': {'left': '0000000000004082', 'right': '0000000000000081', 'initial': 16777215}}


def expected_cases():
    result={f'op9a-{n}':dict(op=0x9a,**c,fac=c['left']) for n,c in BASE_CASES.items()}
    names=('both-zero','aliases','left-zero','right-zero','max-zero','cancel','cancel-reverse','minimum-one-bit','minimum-cancel','half-odd0-tail0','half-odd1-tail0','half-odd0-tail1','boundary-opposite-gap56','boundary-opposite-gap57','sign-cross','overflow','overflow-round','negative-overflow','raw','raw-reversed')
    for op in (0x98,0x9c):
        for n in names:
            c=BASE_CASES[n];result[f'op{op:02x}-{n}']=dict(op=op,**c,fac='5aa5d5c33c918092' if op==0x98 else c['right'])
    for index,fac in enumerate(('0000000000000000','123456789abcde00','0100000000008001','ffffffffffffffff')):
        for n in ('aliases','cancel','minimum-one-bit','minimum-cancel'):
            result[f'fac{index}-{n}']=dict(op=0x98,**dict(BASE_CASES[n],initial=16777215),fac=fac)
    return result

CASES=expected_cases()
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload(case):
    assert case['op'] in (0x98,0x9a,0x9c)
    def assign(at,raw):return b''.join(bytes.fromhex('c706')+struct.pack('<HH',at+2*i,word) for i,word in enumerate(struct.unpack('<'+'H'*(len(raw)//2),raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    prefix=assign(0x1856,b'DSD1')+output(0x1856,4)+output(0x234,4)
    inputs=assign(0x16,bytes.fromhex(case['fac']))+output(0x16,8)+assign(0x1860,bytes.fromhex(case['left']))+output(0x1860,8)+assign(0x1868,bytes.fromhex(case['right']))+output(0x1868,8)+output(0x1f,1)
    call=bytes.fromhex('be6018')+(bytes.fromhex('bf6818') if case['op'] in (0x98,0x9a) else b'')+bytes([0xcd,0x3f,case['op'],0x90,0x90])
    suffix=output(0x16,8)+output(0x1860,8)+output(0x1868,8)+output(0x234,4)+output(0x1f,1)+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')
    return prefix+inputs+call+suffix


def decode(raw):
    from fractions import Fraction
    if not raw[7]:return Fraction(0)
    value=((int.from_bytes(raw[:7],'little')&((1<<55)-1))|(1<<55))*Fraction(2)**(raw[7]-184)
    return -value if raw[6]&128 else value


def expected_entry(left,right,fac):
    from fractions import Fraction
    negated=bytearray(right);negated[6]^=128;negated=bytes(negated)
    if not left[7]:return negated
    if not right[7]:return left
    if abs(left[7]-right[7])>56:return left if left[7]>right[7] else negated
    value=decode(left)-decode(right)
    if not value or abs(value)<Fraction(2)**-128:return fac[:7]+b'\x00'
    negative=value<0;value=abs(value)
    power=value.numerator.bit_length()-value.denominator.bit_length()
    if value<Fraction(2)**power:power-=1
    exponent=power+129;scaled=value*Fraction(2)**(55-power)
    mantissa,rest=divmod(scaled.numerator,scaled.denominator)
    if rest*2>scaled.denominator or(rest*2==scaled.denominator and mantissa%2):mantissa+=1
    if mantissa==1<<56:mantissa>>=1;exponent+=1
    if exponent>255:return None
    bits=(mantissa&((1<<55)-1))|((1<<55) if negative else 0)
    return bits.to_bytes(7,'little')+bytes([exponent])


def error_address(case):
    p=expected_payload(case);call=bytes([0xcd,0x3f,case['op'],0x90,0x90]);assert p.count(call)==1
    return f'{0x6d+p.index(call)+5:04X}'


def verify_trace(trace,case):
    left=bytes.fromhex(case['left']);right=bytes.fromhex(case['right']);fac=bytes.fromhex(case['fac'])
    assert case['op'] in (0x98,0x9a,0x9c),'only qualified direct entry forms'
    if case['op']==0x9c:assert fac==right,'entry9c right operand is the initial FAC, not the memory shadow'
    if case['op']==0x9a:assert fac==left,'entry9a left operand is the initial FAC, not the memory shadow'
    prefix=b'DSD1'+struct.pack('<I',case['initial'])+fac+left+right+b'\x00'
    assert trace[:33]==prefix,'exact initial FAC, ordered operands, RNG and mode'
    want=expected_entry(left,right,fac)
    if want is None:
        address=error_address(case)
        message=('\r\nOverflow in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace==prefix+message,'exact entry-specific native overflow without fabricated state'
    else:
        assert len(trace)==66 and trace[-4:]==b'END!','complete entry-state return frame'
        assert trace[33:41]==want,'exact result and prior-FAC residue'
        assert trace[41:49]==left and trace[49:57]==right,'both memory blocks preserved (left/right shadows for entry9a/9c respectively)'
        assert trace[57:61]==struct.pack('<I',case['initial']) and trace[61]==0,'unrelated RNG and mode preserved'
    return want


def verify_static(runtime):
    import verify_add_double as addition
    addition.verify_static(runtime) # immutable wrapper/kernel/ABI/error packets
    assert [struct.unpack_from('<H',runtime,0x58d+2*op)[0]for op in (0x98,0x9a,0x9c)]==[0xad8c,0xad81,0xad89]
    assert runtime[0xaf81:0xaf97]==bytes.fromhex('be1600eb06e83a71bf1600e8dc718b4d0680f180eb1c'),'direct bindings and register-only right sign flip'
    return verify_inventory()

def verify_inventory():
    import re
    raw=(ROOT/'research/yt-mbf-subtract-double/maintenance-calls.json').read_bytes()
    assert SHA(raw)==INVENTORY_SHA,'fixed original-byte inventory'
    d=json.loads(raw);r=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();listing=(ROOT/'archive/analysis/yt-maint/qb-annotated.txt').read_bytes()
    assert d['format']=='maintenance-direct-double-subtract-callers-v1'
    assert d['authority']=='Static annotated call-site inventory matched to archived bytes; not observed execution or exhaustive indirect coverage.'
    assert SHA(r)==d['original_sha256']=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
    assert SHA(listing)==d['listing_sha256']=='097f46fd3f0e70743b9b89b56c8f5efd13f2bc2b6faf081aae4bb1b0583004c2'
    calls=[];inline=[]
    for address,op in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_(98|9a|9c)\s*\n',listing.decode()):
        off=int(address,16);v=int(op,16);assert r[512+off:512+off+5]==bytes([0xcd,0x3f,v,0x90,0x90]);calls.append(dict(op=v,code_offset=off,file_offset=512+off))
    for address,selector in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_9e[^\n]*\n\s+INLINE ([0-9a-fA-F]{2})\s*\n',listing.decode()):
        off=int(address,16);v=int(selector,16);assert r[512+off:512+off+6]==bytes.fromhex('cd3f9e9090')+bytes([v]);inline.append(dict(code_offset=off,file_offset=512+off,selector=v))
    assert calls==d['direct_calls'] and inline==d['excluded_inline_calls']
    assert len(calls)==DIRECT_COUNT and len(inline)==INLINE_COUNT
    return calls,inline


def verify_corpus(directory,cases,pins_sha,recipe_id,source_name):
    root=Path(directory); manifest=(root/'pins.json').read_bytes(); assert SHA(manifest)==pins_sha,'fixed native manifest'
    pins=json.loads(manifest)['files']
    assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}==set(pins),'complete artifact inventory'
    for name,digest in pins.items(): assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert (SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original executable identity'
    verify_static(runtime)
    source=root/'sources'/source_name; recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe=recipe_id,cases=cases,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'frozen prelaunch acquisition source and recipe'
    assert {p.name for p in root.iterdir()}==set(cases)|{'pins.json','recipe.json','sources'} and {p.name for p in source.parent.iterdir()}=={source.name},'fixed case/source coverage'
    portable=[]
    for name,case in cases.items():
        folder=root/name; meta=json.loads((folder/'result.json').read_text()); stub=expected_payload(case)
        patched=bytearray(original); assert patched[0x23a:0x23f]==bytes.fromhex('cd3d439090'); patched[0x23a:0x23f]=bytes.fromhex('e930009090'); patched[0x26d:0x26d+len(stub)]=stub
        table=struct.unpack_from('<H',original,24)[0]
        for index in range(struct.unpack_from('<H',original,6)[0]):
            offset,segment=struct.unpack_from('<HH',original,table+4*index);at=16*segment+offset
            assert all(not(at<end and at+2>start) for start,end in ((0x3a,0x3f),(0x6d,0x6d+len(stub)))),'no loader relocation overlaps the diagnostic'
        copied=bytearray(runtime); struct.pack_into('<I',copied,0x10234,case['initial'])
        assert set(meta)=={'recipe','case','op','left','right','initial','fac','exit_code','timeout','missing','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'fixed result schema'
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
        portable.append(dict(name=name,**case,output=want.hex() if want is not None else None,trace_hex=trace.hex(),source_trace_sha256=SHA(trace)))
    return portable


def verify(directory=DEFAULT,fixture=FIXTURE):
    rows=verify_corpus(directory,CASES,PINS_SHA,'brun30-subtract-double-entry-state-v1','recover_subtract_double.py')
    doc=dict(format='qb-native-subtract-double-v1',cases=rows)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==doc,'portable fixture equals complete native corpus'
    return doc

if __name__=='__main__':
    d=verify();print('Verified',len(d['cases']),'DOUBLE subtraction controls;',sum(c['output'] is None for c in d['cases']),'exact native Overflows')
