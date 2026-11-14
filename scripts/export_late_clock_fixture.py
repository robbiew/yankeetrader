"""Reuse the three observed late-clock worlds for full before-only Go integration."""
import argparse,base64,gzip,json
from pathlib import Path
import export_clean_port_fixture as parent
import replay_maintenance_clock_matrix as matrix
import replay_maintenance_npcs as npc
import replay_maintenance_wanderer as assault
import replay_maintenance_aux as aux
FIXTURE=parent.ROOT/'internal/qbmaint/testdata/late_clock.json'
def build():
    d=parent.build();root=parent.ROOT/'research/yt-maint/initial-controls/baseline-split'
    before={n:gzip.decompress((root/('before-'+n+'.gz')).read_bytes())for n in matrix.FILES[:3]};rows=[]
    for mode in('observed-a','observed-b','observed-c'):
        name='matrix/late/'+mode;folder=matrix.DEFAULT/'late'/mode;p=matrix.inputs_from_observation(json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes())))
        modeled,stats=matrix.synthesize(before,p,wanderer_encounters=True);n=stats['npcs'];hashes={}
        for file,value in modeled.items():
            target=gzip.decompress((folder/('after-'+file+'.gz')).read_bytes());assert value==target,'complete six-file late native parity';hashes[file]=parent.SHA(target)
        events=[]
        for e in n['encounters']:
            events.append(dict(group=e['group'],sector=e['sector'],force=e['initial_force'],state=e['initial_rng_state'],final_state=e['final_rng_state'],raw_force=e['raw_force'],draws=e['rng_draws'],rounds=len(e['rounds']),damage_rounds=sum('damage'in r for r in e['rounds']),rates=[npc.qb.mbf.enc(r).hex()for r in e['final_rates']]))
        assert len(events)==18
        next_seed=next(v for v in n['helper_seeds']if v['helper']=='h1'and v['ordinal']==41)
        days={key:matrix.legacy_day(before['YTDATA.DAT'],getattr(p,key+'_date'))for key in('wanderer','xannoron','base','final')}
        rows.append(dict(name=name,days=days,initial_state=p.initial_state,helper_one=[v.hex()for v in p.h1_timers],helper_two=[v.hex()for v in p.h2_timers],xannoron_timer=p.xannoron_timer.hex(),
                         aux=dict(NewsDate=p.news_date.isoformat(),NewsClock=p.news_clock,ScoreDate=p.score_date.isoformat(),ScoreClock=p.score_clock),
                         events=events,groups=[n['groups'][g]for g in range(1,21)],mobile_final_state=next_seed['old_state'],final_state=n['final_rng_state'],draws=n['total_draws'],desertion_draws=n['desertion_draws'],lottery=n['lottery_draw'],candidate=n.get('lottery_player')or 0,native_files=hashes))
    assert len(rows)==3
    sources={**d['sources'],'scripts/export_late_clock_fixture.py':parent.SHA(Path(__file__).read_bytes()),'scripts/replay_maintenance_clock_matrix.py':parent.SHA(Path(matrix.__file__).read_bytes()),'scripts/replay_maintenance_npcs.py':parent.SHA(Path(npc.__file__).read_bytes()),'scripts/replay_maintenance_wanderer.py':parent.SHA(Path(assault.__file__).read_bytes()),'scripts/replay_maintenance_aux.py':parent.SHA(Path(aux.__file__).read_bytes())}
    return dict(format='qb-late-clock-integration-v1',sources=sources,before_aux={k:base64.b64encode(v).decode()for k,v in before.items()if k!='YTDATA.DAT'},cases=rows)
def check(path=FIXTURE):
    d=build();assert json.loads(Path(path).read_text())==d,'portable late-clock fixture equals authenticated before inputs, model receipts and six native files';return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();d=check()if a.check else build()
    if not a.check:FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified three full late-clock six-file worlds, 54 modeled encounters and source RNG handoffs')
