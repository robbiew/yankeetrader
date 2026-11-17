"""Export occupied home/mobile phases using existing before-only Python replay.

All phase worlds/cache/routes/events and state receipts are calculated. Native
files and witnesses independently verify each completed run after synthesis.
"""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
from replay_qb_graph import mbf
import replay_maintenance_occupied_records as chain
import replay_maintenance_active_planets as planets
import replay_maintenance_occupied_mercenary as tail
import verify_maintenance_occupied as native
import verify_maintenance_occupied_replay as source
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/occupied_routing.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
    native.verify();source.verify();worlds={};starts=[];phases=[];inputs=[]
    real_planet,real_tail,extract=planets.maintain,tail.maintain,chain.inputs_from_observation
    def clocks(ob):v=extract(ob);inputs.append(v);return v
    def start(world,stream,clocks):
        result=real_planet(world,stream,clocks)
        starts.append(dict(world=bytes(world),state=stream.rng.state,draws=stream.rng.draws));return result
    def end(world,stream):
        before=starts[-1];worlds[SHA(before['world'])]=PACK(before['world']);c=inputs[-1].clock
        phases.append(dict(before_sha256=SHA(before['world']),initial_state=before['state'],
            wanderer_day=chain.matrix.legacy_day(before['world'],c.wanderer_date),xannoron_day=chain.matrix.legacy_day(before['world'],c.xannoron_date),base_day=chain.matrix.legacy_day(before['world'],c.base_date),xannoron_timer=c.xannoron_timer.hex(),
            helpers=[dict(family=1 if f=='h1'else 2,caller=site,timer=t.hex())for f,site,t in stream.schedule[:stream.index]],
            expected_sha256=SHA(world),final_state=stream.rng.state,draws=stream.rng.draws-before['draws'],
            birth_ground=int(mbf.get(world,4151,77)),birth_bank=bytes(world[4150*137+117:4150*137+121]).hex(),birth_timestamp=bytes(world[4150*137+89:4150*137+93]).hex(),
            seeds=[dict(family=1 if s['family']=='h1'else 2,caller=s['caller'],timer=s['timer'],old_state=s['old_state'],seeded_state=s['seeded_state'])for s in stream.seeds]))
        return real_tail(world,stream)
    with patch.object(planets,'maintain',start),patch.object(tail,'maintain',end),patch.object(chain,'inputs_from_observation',clocks):report=chain.compare_cases()
    assert len(phases)==len(starts)==len(inputs)==30 and len(report['cases'])==180 and all(c['byte_mismatches']==0 for c in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==1872
    for row,stats in zip(phases,report['statistics']):
        n=stats['npcs'];row.update(name=stats['case']+'/'+stats['observation'],groups=[n['groups'][g]for g in range(1,21)],routes=n['routes'],events=n['events'],wanderer_sector=n['wanderer_sector'],base_sector=n['base_sector'],wanderer_attempts=n['wanderer_attempts'],base_attempts=n['base_attempts'])
    assert sum(len(c['events'])for c in phases)==120
    sources=('scripts/export_occupied_routing_fixture.py','scripts/replay_maintenance_occupied_records.py','scripts/replay_maintenance_active_planets.py','scripts/replay_maintenance_occupied_npcs.py','scripts/replay_maintenance_occupied_mercenary.py','scripts/replay_maintenance_occupied_aux.py','scripts/replay_maintenance_placement.py','scripts/verify_maintenance_occupied.py','scripts/verify_maintenance_occupied_replay.py','research/yt-maint/occupied-route-controls/pins.json','research/yt-maint/occupied-replay-native/rea.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-occupied-routing-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=phases,native_six_file_comparisons=180,native_rng_witnesses=1872)
def validate(document,expected):
    def normalized(d):
        d=copy.deepcopy(d);d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()};return d
    assert normalized(document)==normalized(expected),'complete modeled routing worlds/receipts and native qualification'
def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 30 occupied home/mobile phases /120 combat events; 1080 native files /1872 RNG witnesses')
