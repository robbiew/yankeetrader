"""Export modeled planet-phase inputs from existing native-qualified chains.

Phase worlds and RNG states come only from Python synthesis. Complete native
six-file oracles are opened after each three-day prediction, never by the phase.
"""
import argparse, base64, copy, gzip, hashlib, json
from pathlib import Path
from unittest.mock import patch
import verify_maintenance_convergence as convergence
import verify_maintenance_evolved_replay as native
import replay_maintenance_evolved_records as chain
import replay_maintenance_evolved_planets as planets
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/evolved_planets.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()

def build():
    convergence.verify();native.verify()
    initial=convergence.initial_inputs();worlds={};rows=[];comparisons=0;witnesses=0
    original=planets.maintain
    for mode in ('observed-a','observed-b','observed-c'):
        observations=tuple(json.loads(gzip.decompress((convergence.DEFAULT/f'day-{day}'/mode/'host-time.json.gz').read_bytes()))for day in (1,2,3))
        inputs=tuple(chain.inputs_from_observation(ob)for ob in observations)
        pending=[]
        def phase(world,stream,clocks):
            before=bytes(world);state=stream.rng.state
            stats=original(world,stream,clocks)
            worlds[SHA(before)]=PACK(before)
            pending.append(dict(name=mode+'/day-'+str(len(pending)+1),before_sha256=SHA(before),initial_state=state,
                clocks=[dict(record=r,day=d,timer_minutes=t.hex())for r,d,t in clocks],
                expected_sha256=SHA(world),final_state=stats['final_rng_state'],draws=stats['rng_draws'],
                rows=[dict(record=r['record'],day=r['day'],elapsed=mbf.enc(r['elapsed']).hex(),
                    event_draws=[mbf.enc(v).hex()for v in r['event_draws']],ground=r['ground'],
                    cargo_rates=[mbf.enc(v).hex()for v in r['cargo_rates']])for r in stats['rows']]))
            return stats
        with patch.object(planets,'maintain',phase):
            outputs,statistics=chain.synthesize_chain(initial,inputs)
        assert len(pending)==3
        # No native child or oracle was supplied to synthesis or instrumentation.
        for day,(actual,stats,ob) in enumerate(zip(outputs,statistics,observations),1):
            witnesses+=chain.validate_rng_witnesses(ob,stats)
            for target in chain.MODES:
                expected={n:gzip.decompress((convergence.DEFAULT/f'day-{day}'/target/('after-'+n+'.gz')).read_bytes())for n in chain.FILES}
                result=chain.compare(expected,actual)
                assert result['byte_mismatches']==0, (mode,day,target,result)
                comparisons+=1
        rows.extend(pending)
    assert len(rows)==9 and comparisons==54 and witnesses==501
    sources=('scripts/export_evolved_planet_fixture.py','scripts/replay_maintenance_evolved_planets.py',
        'scripts/replay_maintenance_evolved_records.py','scripts/replay_maintenance_evolved_ports.py',
        'scripts/replay_maintenance_evolved_npcs.py','scripts/replay_maintenance_evolved_aux.py',
        'scripts/replay_maintenance_collision_npcs.py','scripts/replay_maintenance_collision_records.py',
        'scripts/verify_maintenance_convergence.py','scripts/verify_maintenance_evolved_replay.py',
        'research/yt-maint/convergence-chain-controls/pins.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-evolved-planet-replay-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},
        worlds=worlds,cases=rows,native_six_file_comparisons=comparisons,native_rng_witnesses=witnesses)

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
    print('Verified 9 modeled planet phases /27 planets; 54 native six-file chains and 501 RNG witnesses')
