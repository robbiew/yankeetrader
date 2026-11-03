"""Verify exact native byte contracts for TIMER, RANDOMIZE, RND and app call sites."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
BINARIES={'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
          'YT-INIT.EXE':'601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'}
CONTRACTS={
 'runtime-rea.json':('BRUN30.EXE',{'0x1b349':32,'0x1abe3':16,'0x1c12f':133,'0x2002c':12}),
 'dispatch-rea.json':('BRUN30.EXE',{'0x101f7':2,'0x104ef':2,'0x10255':2,'0x101d9':2}),
 'initializer-rea.json':('YT-INIT.EXE',{'0x10030':63,'0x10921':61,'0x1004c':33})}

def image(raw):
    assert raw[:2]==b'MZ'
    data=bytearray(raw[struct.unpack_from('<H',raw,8)[0]*16:]);at=struct.unpack_from('<H',raw,24)[0]
    for i in range(struct.unpack_from('<H',raw,6)[0]):
        off,seg=struct.unpack_from('<HH',raw,at+i*4);p=seg*16+off
        struct.pack_into('<H',data,p,(struct.unpack_from('<H',data,p)[0]+0x1000)&0xffff)
    return data

def check_bundle(path,binary,reads):
    raw=(ROOT/'archive/dos-original'/binary).read_bytes();assert SHA(raw)==BINARIES[binary]
    loaded=image(raw);records=json.loads(Path(path).read_text())['records'];seen=set()
    assert len(records)==len(reads),'native coverage'
    for r in records:
        n=r['normalized_result'];address=n['address']
        assert r['operation']=='read_bytes' and r['subject']['digest']['sha256']==SHA(raw),'native target'
        assert address in reads and address not in seen,'native range'
        size=reads[address]
        assert r['parameters']=={'address':address,'length':size},'native parameters'
        assert n['complete'] and n['returned_bytes']==n['requested_bytes']==size,'truncated native read'
        p=int(address,16)-0x10000
        assert bytes.fromhex(n['bytes_hex'])==loaded[p:p+size],'native bytes'
        seen.add(address)
    assert seen==set(reads),'missing native ranges'

def verify(directory):
    for name,(binary,reads) in CONTRACTS.items():check_bundle(Path(directory)/name,binary,reads)
    # Reuse the already retained LCG/normalizer observations; no duplicate query.
    check_bundle(ROOT/'research/yt-port-generation/runtime-rea.json','BRUN30.EXE',{'0x1b2c2':110,'0x2002c':12})
    return 13
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',nargs='?',type=Path,default=ROOT/'research/yt-rng-seeding');a=p.parse_args()
    print(f'Native RNG contracts verified: {verify(a.directory)} retained observations.')
