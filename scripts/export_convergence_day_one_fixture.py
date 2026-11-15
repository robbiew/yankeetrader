"""Export modeled day-one creation/mobile phases from existing convergence captures."""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import verify_maintenance_convergence as convergence
import verify_maintenance_evolved_replay as native
import replay_maintenance_evolved_records as chain
import replay_maintenance_evolved_planets as planets
import replay_maintenance_occupied_mercenary as tail
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/convergence_day_one.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()

def build():
    convergence.verify();native.verify()
    worlds={};starts=[];phases=[];inputs=[]
    real_planet,real_tail,extract=planets.maintain,tail.maintain,chain.inputs_from_observation
    def source(ob):v=extract(ob);inputs.append(v);return v
    def start(world,stream,clocks):
        result=real_planet(world,stream,clocks)
        starts.append(dict(world=bytes(world),state=stream.rng.state,draws=stream.rng.draws,day=clocks[0][1]))
        return result
    def end(world,stream):
        before=starts[-1];phases.append(None)
        if before['day']==306:
            worlds[SHA(before['world'])]=PACK(before['world'])
            clock=inputs[len(starts)-1].clock
            phases[-1]=dict(before_sha256=SHA(before['world']),initial_state=before['state'],
                wanderer_day=chain.legacy_day(before['world'],clock.wanderer_date),
                xannoron_day=chain.legacy_day(before['world'],clock.xannoron_date),
                base_day=chain.legacy_day(before['world'],clock.base_date),xannoron_timer=clock.xannoron_timer.hex(),
                helpers=[dict(family=1 if f=='h1'else 2,caller=c,timer=t.hex())for f,c,t in stream.schedule[:stream.index]],
                expected_sha256=SHA(world),final_state=stream.rng.state,draws=stream.rng.draws-before['draws'],
                timestamp=world[(4151-1)*137+89:(4151-1)*137+93].hex(),bank=world[(4151-1)*137+117:(4151-1)*137+121].hex(),
                ground=int(mbf.get(world,4151,77)),
                seeds=[dict(family=1 if s['family']=='h1'else 2,caller=s['caller'],timer=s['timer'],old_state=s['old_state'],seeded_state=s['seeded_state'])for s in stream.seeds])
        return real_tail(world,stream)
    with patch.object(planets,'maintain',start),patch.object(tail,'maintain',end),patch.object(chain,'inputs_from_observation',source),patch.object(chain,'initial_before',lambda *_:convergence.initial_inputs()):
        report=chain.compare_cases()
    assert len(phases)==9 and all(r['byte_mismatches']==0 for r in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==501
    assert sum(s['fields']for s in report['cache_checks'])==1440
    rows=[]
    for phase,stats in zip(phases,report['statistics']):
        if phase is None:continue
        n=stats['npcs'];assert n['created']==('wanderer','xannoron','base')
        phase.update(name=stats['observation']+'/'+stats['day'],created=list(n['created']),
            cache=[dict(sector=n['cache_locations'][g],strength=n['cache_forces'][g])for g in range(1,21)],
            groups=[n['groups'][g]for g in range(1,21)],routes=[{k:r[k]for k in ('group','origin','target','fallback','candidate','preferred','candidate_draws','interception_draws','route','strength')}for r in n['routes']],
            wanderer_sector=n['wanderer_sector'],base_sector=n['base_sector'],wanderer_attempts=n['wanderer_attempts'],base_attempts=n['base_attempts'])
        rows.append(phase)
    assert len(rows)==3
    sources=('scripts/export_convergence_day_one_fixture.py','scripts/replay_maintenance_evolved_records.py',
        'scripts/replay_maintenance_evolved_npcs.py','scripts/replay_maintenance_evolved_planets.py',
        'scripts/replay_maintenance_placement.py','scripts/verify_maintenance_convergence.py',
        'scripts/verify_maintenance_evolved_replay.py','research/yt-maint/convergence-chain-controls/pins.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-convergence-day-one-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=rows,
        native_six_file_comparisons=54,native_rng_witnesses=501,native_cache_fields=1440)

def validate(document,expected):
    def normalized(d):
        d=copy.deepcopy(d);d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()};return d
    assert normalized(document)==normalized(expected),'complete modeled day-one phase and native qualifications'

def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 3 modeled day-one phases; 324 native files /501 RNG witnesses /1440 cache fields')
