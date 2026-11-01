"""Verify original broadcast records, read transitions and exact replay chains."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
SHA=lambda b:hashlib.sha256(b).hexdigest()
SEND='C;5;ALL\r~~YT BROADCAST PROBE\r\r~~S\r~~~~6;1'
EXPECTED={
 'broadcast-send':dict(command=SEND,patches=[]),
 'broadcast-abort':dict(command=SEND.replace('~~S','~~A;Y'),patches=[]),
 'recipient-read':dict(command='\r~~~~C;6;1',patches=[],parent='broadcast-send',actor='ENEMY'),
 'sender-read':dict(command='\r~~~~C;6;1',patches=[],parent='broadcast-send'),
 'recipient-again':dict(command='\r~~~~C;6;1',patches=[],parent='recipient-read',actor='ENEMY'),
 'sender-after-recipient':dict(command='\r~~~~C;6;1',patches=[],parent='recipient-read'),
}
GRAPH={1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}

def check(path=ROOT/'research/yt-broadcast-radio/dos'):
 path=Path(path)
 base=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
 assert gzip.decompress((path/'baseline.dat.gz').read_bytes())==base
 summary=json.loads((path/'results.json').read_text());rows=summary['scenarios']
 assert summary['recipe']=='broadcast-radio-v1' and len(rows)==len(EXPECTED) and {r['name']for r in rows}==set(EXPECTED)
 recipe=json.loads((path/'recipe.json').read_text());assert recipe['recipe']=='broadcast-radio-v1'
 assert {r['name']:r for r in recipe['scenarios']}=={n:dict(name=n,**c)for n,c in EXPECTED.items()}
 worlds={};aux={}
 for r in rows:
  n=r['name'];c=EXPECTED[n];d=path/n
  assert r==json.loads((d/'result.json').read_text())
  for k,v in dict(name=n,**c).items():assert r[k]==v,(n,k)
  assert r['recipe']=='broadcast-radio-v1' and r['complete'] and not r['timed_out'] and r['date']=='10/24/2026' and r['time']=='00:00:00' and r['baseline_sha256']==SHA(base)
  for filename,h in r['binaries'].items():
   source=ROOT/('archive/analysis/yt-combat/'+filename if filename=='KEYFEED.COM'else 'archive/dos-original/'+filename)
   assert SHA(source.read_bytes())==h,(n,filename)
  assert set(r['binaries'])=={'YT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM'}
  assert set(r['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
  for f,h in r['files'].items():assert SHA((d/f).read_bytes())==h,(n,f)
  assert (d/'DOSDATE.LOG').read_text().splitlines()[0]=='Current date: Sat 10/24/2026'
  assert (d/'DOSTIME.LOG').read_text().splitlines()[0]=='Current time: 0:00:00.00am'
  before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes());worlds[n]=(before,after)
  rawbefore={k:bytes.fromhex(v)for k,v in json.loads(gzip.decompress((d/'side-before.json.gz').read_bytes())).items()}
  side=json.loads(gzip.decompress((d/'sidefiles.json.gz').read_bytes()));assert set(side)==set(rawbefore)
  rawafter={k:bytes.fromhex(v['hex'])for k,v in side.items()}
  for f,v in side.items():assert v['before_sha256']==SHA(rawbefore[f])and v['after_sha256']==SHA(rawafter[f]),(n,f)
  aux[n]=(rawbefore,rawafter)
  if c.get('parent'):
   expected=bytearray(worlds[c['parent']][1]);assert rawbefore==aux[c['parent']][1],(n,'auxiliary chain')
   patches=[]
  else:
   expected=bytearray(base)
   for sector,warps in GRAPH.items():
    start=(51+sector-1)*137;expected[start:start+137]=bytes(137)
    for o,v in zip(range(41,65,4),warps):mbf.put(expected,51+sector,o,v)
   patches=[[2,o,v]for o,v in {45:0,49:500,57:1,89:0,93:0,105:0,125:0}.items()]
   patches += [[3,o,v]for o,v in {45:0,57:2,61:42,53:7,89:0,125:1}.items()]
   patches += [[52,65,1],[152,65,2],[3053,93,101],[153,93,2],[4053,73,0],[4053,77,12]]
  patches+=c['patches'];assert r['applied_patches']==patches
  for record,offset,value in patches:mbf.put(expected,record,offset,value)
  assert before==expected,(n,'starting world')
  assert (d/'KEYS.TXT').read_bytes()==('\r~~~~~\r~'+c['command']+'\r~~~~'+'\rQ;Y\r~~'*24).encode()
  text=(d/'transcript.txt').read_text()
  assert 'Returning to Yankee Trader Local Logon Program...'in text and 'Entering a new player'not in text and 'Entering a new ship'not in text
  actor=3 if c.get('actor')=='ENEMY'else 2
  for offset in (45,49,53,57,61,65,69,73,77,81,89,93,97,105,113,121,125,129):assert mbf.get(before,actor,offset)==mbf.get(after,actor,offset),(n,'resource',offset)
  mail=rawafter['YTRMSG.DAT'];assert len(mail)%86==0
  packets=[(mbf.get(mail[i:i+86],1,0),mbf.get(mail[i:i+86],1,4),mbf.get(mail[i:i+86],1,8),mail[i+12:i+86].rstrip())for i in range(0,len(mail),86)]
  if n=='broadcast-abort':
   assert not packets and 'Transmission successful!'not in text
  else:
   counter=30 if n=='broadcast-send'else 26 if n in ('recipient-again','sender-after-recipient')else 28
   assert packets==[(counter,-2,2,b'YT BROADCAST PROBE')],(n,packets)
   assert text.count('YT BROADCAST PROBE')==2,(n,'body count')
   assert text.count('Transmission successful!')==int(n=='broadcast-send')
   headers=[line.rstrip()for line in text.splitlines()if line.startswith('Message to:')]
   assert headers==['Message to: All * From: Q']*(1 if n=='broadcast-send'else 2),(n,headers)
   if n!='broadcast-send':
    startup=text.split('<Computer activated>')[0]
    assert startup.count('YT BROADCAST PROBE')==1,(n,'startup delivery')
 print('Verified 6 DOS broadcast sessions: send/abort, exact world/auxiliary chains, shared counter 30 -> 28 -> 26, repeated reader and sender-after-recipient delivery.')


if __name__=='__main__':check(Path(sys.argv[1])if len(sys.argv)>1 else ROOT/'research/yt-broadcast-radio/dos')
