"""Export modeled planet-phase inputs from existing native-qualified chains.

Phase worlds and RNG states come only from Python synthesis. Complete native
six-file oracles are opened after each three-day prediction, never by the phase.
"""
import argparse, base64, copy, gzip, hashlib, json
from pathlib import Path
from unittest.mock import patch
import verify_maintenance_evolved_combat as native
import replay_maintenance_evolved_combat_records as chain
import replay_maintenance_evolved_combat_planets as planets
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/evolved_occupied_planets.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()

def build():
    native.verify();worlds={};rows=[];original=planets.maintain
    def phase(world,stream,clocks):
        before=bytes(world);state=stream.rng.state
        stats=original(world,stream,clocks);worlds[SHA(before)]=PACK(before)
        rows.append(dict(before_sha256=SHA(before),initial_state=state,
            clocks=[dict(record=r,day=d,timer_minutes=t.hex())for r,d,t in clocks],
            expected_sha256=SHA(world),final_state=stats['final_rng_state'],draws=stats['rng_draws'],
            rows=[dict(record=r['record'],day=r['day'],elapsed=mbf.enc(r['elapsed']).hex(),
                event_draws=[mbf.enc(v).hex()for v in r['event_draws']],ground=r['ground'],
                cargo_rates=[mbf.enc(v).hex()for v in r['cargo_rates']])for r in stats['rows']]))
        return stats
    with patch.object(planets,'maintain',phase):report=chain.compare_cases()
    assert len(rows)==24 and len(report['cases'])==144 and all(c['byte_mismatches']==0 for c in report['cases'])
    witnesses=sum(c['rng_witness_checks']for c in report['statistics']);assert witnesses==1242
    for row,stat in zip(rows,report['statistics']):row['name']=stat['case']+'/child-'+str(stat['child'])+'/'+stat['observation']
    sources=('scripts/export_evolved_occupied_planet_fixture.py','scripts/replay_maintenance_evolved_combat_planets.py',
        'scripts/replay_maintenance_evolved_combat_records.py','scripts/replay_maintenance_evolved_clock_ports.py',
        'scripts/replay_maintenance_evolved_combat_npcs.py','scripts/replay_maintenance_evolved_combat_aux.py',
        'scripts/replay_maintenance_occupied_records.py','scripts/replay_maintenance_collision_npcs.py',
        'scripts/replay_maintenance_collision_records.py','scripts/verify_maintenance_evolved_combat.py',
        'research/yt-maint/evolved-combat-controls/pins.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-evolved-occupied-planet-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=rows,native_six_file_comparisons=144,native_rng_witnesses=witnesses)

def validate(document,expected):
    def normalized(d):
        d=copy.deepcopy(d)
        d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()}
        return d
    assert normalized(document)==normalized(expected),'complete modeled phase inputs/outcomes backed by native chains'

def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 24 modeled occupied child planet phases; 144 native six-file comparisons and 1242 child witnesses')
