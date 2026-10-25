from pathlib import Path
import sys,shutil
sys.path.insert(0,'analysis/yt-maint')
from experiments import put
root=Path('analysis/yt-combat/experiments')
for name in ('kill','hidden','team','fight','retaliation'):
 d=root/('fixture-ship-'+name);shutil.copytree(root/'fixture-missile-shipfighters',d)
 b=bytearray((d/'YTDATA.DAT').read_bytes())
 for r,vals in [(2,{57:100,61:10000,53:10000,81:1005,97:0,113:0,125:1}),(3,{57:100,61:10,53:10,97:0,113:0,125:0,81:12345,93:7,129:5})]:
  for off,v in vals.items():put(b,r,off,v)
 if name=='hidden':put(b,3,125,1)
 if name=='team':put(b,2,89,1);put(b,3,89,1)
 if name=='fight':put(b,3,61,1000);put(b,3,53,10000)
 if name=='retaliation':
  put(b,2,53,1);put(b,2,61,10);put(b,3,97,1000);put(b,3,61,1000000);put(b,3,53,1000000)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
