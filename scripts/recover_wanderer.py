"""Capture The Wanderer only in independently copied original DOS fixtures."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE='wanderer-lifecycle-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()
BINS=('YT.EXE','YTMAINT.EXE','YT-INIT.EXE','RMT-INIT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
GRAPH={1:[100],100:[101,106],101:[102],102:[103],103:[100],106:[107],107:[100],3000:[]}


def cases():
 out=[]
 def add(name,mode='maintenance',command='',patches=(),expect='relocation',**kw):out.append(dict(name=name,mode=mode,command=command,patches=list(patches),expect=expect,**kw))
 add('maint-linked')
 add('maint-missing-link',patches=[(151,93,0)],expect='regeneration')
 add('maint-inactive-linked',patches=[(4052,85,0)])
 add('maint-inactive-missing',patches=[(151,93,0),(4052,85,0)],expect='regeneration')
 add('maint-duplicate-links',patches=[(152,93,1)],expect='duplicate')
 add('maint-owned',patches=[(4052,73,2)])
 add('maint-foreign',patches=[(4052,73,3)])
 add('maint-zero-bank',patches=[(4052,117,0)])
 add('maint-one-bank',patches=[(4052,117,1)])
 add('maint-missing-zero-bank',patches=[(151,93,0),(4052,117,0)],expect='regeneration')
 add('maint-renamed',name_patch='Traveller')
 add('maint-missing-stale-tail',patches=[(151,93,0),(4052,89,.25),(4052,93,123),(4052,97,17),(4052,101,19),(4052,105,23),(4052,109,29),(4052,113,31),(4052,121,37),(4052,129,41)],expect='regeneration')
 add('maint-source-only-empty',fill_planets=True,expect='source-only')
 for name,sector,extra in [('earth',1,[]),('mines',300,[(351,129,3)]),('fighters',300,[(351,81,100),(351,85,3)]),('disconnected',300,[])]:
  add('maint-only-'+name,fill_planets=True,patches=[(151,93,0),(51+sector,93,0)]+extra,expect='only-candidate',candidate=sector)
 add('maint-next-day',parent='maint-owned',date='10/25/2026',expect='relocation')
 add('maint-same-day',parent='maint-owned',time='00:01:00',expect='relocation')
 add('maint-regenerated-next-day',parent='maint-missing-stale-tail',date='10/25/2026',expect='relocation')
 add('reset-defaults',mode='reset',expect='reset')
 add('reset-first-maintenance',parent='reset-defaults',time='00:01:00',expect='regeneration')
 add('init-defaults',mode='initializer',expect='initialized')
 add('init-same-day',parent='init-defaults',time='00:01:00',expect='relocation')
 add('init-next-day',parent='init-defaults',date='10/25/2026',expect='relocation')
 add('maint-clock-backward',parent='maint-owned',date='10/23/2026',expect='relocation')
 def game(name,command,patches=(),expect='landing',**kw):add(name,'game',command,patches,expect,**kw)
 game('land-neutral','L;D;L',[(4052,73,0)])
 game('land-owned','L;D;L',[(4052,73,2)])
 game('land-foreign-unguarded','L;D;L',[(4052,73,3),(4052,77,0)])
 game('land-foreign-guarded','L\r~~N',[(4052,73,3)],expect='denied')
 game('land-neutral-guarded','L;D;L',[(4052,73,0)])
 game('land-team','L;D;L',[(4052,73,3),(2,89,1),(3,89,1)])
 game('rename-reserved','L;N;L',expect='rename-refused')
 game('rename-renamed-slot','L;N;L',expect='rename-refused',name_patch='Traveller')
 game('bank-owned','L;B;2000;L',[(4052,73,2)],expect='bank',bank_target=2000)
 game('transfer-owned','L;T;F;123;L',[(4052,73,2)],expect='transfer')
 def move(name,dest=102,patches=(),reply='Y',expect='transport',**kw):game(name,'L;!;'+str(dest)+'\r~~~~'+reply,patches,expect,destination=dest,**kw)
 move('transport-two')
 move('transport-one',101)
 move('transport-three',103)
 move('transport-cancel',reply='N',expect='cancel')
 move('transport-blank',reply='',expect='cancel')
 move('transport-nine',101,[(2,49,9)],expect='insufficient')
 move('transport-ten',101,[(2,49,10)])
 move('transport-nineteen',102,[(2,49,19)],expect='insufficient')
 move('transport-twenty',102,[(2,49,20)])
 move('transport-owned',patches=[(4052,73,2)])
 move('transport-teammate',patches=[(4052,73,3),(2,89,1),(3,89,1)])
 move('transport-unguarded',patches=[(4052,73,3),(4052,77,0)])
 move('transport-renamed',name_patch='Traveller')
 move('transport-occupied-planned',101,[(152,93,2),(4053,85,11)],expect='collision')
 move('transport-zero-fighters',101,[(152,93,2),(4053,85,11),(2,61,0)],expect='collision')
 move('transport-planned-mines',patches=[(152,129,3)],expect='planned-mines')
 move('transport-planned-fighters',patches=[(152,81,100),(152,85,3)],expect='planned-fighters')
 move('transport-planet-mines',all_mines=True)
 move('transport-planet-fighters',all_fighters=True)
 game('transport-reentry','L\r~~N',parent='transport-two',time='00:01:00',expect='no-planet')
 add('transport-maintenance',parent='transport-owned',date='10/25/2026',patches=[(2,109,0),(3,109,0)],expect='relocation')
 return out


def exploratory_cases():
 return [dict(name='maint-no-vacancy',mode='maintenance',command='',patches=[(151,93,2)],expect='bounded-no-candidate',fill_planets=True,timeout=8)]


def common_patches():
 p=[]
 for r in range(4,52):
  p += [(r,o,0)for o in range(41,137,4)];p +=[(r,109,-1),(r,85,0)]
 for sector in range(1,3001):
  p += [(51+sector,o,0)for o in (81,85,93,105,129)]
 for port in range(1,1001):p +=[(3051+port,89,0),(3051+port,97,0)]
 for slot in range(1,101):p +=[(4051+slot,85,0)]
 for sector,warps in GRAPH.items():p +=[(51+sector,o,warps[i]if i<len(warps)else 0)for i,o in enumerate(range(41,65,4))]
 p += [(1,81,296),(1,117,1114),(52,105,1114),(151,93,1),(2051,93,99),(1165,93,100),(1165,81,1),(1165,85,-1)]
 p += [(2,o,v)for o,v in {41:297,45:0,49:500,53:10000,57:100,61:10000,65:100,69:10,73:20,77:30,81:100000,89:0,97:7,109:0,113:9,117:0,121:1000,125:1,129:8}.items()]
 p += [(3,o,v)for o,v in {41:297,45:0,49:500,57:110,89:0,109:0}.items()]
 p += [(4052,o,v)for o,v in {41:297,45:10,49:20,53:30,57:100,61:200,65:300,69:37,73:2,77:23,81:0,85:12,89:0,113:41,117:1234,125:43,129:47}.items()]
 for r,name,owner,ground,bank in [(4150,'Mercenary Base',-2,150000,25000000),(4151,'Xannoron',-1,100,100000)]:
  p +=[(r,o,0)for o in range(41,137,4)]
  p +=[(r,41,297),(r,73,owner),(r,77,ground),(r,85,len(name)),(r,117,bank)]
 return p


def auxfiles(d):return {p.name:p.read_bytes()for p in d.iterdir()if p.is_file()and p.name!='YTDATA.DAT'and p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP')}
def capture(destination,selected,workers,reuse=None):
 destination.mkdir(parents=True,exist_ok=False);base=(SOURCE/'YTDATA.DAT').read_bytes()
 (destination/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
 (destination/'recipe.json').write_text(json.dumps(dict(recipe=RECIPE,graph=GRAPH,common_patches=common_patches(),scenarios=selected),indent=2)+'\n')
 retained={}
 if reuse:
  for c in selected:
   source=reuse/c['name'];meta=source/'result.json';packed=source/'result.json.gz'
   if not(meta.exists()or packed.exists()):continue
   row=json.loads(meta.read_text()if meta.exists()else gzip.decompress(packed.read_bytes()))
   if not row['complete']or any(row.get(k)!=v for k,v in c.items()):continue
   for n,h in row['files'].items():assert SHA((source/n).read_bytes())==h,('reuse hash',c['name'],n)
   shutil.copytree(source,destination/c['name']);retained[c['name']]=row

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
   for n,row in json.loads(gzip.decompress((parent/'sidefiles.json.gz').read_bytes())).items():(d/n).write_bytes(bytes.fromhex(row['hex']))
   applied=list(c['patches'])
  else:
   before=bytearray(base);applied=common_patches()
   for name,r in [('Mercenary Base',4150),('Xannoron',4151)]:before[(r-1)*137:(r-1)*137+41]=name.encode().ljust(41,b' ')
   # These are explicit synthetic pointer-saturation controls, not claims of a
   # valid 3000-planet DOS universe (the native planet table has only100 slots).
   if c.get('fill_planets'):
    applied += [(51+s,93,2)for s in range(1,3001)];applied +=[(151,93,1),(1165,93,100),(2051,93,99)]
   if c.get('all_mines'):applied +=[(51+s,129,3)for s in range(1,3001)if s not in (1,100,101)]
   if c.get('all_fighters'):
    applied +=[(51+s,o,v)for s in range(1,3001)if s not in (1,100,101)for o,v in ((81,100),(85,3))]
   applied +=c['patches']
  for r,o,v in applied:mbf.put(before,r,o,v)
  if c.get('name_patch'):before[4051*137:4051*137+41]=c['name_patch'].encode().ljust(41,b' ')
  before=bytes(before);(d/'YTDATA.DAT').write_bytes(before)
  side=auxfiles(d);(d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({n:v.hex()for n,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
  if c['mode']=='game':keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode();program='local TESTER > GAME.LOG'
  elif c['mode']=='initializer':keys=b'Y\r\n\r\n';program='yt-init < KEYS.TXT > GAME.LOG'
  elif c['mode']=='reset':keys=('~~~~Y\r'+'~~\r'*12).encode();program='rmt-init > GAME.LOG'
  else:keys=b'~~~~\r';program='ytmaint > GAME.LOG'
  (d/'KEYS.TXT').write_bytes(keys)
  date=c.get('date','10/24/2026');clock=c.get('time','00:00:00')
  commands=[f'mount c {d}','c:','date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG']+([]if c['mode']=='initializer'else['keyfeed'])+[program,'echo WANDERER_PROGRAM_RETURNED > RETURN.LOG','exit']
  timed_out=False
  try:
   with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for cmd in commands for v in ('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=c.get('timeout',120),check=True)
  except subprocess.TimeoutExpired:timed_out=True
  after=(d/'YTDATA.DAT').read_bytes();raw=(d/'GAME.LOG').read_bytes();text=raw.decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text);(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0))
  for tag,b in [('before',before),('after',after)]:(d/(tag+'.dat.gz')).write_bytes(gzip.compress(b,mtime=0))
  final=auxfiles(d);(d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps({n:dict(hex=v.hex(),before_sha256=SHA(side[n])if n in side else None,after_sha256=SHA(v))for n,v in sorted(final.items())},indent=2)+'\n').encode(),mtime=0))
  if not(d/'RETURN.LOG').exists():(d/'RETURN.LOG').write_bytes(b'')
  returned=b'WANDERER_PROGRAM_RETURNED'in(d/'RETURN.LOG').read_bytes()
  keep={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
  result={**c,'recipe':RECIPE,'baseline_sha256':SHA(base),'applied_patches':applied,'date':date,'time':clock,'timeout_seconds':c.get('timeout',120),'timed_out':timed_out,'program_returned':returned,'complete':returned and not timed_out,'binaries':binaries,'files':{n:SHA((d/n).read_bytes())for n in sorted(keep)}}
  (d/'result.json.gz').write_bytes(gzip.compress((json.dumps(result,indent=2)+'\n').encode(),mtime=0))
  for p in d.iterdir():
   if p.is_file()and p.name not in keep|{'result.json','result.json.gz'}:p.unlink()
  refs=[s for s in range(1,3001)if mbf.get(after,51+s,93)==1]
  print(c['name'],result['complete'],'refs',refs[:8],'ship',mbf.get(after,2,57),'turns',mbf.get(after,2,49),'owner',mbf.get(after,4052,73),'bank',mbf.get(after,4052,117),flush=True)
  return result
 roots=[c for c in selected if not c.get('parent')and c['name']not in retained]
 with ThreadPoolExecutor(max_workers=workers)as pool:results=list(retained.values())+list(pool.map(run,roots))
 for c in selected:
  if c.get('parent')and c['name']not in retained:results.append(run(c))
 (destination/'results.json.gz').write_bytes(gzip.compress((json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n').encode(),mtime=0))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=4);p.add_argument('--exploratory',action='store_true');p.add_argument('--reuse',type=Path);a=p.parse_args();todo=exploratory_cases()if a.exploratory else cases()
 if not shutil.which('dosbox-staging'):p.error('DOSBox Staging required')
 if a.only:
  unknown=set(a.only)-{c['name']for c in todo}
  if unknown:p.error('unknown control '+str(unknown))
  todo=[c for c in todo if c['name']in a.only]
  if any(c.get('parent')and c['parent']not in a.only for c in todo):p.error('include exact declared parent')
 capture(a.destination.resolve(),todo,a.workers,a.reuse)
