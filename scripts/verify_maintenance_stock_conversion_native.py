"""Authenticate retained static evidence for the bounded stock-pickup INT path.

Four existing byte observations in three immutable packets are reused, including
both the INT entry and its backward positive-path target. This verifies original
source/dispatch/mask contracts, not general MBF arithmetic or new DOS execution.
No acquisition writer or replay model is imported.
"""
import hashlib
import json
from pathlib import Path
import struct

from verify_rng_native import image

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
BINARIES={
 'YTMAINT.EXE':'8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
 'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
}
PACKETS={
 'pickup':('research/yt-maint/collision-replay-native/rea.json','be0f500c1a8b201970dcbb65bbe4b6c718f668fba5326d582af840289cccb202','records'),
 'dispatch':('research/yt-xannor-planets/rea/assault-paths.json','4fc6d6c55c2c18fe43c4e9ca459bf53af571a8237f23d6fa897fe114f46f232b','records'),
 'floor':('research/yt-plague-civil-war/rea/target-paths.json','4bfa563cefe57e531601268833452f5fb620573686daa5d249bcb7e9debe007a','observations'),
}
CONTRACTS={
 'pickup':('pickup','ev_c92656dd4a34f4605e434c81cbd3e9f730962d0373f2a3fecfce72256fbfcd2f','YTMAINT.EXE','0x14600',3462),
 'dispatch':('dispatch','ev_4390e0214550c70e645826a190f8145dff501480374c0ed92fdb697c34198a9b','BRUN30.EXE','0x10171',106),
 'positive-entry':('dispatch','ev_4888ae8d5fad919bf11ecf6e4461c59ac2011bdceeab000c71c7272060e18374','BRUN30.EXE','0x1ac9d',184),
 'floor':('floor','ev_567123d41857df939d326c9daf676249df6b745ddf6c8bd7b563373a125605f5','BRUN30.EXE','0x1acb2',180),
}


def packet_records(raw,key):
    """Require the complete retained packet identity before choosing a read."""
    _,digest,shape=PACKETS[key]
    assert type(raw)is bytes and SHA(raw)==digest,'immutable complete native packet '+key
    value=json.loads(raw)
    rows=value[shape]
    if shape=='observations':rows=[r['evidence']for r in rows]
    assert type(rows)is list and all(type(r)is dict for r in rows),'complete native observation inventory'
    return rows


def select_records(packets):
    assert type(packets)is dict and set(packets)==set(PACKETS),'all three retained native packets required'
    rows={key:packet_records(packets[key],key)for key in PACKETS};selected={}
    for name,(key,evidence,_,_,_)in CONTRACTS.items():
        found=[r for r in rows[key]if r.get('evidence_id')==evidence]
        assert len(found)==1,'one exact independently declared evidence ID '+name
        selected[name]=found[0]
    return selected


def verify_record(record,binary,name):
    _,evidence,subject,address,count=CONTRACTS[name]
    assert type(binary)is bytes and SHA(binary)==BINARIES[subject],'immutable original subject binary'
    assert record['evidence_id']==evidence and record['operation']=='read_bytes'and record['subject']['digest']['sha256']==BINARIES[subject],'exact evidence identity, operation and subject'
    assert record['parameters']==dict(address=address,length=count),'exact independently declared native parameters'
    value=record['normalized_result'];data=bytes.fromhex(value['bytes_hex'])
    assert value['address']==address and value['complete']is True and value['requested_bytes']==value['returned_bytes']==len(data)==count,'complete untruncated native range'
    at=int(address,16)-0x10000
    assert data==image(binary)[at:at+count],'all normalized bytes equal original relocated MZ LOAD image'
    return data


def verify_paths(maintenance,runtime):
    """Bind the original numeric call, positive INT path and clear/save order."""
    assert type(maintenance)is bytes and SHA(maintenance)==BINARIES['YTMAINT.EXE'],'original maintenance identity'
    assert type(runtime)is bytes and SHA(runtime)==BINARIES['BRUN30.EXE'],'original runtime identity'
    main=image(maintenance);run=image(runtime)
    #4cd3 CVS reads the four-byte stock string into SINGLE FAC1a;4cdb INT
    #operates on that FAC, then4ce5 stores the result at7bf8. This is not the
    #later3f/77 conversion at4cf2, which follows the namelen descriptor1894.
    assert main[0x4cd0:0x4cea]==bytes.fromhex('bbc418cd3d199090bb1a00cd3d0390908bdfbff87bcd3f7d9090'),'exact stock decode, SINGLE INT and saved amount sequence'
    assert struct.unpack_from('<H',run,0x171+3*2)[0]==0xacb2,'INT3D opcode03 selects the original SINGLE floor entry'
    assert run[0xacb2:0xacc1]==bytes.fromhex('8926080a87f3e8ae0087f351b90200'),'single INT entry and two-byte fraction precision'
    assert run[0xacc1:0xaccf]==bytes.fromhex('803e1d000074e8f6061c008074ce'),'zero exponent and sign select the positive branch'
    branch=0xaccf+int.from_bytes(bytes(run[0xacce:0xaccf]),'little',signed=True)
    assert branch==0xac9d and run[branch:branch+5]==bytes.fromhex('e8770059cb'),'positive INT path calls the retained fraction masker'
    assert branch+3+struct.unpack_from('<h',run,branch+1)[0]==0xad17,'positive path calls actual mask helper AD17'
    assert run[0xad17:0xad47]==bytes.fromhex('505357a01d002c807626bf1c008ad8d0e8d0e8d0e8982bf82bc87210932407bb9605d7200532c04ffdf3aafc5f5b58c3'),'exponent-scaled fraction mask and low-byte clear, without positive rounding increment'
    assert run[0xad47:0xad4e]==bytes.fromhex('c6061d0000ebf5'),'positive values below one clear the FAC exponent without a rounding increment'
    #Original4d09..4d34 replaces the complete stock string with literal8472
    #and saves the planet before amount addition and receipt construction.
    assert main[0x4d09:0x4d34]==bytes.fromhex('bb7284cd3d1c9090bac418cd3f5b90908bdfbfe418be2c7ccd3f7f90908bd3bb1a00cd3e7b90908bd833d2'),'complete stock clear and planet-save argument sequence'
    assert main[0x4d34:0x4d39]==bytes.fromhex('cd3e289090')and main[0x4da5:0x4daa]==bytes.fromhex('cd3e289090'),'actual planet PUT precedes addition and actual sector PUT precedes receipts'
    assert maintenance[0x8472+0xfd0:0x8476+0xfd0]==bytes.fromhex('00008000'),'whole stock clear uses exact original source literal8472'
    assert main[0x4d68:0x4d99]==bytes.fromhex('bef87bcd3f7390908bdfbf207ccd3f8290908bd7bf907bcd3f829090cd3f7a9090bb1a00cd3d1c9090ba9018cd3f5b9090'),'converted amount is added after planet clear/save and before public output'
    assert main[0x4e34:0x4e41]==bytes.fromhex('bef87bcd3fa790907703e97f00'),'taking receipt tests converted whole amount, not original fractional stock'
    return dict(stock_INT_call='0x14cdb',dispatch_entry='0x10177',single_INT_entry='0x1acb2',positive_mask_helper='0x1ad17',source_stock_clear='00008000')


def verify():
    packets={key:(ROOT/path).read_bytes()for key,(path,_,_)in PACKETS.items()}
    records=select_records(packets);binaries={name:(ROOT/'archive/dos-original'/name).read_bytes()for name in BINARIES}
    for name,contract in CONTRACTS.items():verify_record(records[name],binaries[contract[2]],name)
    paths=verify_paths(binaries['YTMAINT.EXE'],binaries['BRUN30.EXE'])
    return dict(reused_native_packets=3,reused_native_reads=4,retained_read_bytes=3932,overlapping_reads=True,**paths,
                scope='source positive SINGLE INT branch and complete stock clearing; no general MBF or new execution claim')


if __name__=='__main__':print('Stock conversion native evidence verified:',verify())
