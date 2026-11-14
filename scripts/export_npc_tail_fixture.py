"""Reuse existing native worlds; initial no-hiring tail has only RNG effects."""
import argparse,base64,gzip,json
from pathlib import Path
import export_mercenary_base_fixture as base
import export_clean_port_fixture as parent
import replay_maintenance_npcs as npc
from replay_maintenance_calendar import parameters
from replay_maintenance_clock_matrix import inputs_from_observation,legacy_day
FIXTURE=parent.ROOT/'internal/qbmaint/testdata/npc_tail.json'
def build():
    b=base.build();d=parent.build();rows=[]
    for c in b['cases']:
        family,profile,mode=c['name'].split('/');folder=(parent.calendar.DEFAULT if family=='calendar'else parent.matrix.DEFAULT)/profile/mode
        ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));p=parameters(profile,ob)if family=='calendar'else inputs_from_observation(ob)
        rng=npc.qb.QB3(c['final_state'])
        for _ in range(20):rng.rnd()
        lottery=rng.rnd();candidate=0;timer=None
        if lottery>=.5:
            assert len(p.h1_timers)==42,'conditional helper inventory';timer=p.h1_timers[41];rng.state=(rng.state&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16);candidate=rng.integer(50)+1
        else:assert len(p.h1_timers)==41,'no unused helper input'
        pc=next(v for v in d['cases']if v['name']==c['name']);before=gzip.decompress(base64.b64decode(d['worlds'][pc['before_sha256']]))
        day=p.date.timetuple().tm_yday if family=='calendar'else legacy_day(before,p.final_date)
        # Independent existing complete NPC model verifies branch/state accounting.
        if family=='calendar':_,stats=npc.synthesize(before,p.h1_timers,p.h2_timers,day=c['day'],xannoron_timer=p.xannoron_timer,initial_state=p.initial_state)
        else:
            days={k:legacy_day(before,getattr(p,k+'_date'))for k in('wanderer','xannoron','base')}
            _,stats=npc.synthesize_clock_matrix(before,p.h1_timers,p.h2_timers,days,xannoron_timer=p.xannoron_timer,initial_state=p.initial_state)
        assert rng.state==stats['final_rng_state']and lottery==stats['lottery_draw'],'independent tail continuation'
        after=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
        rows.append(dict(name=c['name'],state=c['final_state'],candidate_timer=None if timer is None else timer.hex(),candidate=candidate,lottery=lottery,draws=21+bool(candidate),final_state=rng.state,final_day=day,native_world_sha256=parent.SHA(after)))
    assert len(rows)==29
    sources={**b['sources'],'scripts/export_npc_tail_fixture.py':parent.SHA(Path(__file__).read_bytes())}
    return dict(format='qb-initial-npc-tail-v1',sources=sources,excluded_later_encounters=b['excluded_later_encounters'],cases=rows)
def check(path=FIXTURE):
    d=build();assert json.loads(Path(path).read_text())==d,'portable tail fixture equals authenticated inputs, independent model and whole native world';return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();d=check()if a.check else build()
    if not a.check:FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'modeled NPC tails and whole native world oracles')
