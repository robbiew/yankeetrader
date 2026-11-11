"""Capture one BRUN30 inline8d resolver-only controls per disposable process.

Every first outcome (including timeout, partial trace and runtime error) is kept.
No observed artifact is retried or rewritten by this acquisition.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA = '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


def cases():
    result={}
    contexts=(('bm',0x6d62,0x6000,0x6800,(0,128,127,255)),('bz',0x7a62,0x6000,0x6800,(0,128,127,255)),('bm-wrap',0x6d62,0xfff8,0x6800,(0,1,127)),('bz-wrap',0x7a62,0x6000,0xfff8,(0,1,127)),('fallback',0,0x6000,0x6800,(0x84,)))
    for label,magic,base10,base12,selectors in contexts:
        for selector in selectors:
            result[f'address-{label}-{selector:02x}']=dict(kind='address',magic=magic,base10=base10,base12=base12,selector=selector,left='00000000',fac='a55a3288',initial=16777215)
    return result


def offset(case,alternate=False):
    base=case['base12'] if (case['magic']==0x7a62)^alternate else case['base10']
    return (base+8*(case['selector']&127))&65535


def payload(case):
    code=bytearray()
    def emit(raw):code.extend(bytes.fromhex(raw))
    def word(at,value,cs=False):
        if cs:emit('2e')
        code.extend(bytes.fromhex('c706')+struct.pack('<HH',at,value))
    def assign(at,raw):
        for i in (0,2):word(at+i,int.from_bytes(raw[i:i+2],'little'))
    def output(at,size):code.extend(bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    # All metadata changes occur after the two untouched original startup calls.
    emit('5589e583ec021e07') # New BP frame, one word local, ES=DS.
    word(0x5000,case['magic']);emit('8cd80500058946fe') # [SS:BP-2] = DS + 0500.
    word(0x10,case['base10'],True);word(0x12,case['base12'],True)
    assign(0x1a,bytes.fromhex(case['fac']));assign(0x1860,bytes.fromhex(case['left']))
    word(0x1870,case['selector'])
    if case['kind']=='full':
        assign(offset(case),bytes.fromhex(case['left']))
        poison='00000082' if case['left']=='00000081' else '00000081'
        assign(offset(case,True),bytes.fromhex(poison))
    # Capture actual descriptor tag, caller-CS base words and constructed frame.
    emit('a10050a380182ea11000a382182ea11200a384188c1e86188c0688188b46fea38a18892e8c18')
    assign(0x1856,b'ID8D');output(0x1856,4);output(0x234,4);output(0x1a,4);output(0x1860,4);output(0x1f,1);output(0x1870,1);output(0x1880,14)
    emit('b8efbecd3f8d9090');code.append(case['selector'])
    emit('89369018893e9218a394188c1e96188c069818892e9a18')
    output(0x1890,12);output(0x1a,4);output(0x234,4);output(0x1f,1)
    if case['kind']=='full':output(offset(case),4);output(offset(case,True),4)
    assign(0x1856,b'END!');output(0x1856,4);emit('89ec5db8004ccd21')
    return bytes(code)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('destination',type=Path); p.add_argument('--scratch',required=True,type=Path); a=p.parse_args()
    out=a.destination.absolute(); scratch=a.scratch.absolute(); assert not out.exists() and not scratch.exists()
    initial=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes(); host=Path('/opt/homebrew/bin/dosbox-staging')
    assert (SHA(initial),SHA(runtime))==(INIT_SHA,RUNTIME_SHA)
    assert initial[0x23a:0x23f]==bytes.fromhex('cd3d439090')
    out.mkdir(parents=True); scratch.mkdir(); (out/'sources').mkdir(); shutil.copyfile(__file__,out/'sources'/Path(__file__).name)
    matrix=cases(); recipe=dict(recipe='brun30-inline-divide-address-v1',cases=matrix,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
    for name,case in matrix.items():
        temp=scratch/name; temp.mkdir(); folder=out/name; folder.mkdir(); stub=payload(case)
        patched=bytearray(initial); patched[0x23a:0x23f]=bytes.fromhex('e930009090'); patched[0x26d:0x26d+len(stub)]=stub
        copied=bytearray(runtime); struct.pack_into('<I',copied,0x10234,case['initial'])
        if case['kind']=='address':
            assert copied[0xb728:0xb72b]==bytes.fromhex('bf1a00')
            copied[0xb728:0xb72b]=bytes.fromhex('cb9090') # Resolver-only return; no operand dereference.
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
        trace=(folder/'TRACE.BIN').read_bytes() if (folder/'TRACE.BIN').exists() else b''
        if timeout or exit_code or len(trace)!=(57 if case['kind']=='address' else 65) or not trace.startswith(b'ID8D') or not trace.endswith(b'END!'):
            raise RuntimeError('first malformed outcome retained; do not retry or continue unsafe controls: '+name)

if __name__=='__main__': main()
