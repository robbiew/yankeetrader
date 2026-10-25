from pathlib import Path
import os, shutil, subprocess, json, hashlib, sys
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
variant=sys.argv[1] if len(sys.argv)>1 else 'main'
run=OUT/('run-'+variant)
run.mkdir(exist_ok=True)
source=ROOT/'analysis/yt-combat/experiments/team-transfer-current'
for p in source.iterdir():
 if p.suffix.upper() in ('.DAT','.ASC','.ANS','.DOC','.EXE','.DEF'):shutil.copy2(p,run/p.name)
if variant=='config': shutil.copy2(ROOT/'YTCONFIG.EXE',run/'YTCONFIG.EXE')
# Reuse the known fixture's pre-session data.
shutil.copy2(source/'before.dat',run/'YTDATA.DAT')
for n in ['CAPTURE.COM','DUMP.COM']:shutil.copy2(OUT/n,run/n)
keys='~@\r~~~~~@\r~~@?\r~~@C\r~~@1\r~T\r~~@1\r~L\r~~@?\r~~@L\r~Q;Y\r~\r~\r'
if variant=='computer': keys='\r~~~~~\r~C\r~?\r~~@1\r~Q;Y\r~\r~\r'
if variant=='config': keys='~~@X\r'
(run/'KEYS.TXT').write_bytes(keys.encode())
args=['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {run}','-c','c:','-c','date 10/24/2026','-c','time 00:00:00','-c','capture','-c',('ytconfig > GAME.LOG' if variant=='config' else 'local TESTER > GAME.LOG'),'-c','dump','-c','exit']
with (run/'dosbox.log').open('w') as f:
 subprocess.run(args,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=f,stderr=subprocess.STDOUT,timeout=90)
p=run/'SCREENS.BIN'
print('Captured',p.stat().st_size//4016,'frames;',p.stat().st_size,'bytes')
(run/'provenance.json').write_text(json.dumps({'fixture':str(source.relative_to(ROOT)),'initial_data_sha256':hashlib.sha256((source/'before.dat').read_bytes()).hexdigest(),'game_sha256':hashlib.sha256((ROOT/'YT.EXE').read_bytes()).hexdigest(),'keys':keys,'executed_binary':('YTCONFIG.EXE' if variant=='config' else 'YT.EXE'),'executed_binary_sha256':hashlib.sha256((run/('YTCONFIG.EXE' if variant=='config' else 'YT.EXE')).read_bytes()).hexdigest(),'frame_size':4016,'format':'16-byte BIOS metadata followed by 2000 character/attribute pairs from active B800 text page'},indent=2)+'\n')
