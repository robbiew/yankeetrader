"""Export original-input recipes and complete three-day modeled chain receipts.

No child snapshot or expected endpoint becomes a synthesis input. Existing
independent native comparison remains separate from model-derived receipts.
"""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import replay_maintenance_evolved_combat_records as chain
import replay_maintenance_occupied_mercenary as first_tail
import replay_maintenance_evolved_combat_mercenary as child_tail
import verify_maintenance_evolved_combat as native
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/evolved_occupied_chain.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
 native.verify();rows=[];worlds={};boundaries=[];real=chain.synthesize_chain
 def bracket(fn):
  def tail(world,stream):
   boundaries.append(dict(index=stream.index,state=stream.rng.state))
   return fn(world,stream)
  return tail
 def synth(before,inputs):
  start=len(boundaries);outputs,stats=real(before,inputs);phases=boundaries[start:];assert len(phases)==3
  originals={n:SHA(b)for n,b in before.items()}
  for n,b in before.items():worlds[SHA(b)]=PACK(b)
  days=[]
  for i,(source,out,stat,phase)in enumerate(zip(inputs,outputs,stats,phases)):
   clock=source.clock
   raw=lambda rows:[dict(family=1 if f=='h1'else 2,caller=c,timer=t.hex())for f,c,t in rows]
   creation=None
   if i==0:
    creation=dict(wanderer_day=chain.legacy_day(before['YTDATA.DAT'],clock.wanderer_date),xannoron_day=chain.legacy_day(before['YTDATA.DAT'],clock.xannoron_date),base_day=chain.legacy_day(before['YTDATA.DAT'],clock.base_date),xannoron_timer=clock.xannoron_timer.hex())
   else:assert clock.wanderer_date is None and clock.xannoron_date is None and clock.base_date is None and clock.xannoron_timer is None
   days.append(dict(day=306+i,startup_state=clock.initial_state,
    ports=dict(days=[chain.legacy_day(before['YTDATA.DAT'],d)for d in clock.port_dates],timers=[t.hex()for t in clock.port_timer_minutes]),
    planets=[dict(record=r,day=d,timer=t.hex())for r,d,t in source.planet_clocks],creation=creation,
    home_helpers=raw(source.schedule[:phase['index']]),tail_helpers=raw(source.schedule[phase['index']:]),
    reports=dict(news_date=clock.news_date.isoformat(),news_clock=clock.news_clock,score_date=clock.score_date.isoformat(),score_clock=clock.score_clock),
    expected_files={n:SHA(b)for n,b in out.items()},routing_final_state=phase['state'],final_state=stat['npcs']['final_rng_state']))
  rows.append(dict(initial_files=originals,days=days));return outputs,stats
 with patch.object(first_tail,'maintain',bracket(first_tail.maintain)),patch.object(child_tail,'maintain',bracket(child_tail.maintain)),patch.object(chain,'synthesize_chain',synth):report=chain.compare_cases()
 assert len(rows)==12 and len(report['cases'])==144 and all(r['byte_mismatches']==0 for r in report['cases'])
 assert sum(s['rng_witness_checks']for s in report['statistics'])==1242
 for row,stat in zip(rows,report['statistics'][::2]):row['name']=stat['case']+'/'+stat['observation']
 sources=('scripts/export_evolved_occupied_chain_fixture.py','scripts/replay_maintenance_evolved_combat_records.py','scripts/replay_maintenance_occupied_records.py','scripts/replay_maintenance_evolved_combat_npcs.py','scripts/replay_maintenance_evolved_combat_planets.py','scripts/replay_maintenance_evolved_combat_mercenary.py','scripts/replay_maintenance_evolved_combat_aux.py','scripts/replay_maintenance_evolved_clock_ports.py','scripts/verify_maintenance_evolved_combat.py','research/yt-maint/evolved-combat-controls/pins.json','archive/dos-original/YTMAINT.EXE')
 return dict(format='qb-evolved-occupied-chain-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=rows,native_six_file_comparisons=144,native_rng_witnesses=1242)
def validate(d,e):
 def norm(v):
  v=json.loads(json.dumps(v));v['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(b,validate=True))).decode()for k,b in v['worlds'].items()};return v
 assert norm(d)==norm(e),'complete original-input chain recipes and owned-day oracles'
def check():
 e=build();validate(json.loads(FIXTURE.read_text()),e);return e
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
 if a.check:d=check()
 else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
 print('Verified 12 modeled three-day chains /36 six-file results; 864 native child files /1242 witnesses')
