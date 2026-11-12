"""Capture one BRUN30 raw-DOUBLE subtraction entry-state per disposable process.

Every first outcome (including timeout, partial trace and runtime error) is kept.
No observed artifact is retried or rewritten by this acquisition.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA = '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


BASE_CASES={'both-zero': {'left': '0000000000000000', 'right': '0000000000008000', 'initial': 5},
 'aliases': {'left': '123456789abcde00', 'right': 'ffffffffffff7f00', 'initial': 5},
 'left-zero': {'left': '123456789abcde00', 'right': '0000000000000081', 'initial': 5},
 'right-zero': {'left': '0000000000000081', 'right': '123456789abc5e00', 'initial': 5},
 'max-zero': {'left': 'ffffffffffff7fff', 'right': '123456789abc5e00', 'initial': 5},
 'zero-max': {'left': '123456789abcde00', 'right': 'ffffffffffff7fff', 'initial': 5},
 'one': {'left': '0000000000000081', 'right': '0000000000008081', 'initial': 5},
 'one-negative': {'left': '0000000000008081', 'right': '0000000000000081', 'initial': 5},
 'fraction': {'left': '0000000000004081', 'right': '000000000000c081', 'initial': 5},
 'cancel': {'left': '0000000000004081', 'right': '0000000000004081', 'initial': 5},
 'cancel-reverse': {'left': '000000000000c081', 'right': '000000000000c081', 'initial': 5},
 'sign-cross': {'left': '0000000000002081', 'right': '0000000000004081', 'initial': 5},
 'raw': {'left': 'cdab896745230181', 'right': '436587a9cbedef81', 'initial': 5},
 'raw-reversed': {'left': '436587a9cbed6f81', 'right': 'cdab896745238181', 'initial': 5},
 'minimum-one-bit': {'left': '0100000000000001', 'right': '0000000000000001', 'initial': 5},
 'minimum-cancel': {'left': '0100000000000001', 'right': '0100000000000001', 'initial': 5},
 'minimum-binade': {'left': 'ffffffffffff7f01', 'right': '0000000000008001', 'initial': 5},
 'max-min': {'left': 'ffffffffffff7fff', 'right': '0000000000008001', 'initial': 5},
 'overflow': {'left': 'ffffffffffff7fff', 'right': 'ffffffffffffffff', 'initial': 5},
 'negative-overflow': {'left': 'ffffffffffffffff', 'right': 'ffffffffffff7fff', 'initial': 5},
 'overflow-round': {'left': 'ffffffffffff7fff', 'right': '00000000000080c7', 'initial': 5},
 'max-in-range': {'left': 'ffffffffffff7fff', 'right': '00000000000080c6', 'initial': 5},
 'high-cancel': {'left': 'ffffffffffff7fff', 'right': 'ffffffffffff7fff', 'initial': 5},
 'half-odd0-tail0': {'left': '0000000000000081', 'right': '0000000000008049', 'initial': 5},
 'half-odd0-tail1': {'left': '0000000000000081', 'right': '0100000000008049', 'initial': 5},
 'half-odd0-tail36028797018963967': {'left': '0000000000000081',
                                     'right': 'ffffffffffffff49',
                                     'initial': 5},
 'half-odd1-tail0': {'left': '0100000000000081', 'right': '0000000000008049', 'initial': 5},
 'half-odd1-tail1': {'left': '0100000000000081', 'right': '0100000000008049', 'initial': 5},
 'half-odd1-tail36028797018963967': {'left': '0100000000000081',
                                     'right': 'ffffffffffffff49',
                                     'initial': 5},
 'same-gap0': {'left': 'cdab896745230181', 'right': '436587a9cbedef81', 'initial': 5},
 'opposite-gap0': {'left': 'cdab896745230181', 'right': '436587a9cbed6f81', 'initial': 5},
 'same-gap1': {'left': 'cdab896745230181', 'right': '436587a9cbedef80', 'initial': 5},
 'opposite-gap1': {'left': 'cdab896745230181', 'right': '436587a9cbed6f80', 'initial': 5},
 'same-gap5': {'left': 'cdab896745230181', 'right': '436587a9cbedef7c', 'initial': 5},
 'opposite-gap5': {'left': 'cdab896745230181', 'right': '436587a9cbed6f7c', 'initial': 5},
 'same-gap6': {'left': 'cdab896745230181', 'right': '436587a9cbedef7b', 'initial': 5},
 'opposite-gap6': {'left': 'cdab896745230181', 'right': '436587a9cbed6f7b', 'initial': 5},
 'same-gap7': {'left': 'cdab896745230181', 'right': '436587a9cbedef7a', 'initial': 5},
 'opposite-gap7': {'left': 'cdab896745230181', 'right': '436587a9cbed6f7a', 'initial': 5},
 'same-gap8': {'left': 'cdab896745230181', 'right': '436587a9cbedef79', 'initial': 5},
 'opposite-gap8': {'left': 'cdab896745230181', 'right': '436587a9cbed6f79', 'initial': 5},
 'same-gap13': {'left': 'cdab896745230181', 'right': '436587a9cbedef74', 'initial': 5},
 'opposite-gap13': {'left': 'cdab896745230181', 'right': '436587a9cbed6f74', 'initial': 5},
 'same-gap14': {'left': 'cdab896745230181', 'right': '436587a9cbedef73', 'initial': 5},
 'opposite-gap14': {'left': 'cdab896745230181', 'right': '436587a9cbed6f73', 'initial': 5},
 'same-gap15': {'left': 'cdab896745230181', 'right': '436587a9cbedef72', 'initial': 5},
 'opposite-gap15': {'left': 'cdab896745230181', 'right': '436587a9cbed6f72', 'initial': 5},
 'same-gap16': {'left': 'cdab896745230181', 'right': '436587a9cbedef71', 'initial': 5},
 'opposite-gap16': {'left': 'cdab896745230181', 'right': '436587a9cbed6f71', 'initial': 5},
 'same-gap17': {'left': 'cdab896745230181', 'right': '436587a9cbedef70', 'initial': 5},
 'opposite-gap17': {'left': 'cdab896745230181', 'right': '436587a9cbed6f70', 'initial': 5},
 'same-gap31': {'left': 'cdab896745230181', 'right': '436587a9cbedef62', 'initial': 5},
 'opposite-gap31': {'left': 'cdab896745230181', 'right': '436587a9cbed6f62', 'initial': 5},
 'same-gap32': {'left': 'cdab896745230181', 'right': '436587a9cbedef61', 'initial': 5},
 'opposite-gap32': {'left': 'cdab896745230181', 'right': '436587a9cbed6f61', 'initial': 5},
 'same-gap33': {'left': 'cdab896745230181', 'right': '436587a9cbedef60', 'initial': 5},
 'opposite-gap33': {'left': 'cdab896745230181', 'right': '436587a9cbed6f60', 'initial': 5},
 'same-gap47': {'left': 'cdab896745230181', 'right': '436587a9cbedef52', 'initial': 5},
 'opposite-gap47': {'left': 'cdab896745230181', 'right': '436587a9cbed6f52', 'initial': 5},
 'same-gap48': {'left': 'cdab896745230181', 'right': '436587a9cbedef51', 'initial': 5},
 'opposite-gap48': {'left': 'cdab896745230181', 'right': '436587a9cbed6f51', 'initial': 5},
 'same-gap49': {'left': 'cdab896745230181', 'right': '436587a9cbedef50', 'initial': 5},
 'opposite-gap49': {'left': 'cdab896745230181', 'right': '436587a9cbed6f50', 'initial': 5},
 'same-gap53': {'left': 'cdab896745230181', 'right': '436587a9cbedef4c', 'initial': 5},
 'opposite-gap53': {'left': 'cdab896745230181', 'right': '436587a9cbed6f4c', 'initial': 5},
 'same-gap54': {'left': 'cdab896745230181', 'right': '436587a9cbedef4b', 'initial': 5},
 'opposite-gap54': {'left': 'cdab896745230181', 'right': '436587a9cbed6f4b', 'initial': 5},
 'same-gap55': {'left': 'cdab896745230181', 'right': '436587a9cbedef4a', 'initial': 5},
 'opposite-gap55': {'left': 'cdab896745230181', 'right': '436587a9cbed6f4a', 'initial': 5},
 'same-gap56': {'left': 'cdab896745230181', 'right': '436587a9cbedef49', 'initial': 5},
 'opposite-gap56': {'left': 'cdab896745230181', 'right': '436587a9cbed6f49', 'initial': 5},
 'same-gap57': {'left': 'cdab896745230181', 'right': '436587a9cbedef48', 'initial': 5},
 'opposite-gap57': {'left': 'cdab896745230181', 'right': '436587a9cbed6f48', 'initial': 5},
 'same-gap58': {'left': 'cdab896745230181', 'right': '436587a9cbedef47', 'initial': 5},
 'opposite-gap58': {'left': 'cdab896745230181', 'right': '436587a9cbed6f47', 'initial': 5},
 'boundary-opposite-gap55': {'left': '0000000000000081', 'right': '000000000000404a', 'initial': 5},
 'boundary-negative-gap55': {'left': '0000000000008081', 'right': '000000000000c04a', 'initial': 5},
 'boundary-reverse-gap55': {'left': '000000000000c04a', 'right': '0000000000008081', 'initial': 5},
 'boundary-opposite-gap56': {'left': '0000000000000081', 'right': '0000000000004049', 'initial': 5},
 'boundary-negative-gap56': {'left': '0000000000008081', 'right': '000000000000c049', 'initial': 5},
 'boundary-reverse-gap56': {'left': '000000000000c049', 'right': '0000000000008081', 'initial': 5},
 'boundary-opposite-gap57': {'left': '0000000000000081', 'right': '0000000000004048', 'initial': 5},
 'boundary-negative-gap57': {'left': '0000000000008081', 'right': '000000000000c048', 'initial': 5},
 'boundary-reverse-gap57': {'left': '000000000000c048', 'right': '0000000000008081', 'initial': 5},
 'boundary-opposite-gap58': {'left': '0000000000000081', 'right': '0000000000004047', 'initial': 5},
 'boundary-negative-gap58': {'left': '0000000000008081', 'right': '000000000000c047', 'initial': 5},
 'boundary-reverse-gap58': {'left': '000000000000c047', 'right': '0000000000008081', 'initial': 5},
 'max-rng-cancel': {'left': '0100000000000081', 'right': '0100000000000081', 'initial': 16777215},
 'max-rng-half': {'left': '0100000000000081', 'right': '0100000000008049', 'initial': 16777215},
 'reverse-aliases': {'left': 'ffffffffffffff00', 'right': '123456789abcde00', 'initial': 5},
 'sub-one-three': {'left': '0000000000000081', 'right': '0000000000004082', 'initial': 5},
 'sub-three-one': {'left': '0000000000004082', 'right': '0000000000000081', 'initial': 16777215}}


def cases():
    result={f'op9a-{n}':dict(op=0x9a,**c,fac=c['left']) for n,c in BASE_CASES.items()}
    names=('both-zero','aliases','left-zero','right-zero','max-zero','cancel','cancel-reverse','minimum-one-bit','minimum-cancel','half-odd0-tail0','half-odd1-tail0','half-odd0-tail1','boundary-opposite-gap56','boundary-opposite-gap57','sign-cross','overflow','overflow-round','negative-overflow','raw','raw-reversed')
    for op in (0x98,0x9c):
        for n in names:
            c=BASE_CASES[n];result[f'op{op:02x}-{n}']=dict(op=op,**c,fac='5aa5d5c33c918092' if op==0x98 else c['right'])
    for index,fac in enumerate(('0000000000000000','123456789abcde00','0100000000008001','ffffffffffffffff')):
        for n in ('aliases','cancel','minimum-one-bit','minimum-cancel'):
            result[f'fac{index}-{n}']=dict(op=0x98,**dict(BASE_CASES[n],initial=16777215),fac=fac)
    return result


def payload(case):
    assert case['op'] in (0x98,0x9a,0x9c)
    code=bytearray()
    def assign(at,raw):
        for i in range(0,len(raw),2):code.extend(b'\xc7\x06'+struct.pack('<HH',at+i,int.from_bytes(raw[i:i+2],'little')))
    def output(at,length):code.extend(bytes.fromhex('bb0100b9')+struct.pack('<H',length)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    assign(0x1856,b'DSD1');output(0x1856,4);output(0x234,4)
    assign(0x16,bytes.fromhex(case['fac']));output(0x16,8)
    assign(0x1860,bytes.fromhex(case['left']));output(0x1860,8)
    assign(0x1868,bytes.fromhex(case['right']));output(0x1868,8);output(0x1f,1)
    code.extend(bytes.fromhex('be6018'))
    if case['op'] in (0x98,0x9a):code.extend(bytes.fromhex('bf6818'))
    code.extend(bytes([0xcd,0x3f,case['op'],0x90,0x90]))
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
    matrix=cases(); recipe=dict(recipe='brun30-subtract-double-entry-state-v1',cases=matrix,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
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
