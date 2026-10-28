"""Create and run controlled DOS cases only in a prepared disposable recovery.
Usage: python3 run_cases.py /tmp/yt-production-recovery
The original archive and retained result directory are never mounted by DOSBox.
"""
from pathlib import Path
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys

recovery=Path(sys.argv[1]).resolve()
archive=Path(__file__).resolve().parents[3]/'archive'
if recovery.is_relative_to(archive):raise SystemExit('Refusing to write inside the immutable archive')
assert (recovery/'analysis/yt-combat/run_clock_session.py').is_file()
sys.path.insert(0,str(recovery/'analysis/yt-maint'))
from experiments import put
root=recovery/'analysis/yt-combat/experiments'
specs=[
 ('partial-cap',[100000]*3,[1000000]*3),
 ('partial-clamp',[1,100000,1],[10,1000000,10]),
 ('destroy',[1]*3,[10]*3),
 ('destroy-bank',[1]*3,[10]*3,12345),
 ('ore-only',[100000,0,0],[0]*3),
 ('organics-only',[0,100000,0],[0]*3),
 ('equipment-only',[0,0,100000],[0]*3),
 ('ore-trigger',[100000,1,0],[0]*3),
 ('zero-production',[0]*3,[0]*3),
 ('ore-stock-derived',[0]*3,[1000000,0,0]),
]
for spec in specs:
 name,rates,stocks=spec[:3]
 bank=spec[3] if len(spec)>3 else 0
 d=root/('fixture-production-'+name)
 shutil.copytree(root/'fixture-missile-production',d)
 b=bytearray((d/'YTDATA.DAT').read_bytes())
 for off,val in zip((45,49,53),rates):put(b,4052,off,val)
 for off,val in zip((57,61,65),stocks):put(b,4052,off,val)
 for off,val in {41:297,89:0,77:0,117:bank,69:111,113:222,125:333,129:444}.items():put(b,4052,off,val)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)

def run(spec):
 name=spec[0]
 command=[sys.executable,str(recovery/'analysis/yt-combat/run_clock_session.py'),'production-'+name,'fixture-production-'+name,'|~~~~~|~!;101;20|~~~~~~Q;Y|~~~~~|','60']
 result=subprocess.run(command,cwd=recovery,capture_output=True,text=True,env={**os.environ,'YT_DOS_DATE':'10/24/2026','YT_DOS_TIME':'00:00:00'},timeout=70)
 log=root/('production-'+name)
 (log/'runner.txt').write_text(result.stdout+result.stderr)
 normal=b'Returning to Yankee Trader Local Logon Program' in (log/'GAME.LOG').read_bytes()
 print(name,result.returncode,'normal-return=',normal,flush=True)
 return result.returncode if normal and result.stdout.startswith('completed') else 1
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 assert all(code==0 for code in pool.map(run,specs))
(recovery/'production-cases.json').write_text(json.dumps(specs,indent=2)+'\n')
