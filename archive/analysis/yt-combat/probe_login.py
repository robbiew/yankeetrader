from pathlib import Path
import shutil,subprocess,os
ROOT=Path(__file__).resolve().parent;d=ROOT/'experiments/login-keyfeed';d.mkdir(parents=True,exist_ok=False)
base=ROOT.parent/'dos-validation/evidence';src=ROOT.parent.parent
for p in base.iterdir():
 if p.suffix.upper() in ('.DAT','.ASC'):shutil.copy2(p,d/p.name)
for n in ['YT.EXE','LOCAL.EXE','BRUN30.EXE','YTINSTR.DOC','YTOPEN.ASC','YTOPEN.ANS']:shutil.copy2(src/n,d/n)
shutil.copy2(ROOT/'KEYFEED.COM',d/'KEYFEED.COM')
(d/'KEYS.TXT').write_bytes(b'\r~~~~\r~~~~Y\r~~~~\r~~~~Q\r~~~~Y\r')
try:
 subprocess.run(['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {d}','-c','c:','-c','keyfeed','-c','local TESTER > game.log','-c','exit'],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=(d/'dosbox.log').open('w'),stderr=subprocess.STDOUT,timeout=35)
 print('completed')
except subprocess.TimeoutExpired:print('timeout; stopped emulator')
print([(p.name,p.stat().st_size) for p in d.iterdir() if p.suffix.upper() in ('.LOG','.DEF')])
