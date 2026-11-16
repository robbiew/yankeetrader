"""Export modeled tail phases from retained convergence and Mercenary controls.

No native child, captured RNG state, cache probe or after-world feeds synthesis.
Intermediate phase hashes remain modeled, with full native checks separate.
"""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import verify_maintenance_convergence as convergence
import verify_maintenance_evolved_replay as native
import verify_maintenance_occupied as occupied_evidence
import verify_maintenance_placement as placement
import replay_maintenance_evolved_records as chain
import replay_maintenance_occupied_records as occupied
import replay_maintenance_collision_records as collision
import replay_maintenance_occupied_mercenary as large
import replay_maintenance_collision_mercenary as small
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/evolved_tail.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()

def build():
    convergence.verify();native.verify();occupied_evidence.verify();placement.verify()
    worlds={};pending=[];rows=[];checks=0;witnesses=0
    def wrapper(original):
        def tail(world,stream):
            before=bytes(world);state=stream.rng.state;draws=stream.rng.draws;index=stream.index
            result=original(world,stream)
            worlds[SHA(before)]=PACK(before)
            pending.append(dict(before_sha256=SHA(before),initial_state=state,expected_sha256=SHA(world),
                mercenary=result,_stream=stream,_draws=draws,_index=index))
            return result
        return tail
    def finish(frame,name,npc):
        stream=frame.pop('_stream');index=frame.pop('_index');draws=frame.pop('_draws')
        frame.update(name=name,final_state=stream.rng.state,draws=stream.rng.draws-draws,
            lottery=mbf.enc(npc['lottery']).hex(),candidate=npc['lottery_player']or 0,
            helpers=[dict(family=1 if f=='h1'else 2,caller=c,timer=t.hex())for f,c,t in stream.schedule[index:]],
            seeds=[dict(family=1 if s['family']=='h1'else 2,caller=s['caller'],timer=s['timer'],old_state=s['old_state'],seeded_state=s['seeded_state'])for s in stream.seeds[index:]])
        for activation in frame['mercenary']['activations']:activation['gate']=mbf.enc(activation['gate']).hex()
        rows.append(frame)
    with patch.object(large,'maintain',wrapper(large.maintain)),patch.object(small,'maintain',wrapper(small.maintain)),patch.object(chain,'initial_before',lambda *_:convergence.initial_inputs()):
        report=chain.compare_cases()
        assert len(pending)==9 and all(r['byte_mismatches']==0 for r in report['cases'])
        checks+=len(report['cases']);witnesses+=sum(s['rng_witness_checks']for s in report['statistics'])
        assert sum(s['fields']for s in report['cache_checks'])==1440
        for frame,stats in zip(pending,report['statistics']):finish(frame,'convergence/'+stats['observation']+'/'+stats['day'],stats['npcs'])
        pending.clear()
        for model,case,before in ((occupied,'route-mercenary-100000',occupied_evidence.before_inputs('route-mercenary-100000')),
                                 (collision,'pointer-mercenary-sector',placement.before_inputs('pointer-mercenary-sector'))):
            for mode in ('observed-a','observed-b','observed-c'):
                ob=json.loads(gzip.decompress((model.DEFAULT/case/mode/'host-time.json.gz').read_bytes()))
                actual,stats=model.synthesize(before,model.inputs_from_observation(ob))
                assert len(pending)==1
                witnesses+=collision.validate_rng_witnesses(ob,stats)
                for target in chain.MODES:
                    expected={n:gzip.decompress((model.DEFAULT/case/target/('after-'+n+'.gz')).read_bytes())for n in chain.FILES}
                    assert chain.compare(expected,actual)['byte_mismatches']==0,(case,mode,target)
                    checks+=1
                finish(pending.pop(),case+'/'+mode,stats['npcs'])
    assert len(rows)==15 and checks==90
    sources=('scripts/export_evolved_tail_fixture.py','scripts/replay_maintenance_occupied_mercenary.py',
        'scripts/replay_maintenance_collision_mercenary.py','scripts/replay_maintenance_evolved_records.py',
        'scripts/replay_maintenance_evolved_npcs.py','scripts/replay_maintenance_occupied_records.py',
        'scripts/replay_maintenance_collision_records.py','scripts/verify_maintenance_convergence.py',
        'scripts/verify_maintenance_occupied.py','scripts/verify_maintenance_placement.py',
        'research/yt-maint/convergence-chain-controls/pins.json','research/yt-maint/occupied-route-controls/pins.json',
        'research/yt-maint/placement-cache-controls/pins.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-evolved-tail-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=rows,
        native_six_file_comparisons=checks,native_rng_witnesses=witnesses,native_cache_fields=1440)

def validate(document,expected):
    def normalized(d):
        d=copy.deepcopy(d);d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()};return d
    assert normalized(document)==normalized(expected),'complete modeled tail inputs/outcomes and native qualifications'

def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'modeled tails;',d['native_six_file_comparisons']*6,'native files /',d['native_rng_witnesses'],'RNG witnesses /1440 cache fields')
