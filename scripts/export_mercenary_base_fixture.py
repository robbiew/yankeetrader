"""Before-only Mercenary Base birth with existing native record/link oracles."""
import argparse,base64,gzip,json
from pathlib import Path
import export_mobile_groups_fixture as mobile
import export_xannoron_birth_fixture as birth
import export_clean_port_fixture as parent
import export_wanderer_birth_fixture as wanderer
import replay_maintenance_npcs as npc
from replay_maintenance_calendar import parameters
from replay_maintenance_clock_matrix import inputs_from_observation,legacy_day
FIXTURE=parent.ROOT/'internal/qbmaint/testdata/mercenary_base.json'

def synthesize(before,day,timer,state):
    rec=bytearray(before[4149*137:4150*137]);rec[:41]=b'Mercenary Base'.ljust(41,b' ')
    for off,v in((85,14),(41,day-10)):rec[off:off+4]=npc.qb.mbf.enc(v)
    for offsets,a in(((45,49,53),0x8134),((57,61,65,69),0x8742),((73,),0x800e),((77,),0x8746),((117,),0x874a),((125,),0x874e)):
        for off in offsets:rec[off:off+4]=npc.constants()[a]
    rng=npc.qb.QB3(state);rng.state=(state&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16);seeded=rng.state;sector=rng.integer(3000)
    return bytes(rec),sector,seeded,rng.state

def build():
    m=mobile.build();d=parent.build();x={c['name']:c for c in birth.build()['cases']};rows=[]
    for c in m['cases']:
        family,profile,mode=c['name'].split('/');folder=(parent.calendar.DEFAULT if family=='calendar'else parent.matrix.DEFAULT)/profile/mode
        xc=x[c['name']];before=gzip.decompress(base64.b64decode(d['worlds'][xc['before_sha256']]))
        ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));p=parameters(profile,ob)if family=='calendar'else inputs_from_observation(ob)
        day=p.date.timetuple().tm_yday if family=='calendar'else legacy_day(before,p.base_date)
        timer=p.h1_timers[40];record,sector,seeded,final=synthesize(before,day,timer,c['final_state'])
        # Placement admission uses only prior modeled links, never after-worlds.
        _,wsector,_,_=wanderer.synthesize(before,xc['wanderer_day'],p.h1_timers[0],p.initial_state)
        assert sector not in(wsector,xc['hq']),'no placement retry in retained scope'
        after=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes());at=(50+sector)*137+93;link=after[at:at+4]
        assert record==after[4149*137:4150*137]and link==npc.qb.mbf.enc(99),'complete native base record/link'
        rows.append(dict(name=c['name'],day=day,timer_hex=timer.hex(),state=c['final_state'],sector=sector,seeded_state=seeded,final_state=final,record_hex=record.hex(),link_hex=link.hex()))
    assert len(rows)==29
    sources={**m['sources'],'scripts/export_mercenary_base_fixture.py':parent.SHA(Path(__file__).read_bytes())}
    return dict(format='qb-mercenary-base-v1',sources=sources,excluded_later_encounters=m['excluded_later_encounters'],cases=rows)
def check(path=FIXTURE):
    d=build();assert json.loads(Path(path).read_text())==d,'portable base fixture equals authenticated model and native record/link';return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();d=check()if a.check else build()
    if not a.check:FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'native Mercenary Base records/links and modeled group handoffs')
