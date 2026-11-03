"""Capture raw BRUN30 seed/FAC records using a declared copied-initializer probe."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
SAMPLES=256

def payload(mode,raw):
    code=bytearray()
    def emit(h):code.extend(bytes.fromhex(h))
    def words(address,value):
        emit('c706');code.extend(struct.pack('<HH',address,int.from_bytes(value[:2],'little')))
        emit('c706');code.extend(struct.pack('<HH',address+2,int.from_bytes(value[2:],'little')))
    def write(address):
        emit('bb0100 b90400 ba');code.extend(struct.pack('<H',address));emit('b440 cd21')
    words(0x1856,b'RNG1');write(0x1856);write(0x234)
    if mode=='timer':emit('cd3d439090')
    else:words(0x1a,bytes.fromhex(raw or '00000000'))
    write(0x1a)
    if mode!='unseeded':emit('cd3fb19090')
    write(0x1a)
    if mode!='unseeded':emit('bb1a00 cd3e099090')
    write(0x234)
    emit('b9');code.extend(struct.pack('<H',SAMPLES));loop=len(code)
    emit('51 cd3d349090');write(0x234);write(0x1a);emit('59 e2')
    distance=loop-(len(code)+1);assert -128<=distance<0
    code.extend(struct.pack('b',distance))
    words(0x1856,b'END!');write(0x1856);emit('b8004c cd21')
    return bytes(code)

def run(destination,cases):
    destination.mkdir(parents=True,exist_ok=False)
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes()
    runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert original[0x23a:0x23f]==bytes.fromhex('cd3d439090')
    load=0x6d
    for case in cases:
        d=destination/case['name'];d.mkdir()
        stub=payload(case['mode'],case.get('raw'))
        patched=bytearray(original)
        patched[0x23a:0x23f]=b'\xe9'+struct.pack('<h',load-0x3d)+b'\x90\x90'
        patched[512+load:512+load+len(stub)]=stub
        copied=bytearray(runtime);struct.pack_into('<I',copied,0x10234,case.get('state',5))
        (d/'YT-INIT.EXE').write_bytes(patched);(d/'BRUN30.EXE').write_bytes(copied)
        commands=['mount c '+str(d),'c:','date '+case.get('date','11/02/2026'),'time '+case.get('time','00:00:00'),
                  'date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init > TRACE.BIN','echo PROBE_RETURNED > RETURN.LOG','exit']
        (d/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
        with (d/'dosbox.log').open('w') as out:
            subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for cmd in commands for x in ('-c',cmd)],
                           env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=out,stderr=subprocess.STDOUT,check=True,timeout=60)
        trace=(d/'TRACE.BIN').read_bytes()
        assert len(trace)==24+8*SAMPLES and trace[:4]==b'RNG1' and trace[-4:]==b'END!',(case,len(trace),trace[:80])
        keep={'TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','COMMANDS.TXT','dosbox.log'}
        meta={**case,'recipe':'qb-rng-raw-v1','samples':SAMPLES,'original_initializer_sha256':SHA(original),'original_runtime_sha256':SHA(runtime),
              'copied_initializer_sha256':SHA(patched),'copied_runtime_sha256':SHA(copied),'payload_hex':stub.hex(),
              'payload_file_offset':512+load,'payload_code_offset':load,'files':{p:SHA((d/p).read_bytes()) for p in sorted(keep)}}
        (d/'result.json').write_text(json.dumps(meta,indent=2)+'\n')
        for p in d.iterdir():
            if p.name not in keep|{'result.json'}:p.unlink()
        print(case['name'],trace[:20].hex(),flush=True)

CASES=[{'name':'unseeded-5','mode':'unseeded'},
       {'name':'timer-midnight','mode':'timer'}, {'name':'timer-repeat','mode':'timer'},
       {'name':'timer-plus-one','mode':'timer','time':'00:00:01'}, {'name':'timer-noon','mode':'timer','time':'12:34:00'},
       {'name':'timer-next-date','mode':'timer','date':'11/03/2026'},
       {'name':'raw-zero','mode':'raw','raw':'00000000'}, {'name':'raw-zero-residue','mode':'raw','raw':'00004800'},
       {'name':'raw-100-half','mode':'raw','raw':'00004987'}, {'name':'raw-negative-100-half','mode':'raw','raw':'0000c987'},
       {'name':'raw-preserved-low','mode':'raw','raw':'00004987','state':0x1234ab},
       {'name':'unseeded-zero','mode':'unseeded','state':0}, {'name':'unseeded-one','mode':'unseeded','state':1},
       {'name':'unseeded-max','mode':'unseeded','state':0xffffff},
       {'name':'unseeded-next-zero','mode':'unseeded','state':7140929},
       {'name':'unseeded-next-max','mode':'unseeded','state':12174572}]
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);parser.add_argument('--pilot',action='store_true');args=parser.parse_args()
    run(args.destination,CASES[:2] if args.pilot else CASES)
