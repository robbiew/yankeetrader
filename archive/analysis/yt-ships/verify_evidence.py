from pathlib import Path
import sys,re,json,hashlib
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'yt-maint'))
from experiments import get
sys.path.insert(0,str(ROOT))
from recovered_rules import fighter_duel,shield_duel,retaliation_volley,cloak_tick
root=ROOT.parent/'yt-combat/experiments'
checks=0;results=[]
def ck(ok,msg):
 global checks
 assert ok,msg
 checks+=1
h=hashlib.sha256((ROOT.parent.parent/'YT.EXE').read_bytes()).hexdigest()
ck(h=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037','archival executable')
names=['ship-kill','ship-hidden','ship-team','ship-fight','ship-retaliation','ship-earthdeath','ship-counterdeath-adj','ship-counter-six-adj','ship-cloakdecay','ship-relogin-same','ship-relogin-next','ship-self-same','ship-self-next','ship-refresh-turns','ship-earth-respawn','ship-anticloak','ship-counter-relogin']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in names:
 d=root/name;b=(d/'YTDATA.DAT').read_bytes();before=(d/'before.dat').read_bytes();log=(d/'GAME.LOG').read_text(errors='replace').replace('\\r\\n','\n')
 ck(digest(d/'YT.EXE')==h,name+' copied original')
 ck('Syntax error' not in log and 'Illegal function' not in log,name+' runtime errors')
 row={'scenario':name,'normal_return':'Returning to Yankee Trader Local Logon Program' in log,'log_sha256':digest(d/'GAME.LOG'),'before_sha256':digest(d/'before.dat'),'after_sha256':digest(d/'YTDATA.DAT')}
 if name in ('ship-kill','ship-fight','ship-retaliation'):
  lost=int(re.search(r'You lost (\d+) fighter',log)[1]);killed=int(re.search(r'You destroyed (\d+) enemy',log)[1])
  ck(get(b,3,61)==get(before,3,61)-killed,name+' defender fighter accounting')
  ck(get(b,2,49)==500,name+' no direct attack turn fee')
  if 'Fighters remaining:' in log:
   f=int(re.search(r'Fighters remaining: (\d+)',log)[1]);s=int(re.search(r'Shields reduced to: (\d+)',log)[1])
   ck(get(b,2,61)==9000+f,name+' committed survivors restored');ck(get(b,3,53)==s,name+' shield persistence')
   row.update(shield_stage_survivors=f,target_shields=s)
  else:ck(get(b,2,61)==0 and get(b,2,45)==0,name+' depleted attacking fighters but no death')
  row.update(attacker_fighter_losses=lost,defender_fighter_losses=killed)
  if name=='ship-kill':
   loot=int(re.search(r'Credits: (\d+)',log)[1]);ck(get(b,2,81)==1005+loot,'salvage credited');ck(get(b,3,45)==2 and get(b,3,57)==0,'victim death marker and position');ck(get(b,3,81)==12345,'victim retains credits while dead')
  if name=='ship-retaliation':ck('shot back' not in log and get(b,3,97)==1000,'direct failed attack has no missile retaliation in fixture')
 elif name in ('ship-hidden','ship-team'):
  ck(get(b,3,61)==10 and get(b,3,53)==10,name+' target untouched')
  ck("There's no one here!" in log if name.endswith('hidden') else 'NOT attacking team member' in log,name+' selection branch')
 elif name=='ship-earthdeath':
  ck(get(b,52,129)==60,'Earth retains 60 mines');ck(get(b,2,45)==2 and get(b,2,57)==0,'mine-triggered self death');ck('Your ship has been destroyed!' in log,name+' death transcript')
 elif name=='ship-earth-respawn':
  ck(get(before,52,129)==60 and get(b,52,129)==49,'Earth spawn mines consumed but persist');ck('EMERGENCY WARP ENGAGED' in log,'replacement ship forced escape');ck(get(b,3,49)==409 and get(b,3,61)==0 and get(b,3,53)==0,'replacement loses combat defenses and 91 turns')
 elif name in ('ship-counterdeath-adj','ship-counter-six-adj'):
  n=int(re.search(r'shot back with (\d+) missiles',log)[1]);ck(get(b,3,97)==get(before,3,97)-n,name+' counter ammunition');ck(get(b,2,97)==0,name+' initial missile used');row['retaliation_missiles']=n
  if name=='ship-counter-six-adj':ck(n==6,'stored score 500000 produces six');ck(get(b,2,61)==1991521,'counter fighter damage persisted')
  else:ck('Q  was destroyed!' in log and get(b,2,57)==0 and get(b,2,45)==2,'enemy missile death ends with self marker')
 elif name=='ship-cloakdecay':
  ck(get(b,2,49)==475 and abs(get(b,2,125)-.99)<1e-6,'25-turn boundary cloak decay')
 elif name=='ship-anticloak':
  ck('Enemy  is uncloaked!' in log and 'Attack Enemy' in log,'anti-cloak exposes selectable target');ck(get(b,2,81)==500000,'500000 anti-cloak fee');ck(get(b,3,125)==1,'target cloak energy not persistently removed');ck('Cloak Energy. : FAIL' in log,'buyer session cloak disabled')
 elif name in ('ship-self-same','ship-counter-relogin'):
  ck('You managed to kill yourself' in log and 'You will be allowed to play again tomorrow!' in log,name+' same-day refusal');ck('Your ship has been built.' not in log,name+' no replacement')
 else:
  ck('Your ship has been built.' in log,name+' rebuild')
  for o,v in {45:0,49:500,53:100,57:1,61:25,65:10,81:1005,97:1,113:0,125:1,129:0}.items():ck(get(b,3,o)==v,name+f' reset {o}')
  if name=='ship-refresh-turns':ck(get(before,3,49)==37,'refill from 37, not already 500')
 results.append(row)
# Paired processes sharing one world: inspect transitions, not only final output.
for name in ('ship-online','ship-stale-position'):
 d=root/name;ck(digest(d/'YT.EXE')==h,name+' executable');b=(d/'YTDATA.DAT').read_bytes();a=(d/'ATTACK.LOG').read_text(errors='replace').replace('\\r\\n','\n');v=(d/'VICTIM.LOG').read_text(errors='replace').replace('\\r\\n','\n')
 ck('You destroyed the ship' in a,name+' attacker completed kill')
 if name=='ship-online':
  snaps=[p.read_bytes() for p in sorted(d.glob('snapshot-*.dat'))];ck(any(get(x,3,45)==2 and get(x,3,57)==0 for x in snaps),'online death before ghost move');ck(get(b,3,45)==2 and get(b,3,57)==101 and get(b,3,49)==499,'dead player subsequently moved and spent turn');ck('Move to which sector? 101' in v,'ghost movement input captured')
 else:
  events=json.loads((d/'events.json').read_text());m=next(i for i,e in enumerate(events) if e['death_sector_fighters_shields_credits'][:2]==[0,101]);k=next(i for i,e in enumerate(events) if e['death_sector_fighters_shields_credits'][0]==2);ck(m<k,'victim moved before stale kill');ck('Sector: 100' in a and 'Attack Enemy' in a,'attacker stayed in cached target sector');ck('Sector: 101' in v,'victim moved to different sector')
 results.append({'scenario':name,'processes':2,'attacker_log_sha256':digest(d/'ATTACK.LOG'),'victim_log_sha256':digest(d/'VICTIM.LOG'),'after_sha256':digest(d/'YTDATA.DAT')})
# Model examples, separate from DOS verification.
ck(fighter_duel(10,10,1,lambda:.5)==(10,0,0,10),'model fighter duel')
ck(shield_duel(200,200,lambda:.1)==(200,0),'model large shield batches')
ck(shield_duel(100,10,lambda:.5)==(0,10),'model small shield batches')
ck(retaliation_volley(500000,100,lambda:.1)==6,'model score retaliation')
ck(retaliation_volley(0,100,lambda:.1)==11,'model fallback retaliation')
ck(abs(cloak_tick(1,475)-.99)<1e-9,'model cloak decay')
(ROOT/'evidence.json').write_text(json.dumps({'checks':checks,'standalone_sessions':len(names),'paired_scenarios':2,'total_dos_processes':len(names)+4,'model_checks':6,'results':results,'limits':['No bit-exact original RNG capture or MBF arithmetic.','Concurrent findings reproduced in two DOSBox processes sharing one isolated directory.','Replacement ship Earth-mine probe stopped at a command prompt after forced emergency escape.','Same-sector missile self-destruct probes are excluded from retaliation conclusions.']},indent=2)+'\n')
print(f'{checks} checks passed; {len(names)} standalone sessions and two paired scenarios ({len(names)+4} DOS processes); six separate model checks.')
