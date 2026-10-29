"""Recover DOS newspaper behavior in disposable copies; never mount the archive."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-create'
TODAY=b'TODAY FIRST\r\n  - TODAY BULLET\r\n *** TODAY COMBAT\r\n +++ TODAY ACTION\r\n-=* TODAY PLAYER\r\nTODAY LAST\r\n'
YESTERDAY=b'YESTERDAY FIRST\r\nYESTERDAY SECOND\r\nYESTERDAY LAST\r\n'

def scenarios():
 return [
  ('today','C;8;T\r~~1',TODAY,YESTERDAY,None),
  ('yesterday','C;8;Y\r~~1',TODAY,YESTERDAY,None),
  ('invalid-choice','C;8;X;T\r~~1',TODAY,YESTERDAY,None),
  ('lowercase','C;8;t\r~~1',TODAY,YESTERDAY,None),
  ('empty-today','C;8;T\r~~1',b'',YESTERDAY,None),
  ('missing-yesterday','C;8;Y\r~~1',TODAY,None,None),
  ('dos-eof','C;8;T\r~~1',b'TODAY FIRST\r\n\x1aHIDDEN TAIL\r\n',YESTERDAY,None),
  ('empty-yesterday','C;8;Y\r~~1',TODAY,b'',None),
  ('yesterday-eof','C;8;Y\r~~1',TODAY,b'YESTERDAY FIRST\r\n\x1aHIDDEN TAIL\r\n',None),
  ('team-created','T;2\r~~~~News Team\r~~~~ABCD\r~~~~1;C;8;T\r~~1',TODAY,YESTERDAY,None),
  ('rotate-next-day','',TODAY,YESTERDAY,'10/25/2026'),
  ('rotate-same-day','',TODAY,YESTERDAY,'10/24/2026'),
 ]

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('destination',type=Path);parser.add_argument('--only',nargs='+');args=parser.parse_args()
 dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=False)
 dosbox=shutil.which('dosbox-staging')
 if dosbox is None:parser.error('DOSBox Staging not found')
 spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
 source=(SOURCE/'YTDATA.DAT').read_bytes();base=bytearray(source)
 for off,value in {57:1,89:0}.items():mbf.put(base,2,off,value)
 base=bytes(base);sha=lambda b:hashlib.sha256(b).hexdigest()
 cases=scenarios()
 if args.only:
  if set(args.only)-{c[0] for c in cases}:parser.error('unknown probe')
  cases=[c for c in cases if c[0] in args.only]
 def run(case,parent=None):
  name,command,today,yesterday,maintenance=case;d=dest/name;d.mkdir()
  for p in SOURCE.iterdir():
   if p.suffix.upper() in ('.DAT','.EXE','.DOC','.DEF','.ASC','.ANS'):shutil.copy2(p,d/p.name)
  for filename in ('YTMAINT.EXE',):shutil.copy2(ROOT/'archive/dos-original'/filename,d/filename)
  feeder=ROOT/'archive/analysis/yt-combat/KEYFEED.COM';shutil.copy2(feeder,d/feeder.name)
  before=base if parent is None else gzip.decompress((dest/parent/'after.dat.gz').read_bytes())
  (d/'YTDATA.DAT').write_bytes(before)
  news={'YTNEWS.DAT':today,'YTYNEWS.DAT':yesterday}
  if parent is not None:
   prior=json.loads((dest/parent/'result.json').read_text())
   news={f:gzip.decompress((dest/parent/(f+'.after.gz')).read_bytes()) if prior['news'][f]['after_sha256'] is not None else None for f in news}
  for filename,payload in news.items():
   if payload is None:(d/filename).unlink(missing_ok=True)
   else:(d/filename).write_bytes(payload)
  keys=b'\r~~~~~\r~'+command.encode()+b'\r~~~~'+b'\rQ;Y\r~~'*24
  (d/'KEYS.TXT').write_bytes(keys)
  date=maintenance or '10/24/2026';exe='YTMAINT.EXE' if maintenance else 'YT.EXE'
  invocation='ytmaint > game.log' if maintenance else 'local TESTER > game.log'
  commands=['mount c '+str(d),'c:','date '+date,'time 00:00:00']+([] if maintenance else ['keyfeed'])+[invocation,'exit']
  complete=True
  try:
   with (d/'dosbox.log').open('w') as log:
    subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[item for c in commands for item in ('-c',c)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=150,check=True)
  except subprocess.TimeoutExpired:complete=False
  after=(d/'YTDATA.DAT').read_bytes();transcript=(d/'GAME.LOG').read_bytes().decode('cp437').replace('\\r\\n','\n').replace('\r\n','\n')
  (d/'transcript.txt').write_text(transcript)
  retained={'KEYS.TXT','transcript.txt','dosbox.log','before.dat.gz','after.dat.gz'}
  for tag,data in [('before',before),('after',after)]:(d/(tag+'.dat.gz')).write_bytes(gzip.compress(data,mtime=0))
  news_result={}
  for filename,payload in news.items():
   saved=(d/filename).read_bytes() if (d/filename).exists() else None
   news_result[filename]={'before_sha256':sha(payload) if payload is not None else None,'after_sha256':sha(saved) if saved is not None else None}
   for tag,data in [('before',payload),('after',saved)]:
    if data is not None:
     f=filename+'.'+tag+'.gz';(d/f).write_bytes(gzip.compress(data,mtime=0));retained.add(f)
  result={'name':name,'command':command,'maintenance':maintenance,'parent':parent,'complete':complete and ('Returning to Yankee Trader' in transcript if not maintenance else 'Maintenance Complete' in transcript),
    'source_sha256':sha(source),'baseline_sha256':sha(base),'before_sha256':sha(before),'after_sha256':sha(after),'executable':exe,'executable_sha256':sha((d/exe).read_bytes()),'keyfeed_sha256':sha(feeder.read_bytes()),
    'date':date,'time':'00:00:00','news':news_result,'files':{f:sha((d/f).read_bytes()) for f in retained}}
  (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  for p in d.iterdir():
   if p.is_file() and p.name not in retained|{'result.json'}:p.unlink()
  print(name,result['complete'],flush=True);return result
 with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,cases))
 if not args.only or 'team-created' in args.only:results.append(run(('team-reconnect','C;8;T\r~~1',None,None,None),'team-created'))
 (dest/'results.json').write_text(json.dumps({'scenarios':results},indent=2)+'\n')
if __name__=='__main__':main()
