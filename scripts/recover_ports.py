"""Capture DOS Earth and cargo screens in disposable copies of known trade fixtures."""
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
 ('earth','fixture-trade-earth','\r~~~~~\r~P\r~~@3\r~~@1\r~~@0\r~~@Q;Y\r~\r~\r'),
 ('buy','fixture-trade-high','\r~~~~~\r~P\r~~@10\r~~@Y\r~~@Q;Y\r~\r~\r'),
 ('owned','fixture-trade-other','\r~~~~~\r~P\r~~@10\r~~@Y\r~~@Q;Y\r~\r~\r'),
 ('self','fixture-trade-self','\r~~~~~\r~P\r~~@10\r~~@Y\r~~@Q;Y\r~\r~\r'),
 ('decline','fixture-trade-high','\r~~~~~\r~P\r~~@10\r~~@N\r~~@Q;Y\r~\r~\r'),
 ('holds-buy','fixture-trade-earth','\r~~~~~\r~P\r~~@2\r~~@1\r~~@0\r~~@Q;Y\r~\r~\r'),
 ('holds','fixture-trade-earth','\r~~~~~\r~P\r~~@2\r~~@0\r~~@0\r~~@Q;Y\r~\r~\r'),
 ('forces','fixture-trade-earth','\r~~~~~\r~P\r~~@7\r~~@1\r~~@0\r~~@Q;Y\r~\r~\r'),
 ('shields','fixture-trade-earth','\r~~~~~\r~P\r~~@8\r~~@1\r~~@0\r~~@Q;Y\r~\r~\r'),
 ('sell','fixture-trade-sell','\r~~~~~\r~P\r~~@10\r~~@Y\r~~@Q;Y\r~\r~\r'),
]
if args.only:scenarios=[row for row in scenarios if row[0] in args.only]
def run(row):
 name,fixture,keys=row;base=root/'analysis/yt-combat/experiments'/fixture;d=out/name;d.mkdir()
 for p in base.iterdir():
  if p.suffix.upper() in ('.DAT','.ASC','.ANS','.DOC','.EXE','.DEF'):shutil.copy2(p,d/p.name)
 shutil.copy2(base/'before.dat',d/'YTDATA.DAT')
 patches=[]
 if name=='holds-buy':
  sys.path.insert(0,str(root/'analysis/yt-maint'))
  from experiments import put
  data=bytearray((d/'YTDATA.DAT').read_bytes());put(data,2,65,10)
  (d/'YTDATA.DAT').write_bytes(data)
  patches=[{'record':2,'offset':65,'value':10}]
 input_sha256=hashlib.sha256((d/'YTDATA.DAT').read_bytes()).hexdigest()
 for n in ['CAPTURE.COM','DUMP.COM']:shutil.copy2(root/'analysis/art-menus/screen-recovery'/n,d/n)
 (d/'KEYS.TXT').write_bytes(keys.encode())
 with (d/'dosbox.log').open('w') as f:
  subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {d}','-c','c:','-c','date 10/24/2026','-c','time 00:00:00','-c','capture','-c','local TESTER > GAME.LOG','-c','dump','-c','exit'],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=f,stderr=subprocess.STDOUT,timeout=85,check=True)
 (d/'transcript.txt').write_text((d/'GAME.LOG').read_bytes().decode('cp437'))
 (d/'provenance.json').write_text(json.dumps({'actor':'TESTER','fixture':fixture,'patches':patches,'input_sha256':input_sha256,'keys':keys,'before_sha256':hashlib.sha256((base/'before.dat').read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((d/'YT.EXE').read_bytes()).hexdigest(),'screens_sha256':hashlib.sha256((d/'SCREENS.BIN').read_bytes()).hexdigest(),'game_log_sha256':hashlib.sha256((d/'GAME.LOG').read_bytes()).hexdigest(),'capture_sha256':hashlib.sha256((d/'CAPTURE.COM').read_bytes()).hexdigest(),'dump_sha256':hashlib.sha256((d/'DUMP.COM').read_bytes()).hexdigest()},indent=2))
 print(name,(d/'SCREENS.BIN').stat().st_size//4016,'frames',flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,scenarios))
