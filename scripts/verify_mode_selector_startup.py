"""Authenticate bounded selector references and post-startup observations.

No empty reference result or byte-signature absence is promoted to an exhaustive
proof about indirect writes or later gameplay. No replay policy is selected here.
"""
import hashlib,json,shlex,struct
from pathlib import Path
from verify_rng_clock import read_date,read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-mode-selector/native'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='90d2ae2297df484209306ea1b872ce49311ca8784ad3568d06013aad6f2ba263'
RUNTIME_SHA='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
PROGRAMS={'LOCAL.EXE': 'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a', 'PORTNAME.EXE': 'fc5239f345b39d0d425d1f41af54352fa545f7392fda26c700180382a1524ec4', 'RMT-INIT.EXE': '05f639fe5249ac6ae8e28d8656f4c5e668e40ff08bf66524b109ad31a2217dac', 'YT-INIT.EXE': '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2', 'YT.EXE': 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037', 'YTCONFIG.EXE': '120da32994a9ae3b8b9276aeabe076a5d1e2aab86c011cf175db7573e59faa03', 'YTMAINT.EXE': '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'}
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_payload():
    def assign(raw):return b''.join(bytes.fromhex('c706')+struct.pack('<HH',0x1856+i,word) for i,word in zip((0,2),struct.unpack('<HH',raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    return assign(b'MSEL')+output(0x1856,4)+output(0,64)+assign(b'END!')+output(0x1856,4)+bytes.fromhex('b8004ccd21')


def verify_relocations(original,payload_length):
    table=struct.unpack_from('<H',original,24)[0];count=struct.unpack_from('<H',original,6)[0]
    for i in range(count):
        offset,segment=struct.unpack_from('<HH',original,table+4*i);at=16*segment+offset
        for start,end in ((0x3a,0x3f),(0x6d,0x6d+payload_length)):
            assert not(at<end and at+2>start),'no loader relocation may overlap the entry hook or diagnostic'


def verify_trace(trace):
    assert len(trace)==72 and trace[:4]==b'MSEL' and trace[-4:]==b'END!','complete startup snapshot frame'
    assert trace[4+0x1f]==0,'observed selector zero after untouched original startup'
    return trace[4:68]


def verify_static():
    from audit_mode_selector_bytes import build
    from verify_int16_double import verify_static as verify_conversion_kernel
    runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes();assert SHA(runtime)==RUNTIME_SHA
    verify_conversion_kernel(runtime)
    path=ROOT/'research/yt-mbf-mode-selector/byte-inventory.json';raw=path.read_bytes()
    assert SHA(raw)=='fae12b4c7ba183973c3c0bd5769d87832d95d1e5b21386a476d526faf57cce93','fixed ordinary byte inventory'
    report=json.loads(raw);assert report==build(),'complete original-file byte-signature inventory'
    rows=report['programs'];assert len(rows)==8 and all(not r['enumerated_store_candidates'] for r in rows),'bounded enumerated store scan'
    assert rows[0]['compare_mode4_offsets']==[0xab07,0xab3b,0xab66,0xaba3,0xd8f5],'five known direct comparisons remain visible'
    for name,pin in [('selector-xrefs.json','e4e199c181c85d55de027ad49d90004db3276a7d27f1e13bfe7a87759889fe6a'),('fifth-selector-read.json','25fb9f7606183eff95215a475232201e120b1d7be0d24a6c96f64b29b4e9b65f')]:
        raw=(ROOT/'research/yt-mbf-mode-selector/rea'/name).read_bytes();assert SHA(raw)==pin,'immutable REA evidence'
        envelope=json.loads(raw);assert envelope['ok'] is True;e=envelope['data'];assert e['subject']['digest']['sha256']==RUNTIME_SHA and e['provider']['id']=='ghidra'
        if name=='selector-xrefs.json':
            assert e['operation']=='xrefs' and e['parameters']==dict(address='0x1fe1f') and e['normalized_result']==[],'retained empty provider reference result, not proof of absence'
        else:
            n=e['normalized_result'];assert n['address']=='0x1d6e3' and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==30
            assert bytes.fromhex(n['bytes_hex'])==runtime[0xd8e3:0xd901],'fifth selector-read source mapping'
    return report


def verify_replay_sources():
    # These pre-existing contracts distinguish INT-to-MBF stock pickup from
    # the later name-related signed16 conversion; no mode-4 integration follows.
    from verify_maintenance_stock_conversion_native import verify as stock_source
    from verify_initializer_native import verify as initializer_source
    stock_source();initializer_source()
    init=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes()
    maint=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    assert init[0x18ab:0x18b0]==bytes.fromhex('cd3f759090'),'existing sector-write signed16 call'
    assert maint[0x4eea:0x4efd]==bytes.fromhex('bb9418cd3d199090cd3f77909087d3bb6418cd'),'later name-related signed16 call is separate from stock INT'
    return dict(initializer_conversion_file_offset=0x18ab,stock_INT_file_offset=0x4edb,name_conversion_file_offset=0x4ef2,decision='no-mode4-replay-migration-admitted')


def verify(directory=DEFAULT):
    root=Path(directory);raw=(root/'pins.json').read_bytes();assert SHA(raw)==PINS_SHA,'fixed startup manifest'
    pins=json.loads(raw)['files'];assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}==set(pins),'complete startup artifact inventory'
    for name,digest in pins.items():assert SHA((root/name).read_bytes())==digest,'immutable startup artifact '+name
    originals={n:(ROOT/'archive/dos-original'/n).read_bytes() for n in PROGRAMS};runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert SHA(runtime)==RUNTIME_SHA and {n:SHA(b) for n,b in originals.items()}==PROGRAMS,'all eight original binary identities'
    source=root/'sources/recover_mode_selector_startup.py';recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe='brun30-normal-startup-selector-v1',programs=PROGRAMS,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'fixed prelaunch recipe and actual frozen source'
    assert {p.name for p in root.iterdir()}=={n.lower() for n in PROGRAMS}|{'pins.json','sources','recipe.json'} and {p.name for p in source.parent.iterdir()}=={source.name}
    snapshots={};stub=expected_payload()
    for name,original in originals.items():
        folder=root/name.lower();meta=json.loads((folder/'result.json').read_text());header=struct.unpack_from('<H',original,8)[0]*16
        assert original[header:header+2]==b'bm' and struct.unpack_from('<H',original,20)[0]+16*struct.unpack_from('<H',original,22)[0]==0x30,'original entry starts at the two preserved calls';startup=original[header+0x30:header+0x3a];assert startup[0]==startup[5]==0x9a
        verify_relocations(original,len(stub))
        patched=bytearray(original);patched[header+0x3a:header+0x3f]=bytes.fromhex('e930009090');patched[header+0x6d:header+0x6d+len(stub)]=stub
        assert patched[header+0x30:header+0x3a]==startup,'both normal startup calls untouched'
        assert set(meta)=={'recipe','program','header','startup_hex','original_body_hex','exit_code','timeout','missing','payload_hex','copied_program_sha256','runtime_sha256','files'}
        assert meta['recipe']==recipe['recipe'] and meta['program']==name and meta['header']==header and meta['startup_hex']==startup.hex() and meta['original_body_hex']==original[header+0x3a:header+0x3f].hex()
        assert meta['exit_code']==0 and meta['timeout'] is False and meta['missing']==[],'complete natural startup probe outcome'
        assert meta['payload_hex']==stub.hex() and meta['copied_program_sha256']==SHA(patched) and meta['runtime_sha256']==RUNTIME_SHA,'full copied program reconstruction; original runtime untouched'
        assert set(meta['files'])==FILES and {p.name for p in folder.iterdir()}==FILES|{'result.json'}
        for file,digest in meta['files'].items():assert SHA((folder/file).read_bytes())==digest
        commands=(folder/'COMMANDS.TXT').read_text().splitlines();assert len(commands)==11 and commands[0].startswith(('mount c /tmp/','mount c /private/tmp/')) and Path(commands[0][8:]).name==name.lower()
        assert commands[1:]==['c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG',name+' > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit']
        argv=['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in ('-c',c)]
        assert json.loads((folder/'launch.json').read_text())==argv
        messages=[line.split(' | ',1)[1] for line in (folder/'dosbox.stderr').read_text().splitlines() if ' | ' in line]
        assert [shlex.split(m[11:]) for m in messages if m.startswith('arguments: ')]==[argv] and messages.count('dosbox-staging version 0.83.0 ()')==1
        assert 'SDL: dummy video initialised' in messages and "MIXER: Sound output disabled ('nosound' mode)" in messages and any(m.startswith('CPU: Setting fixed 200000 cycles.') for m in messages)
        assert (folder/'dosbox.stdout').read_bytes()==b'' and (folder/'ERROR.LOG').read_bytes()==b'' and (folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n' and (folder/'RETURN.LOG').read_bytes()==b'PROBE_RETURNED\r\n'
        assert read_date((folder/'DOSDATE.LOG').read_bytes()).isoformat()=='2026-11-02' and abs(read_time((folder/'DOSTIME.LOG').read_bytes()))<=.1
        snapshots[name]=verify_trace((folder/'TRACE.BIN').read_bytes()).hex()
    static=verify_static();decision=verify_replay_sources()
    return dict(startup_snapshots=snapshots,selector=0,byte_inventory_programs=len(static['programs']),**decision)

if __name__=='__main__':
    r=verify();print('Verified',len(r['startup_snapshots']),'original-startup snapshots (selector zero), eight-file bounded byte audit and source-separated replay decision')
