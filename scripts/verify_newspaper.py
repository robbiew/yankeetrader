"""Verify original newspaper replays, event contents, history rotation and provenance."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
TODAY=b'TODAY FIRST\r\n  - TODAY BULLET\r\n *** TODAY COMBAT\r\n +++ TODAY ACTION\r\n-=* TODAY PLAYER\r\nTODAY LAST\r\n'
YESTERDAY=b'YESTERDAY FIRST\r\nYESTERDAY SECOND\r\nYESTERDAY LAST\r\n'
LOGIN=rb'-=\*=- \d{2}:\d{2}:\d{2} Q  Logged on -=\*=-\r\n'
TEAM=b'Q  Created Team 1 -=- News Team\r\n'
MISSING=b'*** GAME FILE [YTYNEWS.DAT] NOT FOUND! ***\r\n'

def check(path):
 source=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-create/YTDATA.DAT').read_bytes()
 base=bytearray(source)
 for off,value in {57:1,89:0}.items():mbf.put(base,2,off,value)
 expected=json.loads((ROOT/'research/yt-newspaper/expected.json').read_text())
 results=json.loads((path/'results.json').read_text())['scenarios'];by_name={r['name']:r for r in results}
 assert len(results)==len(expected) and set(by_name)==set(expected),'scenario set'
 for result in results:
  name=result['name'];d=path/name;gold=expected[name]
  assert result==json.loads((d/'result.json').read_text()),(name,'manifest copies')
  assert result['complete'] and result['source_sha256']==sha(source) and result['baseline_sha256']==sha(base),name
  assert result['command']==gold['command'] and result['maintenance']==gold['maintenance'] and result['parent']==gold['parent'],(name,'inputs')
  assert result['date']==(gold['maintenance'] or '10/24/2026') and result['time']=='00:00:00',name
  exe='YTMAINT.EXE' if gold['maintenance'] else 'YT.EXE'
  assert result['executable']==exe and result['executable_sha256']==sha((ROOT/'archive/dos-original'/exe).read_bytes()),name
  assert result['keyfeed_sha256']==sha((ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()),name
  before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
  assert sha(before)==result['before_sha256'] and sha(after)==result['after_sha256'],name
  assert before==(gzip.decompress((path/gold['parent']/'after.dat.gz').read_bytes()) if gold['parent'] else base),(name,'world input')
  keys=b'\r~~~~~\r~'+gold['command'].encode()+b'\r~~~~'+b'\rQ;Y\r~~'*24
  assert (d/'KEYS.TXT').read_bytes()==keys,(name,'keystrokes')
  retained={'KEYS.TXT','before.dat.gz','after.dat.gz','transcript.txt','dosbox.log'}
  news={}
  for filename in ('YTNEWS.DAT','YTYNEWS.DAT'):
   news[filename]={}
   for tag in ('before','after'):
    f=filename+'.'+tag+'.gz';declared=result['news'][filename][tag+'_sha256']
    p=d/f
    assert p.exists()==(declared is not None),(name,f,'presence')
    b=gzip.decompress(p.read_bytes()) if declared is not None else None
    assert b is None or sha(b)==declared,(name,f,'digest')
    news[filename][tag]=b
    if b is not None:retained.add(f)
  assert set(result['files'])==retained,(name,'artifact set')
  for f,h in result['files'].items():assert sha((d/f).read_bytes())==h,(name,f)
  initial_today=TODAY;initial_yesterday=YESTERDAY
  if name=='empty-today':initial_today=b''
  if name=='missing-yesterday':initial_yesterday=None
  if name=='dos-eof':initial_today=b'TODAY FIRST\r\n\x1aHIDDEN TAIL\r\n'
  if name=='empty-yesterday':initial_yesterday=b''
  if name=='yesterday-eof':initial_yesterday=b'YESTERDAY FIRST\r\n\x1aHIDDEN TAIL\r\n'
  if gold['parent']:
   for filename in news:assert news[filename]['before']==gzip.decompress((path/gold['parent']/(filename+'.after.gz')).read_bytes()),(name,'linked newspaper')
  else:assert news['YTNEWS.DAT']['before']==initial_today and news['YTYNEWS.DAT']['before']==initial_yesterday,(name,'newspaper input')
  text=(d/'transcript.txt').read_text()
  if gold['maintenance']:
   assert 'Daily Maintenance Completed OK' in text and 'ERROR' not in text,name
   assert news['YTYNEWS.DAT']['after']==TODAY+b'\x1a',(name,'rotation')
   current=news['YTNEWS.DAT']['after']
   date='10-25-2026' if name=='rotate-next-day' else '10-24-2026'
   assert current.startswith(('00:00:00 '+date+': Maintenance Program Ran').encode()) and b'TODAY FIRST' not in current and b'YESTERDAY FIRST' not in current,name
   assert ('Maintenance not needed!' in text)==(name=='rotate-same-day'),name
   assert mbf.get(after,1,81)==(298 if name=='rotate-next-day' else 297),name
  else:
   assert 'Returning to Yankee Trader Local Logon Program' in text and 'Entering a new player' not in text and 'Entering a new ship' not in text,name
   prompt="Do you want to read [T]oday's or [Y]esterday's news? [T/Y] -=> "
   assert text.count(prompt)==gold['prompts'],(name,'selection retry')
   section=text.rsplit(prompt,1)[1].split('Computer command (?=help)?',1)[0]
   for fragment in gold['contains']:assert fragment in section,(name,fragment)
   for fragment in gold['absent']:assert fragment not in section,(name,fragment)
   selected=news['YTYNEWS.DAT' if gold['day']=='yesterday' else 'YTNEWS.DAT']['after']
   if selected is not None:
    position=0
    for line in selected.split(b'\x1a',1)[0].decode('cp437').splitlines():
     index=section.find(line,position)
     assert index>=0,(name,'selected news line missing or reordered',line)
     position=index+len(line)
   for off in (49,53,57,61,65,69,73,77,81,93,97,113,117,121,125,129):assert mbf.get(before,2,off)==mbf.get(after,2,off),(name,off,'ship resource mutation')
   assert mbf.get(after,2,49)==500 and mbf.get(after,2,57)==1,name
   assert news['YTYNEWS.DAT']['after']==news['YTYNEWS.DAT']['before'],(name,'yesterday changed during read')
   prefix=news['YTNEWS.DAT']['before'].split(b'\x1a',1)[0]
   current=news['YTNEWS.DAT']['after'];assert current.startswith(prefix),(name,'append lost history')
   tail=current[len(prefix):]
   extra=TEAM if name=='team-created' else MISSING if name=='missing-yesterday' else b''
   assert re.fullmatch(LOGIN+re.escape(extra)+rb'\x1a',tail),(name,'unexpected log output',tail)
   assert b'ABCD' not in current,(name,'team password leaked into public news')
   if name in ('team-created','team-reconnect'):
    assert mbf.get(after,2,89)==1 and current.count(TEAM)==1,name
   if name=='team-reconnect':assert len(re.findall(LOGIN,current))==2,(name,'reconnect append')
 # Cross-check complete primitive byte reads against each independently relocated EXE.
 for filename in ('rea.json','maintenance-rea.json'):
  entries=json.loads((ROOT/'research/yt-newspaper'/filename).read_text())['byte_evidence']
  for entry in entries:
   executable=(ROOT/'archive/dos-original'/entry['subject']['name']).read_bytes()
   assert entry['subject']['digest']['sha256']==sha(executable),'REA target'
   u16=lambda p:int.from_bytes(executable[p:p+2],'little')
   image=bytearray(executable[u16(8)*16:])
   for i in range(u16(6)):
    pos=u16(24)+4*i;off=u16(pos)+16*u16(pos+2)
    image[off:off+2]=((int.from_bytes(image[off:off+2],'little')+0x1000)&65535).to_bytes(2,'little')
   r=entry['normalized_result'];offset=int(r['address'],16)-65536
   assert r['complete'] and r['returned_bytes']==r['requested_bytes'] and image[offset:offset+r['returned_bytes']].hex()==r['bytes_hex'],'REA bytes'
 print(f'Verified {len(results)} DOS newspaper sessions, {len(results)*2} world snapshots, event/reconnect chains and rotation controls.')
if __name__=='__main__':check(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'research/yt-newspaper/dos')
