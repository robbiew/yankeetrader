"""Export ordinary occupied-world economy phases from existing qualified replay.

Phase worlds and RNG receipts are modeled. Native six-file targets and RNG
witnesses validate completed synthesis separately and never correct its inputs.
"""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import replay_maintenance_occupied_records as chain
import replay_maintenance_active_planets as planets
import verify_maintenance_occupied as native
import verify_maintenance_occupied_replay as source
from replay_qb_graph import mbf
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/occupied_planets.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
    native.verify();source.verify()
    worlds={};rows=[];real=planets.maintain;extract=chain.inputs_from_observation;load=chain.before_inputs
    current={}
    def initial(case,*args):
        result=load(case,*args);current['initial']=bytes(result['YTDATA.DAT']);return result
    def inputs(ob):
        result=extract(ob);current['inputs']=result;return result
    def phase(world,stream,clocks):
        before=bytes(world);state=stream.rng.state;stats=real(world,stream,clocks);v=current['inputs']
        for b in (current['initial'],before):worlds[SHA(b)]=PACK(b)
        rows.append(dict(initial_before_sha256=SHA(current['initial']),before_sha256=SHA(before),initial_state=state,
            ports=dict(days=[chain.matrix.legacy_day(current['initial'],d)for d in v.clock.port_dates],timer_minutes=[b.hex()for b in v.clock.port_timer_minutes]),
            clocks=[dict(record=r,day=d,timer_minutes=b.hex())for r,d,b in clocks],expected_sha256=SHA(world),final_state=stats['final_rng_state'],draws=stats['rng_draws'],
            rows=[dict(record=r['record'],day=r['day'],elapsed=mbf.enc(r['elapsed']).hex(),event_draws=[mbf.enc(b).hex()for b in r['event_draws']],ground=r['ground'],cargo_rates=[mbf.enc(b).hex()for b in r['cargo_rates']])for r in stats['rows']]))
        return stats
    with patch.object(chain,'before_inputs',initial),patch.object(chain,'inputs_from_observation',inputs),patch.object(planets,'maintain',phase):report=chain.compare_cases()
    assert len(rows)==30 and len(report['cases'])==180 and all(c['byte_mismatches']==0 for c in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==1872
    assert sum(len(r['rows'])for r in rows)==24
    for row,s in zip(rows,report['statistics']):row['name']=s['case']+'/'+s['observation']
    sources=('scripts/export_occupied_planet_fixture.py','scripts/replay_maintenance_occupied_records.py','scripts/replay_maintenance_active_planets.py','scripts/replay_maintenance_occupied_npcs.py','scripts/replay_maintenance_occupied_aux.py','scripts/replay_maintenance_occupied_mercenary.py','scripts/verify_maintenance_occupied.py','scripts/verify_maintenance_occupied_replay.py','research/yt-maint/occupied-route-controls/pins.json','research/yt-maint/occupied-replay-native/rea.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-occupied-planets-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=rows,native_six_file_comparisons=180,native_rng_witnesses=1872)
def validate(document,expected):
    def normalize(d):
        d=copy.deepcopy(d);d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()};return d
    assert normalize(document)==normalize(expected),'complete occupied economy phase inputs/receipts and native qualification'
def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:check()
    else:FIXTURE.write_text(json.dumps(build(),indent=2)+'\n')
    print('Verified 30 occupied planet phases /24 updates; 1080 native files /1872 RNG witnesses')
