"""Capture original DOS startup screens without modifying the preserved archive."""
from pathlib import Path
import shutil,os,subprocess,json,hashlib
from concurrent.futures import ThreadPoolExecutor
import argparse
parser=argparse.ArgumentParser(description="Capture new and returning DOS startup sequences in disposable fixtures.")
parser.add_argument("destination",type=Path)
parser.add_argument("--archive",type=Path,default=Path(__file__).resolve().parents[1]/"archive")
parser.add_argument("--dosbox",default="dosbox-staging")
args=parser.parse_args()
dosbox=shutil.which(args.dosbox)
if not dosbox:parser.error("DOSBox Staging not found; set PATH or pass --dosbox")
root=args.archive.resolve();base=root/'analysis/yt-combat/experiments/team-transfer-current';out=args.destination.resolve();out.mkdir(parents=True,exist_ok=False)
scenarios=[('returning','TESTER','~@\r~~~~~@\r~?~~@\r~~@Q;Y\r~\r~\r'),('new','NEWTRADER','~@\r~~~~~@Pilot\r~~@Y\r~~@N\r~~@\r~~@?\r~~@Q;Y\r~\r~\r')]
def run(row):
 name,actor,keys=row;d=out/name;d.mkdir()
 for p in base.iterdir():
  if p.suffix.upper() in ('.DAT','.ASC','.ANS','.DOC','.EXE','.DEF'):shutil.copy2(p,d/p.name)
 shutil.copy2(base/'before.dat',d/'YTDATA.DAT')
 for n in ['CAPTURE.COM','DUMP.COM']:shutil.copy2(root/'analysis/art-menus/screen-recovery'/n,d/n)
 (d/'KEYS.TXT').write_bytes(keys.encode())
 with (d/'dosbox.log').open('w') as f:
  subprocess.run([dosbox,'--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {d}','-c','c:','-c','date 10/24/2026','-c','time 00:00:00','-c','capture','-c',f'local {actor} > GAME.LOG','-c','dump','-c','exit'],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=f,stderr=subprocess.STDOUT,timeout=85,check=True)
 (d/'transcript.txt').write_text((d/'GAME.LOG').read_bytes().decode('cp437').replace('\\r\\n','\n'))
 (d/'provenance.json').write_text(json.dumps({'actor':actor,'keys':keys,'before_sha256':hashlib.sha256((base/'before.dat').read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((d/'YT.EXE').read_bytes()).hexdigest()},indent=2))
 print(name,'complete', (d/'SCREENS.BIN').stat().st_size//4016)
with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,scenarios))
