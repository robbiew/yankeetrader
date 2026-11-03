"""Independently validate copied-initializer non-RNG state hooks and worlds."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
from verify_rng_clock import read_date,read_time
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
INIT_SHA='601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
SITES={'graph-end':0x18ee,'placement-end':0x1a4d,'ports-end':0x1ecf}
CLOCKS={'midnight':'00:00:00','second-one':'00:00:01','second-two':'00:00:02','later':'12:34:00'}
# Pinned native records, independent of editable per-case metadata.
OBSERVED = {
    'midnight': (0xc3cfff, 0x54bf86, 0x1ca785),
    'second-one': (0x6af4df, 0x451a25, 0xbcd835),
    'second-two': (0x38cb82, 0x1ae0f8, 0x79697c),
    'later': (0xd1df02, 0x6c4e19, 0x34b8fc),
}
FILES={'INIT.LOG','INITRET.LOG','COMMANDS.TXT','ANSWERS.TXT','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','before-maint.dat.gz'}

def payload_contract():
    # Independent assembly of the audited register/scratch-preserving write hook.
    prefix=bytes.fromhex('9c50535152ff365618ff365818')
    stores=b'\xc7\x06'+struct.pack('<HH',0x1856,0x5200)+b'\xc7\x06'+struct.pack('<HH',0x1858,0x2153)
    writes=b''.join(bytes.fromhex('bb0100b90400ba')+struct.pack('<H',at)+bytes.fromhex('b440cd21')for at in (0x1856,0x234))
    restore=bytes.fromhex('8f0658188f0656185a595b589dc3')
    result=prefix+stores+writes+restore
    assert len(result)==65
    return result

def verify(destination):
    destination=Path(destination);names={clock+'-'+phase for clock in CLOCKS for phase in SITES}
    assert {p.name for p in destination.iterdir()if p.is_dir()}==names,'state-hook case coverage'
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert SHA(original)==INIT_SHA and SHA(runtime)==RUNTIME_SHA
    assert original[0x2806:0x284a]==bytes([0x90])*68,'original cave'
    payload=payload_contract();outcomes={}
    for clock,time in CLOCKS.items():
        baseline_dir=ROOT/'research/yt-rng-seeding/clock-dos'/clock
        baseline=gzip.decompress((baseline_dir/'before-maint.dat.gz').read_bytes())
        baseline_meta=json.loads((baseline_dir/'result.json').read_text())
        assert SHA(baseline)==baseline_meta['fingerprints']['world_sha256'] and len(baseline)==4151*137
        for phase,site in SITES.items():
            name=clock+'-'+phase;d=destination/name;meta=json.loads((d/'result.json').read_text())
            assert meta['name']==name and meta['clock']==clock and meta['phase']==phase
            assert meta['recipe']=='port-rng-state-hook-v1' and meta['date']=='11/02/2026' and meta['time']==time
            assert meta['site_code_offset']==site and meta['cave_code_offset']==0x2606
            assert meta['payload_hex']==payload.hex(),'payload contract'
            assert original[site+512:site+517]==bytes.fromhex('cd3fbc9090')
            patched=bytearray(original)
            patched[site+512:site+517]=b'\xe8'+struct.pack('<h',0x2606-(site+3))+b'\x90\x90'
            patched[0x2806:0x2847]=payload
            assert meta['initializer_original_sha256']==INIT_SHA and meta['initializer_copied_sha256']==SHA(patched),'entire copied executable'
            assert meta['runtime_sha256']==RUNTIME_SHA and meta['maintenance_sha256']==SHA(bytes.fromhex('b8004ccd21'))
            assert set(meta['files'])==FILES
            for filename,digest in meta['files'].items():assert SHA((d/filename).read_bytes())==digest,(name,filename)
            assert (d/'ANSWERS.TXT').read_bytes()==b'Y\r\n\r\n'
            assert (d/'COMMANDS.TXT').read_text().splitlines()==['date 11/02/2026','time '+time,'date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init < answers.txt > init.log','echo INITIALIZER_RETURNED > INITRET.LOG']
            assert read_date((d/'DOSDATE.LOG').read_bytes()).strftime('%m/%d/%Y')=='11/02/2026'
            assert read_time((d/'DOSTIME.LOG').read_bytes())==read_time((baseline_dir/'DOSTIME.LOG').read_bytes()),'raw clock baseline'
            assert b'INITIALIZER_RETURNED' in(d/'INITRET.LOG').read_bytes()
            world=gzip.decompress((d/'before-maint.dat.gz').read_bytes())
            assert world==baseline and meta['baseline_world_sha256']==SHA(baseline),'hook changed baseline world'
            log=(d/'INIT.LOG').read_bytes();assert b'<YT-INIT Normal Termination>' in log
            assert log.count(b'\0RS!')==1,'unique raw state record'
            at=log.index(b'\0RS!');state=int.from_bytes(log[at+4:at+8],'little')
            assert len(log[at+4:at+8])==4 and state<1<<24 and meta['state']==state,'raw state'
            assert state==OBSERVED[clock][list(SITES).index(phase)], 'retained native state changed'
            outcomes[name]=state
    return outcomes

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',nargs='?',type=Path,default=ROOT/'research/yt-port-replay/state-dos');a=p.parse_args();print(json.dumps(verify(a.destination),indent=2))
