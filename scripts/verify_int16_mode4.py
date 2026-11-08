"""Independent explicit-mode-4 signed16 audit for both MBF input precisions."""
import hashlib, json, shlex, struct
from fractions import Fraction
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-int16-mode4/native'
PRECISION=ROOT/'research/yt-mbf-int16-mode4/precision-native'
PRECISION_PINS_SHA='59ecd61345bd813b96fbcaedcc4a5228c64580bdb990b9aca2b7a4e63bcb77fb'
PRECISION_RAWS=['ffffffffffff7f80','ffffffffffffff80','0100000000000081','0100000000008081','ffffffffffff7f81','ffffffffffffff81','0100000000000082','0100000000008082','ffffffffffff7f8f','ffffffffffffff8f','0100000000000090','0100000000008090']
PRECISION_CASES={f'precision-double-op{op:02x}-{i:02d}':dict(kind='double',op=op,raw=raw,initial=16777215) for op in (0x76,0x78) for i,raw in enumerate(PRECISION_RAWS)}
FIXTURE=ROOT/'internal/qbmbf/testdata/native_int16_mode4.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='d80aa5edafb813dd75bbf9425e1fac168beac27bde3e190d1f35d4172a2fa1a5'
RAWS={'single': ['00000000', '0000007f', '0000807f', 'ffff7f7f', 'ffffff7f', '00000080', '00008080', '01000080', '01008080', '00004080', '0000c080', '00000081', '00008081', '00004081', '0000c081', 'ffff1f82', 'ffff9f82', '00002082', '0000a082', '01002082', '0100a082', '00006082', '0000e082', '00fe7f8f', '00feff8f', '80fe7f8f', '80feff8f', 'fffe7f8f', 'fffeff8f', '00ff7f8f', '00ffff8f', '01ff7f8f', '01ffff8f', '00000090', '00008090', '80000090', '80008090', '81000090', '81008090', '00010090', '00018090', '00000091', '00008091', 'ffff7f00', 'ffffff00', '12345600', 'ffff7fff', 'ffffffff'], 'double': ['0000000000000000', '000000000000007f', '000000000000807f', 'ffffffffffff7f7f', 'ffffffffffffff7f', '0000000000000080', '0000000000008080', '0100000000000080', '0100000000008080', '0000000000004080', '000000000000c080', '0000000000000081', '0000000000008081', '0000000000004081', '000000000000c081', 'ffffffffffff1f82', 'ffffffffffff9f82', '0000000000002082', '000000000000a082', '0100000000002082', '010000000000a082', '0000000000006082', '000000000000e082', '0000000000fe7f8f', '0000000000feff8f', '0000000080fe7f8f', '0000000080feff8f', 'fffffffffffe7f8f', 'fffffffffffeff8f', '0000000000ff7f8f', '0000000000ffff8f', '0100000000ff7f8f', '0100000000ffff8f', '0000000000000090', '0000000000008090', '0000000040000090', '0000000040008090', 'ffffffff7f000090', 'ffffffff7f008090', '0000000080000090', '0000000080008090', '0100000080000090', '0100000080008090', '0000000000010090', '0000000000018090', '0000000000000091', '0000000000008091', 'ffffffffffff7f00', 'ffffffffffffff00', '123456789abcde00', 'ffffffffffff7fff', 'ffffffffffffffff']}
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}
CASES={f'{kind}-op{op:02x}-{i:02d}':dict(kind=kind,op=op,raw=raw,initial=5)
       for kind,ops in [('single',(0x75,0x77)),('double',(0x76,0x78))]
       for op in ops for i,raw in enumerate(RAWS[kind])}


def expected_payload(case):
    def assign(at,raw):
        return b''.join(b'\xc7\x06'+struct.pack('<HH',at+2*i,word) for i,word in enumerate(struct.unpack('<'+'H'*(len(raw)//2),raw)))
    def output(at,size): return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    raw=bytes.fromhex(case['raw']); single=case['kind']=='single'; at=0x1a if single else 0x16
    prefix=assign(0x1856,b'M4S!' if single else b'M4D!')+output(0x1856,4)+output(0x234,4)+assign(at,raw)+output(at,len(raw))+output(0x1f,1)
    setting=bytes.fromhex('c6061f0004')+output(0x1f,1)
    call=(b'\xbe'+struct.pack('<H',at) if case['op'] in (0x75,0x76) else b'')+bytes([0xcd,0x3f,case['op'],0x90,0x90])
    suffix=bytes.fromhex('891e5c18')+output(0x185c,2)+output(at,len(raw))+output(0x234,4)+output(0x1f,1)+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')
    return prefix+setting+call+suffix


def expected_integer(raw):
    if not raw[-1]: return 0
    precision=(len(raw)-1)*8; hidden=1<<(precision-1)
    mantissa=(int.from_bytes(raw[:-1],'little')&(hidden-1))|hidden
    value=mantissa*Fraction(2)**(raw[-1]-128-precision)
    if raw[-2]&128: value=-value
    integer=value.numerator//value.denominator
    return integer if -32768<=integer<=32767 else None


def verify_trace(trace,case):
    raw=bytes.fromhex(case['raw']); single=case['kind']=='single'; size=len(raw)
    prefix=(b'M4S!' if single else b'M4D!')+struct.pack('<I',case['initial'])+raw+b'\x00\x04'
    at=len(prefix); assert trace[:at]==prefix,'exact input/RNG, original mode zero and explicit applied mode four'
    want=expected_integer(raw)
    if want is None:
        address={0x75:'00D3',0x77:'00D0',0x76:'00DF',0x78:'00DC'}[case['op']]
        message=('\r\nOverflow in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace==prefix+message,'complete native mode-4 overflow without fabricated result'
    else:
        assert len(trace)==2*size+21 and trace[-4:]==b'END!','complete mode-4 return framing'
        assert struct.unpack('<h',trace[at:at+2])[0]==want,'exact signed16 native floor result'
        result=struct.pack('<h',want)
        fac=result+raw[2:] if single else raw[:4]+result+raw[6:]
        assert trace[at+2:at+2+size]==fac,'exact FAC result word and unaffected bytes'
        assert trace[at+2+size:at+6+size]==struct.pack('<I',case['initial']) and trace[at+6+size]==4,'RNG and applied mode preserved on return'
    return want


def verify_static(runtime):
    from verify_int16_double import verify_static as verify_existing_dispatch_kernel_and_helper
    verify_existing_dispatch_kernel_and_helper(runtime)
    # Complete original mode-selected floor/overflow branches are already in
    # the authenticated shared-kernel observation; no new static read is needed.
    assert runtime[0xab3b:0xab42]==bytes.fromhex('803e1f000474ae'),'mode four selects the original separate branch'


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
        copied=bytearray(runtime); struct.pack_into('<I',copied,0x10234,case['initial'])
        assert set(meta)=={'recipe','case','kind','op','raw','initial','exit_code','timeout','missing','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'fixed result schema'
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
    return portable


def verify(directory=DEFAULT,fixture=FIXTURE,precision_directory=PRECISION):
    portable=verify_corpus(directory,CASES,PINS_SHA,'brun30-int16-mode4-v1','recover_int16_mode4.py')
    portable+=verify_corpus(precision_directory,PRECISION_CASES,PRECISION_PINS_SHA,'brun30-int16-mode4-precision-v1','recover_int16_mode4_precision.py')
    document=dict(format='qb-native-int16-mode4-v1',cases=portable)
    if fixture is not None: assert json.loads(Path(fixture).read_text())==document,'portable fixture equals both complete native corpora'
    return document

if __name__=='__main__':
    doc=verify(); print('Verified',len(doc['cases']),'mode-4 native conversions,',sum(c['value'] is None for c in doc['cases']),'native overflow outcomes')
