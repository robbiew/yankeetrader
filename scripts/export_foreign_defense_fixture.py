"""Reuse occupied-world captures/Python defense rules for bounded Go combat.

Encounter phase worlds and states are modeled, not new native observations.
Full native files and RNG witnesses independently qualify the completed runs.
"""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import replay_maintenance_occupied_records as chain
import replay_maintenance_occupied_npcs as combat
import verify_maintenance_occupied as native
import verify_maintenance_occupied_replay as source
from replay_qb_graph import mbf,QB3
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/foreign_defense.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
    native.verify();source.verify();worlds={};events=[];real=combat.defense
    def record(world,stream,group,sector,force,run):
        before=bytes(world);state=stream.rng.state;event=run(world,stream,group,sector,force)
        worlds[SHA(before)]=PACK(before)
        return dict(before_sha256=SHA(before),group=group,sector=sector,force=force,initial_state=state,expected_sha256=SHA(world),event=event)
    def phase(world,stream,group,sector,force):
        row=record(world,stream,group,sector,force,real);events.append(row);return row['event']
    with patch.object(combat,'defense',phase):report=chain.compare_cases()
    assert len(report['cases'])==180 and all(c['byte_mismatches']==0 for c in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==1872
    index=0
    for row in report['statistics']:
        selected=[v for v in row['npcs']['events']if v['kind']=='defense']
        for event in selected:
            assert events[index]['event']==event
            events[index]['name']=row['case']+'/'+row['observation']+'/group-'+str(event['group']);index+=1
    assert index==len(events)==63
    # Synthetic controls use the same Python rule and real LCG. The inverse seed
    # selects exact .5 and adjacent 24-bit fractions without injecting draws.
    modulus=1<<24;inverse=pow(214013,-1,modulus)
    seeds=[0,((1<<23)-1744579)*inverse%modulus,((1<<23)+1-1744579)*inverse%modulus]
    # QB3's constants are authenticated separately; check the computed gate seed.
    assert QB3(seeds[1]).rnd()==.5 and QB3(seeds[2]).rnd()>.5
    synthetic=[]
    for force,defenders in ((499,499),(500,500),(501,501),(5000,5000),(5001,5001),(6000,5000),(6000,5001),(5001,100000)):
        for state in seeds:
            world=bytearray(4151*137)
            for off,v in ((53,51),(57,3051),(61,4051),(93,4151)):mbf.put(world,1,off,v)
            mbf.put(world,905,81,defenders);mbf.put(world,905,85,-2)
            row=record(world,SimpleNamespace(rng=QB3(state)),2,854,force,real)
            row['name']=f'synthetic/{force}-{defenders}/{state:06x}';synthetic.append(row)
    sources=('scripts/export_foreign_defense_fixture.py','scripts/replay_maintenance_occupied_records.py','scripts/replay_maintenance_occupied_npcs.py','scripts/replay_maintenance_occupied_aux.py','scripts/replay_maintenance_occupied_mercenary.py','scripts/replay_qb_graph.py','scripts/verify_maintenance_occupied.py','scripts/verify_maintenance_occupied_replay.py','research/yt-maint/occupied-route-controls/pins.json','research/yt-maint/occupied-replay-native/rea.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-foreign-defense-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=events,synthetic=synthetic,native_six_file_comparisons=180,native_rng_witnesses=1872)
def validate(document,expected):
    def normalize(d):
        d=copy.deepcopy(d);d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()};return d
    assert normalize(document)==normalize(expected),'complete modeled combat inputs/receipts and native qualification'
def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'modeled defense encounters /',len(d['synthetic']),'synthetic boundaries; 1080 native files /1872 RNG witnesses')
