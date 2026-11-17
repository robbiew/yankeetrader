"""Export remaining occupied tail and six-file receipts from retained Python runs.

Reuses existing economy/routing/report fixtures for the other phase inputs.
Native outputs and RNG witnesses only audit completed before-only synthesis.
"""
import argparse,hashlib,json
from pathlib import Path
from unittest.mock import patch
import replay_maintenance_occupied_records as chain
import replay_maintenance_occupied_mercenary as tail
import verify_maintenance_occupied as native
import verify_maintenance_occupied_replay as source
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/occupied_records.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def build():
    native.verify();source.verify();rows=[];phases=[];real=chain.synthesize;maintain=tail.maintain
    def phase(world,stream):
        phases.append(dict(before_sha256=SHA(world),initial_state=stream.rng.state,start_draws=stream.rng.draws,
            helpers=[dict(family=1 if f=='h1'else 2,caller=site,timer=t.hex())for f,site,t in stream.schedule[stream.index:]]))
        return maintain(world,stream)
    def synth(before,inputs):
        outputs,stats=real(before,inputs);p=phases[-1];n=stats['npcs'];p['draws']=n['total_draws']-p.pop('start_draws')
        rows.append(dict(initial_before_sha256=SHA(before['YTDATA.DAT']),startup_state=inputs.clock.initial_state,
            final_day=stats['final_day'],tail=p,expected_files={k:SHA(v)for k,v in outputs.items()},
            final_state=n['final_rng_state'],lottery=chain.matrix.graph.mbf.enc(n['lottery']).hex(),candidate=n['lottery_player'] or 0,mercenary=n['mercenary']))
        return outputs,stats
    with patch.object(tail,'maintain',phase),patch.object(chain,'synthesize',synth):report=chain.compare_cases()
    assert len(rows)==30 and len(report['cases'])==180 and all(c['byte_mismatches']==0 for c in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==1872
    for r,s in zip(rows,report['statistics']):r['name']=s['case']+'/'+s['observation']
    sources=('scripts/export_occupied_records_fixture.py','scripts/replay_maintenance_occupied_records.py','scripts/replay_maintenance_occupied_npcs.py','scripts/replay_maintenance_occupied_mercenary.py','scripts/replay_maintenance_occupied_aux.py','scripts/replay_maintenance_active_planets.py','scripts/replay_maintenance_clock_matrix.py','scripts/verify_maintenance_occupied.py','scripts/verify_maintenance_occupied_replay.py','research/yt-maint/occupied-route-controls/pins.json','research/yt-maint/occupied-replay-native/rea.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-occupied-records-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},cases=rows,native_six_file_comparisons=180,native_rng_witnesses=1872)
def validate(d,e):assert d==e,'complete tail clocks/receipts and six-file outputs'
def check():
    e=build();validate(json.loads(FIXTURE.read_text()),e);return e
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:check()
    else:FIXTURE.write_text(json.dumps(build(),indent=2)+'\n')
    print('Verified 30 occupied tail/six-file sets; 1080 native files /1872 RNG witnesses')
