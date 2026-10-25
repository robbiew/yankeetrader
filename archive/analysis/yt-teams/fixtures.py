from pathlib import Path
import sys,shutil
sys.path.insert(0,'analysis/yt-maint');from experiments import put
r=Path('analysis/yt-combat/experiments')
for name in ['create','join','wrong','full','member','captain','quit','last','dead-captain','defense','transfer']:
 d=r/('fixture-team-'+name);shutil.copytree(r/'fixture-planet-team-bank',d);b=bytearray((d/'YTDATA.DAT').read_bytes())
 # Team metadata shares the sector records for sectors 1..50.
 for i in range(52,102):
  p=(i-1)*137;b[p:p+41]=b' '*41
  for o in [73,77,109,117,121,125]:put(b,i,o,0)
  b[p+113:p+117]=b'    '
 for i,n in [(2,'Q'),(3,'Enemy'),(4,'Third'),(5,'Fourth'),(6,'Fifth')]:
  if i>3:b[(i-1)*137:i*137]=b[137:274]
  p=(i-1)*137;b[p:p+41]=(n+' ').encode().ljust(41,b' ')
  for o,v in {45:0,57:100,61:1000,81:100000,85:len(n)+1,89:0,125:1}.items():put(b,i,o,v)
 put(b,4053,73,3);put(b,4053,77,100);put(b,4053,117,10000)
 members=[2,3,0,0];captain=2
 if name in ['join','wrong']:members=[3,0,0,0];captain=3
 if name=='full':members=[3,4,5,6];captain=3
 if name=='last':members=[2,0,0,0]
 if name=='create':members=[0,0,0,0];captain=0
 for i in members:
  if i:put(b,i,89,1)
 p=51*137;b[p:p+41]=b'Orion'.ljust(41,b' ');put(b,52,73,5 if captain else 0);put(b,52,77,captain);b[p+113:p+117]=b'ABCD'
 for o,i in zip([109,117,121,125],members):put(b,52,o,i)
 if name=='dead-captain':put(b,2,45,2)
 if name in ['defense','transfer']:
  put(b,152,81,100);put(b,152,85,3)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
for name in ['transfer-current','transfer-foreign','captain-gone','port-account','owned-assets']:
 d=r/('fixture-team-'+name);shutil.copytree(r/'fixture-team-captain',d);b=bytearray((d/'YTDATA.DAT').read_bytes())
 if name.startswith('transfer-'):put(b,151,81,100);put(b,151,85,3 if name=='transfer-current' else 4)
 if name=='captain-gone':put(b,2,89,0)
 if name=='port-account':put(b,3053,97,3);put(b,3053,89,10000);put(b,3,117,1)
 if name=='owned-assets':
  b[(4054-1)*137:4054*137]=b[(4053-1)*137:4053*137]
  for rec,o,v in [(4054,73,2),(4054,117,12000),(152,93,3),(153,81,200),(153,85,2),(3053,97,2),(3053,89,7000),(2,117,1)]:put(b,rec,o,v)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
