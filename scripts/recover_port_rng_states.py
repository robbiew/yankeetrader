"""Capture non-RNG state hooks in disposable initializer copies."""
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
INIT_SHA='601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
SITES={'graph-end':0x18ee,'placement-end':0x1a4d,'ports-end':0x1ecf}
CLOCKS={'midnight':'00:00:00','second-one':'00:00:01','second-two':'00:00:02','later':'12:34:00'}
PAYLOAD=bytes.fromhex('9c50535152 ff365618 ff365818 c70656180052 c70658185321 bb0100b90400ba5618b440cd21 bb0100b90400ba3402b440cd21 8f065818 8f065618 5a595b589d c3')
assert len(PAYLOAD)==65

def run(destination):
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert SHA(original)==INIT_SHA and SHA(runtime)==RUNTIME_SHA
    assert original[0x2806:0x284a]==b'\x90'*68
    destination.mkdir(parents=True,exist_ok=False)
    for clock,time in CLOCKS.items():
        baseline=gzip.decompress((ROOT/'research/yt-rng-seeding/clock-dos'/clock/'before-maint.dat.gz').read_bytes())
        for phase,site in SITES.items():
            name=clock+'-'+phase;d=destination/name;d.mkdir()
            assert original[site+512:site+517]==bytes.fromhex('cd3fbc9090')
            patched=bytearray(original);jump=b'\xe8'+struct.pack('<h',0x2606-site-3)+b'\x90\x90'
            assert site+517<=0x2806
            patched[site+512:site+517]=jump;patched[0x2806:0x2806+65]=PAYLOAD
            (d/'YT-INIT.EXE').write_bytes(patched);(d/'BRUN30.EXE').write_bytes(runtime);(d/'YTMAINT.EXE').write_bytes(bytes.fromhex('b8004ccd21'))
            (d/'ANSWERS.TXT').write_bytes(b'Y\r\n\r\n')
            commands=['date 11/02/2026','time '+time,'date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init < answers.txt > init.log','echo INITIALIZER_RETURNED > INITRET.LOG']
            (d/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
            with(d/'dosbox.log').open('w')as out:
                subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for cmd in ['mount c '+str(d),'c:']+commands+['exit'] for x in ('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=out,stderr=subprocess.STDOUT,check=True,timeout=60)
            world=(d/'YTDATA.DAT').read_bytes();assert world==baseline,'hook changed world'
            log=(d/'INIT.LOG').read_bytes();assert log.count(b'\0RS!')==1 and b'<YT-INIT Normal Termination>' in log
            at=log.index(b'\0RS!');state=int.from_bytes(log[at+4:at+8],'little');assert state<1<<24
            assert b'INITIALIZER_RETURNED' in(d/'INITRET.LOG').read_bytes()
            (d/'before-maint.dat.gz').write_bytes(gzip.compress(world,mtime=0))
            keep={'INIT.LOG','INITRET.LOG','COMMANDS.TXT','ANSWERS.TXT','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','before-maint.dat.gz'}
            meta=dict(name=name,clock=clock,phase=phase,recipe='port-rng-state-hook-v1',date='11/02/2026',time=time,site_code_offset=site,cave_code_offset=0x2606,payload_hex=PAYLOAD.hex(),initializer_original_sha256=INIT_SHA,initializer_copied_sha256=SHA(patched),runtime_sha256=RUNTIME_SHA,maintenance_sha256=SHA(bytes.fromhex('b8004ccd21')),baseline_world_sha256=SHA(baseline),state=state,files={p:SHA((d/p).read_bytes())for p in sorted(keep)})
            (d/'result.json').write_text(json.dumps(meta,indent=2)+'\n')
            for p in d.iterdir():
                if p.name not in keep|{'result.json'}:p.unlink()
            print(name,hex(state),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);run(p.parse_args().destination.resolve())
