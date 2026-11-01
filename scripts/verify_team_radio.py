"""Verify DOS team radio routing, independent flags and exact auxiliary chains."""
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
SHA=lambda b:hashlib.sha256(b).hexdigest()
SEND='C;5;TEAM\r~~YT TEAM PROBE\r\r~~S\r~~~~6;1'
COMMON=[[2,89,1],[3,89,1],[4,89,1],[5,89,0],[6,89,0]]
EXPECTED={
 'team-send':dict(command=SEND,patches=COMMON,roster=[2,3,4]),
 'team-abort':dict(command=SEND.replace('~~S','~~A;Y'),patches=COMMON,roster=[2,3,4]),
 'no-team':dict(command='C;5;TEAM;1',patches=[[2,89,0],[3,89,1],[4,89,1]],roster=[3,4]),
 'two-members':dict(command=SEND,patches=[[2,89,1],[3,89,0],[4,89,1],[5,89,0],[6,89,0]],roster=[2,4]),
 'recipient-read':dict(command='\r~~~~C;6;1',patches=[],parent='team-send',actor='ENEMY'),
 'sender-read':dict(command='\r~~~~C;6;1',patches=[],parent='team-send'),
 'recipient-left':dict(command='\r~~~~C;6;1',patches=[[3,89,0],[52,117,0]],parent='team-send',actor='ENEMY'),
 'outsider-read':dict(command='\r~~~~C;6;1',patches=[],parent='two-members',actor='ENEMY'),
 'late-join':dict(command='\r~~~~C;6;1',patches=[[3,89,1],[52,121,3]],parent='two-members',actor='ENEMY'),
}
GRAPH={1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}

def check(path=ROOT/'research/yt-team-radio/dos'):
 path=Path(path)
 source_dir=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
 base=(source_dir/'YTDATA.DAT').read_bytes()
 initial_aux={p.name:p.read_bytes()for p in source_dir.iterdir()if p.is_file()and p.suffix.upper()in('.DAT','.ASC')and p.name!='YTDATA.DAT'}
 assert gzip.decompress((path/'baseline.dat.gz').read_bytes())==base
 summary=json.loads((path/'results.json').read_text());rows=summary['scenarios']
 assert summary['recipe']=='team-radio-v1' and len(rows)==len(EXPECTED) and {r['name']for r in rows}==set(EXPECTED)
 recipe=json.loads((path/'recipe.json').read_text());assert recipe['recipe']=='team-radio-v1'
 assert {r['name']:r for r in recipe['scenarios']}=={n:dict(name=n,**c)for n,c in EXPECTED.items()}
 worlds={};aux={}
 for r in rows:
  n=r['name'];c=EXPECTED[n];d=path/n
  assert r==json.loads((d/'result.json').read_text())
  for k,v in dict(name=n,**c).items():assert r[k]==v,(n,k)
  assert r['recipe']=='team-radio-v1' and r['complete'] and not r['timed_out'] and r['date']=='10/24/2026' and r['time']=='00:00:00' and r['baseline_sha256']==SHA(base)
  for filename,h in r['binaries'].items():
   source=ROOT/('archive/analysis/yt-combat/'+filename if filename=='KEYFEED.COM'else 'archive/dos-original/'+filename)
   assert SHA(source.read_bytes())==h,(n,filename)
  assert set(r['binaries'])=={'YT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM'}
  assert set(r['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}
  for f,h in r['files'].items():assert SHA((d/f).read_bytes())==h,(n,f)
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
   assert rawbefore==initial_aux,(n,'source auxiliary baseline')
   expected=bytearray(base)
   for sector,warps in GRAPH.items():
    start=(51+sector-1)*137;expected[start:start+137]=bytes(137)
    for o,v in zip(range(41,65,4),warps):mbf.put(expected,51+sector,o,v)
   patches=[[2,o,v]for o,v in {45:0,49:500,57:1,89:0,93:0,105:0,125:0}.items()]
   patches += [[3,o,v]for o,v in {45:0,57:2,61:42,53:7,89:0,125:1}.items()]
   patches += [[52,65,1],[152,65,2],[3053,93,101],[153,93,2],[4053,73,0],[4053,77,12]]
   # The capture applies base patches after the raw roster overlay.
   start=51*137;expected[start:start+41]=b'Orion'.ljust(41,b' ');expected[start+113:start+117]=b'ABCD'
   for o,v in [(73,5),(77,c['roster'][0])]+list(zip((109,117,121,125),c['roster']+[0]*(4-len(c['roster'])))):mbf.put(expected,52,o,v)
  patches+=c['patches'];assert r['applied_patches']==patches
  for record,offset,value in patches:mbf.put(expected,record,offset,value)
  assert before==expected,(n,'starting world')
  assert (d/'KEYS.TXT').read_bytes()==('\r~~~~~\r~'+c['command']+'\r~~~~'+'\rQ;Y\r~~'*24).encode()
  text=(d/'transcript.txt').read_text()
  assert 'Returning to Yankee Trader Local Logon Program...'in text and 'Entering a new player'not in text and 'Entering a new ship'not in text
  actor=3 if c.get('actor')=='ENEMY'else 2
  identity='Enemy'if actor==3 else'Tester'
  assert re.findall(r'^Welcome ([^\r\n]+)!$',text,re.MULTILINE)==[identity],(n,'login identity')
  alias=before[(actor-1)*137:(actor-1)*137+41].decode('cp437').rstrip()
  aliases=[a.rstrip()for a in re.findall(r'^Name[ \t]+:[ \t]+([^\r\n]+)$',text,re.MULTILINE)]
  assert aliases and set(aliases)=={alias},(n,'login alias',aliases)
  for offset in (49,53,57,61,65,69,73,77,81,93,97,105,113,121,125,129):assert mbf.get(before,actor,offset)==mbf.get(after,actor,offset),(n,'resource',offset)
  mail=rawafter['YTRMSG.DAT'];assert len(mail)%86==0
  packets=[(mbf.get(mail[i:i+86],1,0),mbf.get(mail[i:i+86],1,4),mbf.get(mail[i:i+86],1,8),mail[i+12:i+86].rstrip())for i in range(0,len(mail),86)]
  if n in ('team-abort','no-team'):
   assert not packets and 'Transmission successful!'not in text
   if n=='no-team':assert "You Don't belong to a team!"in text
  else:
   destinations=[2,4]if n in ('two-members','outsider-read','late-join')else[2,3,4]
   read=3 if n in ('recipient-read','recipient-left')else 2 if n=='sender-read'else 0
   assert packets==[(int(to!=read),to,2,b'YT TEAM PROBE')for to in destinations],(n,packets)
   if n in ('team-send','two-members'):assert text.count('Transmission successful!')==1
   else:
    expected_count=4 if n=='sender-read'else 0 if n in ('outsider-read','late-join')else 2
    assert text.count('YT TEAM PROBE')==expected_count,(n,'delivery count')
 print('Verified 9 DOS team-radio sessions: exact world/auxiliary chains, roster fanout, independent read flags, abort, outsider isolation and membership-change delivery.')

if __name__=='__main__':check(Path(sys.argv[1])if len(sys.argv)>1 else ROOT/'research/yt-team-radio/dos')
