from pathlib import Path
import sys,shutil
sys.path.insert(0,'analysis/yt-maint')
from experiments import put
r=Path('analysis/yt-combat/experiments')
for name in ('high','low','sell','self','other','unowned','quote','port-buy','earth'):
 d=r/('fixture-trade-'+name);shutil.copytree(r/'fixture-ship-hidden',d);b=bytearray((d/'YTDATA.DAT').read_bytes())
 for o,v in {57:100,65:1000,69:0,73:0,77:0,81:1000000,117:0}.items():put(b,2,o,v)
 put(b,151,65,2)
 rec=3053;b[(rec-1)*137:rec*137]=bytes(137);b[(rec-1)*137:(rec-1)*137+41]=b'Test Port'+b' '*32
 vals={41:2,45:297,49:1000,53:1000,57:1000,61:100,65:100,69:100,73:50,77:-50,81:-50,85:9,89:0,93:100,97:0,101:0}
 if name=='low':vals[49]=100
 if name=='sell':vals[73]=-50;put(b,2,69,100)
 if name=='self':vals[97]=2;put(b,2,117,1)
 if name=='other':vals[97]=3;put(b,3,117,1)
 if name=='quote':vals[49]=0
 for o,v in vals.items():put(b,rec,o,v)
 if name=='earth':
  for rec in (2,3):
   for o,v in {57:1,81:2000000 if rec==2 else 1000000,61:25,125:1,117:0}.items():put(b,rec,o,v)
  for o,v in {45:297,89:0,97:0,101:0}.items():put(b,3052,o,v)
 p=d/'YTNAME.DAT';p.write_bytes(p.read_bytes().rstrip(b'\x1a')+b'Enemy,,Enemy,\r\n\x1a')
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
