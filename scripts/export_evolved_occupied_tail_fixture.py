"""Export modeled child tail and reports from retained before-only Python chains."""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import replay_maintenance_evolved_combat_records as chain
import replay_maintenance_evolved_combat_npcs as npcs
import replay_maintenance_evolved_combat_mercenary as mercenary
import replay_maintenance_evolved_combat_aux as auxiliary
import verify_maintenance_evolved_combat as native
from replay_qb_graph import mbf
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/evolved_occupied_tail.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
 native.verify();worlds={};rows=[];pending=[]
 real_merc,real_npc,real_aux=mercenary.maintain,npcs.synthesize,auxiliary.synthesize
 def packed(b):worlds[SHA(b)]=PACK(b);return SHA(b)
 def begin(world,stream):
  row=dict(before_sha256=packed(bytes(world)),initial_state=stream.rng.state,start_draws=stream.rng.draws,start_index=stream.index,stream=stream)
  result=real_merc(world,stream);row['mercenary']=result;row['gates']=[mbf.enc(a['gate']).hex()for a in result['activations']];pending.append(row);return result
 def finish(*args):
  world,stats=real_npc(*args);row=pending.pop();stream=row.pop('stream');draws=row.pop('start_draws');start=row.pop('start_index')
  row.update(expected_sha256=SHA(world),final_state=stream.rng.state,draws=stream.rng.draws-draws,helpers=[dict(family=1 if f=='h1'else 2,caller=site,timer=t.hex())for f,site,t in stream.schedule[start:stream.index]],seeds=stream.seeds,lottery=mbf.enc(stats['lottery']).hex(),candidate=stats['lottery_player']or 0)
  # Only suffix reseeds belong to the exported tail.
  row['seeds']=[dict(family=1 if v['family']=='h1'else 2,caller=v['caller'],timer=v['timer'],old_state=v['old_state'],seeded_state=v['seeded_state'])for v in(row['seeds'][-len(row['helpers']):]if row['helpers']else[])]
  rows.append(row);return world,stats
 def reports(before,world,news_date,news_clock,score_date,score_clock,**kw):
  files,stats=real_aux(before,world,news_date,news_clock,score_date,score_clock,**kw)
  rows[-1].update(report_before={n:packed(b)for n,b in before.items()},report_world=packed(world),report_clock=dict(news_date=news_date.isoformat(),news_clock=news_clock,score_date=score_date.isoformat(),score_clock=score_clock),events=kw['events'],report_sha256={n:SHA(b)for n,b in files.items()},report_stats=stats)
  return files,stats
 with patch.object(mercenary,'maintain',begin),patch.object(chain,'npc_synthesize',finish),patch.object(chain,'aux_synthesize',reports):report=chain.compare_cases()
 assert len(rows)==24 and not pending and len(report['cases'])==144 and all(c['byte_mismatches']==0 for c in report['cases'])
 assert sum(s['rng_witness_checks']for s in report['statistics'])==1242
 for row,stat in zip(rows,report['statistics']):row['name']=stat['case']+'/child-'+str(stat['child'])+'/'+stat['observation']
 sources=('scripts/export_evolved_occupied_tail_fixture.py','scripts/replay_maintenance_evolved_combat_records.py','scripts/replay_maintenance_evolved_combat_npcs.py','scripts/replay_maintenance_evolved_combat_mercenary.py','scripts/replay_maintenance_evolved_combat_aux.py','scripts/replay_maintenance_evolved_combat_planets.py','scripts/verify_maintenance_evolved_combat.py','research/yt-maint/evolved-combat-controls/pins.json','archive/dos-original/YTMAINT.EXE')
 return dict(format='qb-evolved-occupied-tail-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=rows,native_six_file_comparisons=144,native_rng_witnesses=1242)
def validate(d,e):
 def norm(v):
  v=json.loads(json.dumps(v));v['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(b,validate=True))).decode()for k,b in v['worlds'].items()};return v
 assert norm(d)==norm(e),'complete tail/report inputs, outputs and qualification'
def check():
 e=build();validate(json.loads(FIXTURE.read_text()),e);return e
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
 if a.check:d=check()
 else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
 print('Verified 24 modeled tail/report phases; 864 native files /1242 witnesses')
