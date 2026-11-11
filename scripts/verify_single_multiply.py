"""Independent multiplication entry-state, prior-FAC and provenance audit."""
import hashlib, json, shlex, struct
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-multiply/native'
STICKY_DEFAULT=ROOT/'research/yt-mbf-multiply/sticky-native'
STICKY_PINS_SHA='59a7bd67f377c2fe71e12d1166e04cd2272ba1f2717311c92d08a52c0fe69009'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_multiply_single.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='a9dd854bc44795cc7430e80087f0faeeaa7b74c682af10a21e77bc127003a108'
BASE_CASES={
  "both-zero": {
    "left": "00000000",
    "right": "00000000",
    "initial": 5
  },
  "aliases": {
    "left": "12345600",
    "right": "ffffff00",
    "initial": 5
  },
  "left-zero": {
    "left": "12345600",
    "right": "00008081",
    "initial": 5
  },
  "right-zero": {
    "left": "00004081",
    "right": "ffffff00",
    "initial": 5
  },
  "max-zero": {
    "left": "ffff7fff",
    "right": "12345600",
    "initial": 5
  },
  "zero-max": {
    "left": "ffffff00",
    "right": "ffffffff",
    "initial": 5
  },
  "one": {
    "left": "00000081",
    "right": "00000081",
    "initial": 5
  },
  "one-negative": {
    "left": "00008081",
    "right": "00000081",
    "initial": 5
  },
  "fraction": {
    "left": "00004081",
    "right": "00004081",
    "initial": 5
  },
  "fraction-negative": {
    "left": "0000c081",
    "right": "00004081",
    "initial": 5
  },
  "raw-align": {
    "left": "56341281",
    "right": "ac681381",
    "initial": 5
  },
  "raw-align-negative": {
    "left": "56349281",
    "right": "ac681381",
    "initial": 5
  },
  "tie47-odd": {
    "left": "00004081",
    "right": "01000081",
    "initial": 5
  },
  "tie47-odd-negative": {
    "left": "0000c081",
    "right": "01000081",
    "initial": 5
  },
  "tie47-even": {
    "left": "00004081",
    "right": "03000081",
    "initial": 5
  },
  "tie47-even-negative": {
    "left": "0000c081",
    "right": "03000081",
    "initial": 5
  },
  "below47": {
    "left": "ffff3f81",
    "right": "01000081",
    "initial": 5
  },
  "below47-negative": {
    "left": "ffffbf81",
    "right": "01000081",
    "initial": 5
  },
  "above47": {
    "left": "01004081",
    "right": "01000081",
    "initial": 5
  },
  "above47-negative": {
    "left": "0100c081",
    "right": "01000081",
    "initial": 5
  },
  "tie48-odd": {
    "left": "00004081",
    "right": "02004081",
    "initial": 5
  },
  "tie48-odd-negative": {
    "left": "0000c081",
    "right": "02004081",
    "initial": 5
  },
  "tie48-even": {
    "left": "00004081",
    "right": "06004081",
    "initial": 5
  },
  "tie48-even-negative": {
    "left": "0000c081",
    "right": "06004081",
    "initial": 5
  },
  "below48": {
    "left": "ffff7f81",
    "right": "01000081",
    "initial": 5
  },
  "below48-negative": {
    "left": "ffffff81",
    "right": "01000081",
    "initial": 5
  },
  "above48": {
    "left": "01004081",
    "right": "01004081",
    "initial": 5
  },
  "above48-negative": {
    "left": "0100c081",
    "right": "01004081",
    "initial": 5
  },
  "round-carry": {
    "left": "01000081",
    "right": "feff7f81",
    "initial": 5
  },
  "round-carry-negative": {
    "left": "01008081",
    "right": "feff7f81",
    "initial": 5
  },
  "negative-right": {
    "left": "00004081",
    "right": "01008081",
    "initial": 5
  },
  "both-negative": {
    "left": "0000c081",
    "right": "0200c081",
    "initial": 5
  },
  "raw-reversed": {
    "left": "ac681381",
    "right": "56341281",
    "initial": 5
  },
  "ties-reversed": {
    "left": "03000081",
    "right": "00004081",
    "initial": 5
  },
  "million-half": {
    "left": "00247494",
    "right": "00000080",
    "initial": 5
  },
  "thousand-tenth": {
    "left": "00007a8a",
    "right": "cdcc4c7d",
    "initial": 5
  },
  "exp-sum128-800000": {
    "left": "00000040",
    "right": "00000040",
    "initial": 5
  },
  "exp-sum128-c00000": {
    "left": "00004040",
    "right": "00004040",
    "initial": 5
  },
  "exp-sum129-800000": {
    "left": "00000040",
    "right": "00000041",
    "initial": 5
  },
  "exp-sum129-c00000": {
    "left": "00004040",
    "right": "00004041",
    "initial": 5
  },
  "exp-sum130-800000": {
    "left": "00000041",
    "right": "00000041",
    "initial": 5
  },
  "exp-sum130-c00000": {
    "left": "00004041",
    "right": "00004041",
    "initial": 5
  },
  "exp-sum383-800000": {
    "left": "000000bf",
    "right": "000000c0",
    "initial": 5
  },
  "exp-sum383-c00000": {
    "left": "000040bf",
    "right": "000040c0",
    "initial": 5
  },
  "exp-sum384-800000": {
    "left": "000000c0",
    "right": "000000c0",
    "initial": 5
  },
  "exp-sum384-c00000": {
    "left": "000040c0",
    "right": "000040c0",
    "initial": 5
  },
  "exp-sum385-800000": {
    "left": "000000c0",
    "right": "000000c1",
    "initial": 5
  },
  "exp-sum385-c00000": {
    "left": "000040c0",
    "right": "000040c1",
    "initial": 5
  },
  "flush-before-round": {
    "left": "01000040",
    "right": "feff7f41",
    "initial": 5
  },
  "reverse-flush": {
    "left": "feff7f41",
    "right": "01000040",
    "initial": 5
  },
  "negative-flush": {
    "left": "01008040",
    "right": "feff7f41",
    "initial": 5
  },
  "round-overflow": {
    "left": "010000c0",
    "right": "feff7fc0",
    "initial": 5
  },
  "below-upper-range": {
    "left": "ffff7fbf",
    "right": "ffff7fc0",
    "initial": 5
  },
  "min-max": {
    "left": "00000001",
    "right": "ffff7fff",
    "initial": 5
  },
  "max-min": {
    "left": "ffff7fff",
    "right": "00000001",
    "initial": 5
  },
  "max-one": {
    "left": "ffff7fff",
    "right": "00000081",
    "initial": 5
  },
  "min-one": {
    "left": "00000001",
    "right": "00000081",
    "initial": 5
  },
  "min-half": {
    "left": "00000001",
    "right": "00000080",
    "initial": 5
  },
  "max-two": {
    "left": "ffff7fff",
    "right": "00000082",
    "initial": 5
  },
  "max-rng-tie": {
    "left": "00004081",
    "right": "01000081",
    "initial": 16777215
  },
  "max-rng-zero": {
    "left": "12345600",
    "right": "ffffff00",
    "initial": 16777215
  }
}
CASES={f'op91-{n}':dict(op=0x91,**c,fac=c['left']) for n,c in BASE_CASES.items()}
for _op in (0x8f,0x93):
    for _n in ('both-zero','aliases','left-zero','right-zero','max-zero','min-half','flush-before-round','negative-flush','exp-sum129-c00000','exp-sum128-c00000','fraction','tie47-odd','tie48-even','round-overflow','max-two','both-negative'):
        _c=BASE_CASES[_n];CASES[f'op{_op:02x}-{_n}']=dict(op=_op,**_c,fac='5aa5d592' if _op==0x8f else _c['right'])
for _i,_fac in enumerate(('00000000','12345600','01008001','ffffffff')):
    for _n in ('aliases','right-zero','flush-before-round','min-half'):
        CASES[f'fac{_i}-{_n}']=dict(op=0x8f,**dict(BASE_CASES[_n],initial=16777215),fac=_fac)

STICKY_CASES={}
for _n,_left,_right in (('guard47-below-odd','07000081','49926481'),('guard48-below-odd','5b200081','2df07f81'),('guard48-above-even','3d0c0081','15eb7f81')):
    for _neg in (False,True):
        _r=bytearray.fromhex(_left)
        if _neg:_r[2]^=128
        _v=_r.hex();STICKY_CASES[_n+('-negative' if _neg else '')]=dict(op=0x91,left=_v,right=_right,initial=16777215,fac=_v)

FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload(case):
    def assign(at,raw):return b''.join(bytes.fromhex('c706')+struct.pack('<HH',at+2*i,word) for i,word in enumerate(struct.unpack('<HH',raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    prefix=assign(0x1856,b'MUL1')+output(0x1856,4)+output(0x234,4)
    inputs=assign(0x1a,bytes.fromhex(case['fac']))+output(0x1a,4)+assign(0x1860,bytes.fromhex(case['left']))+output(0x1860,4)+assign(0x1864,bytes.fromhex(case['right']))+output(0x1864,4)+output(0x1f,1)
    call=bytes.fromhex('be6018')+(bytes.fromhex('bf6418') if case['op'] in (0x8f,0x91) else b'')+bytes([0xcd,0x3f,case['op'],0x90,0x90])
    suffix=output(0x1a,4)+output(0x1860,4)+output(0x1864,4)+output(0x234,4)+output(0x1f,1)+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')
    return prefix+inputs+call+suffix


def expected_entry(left,right,fac):
    from fractions import Fraction
    from verify_single_add import decode
    if not left[3] or not right[3]:return fac[:3]+b'\x00'
    value=decode(left)*decode(right)
    if abs(value)<Fraction(2)**-128:return fac[:3]+b'\x00' # Native pre-round underflow.
    negative=value<0;value=abs(value)
    power=value.numerator.bit_length()-value.denominator.bit_length()
    if value<Fraction(2)**power:power-=1
    exponent=power+129
    if exponent>255:return None
    scaled=value*Fraction(2)**(23-power);mantissa,rest=divmod(scaled.numerator,scaled.denominator)
    if rest*2>scaled.denominator or(rest*2==scaled.denominator and mantissa%2):mantissa+=1
    if mantissa==1<<24:mantissa>>=1;exponent+=1
    if exponent>255:return None
    bits=(mantissa&0x7fffff)|(0x800000 if negative else 0)
    return bits.to_bytes(3,'little')+bytes([exponent])


def verify_trace(trace,case):
    left=bytes.fromhex(case['left']);right=bytes.fromhex(case['right']);fac=bytes.fromhex(case['fac'])
    assert case['op'] in (0x8f,0x91,0x93),'only qualified direct entry forms'
    if case['op']==0x93:assert fac==right,'entry93 right operand is the initial FAC, not the memory shadow'
    if case['op']==0x91:assert fac==left,'entry91 left operand is the initial FAC, not the memory shadow'
    prefix=b'MUL1'+struct.pack('<I',case['initial'])+fac+left+right+b'\x00'
    assert trace[:21]==prefix,'exact initial FAC, ordered operands, RNG and mode'
    want=expected_entry(left,right,fac)
    if want is None:
        address='00F6' if case['op'] in (0x8f,0x91) else '00F3'
        message=('\r\nOverflow in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace==prefix+message,'exact entry-specific native overflow without fabricated state'
    else:
        assert len(trace)==42 and trace[-4:]==b'END!','complete entry-state return frame'
        assert trace[21:25]==want,'exact result and prior-FAC residue'
        assert trace[25:29]==left and trace[29:33]==right,'both memory blocks preserved (left/right shadows for entry91/93 respectively)'
        assert trace[33:37]==struct.pack('<I',case['initial']) and trace[37]==0,'unrelated RNG and mode preserved'
    return want


def verify_static(runtime):
    from verify_single_add_entries import verify_static as verify_shared
    from verify_rng_native import image
    verify_shared(runtime) # Existing zero exit, range errors, tie-even normalizer.
    raw=(ROOT/'research/yt-plague-civil-war/rea/target-paths.json').read_bytes()
    assert SHA(raw)=='4bfa563cefe57e531601268833452f5fb620573686daa5d249bcb7e9debe007a','immutable retained multiplication packet'
    rows=[o['evidence'] for o in json.loads(raw)['observations'] if o['name']=='runtime-multiply'];assert len(rows)==1
    e=rows[0];n=e['normalized_result'];assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA
    assert n['address']=='0x1b440' and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==220
    assert bytes.fromhex(n['bytes_hex'])==image(runtime)[0xb440:0xb51c]
    raw=(ROOT/'research/yt-xannor-planets/rea/assault-paths.json').read_bytes()
    assert SHA(raw)=='4fc6d6c55c2c18fe43c4e9ca459bf53af571a8237f23d6fa897fe114f46f232b'
    rows=[e for e in json.loads(raw)['records'] if e['subject']['name']=='BRUN30.EXE' and e['normalized_result'].get('address')=='0x11f6b'];assert len(rows)==1
    e=rows[0];n=e['normalized_result'];assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==128
    assert bytes.fromhex(n['bytes_hex'])==image(runtime)[0x1f6b:0x1feb]
    raw=(ROOT/'research/yt-mbf-multiply/rea/multiply-tail.json').read_bytes()
    assert SHA(raw)=='5178b6083c930cba5b60969d094862a566c35b272a7d18cf9224958d622521d9'
    p=json.loads(raw);assert p['ok'] is True;e=p['data'];n=e['normalized_result']
    assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA and e['parameters']==dict(address='0x1b51c',length=4)
    assert n['address']=='0x1b51c' and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==4 and bytes.fromhex(n['bytes_hex'])==image(runtime)[0xb51c:0xb520]
    assert [struct.unpack_from('<H',runtime,0x58d+2*op)[0]for op in (0x8f,0x91,0x93)]==[0xb4ab,0xb4a0,0xb4a8]
    assert runtime[0xb6a0:0xb6ae]==bytes.fromhex('be1a00eb06e81b6abf1a00e8bd6a'),'direct register/FAC entry mappings'
    assert runtime[0xb6b2:0xb6bd]==bytes.fromhex('0ae474e48b4d020aed74dd'),'either zero exponent branches to FAC exponent-only zero'
    assert runtime[0xb6dc:0xb6e6]==bytes.fromhex('d1e2d1d30ae47587ebb4'),'native underflow precedes rounding'
    verify_inventory()


def verify_inventory():
    import re
    raw=(ROOT/'research/yt-mbf-multiply/maintenance-calls.json').read_bytes();assert SHA(raw)=='aa5249a391bbb5f8b66f7db9cc89116c436c24c50b98875482e6298af897b06c'
    d=json.loads(raw);r=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();listing=(ROOT/'archive/analysis/yt-maint/qb-annotated.txt').read_bytes()
    assert d['format']=='maintenance-direct-single-multiply-callers-v1' and d['authority']=='Static annotated call-site inventory matched to archived bytes; not observed execution or exhaustive indirect coverage.'
    assert SHA(r)==d['original_sha256']=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6' and SHA(listing)==d['listing_sha256']=='097f46fd3f0e70743b9b89b56c8f5efd13f2bc2b6faf081aae4bb1b0583004c2'
    calls=[];inline=[]
    for address,op in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_(8f|91|93)\s*\n',listing.decode()):
        off=int(address,16);v=int(op,16);assert r[512+off:512+off+5]==bytes([0xcd,0x3f,v,0x90,0x90]);calls.append(dict(op=v,code_offset=off,file_offset=512+off))
    for address,selector in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_95[^\n]*\n\s+INLINE ([0-9a-fA-F]{2})\s*\n',listing.decode()):
        off=int(address,16);v=int(selector,16);assert r[512+off:512+off+6]==bytes.fromhex('cd3f959090')+bytes([v]);inline.append(dict(code_offset=off,file_offset=512+off,selector=v))
    assert calls==d['direct_calls'] and inline==d['excluded_inline_calls'] and len(calls)==60 and len(inline)==12
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


def verify(directory=DEFAULT,fixture=FIXTURE,sticky_directory=STICKY_DEFAULT):
    portable=verify_corpus(directory,CASES,PINS_SHA,'brun30-multiply-entry-state-v1','recover_single_multiply.py')
    portable+=verify_corpus(sticky_directory,STICKY_CASES,STICKY_PINS_SHA,'brun30-multiply-sticky-v1','recover_single_multiply_sticky.py')
    document=dict(format='qb-native-multiply-single-v1',cases=portable)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==document,'portable fixture equals both complete native corpora'
    return document

if __name__=='__main__':
    doc=verify(); print('Verified',len(doc['cases']),'native multiplication entry-state controls,',sum(c['output'] is None for c in doc['cases']),'native overflow outcomes')
