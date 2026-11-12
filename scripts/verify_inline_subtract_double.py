"""Authenticate eight-byte inline9e protocols without relabeling SINGLE evidence."""
import json,shlex,struct
from pathlib import Path
import verify_inline_add as address
import verify_subtract_double as arithmetic
from verify_inline_add import ROOT,SHA,INIT_SHA,RUNTIME_SHA,HOST_SHA,FILES,read_date,read_time
DEFAULT=ROOT/'research/yt-mbf-inline-subtract-double/native'
ADDRESS_DEFAULT=ROOT/'research/yt-mbf-inline-subtract-double/address-native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_inline_subtract_double.json'
PINS_SHA='aebacca6c1422ae49651dbc20c6be96f877bb164eb1821e8d5d49c836d7d8fba'
ADDRESS_PINS_SHA='0a92080d50a95292cfc970ccdaef4185bd0faa2818e6847ef3d79693c4457e78'
PAIRS={'both-zero': ('0000000000000000', '0000000000008000', 'return'),
 'aliases': ('123456789abcde00', 'ffffffffffff7f00', 'return'),
 'left-zero': ('123456789abcde00', '0000000000000081', 'return'),
 'right-zero': ('0000000000000081', '123456789abc5e00', 'return'),
 'fraction': ('0000000000004081', '000000000000c081', 'return'),
 'negative': ('0000000000008081', '0000000000000081', 'return'),
 'cancel': ('0000000000004081', '0000000000004081', 'return'),
 'cancel-reverse': ('000000000000c081', '000000000000c081', 'return'),
 'underflow': ('0100000000000001', '0000000000000001', 'return'),
 'precision': ('0000000000000081', '0100000000008049', 'return'),
 'tie-even': ('0000000000000081', '0000000000008049', 'return'),
 'tie-odd': ('0100000000000081', '0000000000008049', 'return'),
 'gap56': ('0000000000000081', '0000000000004049', 'return'),
 'gap57': ('0000000000000081', '0000000000004048', 'return'),
 'word-align': ('cdab896745230181', '436587a9cbedef70', 'return'),
 'raw': ('cdab896745230181', '436587a9cbedef81', 'return'),
 'min-range': ('ffffffffffff7f01', '0000000000008001', 'return'),
 'positive-overflow': ('ffffffffffff7fff', 'ffffffffffffffff', 'overflow'),
 'negative-overflow': ('ffffffffffffffff', 'ffffffffffff7fff', 'overflow'),
 'round-overflow': ('ffffffffffff7fff', '00000000000080c7', 'overflow'),
 'raw-cancel': ('cdab896745230181', 'cdab896745230181', 'return'),
 'raw-underflow': ('cdab896745230101', 'ccab896745230101', 'return'),
 'one-minus-three': ('0000000000000081', '0000000000004082', 'return'),
 'three-minus-one': ('0000000000004082', '0000000000000081', 'return')}

def execution_cases():
    result={}
    for label,magic in (('bm',0x6d62),('bz',0x7a62)):
        for name,(left,fac,expect) in PAIRS.items():
            for selector in (0x80,0x8a):
                result[f'{label}-{name}-{selector:02x}']=dict(op=0x9e,expect=expect,kind='full',magic=magic,base10=0x6000,base12=0x6800,selector=selector,left=left,fac=fac,initial=16777215 if name in ('negative-overflow','precision') else 5)
    for pad,magic in ((16,0x6d62),(32,0x7a62)):
        for name in ('positive-overflow','raw-cancel','raw-underflow'):
            left,fac,expect=PAIRS[name]
            result[f'pad{pad}-{name}']=dict(op=0x9e,expect=expect,pad=pad,kind='full',magic=magic,base10=0x6000,base12=0x6800,selector=0x8a,left=left,fac=fac,initial=16777215)
    return result

def address_cases():
    result={}
    contexts=(('bm',0x6d62,0x6000,0x6800,(0,128,127,255)),('bz',0x7a62,0x6000,0x6800,(0,128,127,255)),('bm-wrap',0x6d62,0xfff8,0x6800,(0,1,127)),('bz-wrap',0x7a62,0x6000,0xfff8,(0,1,127)),('fallback',0,0x6000,0x6800,(0x84,)))
    for label,magic,base10,base12,selectors in contexts:
        for selector in selectors:
            result[f'address-{label}-{selector:02x}']=dict(kind='address',magic=magic,base10=base10,base12=base12,selector=selector,left='0000000000000000',fac='a55a32cc117e8088',initial=16777215)
    return result

CASES=execution_cases()
ADDRESS_CASES=address_cases()

def poison(c):return bytes.fromhex('0000000000000082' if c['left']=='0000000000000081' else '0000000000000081')

def expected_payload(c):
    assert c['kind'] in ('address','full') and len(bytes.fromhex(c['left']))==len(bytes.fromhex(c['fac']))==8
    if c['kind']=='full':assert c['op']==0x9e and c['expect'] in ('return','overflow')
    def word(at,value,cs=False):return (b'\x2e' if cs else b'')+bytes.fromhex('c706')+struct.pack('<HH',at,value)
    def assign(at,raw):return b''.join(word(at+2*i,w) for i,w in enumerate(struct.unpack('<'+'H'*(len(raw)//2),raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    pad=bytes.fromhex('83ec')+bytes([c['pad']]) if 'pad' in c else b''
    setup=pad+bytes.fromhex('5589e583ec021e07')+word(0x5000,c['magic'])+bytes.fromhex('8cd80500058946fe')
    setup+=word(0x10,c['base10'],True)+word(0x12,c['base12'],True)+assign(0x16,bytes.fromhex(c['fac']))+assign(0x1860,bytes.fromhex(c['left']))+word(0x1870,c['selector'])
    if c['kind']=='full':setup+=assign(address.expected_offset(c),bytes.fromhex(c['left']))+assign(address.expected_offset(c,True),poison(c))
    setup+=bytes.fromhex('a10050a380182ea11000a382182ea11200a384188c1e86188c0688188b46fea38a18892e8c18')
    prefix=assign(0x1856,b'DSF1' if c['kind']=='full' else b'DS9E')+output(0x1856,4)+output(0x234,4)+output(0x16,8)+output(0x1860,8)+output(0x1f,1)+output(0x1870,1)+output(0x1880,14)
    if c['kind']=='full':prefix+=word(0x18a0,0x9e)+bytes.fromhex('a12900a3a218a12b00a3a418a1060aa3a618a1080aa3a818a1040aa3aa188b4600a3ac18')+output(0x18a0,14)
    call=bytes.fromhex('b8efbecd3f9e9090')+bytes([c['selector']])
    saved=bytes.fromhex('89369018893e9218a394188c1e96188c069818892e9a18')
    suffix=output(0x1890,12)+output(0x16,8)+output(0x234,4)+output(0x1f,1)
    if c['kind']=='full':suffix+=output(address.expected_offset(c),8)+output(address.expected_offset(c,True),8)
    return setup+prefix+call+saved+suffix+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('89ec5db8004ccd21')

def error_address(c):
    assert c['kind']=='full' and c['op']==0x9e
    p=expected_payload(c);call=bytes.fromhex('cd3f9e9090')+bytes([c['selector']]);assert p.count(call)==1
    return f'{0x6d+p.index(call)+6:04X}'

def verify_trace(raw,c):
    assert c['kind'] in ('address','full') and len(bytes.fromhex(c['left']))==len(bytes.fromhex(c['fac']))==8
    left,fac=bytes.fromhex(c['left']),bytes.fromhex(c['fac'])
    assert len(raw)>=40 and raw[:4]==(b'DSF1' if c['kind']=='full' else b'DS9E'),'separate eight-byte protocol marker'
    assert raw[4:8]==struct.pack('<I',c['initial']) and raw[8:16]==fac and raw[16:24]==left and raw[24]==0 and raw[25]==c['selector'],'full-width FAC/input/RNG/mode/selector'
    magic,b10,b12,ds,es,descriptor,bp=struct.unpack('<7H',raw[26:40])
    assert (magic,b10,b12)==(c['magic'],c['base10'],c['base12']) and ds and es==ds and descriptor==(ds+0x500)&65535 and bp>=2,'actual descriptor and caller-header context'
    offset=address.expected_offset(c)
    if c['kind']=='address':
        assert len(raw)==69 and raw[-4:]==b'END!','complete resolver-only frame'
        si,di,ax,after_ds,after_es,after_bp=struct.unpack('<6H',raw[40:52])
        assert si==di==offset and ax==0xbeef and (after_ds,after_es,after_bp)==(ds,es,bp),'offset-only resolver registers'
        assert raw[52:60]==fac and raw[60:64]==struct.pack('<I',c['initial']) and raw[64]==0,'resolver does not claim arithmetic or operand reads'
        return dict(resolved=offset,fac_after=raw[52:60].hex())
    assert c['op']==0x9e and c['expect'] in ('return','overflow') and len(raw)>=54
    op,route,hook,saved_bp,saved_sp,module_sp,original_bp=struct.unpack('<7H',raw[40:54])
    assert op==0x9e and route==0xa68 and hook==0 and saved_sp==0,'default admitted error route; no ON ERROR hook'
    assert original_bp>=40 and saved_bp==original_bp and module_sp+6==original_bp and bp+8+c.get('pad',0)==original_bp,'declared bootstrap/padded BP context'
    assert offset<=65528 and address.expected_offset(c,True)<=65528,'safe complete eight-byte spans'
    want=arithmetic.expected_entry(left,fac,fac)
    assert (want is None)==(c['expect']=='overflow'),'qualified DOUBLE arithmetic determines outcome'
    if want is None:
        at=error_address(c);message=('\r\nOverflow in module YT-INIT  at address 01A3:'+at+'\r\n\r\nHit any key to return to system').encode()
        assert raw[54:]==message,'complete exact error at consumed-selector continuation; no invented post-error FAC'
        return dict(output=None,error_address=at)
    assert len(raw)==99 and raw[-4:]==b'END!','complete full-return frame'
    si,di,ax,after_ds,after_es,after_bp=struct.unpack('<6H',raw[54:66])
    assert si==offset and di==0x16 and ax==0xbeef and (after_ds,after_es,after_bp)==(ds,es,bp),'DOUBLE FAC selection and preserved registers'
    assert raw[66:74]==want and raw[74:78]==struct.pack('<I',c['initial']) and raw[78]==0,'full raw DOUBLE output, RNG and mode'
    assert raw[79:87]==left and raw[87:95]==poison(c),'selected and alternate-base eight-byte blocks preserved'
    return dict(output=want.hex(),error_address=None)

def verify_static(runtime):
    arithmetic.verify_static(runtime) # retained DOUBLE entry/kernel and shared frame/error packets
    assert struct.unpack_from('<H',runtime,0x58d+2*0x9e)[0]==0xad86,'original inline9e dispatch'
    assert runtime[0xaf86:0xaf8f]==bytes.fromhex('e83a71bf1600e8dc71'),'retained resolver, DOUBLE FAC and ABI entry'
    _,calls=arithmetic.verify_inventory();assert calls==[],'no inline9e sites in bounded maintenance inventory'
    return calls

def verify_corpus(directory,cases,pins_sha,recipe_id,source_name,kind):
    assert kind in ('address','full') and all(c['kind']==kind for c in cases.values()),'closed DOUBLE protocol'
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
        if kind=='address':
            assert copied[0xaf89:0xaf8c]==bytes.fromhex('bf1600')
            copied[0xaf89:0xaf8c]=bytes.fromhex('cb9090')
        assert set(meta)==set(case)|{'recipe','case','exit_code','timeout','missing','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'fixed result schema'
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
        portable.append(dict(name=name,**case,**want,trace_hex=trace.hex(),source_trace_sha256=SHA(trace)))
    return portable


def verify(directory=DEFAULT,fixture=FIXTURE,address_directory=ADDRESS_DEFAULT):
    full=verify_corpus(directory,CASES,PINS_SHA,'brun30-inline-subtract-double-v1','recover_inline_subtract_double.py','full')
    offsets=verify_corpus(address_directory,ADDRESS_CASES,ADDRESS_PINS_SHA,'brun30-inline-subtract-double-address-v1','recover_inline_subtract_double_address.py','address')
    doc=dict(format='qb-native-inline-subtract-double-v1',address_cases=offsets,execution_cases=full)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==doc,'portable fixture equals both complete DOUBLE corpora'
    return doc

if __name__=='__main__':
    d=verify();print('Verified',len(d['address_cases']),'eight-byte resolver controls and',len(d['execution_cases']),'full inline9e controls;',sum(c['output']is None for c in d['execution_cases']),'exact native Overflows')
