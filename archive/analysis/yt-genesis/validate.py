"""Verify preserved original-DOS results, never execute/reset a live game."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis/yt-maint'))
from experiments import get,record
R=ROOT/'analysis/yt-combat/experiments';checks=0
def check(v,msg):
 global checks
 assert v,msg
 checks+=1
def load(n,f='YTDATA.DAT'):return (R/n/f).read_bytes()
def log(n):return (R/n/'GAME.LOG').read_text(errors='replace').replace('\\r\\n','\n')
for n,phrase in [('gen-299','1 short'),('gen-disabled','*FUNCTION DISABLED*'),('gen-cancel','Alas, today'),('gen-custom','198 short')]:
 a=load(n,'before.dat');b=load(n)
 check(phrase in log(n),n+' output')
 check('Initialization completed sucessfully!' not in log(n),n+' no reset')
 check(a[51*137:]==b[51*137:],n+' sector/port/planet records unchanged')
 check(get(a,2,117)==get(b,2,117),n+' port count retained')
for n,threshold in [('gen-300',300),('gen-counter',300),('gen-custom200',200),('gen-20',20)]:
 a=load(n,'before.dat');b=load(n)
 check('Initialization completed sucessfully!' in log(n),n+' completed')
 check(len(b)==4151*137,n+' record size/count')
 check(all(record(b,i)['text']=='' and all(get(b,i,o)==0 for o in range(41,133,4)) for i in range(2,52)),n+' all humans cleared')
 check(all(get(b,i,97)==0 for i in range(3052,4052)),n+' all ports unowned')
 check(all(get(b,i,85)==0 for i in range(4052,4152)),n+' all planets inactive')
 check(all(get(b,i,89)==0 for i in range(3052,4052)),n+' all treasuries cleared')
 check(record(b,3052)['text']=='Earth' and get(b,3052,93)==1 and get(b,52,65)==1,n+' Earth linkage')
 check(get(b,1,105)==threshold,n+' normalized threshold')
 check(get(b,1,125)==6324,n+' reset year')
 check(get(b,1,81)==296,n+' yesterday maintenance')
 check(get(b,3052,45)==287 and all(get(b,3052,o)==0 for o in [49,53,57]),n+' production pending')
 check(all(get(a,1,o)==get(b,1,o) for o in [49,53,57,61,65,69,73,77,93,101,121]),n+' settings retained')
 check(not (R/n/'RMTINIT.TMP').exists(),n+' handoff consumed')
 check((R/n/'YTNAME.DAT').read_bytes().rstrip(b'\x1a\r\n')==b'Dummy,Dummy,Dummy,Dummy',n+' aliases reset')
 check('Prophesy has been fulfilled' in (R/n/'YTNEWS.DAT').read_text(errors='replace'),n+' announcement')
 check(a[51*137:3051*137]!=b[51*137:3051*137],n+' map changed')
check(sum(get(load('gen-counter','before.dat'),i,97)==2 for i in range(3052,4052))==0,'counter fixture has no owned ports')
a=load('gen-postmaint','postreset.dat');b=load('gen-postmaint')
check(get(a,1,81)==296 and get(b,1,81)==297,'first maintenance date')
check('Daily Maintenance Completed OK' in (R/'gen-postmaint/FIRSTMAI.LOG').read_text(errors='replace'),'maintenance completed')
check([record(b,i)['text'] for i in [4052,4150,4151]]==['The Wanderer','Mercenary Base','Xannoron'],'maintenance builds NPC planets')
check(all(get(b,3052,s)==10*get(b,3052,p) for s,p in [(49,61),(53,65),(57,69)]),'maintenance fills Earth stock')
for row in json.loads((ROOT/'analysis/executable-inventory.json').read_text()):
 check(hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['sha256'],'original hash '+row['file'])
for name,digest in json.loads((ROOT/'analysis/yt-genesis/original-hashes.json').read_text()).items():
 check(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'original '+name)
 check(hashlib.sha256((R/'gen-300'/name).read_bytes()).hexdigest()==digest,'tested '+name)
print(f'{checks} checks passed across eight Genesis sessions and one post-reset maintenance run.')
