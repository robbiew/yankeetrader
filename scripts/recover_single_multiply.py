"""Capture one BRUN30 raw-SINGLE multiplication entry-state per disposable process.

Every first outcome (including timeout, partial trace and runtime error) is kept.
No observed artifact is retried or rewritten by this acquisition.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA = '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


BASE_CASES={'both-zero': {'left': '00000000', 'right': '00000000', 'initial': 5}, 'aliases': {'left': '12345600', 'right': 'ffffff00', 'initial': 5}, 'left-zero': {'left': '12345600', 'right': '00008081', 'initial': 5}, 'right-zero': {'left': '00004081', 'right': 'ffffff00', 'initial': 5}, 'max-zero': {'left': 'ffff7fff', 'right': '12345600', 'initial': 5}, 'zero-max': {'left': 'ffffff00', 'right': 'ffffffff', 'initial': 5}, 'one': {'left': '00000081', 'right': '00000081', 'initial': 5}, 'one-negative': {'left': '00008081', 'right': '00000081', 'initial': 5}, 'fraction': {'left': '00004081', 'right': '00004081', 'initial': 5}, 'fraction-negative': {'left': '0000c081', 'right': '00004081', 'initial': 5}, 'raw-align': {'left': '56341281', 'right': 'ac681381', 'initial': 5}, 'raw-align-negative': {'left': '56349281', 'right': 'ac681381', 'initial': 5}, 'tie47-odd': {'left': '00004081', 'right': '01000081', 'initial': 5}, 'tie47-odd-negative': {'left': '0000c081', 'right': '01000081', 'initial': 5}, 'tie47-even': {'left': '00004081', 'right': '03000081', 'initial': 5}, 'tie47-even-negative': {'left': '0000c081', 'right': '03000081', 'initial': 5}, 'below47': {'left': 'ffff3f81', 'right': '01000081', 'initial': 5}, 'below47-negative': {'left': 'ffffbf81', 'right': '01000081', 'initial': 5}, 'above47': {'left': '01004081', 'right': '01000081', 'initial': 5}, 'above47-negative': {'left': '0100c081', 'right': '01000081', 'initial': 5}, 'tie48-odd': {'left': '00004081', 'right': '02004081', 'initial': 5}, 'tie48-odd-negative': {'left': '0000c081', 'right': '02004081', 'initial': 5}, 'tie48-even': {'left': '00004081', 'right': '06004081', 'initial': 5}, 'tie48-even-negative': {'left': '0000c081', 'right': '06004081', 'initial': 5}, 'below48': {'left': 'ffff7f81', 'right': '01000081', 'initial': 5}, 'below48-negative': {'left': 'ffffff81', 'right': '01000081', 'initial': 5}, 'above48': {'left': '01004081', 'right': '01004081', 'initial': 5}, 'above48-negative': {'left': '0100c081', 'right': '01004081', 'initial': 5}, 'round-carry': {'left': '01000081', 'right': 'feff7f81', 'initial': 5}, 'round-carry-negative': {'left': '01008081', 'right': 'feff7f81', 'initial': 5}, 'negative-right': {'left': '00004081', 'right': '01008081', 'initial': 5}, 'both-negative': {'left': '0000c081', 'right': '0200c081', 'initial': 5}, 'raw-reversed': {'left': 'ac681381', 'right': '56341281', 'initial': 5}, 'ties-reversed': {'left': '03000081', 'right': '00004081', 'initial': 5}, 'million-half': {'left': '00247494', 'right': '00000080', 'initial': 5}, 'thousand-tenth': {'left': '00007a8a', 'right': 'cdcc4c7d', 'initial': 5}, 'exp-sum128-800000': {'left': '00000040', 'right': '00000040', 'initial': 5}, 'exp-sum128-c00000': {'left': '00004040', 'right': '00004040', 'initial': 5}, 'exp-sum129-800000': {'left': '00000040', 'right': '00000041', 'initial': 5}, 'exp-sum129-c00000': {'left': '00004040', 'right': '00004041', 'initial': 5}, 'exp-sum130-800000': {'left': '00000041', 'right': '00000041', 'initial': 5}, 'exp-sum130-c00000': {'left': '00004041', 'right': '00004041', 'initial': 5}, 'exp-sum383-800000': {'left': '000000bf', 'right': '000000c0', 'initial': 5}, 'exp-sum383-c00000': {'left': '000040bf', 'right': '000040c0', 'initial': 5}, 'exp-sum384-800000': {'left': '000000c0', 'right': '000000c0', 'initial': 5}, 'exp-sum384-c00000': {'left': '000040c0', 'right': '000040c0', 'initial': 5}, 'exp-sum385-800000': {'left': '000000c0', 'right': '000000c1', 'initial': 5}, 'exp-sum385-c00000': {'left': '000040c0', 'right': '000040c1', 'initial': 5}, 'flush-before-round': {'left': '01000040', 'right': 'feff7f41', 'initial': 5}, 'reverse-flush': {'left': 'feff7f41', 'right': '01000040', 'initial': 5}, 'negative-flush': {'left': '01008040', 'right': 'feff7f41', 'initial': 5}, 'round-overflow': {'left': '010000c0', 'right': 'feff7fc0', 'initial': 5}, 'below-upper-range': {'left': 'ffff7fbf', 'right': 'ffff7fc0', 'initial': 5}, 'min-max': {'left': '00000001', 'right': 'ffff7fff', 'initial': 5}, 'max-min': {'left': 'ffff7fff', 'right': '00000001', 'initial': 5}, 'max-one': {'left': 'ffff7fff', 'right': '00000081', 'initial': 5}, 'min-one': {'left': '00000001', 'right': '00000081', 'initial': 5}, 'min-half': {'left': '00000001', 'right': '00000080', 'initial': 5}, 'max-two': {'left': 'ffff7fff', 'right': '00000082', 'initial': 5}, 'max-rng-tie': {'left': '00004081', 'right': '01000081', 'initial': 16777215}, 'max-rng-zero': {'left': '12345600', 'right': 'ffffff00', 'initial': 16777215}}


def cases():
    result={f'op91-{n}':dict(op=0x91,**c,fac=c['left']) for n,c in BASE_CASES.items()}
    names=('both-zero','aliases','left-zero','right-zero','max-zero','min-half','flush-before-round','negative-flush','exp-sum129-c00000','exp-sum128-c00000','fraction','tie47-odd','tie48-even','round-overflow','max-two','both-negative')
    for op in (0x8f,0x93):
        for n in names:
            c=BASE_CASES[n];result[f'op{op:02x}-{n}']=dict(op=op,**c,fac='5aa5d592' if op==0x8f else c['right'])
    for index,fac in enumerate(('00000000','12345600','01008001','ffffffff')):
        for n in ('aliases','right-zero','flush-before-round','min-half'):
            result[f'fac{index}-{n}']=dict(op=0x8f,**dict(BASE_CASES[n],initial=16777215),fac=fac)
    return result


def payload(case):
    code=bytearray()
    def assign(at,raw):
        for i in (0,2):code.extend(b'\xc7\x06'+struct.pack('<HH',at+i,int.from_bytes(raw[i:i+2],'little')))
    def output(at,length):code.extend(bytes.fromhex('bb0100b9')+struct.pack('<H',length)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    assign(0x1856,b'MUL1');output(0x1856,4);output(0x234,4)
    assign(0x1a,bytes.fromhex(case['fac']));output(0x1a,4)
    assign(0x1860,bytes.fromhex(case['left']));output(0x1860,4)
    assign(0x1864,bytes.fromhex(case['right']));output(0x1864,4);output(0x1f,1)
    code.extend(bytes.fromhex('be6018'))
    if case['op'] in (0x8f,0x91):code.extend(bytes.fromhex('bf6418'))
    code.extend(bytes([0xcd,0x3f,case['op'],0x90,0x90]))
    output(0x1a,4);output(0x1860,4);output(0x1864,4);output(0x234,4);output(0x1f,1)
    assign(0x1856,b'END!');output(0x1856,4);code.extend(bytes.fromhex('b8004ccd21'))
    return bytes(code)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('destination',type=Path); p.add_argument('--scratch',required=True,type=Path); a=p.parse_args()
    out=a.destination.absolute(); scratch=a.scratch.absolute(); assert not out.exists() and not scratch.exists()
    initial=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes(); host=Path('/opt/homebrew/bin/dosbox-staging')
    assert (SHA(initial),SHA(runtime))==(INIT_SHA,RUNTIME_SHA)
    assert initial[0x23a:0x23f]==bytes.fromhex('cd3d439090')
    out.mkdir(parents=True); scratch.mkdir(); (out/'sources').mkdir(); shutil.copyfile(__file__,out/'sources'/Path(__file__).name)
    matrix=cases(); recipe=dict(recipe='brun30-multiply-entry-state-v1',cases=matrix,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
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
