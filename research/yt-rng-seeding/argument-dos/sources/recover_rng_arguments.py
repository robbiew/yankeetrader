"""Acquire bounded BRUN30 RND(argument) probes in disposable copied executables."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
CASES={
 'zero-state-zero':(0,['00000000']), 'zero-state-five':(5,['00000000']),
 'zero-state-max':(0xffffff,['00000000']), 'residual-zero':(0x1234ab,['ffff7f00']),
 'negative-zero':(0x1234ab,['fffffe00']), 'positive-one':(5,['00000081']),
 'positive-half':(5,['00000080']), 'positive-large':(0xffffff,['00004987']),
 'negative-one':(5,['00008081']), 'negative-one-old-state':(0x1234ab,['00008081']),
 'negative-half':(5,['00008080']), 'negative-large':(5,['0000c987']),
 'negative-low-carry':(5,['ffff8081']), 'negative-wrap':(5,['ffffffff']),
 'mixed':(5,['00000000','00000081','00008081','fffffe00']),
 'mixed-old-state':(0x1234ab,['00004987','0000c987','00000000','00000081']),
}
INIT_SHA='601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


def payload(arguments):
    code=bytearray()
    def emit(h):code.extend(bytes.fromhex(h))
    def store(at,raw):
        for offset in(0,2):code.extend(b'\xc7\x06'+struct.pack('<HH',at+offset,int.from_bytes(raw[offset:offset+2],'little')))
    def output(at):code.extend(bytes.fromhex('bb0100b90400ba')+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    store(0x1856,b'RND2');output(0x1856);output(0x234)
    emit('b9');code.extend(struct.pack('<H',64//len(arguments)));loop=len(code);emit('51')
    for raw in arguments:
        store(0x1a,bytes.fromhex(raw));output(0x1a);emit('bb1a00cd3d339090');output(0x234);output(0x1a)
    emit('59497403e9');code.extend(struct.pack('<h',loop-(len(code)+2)))
    store(0x1856,b'END!');output(0x1856);emit('b8004ccd21');return bytes(code)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--scratch',type=Path,required=True);a=p.parse_args()
    out=a.destination.absolute();scratch=a.scratch.absolute();assert not out.exists()and not scratch.exists(),'fresh paths required'
    initial=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes();host=Path('/opt/homebrew/bin/dosbox-staging')
    assert(SHA(initial),SHA(runtime))==(INIT_SHA,RUNTIME_SHA)
    assert initial[0x23a:0x23f]==bytes.fromhex('cd3d439090')and runtime[0x3d7:0x3db]==bytes.fromhex('c7b2c2b2')
    out.mkdir();scratch.mkdir();(out/'sources').mkdir();shutil.copyfile(Path(__file__),out/'sources'/Path(__file__).name)
    recipe=dict(recipe='brun30-rnd-arguments-v1',cases=CASES,samples=64,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
    for name,(state,args)in CASES.items():
        temp=scratch/name;temp.mkdir();folder=out/name;folder.mkdir();stub=payload(args)
        patched=bytearray(initial);patched[0x23a:0x23f]=b'\xe9'+struct.pack('<h',0x6d-0x3d)+b'\x90\x90';patched[0x26d:0x26d+len(stub)]=stub
        copied=bytearray(runtime);struct.pack_into('<I',copied,0x10234,state)
        (temp/'YT-INIT.EXE').write_bytes(patched);(temp/'BRUN30.EXE').write_bytes(copied)
        commands=['mount c '+str(temp),'c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit']
        argv=[str(host),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in('-c',c)]
        (folder/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n');(folder/'launch.json').write_text(json.dumps(argv,indent=2)+'\n')
        with(folder/'dosbox.stdout').open('wb')as stdout,(folder/'dosbox.stderr').open('wb')as stderr:
            child=subprocess.run(argv,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=stdout,stderr=stderr,timeout=20,check=True)
        for file in('TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'):shutil.copyfile(temp/file,folder/file)
        trace=(folder/'TRACE.BIN').read_bytes();assert len(trace)==780 and trace[:4]==b'RND2'and trace[-4:]==b'END!','complete diagnostic trace'
        assert(temp/'YT-INIT.EXE').read_bytes()==patched and(temp/'BRUN30.EXE').read_bytes()==copied
        meta=dict(recipe=recipe['recipe'],case=name,initial_state=state,arguments=args,exit_code=child.returncode,payload_hex=stub.hex(),copied_initializer_sha256=SHA(patched),copied_runtime_sha256=SHA(copied),files={p.name:SHA(p.read_bytes())for p in sorted(folder.iterdir())})
        (folder/'result.json').write_text(json.dumps(meta,indent=2)+'\n');print(name,'complete',flush=True)

if __name__=='__main__':main()
