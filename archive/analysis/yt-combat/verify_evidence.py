"""Check captured unmodified DOS game evidence, without rerunning the emulator."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'yt-maint'))
from experiments import get
sys.path.insert(0,str(ROOT))
from recovered_rules import surrender,plasma_absorb,plasma_energy
checks=0
rows=[]
def check(value,message):
 global checks
 assert value,message
 checks+=1
runtime_hash=hashlib.sha256((ROOT.parent.parent/'BRUN30.EXE').read_bytes()).hexdigest()
original=hashlib.sha256((ROOT.parent.parent/'YT.EXE').read_bytes()).hexdigest()
check(original=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037','original YT hash')
for name in ('plasma-one','plasma-fast','plasma-two','plasma-mines','plasma-shields','plasma-distance','plasma-planet','surrender-first','surrender-confirm','surrender-immediate','surrender-ten','surrender-xannor'):
 d=ROOT/'experiments'/name
 log=(d/'GAME.LOG').read_text(errors='replace').replace('\\r\\n','\n')
 check(hashlib.sha256((d/'YT.EXE').read_bytes()).hexdigest()==original,name+' copied binary')
 check(hashlib.sha256((d/'BRUN30.EXE').read_bytes()).hexdigest()==runtime_hash,name+' copied runtime')
 check('Syntax error' not in log and 'Illegal function' not in log,name+' runtime errors')
 b=(d/'YTDATA.DAT').read_bytes()
 row={'case':name,'game_finished': 'Returning to Yankee Trader Local Logon Program' in log,
      'log_sha256':hashlib.sha256((d/'GAME.LOG').read_bytes()).hexdigest(),
      'data_sha256':hashlib.sha256(b).hexdigest()}
 if name.startswith('plasma'):
  check('Plasma bolts dissipated.' in log,name+' attack complete')
  n=2 if name=='plasma-two' else 1
  check(get(b,2,113)==10-n,name+' ammunition persisted')
  check(get(b,2,49)==499,name+' exactly one turn')
  if name in ('plasma-one','plasma-fast','plasma-two','plasma-distance'):
   hits=int(re.search(r'bolts destroyed (\d+) fighters!',log)[1]);sector=102 if name.endswith('distance') else 101
   check(get(b,51+sector,81)==1000000-hits,name+' sector damage persisted')
   row.update(actual=hits,spreadsheet=50000*n*n)
  elif name=='plasma-mines':
   hits=int(re.search(r'bolts destroyed (\d+) mines',log)[1]);check(get(b,152,129)==10000-hits,name+' mine damage persisted')
   row.update(actual=hits,spreadsheet=250)
  elif name=='plasma-shields':
   remaining=int(re.search(r'shields to (\d+) units',log)[1]);check(get(b,3,53)==remaining,name+' ship damage persisted')
   row.update(actual=1000000-remaining,spreadsheet=25000)
  else:
   lost,total=map(float,re.search(r'Productivity reduced by ([\d.]+) units to ([\d.]+)',log).groups())
   gf_lost,gf_left=map(int,re.search(r'Ground forces reduced by (\d+) units to (\d+)',log).groups())
   check(abs(sum(get(b,4052,o) for o in (45,49,53))-total)<.02,name+' productivity total persisted')
   check(get(b,4052,77)==gf_left,name+' ground damage persisted')
   row.update(ground_damage=gf_lost,spreadsheet_ground=1000,production_damage=lost,spreadsheet_production=[1000,3000])
  if name=='plasma-distance':
   check('sector 101. 2500000 Megawatts remaining.' in log,'first hop full power')
   check('sector 102. 2450000 Megawatts remaining.' in log,'second hop attenuation')
 else:
  lost=int(re.search(r'You lost (\d+) fighter',log)[1]);killed=int(re.search(r'You destroyed (\d+) enemy',log)[1])
  m=re.search(r'(\d+) fighters surrendered!',log);joined=int(m[1]) if m else 0
  check(get(b,2,61)==2000000-lost+joined,name+' player accounting persisted')
  check(get(b,151,81)==0,name+' defenders cleared')
  check(killed+joined==(500000 if name in ('surrender-first','surrender-confirm') else 1000),name+' defender accounting')
  row.update(lost=lost,killed=killed,joined=joined)
  if name=='surrender-immediate':check((lost,killed,joined)==(0,0,1000),'strictly above ten immediate surrender')
  if name=='surrender-ten':check(lost+killed>0,'exactly ten does not immediately surrender')
  if name=='surrender-xannor':check(joined==0 and 'Whee fyte to the deeth' in log,'Xannor refusal')
  if name in ('surrender-first','surrender-confirm'):row['spreadsheet_joined']=84040
 rows.append(row)
# Independent model checks, explicitly separate from DOS observations.
check(surrender(10001,1000,1,lambda:.5)['joined']==1000,'model strict threshold')
check(surrender(10000,1000,1,lambda:.5)['joined']==950,'model exactly ten one defender batch')
check(plasma_energy(1,2)==2450000,'model distance')
check(plasma_absorb(2500000,1000000,'fighters',lambda:.5)[0]==50400,'model discrete fighter steps')
check(plasma_absorb(2500000,10000,'mines',lambda:.5)[0]==362,'model discrete mine steps')
result={'checks':checks,'yt_exe_sha256':original,'dos_cases':rows,'limitations':['RNG sequence not captured; model checks do not establish bit-exact MBF/RNG reproduction.','Early exploratory probes and incomplete logins are excluded.','Planet load applies lazy updates before impact; use reported impact damage, not raw before/after difference.']}
(ROOT/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'{checks} checks passed across {len(rows)} captured combat sessions; 5 checks concern the reconstructed model.')
