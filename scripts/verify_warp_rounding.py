"""Check retained one-shortcut DOS controls independently of their capture writer."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
INIT_SHA='601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
BASELINE_SHA='d59906b9538555eea408a16330a53bf33d72b9e3edeb42237f70ea92867627af'
REQUIRED={'before-maint.dat.gz','INIT.LOG','INITRET.LOG','ANSWERS.TXT','init-dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
# Fixed observed cells distinguish truncation and ties-even from positive half-up.
CASES={'integer-100':(100.0,100),'fraction-100-25':(100.25,100),'tie-100-5':(100.5,101),
       'fraction-100-75':(100.75,101),'tie-101-5':(101.5,102)}
spec=importlib.util.spec_from_file_location('rounding_mbf_primitives',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def verify(destination,baseline=None):
    destination=Path(destination)
    baseline=Path(baseline)if baseline else ROOT/'research/yt-warp-generation/dos/repair-only/before-maint.dat.gz'
    base=gzip.decompress(baseline.read_bytes())
    assert SHA(base)==BASELINE_SHA,'changed repair-only reference'
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes()
    assert SHA(original)==INIT_SHA
    assert SHA((ROOT/'archive/dos-original/BRUN30.EXE').read_bytes())==RUNTIME_SHA
    assert {d.name for d in destination.iterdir()if d.is_dir()}==set(CASES),'missing rounding controls'
    outcomes=[]
    for name,(value,sector)in CASES.items():
        d=destination/name;meta=json.loads((d/'result.json').read_text())
        assert meta['recipe']=='shortcut-index-rounding-v1' and meta['name']==name and meta['value']==value
        assert meta['date']=='11/02/2026' and meta['time']=='00:00:00'
        assert meta['initializer_original_sha256']==INIT_SHA and meta['maintenance_child']=='declared-exit-stub'
        patches=[dict(offset=0x15b3,before='cd3d34',after='e98102',purpose='stop after first shortcut write'),
                 dict(offset=0x2ff6,before='00004889',after='00000000',purpose='zero shortcut random scale'),
                 dict(offset=0x29e6,before='00000084',after=mbf.enc(value).hex(),purpose='synthetic shortcut offset; month11 control')]
        assert meta['patches']==patches,'changed declared executable patches'
        patched=bytearray(original)
        for patch in patches:
            at=patch['offset'];before=bytes.fromhex(patch['before']);after=bytes.fromhex(patch['after'])
            assert original[at:at+len(before)]==before
            patched[at:at+len(after)]=after
        copied_sha=SHA(patched)
        assert meta['initializer_copied_sha256']==copied_sha
        assert meta['binaries']=={'YT-INIT.EXE':copied_sha,'BRUN30.EXE':RUNTIME_SHA,'YTMAINT.EXE':SHA(bytes.fromhex('b8004ccd21'))}
        assert set(meta['files'])==REQUIRED
        for filename,digest in meta['files'].items():assert SHA((d/filename).read_bytes())==digest,(name,filename)
        assert (d/'ANSWERS.TXT').read_bytes()==b'Y\r\n\r\n'
        assert b'Current date: Mon 11/02/2026' in(d/'DOSDATE.LOG').read_bytes(),'calendar control changed'
        assert b'Current time: 0:00:00.00am' in(d/'DOSTIME.LOG').read_bytes(),'clock control changed'
        assert b'INITIALIZER_RETURNED' in(d/'INITRET.LOG').read_bytes()
        assert b'<YT-INIT Normal Termination>' in(d/'INIT.LOG').read_bytes()
        world=gzip.decompress((d/'before-maint.dat.gz').read_bytes())
        assert len(world)==4151*137
        assert mbf.get(base,51+sector,61)==0,'chosen baseline slot occupied'
        changes=[]
        for s in range(1,3001):
            for slot,offset in enumerate((41,45,49,53,57,61)):
                before=mbf.get(base,51+s,offset);after=mbf.get(world,51+s,offset)
                if before!=after:changes.append((s,slot,before,after))
        assert changes==[(sector,5,0.0,1.0)],(name,changes)
        outcomes.append(dict(name=name,index_value=value,changed_sector=sector))
    return outcomes

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',nargs='?',type=Path,default=ROOT/'research/yt-warp-generation/rounding-dos')
    parser.add_argument('--baseline',type=Path)
    args=parser.parse_args();print(json.dumps(verify(args.destination,args.baseline),indent=2))
    print('Verified five one-write shortcut controls: nearest integer with positive halves rounded upward.')
