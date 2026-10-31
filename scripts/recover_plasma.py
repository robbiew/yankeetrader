"""Capture unmodified DOS plasma launch, routing and disruption in isolated copied worlds."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE='plasma-routing-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()
BINS=('YT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)

def cases():
 out=[]
 def add(name,command='+;101;1',patches=(),**kw):out.append(dict(dict(name=name,command=command,sectors=3000,start=100,standard=True,patches=list(patches)),**kw))
 add('quiet-origin','I')
 add('empty-adjacent')
 add('no-bolts','+',patches=[(2,113,0)])
 add('zero-turns','+;101;1',patches=[(2,49,0)])
 add('one-turn',patches=[(2,49,1)])
 add('zero-sector-reprompt','+;0\r~~~101\r~~0')
 add('blank-sector','+\r~~\r')
 add('cancel-count','+;101;0')
 add('negative-count','+;101;-1')
 add('oversized-count','+;101;10')
 add('invalid-sector','+;3001\r~~~101\r~~0')
 add('own-sector','+;100;1')
 add('own-sector-cloaked','+;100;1',patches=[(2,125,0)])
 add('earth-target','+;1;1',graph={100:[1]})
 add('two-hop','+;102;1')
 add('three-hop','+;103;1')
 add('route-dead-end','+;200;1',graph={100:[]})
 add('route-tie','+;104;1',graph={100:[102,101],101:[104],102:[104]})
 add('repeat-volley','+;101;1;+;101;1')
 add('fighters-enemy',patches=[(152,81,1000000),(152,85,3)])
 add('fighters-self',patches=[(152,81,1000000),(152,85,2)])
 add('fighters-two-bolts','+;101;2',patches=[(152,81,1000000),(152,85,3)])
 add('fighter-spill',patches=[(152,81,1),(152,85,3),(152,129,10000)])
 add('mines-only',patches=[(152,129,10000)])
 add('enemy-ship',patches=[(3,57,101),(3,53,1000000),(3,61,0)])
 add('cloaked-ship',patches=[(3,57,101),(3,53,1000000),(3,61,0),(3,125,0)])
 add('team-ship',patches=[(3,57,101),(3,53,1000000),(3,61,0),(2,89,7),(3,89,7)])
 add('ship-fighters',patches=[(3,57,101),(3,53,1000000),(3,61,1000000)])
 add('two-ships',patches=[(3,57,101),(3,53,1000000),(3,61,0),(4,41,297),(4,57,101),(4,53,1000000),(4,61,0),(4,85,6),(4,109,0),(4,125,1)])
 add('lethal-ship',patches=[(3,57,101),(3,53,1),(3,61,0),(3,65,10),(3,69,0),(3,73,0),(3,77,0)])
 add('planet-productive',planet=True)
 add('planet-zero-projection','L\r~~~N',planet=True,patches=[(151,93,2),(152,93,0)],planet_patches=[(45,0),(49,0),(53,0),(77,1)])
 add('planet-small-projection','L\r~~~N',planet=True,patches=[(151,93,2),(152,93,0)],planet_patches=[(45,1),(49,1),(53,1),(77,1)])
 add('planet-small',planet=True,planet_patches=[(45,1),(49,1),(53,1),(77,1)])
 add('planet-zero',planet=True,planet_patches=[(45,0),(49,0),(53,0),(77,1)])
 add('planet-organic-small',planet=True,planet_patches=[(45,0),(49,1),(53,1),(57,0),(61,0),(65,0),(77,1)])
 add('planet-no-ore-stock',planet=True,planet_patches=[(57,0)])
 add('mixed-defense',planet=True,patches=[(152,81,1),(152,85,3),(152,129,1),(3,57,101),(3,53,1),(3,61,0)])
 add('hole-592','+;592;1',graph={100:[592],592:[101]})
 add('hole-1051','+;1051;1',graph={100:[1051],1051:[101]})
 add('hole-target-defenses','+;592;1',graph={100:[592]},patches=[(643,81,1000000),(643,85,3)])
 add('hole-enroute','+;102;1',graph={100:[592],592:[102]})
 add('hole-sensors','S',graph={100:[592,1051,101]})
 add('adjacent-clock-01',time='01:00:00')
 add('fractional-count','+;101;1.9')
 add('avoid-route','C;7;1;101;1;+;102;1')
 add('route-tie-reverse','+;104;1',graph={100:[101,102],101:[104],102:[104]})
 add('range-exhaustion','+;160;1',timeout=180)
 add('empty-two-bolts','+;103;2')
 add('self-lethal','+;100;1',patches=[(2,53,1),(2,61,0),(2,65,1),(2,69,0),(2,73,0),(2,77,0)])
 add('friendly-small',patches=[(152,81,1),(152,85,2)])
 add('planet-self',planet=True,planet_patches=[(73,2)])
 add('planet-team',planet=True,patches=[(2,89,7),(3,89,7)])
 add('planet-ore-only-full',planet=True,planet_patches=[(45,10000),(49,0),(53,0),(57,1000),(61,0),(65,0)])
 add('planet-ore-only-empty',planet=True,planet_patches=[(45,10000),(49,0),(53,0),(57,0),(61,0),(65,0)])
 add('planet-impact-zero',planet=True,planet_patches=[(45,0),(49,0),(53,0),(57,0),(61,0),(65,0),(77,1)])
 add('planet-zero-empty',planet=True,planet_patches=[(45,0),(49,0),(53,0),(57,0),(77,1)])
 add('hole-rebuilt-route','+;592;1',graph={100:[592],592:[2368]},patches=[(2419,81,1000000),(2419,85,3)])
 add('hole-back-through-self','+;592;1',graph={100:[592,2368],592:[100]})
 add('hole-two-redirects','+;592;1',graph={100:[592],592:[1051],1051:[2368]})
 add('volley-reload','I',parent='repeat-volley',start=None,time='00:01:00')
 add('planet-reload','I',parent='planet-small',start=None,time='00:01:00')
 return out

def common_patches(c):
 patches=[]
 for r in range(4,52):patches +=[(r,o,0)for o in range(41,137,4)]+[(r,109,-1)]
 for sector in range(1,3001):
  # Empty declared sector table and directed links, retaining original table geometry.
  patches +=[(51+sector,o,0)for o in range(41,137,4)]
 for sector in range(100,161):patches +=[(51+sector,41,sector+1 if sector<160 else 100)]
 for sector,warps in c.get('graph',{}).items():patches +=[(51+int(sector),o,warps[i]if i<len(warps)else 0)for i,o in enumerate(range(41,65,4))]
 patches +=[(2,o,v)for o,v in{41:297,45:0,49:500,53:1000000,57:c['start'],61:10000,65:100,69:10,73:20,77:30,81:100000,89:0,93:0,97:7,105:0,109:0,113:9,117:0,121:1000,125:1,129:8}.items()]
 patches +=[(3,o,v)for o,v in{41:297,45:0,49:500,57:200,61:0,53:0,65:100,69:0,73:0,77:0,85:6,89:0,97:0,109:0,125:1}.items()]
 if c.get('planet'):patches +=[(152,93,2)]
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
   parent=destination/c['parent'];b=bytearray(gzip.decompress((parent/'after.dat.gz').read_bytes()))
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
   applied=common_patches(c)+c['patches']
  for r,o,v in applied:mbf.put(b,r,o,v)
  before=bytes(b);(d/'YTDATA.DAT').write_bytes(before)
  side=auxfiles(d);(d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({k:v.hex()for k,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
  keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode();(d/'KEYS.TXT').write_bytes(keys)
  date=c.get('date','10/24/2026');clock=c.get('time','00:00:00')
  commands=[f'mount c {d}','c:','date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','keyfeed','local TESTER > GAME.LOG','echo PLASMA_PROGRAM_RETURNED > RETURN.LOG','exit']
  timed=False
  try:
   with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for cmd in commands for v in('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=c.get('timeout',120),check=True)
  except subprocess.TimeoutExpired:timed=True
  after=(d/'YTDATA.DAT').read_bytes();raw=(d/'GAME.LOG').read_bytes();text=raw.decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text);(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0))
  for tag,data in [('before',before),('after',after)]:(d/(tag+'.dat.gz')).write_bytes(gzip.compress(data,mtime=0))
  final=auxfiles(d);(d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps({k:dict(hex=v.hex(),before_sha256=SHA(side[k])if k in side else None,after_sha256=SHA(v))for k,v in sorted(final.items())},indent=2)+'\n').encode(),mtime=0))
  if not(d/'RETURN.LOG').exists():(d/'RETURN.LOG').write_bytes(b'')
  returned=b'PLASMA_PROGRAM_RETURNED'in(d/'RETURN.LOG').read_bytes()
  keep={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
  result={**c,'recipe':RECIPE,'baseline_sha256':SHA(base),'applied_patches':applied,'date':date,'time':clock,'timeout_seconds':c.get('timeout',120),'timed_out':timed,'program_returned':returned,'complete':returned and not timed,'binaries':bins,'files':{k:SHA((d/k).read_bytes())for k in sorted(keep)}}
  (d/'result.json.gz').write_bytes(gzip.compress((json.dumps(result,indent=2)+'\n').encode(),mtime=0))
  for p in d.iterdir():
   if p.is_file()and p.name not in keep|{'result.json.gz'}:p.unlink()
  print(c['name'],result['complete'],'entries',text.count('Bolt entering sector'),'ship',mbf.get(after,2,57),'turns',mbf.get(after,2,49),'cash',mbf.get(after,2,81),flush=True)
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
