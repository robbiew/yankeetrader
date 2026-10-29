"""Verify preserved original-DOS bribe probes and their conservation rules."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence',type=Path,default=ROOT/'research/yt-mercenaries/dos')
args=parser.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()

def number(data,record,offset):
    raw=data[(record-1)*137+offset:(record-1)*137+offset+4]
    m=int.from_bytes(raw[:3],'little')
    return 0 if raw[3]==0 else (-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/2**23)*2.0**(raw[3]-129)

def put(data,record,offset,value):
    raw=bytes(4)
    if value:
        fraction,exponent=math.frexp(abs(value));mantissa=round((fraction*2-1)*2**23)
        if mantissa==2**23:mantissa=0;exponent+=1
        raw=(mantissa|(0x800000 if value<0 else 0)).to_bytes(3,'little')+bytes([exponent+128])
    start=(record-1)*137+offset;data[start:start+4]=raw

# Inputs and expected outcomes are independent of the captured manifests.
expected={
    'blank':('', 'cancel'), 'zero':('0','insult'), 'negative':('-1','insult'),
    'one':('1','insult'), 'hundred':('100','insult'), 'thousand':('1000','accept'),
    'two-hundred':('200','accept'), 'three-hundred':('300','accept'),
    'ten-thousand':('10000','accept'), 'fifty-thousand':('50000','accept'),
    'all-credits':('100000','accept'), 'over-budget':('100001','insult'),
    'fraction':('50000.5','accept'), 'text':('abc','insult'),
    'planet':('50000','planet'), 'human-weak':('','human'), 'xannor':('','xannor'),
    'merc-weak':('50000','accept'), 'merc-zero-force':('50000','accept'),
}
cases=json.loads((args.evidence/'results.json').read_text())['scenarios']
assert len(cases)==len(expected) and {c['name'] for c in cases}=={'npc-bribe-'+n for n in expected}
source=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
exe=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
assert sha(exe)=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
feeder=(ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
graph={100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
for c in cases:
    name=c['name'];short=name.removeprefix('npc-bribe-');offer,outcome=expected[short];d=args.evidence/name
    assert json.loads((d/'result.json').read_text())==c,name
    assert c['command']=='M;101\r~~B\r~~'+offer,name
    assert c['dos_time']=='00:00:00' and c['source_sha256']==sha(source),name
    assert c['executable_sha256']==sha(exe) and c['keyfeed_sha256']==sha(feeder),name
    for tag,file in [('keys','KEYS.TXT'),('transcript','transcript.txt'),('dosbox_log','dosbox.log')]:
        assert sha((d/file).read_bytes())==c[tag+'_sha256'],(name,file)
    keys=b'\r~~~~~\r~'+c['command'].encode()+b'\r~~~~'+b'\rQ;Y\r~~'*24
    assert (d/'KEYS.TXT').read_bytes()==keys,name
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
    for label,data in [('before',before),('after',after)]:
        assert len(data)==568687 and sha(data)==c[label+'_sha256'],(name,label)
        assert number(data,2,49)==c['turns_'+label] and number(data,2,57)==c['sector_'+label],name
    rebuilt=bytearray(source)
    assert c['graph']=={str(k):v for k,v in graph.items()},name
    for sector,warps in graph.items():
        r=51+sector;rebuilt[(r-1)*137:r*137]=bytes(137)
        for offset,target in zip(range(41,65,4),warps):put(rebuilt,r,offset,target)
    for r,fields in [(2,{45:0,49:500,57:100,89:0,105:0,125:0}), (3,{45:0,57:103,61:42,53:7,89:0,125:0}), (152,{65:2}), (3053,{93:101}), (153,{93:2}), (4053,{73:0,77:12})]:
        for offset,value in fields.items():put(rebuilt,r,offset,value)
    patches={(2,93):0,(2,61):2000,(152,81):100,(152,85):-2}
    if short=='planet':patches.update({(152,93):2,(4053,73):-2})
    if short=='human-weak':patches.update({(152,85):3,(2,61):10})
    if short=='xannor':patches[(152,85)]=-1
    if short=='merc-weak':patches[(2,61)]=10
    if short=='merc-zero-force':patches[(2,61)]=0
    assert {(p['record'],p['offset']):p['value'] for p in c['patches']}==patches,name
    for (r,o),v in patches.items():put(rebuilt,r,o,v)
    assert bytes(rebuilt)==before,(name,'undeclared fixture mutation')
    text=(d/'transcript.txt').read_text()
    assert 'Returning to Yankee Trader Local Logon Program' in text,name
    assert (number(after,2,57),number(after,2,49),number(after,2,45))==(101,499,0),name
    assert number(after,2,53)==number(before,2,53),name
    cash=number(after,2,81);fighters=number(after,2,61)
    if outcome=='accept':
        assert 'Good Deal! We join up with you!' in text,name
        assert cash==100000-float(offer) and fighters==number(before,2,61)+100,name
        assert number(after,152,81)==number(after,152,85)==0,name
    elif outcome in ('insult','xannor'):
        assert ('You insult us' if outcome=='insult' else "We don't accept no Bribes") in text,name
        lost=int(re.search(r'You lost (\d+) fighter\(s\)',text)[1])
        assert cash==100000 and fighters==2000-lost and 0<lost<2000,name
        assert number(after,152,81)==number(after,152,85)==0,name
        assert 'You destroyed 100 enemy fighters.' in text,name
    else:
        assert cash==100000 and fighters==number(before,2,61),name
        assert number(after,152,81)==100 and number(after,152,85)==patches[(152,85)],name
        if outcome=='planet':assert 'This planet is OURS!' in text,name
        if outcome=='human':assert "We don't accept no Bribes" in text,name
        assert 'Good Deal!' not in text and 'You lost' not in text,name

# Cross-check REA's loaded bytes against the unchanged MZ file, independently
# of the archived annotation's incorrect disassembly after INT 3F/AE.
header=struct.unpack_from('<H',exe,8)[0]*16
records=json.loads((ROOT/'research/yt-mercenaries/rea/offer-path.json').read_text())['records']
assert len(records)==2
for r in records:
    assert r['subject']['digest']['sha256']==sha(exe) and r['operation']=='read_bytes'
    v=r['normalized_result'];start=header+int(v['address'],16)-0x10000
    assert v['complete'] and bytes.fromhex(v['bytes_hex'])==exe[start:start+v['requested_bytes']]
assert 'cd3fae01cd3f82cd3fa680' in records[0]['normalized_result']['bytes_hex']
print(f'Verified {len(cases)} DOS bribe sessions, {2*len(cases)} snapshots, exact fixture provenance, offers and faction outcomes; two REA byte observations.')
