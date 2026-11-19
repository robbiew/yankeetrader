"""Export occupied home/mobile phases using existing before-only Python replay.

All phase worlds/cache/routes/events and state receipts are calculated. Native
files and witnesses independently verify each completed run after synthesis.
"""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
from replay_qb_graph import mbf
from replay_maintenance_placement import cache
import replay_maintenance_evolved_combat_records as chain
import replay_maintenance_evolved_combat_planets as planets
import replay_maintenance_evolved_combat_mercenary as tail
import verify_maintenance_evolved_combat as native
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/evolved_occupied_mobile.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
    native.verify();worlds={};starts=[];phases=[];inputs=[]
    real_planet,real_tail,extract=planets.maintain,tail.maintain,chain.inputs_from_observation
    def clocks(ob):v=extract(ob);inputs.append(v);return v
    def start(world,stream,clocks):
        result=real_planet(world,stream,clocks)
        starts.append(dict(world=bytes(world),state=stream.rng.state,draws=stream.rng.draws,index=stream.index));return result
    def end(world,stream):
        before=starts[-1];normalized=cache(before['world']);worlds[SHA(before['world'])]=PACK(before['world'])
        phases.append(dict(before_sha256=SHA(before['world']),initial_state=before['state'],
            helpers=[dict(family=1 if f=='h1'else 2,caller=site,timer=t.hex())for f,site,t in stream.schedule[before['index']:stream.index]],
            expected_sha256=SHA(world),final_state=stream.rng.state,draws=stream.rng.draws-before['draws'],
            cache=[dict(sector=normalized['locations'][g],strength=normalized['forces'][g])for g in range(1,21)],
            cleared_sectors=list(normalized['cleared_sectors']),normalized_total=normalized['total'],
            xannoron_increment=int(mbf.get(world,4151,77)-mbf.get(before['world'],4151,77)),
            allocations=sum(f=='h2'and site==0x31a3 for f,site,t in stream.schedule[before['index']:stream.index]),
            seeds=[dict(family=1 if s['family']=='h1'else 2,caller=s['caller'],timer=s['timer'],old_state=s['old_state'],seeded_state=s['seeded_state'])for s in stream.seeds]))
        return real_tail(world,stream)
    with patch.object(planets,'maintain',start),patch.object(tail,'maintain',end),patch.object(chain,'inputs_from_observation',clocks):report=chain.compare_cases()
    assert len(phases)==len(starts)==24 and len(inputs)==36 and len(report['cases'])==144 and all(c['byte_mismatches']==0 for c in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==1242
    for row,stats in zip(phases,report['statistics']):
        n=stats['npcs'];row.update(name=stats['case']+'/child-'+str(stats['child'])+'/'+stats['observation'],groups=[n['groups'][g]for g in range(1,21)],routes=n['routes'],events=n['events'],wanderer_sector=n['wanderer_sector'],base_sector=n['base_sector'],wanderer_attempts=n['wanderer_attempts'],base_attempts=n['base_attempts'])
    sources=('scripts/export_evolved_occupied_mobile_fixture.py','scripts/replay_maintenance_evolved_combat_records.py','scripts/replay_maintenance_evolved_combat_planets.py','scripts/replay_maintenance_evolved_combat_npcs.py','scripts/replay_maintenance_evolved_combat_mercenary.py','scripts/replay_maintenance_evolved_combat_aux.py','scripts/replay_maintenance_placement.py','scripts/replay_maintenance_occupied_records.py','scripts/verify_maintenance_evolved_combat.py','research/yt-maint/evolved-combat-controls/pins.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-evolved-occupied-mobile-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=phases,native_six_file_comparisons=144,native_rng_witnesses=1242)
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
    print('Verified',len(d['cases']),'modeled home/mobile child phases; 864 native files /1242 witnesses')
