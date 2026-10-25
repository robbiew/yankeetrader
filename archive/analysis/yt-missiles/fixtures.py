from pathlib import Path
import sys,shutil
sys.path.insert(0,'analysis/yt-maint')
from experiments import put
root=Path('analysis/yt-combat/experiments')
for name,source in [('missile-fighters','plasma'),('missile-shields','shields'),('missile-mines','mines'),('missile-planet','planet'),('assault-win','planet'),('assault-loss','planet')]:
 d=root/('fixture-'+name);shutil.copytree(root/('fixture-'+source),d)
 b=bytearray((d/'YTDATA.DAT').read_bytes());put(b,2,97,100)
 if name.startswith('assault'):
  put(b,2,57,101);put(b,2,121,10000);put(b,4052,77,10 if name.endswith('win') else 100000)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)

for name in ('missile-production','missile-uncloaked','missile-shipfighters'):
 source='missile-planet' if name=='missile-production' else 'missile-shields'
 d=root/('fixture-'+name);shutil.copytree(root/('fixture-'+source),d)
 b=bytearray((d/'YTDATA.DAT').read_bytes())
 if name=='missile-production':
  put(b,4052,77,0)
  for off in (45,49,53):put(b,4052,off,100000)
 else:
  put(b,3,125,0)
  if name=='missile-shipfighters':put(b,3,61,1000000)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
