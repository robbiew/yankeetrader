"""Reuse occupied-world captures/Python strong neutral-planet ground rules.

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
FIXTURE=ROOT/'internal/qbmaint/testdata/neutral_ground.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
    native.verify();source.verify();worlds={};events=[];real=combat.ground_assault
    def record(world,stream,group,sector,force,run):
        before=bytes(world);state=stream.rng.state;event=run(world,stream,group,sector,force)
        worlds[SHA(before)]=PACK(before)
        return dict(before_sha256=SHA(before),group=group,sector=sector,force=force,initial_state=state,expected_sha256=SHA(world),event=event)
    def phase(world,stream,group,sector,force):
        row=record(world,stream,group,sector,force,real);events.append(row);return row['event']
    with patch.object(combat,'ground_assault',phase):report=chain.compare_cases()
    assert len(report['cases'])==180 and all(c['byte_mismatches']==0 for c in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==1872
    index=0
    for row in report['statistics']:
        selected=[v for v in row['npcs']['events']if v['kind']=='planet']
        for event in selected:
            assert events[index]['event']==event
            events[index]['name']=row['case']+'/'+row['observation']+'/group-'+str(event['group']);index+=1
    assert index==len(events)==57
    # Real LCG inverse seeds select zero, exact half and maximum fractions.
    modulus=1<<24;inverse=pow(214013,-1,modulus)
    seeds=[0,(-1744579)*inverse%modulus,((1<<23)-1744579)*inverse%modulus,((1<<24)-1-1744579)*inverse%modulus]
    assert QB3(seeds[1]).rnd()==0 and QB3(seeds[2]).rnd()==.5 and QB3(seeds[3]).rnd()==(modulus-1)/modulus
    synthetic=[]
    for force in (1,500,10000):
        for ground in (500001,500001.5,505000):
            for state in seeds:
                world=bytearray(4151*137)
                for off,v in ((53,51),(57,3051),(61,4051),(93,4151)):mbf.put(world,1,off,v)
                at=4052*137;world[at:at+41]=b'Route Haven'.ljust(41,b' ')
                for rec,off,v in ((905,93,2),(4053,85,11),(4053,73,0),(4053,77,ground),(4053,45,1010),(4053,57,1000)):
                    mbf.put(world,rec,off,v)
                row=record(world,SimpleNamespace(rng=QB3(state)),2,854,force,real)
                row['name']=f'synthetic/{force}-{ground}/{state:06x}';synthetic.append(row)
    sources=('scripts/export_neutral_ground_fixture.py','scripts/replay_maintenance_occupied_records.py','scripts/replay_maintenance_occupied_npcs.py','scripts/replay_maintenance_occupied_aux.py','scripts/replay_maintenance_occupied_mercenary.py','scripts/replay_qb_graph.py','scripts/verify_maintenance_occupied.py','scripts/verify_maintenance_occupied_replay.py','research/yt-maint/occupied-route-controls/pins.json','research/yt-maint/occupied-replay-native/rea.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-neutral-ground-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=events,synthetic=synthetic,native_six_file_comparisons=180,native_rng_witnesses=1872)
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
    print('Verified',len(d['cases']),'modeled ground encounters /',len(d['synthetic']),'synthetic boundaries; 1080 native files /1872 RNG witnesses')
