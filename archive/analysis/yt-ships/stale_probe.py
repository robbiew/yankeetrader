from pathlib import Path
import shutil,subprocess,os,time,sys
sys.path.insert(0,'analysis/yt-maint')
from experiments import put,get
root=Path('analysis/yt-combat').resolve();d=root/'experiments/ship-stale-position';shutil.copytree(root/'experiments/fixture-ship-kill',d)
b=bytearray((d/'YTDATA.DAT').read_bytes());put(b,3,129,0);put(b,3,93,0);(d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
p=d/'YTNAME.DAT';p.write_bytes(p.read_bytes().rstrip(b'\x1a')+b'Enemy,,Enemy,\r\n\x1a')
shutil.copy2(root/'KEYFEED.COM',d/'KEYFEED.COM')
env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
def start(user,log,keys):
 (d/'KEYS.TXT').write_bytes(keys.replace('|','\r').encode())
 return subprocess.Popen(['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {d}','-c','c:','-c','date 10/24/2026','-c','time 00:00:00','-c','keyfeed','-c',f'local {user} > {log}','-c','exit'],env=env,stdout=(d/(log+'.host')).open('w'),stderr=subprocess.STDOUT)
v=start('Enemy','victim.log','|~~~~~|~~~~~~~~~M;101|~~~~~~~~~~~~I|~~Q;Y|')
time.sleep(15)
(d/'before-attacker.dat').write_bytes((d/'YTDATA.DAT').read_bytes())
a=start('TESTER','attack.log','|~~~~~|~~~~A|~~Y|~1000|~~~~~~Q;Y|')
seen=None;events=[]
for t in range(850):
 time.sleep(.1)
 raw=(d/'YTDATA.DAT').read_bytes();state=[get(raw,3,o) for o in (45,57,61,53,81)]
 if state!=seen:
  (d/f'event-{len(events)}.dat').write_bytes(raw);events.append({'seconds_after_attacker_start':t/10,'death_sector_fighters_shields_credits':state});seen=state
import json
(d/'events.json').write_text(json.dumps(events,indent=2))
for p in (v,a):
 if p.poll() is None:p.terminate()
 p.wait(timeout=5)
print('Two-session probe completed; snapshots saved.')
