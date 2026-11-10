"""Independent subtraction entry-state, prior-FAC and provenance audit."""
import hashlib, json, shlex, struct
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-sub/native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_sub_entries.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='9e2d8e12e93da3a41bf44872cfe201fd2d2d061ca9c2d65f6da92aca4886a6fe'
BASE_CASES={
  "both-zero": {
    "left": "00000000",
    "right": "00000000",
    "initial": 5
  },
  "zero-aliases": {
    "left": "12345600",
    "right": "ffffff00",
    "initial": 5
  },
  "reverse-zero-aliases": {
    "left": "ffffff00",
    "right": "12345600",
    "initial": 5
  },
  "left-zero-alias": {
    "left": "12345600",
    "right": "00000081",
    "initial": 5
  },
  "right-zero-alias": {
    "left": "00000081",
    "right": "ffffff00",
    "initial": 5
  },
  "negative-plus-zero": {
    "left": "00008081",
    "right": "12345600",
    "initial": 5
  },
  "zero-plus-negative": {
    "left": "ffffff00",
    "right": "00008081",
    "initial": 5
  },
  "min-plus-zero": {
    "left": "00000001",
    "right": "ffffff00",
    "initial": 5
  },
  "one-plus-one": {
    "left": "00000081",
    "right": "00000081",
    "initial": 5
  },
  "negative-one-plus-one": {
    "left": "00008081",
    "right": "00000081",
    "initial": 5
  },
  "one-plus-negative-one": {
    "left": "00000081",
    "right": "00008081",
    "initial": 5
  },
  "negative-one-pair": {
    "left": "00008081",
    "right": "00008081",
    "initial": 5
  },
  "fraction-cancel": {
    "left": "00004081",
    "right": "0000c081",
    "initial": 5
  },
  "reverse-fraction-cancel": {
    "left": "0000c081",
    "right": "00004081",
    "initial": 5
  },
  "positive-sign-cross": {
    "left": "0000c081",
    "right": "00000082",
    "initial": 5
  },
  "negative-sign-cross": {
    "left": "00004081",
    "right": "00008082",
    "initial": 5
  },
  "same-exponent-difference": {
    "left": "00006081",
    "right": "0000c081",
    "initial": 5
  },
  "reverse-exponent-difference": {
    "left": "0000c081",
    "right": "00006081",
    "initial": 5
  },
  "integer-carry": {
    "left": "ffff7f98",
    "right": "00000081",
    "initial": 5
  },
  "negative-integer-carry": {
    "left": "ffffff98",
    "right": "00008081",
    "initial": 5
  },
  "small-lsb-odd": {
    "left": "01000098",
    "right": "00000080",
    "initial": 5
  },
  "negative-small-lsb-odd": {
    "left": "01008098",
    "right": "00008080",
    "initial": 5
  },
  "raw-align-positive": {
    "left": "56341291",
    "right": "ac681380",
    "initial": 5
  },
  "raw-align-negative": {
    "left": "56349291",
    "right": "ac689380",
    "initial": 5
  },
  "raw-align-sign-cross": {
    "left": "56341291",
    "right": "ac689380",
    "initial": 5
  },
  "raw-align-reversed": {
    "left": "ac689380",
    "right": "56341291",
    "initial": 5
  },
  "minimum-cancel": {
    "left": "00000001",
    "right": "00008001",
    "initial": 5
  },
  "minimum-one-bit": {
    "left": "01000001",
    "right": "00008001",
    "initial": 5
  },
  "minimum-negative-bit": {
    "left": "00000001",
    "right": "01008001",
    "initial": 5
  },
  "negative-minimum-one-bit": {
    "left": "01008001",
    "right": "00000001",
    "initial": 5
  },
  "minimum-near-binade": {
    "left": "00000002",
    "right": "ffffff01",
    "initial": 5
  },
  "minimum-near-binade-reverse": {
    "left": "ffffff01",
    "right": "00000002",
    "initial": 5
  },
  "max-pair": {
    "left": "ffff7fff",
    "right": "ffff7fff",
    "initial": 5
  },
  "negative-max-pair": {
    "left": "ffffffff",
    "right": "ffffffff",
    "initial": 5
  },
  "max-cancel": {
    "left": "ffff7fff",
    "right": "ffffffff",
    "initial": 5
  },
  "negative-max-cancel": {
    "left": "ffffffff",
    "right": "ffff7fff",
    "initial": 5
  },
  "max-ulp-difference": {
    "left": "ffff7fff",
    "right": "feffffff",
    "initial": 5
  },
  "reverse-max-ulp-difference": {
    "left": "feffffff",
    "right": "ffff7fff",
    "initial": 5
  },
  "max-with-min": {
    "left": "ffff7fff",
    "right": "00000001",
    "initial": 5
  },
  "min-with-max": {
    "left": "00000001",
    "right": "ffff7fff",
    "initial": 5
  },
  "max-round-overflow": {
    "left": "ffff7fff",
    "right": "000000e7",
    "initial": 5
  },
  "negative-max-round-overflow": {
    "left": "ffffffff",
    "right": "000080e7",
    "initial": 5
  },
  "max-below-round": {
    "left": "ffff7fff",
    "right": "ffff7fe6",
    "initial": 5
  },
  "max-negative-tiny": {
    "left": "ffff7fff",
    "right": "000080e7",
    "initial": 5
  },
  "positive-lsb0-below": {
    "left": "00000081",
    "right": "ffff7f68",
    "initial": 5
  },
  "positive-lsb0-tie": {
    "left": "00000081",
    "right": "00000069",
    "initial": 5
  },
  "positive-lsb0-above": {
    "left": "00000081",
    "right": "01000069",
    "initial": 5
  },
  "positive-lsb1-below": {
    "left": "01000081",
    "right": "ffff7f68",
    "initial": 5
  },
  "positive-lsb1-tie": {
    "left": "01000081",
    "right": "00000069",
    "initial": 5
  },
  "positive-lsb1-above": {
    "left": "01000081",
    "right": "01000069",
    "initial": 5
  },
  "positive-gap23-add": {
    "left": "00000081",
    "right": "0000406a",
    "initial": 5
  },
  "positive-gap23-subtract": {
    "left": "00000081",
    "right": "0000c06a",
    "initial": 5
  },
  "positive-gap23-reversed": {
    "left": "0000c06a",
    "right": "00000081",
    "initial": 5
  },
  "positive-gap24-add": {
    "left": "00000081",
    "right": "00004069",
    "initial": 5
  },
  "positive-gap24-subtract": {
    "left": "00000081",
    "right": "0000c069",
    "initial": 5
  },
  "positive-gap24-reversed": {
    "left": "0000c069",
    "right": "00000081",
    "initial": 5
  },
  "positive-gap25-add": {
    "left": "00000081",
    "right": "00004068",
    "initial": 5
  },
  "positive-gap25-subtract": {
    "left": "00000081",
    "right": "0000c068",
    "initial": 5
  },
  "positive-gap25-reversed": {
    "left": "0000c068",
    "right": "00000081",
    "initial": 5
  },
  "positive-gap26-add": {
    "left": "00000081",
    "right": "00004067",
    "initial": 5
  },
  "positive-gap26-subtract": {
    "left": "00000081",
    "right": "0000c067",
    "initial": 5
  },
  "positive-gap26-reversed": {
    "left": "0000c067",
    "right": "00000081",
    "initial": 5
  },
  "negative-lsb0-below": {
    "left": "00008081",
    "right": "ffffff68",
    "initial": 5
  },
  "negative-lsb0-tie": {
    "left": "00008081",
    "right": "00008069",
    "initial": 5
  },
  "negative-lsb0-above": {
    "left": "00008081",
    "right": "01008069",
    "initial": 5
  },
  "negative-lsb1-below": {
    "left": "01008081",
    "right": "ffffff68",
    "initial": 5
  },
  "negative-lsb1-tie": {
    "left": "01008081",
    "right": "00008069",
    "initial": 5
  },
  "negative-lsb1-above": {
    "left": "01008081",
    "right": "01008069",
    "initial": 5
  },
  "negative-gap23-add": {
    "left": "00008081",
    "right": "0000c06a",
    "initial": 5
  },
  "negative-gap23-subtract": {
    "left": "00008081",
    "right": "0000406a",
    "initial": 5
  },
  "negative-gap23-reversed": {
    "left": "0000406a",
    "right": "00008081",
    "initial": 5
  },
  "negative-gap24-add": {
    "left": "00008081",
    "right": "0000c069",
    "initial": 5
  },
  "negative-gap24-subtract": {
    "left": "00008081",
    "right": "00004069",
    "initial": 5
  },
  "negative-gap24-reversed": {
    "left": "00004069",
    "right": "00008081",
    "initial": 5
  },
  "negative-gap25-add": {
    "left": "00008081",
    "right": "0000c068",
    "initial": 5
  },
  "negative-gap25-subtract": {
    "left": "00008081",
    "right": "00004068",
    "initial": 5
  },
  "negative-gap25-reversed": {
    "left": "00004068",
    "right": "00008081",
    "initial": 5
  },
  "negative-gap26-add": {
    "left": "00008081",
    "right": "0000c067",
    "initial": 5
  },
  "negative-gap26-subtract": {
    "left": "00008081",
    "right": "00004067",
    "initial": 5
  },
  "negative-gap26-reversed": {
    "left": "00004067",
    "right": "00008081",
    "initial": 5
  },
  "max-rng-cancel": {
    "left": "00006081",
    "right": "0000e081",
    "initial": 16777215
  },
  "max-rng-sticky": {
    "left": "00000081",
    "right": "0000c068",
    "initial": 16777215
  }
}
CASES={f'op{op:02x}-{name}':dict(op=op,**c,fac='5aa5d592' if op==0x97 else c['left'] if op==0x99 else c['right']) for op in (0x97,0x99,0x9b) for name,c in BASE_CASES.items()}
for _index,_fac in enumerate(('00000000','12345600','01008001','ffffffff')):
    for _name,(_left,_right) in {'both-zero':('00000000','00000000'),'aliases':('12345600','ffffff00'),'cancel':('00004081','00004081'),'underflow':('01000001','00000001'),'reverse-underflow':('00000001','01000001')}.items():
        CASES[f'fac{_index}-{_name}']=dict(op=0x97,left=_left,right=_right,initial=16777215,fac=_fac)


FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload(case):
    def assign(at,raw):return b''.join(bytes.fromhex('c706')+struct.pack('<HH',at+2*i,word) for i,word in enumerate(struct.unpack('<HH',raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    prefix=assign(0x1856,b'SUB1')+output(0x1856,4)+output(0x234,4)
    inputs=assign(0x1a,bytes.fromhex(case['fac']))+output(0x1a,4)+assign(0x1860,bytes.fromhex(case['left']))+output(0x1860,4)+assign(0x1864,bytes.fromhex(case['right']))+output(0x1864,4)+output(0x1f,1)
    call=bytes.fromhex('be6018')+(bytes.fromhex('bf6418') if case['op'] in (0x97,0x99) else b'')+bytes([0xcd,0x3f,case['op'],0x90,0x90])
    suffix=output(0x1a,4)+output(0x1860,4)+output(0x1864,4)+output(0x234,4)+output(0x1f,1)+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')
    return prefix+inputs+call+suffix


def expected_entry(left,right,fac):
    # The subtraction wrapper flips the right sign in AX, including exponent-zero aliases.
    # No memory/FAC input is mutated. Arithmetic remains the qualified addition model.
    from verify_single_add_entries import expected_entry as add_entry
    negated=right[:2]+bytes([right[2]^128])+right[3:]
    return add_entry(left,negated,fac)


def verify_trace(trace,case):
    left=bytes.fromhex(case['left']);right=bytes.fromhex(case['right']);fac=bytes.fromhex(case['fac'])
    assert case['op'] in (0x97,0x99,0x9b),'only qualified direct entry forms'
    if case['op']==0x9b:assert fac==right,'entry9b right operand is the initial FAC, not the memory shadow'
    if case['op']==0x99:assert fac==left,'entry99 left operand is the initial FAC, not the memory shadow'
    prefix=b'SUB1'+struct.pack('<I',case['initial'])+fac+left+right+b'\x00'
    assert trace[:21]==prefix,'exact initial FAC, ordered operands, RNG and mode'
    want=expected_entry(left,right,fac)
    if want is None:
        address='00F6' if case['op'] in (0x97,0x99) else '00F3'
        message=('\r\nOverflow in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace==prefix+message,'exact entry-specific native overflow without fabricated state'
    else:
        assert len(trace)==42 and trace[-4:]==b'END!','complete entry-state return frame'
        assert trace[21:25]==want,'exact result and prior-FAC residue'
        assert trace[25:29]==left and trace[29:33]==right,'both memory blocks preserved (left/right shadows for entry99/9b respectively)'
        assert trace[33:37]==struct.pack('<I',case['initial']) and trace[37]==0,'unrelated RNG and mode preserved'
    return want


def verify_static(runtime):
    from verify_single_add_entries import verify_static as verify_shared
    from verify_rng_native import image
    verify_shared(runtime)
    raw=(ROOT/'research/yt-xannor-planets/rea/assault-paths.json').read_bytes()
    assert SHA(raw)=='4fc6d6c55c2c18fe43c4e9ca459bf53af571a8237f23d6fa897fe114f46f232b','immutable retained wrapper packet'
    rows=json.loads(raw)['records']
    for address,size in (('0x1038d',396),('0x1b354',96),('0x11f6b',128)):
        found=[e for e in rows if e['subject']['name']=='BRUN30.EXE' and e['normalized_result'].get('address')==address];assert len(found)==1
        e=found[0];n=e['normalized_result'];assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA and n['complete'] is True and n['returned_bytes']==n['requested_bytes']==size
        at=int(address,16)-0x10000;assert bytes.fromhex(n['bytes_hex'])==image(runtime)[at:at+size]
    assert [struct.unpack_from('<H',runtime,0x58d+2*op)[0] for op in (0x97,0x99,0x9b)]==[0xb35f,0xb354,0xb35c],'direct subtraction dispatch'
    assert runtime[0xb554:0xb569]==bytes.fromhex('be1a00eb06e8676bbf1a00e8096c8b45023480eb11'),'right sign flipped in register before joining addition b37a'
    verify_inventory()


def verify_inventory():
    import re
    raw=(ROOT/'research/yt-mbf-sub/maintenance-calls.json').read_bytes()
    assert SHA(raw)=='cdf310d4924ebd3fac189f5d69fe9585ddf4ca11d2355eb5a65fb9082d8bc632','fixed original caller inventory'
    d=json.loads(raw);original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();listing=(ROOT/'archive/analysis/yt-maint/qb-annotated.txt').read_bytes()
    assert d['format']=='maintenance-direct-single-subtract-callers-v1' and d['authority']=='Static annotated direct-call inventory matched to archived bytes; not observed execution or exhaustive indirect coverage.'
    assert SHA(original)==d['original_sha256']=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
    assert SHA(listing)==d['listing_sha256']=='097f46fd3f0e70743b9b89b56c8f5efd13f2bc2b6faf081aae4bb1b0583004c2'
    calls=[]
    for address,op in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_(97|99|9b)\s*\n',listing.decode()):
        off=int(address,16);opcode=int(op,16);assert original[512+off:512+off+5]==bytes([0xcd,0x3f,opcode,0x90,0x90]);calls.append(dict(code_offset=off,file_offset=512+off,op=opcode))
    assert calls==d['calls'],'static direct callers match original code'
    return calls


def verify(directory=DEFAULT,fixture=FIXTURE):
    root=Path(directory); manifest=(root/'pins.json').read_bytes(); assert SHA(manifest)==PINS_SHA,'fixed native manifest'
    pins=json.loads(manifest)['files']
    assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}==set(pins),'complete artifact inventory'
    for name,digest in pins.items(): assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert (SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original executable identity'
    verify_static(runtime)
    source=root/'sources/recover_single_sub.py'; recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe='brun30-sub-entry-state-v1',cases=CASES,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'frozen prelaunch acquisition source and recipe'
    assert {p.name for p in root.iterdir()}==set(CASES)|{'pins.json','recipe.json','sources'} and {p.name for p in source.parent.iterdir()}=={source.name},'fixed case/source coverage'
    portable=[]
    for name,case in CASES.items():
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
    document=dict(format='qb-native-sub-entry-state-v1',cases=portable)
    if fixture is not None: assert json.loads(Path(fixture).read_text())==document,'portable fixture equals whole native corpus'
    return document

if __name__=='__main__':
    doc=verify(); print('Verified',len(doc['cases']),'native subtraction entry-state controls,',sum(c['output'] is None for c in doc['cases']),'native overflow outcomes')
