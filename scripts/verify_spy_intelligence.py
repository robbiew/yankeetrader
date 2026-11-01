"""Independently check copied DOS spy fixtures, resources and positive reports."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mbf', ROOT/'archive/analysis/yt-maint/experiments.py')
mbf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mbf)
SHA = lambda b: hashlib.sha256(b).hexdigest()
CASES = {
 'visible': ([[3,57,101],[3,125,0]], 1, 1, 0),
 'full-cloak': ([[3,57,101],[3,125,1]], 0, 0, 0),
 'partial-cloak': ([[3,57,101],[3,125,.5]], 1, 1, 1),
 'two-ships': ([[3,57,101],[3,125,0],[4,57,101],[4,125,0]], 1, 1, 0),
 'caller-only': ([[3,57,200],[3,125,0]], 0, 0, 0),
 'disruption': ([[1,57,54],[53,41,3],[54,41,2]], 1, 0, 0),
}

def check(path=ROOT/'research/yt-spies/intelligence/dos'):
 path=Path(path)
 source=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
 base=bytearray(source)
 for offset,value in {57:1,81:2000000,89:0,125:0}.items():mbf.put(base,2,offset,value)
 mbf.put(base,52,65,1)
 for sector,to in [(100,1),(101,102),(102,101)]:
  record=51+sector;base[(record-1)*137:record*137]=bytes(137);mbf.put(base,record,41,to)
 mbf.put(base,52,41,100);mbf.put(base,3,57,200)
 results=json.loads((path/'results.json').read_text())['scenarios']
 assert len(results)==len(CASES) and {r['name']for r in results}==set(CASES)
 for r in results:
  name=r['name'];d=path/name;patches,headers,ships,shimmer=CASES[name]
  assert r==json.loads((d/'result.json').read_text())
  assert r['complete'] and r['source_sha256']==SHA(source) and r['baseline_sha256']==SHA(base)
  assert r['executable_sha256']==SHA((ROOT/'archive/dos-original/YT.EXE').read_bytes())
  assert r['keyfeed_sha256']==SHA((ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes())
  assert r['patches']==patches and r['dos_date']=='10/24/2026' and r['dos_time']=='00:00:00'
  expected=bytearray(base)
  for record,offset,value in patches:mbf.put(expected,record,offset,value)
  before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
  assert before==expected and r['before_sha256']==SHA(before) and r['after_sha256']==SHA(after)
  assert set(r['files'])=={'KEYS.TXT','transcript.txt','scoreboard.txt','dosbox.log'}
  for f,h in r['files'].items():assert SHA((d/f).read_bytes())==h,(name,f)
  hire='P;9;1;101\r~~~~\r~~0;'
  command=hire+'M;100;C;15;1;M;1;C;15;1'
  if name=='caller-only':command=hire.replace('101','100')+'M;100;C;15;1;M;1;C;15;1'
  if name=='disruption':command='P;9;1;2\r~~~~\r~~0;P;0;C;15;1;P;0;C;15;1'
  assert r['command']==command
  assert (d/'KEYS.TXT').read_bytes()==b'\r~~~~~\r~'+command.encode()+b'\r~~~~'+b'\rQ;Y\r~~'*24
  text=(d/'transcript.txt').read_text()
  assert 'Returning to Yankee Trader'in text and 'Entering a new ship'not in text and 'Entering a new player'not in text
  assert text.count('RADIO MESSAGE FROM SPY')==headers and text.count('Other Ships:')==ships and text.count('The spy detected the shimmering')==shimmer,name
  assert text.count('** Space-time disruption detected! **')==int(name=='disruption'),name
  locations=[int(x) for x in re.findall(r'Spy # 1 will hunt in sector (\d+)',text)]
  if name=='caller-only':assert len(locations)==3 and locations[:2]==[100,1] and locations[2]in[100,2,3,4,5,6]
  else:assert locations==([2,3,1]if name=='disruption'else[101,102,101]),(name,locations)
  records=re.findall(r'^    .* - Fighters: .*$',text,re.MULTILINE)
  expected_records=['    Enemy  - Team: 1 - Fighters: 1000 - Shields: 10']if ships else[]
  if name=='two-ships':expected_records.append('    Third  - Fighters: 1000 - Shields: 10000')
  assert records==expected_records,(name,'complete ordered ship records',records)
  assert mbf.get(after,2,81)==1667000 and mbf.get(after,2,49)==497 and r['actor_turns']==497,name
  for record in (2,3,4):assert mbf.get(after,record,125)==mbf.get(before,record,125),(name,'persistent cloak changed')
 print('Verified 6 DOS spy controls: positive ships, partial/full cloak, multiple ships, caller exclusion, disruption and unchanged saved cloak.')

if __name__=='__main__':check(Path(sys.argv[1])if len(sys.argv)>1 else ROOT/'research/yt-spies/intelligence/dos')
