from pathlib import Path
import sys,hashlib,re,json
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'yt-maint'))
from experiments import get
sys.path.insert(0,str(ROOT))
from recovered_rules import sector_fighters,planet_ground,assault
count=0
rows=[]
def ck(v,msg):
 global count
 assert v,msg
 count+=1
h=hashlib.sha256((ROOT.parent.parent/'YT.EXE').read_bytes()).hexdigest()
ck(h=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037','original game unchanged')
for name in ('missile-fighters','missile-mines','missile-shields','missile-planet','missile-production','missile-uncloaked','missile-shipfighters','missile-ground-fixed','assault-win','assault-loss'):
 d=ROOT.parent/'yt-combat/experiments'/name
 b=(d/'YTDATA.DAT').read_bytes();before=(d/'before.dat').read_bytes();raw=(d/'GAME.LOG').read_bytes();log=raw.decode(errors='replace').replace('\\r\\n','\n')
 ck(hashlib.sha256((d/'YT.EXE').read_bytes()).hexdigest()==h,name+' original copy')
 ck('Returning to Yankee Trader Local Logon Program' in log,name+' normal return')
 ck('Illegal function' not in log and 'Syntax error' not in log,name+' runtime errors')
 r={'case':name,'log_sha256':hashlib.sha256(raw).hexdigest(),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(b).hexdigest()}
 if name.startswith('missile'):
  ck(get(b,2,97)==80,name+' ammunition')
  ck(get(b,2,49)==499,name+' turn cost')
  if name=='missile-fighters':
   hits=int(re.search(r'Missiles destroyed (\d+) fighters',log)[1]);ck(get(b,152,81)==1000000-hits,name+' persisted damage');r.update(hits=hits,sheet_range=[49000,51000])
  elif name=='missile-mines':
   hits=int(re.search(r'missiles destroyed (\d+) mines',log)[1]);ck(get(b,152,129)==10000-hits and hits==20,name+' one missile per mine');r.update(hits=hits,sheet=20)
  elif name=='missile-shields':
   ck(get(b,3,53)==1000000 and get(b,3,61)==0,name+' cloaked target skipped');r['shield_damage']=0
  elif name in ('missile-uncloaked','missile-shipfighters'):
   shields,fighters=map(int,re.search(r'shields to (\d+) units and destroying (\d+) fighters',log).groups())
   ck(get(b,3,53)==shields,name+' shield persistence');ck(get(b,3,61)==get(before,3,61)-fighters,name+' fighter persistence')
   ck('shot back with 1 missiles' in log,name+' retaliation observed');r.update(shield_damage=1000000-shields,fighter_damage=fighters,sheet_shields=23000,sheet_fighters=[49000,51000])
  elif name=='missile-production':
   loss,total=map(float,re.search(r'Productivity reduced by ([\d.]+) units to ([\d.]+)',log).groups());ck(abs(sum(get(b,4052,o) for o in (45,49,53))-total)<.1,name+' production persistence');r.update(production_damage=loss,sheet_range=[20000,60000])
  else:
   left=int(re.search(r'Ground forces reduced to (\d+)',log)[1]);ck(get(b,4052,77)==left,name+' ground persistence');r.update(initial_ground=5000,final_ground=left,sheet_loss=250)
 else:
  committed=1000 if name.endswith('win') else 100
  ck(get(b,2,121)==10000-committed,name+' committed forces removed')
  ck(get(b,2,49)==500,name+' no turn deducted')
  a=committed;defenders=int(re.search(r'Sensors report ground forces of (\d+)',log)[1]);initial=defenders
  events=re.findall(r'(Your forces remaining\s*:|Ground forces remaining:) (\d+)!',log)
  ck(bool(events),name+' combat trace')
  for side,value in events:
   value=int(value)
   if side.startswith('Your'):ck(0<=value<=a and a-value<=defenders,name+' attacker step bound');a=value
   else:ck(0<=value<=defenders and defenders-value<=a,name+' defender step bound');defenders=value
  if name.endswith('win'):
   ck("You've captured the planet!" in log,name+' capture')
   ck(get(b,4052,73)==2 and get(b,4052,77)==a,name+' ownership and garrison')
  else:
   ck('Attack Failed!' in log,name+' failure')
   ck(get(b,4052,73)==3 and get(b,4052,77)==defenders,name+' owner and defenders retained')
  r.update(committed=committed,initial_defenders=initial,surviving_attackers=a,surviving_defenders=defenders,garrison=get(b,4052,77))
 rows.append(r)
# Separate algorithm sanity checks with deterministic injected draws, not DOS runs.
ck(sector_fighters(20,1000000,lambda:.5)==(50000,20),'model sector mean draw')
ck(planet_ground(20,5000,lambda:.5)==(4750,20),'model ground mean draw')
ck(assault(1000,10,lambda:.1)[:2]==(1000,0),'model victorious assault')
ck(assault(100,100000,lambda:.5)[:2]==(0,100000),'model failed assault')
(ROOT/'evidence.json').write_text(json.dumps({'checks':count,'dos_sessions':rows,'model_checks':4,'limitations':['No original RNG capture or bit-exact MBF emulation.','Planet lazy updates precede combat; fixed-clock ground case isolates elapsed growth to seconds.','No spreadsheet formula models planetary assault.']},indent=2)+'\n')
print(f'{count} checks passed over {len(rows)} DOS sessions, including 4 separate model checks.')
