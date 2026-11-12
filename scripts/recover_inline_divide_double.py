"""Capture bounded BRUN30 inline8e DOUBLE division results and errors per disposable process.

Every first outcome (including timeout, partial trace and runtime error) is kept.
No observed artifact is retried or rewritten by this acquisition.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA = '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


PAIRS={'both-zero': ('0000000000000000', '0000000000000000', 'division_by_zero'),
 'aliases': ('0000000012345600', '00000000ffffff00', 'division_by_zero'),
 'left-zero': ('0000000012345600', '0000000000008081', 'return'),
 'right-zero': ('0000000000004081', '00000000ffffff00', 'division_by_zero'),
 'max-zero': ('00000000ffff7fff', '0000000012345600', 'division_by_zero'),
 'one': ('0000000000000081', '0000000000000081', 'return'),
 'three-two': ('0000000000004082', '0000000000000082', 'return'),
 'two-three': ('0000000000000082', '0000000000004082', 'return'),
 'one-three': ('0000000000000081', '0000000000004082', 'return'),
 'raw': ('0000000056341281', '00000000ac681381', 'return'),
 'raw-reversed': ('00000000ac681381', '0000000056341281', 'return'),
 'max-one': ('00000000ffff7fff', '0000000000000081', 'return'),
 'min-one': ('0000000000000001', '0000000000000081', 'return'),
 'min-two': ('0000000000000001', '0000000000000082', 'return'),
 'max-half': ('00000000ffff7fff', '0000000000000080', 'overflow'),
 'max-min': ('00000000ffff7fff', '0000000000000001', 'overflow'),
 'negative-right': ('0000000000004082', '0000000000008082', 'return'),
 'both-negative': ('000000000000c082', '0000000000008082', 'return'),
 'guard55-below-0': ('0200000000004081', '0100000000000081', 'return'),
 'guard55-below-1': ('5955555555559581', '0300000000000081', 'return'),
 'guard55-above-0': ('b0aaaaaaaaaa6a81', '0300000000000081', 'return'),
 'guard55-above-1': ('010000000000c081', '0100000000000081', 'return'),
 'guard56-below-0': ('2049922449922481', 'f9ffffffffff7f81', 'return'),
 'guard56-below-1': ('4f1886611886e181', 'ebffffffffff7f81', 'return'),
 'guard56-above-0': ('0000000000000081', 'ffffffffffff7f81', 'return'),
 'guard56-above-1': ('535555555555d581', 'fdffffffffff7f81', 'return'),
 'uf0-late': ('0000000000000001', 'cdab896745230181', 'return'),
 'uf0-early': ('0000000000000001', 'cdab896745230182', 'return'),
 'uf0-minimum': ('cdab896745230101', 'cdab896745230181', 'return'),
 'uf1-late': ('0000000000000001', 'ffffffffffff7f81', 'return'),
 'uf1-early': ('0000000000000001', 'ffffffffffff7f82', 'return'),
 'uf1-minimum': ('ffffffffffff7f01', 'ffffffffffff7f81', 'return'),
 'uf2-late': ('0000000000000001', '0100000000000081', 'return'),
 'uf2-early': ('0000000000000001', '0100000000000082', 'return'),
 'uf2-minimum': ('0100000000000001', '0100000000000081', 'return')}

def cases():
    result={}
    for label,magic in (('bm',0x6d62),('bz',0x7a62)):
        for name,(left,fac,expect) in PAIRS.items():
            for selector in (0x80,0x8a):
                result[f'{label}-{name}-{selector:02x}']=dict(op=0x8e,expect=expect,kind='full',magic=magic,base10=0x6000,base12=0x6800,selector=selector,left=left,fac=fac,initial=16777215 if name.startswith(('sticky','partial-word')) else 5)
    for pad,magic in ((16,0x6d62),(32,0x7a62)):
        for name in ('max-half','both-zero','uf0-late','uf0-early'):
            left,fac,expect=PAIRS[name]
            result[f'pad{pad}-{name}']=dict(op=0x8e,expect=expect,pad=pad,kind='full',magic=magic,base10=0x6000,base12=0x6800,selector=0x8a,left=left,fac=fac,initial=16777215)
    return result


def offset(case,alternate=False):
    base=case['base12'] if (case['magic']==0x7a62)^alternate else case['base10']
    return (base+8*(case['selector']&127))&65535


def payload(case):
    assert case['kind']=='full' and case['op']==0x8e and len(bytes.fromhex(case['fac']))==len(bytes.fromhex(case['left']))==8
    code=bytearray()
    def emit(raw):code.extend(bytes.fromhex(raw))
    def word(at,value,cs=False):
        if cs:emit('2e')
        code.extend(bytes.fromhex('c706')+struct.pack('<HH',at,value))
    def assign(at,raw):
        for i in range(0,len(raw),2):word(at+i,int.from_bytes(raw[i:i+2],'little'))
    def output(at,size):code.extend(bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    # All metadata changes occur after the two untouched original startup calls.
    if 'pad' in case:emit('83ec'+format(case['pad'],'02x'))
    emit('5589e583ec021e07') # New BP frame, one word local, ES=DS.
    word(0x5000,case['magic']);emit('8cd80500058946fe') # [SS:BP-2] = DS + 0500.
    word(0x10,case['base10'],True);word(0x12,case['base12'],True)
    assign(0x16,bytes.fromhex(case['fac']));assign(0x1860,bytes.fromhex(case['left']))
    word(0x1870,case['selector'])
    if case['kind']=='full':
        assign(offset(case),bytes.fromhex(case['left']))
        poison='0000000000000082' if case['left']=='0000000000000081' else '0000000000000081'
        assign(offset(case,True),bytes.fromhex(poison))
    # Capture actual descriptor tag, caller-CS base words and constructed frame.
    emit('a10050a380182ea11000a382182ea11200a384188c1e86188c0688188b46fea38a18892e8c18')
    assign(0x1856,b'DVF1');output(0x1856,4);output(0x234,4);output(0x16,8);output(0x1860,8);output(0x1f,1);output(0x1870,1);output(0x1880,14)
    # Snapshot pre-entry runtime error context separately from synthetic BP.
    word(0x18a0,case['op'])
    emit('a12900a3a218a12b00a3a418a1060aa3a618a1080aa3a818a1040aa3aa188b4600a3ac18')
    output(0x18a0,14)
    emit('b8efbecd3f');code.extend(bytes([case['op'],0x90,0x90,case['selector']]))
    emit('89369018893e9218a394188c1e96188c069818892e9a18')
    output(0x1890,12);output(0x16,8);output(0x234,4);output(0x1f,1)
    if case['kind']=='full':output(offset(case),8);output(offset(case,True),8)
    assign(0x1856,b'END!');output(0x1856,4);emit('89ec5db8004ccd21')
    return bytes(code)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('destination',type=Path); p.add_argument('--scratch',required=True,type=Path); a=p.parse_args()
    out=a.destination.absolute(); scratch=a.scratch.absolute(); assert not out.exists() and not scratch.exists()
    initial=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes(); host=Path('/opt/homebrew/bin/dosbox-staging')
    assert (SHA(initial),SHA(runtime))==(INIT_SHA,RUNTIME_SHA)
    assert initial[0x23a:0x23f]==bytes.fromhex('cd3d439090')
    out.mkdir(parents=True); scratch.mkdir(); (out/'sources').mkdir(); shutil.copyfile(__file__,out/'sources'/Path(__file__).name)
    matrix=cases(); recipe=dict(recipe='brun30-inline-divide-double-v1',cases=matrix,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
    for name,case in matrix.items():
        temp=scratch/name; temp.mkdir(); folder=out/name; folder.mkdir(); stub=payload(case)
        patched=bytearray(initial); patched[0x23a:0x23f]=bytes.fromhex('e930009090'); patched[0x26d:0x26d+len(stub)]=stub
        copied=bytearray(runtime); struct.pack_into('<I',copied,0x10234,case['initial'])
        (temp/'YT-INIT.EXE').write_bytes(patched); (temp/'BRUN30.EXE').write_bytes(copied)
        commands=['mount c '+str(temp),'c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit']
        argv=[str(host),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in ('-c',c)]
        (folder/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n'); (folder/'launch.json').write_text(json.dumps(argv,indent=2)+'\n')
        timeout=False
        with (folder/'dosbox.stdout').open('wb') as stdout,(folder/'dosbox.stderr').open('wb') as stderr:
            with subprocess.Popen(argv,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=stdout,stderr=stderr) as child:
                try: child.wait(timeout=20)
                except subprocess.TimeoutExpired: timeout=True; child.kill(); child.wait()
                exit_code=child.returncode
        missing=[]
        for file in ('TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'):
            if (temp/file).exists(): shutil.copyfile(temp/file,folder/file)
            else: missing.append(file)
        assert (temp/'YT-INIT.EXE').read_bytes()==patched and (temp/'BRUN30.EXE').read_bytes()==copied
        meta=dict(recipe=recipe['recipe'],case=name,**case,exit_code=exit_code,timeout=timeout,missing=missing,payload_hex=stub.hex(),copied_initializer_sha256=SHA(patched),copied_runtime_sha256=SHA(copied),files={p.name:SHA(p.read_bytes()) for p in sorted(folder.iterdir())})
        (folder/'result.json').write_text(json.dumps(meta,indent=2)+'\n'); print(name,exit_code,'timeout' if timeout else 'returned',flush=True)
        if timeout or exit_code or missing:
            raise RuntimeError('first incomplete process outcome retained; inspect before further acquisition: '+name)

if __name__=='__main__': main()
