"""Capture DOS planet rename screens in disposable copies of known planet fixtures."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('destination',type=Path)
parser.add_argument('--archive',type=Path,default=Path(__file__).resolve().parents[1]/'archive')
parser.add_argument('--dosbox',default='dosbox-staging')
parser.add_argument('--only',nargs='+',help='Capture only the named scenarios')
args=parser.parse_args()
dosbox=shutil.which(args.dosbox)
if not dosbox:parser.error('DOSBox Staging not found')
root=args.archive.resolve();out=args.destination.resolve();out.mkdir(parents=True,exist_ok=False)
# @ captures text-mode B800 cells without sending a key; ~ waits 36 BIOS ticks.
scenarios=[
 ('last-slot','planet-takeall','\r~~~~~\r~L;N\r~~@New Eden\r~~@Y\r~~@L;Q;Y\r~\r~\r'),
 ('other-reserved','planet-takeall','\r~~~~~\r~L;N\r~~@Xannoron\r~~@N;Mercenary Base\r~~@L;Q;Y\r~\r~\r'),
 ('spaces','planet-takeall','\r~~~~~\r~L;N\r~~@   Test  Name   \r~~@Y\r~~@D\r~~@L;Q;Y\r~\r~\r'),
 ('case','planet-takeall','\r~~~~~\r~L;N\r~~@mIxEd nAME\r~~@Y\r~~@D\r~~@L;Q;Y\r~\r~\r'),
 ('punctuation','planet-takeall','\r~~~~~\r~L;N\r~~@o\'brien alpha-beta x_Y 42base\r~~@Y\r~~@D\r~~@L;Q;Y\r~\r~\r'),
 ('owner','planet-takeall','\r~~~~~\r~L;N\r~~@New Eden\r~~@Y\r~~@D\r~~@L;Q;Y\r~\r~\r'),
 ('blank','planet-takeall','\r~~~~~\r~L;N\r~~@\r~~@L;Q;Y\r~\r~\r'),
 ('retry','planet-takeall','\r~~~~~\r~L;N\r~~@First Name\r~~@N\r~~@Second Name\r~~@\r~~@L;Q;Y\r~\r~\r'),
 ('reserved','planet-takeall','\r~~~~~\r~L;N\r~~@The Wanderer\r~~@L;Q;Y\r~\r~\r'),
 ('lowercase','planet-takeall','\r~~~~~\r~L;N;the wanderer\r~~@Y\r~~@L;Q;Y\r~\r~\r'),
 ('team','planet-team-bank','\r~~~~~\r~L;N\r~~@New Eden\r~~@Y\r~~@L;Q;Y\r~\r~\r'),
 ('foreign','planet-unguarded-bank','\r~~~~~\r~L;N\r~~@New Eden\r~~@Y\r~~@L;Q;Y\r~\r~\r'),
 ('unowned','planet-takeall','\r~~~~~\r~L;N\r~~@New Eden\r~~@Y\r~~@L;Q;Y\r~\r~\r'),
 ('long','planet-takeall','\r~~~~~\r~L;N\r~~@12345678901234567890123456789012345678901234567890\r~~@Y\r~~@L;Q;Y\r~\r~\r'),
]
if args.only:scenarios=[row for row in scenarios if row[0] in args.only]
def run(row):
 name,fixture,keys=row;base=root/'analysis/yt-combat/experiments'/fixture;d=out/name;d.mkdir()
 for p in base.iterdir():
  if p.suffix.upper() in ('.DAT','.ASC','.ANS','.DOC','.EXE','.DEF'):shutil.copy2(p,d/p.name)
 shutil.copy2(base/'before.dat',d/'YTDATA.DAT')
 patches=[]
 if name=='unowned':
  sys.path.insert(0,str(root/'analysis/yt-maint'))
  from experiments import put
  data=bytearray((d/'YTDATA.DAT').read_bytes())
  for offset,value in [(73,0),(77,0)]:put(data,4053,offset,value);patches.append({'record':4053,'offset':offset,'value':value})
  (d/'YTDATA.DAT').write_bytes(data)
 if name=='last-slot':
  sys.path.insert(0,str(root/'analysis/yt-maint'))
  from experiments import put
  data=bytearray((d/'YTDATA.DAT').read_bytes())
  data[(4151-1)*137:4151*137]=data[(4053-1)*137:4053*137]
  put(data,151,93,100)
  (d/'YTDATA.DAT').write_bytes(data)
  patches=[{'copy_record':4053,'to_record':4151},{'record':151,'offset':93,'value':100}]
 input_sha256=hashlib.sha256((d/'YTDATA.DAT').read_bytes()).hexdigest()
 for n in ['CAPTURE.COM','DUMP.COM']:shutil.copy2(root/'analysis/art-menus/screen-recovery'/n,d/n)
 (d/'KEYS.TXT').write_bytes(keys.encode())
 with (d/'dosbox.log').open('w') as f:
  subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {d}','-c','c:','-c','date 10/24/2026','-c','time 00:00:00','-c','capture','-c','local TESTER > GAME.LOG','-c','dump','-c','exit'],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=f,stderr=subprocess.STDOUT,timeout=85,check=True)
 (d/'transcript.txt').write_text((d/'GAME.LOG').read_bytes().decode('cp437'))
 (d/'provenance.json').write_text(json.dumps({'after_sha256':hashlib.sha256((d/'YTDATA.DAT').read_bytes()).hexdigest(),'actor':'TESTER','fixture':fixture,'patches':patches,'input_sha256':input_sha256,'keys':keys,'before_sha256':hashlib.sha256((base/'before.dat').read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((d/'YT.EXE').read_bytes()).hexdigest(),'screens_sha256':hashlib.sha256((d/'SCREENS.BIN').read_bytes()).hexdigest(),'game_log_sha256':hashlib.sha256((d/'GAME.LOG').read_bytes()).hexdigest(),'capture_sha256':hashlib.sha256((d/'CAPTURE.COM').read_bytes()).hexdigest(),'dump_sha256':hashlib.sha256((d/'DUMP.COM').read_bytes()).hexdigest()},indent=2))
 print(name,(d/'SCREENS.BIN').stat().st_size//4016,'frames',flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,scenarios))
