"""Capture one BRUN30 raw-DOUBLE division entry-state per disposable process.

Every first outcome (including timeout, partial trace and runtime error) is kept.
No observed artifact is retried or rewritten by this acquisition.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA = '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


MATRIX={'uf0-late-op88': {'op': 136,
                   'left': '0000000000000001',
                   'right': 'cdab896745230181',
                   'fac': '5aa5d5c33c918092',
                   'initial': 16777215},
 'uf0-late-op8a': {'op': 138,
                   'left': '0000000000000001',
                   'right': 'cdab896745230181',
                   'fac': '0000000000000001',
                   'initial': 16777215},
 'uf0-late-op8c': {'op': 140,
                   'left': '0000000000000001',
                   'right': 'cdab896745230181',
                   'fac': 'cdab896745230181',
                   'initial': 16777215},
 'uf0-early-op88': {'op': 136,
                    'left': '0000000000000001',
                    'right': 'cdab896745230182',
                    'fac': '5aa5d5c33c918092',
                    'initial': 16777215},
 'uf0-early-op8a': {'op': 138,
                    'left': '0000000000000001',
                    'right': 'cdab896745230182',
                    'fac': '0000000000000001',
                    'initial': 16777215},
 'uf0-early-op8c': {'op': 140,
                    'left': '0000000000000001',
                    'right': 'cdab896745230182',
                    'fac': 'cdab896745230182',
                    'initial': 16777215},
 'uf0-minimum-op88': {'op': 136,
                      'left': 'cdab896745230101',
                      'right': 'cdab896745230181',
                      'fac': '5aa5d5c33c918092',
                      'initial': 16777215},
 'uf0-minimum-op8a': {'op': 138,
                      'left': 'cdab896745230101',
                      'right': 'cdab896745230181',
                      'fac': 'cdab896745230101',
                      'initial': 16777215},
 'uf0-minimum-op8c': {'op': 140,
                      'left': 'cdab896745230101',
                      'right': 'cdab896745230181',
                      'fac': 'cdab896745230181',
                      'initial': 16777215},
 'uf1-late-op88': {'op': 136,
                   'left': '0000000000000001',
                   'right': 'ffffffffffff7f81',
                   'fac': '5aa5d5c33c918092',
                   'initial': 16777215},
 'uf1-late-op8a': {'op': 138,
                   'left': '0000000000000001',
                   'right': 'ffffffffffff7f81',
                   'fac': '0000000000000001',
                   'initial': 16777215},
 'uf1-late-op8c': {'op': 140,
                   'left': '0000000000000001',
                   'right': 'ffffffffffff7f81',
                   'fac': 'ffffffffffff7f81',
                   'initial': 16777215},
 'uf1-early-op88': {'op': 136,
                    'left': '0000000000000001',
                    'right': 'ffffffffffff7f82',
                    'fac': '5aa5d5c33c918092',
                    'initial': 16777215},
 'uf1-early-op8a': {'op': 138,
                    'left': '0000000000000001',
                    'right': 'ffffffffffff7f82',
                    'fac': '0000000000000001',
                    'initial': 16777215},
 'uf1-early-op8c': {'op': 140,
                    'left': '0000000000000001',
                    'right': 'ffffffffffff7f82',
                    'fac': 'ffffffffffff7f82',
                    'initial': 16777215},
 'uf1-minimum-op88': {'op': 136,
                      'left': 'ffffffffffff7f01',
                      'right': 'ffffffffffff7f81',
                      'fac': '5aa5d5c33c918092',
                      'initial': 16777215},
 'uf1-minimum-op8a': {'op': 138,
                      'left': 'ffffffffffff7f01',
                      'right': 'ffffffffffff7f81',
                      'fac': 'ffffffffffff7f01',
                      'initial': 16777215},
 'uf1-minimum-op8c': {'op': 140,
                      'left': 'ffffffffffff7f01',
                      'right': 'ffffffffffff7f81',
                      'fac': 'ffffffffffff7f81',
                      'initial': 16777215},
 'uf2-late-op88': {'op': 136,
                   'left': '0000000000000001',
                   'right': '0100000000000081',
                   'fac': '5aa5d5c33c918092',
                   'initial': 16777215},
 'uf2-late-op8a': {'op': 138,
                   'left': '0000000000000001',
                   'right': '0100000000000081',
                   'fac': '0000000000000001',
                   'initial': 16777215},
 'uf2-late-op8c': {'op': 140,
                   'left': '0000000000000001',
                   'right': '0100000000000081',
                   'fac': '0100000000000081',
                   'initial': 16777215},
 'uf2-early-op88': {'op': 136,
                    'left': '0000000000000001',
                    'right': '0100000000000082',
                    'fac': '5aa5d5c33c918092',
                    'initial': 16777215},
 'uf2-early-op8a': {'op': 138,
                    'left': '0000000000000001',
                    'right': '0100000000000082',
                    'fac': '0000000000000001',
                    'initial': 16777215},
 'uf2-early-op8c': {'op': 140,
                    'left': '0000000000000001',
                    'right': '0100000000000082',
                    'fac': '0100000000000082',
                    'initial': 16777215},
 'uf2-minimum-op88': {'op': 136,
                      'left': '0100000000000001',
                      'right': '0100000000000081',
                      'fac': '5aa5d5c33c918092',
                      'initial': 16777215},
 'uf2-minimum-op8a': {'op': 138,
                      'left': '0100000000000001',
                      'right': '0100000000000081',
                      'fac': '0100000000000001',
                      'initial': 16777215},
 'uf2-minimum-op8c': {'op': 140,
                      'left': '0100000000000001',
                      'right': '0100000000000081',
                      'fac': '0100000000000081',
                      'initial': 16777215},
 'uf3-late-op88': {'op': 136,
                   'left': '0000000000000001',
                   'right': '0706050403020181',
                   'fac': '5aa5d5c33c918092',
                   'initial': 16777215},
 'uf3-late-op8a': {'op': 138,
                   'left': '0000000000000001',
                   'right': '0706050403020181',
                   'fac': '0000000000000001',
                   'initial': 16777215},
 'uf3-late-op8c': {'op': 140,
                   'left': '0000000000000001',
                   'right': '0706050403020181',
                   'fac': '0706050403020181',
                   'initial': 16777215},
 'uf3-early-op88': {'op': 136,
                    'left': '0000000000000001',
                    'right': '0706050403020182',
                    'fac': '5aa5d5c33c918092',
                    'initial': 16777215},
 'uf3-early-op8a': {'op': 138,
                    'left': '0000000000000001',
                    'right': '0706050403020182',
                    'fac': '0000000000000001',
                    'initial': 16777215},
 'uf3-early-op8c': {'op': 140,
                    'left': '0000000000000001',
                    'right': '0706050403020182',
                    'fac': '0706050403020182',
                    'initial': 16777215},
 'uf3-minimum-op88': {'op': 136,
                      'left': '0706050403020101',
                      'right': '0706050403020181',
                      'fac': '5aa5d5c33c918092',
                      'initial': 16777215},
 'uf3-minimum-op8a': {'op': 138,
                      'left': '0706050403020101',
                      'right': '0706050403020181',
                      'fac': '0706050403020101',
                      'initial': 16777215},
 'uf3-minimum-op8c': {'op': 140,
                      'left': '0706050403020101',
                      'right': '0706050403020181',
                      'fac': '0706050403020181',
                      'initial': 16777215},
 'late-prior-fac0': {'op': 136,
                     'left': '0000000000000001',
                     'right': 'cdab896745230181',
                     'fac': '0000000000000000',
                     'initial': 5},
 'late-prior-fac1': {'op': 136,
                     'left': '0000000000000001',
                     'right': 'cdab896745230181',
                     'fac': '123456789abcde00',
                     'initial': 5},
 'late-prior-fac2': {'op': 136,
                     'left': '0000000000000001',
                     'right': 'cdab896745230181',
                     'fac': '0100000000008001',
                     'initial': 5},
 'late-prior-fac3': {'op': 136,
                     'left': '0000000000000001',
                     'right': 'cdab896745230181',
                     'fac': 'ffffffffffffffff',
                     'initial': 5}}

def cases():return {n:dict(c) for n,c in MATRIX.items()}


def payload(case):
    assert case['op'] in (0x88,0x8a,0x8c)
    code=bytearray()
    def assign(at,raw):
        for i in range(0,len(raw),2):code.extend(b'\xc7\x06'+struct.pack('<HH',at+i,int.from_bytes(raw[i:i+2],'little')))
    def output(at,length):code.extend(bytes.fromhex('bb0100b9')+struct.pack('<H',length)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    assign(0x1856,b'DDP1');output(0x1856,4);output(0x234,4)
    assign(0x16,bytes.fromhex(case['fac']));output(0x16,8)
    assign(0x1860,bytes.fromhex(case['left']));output(0x1860,8)
    assign(0x1868,bytes.fromhex(case['right']));output(0x1868,8);output(0x1f,1)
    code.extend(bytes.fromhex('be6018'))
    if case['op'] in (0x88,0x8a):code.extend(bytes.fromhex('bf6818'))
    code.extend(bytes([0xcd,0x3f,case['op'],0x88,0x88]))
    output(0x16,8);output(0x1860,8);output(0x1868,8);output(0x234,4);output(0x1f,1)
    assign(0x1856,b'END!');output(0x1856,4);code.extend(bytes.fromhex('b8004ccd21'))
    return bytes(code)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('destination',type=Path); p.add_argument('--scratch',required=True,type=Path); a=p.parse_args()
    out=a.destination.absolute(); scratch=a.scratch.absolute(); assert not out.exists() and not scratch.exists()
    initial=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes(); host=Path('/opt/homebrew/bin/dosbox-staging')
    assert (SHA(initial),SHA(runtime))==(INIT_SHA,RUNTIME_SHA)
    assert initial[0x23a:0x23f]==bytes.fromhex('cd3d439090')
    out.mkdir(parents=True); scratch.mkdir(); (out/'sources').mkdir(); shutil.copyfile(__file__,out/'sources'/Path(__file__).name)
    matrix=cases(); recipe=dict(recipe='brun30-divide-double-late-underflow-v1',cases=matrix,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
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
