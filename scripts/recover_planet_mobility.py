"""Capture planetary thrusters and forced landing only in disposable DOS worlds."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE='planet-mobility-v1'
GRAPH={1:[100],100:[101,106],101:[102],102:[103],103:[104],104:[105],105:[100,1],106:[107],107:[108],108:[109],109:[110],110:[100],3000:[]}
BINS=('YT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')
SHA=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)


def cases():
 out=[]
 def add(name,command,patches=(),**kw):out.append(dict(name=name,command=command,patches=list(patches),**kw))
 def move(name,destination=101,patches=(),reply='Y',hops=1,expect='route',**kw):
  add(name,'L;!;'+str(destination)+'\r~~~~'+reply,patches,expect=expect,destination=destination,hops=hops,**kw)
 def force(name,quantity,patches=(),ground=100,carried=1000,owner=3,reply='Y',expect='assault',**kw):
  command='L' if quantity is None else 'L\r~~'+reply+'\r~~'+str(quantity)
  add(name,command,[(4053,73,owner),(4053,77,ground),(2,121,carried)]+list(patches),expect=expect,committed=quantity,**kw)
 add('control-owned','L;L',expect='landing')
 move('move-one')
 move('move-two',102,hops=2)
 move('move-four',104,hops=4)
 move('move-cancel',reply='N',expect='cancel')
 move('move-blank',reply='',expect='cancel')
 for name,dest in [('current',100),('zero',0),('negative',-1),('outside',3001),('unreachable',3000)]:move('move-'+name,dest,hops=0,expect='invalid-route')
 for name,turns,destination,hops in [('one-below',9,101,1),('one-exact',10,101,1),('two-below',19,102,2),('two-exact',20,102,2),('two-above',21,102,2)]:
  move('turns-'+name,destination,[(2,49,turns)],hops=hops,expect='insufficient'if turns<hops*10 else'route')
 for name,sector,stock in [('first',101,10000),('later',102,10000),('one-fighter',101,1),('zero-fighters',101,0)]:
  move('collision-'+name,102 if sector==102 else 101,[(51+sector,93,3),(2,61,stock)],hops=2 if sector==102 else 1,expect='collision',planet_copies=[[2,3]],collision_sector=sector)
 move('move-unguarded',patches=[(4053,73,3),(4053,77,0)])
 move('move-teammate',patches=[(4053,73,3),(2,89,1),(3,89,1)])
 move('move-neutral',patches=[(4053,73,0),(4053,77,0)])
 move('move-captured-xannoron',patches=[(151,93,100),(4053,85,0),(1165,93,0)],expect='reserved-home',planet_copies=[[2,100]],source_slot=100)
 move('move-wanderer',102,[(151,93,1),(4053,85,0),(636,93,0)],hops=2,expect='wanderer',planet_copies=[[2,1]],source_slot=1)
 move('move-mines',102,[(152,129,3)],hops=2)
 move('move-hostile-fighters',102,[(152,81,100),(152,85,3)],hops=2)
 move('move-own-fighters',102,[(152,81,100),(152,85,2)],hops=2)
 move('move-later-hostile',103,[(153,81,100),(153,85,3)],hops=3)
 move('move-anomaly-first',102,[(152,133,1)],hops=2,expect='anomaly')
 move('move-anomaly-later',103,[(153,133,1)],hops=3,expect='anomaly')
 move('move-earth',1,hops=6)
 move('move-cloak-boundary',patches=[(2,49,35),(2,125,1)])
 force('force-decline',None,reply='N',expect='decline')
 out[-1]['command']='L\r~~N'
 force('force-blank',None,expect='decline');out[-1]['command']='L\r~~'
 force('force-no-troops',None,carried=0,expect='no-troops')
 for name,quantity in [('zero',0),('negative',-1),('over',1001),('invalid','junk')]:force('force-'+name,quantity,expect='invalid-force')
 force('force-full',1000)
 force('force-partial',100,ground=10)
 force('force-loss',10,ground=10000)
 force('force-one',1,ground=1)
 force('force-fraction',1.9,ground=2)
 force('land-fractional-defender',None,ground=.25,expect='landing')
 force('land-unguarded',None,ground=0,expect='landing')
 force('land-neutral-defended',None,owner=0,expect='permission')
 force('land-teammate',None,[(2,89,1),(3,89,1)],expect='landing')
 force('land-dead-governor',None,[(3,45,2)],expect='permission')
 force('force-mercenary',1000,owner=-2)
 force('force-xannor',1000,owner=-1)
 force('force-no-ship-defenses',1000,[(2,61,0),(2,53,0)],ground=10)
 add('captured-reentry','L;L',expect='reentry',parent='force-partial',time='00:01:00')
 add('failed-retry','L\r~~Y\r~~10',expect='assault',committed=10,parent='force-loss',time='00:01:00')
 return out


def common_patches():
 patches=[]
 for sector,warps in GRAPH.items():
  patches += [(51+sector,o,warps[i] if i<len(warps)else 0)for i,o in enumerate(range(41,65,4))]
  patches += [(51+sector,o,0)for o in(81,85,93,129)]
 patches += [(151,93,2)]
 patches += [(2,o,v)for o,v in{41:297,45:0,49:500,53:10000,57:100,61:10000,65:100,69:10,73:20,77:30,81:100000,89:0,97:7,113:9,121:1000,125:1,129:8}.items()]
 patches += [(4053,o,v)for o,v in{41:297,45:10,49:20,53:30,57:100,61:200,65:300,69:70,73:2,77:100,85:11,89:0,113:90,117:1234,125:80,129:600}.items()]
 return patches


def auxfiles(d):return {p.name:p.read_bytes()for p in d.iterdir()if p.is_file()and p.name!='YTDATA.DAT'and p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP')}
def capture(destination,selected,workers=4):
 destination.mkdir(parents=True,exist_ok=False)
 base=(SOURCE/'YTDATA.DAT').read_bytes();(destination/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
 (destination/'recipe.json').write_text(json.dumps(dict(recipe=RECIPE,graph=GRAPH,common_patches=common_patches(),scenarios=selected),indent=2)+'\n')
 def run(c):
  d=destination/c['name'];d.mkdir()
  for p in SOURCE.iterdir():
   if p.suffix.upper()in('.DAT','.ASC','.ANS','.DOC','.DEF'):shutil.copy2(p,d/p.name)
  binaries={}
  for name in BINS:
   src=ROOT/'archive/analysis/yt-combat/KEYFEED.COM'if name=='KEYFEED.COM'else ROOT/'archive/dos-original'/name
   shutil.copy2(src,d/name);binaries[name]=SHA(src.read_bytes())
  if c.get('parent'):
   parent=destination/c['parent'];before=bytearray(gzip.decompress((parent/'after.dat.gz').read_bytes()))
   for p in d.iterdir():
    if p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP'):p.unlink()
   for name,row in json.loads(gzip.decompress((parent/'sidefiles.json.gz').read_bytes())).items():(d/name).write_bytes(bytes.fromhex(row['hex']))
   patches=c['patches']
  else:before=bytearray(base);patches=common_patches()+c['patches']
  # Copies use the common initialized planet, before case-specific mutations.
  if c.get('planet_copies'):
   for r,o,v in common_patches():mbf.put(before,r,o,v)
   for source,target in c['planet_copies']:before[(4051+target-1)*137:(4051+target)*137]=before[(4051+source-1)*137:(4051+source)*137]
   patches=c['patches']
  for r,o,v in patches:mbf.put(before,r,o,v)
  before=bytes(before);(d/'YTDATA.DAT').write_bytes(before)
  side=auxfiles(d);(d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({n:v.hex()for n,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
  tail='Q;Y\r~~~~'
  keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+tail*12).encode();(d/'KEYS.TXT').write_bytes(keys)
  date=c.get('date','10/24/2026');clock=c.get('time','00:00:00')
  commands=[f'mount c {d}','c:','date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','keyfeed','local TESTER > GAME.LOG','echo MOBILITY_PROGRAM_RETURNED > RETURN.LOG','exit']
  timed_out=False
  try:
   with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[x for cmd in commands for x in('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
  except subprocess.TimeoutExpired:timed_out=True
  after=(d/'YTDATA.DAT').read_bytes();raw=(d/'GAME.LOG').read_bytes();text=raw.decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text);(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0))
  for label,value in [('before',before),('after',after)]:(d/(label+'.dat.gz')).write_bytes(gzip.compress(value,mtime=0))
  final=auxfiles(d);(d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps({n:dict(hex=v.hex(),before_sha256=SHA(side[n])if n in side else None,after_sha256=SHA(v))for n,v in sorted(final.items())},indent=2)+'\n').encode(),mtime=0))
  if not(d/'RETURN.LOG').exists():(d/'RETURN.LOG').write_bytes(b'')
  returned=b'MOBILITY_PROGRAM_RETURNED'in(d/'RETURN.LOG').read_bytes()
  keep={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
  result={**c,'recipe':RECIPE,'baseline_sha256':SHA(base),'applied_patches':(c['patches']if c.get('parent')else common_patches()+c['patches']),'date':date,'time':clock,'timeout_seconds':120,'timed_out':timed_out,'program_returned':returned,'complete':returned and not timed_out,'binaries':binaries,'files':{n:SHA((d/n).read_bytes())for n in sorted(keep)}}
  (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  for p in d.iterdir():
   if p.is_file()and p.name not in keep|{'result.json'}:p.unlink()
  print(c['name'],result['complete'],'sector',mbf.get(after,2,57),'turns',mbf.get(after,2,49),'ground',mbf.get(after,2,121),'owner',mbf.get(after,4053,73),'defenders',mbf.get(after,4053,77),flush=True)
  return result
 with ThreadPoolExecutor(max_workers=workers)as pool:results=list(pool.map(run,[c for c in selected if not c.get('parent')]))
 for c in selected:
  if c.get('parent'):results.append(run(c))
 (destination/'results.json').write_text(json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=4);a=p.parse_args();todo=cases()
 if not shutil.which('dosbox-staging'):p.error('DOSBox Staging is required')
 if a.only:
  if set(a.only)-{c['name']for c in todo}:p.error('unknown control')
  todo=[c for c in todo if c['name']in a.only]
  if any(c.get('parent')and c['parent']not in a.only for c in todo):p.error('include declared parent')
 capture(a.destination.resolve(),todo,a.workers)
