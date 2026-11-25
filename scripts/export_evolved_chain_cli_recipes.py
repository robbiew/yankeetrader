"""Adapt existing qualified three-day fixtures to strict research CLI v4 recipes.

Only original files and source clocks enter recipes; comparison oracles remain
separate and are never loaded by qbmaint-replay.
"""
import argparse,base64,gzip,hashlib,json,shutil
from pathlib import Path
import export_occupied_cli_recipes as initial
ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'internal/qbmaint/testdata'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def load(n):return json.loads((FIXTURES/(n+'.json')).read_text())
def build():
 chain=load('evolved_occupied_chain');planets=load('evolved_occupied_planets');mobile=load('evolved_occupied_mobile');tail=load('evolved_occupied_tail')
 phase=lambda d:{r['name']:r for r in d['cases']}
 pi,mi,ti=map(phase,(planets,mobile,tail));parents={r['name']:r for r in initial.build()}
 sources={**chain['sources'],'scripts/export_evolved_chain_cli_recipes.py':SHA(Path(__file__).read_bytes())}
 for n,h in sources.items():assert SHA((ROOT/n).read_bytes())==h,'stale qualified source: '+n
 rows=[]
 for c in chain['cases']:
  before={n:gzip.decompress(base64.b64decode(chain['worlds'][h]))for n,h in c['initial_files'].items()}
  assert all(SHA(before[n])==h for n,h in c['initial_files'].items())
  days=[];oracles=[];case,mode=c['name'].split('/')
  for i,d in enumerate(c['days']):
   days.append(dict(day=d['day'],initial_state=d['startup_state'],ports=dict(days=d['ports']['days'],timer_minutes=d['ports']['timers']),
    planets=[dict(record=r['record'],day=r['day'],timer_minutes=r['timer'])for r in d['planets']],creation=[]if d['creation']is None else[d['creation']],home_helpers=d['home_helpers'],tail_helpers=d['tail_helpers'],aux=d['reports']))
   if i==0:draws=parents[c['name'].replace('/','-')]['oracle']['draws']
   else:
    key=case+'/child-'+str(i)+'/'+mode;draws=pi[key]['draws']+mi[key]['draws']+ti[key]['draws']
    assert ti[key]['final_state']==d['final_state']
   oracles.append(dict(files=d['expected_files'],final_state=d['final_state'],draws=draws))
  recipe=dict(format='qbmaint-replay-v4',profile='evolved-occupied-three-day',name=c['name'].replace('/','-'),before_sha256=c['initial_files'],source_sha256=sources,days=days)
  rows.append(dict(name=recipe['name'],recipe=recipe,before=before,oracles=oracles))
 assert len(rows)==12
 return rows
def export(out):
 rows=build();out=Path(out);out.mkdir()
 try:
  for row in rows:
   folder=out/row['name'];folder.mkdir();before=folder/'before';before.mkdir()
   for n,b in row['before'].items():(before/n).write_bytes(b)
   (folder/'recipe.json').write_text(json.dumps(row['recipe'],indent=2)+'\n')
   (folder/'oracles.json').write_text(json.dumps(row['oracles'],indent=2)+'\n')
 except BaseException:shutil.rmtree(out);raise
 return len(rows)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print('Exported',export(a.out),'existing-fixture v4 chain recipes to',a.out)
