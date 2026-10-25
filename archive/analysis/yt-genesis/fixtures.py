from pathlib import Path
import shutil,sys
sys.path.insert(0,'analysis/yt-maint')
from experiments import put
r=Path('analysis/yt-combat/experiments')
for name,count,threshold,actual in [('299',299,300,299),('300',300,300,300),('cancel',300,300,300),('disabled',301,301,301),('counter',300,300,0)]:
 d=r/('fixture-gen-'+name);shutil.copytree(r/'fixture-trade-earth',d)
 for f in ['RMT-INIT.EXE','YTMAINT.EXE']:shutil.copy2(f,d/f)
 b=bytearray((d/'YTDATA.DAT').read_bytes());put(b,1,105,threshold);put(b,2,117,count)
 for p in range(1,1001):put(b,3051+p,97,2 if p<=actual else 0)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
# Customized defaults and the runtime's hidden <20 fallback.
for name,count,threshold,actual in [('custom',2,2,2),('custom200',200,2,200),('20',20,20,20)]:
 d=r/('fixture-gen-'+name);shutil.copytree(r/'fixture-gen-300',d)
 b=bytearray((d/'YTDATA.DAT').read_bytes())
 for o,v in {49:777,65:31,69:4321,73:17,77:9,101:7,105:threshold,121:850,125:7000}.items():put(b,1,o,v)
 put(b,2,117,count)
 for p in range(1,1001):put(b,3051+p,97,2 if p<=actual else 0)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
