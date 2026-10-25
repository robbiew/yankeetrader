from pathlib import Path
import shutil,subprocess,os,sys
ROOT=Path(__file__).resolve().parent
name=sys.argv[1];source=ROOT/'experiments'/sys.argv[2];d=ROOT/'experiments'/name
d.mkdir(exist_ok=False)
for p in source.iterdir():
 if p.suffix.upper() in ('.DAT','.ASC','.ANS','.DOC','.EXE','.DEF'):shutil.copy2(p,d/p.name)
shutil.copy2(ROOT/'KEYFEED.COM',d/'KEYFEED.COM')
(d/'KEYS.TXT').write_bytes(sys.argv[3].replace('|','\r').encode())
try:
 subprocess.run(['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {d}','-c','c:','-c','keyfeed','-c','local TESTER > game.log','-c','exit'],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=(d/'dosbox.log').open('w'),stderr=subprocess.STDOUT,timeout=int(sys.argv[4]) if len(sys.argv)>4 else 40)
 print('completed')
except subprocess.TimeoutExpired:print('timeout; stopped emulator')
print((d/'GAME.LOG').read_text(errors='replace').replace('\\r\\n','\n'))
