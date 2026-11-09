"""Observe the selector after original startup in seven copied shipped programs.

Runtime and both original startup calls are untouched. Redirect only the first
user-body instruction to a snapshot-and-exit diagnostic; no gameplay is executed.
"""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
PROGRAMS=('LOCAL.EXE','PORTNAME.EXE','RMT-INIT.EXE','YT-INIT.EXE','YT.EXE','YTCONFIG.EXE','YTMAINT.EXE')
RUNTIME_SHA='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


def payload():
    code=bytearray()
    def assign(raw):
        for i in (0,2):code.extend(b'\xc7\x06'+struct.pack('<HH',0x1856+i,int.from_bytes(raw[i:i+2],'little')))
    def output(at,size):code.extend(bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    assign(b'MSEL');output(0x1856,4);output(0,64)
    assign(b'END!');output(0x1856,4);code.extend(bytes.fromhex('b8004ccd21'))
    return bytes(code)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--scratch',type=Path,required=True);a=p.parse_args()
    out=a.destination.absolute();scratch=a.scratch.absolute();assert not out.exists() and not scratch.exists()
    runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes();assert SHA(runtime)==RUNTIME_SHA
    originals={name:(ROOT/'archive/dos-original'/name).read_bytes() for name in PROGRAMS};host=Path('/opt/homebrew/bin/dosbox-staging')
    out.mkdir(parents=True);scratch.mkdir();(out/'sources').mkdir();shutil.copyfile(__file__,out/'sources'/Path(__file__).name)
    recipe=dict(recipe='brun30-normal-startup-selector-v1',programs={k:SHA(v) for k,v in originals.items()},runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');stub=payload()
    for name,original in originals.items():
        key=name.lower();folder=out/key;folder.mkdir();temp=scratch/key;temp.mkdir()
        header=struct.unpack_from('<H',original,8)[0]*16;assert original[header:header+2]==b'bm'
        startup=original[header+0x30:header+0x3a];assert startup[0]==startup[5]==0x9a
        patched=bytearray(original);patched[header+0x3a:header+0x3f]=bytes.fromhex('e930009090');patched[header+0x6d:header+0x6d+len(stub)]=stub
        assert patched[header+0x30:header+0x3a]==startup
        (temp/name).write_bytes(patched);(temp/'BRUN30.EXE').write_bytes(runtime)
        commands=['mount c '+str(temp),'c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG',name+' > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit']
        argv=[str(host),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in ('-c',c)]
        (folder/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n');(folder/'launch.json').write_text(json.dumps(argv,indent=2)+'\n')
        timeout=False
        with (folder/'dosbox.stdout').open('wb') as stdout,(folder/'dosbox.stderr').open('wb') as stderr:
            with subprocess.Popen(argv,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=stdout,stderr=stderr) as child:
                try:child.wait(timeout=20)
                except subprocess.TimeoutExpired:timeout=True;child.kill();child.wait()
                exit_code=child.returncode
        missing=[]
        for file in ('TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'):
            if (temp/file).exists():shutil.copyfile(temp/file,folder/file)
            else:missing.append(file)
        assert (temp/name).read_bytes()==patched and (temp/'BRUN30.EXE').read_bytes()==runtime
        meta=dict(recipe=recipe['recipe'],program=name,header=header,startup_hex=startup.hex(),original_body_hex=original[header+0x3a:header+0x3f].hex(),exit_code=exit_code,timeout=timeout,missing=missing,payload_hex=stub.hex(),copied_program_sha256=SHA(patched),runtime_sha256=SHA(runtime),files={p.name:SHA(p.read_bytes()) for p in sorted(folder.iterdir())})
        (folder/'result.json').write_text(json.dumps(meta,indent=2)+'\n');print(name,exit_code,'timeout' if timeout else 'returned',flush=True)

if __name__=='__main__':main()
