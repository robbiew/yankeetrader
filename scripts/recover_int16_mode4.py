"""Capture one BRUN30 explicit-mode-4 signed16 conversion per disposable process.

Every first outcome (including timeout, partial trace and runtime error) is kept.
No observed artifact is retried or rewritten by this acquisition.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA = '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


RAWS={'single': ['00000000', '0000007f', '0000807f', 'ffff7f7f', 'ffffff7f', '00000080', '00008080', '01000080', '01008080', '00004080', '0000c080', '00000081', '00008081', '00004081', '0000c081', 'ffff1f82', 'ffff9f82', '00002082', '0000a082', '01002082', '0100a082', '00006082', '0000e082', '00fe7f8f', '00feff8f', '80fe7f8f', '80feff8f', 'fffe7f8f', 'fffeff8f', '00ff7f8f', '00ffff8f', '01ff7f8f', '01ffff8f', '00000090', '00008090', '80000090', '80008090', '81000090', '81008090', '00010090', '00018090', '00000091', '00008091', 'ffff7f00', 'ffffff00', '12345600', 'ffff7fff', 'ffffffff'], 'double': ['0000000000000000', '000000000000007f', '000000000000807f', 'ffffffffffff7f7f', 'ffffffffffffff7f', '0000000000000080', '0000000000008080', '0100000000000080', '0100000000008080', '0000000000004080', '000000000000c080', '0000000000000081', '0000000000008081', '0000000000004081', '000000000000c081', 'ffffffffffff1f82', 'ffffffffffff9f82', '0000000000002082', '000000000000a082', '0100000000002082', '010000000000a082', '0000000000006082', '000000000000e082', '0000000000fe7f8f', '0000000000feff8f', '0000000080fe7f8f', '0000000080feff8f', 'fffffffffffe7f8f', 'fffffffffffeff8f', '0000000000ff7f8f', '0000000000ffff8f', '0100000000ff7f8f', '0100000000ffff8f', '0000000000000090', '0000000000008090', '0000000040000090', '0000000040008090', 'ffffffff7f000090', 'ffffffff7f008090', '0000000080000090', '0000000080008090', '0100000080000090', '0100000080008090', '0000000000010090', '0000000000018090', '0000000000000091', '0000000000008091', 'ffffffffffff7f00', 'ffffffffffffff00', '123456789abcde00', 'ffffffffffff7fff', 'ffffffffffffffff']}

def cases():
    return {f'{kind}-op{op:02x}-{i:02d}':dict(kind=kind,op=op,raw=raw,initial=5)
            for kind,ops in [('single',(0x75,0x77)),('double',(0x76,0x78))]
            for op in ops for i,raw in enumerate(RAWS[kind])}


def payload(case):
    code = bytearray()
    def assign(at, raw):
        for i in range(0,len(raw),2): code.extend(b'\xc7\x06'+struct.pack('<HH',at+i,int.from_bytes(raw[i:i+2],'little')))
    def output(at, length): code.extend(b'\xbb\x01\x00\xb9'+struct.pack('<H',length)+b'\xba'+struct.pack('<H',at)+b'\xb4\x40\xcd\x21')
    raw=bytes.fromhex(case['raw']); at=0x1a if case['kind']=='single' else 0x16
    assign(0x1856,b'M4S!' if case['kind']=='single' else b'M4D!'); output(0x1856,4); output(0x234,4)
    assign(at,raw); output(at,len(raw)); output(0x1f,1)
    code.extend(bytes.fromhex('c6061f0004')); output(0x1f,1) # Declared diagnostic intervention, not an inferred normal caller.
    if case['op'] in (0x75,0x76): code.extend(b'\xbe'+struct.pack('<H',at))
    code.extend(bytes([0xcd,0x3f,case['op'],0x90,0x90]))
    code.extend(bytes.fromhex('891e5c18')); output(0x185c,2); output(at,len(raw)); output(0x234,4); output(0x1f,1)
    assign(0x1856,b'END!'); output(0x1856,4); code.extend(bytes.fromhex('b8004ccd21'))
    return bytes(code)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('destination',type=Path); p.add_argument('--scratch',required=True,type=Path); a=p.parse_args()
    out=a.destination.absolute(); scratch=a.scratch.absolute(); assert not out.exists() and not scratch.exists()
    initial=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes(); host=Path('/opt/homebrew/bin/dosbox-staging')
    assert (SHA(initial),SHA(runtime))==(INIT_SHA,RUNTIME_SHA)
    assert initial[0x23a:0x23f]==bytes.fromhex('cd3d439090')
    out.mkdir(parents=True); scratch.mkdir(); (out/'sources').mkdir(); shutil.copyfile(__file__,out/'sources'/Path(__file__).name)
    matrix=cases(); recipe=dict(recipe='brun30-int16-mode4-v1',cases=matrix,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
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

if __name__=='__main__': main()
