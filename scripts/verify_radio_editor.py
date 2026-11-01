"""Verify original multiline editor controls and exact per-line records."""
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
START='C;5;Enemy;Y\r~~'
END='\r~~~~6;1'
EXPECTED={
 'list-continue':dict(command=START+'FIRST\rSECOND\r\r~~L\r~~C\r~~THIRD\r\r~~S'+END,patches=[]),
 'edit-accept':dict(command=START+'alpha alpha\rSECOND\r\r~~E\r~1\r~alpha\r~BETA\r~Y\r~~S'+END,patches=[]),
 'edit-reject':dict(command=START+'alpha alpha\r\r~~E\r~1\r~alpha\r~BETA\r~N\r~~S'+END,patches=[]),
 'abort':dict(command=START+'FIRST\rSECOND\r\r~~A;Y',patches=[]),
 'limit':dict(command=START+'\r'.join('LINE%02d'%i for i in range(1,21))+'\r~~~~S'+END,patches=[]),
 'public-two':dict(command='C;5;ALL\r~~PUBLIC FIRST\rPUBLIC SECOND\r\r~~S'+END,patches=[]),
}
LINES={'list-continue':['FIRST','SECONDTHIRD'],'edit-accept':['BETA alpha','SECOND'],'edit-reject':['alpha alpha'],'abort':[],'limit':['LINE%02d'%i for i in range(1,21)],'public-two':['PUBLIC FIRST','PUBLIC SECOND']}

GRAPH={1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}

def check(path=ROOT/'research/yt-radio-editor/dos'):
 path=Path(path)
 source_dir=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
 base=(source_dir/'YTDATA.DAT').read_bytes()
 initial_aux={p.name:p.read_bytes()for p in source_dir.iterdir()if p.is_file()and p.suffix.upper()in('.DAT','.ASC')and p.name!='YTDATA.DAT'}
 assert gzip.decompress((path/'baseline.dat.gz').read_bytes())==base
 summary=json.loads((path/'results.json').read_text());rows=summary['scenarios']
 assert summary['recipe']=='radio-editor-v1' and len(rows)==len(EXPECTED) and {r['name']for r in rows}==set(EXPECTED)
 recipe=json.loads((path/'recipe.json').read_text());assert recipe['recipe']=='radio-editor-v1'
 assert {r['name']:r for r in recipe['scenarios']}=={n:dict(name=n,**c)for n,c in EXPECTED.items()}
 worlds={};aux={}
 for r in rows:
  n=r['name'];c=EXPECTED[n];d=path/n
  assert r==json.loads((d/'result.json').read_text())
  for k,v in dict(name=n,**c).items():assert r[k]==v,(n,k)
  assert r['recipe']=='radio-editor-v1' and r['complete'] and not r['timed_out'] and r['date']=='10/24/2026' and r['time']=='00:00:00' and r['baseline_sha256']==SHA(base)
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
   assert rawbefore==initial_aux,(n,'source auxiliary baseline')
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
  identity='Enemy'if actor==3 else'Tester'
  assert re.findall(r'^Welcome ([^\r\n]+)!$',text,re.MULTILINE)==[identity],(n,'login identity')
  alias=before[(actor-1)*137:(actor-1)*137+41].decode('cp437').rstrip()
  aliases=[a.rstrip()for a in re.findall(r'^Name[ \t]+:[ \t]+([^\r\n]+)$',text,re.MULTILINE)]
  assert aliases and set(aliases)=={alias},(n,'login alias',aliases)
  for offset in (45,49,53,57,61,65,69,73,77,81,89,93,97,105,113,121,125,129):assert mbf.get(before,actor,offset)==mbf.get(after,actor,offset),(n,'resource',offset)
  mail=rawafter['YTRMSG.DAT'];assert len(mail)%86==0
  packets=[(mbf.get(mail[i:i+86],1,0),mbf.get(mail[i:i+86],1,4),mbf.get(mail[i:i+86],1,8),mail[i+12:i+86])for i in range(0,len(mail),86)]
  expected_packets=[(30 if n=='public-two'else 1,-2 if n=='public-two'else 3,2,line.encode().ljust(74,b' '))for line in LINES[n]]
  assert packets==expected_packets,(n,packets)
  assert text.count('Transmission successful!')==int(n!='abort'),n
  if n=='edit-accept':assert 'Change Saved!'in text
  if n=='edit-reject':assert 'CANCELED!'in text
  if n=='limit':assert 'Message full!'in text
  if n=='list-continue':assert text.count('[L] List [S] Send [A] Abort [C] Continue [E] Edit')>=3
  news=rawafter['YTNEWS.DAT']
  if n=='public-two':assert news.endswith(b'  -  Message from: Q \r\n  -  PUBLIC FIRST\r\n  -  PUBLIC SECOND\r\n\x1a')
  else:
   for line in LINES[n]:assert b'  -  '+line.encode()+b'\r\n'not in news
 print('Verified 6 DOS editor controls: exact inputs, baseline auxiliary files, actor, line packets, first replacement, Continue, rejection, abort, 20-line cap and public text.')


if __name__=='__main__':check(Path(sys.argv[1])if len(sys.argv)>1 else ROOT/'research/yt-radio-editor/dos')
