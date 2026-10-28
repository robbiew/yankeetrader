"""Verify retained DOS saves/logs and static production evidence without emulation."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import math
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'research/yt-missiles/production'
checks=0

def ck(ok,label):
    global checks
    assert ok,label
    checks+=1

def digest(raw):return hashlib.sha256(raw).hexdigest()
def number(raw,record,offset):
    pos=(record-1)*137+offset
    data=raw[pos:pos+4];mant=int.from_bytes(data[:3],'little')
    return 0 if data[3]==0 else (-1 if mant&0x800000 else 1)*(1+(mant&0x7fffff)/2**23)*2**(data[3]-129)
def state(b):return {'production':[number(b,4052,o)for o in(45,49,53)],'stocks':[number(b,4052,o)for o in(57,61,65)],'weapons':[number(b,4052,o)for o in(69,113,125,129)],'owner':number(b,4052,73),'ground':number(b,4052,77),'active':number(b,4052,85),'bank':number(b,4052,117),'sector_planet':number(b,152,93),'ammo':number(b,2,97),'turns':number(b,2,49),'credits':number(b,2,81)}

raw=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
sha=digest(raw)
ck(sha=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037','original executable hash')
word=lambda p:int.from_bytes(raw[p:p+2],'little')
image=bytearray(raw[word(8)*16:(word(4)-1)*512+(word(2)or 512)])
for i in range(word(6)):
    entry=word(24)+4*i;offset=word(entry+2)*16+word(entry)
    image[offset:offset+2]=((int.from_bytes(image[offset:offset+2],'little')+0x1000)&0xffff).to_bytes(2,'little')
for filename,count in [('production-rea.json',1),('production-cache-rea.json',3)]:
    bundle=json.loads((EVIDENCE.parent/filename).read_text());ck(len(bundle['records'])==count,filename+' read count')
    for row in bundle['records']:
        r=row['normalized_result'];start=int(r['address'],16)-0x10000
        ck(row['operation']=='read_bytes' and row['subject']['digest']['sha256']==sha,filename+' identity')
        ck(r['complete'] and r['requested_bytes']==r['returned_bytes'],filename+' complete')
        ck(image[start:start+r['returned_bytes']].hex()==r['bytes_hex'],filename+' original relocated bytes')

manifest=json.loads((EVIDENCE/'evidence.json').read_text())
ck(manifest['dos_normal_sessions']==len(manifest['cases'])==10,'ten normal sessions')
ck(manifest['dos_process_attempts']==11,'one excluded timeout attempt')
for row in manifest['cases']:
    name=row['case'];d=EVIDENCE/'evidence'/name
    before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes());log=(d/'GAME.LOG').read_bytes()
    ck(len(before)==len(after)==4151*137,name+' complete save size')
    ck(digest(before)==row['before_sha256'] and digest(after)==row['after_sha256'],name+' save hashes')
    ck(digest(log)==row['log_sha256'] and digest((d/'KEYS.TXT').read_bytes())==row['keys_sha256'],name+' transcript/input hashes')
    ck(row['executable_sha256']==sha,name+' launched original executable')
    ck(b'Returning to Yankee Trader Local Logon Program'in log,name+' normal completion')
    ck(not any(s in log for s in [b'Illegal function',b'Syntax error',b'Overflow',b'Division by zero']),name+' no runtime error')
    b,a=state(before),state(after)
    ck(b==row['before'] and a==row['after'],name+' decoded record manifest')
    ck(b['ammo']==100 and a['ammo']==80 and b['turns']==500 and a['turns']==499,name+' launch cost')
    ck(a['credits']==b['credits']==1005,name+' no credit salvage')
    ck(a['owner']==b['owner']==3 and a['bank']==b['bank']==(12345 if name=='destroy-bank' else 0) and a['ground']==0,name+' ownership/bank/ground')
    ck(all(math.isfinite(x) and x>=0 for x in a['production']+a['stocks']),name+' nonnegative clamping')
    match=re.search(rb'Productivity reduced by ([\d.]+) units to ([\d.]+)',log)
    ck(match is not None,name+' production receipt')
    ck(abs(float(match[2])-sum(a['production']))<.2,name+' receipt total matches save')
    destroyed=name in ('destroy','destroy-bank','zero-production')
    ck((b'The planet was destroyed!!'in log)==destroyed,name+' destruction receipt')
    ck(a['active']==(0 if destroyed else 7) and a['sector_planet']==(0 if destroyed else 1),name+' active/link lifecycle')
    if destroyed:
        ck(a['production']==a['stocks']==[0,0,0],name+' destroyed production/stocks')
        ck(all(v>0 for v in a['weapons']),name+' inactive residual weapons are retained')
        start=(4052-1)*137
        ck(before[start:start+41]==after[start:start+41],name+' inactive name bytes retained')
    if name in ('partial-cap','partial-clamp'):
        ck(all(abs(stock-10*rate)<=max(.001,10*rate/2**22)for stock,rate in zip(a['stocks'],a['production'])),name+' stocks capped at ten times rates')
    if name=='partial-clamp':ck(a['production'][0]==a['production'][2]==a['stocks'][0]==a['stocks'][2]==0,name+' only exhausted categories clamped')
    if name.endswith('-only'):
        index={'ore-only':0,'organics-only':1,'equipment-only':2}[name]
        ck(59000<a['production'][index]<100100 and all(v==0 for i,v in enumerate(a['production'])if i!=index),name+' isolated category damaged')
    if name=='ore-stock-derived':ck(b['production']==[0,0,0] and 59000<a['production'][0]<100000 and a['production'][1:]==[0,0],name+' newly derived ore is also damaged')
    if name=='ore-trigger':ck(59000<a['production'][0]<100100 and a['production'][1:]==[0,0],name+' positive cached ore survives companion exhaustion')
failed=manifest['excluded_attempt'];log=(EVIDENCE/'evidence'/failed['case']/'GAME.LOG').read_bytes()
ck(digest(log)==failed['log_sha256'] and b'Returning to Yankee Trader Local Logon Program'not in log,'excluded timeout has no normal completion')

spec=importlib.util.spec_from_file_location('production_rules',EVIDENCE/'rules.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
fixtures=[
 (20,[100000]*3,[1000000]*3,dict(production=[80000]*3,stocks=[800000]*3,spent=20,destroyed=False)),
 (20,[1]*3,[10]*3,dict(production=[0]*3,stocks=[0]*3,spent=20,destroyed=True)),
 (20,[0,1,0],[0,10,0],dict(production=[0]*3,stocks=[0]*3,spent=1,destroyed=True)),
 (20,[100000,0,0],[0]*3,dict(production=[80000,0,0],stocks=[0]*3,spent=20,destroyed=False)),
 (20,[0]*3,[0]*3,dict(production=[0]*3,stocks=[0]*3,spent=0,destroyed=True)),
]
for missiles,rates,stocks,want in fixtures:ck(model.bombard(missiles,rates,stocks,lambda:.5)==want,'separate injected-RNG model fixture')
print(f'{checks} checks passed over 10 normally completed DOS sessions, 1 excluded timeout, 4 static byte reads and 5 separate model fixtures.')
