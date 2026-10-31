"""Capture unmodified DOS disruption/black-hole arrivals in isolated copied worlds."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE='disruption-arrival-v1'
SHA=lambda b:hashlib.sha256(b).hexdigest()
BINS=('YT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)

def cases():
 out=[]
 def add(name,command='I',n=3,start=1,patches=(),**kw):out.append(dict(name=name,command=command,sectors=n,start=start,patches=list(patches),**kw))
 add('quiet-origin')
 add('ordinary-arrival','M;2')
 add('startup-arrival',start=2)
 add('upper-safe',start=3)
 add('upper-raw-133',start=3,patches=[(54,133,1)])
 add('scanner-decline','M;2\r~~N',patches=[(2,93,-1)])
 add('scanner-accept','M;2\r~~Y',patches=[(2,93,-1)])
 add('arrival-zero-turns','M;2',patches=[(2,49,1)])
 add('startup-zero-turns',start=2,patches=[(2,49,0)])
 add('startup-low-turns',start=2,patches=[(2,49,7)])
 add('startup-cloak-zero',start=2,patches=[(2,125,0)])
 add('startup-cloak-fraction',start=2,patches=[(2,125,.5)])
 add('startup-hole-mines',start=2,patches=[(53,129,3)])
 add('startup-hole-fighters',start=2,patches=[(53,81,100),(53,85,3)])
 add('startup-hole-both',start=2,patches=[(53,129,3),(53,81,100),(53,85,3)])
 add('startup-landing-mines',start=2,patches=[(54,129,3)])
 add('startup-landing-fighters',start=2,patches=[(54,81,100),(54,85,3)])
 add('startup-landing-both',start=2,patches=[(54,129,3),(54,81,100),(54,85,3)])
 add('startup-landing-lethal',start=2,patches=[(54,129,30),(2,53,0),(2,61,0),(2,65,1),(2,69,0),(2,73,0),(2,77,0),(2,125,0)])
 add('ordinary-hole-both','M;2',patches=[(53,129,3),(53,81,100),(53,85,3)])
 for reply,label in [('N','decline'),('Y','accept')]:
  add('scanner-combined-'+label,'M;2\r~~'+reply,patches=[(2,93,-1),(53,129,3),(53,81,100),(53,85,3)])
 add('autopilot','C;3;3;Y')
 add('autopilot-scanner-decline','C;3;3;Y\r~~N',patches=[(2,93,-1)])
 add('autopilot-scanner-accept','C;3;3;Y\r~~Y',patches=[(2,93,-1)])
 add('manual-warp','W;Y')
 add('thruster-final','L;!;2\r~~~~Y',planet=2)
 add('thruster-intermediate','L;!;3\r~~~~Y',planet=2)
 add('thruster-intermediate-mines','L;!;3\r~~~~Y',planet=2,patches=[(53,129,3)])
 add('thruster-intermediate-fighters','L;!;3\r~~~~Y',planet=2,patches=[(53,81,100),(53,85,3)])
 add('thruster-final-collision','L;!;2\r~~~~Y',planet=2,collision=True)
 add('thruster-ten-turns','L;!;2\r~~~~Y',planet=2,patches=[(2,49,10)])
 add('thruster-cancel','L;!;2\r~~~~N',planet=2)
 add('wanderer-final','L;!;2\r~~~~Y',planet=1)
 for clock in ['00:01:00','01:00:00','02:00:00','03:00:00']:
  add('wanderer-clock-'+clock[:5].replace(':',''),'L;!;2\r~~~~Y',planet=1,time=clock)
 add('two-sector-arrival','M;2',n=2)
 for clock in ['01:00:00','02:00:00','03:00:00']:
  add('startup-clock-'+clock[:2],start=2,time=clock)
 graph={8:[2,3,4,5,6,7]}
 add('eight-sector-sensors','S',n=8,start=8,graph=graph)
 add('eight-sector-arrival-3','M;3',n=8,start=8,graph=graph)
 add('eight-sector-arrival-4','M;4',n=8,start=8,graph=graph)
 add('normal-width-origin',n=3000,start=100,standard=True)
 add('normal-width-adjacent','M;101',n=3000,start=100,standard=True)
 add('normal-width-thruster','L;!;101\r~~~~Y',n=3000,start=100,standard=True,planet=2)
 graph_full={3000:[592,1051]}
 add('normal-width-sensors','S',n=3000,start=3000,standard=True,graph=graph_full)
 add('normal-width-sensors-repeat','S;S',n=3000,start=3000,standard=True,graph=graph_full)
 add('normal-width-arrival-592','M;592',n=3000,start=3000,standard=True,graph=graph_full)
 add('normal-width-arrival-1051','M;1051',n=3000,start=3000,standard=True,graph=graph_full)
 add('normal-width-thruster-hole','L;!;592\r~~~~Y',n=3000,start=3000,standard=True,graph=graph_full,planet=2)
 add('normal-width-wanderer-hole','L;!;592\r~~~~Y',n=3000,start=3000,standard=True,graph=graph_full,planet=1)
 add('normal-width-startup-hole',n=3000,start=592,standard=True)
 add('normal-width-upper-safe',n=3000,start=3000,standard=True)
 add('normal-width-earth-safe',n=3000,start=1,standard=True)
 add('normal-width-reconnect','S',n=3000,start=None,standard=True,graph=graph_full,parent='normal-width-sensors',time='00:01:00')
 add('ordinary-reconnect',parent='ordinary-arrival',time='00:01:00',start=None)
 add('wanderer-reconnect',parent='wanderer-final',time='00:01:00',start=None)
 add('eight-sector-reconnect','S',n=8,start=None,graph=graph,parent='eight-sector-sensors',time='00:01:00')
 return out

def diagnostic_cases():
 return [dict(name='one-sector-loop',command='I',sectors=1,start=1,patches=[(2,49,0)],timeout=40,diagnostic='bounded-native-reentry-loop')]

def common_patches(c):
 n=c['sectors'];patches=[]
 for r in range(4,52):
  patches +=[(r,o,0)for o in range(41,137,4)];patches +=[(r,109,-1),(r,85,0)]
 for sector in range(1,n+1):patches +=[(51+sector,o,0)for o in (81,85,93,105,129,133)]
 if not c.get('standard'):patches +=[(1,57,51+n),(1,61,51+n),(1,93,54+n)]
 for sector in range(1,n+1):
  warps=[sector+1]if sector<n else[1]
  if sector>1 and sector<n:warps +=[1]
  patches +=[(51+sector,o,warps[i]if i<len(warps)else 0)for i,o in enumerate(range(41,65,4))]
  patches +=[(51+sector,o,0)for o in(65,69,73,77)]
 for sector,warps in c.get('graph',{}).items():patches +=[(51+int(sector),o,warps[i]if i<len(warps)else 0)for i,o in enumerate(range(41,65,4))]
 patches +=[(2,o,v)for o,v in{41:297,45:0,49:500,53:10000,57:c['start'],61:10000,65:100,69:10,73:20,77:30,81:100000,89:0,93:0,97:7,105:0,109:0,113:9,117:0,121:1000,125:1,129:8}.items()]
 patches +=[(3,o,v)for o,v in{41:297,45:0,49:500,57:1,61:0,53:0,89:0,109:0,125:1}.items()]
 if c.get('planet'):patches +=[(51+c['start'],93,c['planet'])]
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
    rec=planet_base+c['planet'];src=4053
    b[(rec-1)*137:rec*137]=base[(src-1)*137:src*137]
    name='The Wanderer'if c['planet']==1 else'Test Planet'
    b[(rec-1)*137:(rec-1)*137+41]=name.encode().ljust(41,b' ')
    for o,v in {41:297,45:10,49:20,53:30,57:100,61:200,65:300,69:37,73:2,77:23,81:0,85:len(name),89:0,113:41,117:1234,125:43,129:47}.items():mbf.put(b,rec,o,v)
    if c.get('collision'):
     other=planet_base+3;b[(other-1)*137:other*137]=b[(rec-1)*137:rec*137]
     b[(other-1)*137:(other-1)*137+41]=b'Stationary'.ljust(41,b' ');mbf.put(b,other,85,10)
   applied=common_patches(c)+c['patches']
   if c.get('collision'):applied +=[(53,93,3)]
  for r,o,v in applied:mbf.put(b,r,o,v)
  before=bytes(b);(d/'YTDATA.DAT').write_bytes(before)
  side=auxfiles(d);(d/'side-before.json.gz').write_bytes(gzip.compress((json.dumps({k:v.hex()for k,v in sorted(side.items())},indent=2)+'\n').encode(),mtime=0))
  keys=('\r~~~~~\r~'+c['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode();(d/'KEYS.TXT').write_bytes(keys)
  date=c.get('date','10/24/2026');clock=c.get('time','00:00:00')
  commands=[f'mount c {d}','c:','date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG','keyfeed','local TESTER > GAME.LOG','echo DISRUPTION_PROGRAM_RETURNED > RETURN.LOG','exit']
  timed=False
  try:
   with(d/'dosbox.log').open('w')as log:subprocess.run([shutil.which('dosbox-staging'),'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for cmd in commands for v in('-c',cmd)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=c.get('timeout',120),check=True)
  except subprocess.TimeoutExpired:timed=True
  after=(d/'YTDATA.DAT').read_bytes();raw=(d/'GAME.LOG').read_bytes();text=raw.decode('cp437').replace('\r\n','\n');(d/'transcript.txt').write_text(text);(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0))
  for tag,data in [('before',before),('after',after)]:(d/(tag+'.dat.gz')).write_bytes(gzip.compress(data,mtime=0))
  final=auxfiles(d);(d/'sidefiles.json.gz').write_bytes(gzip.compress((json.dumps({k:dict(hex=v.hex(),before_sha256=SHA(side[k])if k in side else None,after_sha256=SHA(v))for k,v in sorted(final.items())},indent=2)+'\n').encode(),mtime=0))
  if not(d/'RETURN.LOG').exists():(d/'RETURN.LOG').write_bytes(b'')
  returned=b'DISRUPTION_PROGRAM_RETURNED'in(d/'RETURN.LOG').read_bytes()
  keep={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
  result={**c,'recipe':RECIPE,'baseline_sha256':SHA(base),'applied_patches':applied,'date':date,'time':clock,'timeout_seconds':c.get('timeout',120),'timed_out':timed,'program_returned':returned,'complete':returned and not timed,'binaries':bins,'files':{k:SHA((d/k).read_bytes())for k in sorted(keep)}}
  (d/'result.json.gz').write_bytes(gzip.compress((json.dumps(result,indent=2)+'\n').encode(),mtime=0))
  for p in d.iterdir():
   if p.is_file()and p.name not in keep|{'result.json.gz'}:p.unlink()
  print(c['name'],result['complete'],'holes',text.count('A *-BLACK HOLE-*'),'ship',mbf.get(after,2,57),'turns',mbf.get(after,2,49),'cash',mbf.get(after,2,81),flush=True)
  return result
 with ThreadPoolExecutor(max_workers=workers)as pool:results=list(retained.values())+list(pool.map(run,[c for c in selected if not c.get('parent')and c['name']not in retained]))
 for c in selected:
  if c.get('parent')and c['name']not in retained:results.append(run(c))
 (destination/'results.json.gz').write_bytes(gzip.compress((json.dumps(dict(recipe=RECIPE,scenarios=results),indent=2)+'\n').encode(),mtime=0))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--workers',type=int,default=4);p.add_argument('--diagnostic',action='store_true');p.add_argument('--reuse',type=Path);a=p.parse_args();todo=diagnostic_cases()if a.diagnostic else cases()
 if not shutil.which('dosbox-staging'):p.error('DOSBox Staging required')
 if a.only:
  unknown=set(a.only)-{c['name']for c in todo}
  if unknown:p.error('unknown control '+str(unknown))
  todo=[c for c in todo if c['name']in a.only]
  if any(c.get('parent')and c['parent']not in a.only for c in todo):p.error('include exact declared parent')
 capture(a.destination.resolve(),todo,a.workers,a.reuse)
