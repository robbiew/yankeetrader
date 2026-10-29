"""Run original Mercenary maintenance in fresh disposable copies only."""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/dos-validation/evidence'
RECIPE='mercenary-maintenance-isolation-v1'

def cases():
 result=[{'name':f'tax-{tax}','tax':tax} for tax in (0,9,10,19,90,99,100,109,110,199,200,100112)]
 result += [
  {'name':'tax-next-day','parent':'tax-199','date':'10/26/2026'},
  {'name':'split-tax-9','patches':[(3053,89,95),(3054,89,5)]},
  {'name':'split-tax-10','patches':[(3053,89,95),(3054,89,15)]},
  {'name':'union-only-spawn','human':True,'dense_defense':True,'empty_union':True,'tax':10,'patches':[(1165,81,1),(1165,85,-1)]},
  {'name':'capacity-blocked','human':True,'dense_defense':True,'tax':100,'expect_timeout':True,'timeout':8,'patches':[(1165,81,1),(1165,85,-1)]},
  {'name':'earth-tax-excluded','patches':[(3052,89,1000000)]},
  {'name':'move-zero-warp','patches':[(151,41,0),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2)]},
  {'name':'move-empty','patches':[(151,41,101),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2)]},
  {'name':'merge','patches':[(152,41,100),(152,45,0),(152,49,0),(152,53,0),(152,57,0),(152,61,0),(151,81,100),(151,85,-2),(152,81,200),(152,85,-2)]},
  {'name':'mine-kill-remainder','patches':[(151,41,101),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2),(152,129,3)]},
  {'name':'mine-one','patches':[(151,41,101),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2),(152,129,1)]},
  {'name':'xannor-defense','patches':[(151,41,101),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2),(152,81,50),(152,85,-1)]},
  {'name':'human-defense','human':True,'patches':[(151,41,101),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2),(152,81,50),(152,85,2)]},
  {'name':'planet-neutral','patches':[(151,41,101),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2),(152,93,2),(4053,73,0),(4053,129,37)]},
  {'name':'planet-human','human':True,'patches':[(151,41,101),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2),(152,93,2),(4053,73,2),(4053,129,37)]},
  {'name':'planet-held','patches':[(151,41,101),(151,45,0),(151,49,0),(151,53,0),(151,57,0),(151,61,0),(151,81,100),(151,85,-2),(151,93,2),(4053,73,-2),(4053,129,37)]},
  {'name':'base-missing-reference','patches':[(2051,93,0)]},
  {'name':'base-orphan-reference','patches':[(4150,85,0)]},
  {'name':'base-captured','human':True,'patches':[(4150,73,2),(4150,77,123),(4150,117,1234)]},
  {'name':'base-zero-reserves','patches':[(4150,77,0),(4150,117,0)]},
  {'name':'base-positive-reserves','patches':[(4150,77,1),(4150,117,1)]},
 ]
 travel=[(151,o,v)for o,v in [(41,101),(45,0),(49,0),(53,0),(57,0),(61,0),(81,100),(85,-2)]]
 result += [
  {'name':'human-strong-defense','human':True,'patches':travel+[(152,81,1000),(152,85,2)]},
  {'name':'desert-one','human':True,'patches':[(151,81,1),(151,85,2)]},
  {'name':'desert-hundred','human':True,'patches':[(151,81,100),(151,85,2)]},
  {'name':'planet-strong-ground','human':True,'patches':travel+[(152,93,2),(4053,73,2),(4053,77,500000),(4053,129,37)]},
  {'name':'planet-human-guarded','human':True,'patches':travel+[(152,93,2),(4053,73,2),(4053,129,37),(152,81,1000),(152,85,2)]},
  {'name':'planet-xannor-guarded','patches':travel+[(152,93,2),(4053,129,37),(152,81,50),(152,85,-1)]},
  {'name':'planet-human-origin','human':True,'patches':travel+[(151,93,2),(4053,73,2),(4053,129,37)]},
  {'name':'mine-large-force','patches':[p for p in travel if p[:2]!=(151,81)]+[(151,81,100000),(152,129,3)]},
  {'name':'large-xannor-battle','patches':[p for p in travel if p[:2]!=(151,81)]+[(151,81,20000),(152,81,15000),(152,85,-1)]},
 ]
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);p.add_argument('--only',nargs='+');p.add_argument('--parent-world',type=Path);args=p.parse_args()
 dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=False)
 dosbox=shutil.which('dosbox-staging')
 if not dosbox:p.error('DOSBox Staging not found')
 spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
 raw=(SOURCE/'YTDATA.DAT').read_bytes();base=bytearray(raw)
 for r in range(2,52):base[(r-1)*137:r*137]=bytes(137);mbf.put(base,r,109,-1)
 for sector in range(1,3001):
  for off in (81,85,93,105,129):mbf.put(base,51+sector,off,0)
 for port in range(1,1001):
  for off in (89,97):mbf.put(base,3051+port,off,0)
 for slot in range(1,101):base[(4050+slot)*137:(4051+slot)*137]=bytes(137)
 for slot,name,owner in ((1,'The Wanderer',0),(2,'Probe Planet',0),(99,'Mercenary Base',-2),(100,'Xannoron',-1)):
  r=4051+slot;at=(r-1)*137;base[at:at+41]=name.encode().ljust(41,b' ')
  for off,v in {41:298,73:owner,77:1,85:len(name),89:0,117:1}.items():mbf.put(base,r,off,v)
 for r,o,v in ((2050,93,1),(2051,93,99),(1165,93,100),(1,117,1114),(52,105,1114)):mbf.put(base,r,o,v)
 base=bytes(base);sha=lambda b:hashlib.sha256(b).hexdigest()
 todo=cases()
 if args.only:
  if set(args.only)-{c['name'] for c in todo}:p.error('unknown case')
  todo=[c for c in todo if c['name'] in args.only]
 (dest/'baseline.dat.gz').write_bytes(gzip.compress(base,mtime=0))
 def run(case):
  name=case['name'];d=dest/name;d.mkdir()
  for f in SOURCE.iterdir():
   if f.suffix.upper() in ('.DAT','.ASC'):shutil.copy2(f,d/f.name)
  for name in ('YTMAINT.EXE','BRUN30.EXE'):shutil.copy2(ROOT/'archive/dos-original'/name,d/name)
  data=bytearray(base)
  if case.get('parent'):
   parent=args.parent_world or dest/case['parent']/'after.dat.gz'
   data=bytearray(gzip.decompress(parent.read_bytes()))
  if case.get('human'):
   template=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
   data[137:274]=template[137:274]
   for off,v in {41:297,45:0,57:7,89:0,109:0}.items():mbf.put(data,2,off,v)
  if case.get('dense_defense'):
   for sector in range(2,3001):
    mbf.put(data,51+sector,81,1000);mbf.put(data,51+sector,85,2)
  if case.get('empty_union'):
   for sector in range(2,8):
    mbf.put(data,51+sector,81,0);mbf.put(data,51+sector,85,0)
  patches=list(case.get('patches',[]))+([(3053,89,case['tax']*10)] if 'tax' in case else [])
  for r,o,v in patches:mbf.put(data,r,o,v)
  before=bytes(data);(d/'YTDATA.DAT').write_bytes(before)
  date=case.get('date','10/25/2026')
  commands=[f'mount c {d}','c:','date '+date,'time 00:00:00','date > dosdate.log','time > dostime.log','ytmaint > maint.log','exit']
  complete=True
  try:
   with (d/'dosbox.log').open('w') as log:
    subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in ('-c',c)],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=log,stderr=subprocess.STDOUT,timeout=case.get('timeout',45),check=True)
  except subprocess.TimeoutExpired:complete=False
  after=(d/'YTDATA.DAT').read_bytes();text=(d/'MAINT.LOG').read_bytes().decode('cp437').replace('\r\n','\n') if (d/'MAINT.LOG').exists() else ''
  (d/'transcript.txt').write_text(text)
  for tag,b in [('before',before),('after',after)]:(d/(tag+'.dat.gz')).write_bytes(gzip.compress(b,mtime=0))
  keep={'before.dat.gz','after.dat.gz','transcript.txt','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'}
  result={**case,'recipe':RECIPE,'timed_out':not complete,'timeout_seconds':case.get('timeout',45),'complete':complete and 'Daily Maintenance Completed OK' in text,'source_sha256':sha(raw),'baseline_sha256':sha(base),'before_sha256':sha(before),'after_sha256':sha(after),'executable_sha256':sha((d/'YTMAINT.EXE').read_bytes()),'runtime_sha256':sha((d/'BRUN30.EXE').read_bytes()),'date':date,'time':'00:00:00','patches':patches,'files':{f:sha((d/f).read_bytes()) for f in keep if (d/f).exists()}}
  (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  for f in d.iterdir():
   if f.name not in keep|{'result.json'} and f.is_file():f.unlink()
  print(case['name'],result['complete'],flush=True);return result
 with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,[c for c in todo if not c.get('parent')]))
 for case in todo:
  if case.get('parent'):results.append(run(case))
 (dest/'results.json').write_text(json.dumps({'recipe':RECIPE,'scenarios':results},indent=2)+'\n')
if __name__=='__main__':main()
