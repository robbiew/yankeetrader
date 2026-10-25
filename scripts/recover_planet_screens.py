"""Capture DOS planet screens in disposable copies of known planet fixtures."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

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
 ('take-cargo','planet-takeall','\r~~~~~\r~L;1\r~~@5\r~~@2\r~~@5\r~~@3\r~~@5\r~~@L;Q;Y\r~\r~\r'),
 ('take-weapons','planet-takeall','\r~~~~~\r~L;4\r~~@5\r~~@5\r~~@5\r~~@6\r~~@5\r~~@9\r~~@5\r~~@L;Q;Y\r~\r~\r'),
 ('menu','planet-takeall','\r~~~~~\r~L\r~~@?\r~~@D\r~~@L;Q;Y\r~\r~\r'),
 ('transfer','planet-transfer-weapons','\r~~~~~\r~L;T\r~~@F\r~~@123\r~~@L;Q;Y\r~\r~\r'),
 ('cargo','planet-transfer-cargo','\r~~~~~\r~L;T;C\r~~@D\r~~@L;Q;Y\r~\r~\r'),
 ('bank','planet-bank-deposit','\r~~~~~\r~L;B\r~~@15000\r~~@L;Q;Y\r~\r~\r'),
 ('invest','planet-invest251','\r~~~~~\r~L;$\r~~@251\r~~@D\r~~@L;Q;Y\r~\r~\r'),
 ('garrison','planet-ground90','\r~~~~~\r~L;F\r~~@90\r~~@L;Q;Y\r~\r~\r'),
 ('takeall','planet-takeall','\r~~~~~\r~L;A\r~~@D\r~~@L;Q;Y\r~\r~\r'),
 ('create','planet-create','\r~~~~~\r~L\r~~@Y\r~~@New Eden\r~~@Y\r~~@Q;Y\r~\r~\r'),
 ('foreign','planet-foreign','\r~~~~~\r~L\r~~@N\r~~@Q;Y\r~\r~\r'),
]
if args.only:scenarios=[row for row in scenarios if row[0] in args.only]
def run(row):
 name,fixture,keys=row;base=root/'analysis/yt-combat/experiments'/fixture;d=out/name;d.mkdir()
 for p in base.iterdir():
  if p.suffix.upper() in ('.DAT','.ASC','.ANS','.DOC','.EXE','.DEF'):shutil.copy2(p,d/p.name)
 shutil.copy2(base/'before.dat',d/'YTDATA.DAT')
 input_sha256=hashlib.sha256((d/'YTDATA.DAT').read_bytes()).hexdigest()
 for n in ['CAPTURE.COM','DUMP.COM']:shutil.copy2(root/'analysis/art-menus/screen-recovery'/n,d/n)
 (d/'KEYS.TXT').write_bytes(keys.encode())
 with (d/'dosbox.log').open('w') as f:
  subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {d}','-c','c:','-c','date 10/24/2026','-c','time 00:00:00','-c','capture','-c','local TESTER > GAME.LOG','-c','dump','-c','exit'],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=f,stderr=subprocess.STDOUT,timeout=85,check=True)
 (d/'transcript.txt').write_text((d/'GAME.LOG').read_bytes().decode('cp437'))
 (d/'provenance.json').write_text(json.dumps({'actor':'TESTER','fixture':fixture,'input_sha256':input_sha256,'keys':keys,'before_sha256':hashlib.sha256((base/'before.dat').read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((d/'YT.EXE').read_bytes()).hexdigest(),'screens_sha256':hashlib.sha256((d/'SCREENS.BIN').read_bytes()).hexdigest(),'game_log_sha256':hashlib.sha256((d/'GAME.LOG').read_bytes()).hexdigest(),'capture_sha256':hashlib.sha256((d/'CAPTURE.COM').read_bytes()).hexdigest(),'dump_sha256':hashlib.sha256((d/'DUMP.COM').read_bytes()).hexdigest()},indent=2))
 print(name,(d/'SCREENS.BIN').stat().st_size//4016,'frames',flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,scenarios))
