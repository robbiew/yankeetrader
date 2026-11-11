"""Independent division entry-state, prior-FAC and provenance audit."""
import hashlib, json, shlex, struct
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-divide/native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_divide_single.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='91d3fffb144ee8c86115de88b728c84b34b66959197d0d614aaef252e82782af'
BASE_CASES={'both-zero': {'left': '00000000', 'right': '00000000', 'initial': 5},
 'aliases': {'left': '12345600', 'right': 'ffffff00', 'initial': 5},
 'left-zero': {'left': '12345600', 'right': '00008081', 'initial': 5},
 'right-zero': {'left': '00004081', 'right': 'ffffff00', 'initial': 5},
 'max-zero': {'left': 'ffff7fff', 'right': '12345600', 'initial': 5},
 'zero-max': {'left': 'ffffff00', 'right': 'ffffffff', 'initial': 5},
 'one': {'left': '00000081', 'right': '00000081', 'initial': 5},
 'three-two': {'left': '00004082', 'right': '00000082', 'initial': 5},
 'two-three': {'left': '00000082', 'right': '00004082', 'initial': 5},
 'one-three': {'left': '00000081', 'right': '00004082', 'initial': 5},
 'raw': {'left': '56341281', 'right': 'ac681381', 'initial': 5},
 'raw-reversed': {'left': 'ac681381', 'right': '56341281', 'initial': 5},
 'million-half': {'left': '00247494', 'right': '00000080', 'initial': 5},
 'thousand-tenth': {'left': '00007a8a', 'right': 'cdcc4c7d', 'initial': 5},
 'max-one': {'left': 'ffff7fff', 'right': '00000081', 'initial': 5},
 'min-one': {'left': '00000001', 'right': '00000081', 'initial': 5},
 'min-two': {'left': '00000001', 'right': '00000082', 'initial': 5},
 'max-half': {'left': 'ffff7fff', 'right': '00000080', 'initial': 5},
 'max-min': {'left': 'ffff7fff', 'right': '00000001', 'initial': 5},
 'min-max': {'left': '00000001', 'right': 'ffff7fff', 'initial': 5},
 'near-two': {'left': 'ffff7f81', 'right': '00000081', 'initial': 5},
 'near-one-below': {'left': 'feff7f81', 'right': 'ffff7f81', 'initial': 5},
 'guard23-below-odd': {'left': '9ff50b81', 'right': 'd7440881', 'initial': 5},
 'guard23-above-even': {'left': 'f12d1681', 'right': '0fb61481', 'initial': 5},
 'guard24-below-odd': {'left': '868d1281', 'right': '7b4d6c81', 'initial': 5},
 'guard24-above-even': {'left': '6d2b2281', 'right': 'c3622e81', 'initial': 5},
 'delta-129-below': {'left': '00000001', 'right': 'ffff7f82', 'initial': 5},
 'delta-129-equal': {'left': '00000001', 'right': '00000082', 'initial': 5},
 'delta-129-above': {'left': 'ffff7f01', 'right': '00000082', 'initial': 5},
 'delta-128-below': {'left': '00000001', 'right': 'ffff7f81', 'initial': 5},
 'delta-128-equal': {'left': '00000001', 'right': '00000081', 'initial': 5},
 'delta-128-above': {'left': 'ffff7f01', 'right': '00000081', 'initial': 5},
 'delta-127-below': {'left': '00000001', 'right': 'ffff7f80', 'initial': 5},
 'delta-127-equal': {'left': '00000001', 'right': '00000080', 'initial': 5},
 'delta-127-above': {'left': 'ffff7f01', 'right': '00000080', 'initial': 5},
 'delta126-below': {'left': '0000007f', 'right': 'ffff7f01', 'initial': 5},
 'delta126-equal': {'left': '0000007f', 'right': '00000001', 'initial': 5},
 'delta126-above': {'left': 'ffff7f7f', 'right': '00000001', 'initial': 5},
 'delta127-below': {'left': '00000080', 'right': 'ffff7f01', 'initial': 5},
 'delta127-equal': {'left': '00000080', 'right': '00000001', 'initial': 5},
 'delta127-above': {'left': 'ffff7f80', 'right': '00000001', 'initial': 5},
 'delta128-below': {'left': '00000081', 'right': 'ffff7f01', 'initial': 5},
 'delta128-equal': {'left': '00000081', 'right': '00000001', 'initial': 5},
 'delta128-above': {'left': 'ffff7f81', 'right': '00000001', 'initial': 5},
 'three-two-negative': {'left': '0000c082', 'right': '00000082', 'initial': 5},
 'one-three-negative': {'left': '00008081', 'right': '00004082', 'initial': 5},
 'raw-negative': {'left': '56349281', 'right': 'ac681381', 'initial': 5},
 'guard23-below-odd-negative': {'left': '9ff58b81', 'right': 'd7440881', 'initial': 5},
 'guard23-above-even-negative': {'left': 'f12d9681', 'right': '0fb61481', 'initial': 5},
 'guard24-below-odd-negative': {'left': '868d9281', 'right': '7b4d6c81', 'initial': 5},
 'guard24-above-even-negative': {'left': '6d2ba281', 'right': 'c3622e81', 'initial': 5},
 'min-two-negative': {'left': '00008001', 'right': '00000082', 'initial': 5},
 'max-half-negative': {'left': 'ffffffff', 'right': '00000080', 'initial': 5},
 'negative-right': {'left': '00004082', 'right': '00008082', 'initial': 5},
 'both-negative': {'left': '0000c082', 'right': '00008082', 'initial': 5},
 'max-rng-zero': {'left': '12345600', 'right': '00008081', 'initial': 16777215},
 'max-rng-guard': {'left': '6d2b2281', 'right': 'c3622e81', 'initial': 16777215}}

def expected_cases():
    result={f'op89-{n}':dict(op=0x89,**c,fac=c['left']) for n,c in BASE_CASES.items()}
    names=('both-zero','aliases','left-zero','right-zero','max-zero','three-two','two-three','raw','raw-reversed','guard23-below-odd','guard24-above-even','delta-128-below','delta-128-equal','delta127-below','delta127-equal','both-negative')
    for op in (0x87,0x8b):
        for n in names:
            c=BASE_CASES[n];result[f'op{op:02x}-{n}']=dict(op=op,**c,fac='5aa5d592' if op==0x87 else c['right'])
    for index,fac in enumerate(('00000000','12345600','01008001','ffffffff')):
        for n in ('aliases','left-zero','delta-128-below','delta127-equal'):
            result[f'fac{index}-{n}']=dict(op=0x87,**dict(BASE_CASES[n],initial=16777215),fac=fac)
    return result

CASES=expected_cases()
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload(case):
    def assign(at,raw):return b''.join(bytes.fromhex('c706')+struct.pack('<HH',at+2*i,word) for i,word in enumerate(struct.unpack('<HH',raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    prefix=assign(0x1856,b'DIV1')+output(0x1856,4)+output(0x234,4)
    inputs=assign(0x1a,bytes.fromhex(case['fac']))+output(0x1a,4)+assign(0x1860,bytes.fromhex(case['left']))+output(0x1860,4)+assign(0x1864,bytes.fromhex(case['right']))+output(0x1864,4)+output(0x1f,1)
    call=bytes.fromhex('be6018')+(bytes.fromhex('bf6418') if case['op'] in (0x87,0x89) else b'')+bytes([0xcd,0x3f,case['op'],0x90,0x90])
    suffix=output(0x1a,4)+output(0x1860,4)+output(0x1864,4)+output(0x234,4)+output(0x1f,1)+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')
    return prefix+inputs+call+suffix


def expected_entry(left,right,fac):
    from fractions import Fraction
    from verify_single_add import decode
    if not right[3]:return 'division_by_zero'
    if not left[3]:return fac[:3]+b'\x00'
    value=decode(left)/decode(right)
    if abs(value)<Fraction(2)**-128:return fac[:3]+b'\x00' # Native pre-round underflow.
    negative=value<0;value=abs(value)
    power=value.numerator.bit_length()-value.denominator.bit_length()
    if value<Fraction(2)**power:power-=1
    exponent=power+129
    if exponent>255:return 'overflow'
    scaled=value*Fraction(2)**(23-power);mantissa,rest=divmod(scaled.numerator,scaled.denominator)
    if rest*2>scaled.denominator or(rest*2==scaled.denominator and mantissa%2):mantissa+=1
    if mantissa==1<<24:mantissa>>=1;exponent+=1
    if exponent>255:return 'overflow'
    bits=(mantissa&0x7fffff)|(0x800000 if negative else 0)
    return bits.to_bytes(3,'little')+bytes([exponent])


def error_address(case):
    stub=expected_payload(case);call=bytes([0xcd,0x3f,case['op'],0x90,0x90])
    assert stub.count(call)==1,'unique direct diagnostic call site'
    # Direct dispatch saves the continuation after the five-byte call slot.
    return f'{0x6d+stub.index(call)+len(call):04X}'


def verify_trace(trace,case):
    left=bytes.fromhex(case['left']);right=bytes.fromhex(case['right']);fac=bytes.fromhex(case['fac'])
    assert case['op'] in (0x87,0x89,0x8b),'only qualified direct entry forms'
    if case['op']==0x8b:assert fac==right,'entry8b right operand is the initial FAC, not the memory shadow'
    if case['op']==0x89:assert fac==left,'entry89 left operand is the initial FAC, not the memory shadow'
    prefix=b'DIV1'+struct.pack('<I',case['initial'])+fac+left+right+b'\x00'
    assert trace[:21]==prefix,'exact initial FAC, ordered operands, RNG and mode'
    want=expected_entry(left,right,fac)
    if isinstance(want,str):
        address=error_address(case)
        message=('\r\n'+dict(overflow='Overflow',division_by_zero='Division by zero')[want]+' in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace==prefix+message,'exact entry-specific native error without fabricated state'
    else:
        assert len(trace)==42 and trace[-4:]==b'END!','complete entry-state return frame'
        assert trace[21:25]==want,'exact result and prior-FAC residue'
        assert trace[25:29]==left and trace[29:33]==right,'both memory blocks preserved (left/right shadows for entry89/8b respectively)'
        assert trace[33:37]==struct.pack('<I',case['initial']) and trace[37]==0,'unrelated RNG and mode preserved'
    return want


def verify_static(runtime):
    from verify_single_multiply import verify_static as verify_shared
    from verify_inline_overflow import verify_static as verify_errors
    from verify_rng_native import image
    verify_shared(runtime)
    verify_errors(runtime)
    code=image(runtime)
    raw=(ROOT/'research/yt-xannor-planets/rea/assault-paths.json').read_bytes()
    assert SHA(raw)=='4fc6d6c55c2c18fe43c4e9ca459bf53af571a8237f23d6fa897fe114f46f232b'
    rows=[e for e in json.loads(raw)['records'] if e['subject']['name']=='BRUN30.EXE' and e['normalized_result'].get('address')=='0x1b520'];assert len(rows)==1
    e=rows[0];n=e['normalized_result'];assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA
    assert n['complete'] is True and n['requested_bytes']==n['returned_bytes']==48 and bytes.fromhex(n['bytes_hex'])==code[0xb520:0xb550]
    raw=(ROOT/'research/yt-mbf-divide/rea/divide-tail.json').read_bytes();assert SHA(raw)=='2141dff0ba77a4e001ea531cf23011edcb11707311710895d3ec39e77c4dce47'
    p=json.loads(raw);assert p['ok'] is True;e=p['data'];n=e['normalized_result']
    assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA and e['parameters']==dict(address='0x1b550',length=91)
    assert n['address']=='0x1b550' and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==91 and bytes.fromhex(n['bytes_hex'])==code[0xb550:0xb5ab]
    raw=(ROOT/'research/yt-mbf-divide/rea/division-error.json').read_bytes();assert SHA(raw)=='f2c9d1ea9899d9d34f6de777fcce99f42db9f5825071474ae18b4d50987ad0e0'
    p=json.loads(raw);assert p['ok'] is True;e=p['data'];n=e['normalized_result']
    assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA and e['parameters']==dict(address='0x135f8',length=18)
    assert n['address']=='0x135f8' and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==18 and bytes.fromhex(n['bytes_hex'])==code[0x35f8:0x360a]
    assert [struct.unpack_from('<H',runtime,0x58d+2*op)[0]for op in (0x87,0x89,0x8b)]==[0xb52b,0xb520,0xb528]
    assert code[0xb520:0xb52e]==bytes.fromhex('be1a00eb06e89b69bf1a00e83d6a'),'direct register/FAC mappings'
    assert code[0xb52e:0xb53c]==bytes.fromhex('8b4d028b44020aed74430ae474a8'),'divisor zero wins before numerator zero'
    assert code[0xb57b:0xb57e]==bytes.fromhex('e92e54') and code[0x9ac:0x9ae]==bytes.fromhex('b30b'),'error code11'
    assert code[0x35f8:0x360a]==b'\x0bDivision by zero\x00'
    verify_inventory()

def verify_inventory():
    import re
    raw=(ROOT/'research/yt-mbf-divide/maintenance-calls.json').read_bytes();assert SHA(raw)=='4fdb46ef2bb259734ba0b3874ca141c5ec06c813a314380b5ab0ddf325079e3a'
    d=json.loads(raw);r=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();listing=(ROOT/'archive/analysis/yt-maint/qb-annotated.txt').read_bytes()
    assert d['format']=='maintenance-direct-single-divide-callers-v1' and d['authority']=='Static annotated call-site inventory matched to archived bytes; not observed execution or exhaustive indirect coverage.'
    assert SHA(r)==d['original_sha256']=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6' and SHA(listing)==d['listing_sha256']=='097f46fd3f0e70743b9b89b56c8f5efd13f2bc2b6faf081aae4bb1b0583004c2'
    calls=[];inline=[]
    for address,op in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_(87|89|8b)\s*\n',listing.decode()):
        off=int(address,16);v=int(op,16);assert r[512+off:512+off+5]==bytes([0xcd,0x3f,v,0x90,0x90]);calls.append(dict(op=v,code_offset=off,file_offset=512+off))
    for address,selector in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_8d[^\n]*\n\s+INLINE ([0-9a-fA-F]{2})\s*\n',listing.decode()):
        off=int(address,16);v=int(selector,16);assert r[512+off:512+off+6]==bytes.fromhex('cd3f8d9090')+bytes([v]);inline.append(dict(code_offset=off,file_offset=512+off,selector=v))
    assert calls==d['direct_calls'] and inline==d['excluded_inline_calls'] and len(calls)==24 and len(inline)==0
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
        portable.append(dict(name=name,**case,output=want.hex() if isinstance(want,bytes) else None,error=want if isinstance(want,str) else None,trace_hex=trace.hex(),source_trace_sha256=SHA(trace)))
    return portable


def verify(directory=DEFAULT,fixture=FIXTURE):
    portable=verify_corpus(directory,CASES,PINS_SHA,'brun30-divide-entry-state-v1','recover_single_divide.py')
    doc=dict(format='qb-native-divide-single-v1',cases=portable)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==doc,'portable fixture equals complete native corpus'
    return doc

if __name__=='__main__':
    d=verify();print('Verified',len(d['cases']),'division controls:',{k:sum(c['error']==k for c in d['cases']) for k in (None,'overflow','division_by_zero')})
