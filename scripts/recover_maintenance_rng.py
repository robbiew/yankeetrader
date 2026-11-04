"""Capture first-hit RNG phase stops in same-size disposable YTMAINT copies."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINARIES = {'YTMAINT.EXE': '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
            'BRUN30.EXE': '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
            'YT-INIT.EXE': '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'}
# main0044 return guard exits99. A hook jumps to0049 and emits MSP1/state/FAC,
# then exits0. No runtime, MZ header, file size, startup seed or source DAT patch.
PAYLOAD = bytes.fromhex('b8634ccd211e0e1fbb0100b90400ba6d00b440cd211fba3402b440cd21ba1a00b440cd21b8004ccd214d535031')
PHASES = {'seed-timer': (0x7d,0x1a), 'seed-before': (0x85,0x1a), 'seed-after': (0x8d,0x1a),
          'helper1-before': (0x7900,0x1a), 'helper1-after': (0x7908,0x1a),
          'helper1-rnd-after': (0x790d,0x1a), 'helper1-argument': (0x7908,0x7ea4),
          'wanderer-1-before': (0x2237,0x1a), 'wanderer-1-after': (0x223c,0x1a),
          'wanderer-2-before': (0x226c,0x1a), 'wanderer-2-after': (0x2271,0x1a),
          'wanderer-3-before': (0x2363,0x1a), 'wanderer-3-after': (0x2368,0x1a),
          'helper2-before': (0x7946,0x1a), 'helper2-after': (0x794e,0x1a),
          'helper2-rnd-before': (0x7989,0x1a), 'helper2-rnd-after': (0x798e,0x1a),
          'helper2-argument': (0x7989,0x7ea4)}
CASES = {'baseline': ('baseline-split','11/02/2026','00:00:00',False),
         'repeat': ('repeat-split','11/02/2026','00:00:00',False),
         'second-one': ('second-one-split','11/02/2026','00:00:01',False),
         'second-two': ('second-two-split','11/02/2026','00:00:02',False),
         'new-year': ('new-year-split','01/01/2027','00:00:00',False),
         'integrated': ('baseline-integrated','11/02/2026','00:00:00',True)}


def patch(original,site,source):
    assert len(PAYLOAD)==45 and site>=0x73
    payload=PAYLOAD.replace(bytes.fromhex('ba1a00'),b'\xba'+struct.pack('<H',source))
    copied=bytearray(original)
    copied[512+0x44:512+0x44+len(payload)]=payload
    copied[512+site:512+site+5]=b'\xe9'+struct.pack('<H',(0x49-site-3)&65535)+b'\x90\x90'
    assert len(copied)==len(original) and copied[:512]==original[:512]
    return bytes(copied)


def capture(destination,pilot=False):
    binary={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in BINARIES}
    assert {n:SHA(b)for n,b in binary.items()}==BINARIES
    assert shutil.which('dosbox-staging')
    original=binary['YTMAINT.EXE']
    inventory={}
    for signature in ['cd3d349090','cd3d339090']:
        at=512
        while (at:=original.find(bytes.fromhex(signature),at))!=-1:
            inventory[f'rnd-{at-512:04x}']=(at-512,0x1a);at+=5
    assert len(inventory)==43
    destination.mkdir(parents=True,exist_ok=False)
    for case,(oracle,date,clock,integrated)in CASES.items():
        if pilot and case!='baseline':continue
        phases=PHASES if case!='baseline' else PHASES|inventory
        for phase,(site,source)in phases.items():
            d=destination/(case+'--'+phase);d.mkdir()
            copied=patch(original,site,source)
            (d/'YTMAINT.EXE').write_bytes(copied);(d/'BRUN30.EXE').write_bytes(binary['BRUN30.EXE'])
            inputs={}
            if integrated:
                (d/'YT-INIT.EXE').write_bytes(binary['YT-INIT.EXE'])
                (d/'ANSWERS.TXT').write_bytes(b'Y\r\n\r\n');command='yt-init < ANSWERS.TXT > TRACE.BIN'
            else:
                for n in ['YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT']:
                    data=gzip.decompress((ROOT/'research/yt-maint/initial-controls'/oracle/('before-'+n+'.gz')).read_bytes())
                    (d/n).write_bytes(data);inputs[n]=SHA(data)
                command='ytmaint > TRACE.BIN'
            commands=['date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG',command,
                      'if errorlevel 99 echo PROBE_NOT_REACHED > MISS.LOG',
                      'if not errorlevel 1 echo PROBE_RECORDED > HIT.LOG',
                      'echo PROBE_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
            (d/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
            with(d/'dosbox.log').open('w')as log:
                subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in ['mount c '+str(d),'c:']+commands+['exit']for v in ['-c',c]],
                               env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
            trace=(d/'TRACE.BIN').read_bytes();hit_witness=(d/'HIT.LOG').read_bytes();miss_witness=(d/'MISS.LOG').read_bytes()
            hit=trace[-12:-8]==b'MSP1'
            assert (hit_witness,miss_witness)==((b'PROBE_RECORDED\r\n',b'')if hit else(b'',b'PROBE_NOT_REACHED\r\n')),(case,phase,trace[-100:])
            if phase in PHASES:assert hit,(case,phase,'required first-hit boundary missing')
            (d/'partial-world.dat.gz').write_bytes(gzip.compress((d/'YTDATA.DAT').read_bytes(),mtime=0))
            keep={'TRACE.BIN','HIT.LOG','MISS.LOG','RETURN.LOG','DOSDATE.LOG','DOSTIME.LOG','ENDDATE.LOG','ENDTIME.LOG','COMMANDS.TXT','dosbox.log','partial-world.dat.gz'}
            if integrated:keep.add('ANSWERS.TXT')
            meta=dict(recipe='maintenance-rng-first-hit-v1',case=case,phase=phase,oracle=oracle,date=date,time=clock,integrated=integrated,
                      site=site,source=source,hit=hit,original_bytes=original[512+site:512+site+5].hex(),
                      binaries=BINARIES,copied_maintenance_sha256=SHA(copied),inputs=inputs,
                      files={n:SHA((d/n).read_bytes())for n in sorted(keep)})
            (d/'result.json').write_text(json.dumps(meta,indent=2)+'\n')
            for p in d.iterdir():
                if p.name not in keep|{'result.json'}:p.unlink()
        print(case,len(phases),'first-hit probes returned',flush=True)


def capture_oracles(destination):
    binaries={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in BINARIES}
    assert {n:SHA(b)for n,b in binaries.items()}==BINARIES
    assert shutil.which('dosbox-staging')
    p=destination;p.mkdir(parents=True,exist_ok=False)
    for case,(oracle,date,clock,integrated)in CASES.items():
     d=p/case;d.mkdir();inputs={}
     for n,b in binaries.items():(d/n).write_bytes(b)
     if integrated:
      (d/'ANSWERS.TXT').write_bytes(b'Y\r\n\r\n');command='yt-init < ANSWERS.TXT > TRACE.BIN'
     else:
      for n in ['YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT']:
       b=gzip.decompress((ROOT/'research/yt-maint/initial-controls'/oracle/('before-'+n+'.gz')).read_bytes());(d/n).write_bytes(b);inputs[n]=SHA(b)
      command='ytmaint > TRACE.BIN'
     commands=['date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG',command,'echo ORIGINAL_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
     (d/'COMMANDS.TXT').write_text('\n'.join(commands)+'\n')
     with(d/'dosbox.log').open('w')as log:
      subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in ['mount c '+str(d),'c:']+commands+['exit']for v in ['-c',c]],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
     assert b'Daily Maintenance Completed OK'in(d/'TRACE.BIN').read_bytes()
     if integrated:assert b'<YT-INIT Normal Termination>'in(d/'TRACE.BIN').read_bytes()
     for f in list(d.iterdir()):
      if f.suffix.upper()in ('.DAT','.ASC'):(d/('after-'+f.name+'.gz')).write_bytes(gzip.compress(f.read_bytes(),mtime=0));f.unlink()
     for n in BINARIES:(d/n).unlink()
     (d/'result.json').write_text(json.dumps(dict(recipe='maintenance-rng-untouched-v1',case=case,oracle=oracle,date=date,time=clock,integrated=integrated,binaries=BINARIES,inputs=inputs,files={f.name:SHA(f.read_bytes())for f in d.iterdir()}),indent=2)+'\n')
     print(case,'untouched completed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--pilot',action='store_true');p.add_argument('--oracles',action='store_true');a=p.parse_args()
    if a.oracles:capture_oracles(a.destination.resolve())
    else:capture(a.destination.resolve(),a.pilot)
