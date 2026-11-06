"""Independent integrity checks for additional evolved-chain source evidence."""
import hashlib
import json
from pathlib import Path

from verify_rng_native import image
from verify_maintenance_clock_neutral import GUESTS

ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'research/yt-maint/evolved-replay-native/rea.json'
PACKET_SHA='d63718fd9f35e8a04fa7e12b51cb40eb179319e513db2f6c0525d556072c337b'
RANGES={(0x14128,153)}
SHA=lambda b:hashlib.sha256(b).hexdigest()


def verify_records(records,original):
    assert SHA(original)==GUESTS['YTMAINT.EXE'],'immutable original maintenance identity'
    assert type(records)is list and len(records)==1,'one complete additional native read'
    loaded=image(original);seen=set()
    for record in records:
        assert record['operation']=='read_bytes'and record['subject']['name']=='YTMAINT.EXE'and record['subject']['digest']['sha256']==GUESTS['YTMAINT.EXE'],'original native subject/operation'
        params=record['parameters'];key=(int(params['address'],16),params['length'])
        assert key in RANGES and key not in seen,'exact distinct uncovered source ranges'
        value=record['normalized_result'];data=bytes.fromhex(value['bytes_hex']);address,length=key
        assert value['complete']is True and value['requested_bytes']==value['returned_bytes']==len(data)==length,'complete native byte payload'
        assert int(value['address'],16)==address,'requested/returned source address agreement'
        assert data==loaded[address-0x10000:address-0x10000+length],'all native bytes match independently relocated original'
        seen.add(key)
    assert seen==RANGES,'complete additional native range inventory'


def verify(path=PACKET):
    raw=Path(path).read_bytes();assert SHA(raw)==PACKET_SHA,'immutable evolved-chain native packet'
    packet=json.loads(raw);assert set(packet)=={'records'},'exact native packet schema'
    verify_records(packet['records'],(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes())
    return dict(native_reads=1,complete_bytes=153,production_save_version=35)

if __name__=='__main__':print('Evolved-chain native evidence verified:',verify())
