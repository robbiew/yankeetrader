"""Capture bounded DOS3.6 plasma acquisition and removed Mercenary-sales controls in copied worlds."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE='mercenary-plasma-acquisition-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()
BINS=('YT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)

def cases():
 out=[]
 def add(name,command='I',**kw):
  out.append(dict(name=name,command=command,sectors=3000,start=100,standard=True,patches=[],**kw))
 add('quiet','I')
 add('main-help','?')
 add('earth-menu','P;0',location=1)
 add('earth-no-plasma-item','P;PLASMA\r~~~0',location=1)
 add('earth-poor-menu','P;0',location=1,cash=0)
 add('base-look','S')
 add('base-land-refuse','L\r~~~N')
 add('captured-base-menu','L;?;L',owner=2)
 add('captured-base-take','L;9;1;L',owner=2)
 add('ordinary-planet-take','L;9;1;L',slot=2,owner=2)
 add('ordinary-take-all','L;A;L',slot=2,owner=2)
 add('ordinary-deposit','L;T;B;L',slot=2,owner=2)
 add('unowned-planet-take','L;9;1;L',slot=2,owner=0,ground=0)
 add('mother-ship-name','L;?;L',slot=2,owner=2,planet_name='Mercenary Mother Ship')
 add('take-zero','L;9;0;L',slot=2,owner=2)
 add('take-reload','I',parent='ordinary-planet-take')
 add('deposit-reload','I',parent='ordinary-deposit')
 return out

def common_patches(c):
 patches=[]
 for r in range(4,52):patches +=[(r,o,0)for o in range(41,137,4)]+[(r,109,-1)]
 for sector in range(1,3001):patches +=[(51+sector,o,0)for o in range(41,137,4)]
 for sector,warps in {1:[100],100:[1,101],101:[100]}.items():
  patches +=[(51+sector,o,warps[i]if i<len(warps)else 0)for i,o in enumerate(range(41,65,4))]
 patches +=[(2,o,v)for o,v in {41:297,45:0,49:500,53:1000000,57:c.get('location',100),61:10000,65:100,69:10,73:20,77:30,81:c.get('cash',20000000),89:0,93:0,97:7,105:0,109:0,113:9,117:0,121:1000,125:1,129:8}.items()]
 patches +=[(3,o,v)for o,v in {41:297,45:0,49:500,57:200,61:0,53:0,65:100,69:0,73:0,77:0,85:6,89:0,97:0,109:0,125:1}.items()]
 patches += [(52,65,1),(151,93,c.get('slot',99))]
 return patches

def auxfiles(d):return {p.name:p.read_bytes()for p in d.iterdir()if p.is_file()and p.name!='YTDATA.DAT'and p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP')}
def capture(destination,selected,workers=4,reuse=None):
 destination.mkdir(parents=True,exist_ok=False);base=(SOURCE/'YTDATA.DAT').read_bytes()
 (destination/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
 (destination/'recipe.json').write_text(json.dumps(dict(recipe=RECIPE,source=str(SOURCE.relative_to(ROOT)),scenarios=selected),indent=2)+'\n')
 retained={}
 if reuse:
  for c in selected:
   old=reuse/c['name'];meta=old/'result.json.gz'
   if not meta.exists():continue
   row=json.loads(gzip.decompress(meta.read_bytes()))
   if not row['complete']or any(row.get(k)!=json.loads(json.dumps(v))for k,v in c.items()):continue
   if row['timeout_seconds']!=c.get('timeout',120)or row['baseline_sha256']!=SHA(base):continue
   for name,digest in row['files'].items():assert SHA((old/name).read_bytes())==digest,('reuse file hash',c['name'],name)
   shutil.copytree(old,destination/c['name']);retained[c['name']]=row
  print('Reused',len(retained),'complete exact-case captures with verified file hashes.',flush=True)

 def run(c):
  d=destination/c['name'];d.mkdir()
  for p in SOURCE.iterdir():
   if p.suffix.upper()in('.DAT','.ASC','.ANS','.DOC','.DEF'):shutil.copy2(p,d/p.name)
  bins={}
  for name in BINS:
   src=ROOT/'archive/analysis/yt-combat/KEYFEED.COM'if name=='KEYFEED.COM'else ROOT/'archive/dos-original'/name
   shutil.copy2(src,d/name);bins[name]=SHA(src.read_bytes())
  n=c['sectors'];planet_base=4051 if c.get('standard')else 51+n
  if c.get('parent'):
   parent=destination/c['parent']
   parent_result=json.loads(gzip.decompress((parent/'result.json.gz').read_bytes()))
   if not parent_result['complete']:raise RuntimeError('Refusing reload of incomplete parent '+c['parent'])
   b=bytearray(gzip.decompress((parent/'after.dat.gz').read_bytes()))
   for p in d.iterdir():
    if p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP'):p.unlink()
   for k,row in json.loads(gzip.decompress((parent/'sidefiles.json.gz').read_bytes())).items():(d/k).write_bytes(bytes.fromhex(row['hex']))
   applied=list(c['patches'])
  else:
   b=bytearray(base)
   # Explicit table geometry; ordinary-width controls retain original header ranges.
   for record in range(planet_base+1,planet_base+(101 if c.get('standard')else 4)):b[(record-1)*137:record*137]=bytes(137)
   if c.get('planet'):
    rec=4053;src=4053
    b[(rec-1)*137:rec*137]=base[(src-1)*137:src*137]
    name='Target Planet';b[(rec-1)*137:(rec-1)*137+41]=name.encode().ljust(41,b' ')
    for o,v in {41:297,45:10000,49:10000,53:10000,57:1000,61:2000,65:3000,69:37,73:3,77:5000,81:0,85:len(name),89:0,113:41,117:1234,125:43,129:47}.items():mbf.put(b,rec,o,v)
    for o,v in c.get('planet_patches',[]):mbf.put(b,rec,o,v)
   slot=c.get('slot',99);rec=4051+slot
   name=c.get('planet_name','Mercenary Base' if slot==99 else 'Supply World')
   b[(rec-1)*137:(rec-1)*137+41]=name.encode().ljust(41,b' ')
   for o,v in {41:297,45:0,49:0,53:0,57:0,61:0,65:0,69:0,73:c.get('owner',-2),77:c.get('ground',1000),81:0,85:len(name),89:0,113:20,117:1234,125:0,129:20}.items():mbf.put(b,rec,o,v)
   applied=common_patches(c)+c['patches']
  for r,o,v in applied:mbf.put(b,r,o,v)
  before=bytes(b);(d/'YTDATA.DAT').write_bytes(before)
  side=auxfiles(d);(d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({k:v.hex()for k,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
  keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode();(d/'KEYS.TXT').write_bytes(keys)
  date=c.get('date','10/24/2026');clock=c.get('time','00:00:00')
  commands=[f'mount c {d}','c:','date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','keyfeed','local TESTER > GAME.LOG','echo MERCENARY_ACQUISITION_RETURNED > RETURN.LOG','exit']
  timed=False
  try:
   with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for cmd in commands for v in('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=c.get('timeout',120),check=True)
  except subprocess.TimeoutExpired:timed=True
  after=(d/'YTDATA.DAT').read_bytes();raw=(d/'GAME.LOG').read_bytes();text=raw.decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text);(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0))
  for tag,data in [('before',before),('after',after)]:(d/(tag+'.dat.gz')).write_bytes(gzip.compress(data,mtime=0))
  final=auxfiles(d);(d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps({k:dict(hex=v.hex(),before_sha256=SHA(side[k])if k in side else None,after_sha256=SHA(v))for k,v in sorted(final.items())},indent=2)+'\n').encode(),mtime=0))
  if not(d/'RETURN.LOG').exists():(d/'RETURN.LOG').write_bytes(b'')
  returned=b'MERCENARY_ACQUISITION_RETURNED'in(d/'RETURN.LOG').read_bytes()
  keep={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
  result={**c,'recipe':RECIPE,'baseline_sha256':SHA(base),'applied_patches':applied,'date':date,'time':clock,'timeout_seconds':c.get('timeout',120),'timed_out':timed,'program_returned':returned,'complete':returned and not timed,'binaries':bins,'files':{k:SHA((d/k).read_bytes())for k in sorted(keep)}}
  (d/'result.json.gz').write_bytes(gzip.compress((json.dumps(result,indent=2)+'\n').encode(),mtime=0))
  for p in d.iterdir():
   if p.is_file()and p.name not in keep|{'result.json.gz'}:p.unlink()
  print(c['name'],result['complete'],'plasma',mbf.get(after,2,113),'ship',mbf.get(after,2,57),'turns',mbf.get(after,2,49),'cash',mbf.get(after,2,81),flush=True)
  return result
 with ThreadPoolExecutor(max_workers=workers)as pool:results=list(retained.values())+list(pool.map(run,[c for c in selected if not c.get('parent')and c['name']not in retained]))
 for c in selected:
  if c.get('parent')and c['name']not in retained:results.append(run(c))
 (destination/'results.json.gz').write_bytes(gzip.compress((json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n').encode(),mtime=0))
 if any(not row['complete'] for row in results):raise SystemExit('Incomplete controls retained for diagnosis; do not count as successful research.')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=4);p.add_argument('--reuse',type=Path);a=p.parse_args();todo=cases()
 if not shutil.which('dosbox-staging'):p.error('DOSBox Staging required')
 if a.only:
  unknown=set(a.only)-{c['name']for c in todo}
  if unknown:p.error('unknown control '+str(unknown))
  todo=[c for c in todo if c['name']in a.only]
  if any(c.get('parent')and c['parent']not in a.only for c in todo):p.error('include exact declared parent')
 capture(a.destination.resolve(),todo,a.workers,a.reuse)
