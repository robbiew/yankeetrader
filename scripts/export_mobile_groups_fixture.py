"""Reuse authenticated initial worlds/clocks; native group fields are separate oracles."""
import argparse,base64,gzip,json
from pathlib import Path
import export_xannoron_birth_fixture as birth
import export_clean_port_fixture as parent
import export_wanderer_birth_fixture as wanderer
import replay_maintenance_npcs as npc
from replay_maintenance_calendar import parameters
from replay_maintenance_clock_matrix import inputs_from_observation,legacy_day
FIXTURE=parent.ROOT/'internal/qbmaint/testdata/mobile_groups.json'
EXCLUDED=wanderer.EXCLUDED

def projection(world):
    return b''.join(world[(50+s)*137+o:(50+s)*137+o+4]for s in range(1,3001)for o in(81,85,129))+b''.join(world[(51+g)*137+105:(51+g)*137+109]for g in range(20))

def build():
    d=parent.build();x=birth.build();rows=[]
    for c in x['cases']:
        if c['name']in EXCLUDED:continue
        family,profile,mode=c['name'].split('/');folder=(parent.calendar.DEFAULT if family=='calendar'else parent.matrix.DEFAULT)/profile/mode
        before=gzip.decompress(base64.b64decode(d['worlds'][c['before_sha256']]))
        ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));p=parameters(profile,ob)if family=='calendar'else inputs_from_observation(ob)
        if family=='calendar':out,stats=npc.synthesize(before,p.h1_timers,p.h2_timers,day=c['day'],xannoron_timer=p.xannoron_timer,initial_state=p.initial_state)
        else:out,stats=npc.synthesize_clock_matrix(before,p.h1_timers,p.h2_timers,dict(wanderer=c['wanderer_day'],xannoron=c['day'],base=legacy_day(before,p.base_date)),xannoron_timer=p.xannoron_timer,initial_state=p.initial_state)
        # The next helper's old state is an independent Python prefix result,
        # not a newly measured native endpoint. No output feeds synthesis.
        seed=next(s for s in stats['helper_seeds']if s['helper']=='h1'and s['ordinal']==41)
        after=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
        assert projection(out)==projection(after),'whole native group field inventory'
        draws=4+1+19*6+stats['candidate_draws']+stats['interception_draws'] # Wanderer+X birth+top+groups
        rows.append(dict(name=c['name'],state=c['final_state'],helper_one=[v.hex()for v in p.h1_timers[1:40]],helper_two=[v.hex()for v in p.h2_timers],
                         groups=[stats['groups'][g]for g in range(1,21)],top_fallback=stats['top_fallback'],draws=draws-4,final_state=seed['old_state'],native_sha256=parent.SHA(projection(after))))
    assert len(rows)==29
    sources={**x['sources'],'scripts/export_mobile_groups_fixture.py':parent.SHA(Path(__file__).read_bytes())}
    return dict(format='qb-mobile-groups-v1',sources=sources,excluded_later_encounters=list(EXCLUDED),cases=rows)

def check(path=FIXTURE):
    d=build();assert json.loads(Path(path).read_text())==d,'portable mobile fixture equals authenticated before-only model and native fields';return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    d=check()if a.check else build()
    if not a.check:FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'native mobile field inventories and independently modeled RNG continuations')
