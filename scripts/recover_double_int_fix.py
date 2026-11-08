"""Acquire bounded BRUN30 DOUBLE INT/FIX probes in disposable copied executables."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
CASES={'int-zero-aliases': ('int', 5, ['0000000000000000', 'ffffffffffff7f00', 'ffffffffffffff00', '123456789abcde00']), 'int-positive-subunit': ('int', 5, ['0000000000000080', '0000000000004080', 'ffffffffffff7f80', '0000000000000001']), 'int-negative-subunit': ('int', 5, ['0000000000008080', '000000000000c080', 'ffffffffffffff80', '0000000000008001']), 'int-positive-fractions': ('int', 5, ['0000000000004081', '0000000000002082', '0000000000003e85', '0000000000807f88']), 'int-negative-fractions': ('int', 5, ['000000000000c081', '000000000000a082', '000000000000be85', '000000000080ff88']), 'int-positive-byte-boundaries': ('int', 5, ['0000000000807f88', '0000000000400089', '0000000080ff7f90', '0000000040000091']), 'int-negative-byte-boundaries': ('int', 5, ['000000000080ff88', '0000000000408089', '0000000080ffff90', '0000000040008091']), 'int-positive-precision': ('int', 5, ['fcffffffffff7fb5', '02000000000000b6', 'ffffffffffff7fb7', 'ffffffffffff7fb8']), 'int-negative-precision': ('int', 5, ['fcffffffffffffb5', '02000000000080b6', 'ffffffffffffffb7', 'ffffffffffffffb8']), 'int-positive-large': ('int', 5, ['00000000000000b9', '01000000000000d1', 'ffffffffffff7fff', '01000000000000ff']), 'int-negative-large': ('int', 5, ['00000000000080b9', '01000000000080d1', 'ffffffffffffffff', '01000000000080ff']), 'int-mixed-history': ('int', 16777215, ['000000000080ff88', '0000000000004080', '123456789abcde00', '02000000000000b6']), 'fix-zero-aliases': ('fix', 5, ['0000000000000000', 'ffffffffffff7f00', 'ffffffffffffff00', '123456789abcde00']), 'fix-positive-subunit': ('fix', 5, ['0000000000000080', '0000000000004080', 'ffffffffffff7f80', '0000000000000001']), 'fix-negative-subunit': ('fix', 5, ['0000000000008080', '000000000000c080', 'ffffffffffffff80', '0000000000008001']), 'fix-positive-fractions': ('fix', 5, ['0000000000004081', '0000000000002082', '0000000000003e85', '0000000000807f88']), 'fix-negative-fractions': ('fix', 5, ['000000000000c081', '000000000000a082', '000000000000be85', '000000000080ff88']), 'fix-positive-byte-boundaries': ('fix', 5, ['0000000000807f88', '0000000000400089', '0000000080ff7f90', '0000000040000091']), 'fix-negative-byte-boundaries': ('fix', 5, ['000000000080ff88', '0000000000408089', '0000000080ffff90', '0000000040008091']), 'fix-positive-precision': ('fix', 5, ['fcffffffffff7fb5', '02000000000000b6', 'ffffffffffff7fb7', 'ffffffffffff7fb8']), 'fix-negative-precision': ('fix', 5, ['fcffffffffffffb5', '02000000000080b6', 'ffffffffffffffb7', 'ffffffffffffffb8']), 'fix-positive-large': ('fix', 5, ['00000000000000b9', '01000000000000d1', 'ffffffffffff7fff', '01000000000000ff']), 'fix-negative-large': ('fix', 5, ['00000000000080b9', '01000000000080d1', 'ffffffffffffffff', '01000000000080ff']), 'fix-mixed-history': ('fix', 16777215, ['000000000080ff88', '0000000000004080', '123456789abcde00', '02000000000000b6'])}
INIT_SHA='601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'


def payload(operation,arguments):
    code=bytearray()
    def emit(h):code.extend(bytes.fromhex(h))
    def store(at,raw):
        for offset in range(0,len(raw),2):code.extend(b'\xc7\x06'+struct.pack('<HH',at+offset,int.from_bytes(raw[offset:offset+2],'little')))
    def output(at,count=4):code.extend(bytes.fromhex('bb0100b9')+struct.pack('<H',count)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21'))
    store(0x1856,b'DINT'if operation=='int'else b'DFIX');output(0x1856);output(0x234)
    emit('b9');code.extend(struct.pack('<H',64//len(arguments)));loop=len(code);emit('51')
    for raw in arguments:
        store(0x16,bytes.fromhex(raw));output(0x16,8);emit('bb1600cd3d'+('04'if operation=='int'else'02')+'9090');output(0x234);output(0x16,8)
    emit('59497403e9');code.extend(struct.pack('<h',loop-(len(code)+2)))
    store(0x1856,b'END!');output(0x1856);emit('b8004ccd21');return bytes(code)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--scratch',type=Path,required=True);a=p.parse_args()
    out=a.destination.absolute();scratch=a.scratch.absolute();assert not out.exists()and not scratch.exists(),'fresh paths required'
    initial=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes();host=Path('/opt/homebrew/bin/dosbox-staging')
    assert(SHA(initial),SHA(runtime))==(INIT_SHA,RUNTIME_SHA)
    assert initial[0x23a:0x23f]==bytes.fromhex('cd3d439090')and runtime[0x375:0x37b]==bytes.fromhex('a2acb2ac0aad')
    out.mkdir();scratch.mkdir();(out/'sources').mkdir();shutil.copyfile(Path(__file__),out/'sources'/Path(__file__).name)
    recipe=dict(recipe='brun30-double-int-fix-v1',cases=CASES,samples=64,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=SHA(host.resolve().read_bytes()),source_sha256=SHA(Path(__file__).read_bytes()))
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
    for name,(operation,state,args)in CASES.items():
        temp=scratch/name;temp.mkdir();folder=out/name;folder.mkdir();stub=payload(operation,args)
        patched=bytearray(initial);patched[0x23a:0x23f]=b'\xe9'+struct.pack('<h',0x6d-0x3d)+b'\x90\x90';patched[0x26d:0x26d+len(stub)]=stub
        copied=bytearray(runtime);struct.pack_into('<I',copied,0x10234,state)
        (temp/'YT-INIT.EXE').write_bytes(patched);(temp/'BRUN30.EXE').write_bytes(copied)
        commands=['mount c '+str(temp),'c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit']
        argv=[str(host),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in('-c',c)]
        (folder/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n');(folder/'launch.json').write_text(json.dumps(argv,indent=2)+'\n')
        with(folder/'dosbox.stdout').open('wb')as stdout,(folder/'dosbox.stderr').open('wb')as stderr:
            child=subprocess.run(argv,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=stdout,stderr=stderr,timeout=20,check=True)
        for file in('TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'):shutil.copyfile(temp/file,folder/file)
        trace=(folder/'TRACE.BIN').read_bytes();completed=len(trace)==1292 and trace[:4]==(b'DINT'if operation=='int'else b'DFIX')and trace[-4:]==b'END!'
        assert(temp/'YT-INIT.EXE').read_bytes()==patched and(temp/'BRUN30.EXE').read_bytes()==copied
        meta=dict(recipe=recipe['recipe'],case=name,operation=operation,initial_state=state,arguments=args,exit_code=child.returncode,completed=completed,payload_hex=stub.hex(),copied_initializer_sha256=SHA(patched),copied_runtime_sha256=SHA(copied),files={p.name:SHA(p.read_bytes())for p in sorted(folder.iterdir())})
        (folder/'result.json').write_text(json.dumps(meta,indent=2)+'\n');print(name,'complete'if completed else 'native diagnostic stopped',flush=True)

if __name__=='__main__':main()
