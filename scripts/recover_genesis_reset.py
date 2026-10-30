"""Recover Genesis/reset behavior only in disposable copies of original DOS worlds."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-trade-earth'
RECIPE='genesis-reset-v1'
BINS=('YT.EXE','RMT-INIT.EXE','YTMAINT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')
SHA=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)


def cases():
 out=[]
 def add(name,cached=300,owned=300,threshold=300,reply='Y',expect='reset',mode='game',**kw):out.append(dict(name=name,cached=cached,owned=owned,threshold=threshold,reply=reply,expect=expect,mode=mode,**kw))
 add('owned-299',299,299,expect='refusal')
 add('owned-300')
 add('owned-301',301,301)
 add('cancel-no',reply='N',expect='refusal')
 add('cancel-blank',reply='',expect='refusal')
 add('cached-only',owned=0)
 add('records-only',cached=0,expect='refusal')
 add('fallback-short',199,199,19,expect='refusal')
 add('fallback-200',200,200,19)
 add('threshold-20',20,20,20)
 add('disabled-301',999,999,301,expect='refusal')
 add('lottery-zero',20,20,20,patches=[[1,101,0]])
 add('cargo-low',20,20,20,patches=[[1,121,4]])
 add('cargo-high',20,20,20,patches=[[1,121,1001]])
 add('custom-defaults',20,20,20,patches=[[1,o,v]for o,v in {49:777,65:31,69:4321,73:17,77:9,101:7,121:850,125:7000}.items()])
 add('winner-mapping',alias_case_pair=True,score_sentinel=True)
 add('standalone-no',mode='standalone',reply='N',expect='standalone-cancel')
 add('standalone-blank',mode='standalone',reply='',expect='standalone-cancel')
 add('standalone-yes',mode='standalone')
 add('standalone-threshold-high',threshold=301,mode='standalone')
 add('missing-initializer',alias_case_pair=True,omit=['RMT-INIT.EXE'],expect='chain-error')
 add('malformed-marker',mode='standalone',marker='"MISSING.DEF"\r\n',expect='marker-error')
 add('marker-resume',mode='standalone',reply='N',parent='missing-initializer')
 add('first-maintenance',mode='maintenance',parent='winner-mapping',expect='maintenance')
 return out


def auxfiles(d):return {p.name:p.read_bytes()for p in d.iterdir()if p.is_file()and p.name!='YTDATA.DAT'and p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP')}
def capture(destination,selected,workers,reuse=None):
 destination.mkdir(parents=True,exist_ok=False)
 base=(SOURCE/'YTDATA.DAT').read_bytes();(destination/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
 (destination/'recipe.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=selected),indent=2)+'\n')
 retained={}
 for c in selected:
  if c['name']in(reuse or {}):
   source=Path(reuse[c['name']]);row=json.loads((source/'result.json').read_text())
   assert row['complete']and all(row[k]==v for k,v in c.items()),'reuse declaration/completion'
   shutil.copytree(source,destination/c['name']);retained[c['name']]=row
 def run(c):
  d=destination/c['name'];d.mkdir()
  for p in SOURCE.iterdir():
   if p.suffix.upper()in('.DAT','.ASC','.ANS','.DOC','.DEF'):shutil.copy2(p,d/p.name)
  if c.get('parent'):
   parent=destination/c['parent'];b=bytearray(gzip.decompress((parent/'after.dat.gz').read_bytes()))
   for p in d.iterdir():
    if p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP'):p.unlink()
   for name,row in json.loads(gzip.decompress((parent/'sidefiles.json.gz').read_bytes())).items():(d/name).write_bytes(bytes.fromhex(row['hex']))
  else:
   b=bytearray(base)
   mbf.put(b,1,105,c['threshold']);mbf.put(b,2,117,c['cached'])
   for port in range(1,1001):mbf.put(b,3051+port,97,2 if 2<=port<=c['owned']+1 else 0)
   (d/'KEEPME.DAT').write_bytes(b'Unrelated file: do not overwrite.\r\n')
   if c.get('alias_case_pair'):(d/'YTNAME.DAT').write_bytes((d/'YTNAME.DAT').read_bytes().rstrip(b'\x1a')+b'TESTER,,Q,\r\n\x1a')
   if c.get('score_sentinel'):(d/'YTSCORE.ASC').write_bytes(b'PRIOR SEASON SCOREBOARD SENTINEL\r\n')
   if 'marker'in c:(d/'RMTINIT.TMP').write_bytes(c['marker'].encode())
   for r,o,v in c.get('patches',[]):mbf.put(b,r,o,v)
  before=bytes(b);(d/'YTDATA.DAT').write_bytes(before);side=auxfiles(d)
  (d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({n:v.hex()for n,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
  binaries={}
  for name in BINS:
   if name in c.get('omit',[]):continue
   src=ROOT/'archive/analysis/yt-combat/KEYFEED.COM'if name=='KEYFEED.COM'else ROOT/'archive/dos-original'/name
   shutil.copy2(src,d/name);binaries[name]=SHA(src.read_bytes())
  if c['mode']=='game':
   keys='\r~~~~~\r~G\r~~'+c['reply']+'\r~~~~Q;Y\r'+'~~\r'*12
   program='local TESTER > GAME.LOG'
  elif c['mode']=='standalone':
   keys='~~~~'+c['reply']+'\r'+'~~\r'*12;program='rmt-init > GAME.LOG'
  else:keys='~~~~\r';program='ytmaint > GAME.LOG'
  (d/'KEYS.TXT').write_bytes(keys.encode())
  commands=[f'mount c {d}','c:','date 10/24/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','keyfeed',program,'echo GENESIS_PROGRAM_RETURNED > RETURN.LOG','exit']
  timed_out=False
  try:
   with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for cmd in commands for x in('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
  except subprocess.TimeoutExpired:timed_out=True
  after=(d/'YTDATA.DAT').read_bytes();raw=(d/'GAME.LOG').read_bytes();text=raw.decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text);(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0))
  for name,value in [('before',before),('after',after)]:(d/(name+'.dat.gz')).write_bytes(gzip.compress(value,mtime=0))
  final=auxfiles(d);(d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps({n:dict(hex=v.hex(),before_sha256=SHA(side[n])if n in side else None,after_sha256=SHA(v))for n,v in sorted(final.items())},indent=2)+'\n').encode(),mtime=0))
  returned=(d/'RETURN.LOG').exists()and b'GENESIS_PROGRAM_RETURNED'in(d/'RETURN.LOG').read_bytes()
  if not(d/'RETURN.LOG').exists():(d/'RETURN.LOG').write_bytes(b'')
  keep={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
  result={**c,'recipe':RECIPE,'baseline_sha256':SHA(base),'date':'10/24/2026','time':'00:00:00','timeout_seconds':120,'timed_out':timed_out,'program_returned':returned,'complete':returned and not timed_out,'binaries':binaries,'files':{n:SHA((d/n).read_bytes())for n in sorted(keep)}}
  (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  for p in d.iterdir():
   if p.is_file()and p.name not in keep|{'result.json'}:p.unlink()
  print(c['name'],'complete',result['complete'],'reset', 'Initialization completed sucessfully!'in text,'world',len(after),'marker','RMTINIT.TMP'in final,flush=True)
  return result
 with ThreadPoolExecutor(max_workers=workers)as pool:results=list(retained.values())+list(pool.map(run,[c for c in selected if not c.get('parent')and c['name']not in retained]))
 for c in selected:
  if c.get('parent')and c['name']not in retained:results.append(run(c))
 (destination/'results.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n')


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=4);a=p.parse_args();todo=cases()
 if a.only:
  if set(a.only)-{c['name']for c in todo}:p.error('unknown control')
  todo=[c for c in todo if c['name']in a.only]
  if any(c.get('parent')and c['parent']not in a.only for c in todo):p.error('include declared parent')
 capture(a.destination.resolve(),todo,a.workers)
