"""Export existing-home/mobile phase fixtures from native-qualified Python chains.

All phase worlds/states are modeled. Original helper TIMER inputs carry source
caller labels; no captured RNG/cache endpoint or native child seeds synthesis.
"""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import verify_maintenance_convergence as convergence
import verify_maintenance_evolved_replay as native
import replay_maintenance_evolved_records as chain
import replay_maintenance_evolved_planets as planets
import replay_maintenance_occupied_mercenary as mercenary
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/evolved_continuation.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()

def build():
    convergence.verify();native.verify()
    real_planet,real_tail=planets.maintain,mercenary.maintain
    worlds={};phases=[];starts=[]
    def start(world,stream,clocks):
        result=real_planet(world,stream,clocks)
        starts.append(dict(world=bytes(world),state=stream.rng.state,draws=stream.rng.draws,day=clocks[0][1]))
        return result
    def end(world,stream):
        before=starts[-1];phases.append(None)
        if before['day']>306:
            worlds[SHA(before['world'])]=PACK(before['world'])
            phases[-1]=dict(before_sha256=SHA(before['world']),initial_state=before['state'],
                helpers=[dict(family=1 if family=='h1'else 2,caller=caller,timer=timer.hex())for family,caller,timer in stream.schedule[:stream.index]],
                expected_sha256=SHA(world),final_state=stream.rng.state,draws=stream.rng.draws-before['draws'],
                xannoron_increment=int(mbf.get(world,4151,77)-mbf.get(before['world'],4151,77)),
                seeds=[dict(family=1 if s['family']=='h1'else 2,caller=s['caller'],timer=s['timer'],old_state=s['old_state'],seeded_state=s['seeded_state'])for s in stream.seeds])
        return real_tail(world,stream)
    # Model initial input independently. All child handoffs remain modeled.
    with patch.object(planets,'maintain',start),patch.object(mercenary,'maintain',end),patch.object(chain,'initial_before',lambda *_:convergence.initial_inputs()):
        report=chain.compare_cases()
    assert len(report['cases'])==54 and all(r['byte_mismatches']==0 for r in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==501
    assert sum(s['fields']for s in report['cache_checks'])==1440
    assert len(phases)==9 and len(starts)==9
    rows=[]
    for phase,row in zip(phases,report['statistics']):
        if phase is None:continue
        n=row['npcs'];groups=lambda values:[dict(sector=values[g]['sector'],strength=values[g]['strength'])for g in range(1,21)]
        phase.update(name=row['observation']+'/'+row['day'],groups=groups(n['groups']),
            cache=[dict(sector=n['cache_locations'][g],strength=n['cache_forces'][g])for g in range(1,21)],
            wanderer_sector=n['wanderer_sector'],base_sector=n['base_sector'],wanderer_attempts=n['wanderer_attempts'],
            routes=[{k:r[k]for k in ('group','origin','target','fallback','candidate','preferred','candidate_draws','interception_draws','route','strength')}for r in n['routes']],
            allocations=sum(h['family']==2 for h in phase['helpers']))
        assert n['created']==()and n['base_attempts']==[],'only existing-home skip path; no creation clocks'
        rows.append(phase)
    assert len(rows)==6
    sources=('scripts/export_evolved_continuation_fixture.py','scripts/replay_maintenance_evolved_npcs.py',
        'scripts/replay_maintenance_evolved_records.py','scripts/replay_maintenance_evolved_planets.py',
        'scripts/replay_maintenance_placement.py','scripts/replay_maintenance_collision_npcs.py',
        'scripts/replay_maintenance_occupied_mercenary.py','scripts/verify_maintenance_convergence.py',
        'scripts/verify_maintenance_evolved_replay.py','research/yt-maint/convergence-chain-controls/pins.json',
        'archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-evolved-continuation-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=rows,
        native_six_file_comparisons=54,native_rng_witnesses=501,native_cache_fields=1440)

def validate(document,expected):
    def normalized(d):
        d=copy.deepcopy(d);d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()};return d
    assert normalized(document)==normalized(expected),'complete modeled continuation phases and native-qualified metadata'

def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 6 modeled continuation phases; 324 native files /501 RNG witnesses /1440 cache fields')
