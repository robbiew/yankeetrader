"""Export the existing three-day native port controls, without reacquisition.

All three predictions per observer chain precede opening any native target.
Only the modeled port block is carried into the next modeled before-world.
"""
import argparse, base64, copy, gzip, hashlib, json
from pathlib import Path
import verify_maintenance_convergence as convergence
import verify_maintenance_evolved_replay as native
from replay_maintenance_evolved_records import inputs_from_observation, legacy_day
from replay_maintenance_evolved_ports import replay_ports
from replay_qb_graph import mbf

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'internal/qbmaint/testdata/evolved_ports.json'
SHA = lambda b: hashlib.sha256(b).hexdigest()
START, SIZE = 3051*137, 1000*137

def build():
    convergence.verify(); native.verify()
    initial = convergence.initial_inputs()['YTDATA.DAT']
    assert SHA(initial) == '7e470653aabe81d1d3402d8810aca8e2c745e800d0295abcf575d5d7e2a309d3'
    rows = []
    for mode in ('observed-a','observed-b','observed-c'):
        world = initial; predictions = []
        for stage in ('day-1','day-2','day-3'):
            path = convergence.DEFAULT/stage/mode
            observation = json.loads(gzip.decompress((path/'host-time.json.gz').read_bytes()))
            clock = inputs_from_observation(observation).clock
            days = tuple(legacy_day(world, d) for d in clock.port_dates)
            timers = clock.port_timer_minutes
            block, stats = replay_ports(world, days, timers)
            predictions.append((stage, block, dict(name=mode+'/'+stage, days=list(days),
                timer_minutes=[t.hex() for t in timers], expected_sha256=SHA(block),
                class_counts=stats['class_counts'], rate_promotions=stats['rate_promotions'],
                elapsed_min=mbf.enc(stats['elapsed_min']).hex(), elapsed_max=mbf.enc(stats['elapsed_max']).hex())))
            world = world[:START]+block+world[START+SIZE:]
        # The oracle is deliberately unavailable until the complete chain exists.
        for stage, block, row in predictions:
            for target_mode in convergence.MODES:
                observed = gzip.decompress((convergence.DEFAULT/stage/target_mode/'after-YTDATA.DAT.gz').read_bytes())
                assert block == observed[START:START+SIZE], (mode,stage,target_mode,'complete native block')
            rows.append(row)
    sources = ('scripts/export_evolved_port_fixture.py','scripts/replay_maintenance_evolved_ports.py',
        'scripts/replay_maintenance_evolved_records.py','scripts/verify_maintenance_convergence.py',
        'scripts/verify_maintenance_evolved_replay.py','research/yt-maint/convergence-chain-controls/pins.json',
        'archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-evolved-port-replay-v1', sources={n:SHA((ROOT/n).read_bytes()) for n in sources},
        initial_gzip=base64.b64encode(gzip.compress(initial,mtime=0)).decode(), initial_sha256=SHA(initial),
        native_block_comparisons=54, cases=rows)

def validate(document, expected):
    def normalized(d):
        d = copy.deepcopy(d)
        d['initial_gzip'] = base64.b64encode(gzip.decompress(base64.b64decode(d['initial_gzip'],validate=True))).decode()
        return d
    assert normalized(document) == normalized(expected), 'portable inputs and native block oracles'

def check(path=FIXTURE):
    expected = build(); validate(json.loads(Path(path).read_text()),expected); return expected

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check: d=check()
    else: d=build(); FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 9 modeled port blocks against 54 complete native blocks; no native reacquisition')
