"""Verify bounded original-byte initializer contracts without requiring REA.

These static contracts do not constitute fresh provider or runtime observations.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
BINARIES={'YT-INIT.EXE':'601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2','BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'}
LISTING_SHA='e8704fa97b140faab0951494155f6da5db1f19837bdcde030282d273ce48623b'
# Fixed coverage; an editable manifest cannot authorize removing or moving a read.
CONTRACTS={
 'calendar':('YT-INIT.EXE',0x2b5,0x314),
 'field-map-and-config-read':('YT-INIT.EXE',0x5c9,0x239),
 'config-default-writes':('YT-INIT.EXE',0x912,0x3f0),
 'player-writes':('YT-INIT.EXE',0xd4a,0x1a3),
 'sector-writes':('YT-INIT.EXE',0x1872,0x27c),
 'planet-writes':('YT-INIT.EXE',0x2135,0x94),
 'hq-final-patches':('YT-INIT.EXE',0x21ef,0x96),
 'calendar-constants':('YT-INIT.EXE',0x2990,0x88),
 'config-id':('YT-INIT.EXE',0x2bc6,4),
 'config-fighters':('YT-INIT.EXE',0x2bf6,4),
 'config-credits':('YT-INIT.EXE',0x2c18,4),
 'config-inactivity':('YT-INIT.EXE',0x2c58,4),
 'config-turns':('YT-INIT.EXE',0x2cc2,4),
 'config-genesis':('YT-INIT.EXE',0x2d72,4),
 'player-zero':('YT-INIT.EXE',0x2ece,4),
 'hq-fighters':('YT-INIT.EXE',0x3174,4),
 'newspaper-alias-radio':('YT-INIT.EXE',0x2285,0x293),
 'int16-single-dispatch':('BRUN30.EXE',0x63b,2),
 'int16-single-and-tail':('BRUN30.EXE',0xaa73,0x23),
 'single-int16-conversion':('BRUN30.EXE',0xaac8,0x93),
 'single-add-dispatch':('BRUN30.EXE',0x68b,2),
 'single-add-cancellation':('BRUN30.EXE',0xb574,0xc9),
 'normalizer-and-zero-exit':('BRUN30.EXE',0xb63d,0x63),
}

def verify(path=None):
    path=Path(path)if path else ROOT/'research/yt-initializer-replay/native-contracts.json'
    meta=json.loads(path.read_text())
    assert meta['format']=='initializer-native-byte-contracts-v1'
    assert meta['authority']=='Archived original bytes and annotated listing; local disassembly, not fresh REA observations or execution evidence.'
    assert meta['listing_sha256']==LISTING_SHA and SHA((ROOT/'archive/analysis/yt-init/qb-annotated.txt').read_bytes())==LISTING_SHA
    binaries={name:(ROOT/'archive/dos-original'/name).read_bytes()for name in BINARIES}
    for name,raw in binaries.items():assert SHA(raw)==BINARIES[name],'original binary identity'
    contracts=meta['contracts'];assert len(contracts)==len(CONTRACTS),'contract coverage'
    seen=set()
    for c in contracts:
        name=c['name'];assert name in CONTRACTS and name not in seen,'contract identity'
        binary,at,length=CONTRACTS[name]
        assert (c['binary'],c['file_offset'],c['length'])==(binary,at,length),'contract coordinates'
        actual=bytes.fromhex(c['bytes_hex']);assert len(actual)==length and actual==binaries[binary][at:at+length],'original bytes'
        seen.add(name)
    assert seen==set(CONTRACTS)
    return len(contracts)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',nargs='?',type=Path);a=p.parse_args();print(f'Verified {verify(a.path)} bounded initializer byte contracts.')
