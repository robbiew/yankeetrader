"""Capture one BRUN30 raw-SINGLE subtraction entry-state per disposable process.

Every first outcome (including timeout, partial trace and runtime error) is kept.
No observed artifact is retried or rewritten by this acquisition.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA = '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


BASE_CASES={'both-zero': {'left': '00000000', 'right': '00000000', 'initial': 5}, 'zero-aliases': {'left': '12345600', 'right': 'ffffff00', 'initial': 5}, 'reverse-zero-aliases': {'left': 'ffffff00', 'right': '12345600', 'initial': 5}, 'left-zero-alias': {'left': '12345600', 'right': '00000081', 'initial': 5}, 'right-zero-alias': {'left': '00000081', 'right': 'ffffff00', 'initial': 5}, 'negative-plus-zero': {'left': '00008081', 'right': '12345600', 'initial': 5}, 'zero-plus-negative': {'left': 'ffffff00', 'right': '00008081', 'initial': 5}, 'min-plus-zero': {'left': '00000001', 'right': 'ffffff00', 'initial': 5}, 'one-plus-one': {'left': '00000081', 'right': '00000081', 'initial': 5}, 'negative-one-plus-one': {'left': '00008081', 'right': '00000081', 'initial': 5}, 'one-plus-negative-one': {'left': '00000081', 'right': '00008081', 'initial': 5}, 'negative-one-pair': {'left': '00008081', 'right': '00008081', 'initial': 5}, 'fraction-cancel': {'left': '00004081', 'right': '0000c081', 'initial': 5}, 'reverse-fraction-cancel': {'left': '0000c081', 'right': '00004081', 'initial': 5}, 'positive-sign-cross': {'left': '0000c081', 'right': '00000082', 'initial': 5}, 'negative-sign-cross': {'left': '00004081', 'right': '00008082', 'initial': 5}, 'same-exponent-difference': {'left': '00006081', 'right': '0000c081', 'initial': 5}, 'reverse-exponent-difference': {'left': '0000c081', 'right': '00006081', 'initial': 5}, 'integer-carry': {'left': 'ffff7f98', 'right': '00000081', 'initial': 5}, 'negative-integer-carry': {'left': 'ffffff98', 'right': '00008081', 'initial': 5}, 'small-lsb-odd': {'left': '01000098', 'right': '00000080', 'initial': 5}, 'negative-small-lsb-odd': {'left': '01008098', 'right': '00008080', 'initial': 5}, 'raw-align-positive': {'left': '56341291', 'right': 'ac681380', 'initial': 5}, 'raw-align-negative': {'left': '56349291', 'right': 'ac689380', 'initial': 5}, 'raw-align-sign-cross': {'left': '56341291', 'right': 'ac689380', 'initial': 5}, 'raw-align-reversed': {'left': 'ac689380', 'right': '56341291', 'initial': 5}, 'minimum-cancel': {'left': '00000001', 'right': '00008001', 'initial': 5}, 'minimum-one-bit': {'left': '01000001', 'right': '00008001', 'initial': 5}, 'minimum-negative-bit': {'left': '00000001', 'right': '01008001', 'initial': 5}, 'negative-minimum-one-bit': {'left': '01008001', 'right': '00000001', 'initial': 5}, 'minimum-near-binade': {'left': '00000002', 'right': 'ffffff01', 'initial': 5}, 'minimum-near-binade-reverse': {'left': 'ffffff01', 'right': '00000002', 'initial': 5}, 'max-pair': {'left': 'ffff7fff', 'right': 'ffff7fff', 'initial': 5}, 'negative-max-pair': {'left': 'ffffffff', 'right': 'ffffffff', 'initial': 5}, 'max-cancel': {'left': 'ffff7fff', 'right': 'ffffffff', 'initial': 5}, 'negative-max-cancel': {'left': 'ffffffff', 'right': 'ffff7fff', 'initial': 5}, 'max-ulp-difference': {'left': 'ffff7fff', 'right': 'feffffff', 'initial': 5}, 'reverse-max-ulp-difference': {'left': 'feffffff', 'right': 'ffff7fff', 'initial': 5}, 'max-with-min': {'left': 'ffff7fff', 'right': '00000001', 'initial': 5}, 'min-with-max': {'left': '00000001', 'right': 'ffff7fff', 'initial': 5}, 'max-round-overflow': {'left': 'ffff7fff', 'right': '000000e7', 'initial': 5}, 'negative-max-round-overflow': {'left': 'ffffffff', 'right': '000080e7', 'initial': 5}, 'max-below-round': {'left': 'ffff7fff', 'right': 'ffff7fe6', 'initial': 5}, 'max-negative-tiny': {'left': 'ffff7fff', 'right': '000080e7', 'initial': 5}, 'positive-lsb0-below': {'left': '00000081', 'right': 'ffff7f68', 'initial': 5}, 'positive-lsb0-tie': {'left': '00000081', 'right': '00000069', 'initial': 5}, 'positive-lsb0-above': {'left': '00000081', 'right': '01000069', 'initial': 5}, 'positive-lsb1-below': {'left': '01000081', 'right': 'ffff7f68', 'initial': 5}, 'positive-lsb1-tie': {'left': '01000081', 'right': '00000069', 'initial': 5}, 'positive-lsb1-above': {'left': '01000081', 'right': '01000069', 'initial': 5}, 'positive-gap23-add': {'left': '00000081', 'right': '0000406a', 'initial': 5}, 'positive-gap23-subtract': {'left': '00000081', 'right': '0000c06a', 'initial': 5}, 'positive-gap23-reversed': {'left': '0000c06a', 'right': '00000081', 'initial': 5}, 'positive-gap24-add': {'left': '00000081', 'right': '00004069', 'initial': 5}, 'positive-gap24-subtract': {'left': '00000081', 'right': '0000c069', 'initial': 5}, 'positive-gap24-reversed': {'left': '0000c069', 'right': '00000081', 'initial': 5}, 'positive-gap25-add': {'left': '00000081', 'right': '00004068', 'initial': 5}, 'positive-gap25-subtract': {'left': '00000081', 'right': '0000c068', 'initial': 5}, 'positive-gap25-reversed': {'left': '0000c068', 'right': '00000081', 'initial': 5}, 'positive-gap26-add': {'left': '00000081', 'right': '00004067', 'initial': 5}, 'positive-gap26-subtract': {'left': '00000081', 'right': '0000c067', 'initial': 5}, 'positive-gap26-reversed': {'left': '0000c067', 'right': '00000081', 'initial': 5}, 'negative-lsb0-below': {'left': '00008081', 'right': 'ffffff68', 'initial': 5}, 'negative-lsb0-tie': {'left': '00008081', 'right': '00008069', 'initial': 5}, 'negative-lsb0-above': {'left': '00008081', 'right': '01008069', 'initial': 5}, 'negative-lsb1-below': {'left': '01008081', 'right': 'ffffff68', 'initial': 5}, 'negative-lsb1-tie': {'left': '01008081', 'right': '00008069', 'initial': 5}, 'negative-lsb1-above': {'left': '01008081', 'right': '01008069', 'initial': 5}, 'negative-gap23-add': {'left': '00008081', 'right': '0000c06a', 'initial': 5}, 'negative-gap23-subtract': {'left': '00008081', 'right': '0000406a', 'initial': 5}, 'negative-gap23-reversed': {'left': '0000406a', 'right': '00008081', 'initial': 5}, 'negative-gap24-add': {'left': '00008081', 'right': '0000c069', 'initial': 5}, 'negative-gap24-subtract': {'left': '00008081', 'right': '00004069', 'initial': 5}, 'negative-gap24-reversed': {'left': '00004069', 'right': '00008081', 'initial': 5}, 'negative-gap25-add': {'left': '00008081', 'right': '0000c068', 'initial': 5}, 'negative-gap25-subtract': {'left': '00008081', 'right': '00004068', 'initial': 5}, 'negative-gap25-reversed': {'left': '00004068', 'right': '00008081', 'initial': 5}, 'negative-gap26-add': {'left': '00008081', 'right': '0000c067', 'initial': 5}, 'negative-gap26-subtract': {'left': '00008081', 'right': '00004067', 'initial': 5}, 'negative-gap26-reversed': {'left': '00004067', 'right': '00008081', 'initial': 5}, 'max-rng-cancel': {'left': '00006081', 'right': '0000e081', 'initial': 16777215}, 'max-rng-sticky': {'left': '00000081', 'right': '0000c068', 'initial': 16777215}}


def cases():
    matrix={}
    for op in (0x97,0x99,0x9b):
        for name,c in BASE_CASES.items():
            fac='5aa5d592' if op==0x97 else c['left'] if op==0x99 else c['right']
            matrix[f'op{op:02x}-{name}']=dict(op=op,**c,fac=fac)
    probes={'both-zero':('00000000','00000000'),'aliases':('12345600','ffffff00'),'cancel':('00004081','00004081'),'underflow':('01000001','00000001'),'reverse-underflow':('00000001','01000001')}
    for index,fac in enumerate(('00000000','12345600','01008001','ffffffff')):
        for name,(left,right) in probes.items():
            matrix[f'fac{index}-{name}']=dict(op=0x97,left=left,right=right,initial=16777215,fac=fac)
    return matrix


def payload(case):
    code=bytearray()
    def assign(at,raw):
        for i in (0,2):code.extend(b'\xc7\x06'+struct.pack('<HH',at+i,int.from_bytes(raw[i:i+2],'little')))
    def output(at,length):code.extend(bytes.fromhex('bb0100b9')+struct.pack('<H',length)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    assign(0x1856,b'SUB1');output(0x1856,4);output(0x234,4)
    assign(0x1a,bytes.fromhex(case['fac']));output(0x1a,4)
    assign(0x1860,bytes.fromhex(case['left']));output(0x1860,4)
    assign(0x1864,bytes.fromhex(case['right']));output(0x1864,4);output(0x1f,1)
    code.extend(bytes.fromhex('be6018'))
    if case['op'] in (0x97,0x99):code.extend(bytes.fromhex('bf6418'))
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
    matrix=cases(); recipe=dict(recipe='brun30-sub-entry-state-v1',cases=matrix,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
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
