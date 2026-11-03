"""Observe copied-initializer shortcut index rounding with one declared write."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('rounding_mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
INIT_SHA='601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
EXIT_STUB=bytes.fromhex('b8004ccd21')
CASES=[('integer-100',100.0),('fraction-100-25',100.25),('tie-100-5',100.5),('fraction-100-75',100.75),('tie-101-5',101.5)]


def run(destination):
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes()
    runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert SHA(original)==INIT_SHA and SHA(runtime)==RUNTIME_SHA
    destination.mkdir(parents=True,exist_ok=False)
    for name,value in CASES:
        d=destination/name;d.mkdir()
        # Main13b3 is the first instruction following the possible slot6 write.
        # The month8 constant is also used by a calendar comparison. Fixed month11
        # takes its false branch both before and after these synthetic values.
        patches=[dict(offset=0x15b3,before='cd3d34',after='e98102',purpose='stop after first shortcut write'),
                 dict(offset=0x2ff6,before=mbf.enc(400).hex(),after=mbf.enc(0).hex(),purpose='zero shortcut random scale'),
                 dict(offset=0x29e6,before=mbf.enc(8).hex(),after=mbf.enc(value).hex(),purpose='synthetic shortcut offset; month11 control')]
        binary=bytearray(original)
        for patch in patches:
            before=bytes.fromhex(patch['before']);after=bytes.fromhex(patch['after']);at=patch['offset']
            assert len(before)==len(after) and original[at:at+len(before)]==before
            binary[at:at+len(after)]=after
        (d/'YT-INIT.EXE').write_bytes(binary);(d/'BRUN30.EXE').write_bytes(runtime)
        (d/'YTMAINT.EXE').write_bytes(EXIT_STUB);(d/'ANSWERS.TXT').write_bytes(b'Y\r\n\r\n')
        commands=['mount c '+str(d),'c:','date 11/02/2026','time 00:00:00',
                  'date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init < answers.txt > init.log',
                  'echo INITIALIZER_RETURNED > INITRET.LOG','exit']
        with(d/'init-dosbox.log').open('w')as output:
            subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf',
                            '--set','cpu_cycles=200000','--set','nosound=true']+
                           [x for command in commands for x in('-c',command)],
                           env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                           stdout=output,stderr=subprocess.STDOUT,check=True,timeout=120)
        raw=(d/'YTDATA.DAT').read_bytes()
        assert len(raw)==4151*137
        assert b'<YT-INIT Normal Termination>' in(d/'INIT.LOG').read_bytes()
        assert b'INITIALIZER_RETURNED' in(d/'INITRET.LOG').read_bytes()
        (d/'before-maint.dat.gz').write_bytes(gzip.compress(raw,mtime=0))
        keep=['before-maint.dat.gz','INIT.LOG','INITRET.LOG','ANSWERS.TXT','init-dosbox.log','DOSDATE.LOG','DOSTIME.LOG']
        metadata=dict(name=name,value=value,recipe='shortcut-index-rounding-v1',date='11/02/2026',time='00:00:00',
                      initializer_original_sha256=INIT_SHA,initializer_copied_sha256=SHA(binary),patches=patches,
                      maintenance_child='declared-exit-stub',
                      binaries={'YT-INIT.EXE':SHA(binary),'BRUN30.EXE':RUNTIME_SHA,'YTMAINT.EXE':SHA(EXIT_STUB)},
                      files={filename:SHA((d/filename).read_bytes())for filename in keep})
        (d/'result.json').write_text(json.dumps(metadata,indent=2)+'\n')
        for path in d.iterdir():
            if path.name not in keep+['result.json']:path.unlink()
        print(name,value,len(raw),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('destination',type=Path)
    run(parser.parse_args().destination.resolve())
