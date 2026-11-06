"""Independent original-code integrity checks for the collision record replay.

No model or acquisition writer is imported. Prior immutable controls remain
verified by verify_maintenance_placement; this packet authenticates the additional
Mercenary/desertion/lottery source window and exact departure-zero operand.
"""
import hashlib
import json
from pathlib import Path

from verify_rng_native import image
from verify_maintenance_clock_neutral import GUESTS

ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'research/yt-maint/collision-replay-native/rea.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACKET_SHA='be0f500c1a8b201970dcbb65bbe4b6c718f668fba5326d582af840289cccb202'


def verify_record(record,original):
    if SHA(original)!=GUESTS['YTMAINT.EXE']:raise ValueError('original executable identity differs')
    assert record['operation']=='read_bytes'and record['subject']['digest']['sha256']==GUESTS['YTMAINT.EXE'],'original native subject and operation'
    assert record['parameters']==dict(address='0x14600',length=3462),'complete additional source range'
    value=record['normalized_result'];data=bytes.fromhex(value['bytes_hex'])
    assert value['complete']is True and value['requested_bytes']==value['returned_bytes']==len(data)==3462,'complete native source bytes'
    assert data==image(original)[0x4600:0x5386],'all independently relocated original source bytes'
    assert original[0x859e+0xfd0:0x85a2+0xfd0]==bytes.fromhex('00002800'),'source-specific Mercenary departure zero'


def verify(path=PACKET):
    raw=Path(path).read_bytes();assert SHA(raw)==PACKET_SHA,'immutable collision-replay native packet'
    records=json.loads(raw)['records'];assert len(records)==1,'one complete additional native observation'
    verify_record(records[0],(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes())
    return dict(native_reads=1,complete_bytes=3462,production_save_version=35)

if __name__=='__main__':print('Collision replay native evidence verified:',verify())
