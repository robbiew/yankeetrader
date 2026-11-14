"""Reuse late-clock captures for a bounded, independently modeled encounter chain."""
import argparse,base64,gzip,json
from pathlib import Path
from unittest.mock import patch
import export_clean_port_fixture as parent
import replay_maintenance_clock_matrix as matrix
import replay_maintenance_wanderer as encounter
FIXTURE=parent.ROOT/'internal/qbmaint/testdata/wanderer_assault.json'
def build():
    d=parent.build();rows=[];worlds={};source=parent.ROOT/'research/yt-maint/initial-controls/baseline-split'
    before={n:gzip.decompress((source/('before-'+n+'.gz')).read_bytes())for n in matrix.FILES[:3]}
    original=encounter.assault
    for mode in('observed-a','observed-b','observed-c'):
        folder=matrix.DEFAULT/'late'/mode;ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));p=matrix.inputs_from_observation(ob)
        events=[];previous=None;first=None
        def capture(world,stream,group,sector,force,wanderer_sector):
            nonlocal previous,first
            prefix=bytes(world)
            if first is None:first=prefix
            if previous is not None:assert prefix==previous,'only Wanderer fields change between encounter calls'
            state=stream.rng.state;event=original(world,stream,group,sector,force,wanderer_sector);previous=bytes(world)
            events.append(dict(group=group,sector=sector,force=force,state=state,draws=event['rng_draws'],rounds=len(event['rounds']),damage_rounds=sum('damage'in r for r in event['rounds']),raw_force=event['raw_force'],final_state=event['final_rng_state'],record_hex=previous[4051*137:4052*137].hex()))
            return event
        with patch.object(encounter,'assault',side_effect=capture):modeled,stats=matrix.synthesize(before,p,wanderer_encounters=True)
        assert len(events)==18 and [e['group']for e in events]==list(range(2,20))
        # Native targets are opened only after the independent full synthesis.
        for n,v in modeled.items():assert v==gzip.decompress((folder/('after-'+n+'.gz')).read_bytes()),'unchanged complete native six-file observation'
        native=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())[4051*137:4052*137]
        assert previous[4051*137:4052*137]==native,'complete final native Wanderer record'
        key=parent.SHA(first);worlds[key]=parent.packed(first);rows.append(dict(name='matrix/late/'+mode,before_sha256=key,events=events,native_record_hex=native.hex()))
    sources={**d['sources'],'scripts/replay_maintenance_npcs.py':parent.SHA((parent.ROOT/'scripts/replay_maintenance_npcs.py').read_bytes()),'scripts/replay_maintenance_wanderer.py':parent.SHA(Path(encounter.__file__).read_bytes()),'scripts/export_wanderer_assault_fixture.py':parent.SHA(Path(__file__).read_bytes())}
    return dict(format='qb-wanderer-assault-v1',sources=sources,worlds=worlds,cases=rows)
def validate(document,expected):
    # These are derived portable containers, not original native observations.
    # Qualify complete uncompressed worlds across Python/zlib versions.
    import copy
    def normalized(d):
        d=copy.deepcopy(d)
        d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()}
        return d
    assert normalized(document)==normalized(expected),'portable assault fixture equals modeled prefixes/steps and native final records'
def check(path=FIXTURE):
    d=build();validate(json.loads(Path(path).read_text()),d);return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();d=check()if a.check else build()
    if not a.check:FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 54 modeled assault steps and three complete native final Wanderer records')
