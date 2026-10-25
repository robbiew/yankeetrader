import sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'yt-maint'))
from experiments import enc,dec,get,put
ROOT=Path(__file__).resolve().parent
for kind in ('plasma','surrender','immediate'):
 d=ROOT/'experiments'/('fixture-'+kind);d.mkdir(exist_ok=True)
 for p in (ROOT/'experiments/login-keyfeed').iterdir():
  if p.suffix.upper() in ('.DAT','.ASC','.ANS','.DOC','.EXE','.DEF'):shutil.copy2(p,d/p.name)
 b=bytearray((d/'YTDATA.DAT').read_bytes())
 for off,v in {49:500,53:2000000,57:100,61:2000000,105:0,113:10}.items():put(b,2,off,v)
 b[274:315]=b'Enemy '+b' '*35
 for off,v in {41:297,49:500,53:100,57:200,61:100,85:6,97:1,109:-1,125:1}.items():put(b,3,off,v)
 for sector in range(100,104):
  r=51+sector;b[(r-1)*137:r*137]=bytes(137)
  for off,v in {41:sector+1,45:sector-1}.items():put(b,r,off,v)
 if kind=='plasma':
  put(b,152,81,1000000);put(b,152,85,3)
 else:
  put(b,151,81,500000 if kind=='surrender' else 1000);put(b,151,85,3)
 (d/'YTDATA.DAT').write_bytes(b)
 (d/'before.dat').write_bytes(b)
