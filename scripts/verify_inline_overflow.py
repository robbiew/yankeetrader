"""Audit bounded native inline arithmetic errors, bootstrap context and finite controls."""
import json,shlex,struct
from pathlib import Path
import verify_inline_add as shared
import verify_single_sub as subtraction
from verify_inline_add import ROOT,SHA,INIT_SHA,RUNTIME_SHA,HOST_SHA,FILES,read_date,read_time
DEFAULT=ROOT/'research/yt-mbf-inline-overflow/native'
DEPTH_DEFAULT=ROOT/'research/yt-mbf-inline-overflow/depth-native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_inline_overflow.json'
PINS_SHA='7271f3d28b80817d66a7139cf0959666c50d9a8f24e00e3a106b5e7a695c45c3'
DEPTH_PINS_SHA='ae4a70f30a441985174231084d58ac9f41bf495e7fb8826f118a1cebb52e006c'
CASES={}
for _op in (0x85,0x9d):
    for _label,_magic in (('bm',0x6d62),('bz',0x7a62)):
        for _name,_left,_fac,_expect in (
            ('positive-overflow','ffff7fff','ffff7fff' if _op==0x85 else 'ffffffff','overflow'),
            ('negative-overflow','ffffffff','ffffffff' if _op==0x85 else 'ffff7fff','overflow'),
            ('finite-control','00004081','ffff7fff' if _op==0x85 else 'ffffffff','return')):
            CASES[f'op{_op:02x}-{_label}-{_name}']=dict(op=_op,expect=_expect,kind='full',magic=_magic,base10=0x6000,base12=0x6800,selector=0x83,left=_left,fac=_fac,initial=16777215 if _name=='negative-overflow' else 5)
DEPTH_CASES={}
for _op in (0x85,0x9d):
    for _pad,_magic in ((16,0x6d62),(32,0x7a62)):
        for _name,_left,_fac,_expect in (('overflow','ffff7fff','ffff7fff' if _op==0x85 else 'ffffffff','overflow'),('finite-control','00004081','ffff7fff' if _op==0x85 else 'ffffffff','return')):
            DEPTH_CASES[f'op{_op:02x}-pad{_pad}-{_name}']=dict(op=_op,expect=_expect,pad=_pad,kind='full',magic=_magic,base10=0x6000,base12=0x6800,selector=0x83,left=_left,fac=_fac,initial=16777215)


def expected_payload(c):
    def word(at,value,cs=False):return (b'\x2e' if cs else b'')+bytes.fromhex('c706')+struct.pack('<HH',at,value)
    def assign(at,raw):return b''.join(word(at+2*i,w) for i,w in enumerate(struct.unpack('<HH',raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    pad=bytes.fromhex('83ec')+bytes([c['pad']]) if 'pad' in c else b''
    setup=pad+bytes.fromhex('5589e583ec021e07')+word(0x5000,c['magic'])+bytes.fromhex('8cd80500058946fe')
    setup+=word(0x10,c['base10'],True)+word(0x12,c['base12'],True)+assign(0x1a,bytes.fromhex(c['fac']))+assign(0x1860,bytes.fromhex(c['left']))+word(0x1870,c['selector'])
    setup+=assign(shared.expected_offset(c),bytes.fromhex(c['left']))+assign(shared.expected_offset(c,True),bytes.fromhex('00000081'))
    setup+=bytes.fromhex('a10050a380182ea11000a382182ea11200a384188c1e86188c0688188b46fea38a18892e8c18')
    prefix=assign(0x1856,b'IOF1')+output(0x1856,4)+output(0x234,4)+output(0x1a,4)+output(0x1860,4)+output(0x1f,1)+output(0x1870,1)+output(0x1880,14)
    context=word(0x18a0,c['op'])+bytes.fromhex('a12900a3a218a12b00a3a418a1060aa3a618a1080aa3a818a1040aa3aa188b4600a3ac18')+output(0x18a0,14)
    call=bytes.fromhex('b8efbecd3f')+bytes([c['op'],0x90,0x90,c['selector']])
    saved=bytes.fromhex('89369018893e9218a394188c1e96188c069818892e9a18')
    suffix=output(0x1890,12)+output(0x1a,4)+output(0x234,4)+output(0x1f,1)+output(shared.expected_offset(c),4)+output(shared.expected_offset(c,True),4)
    return setup+prefix+context+call+saved+suffix+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('89ec5db8004ccd21')


def error_address(c):
    payload=expected_payload(c);needle=bytes([0xcd,0x3f,c['op'],0x90,0x90,c['selector']]);assert payload.count(needle)==1
    # Resolver LODSB consumes the sixth byte and pushes the advanced return IP.
    return f'{0x6d+payload.index(needle)+6:04X}'


def verify_trace(trace,c):
    assert c['op'] in (0x85,0x9d,0x95,0x8d) and c['kind']=='full' and c['expect'] in ('overflow','return','division_by_zero')
    assert c['expect']!='division_by_zero' or c['op']==0x8d,'division-zero is a division-only outcome'
    assert len(trace)>=46 and trace[:4]==b'IOF1','complete pre-entry frame'
    left,fac=bytes.fromhex(c['left']),bytes.fromhex(c['fac'])
    assert trace[4:8]==struct.pack('<I',c['initial']) and trace[8:12]==fac and trace[12:16]==left and trace[16]==0 and trace[17]==c['selector'],'actual initial RNG, operands, mode and selector'
    magic,b10,b12,ds,es,descriptor,bp=struct.unpack('<7H',trace[18:32])
    assert (magic,b10,b12)==(c['magic'],c['base10'],c['base12']) and ds!=0 and ds==es and descriptor==(ds+0x500)&65535,'actual module metadata and synthetic descriptor'
    op,route,hook,saved_bp,saved_sp,module_sp,original_bp=struct.unpack('<7H',trace[32:46])
    assert op==c['op'] and route==0xa68 and hook==0 and saved_sp==0,'admitted bootstrap error route, no ON ERROR hook, pre-ABI SP snapshot'
    assert original_bp>=40 and saved_bp==original_bp and module_sp+6==original_bp and bp+8+c.get('pad',0)==original_bp,'observed bootstrap/frame-depth context; not arbitrary-frame admission'
    assert shared.expected_offset(c)<=65532 and shared.expected_offset(c,True)<=65532,'safe complete memory spans'
    if c['op']==0x85:
        from verify_single_add_entries import expected_entry
    elif c['op']==0x9d:expected_entry=subtraction.expected_entry
    elif c['op']==0x95:
        from verify_single_multiply import expected_entry
    else:
        from verify_single_divide import expected_entry
    want=expected_entry(left,fac,fac)
    failure=want if isinstance(want,str) else ('overflow' if want is None else None)
    assert (failure or 'return')==c['expect'],'source-qualified arithmetic determines the distinct outcome'
    if failure:
        address=error_address(c);label={'overflow':'Overflow','division_by_zero':'Division by zero'}[failure]
        message=('\r\n'+label+' in module YT-INIT  at address 01A3:'+address+'\r\n\r\nHit any key to return to system').encode()
        assert trace[46:]==message,'exact complete fatal diagnostic with consumed inline return byte; no invented post-error state'
        result=dict(output=None,error_address=address)
        if c['op']==0x8d:result['error']=failure
        return result
    assert len(trace)==79 and trace[-4:]==b'END!','complete finite control return'
    si,di,ax,after_ds,after_es,after_bp=struct.unpack('<6H',trace[46:58])
    assert si==shared.expected_offset(c) and di==0x1a and ax==0xbeef and (after_ds,after_es,after_bp)==(ds,es,bp),'finite control preserves registers and resolves the chosen base'
    assert trace[58:62]==want and trace[62:66]==struct.pack('<I',c['initial']) and trace[66]==0,'finite FAC, RNG and mode'
    assert trace[67:71]==left and trace[71:75]==bytes.fromhex('00000081'),'finite selected/poison memory unchanged'
    result=dict(output=want.hex(),error_address=None)
    if c['op']==0x8d:result['error']=None
    return result


def verify_static(runtime):
    from verify_rng_native import image
    shared.verify_static(runtime);subtraction.verify_static(runtime)
    for name,pin,address,size in [('error-dispatch.json','f8930128fa4c0798d13a6d343c8d74de03ea6fc95c4cd82892c73b4e3fff40fd','0x109a0',180),('error-dispatch-tail.json','bad8f0c49b7ec161740d086b1ed9e9ac3493cbbf4d98ba411a13372b957ec0af','0x10a54',9)]:
        raw=(ROOT/'research/yt-mbf-inline-overflow/rea'/name).read_bytes();assert SHA(raw)==pin,'fixed complete source packet'
        packet=json.loads(raw);assert packet['ok'] is True;e=packet['data'];n=e['normalized_result']
        assert e['operation']=='read_bytes' and e['subject']['digest']['sha256']==RUNTIME_SHA and e['parameters']==dict(address=address,length=size)
        assert n['complete'] is True and n['requested_bytes']==n['returned_bytes']==size and n['address']==address
        at=int(address,16)-0x10000;assert bytes.fromhex(n['bytes_hex'])==image(runtime)[at:at+size]
    assert runtime[0xba0:0xba2]==bytes.fromhex('b306'),'Overflow error code BL=6'
    assert runtime[0xc41:0xc4d]==bytes.fromhex('8b0e2b00e302ffe18b2e060a'),'optional error hook; default saved-BP restoration'
    assert runtime[0xc59:0xc5d]==bytes.fromhex('ff262900'),'default route dispatch'


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


def verify(directory=DEFAULT,fixture=FIXTURE,depth_directory=DEPTH_DEFAULT):
    portable=verify_corpus(directory,CASES,PINS_SHA,'brun30-inline-overflow-v1','recover_inline_overflow.py')
    portable+=verify_corpus(depth_directory,DEPTH_CASES,DEPTH_PINS_SHA,'brun30-inline-overflow-depth-v1','recover_inline_overflow_depth.py')
    doc=dict(format='qb-native-inline-overflow-v1',cases=portable)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==doc,'portable fixture equals both complete native corpora'
    return doc

if __name__=='__main__':
    d=verify();print('Verified',len(d['cases']),'inline error-context controls:',sum(c['output'] is None for c in d['cases']),'exact Overflows and',sum(c['output'] is not None for c in d['cases']),'finite returns')
