"""Reuse undisturbed native Wanderer birth records; never infer inputs from targets."""
import argparse,base64,gzip,json
from pathlib import Path
import export_clean_port_fixture as parent
from replay_maintenance_calendar import parameters
from replay_maintenance_clock_matrix import inputs_from_observation,legacy_day
import replay_maintenance_npcs as npc
ROOT=parent.ROOT
FIXTURE=ROOT/'internal/qbmaint/testdata/wanderer_birth.json'
EXCLUDED=('matrix/late/observed-a','matrix/late/observed-b','matrix/late/observed-c')

def synthesize(before,day,timer,state):
    constants=npc.constants();rng=npc.qb.QB3(state);rng.state=(state&255)|((timer[0]^timer[2])<<8)|((timer[1]^timer[3])<<16)
    seeded=rng.state;sector=rng.integer(3000);rec=bytearray(before[4051*137:4052*137]);rec[:41]=b'The Wanderer'.ljust(41,b' ')
    for off,val in((41,day-10),(85,12),(73,0)):rec[off:off+4]=npc.qb.mbf.enc(val)
    for offsets,address in(((45,49,53),0x82ac),((57,61,65,69,77,125),0x82b0),((117,),0x82b4)):
        for off in offsets:rec[off:off+4]=constants[address]
    return bytes(rec),sector,seeded,rng.state

def build():
    d=parent.build();rows=[]
    for c in d['cases']:
        if c['name']in EXCLUDED:continue # Later native encounters alter birth state.
        family,profile,mode=c['name'].split('/');folder=(parent.calendar.DEFAULT if family=='calendar'else parent.matrix.DEFAULT)/profile/mode
        before=gzip.decompress(base64.b64decode(d['worlds'][c['before_sha256']]))
        ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));p=parameters(profile,ob)if family=='calendar'else inputs_from_observation(ob)
        day=p.date.timetuple().tm_yday if family=='calendar'else legacy_day(before,p.wanderer_date)
        timer=p.h1_timers[0];record,sector,seeded,final=synthesize(before,day,timer,p.initial_state)
        # Targets open only after clock/state extraction and before-only synthesis.
        after=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes());link=after[(50+sector)*137+93:(50+sector)*137+97]
        assert record==after[4051*137:4052*137] and link==npc.qb.mbf.enc(1),'complete undisturbed native birth record and placement'
        rows.append(dict(name=c['name'],before_sha256=c['before_sha256'],day=day,timer_hex=timer.hex(),initial_state=p.initial_state,
                         sector=sector,seeded_state=seeded,final_state=final,record_hex=record.hex(),link_hex=link.hex()))
    assert len(rows)==29
    sources={**d['sources'],'scripts/export_wanderer_birth_fixture.py':parent.SHA(Path(__file__).read_bytes()),
             'scripts/replay_maintenance_npcs.py':parent.SHA((ROOT/'scripts/replay_maintenance_npcs.py').read_bytes()),
             'archive/dos-original/YTMAINT.EXE':npc.MAINT_SHA}
    return dict(format='qb-wanderer-birth-v1',sources=sources,excluded_later_encounters=list(EXCLUDED),cases=rows)

def check(path=FIXTURE):
    d=build();assert json.loads(Path(path).read_text())==d,'portable birth fixture equals authenticated native record/placement and modeled RNG';return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'native whole birth records and links; three later encounters excluded')
