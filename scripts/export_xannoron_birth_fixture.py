"""Before-only Xannoron synthesis; existing native records are separate oracles."""
import argparse,base64,gzip,json,math
from pathlib import Path
import export_clean_port_fixture as parent
import export_wanderer_birth_fixture as wanderer
from replay_maintenance_calendar import parameters
from replay_maintenance_clock_matrix import inputs_from_observation,legacy_day
import replay_maintenance_npcs as npc
ROOT=parent.ROOT
FIXTURE=ROOT/'internal/qbmaint/testdata/xannoron_birth.json'

def synthesize(before,day,timer,state):
    seconds=npc.qb.mbf.dec(timer);assert .01<=seconds<86400,'nonzero native DOS TIMER scope'
    minutes=npc.F32(seconds/60);timestamp=bytearray(npc.qb.mbf.enc(math.floor(minutes))if minutes>=1 else npc.qb.mbf.enc(minutes))
    if minutes<1:timestamp[3]=0
    rng=npc.qb.QB3(state);ground=math.floor(npc.F32(rng.rnd()*250));bank=npc.F32(npc.F32(rng.rnd()*10000000)+100000);ground+=math.floor(npc.F32(rng.rnd()*25));assert ground>0
    rec=bytearray(before[4150*137:4151*137]);rec[:41]=b'Xannoron'.ljust(41,b' ')
    for off,v in((41,day),(85,8),(73,-1),(77,ground),(117,bank),(125,0)):rec[off:off+4]=npc.qb.mbf.enc(v)
    rec[89:93]=timestamp
    for offsets,a in(((45,49,53),0x8134),((57,61,65,69),0x8386)):
        for off in offsets:rec[off:off+4]=npc.constants()[a]
    return bytes(rec),ground,npc.qb.mbf.enc(bank),bytes(timestamp),rng.state

def build():
    d=parent.build();rows=[]
    for c in d['cases']:
        family,profile,mode=c['name'].split('/');folder=(parent.calendar.DEFAULT if family=='calendar'else parent.matrix.DEFAULT)/profile/mode
        before=gzip.decompress(base64.b64decode(d['worlds'][c['before_sha256']]))
        ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));p=parameters(profile,ob)if family=='calendar'else inputs_from_observation(ob)
        wday=p.date.timetuple().tm_yday if family=='calendar'else legacy_day(before,p.wanderer_date)
        day=p.date.timetuple().tm_yday if family=='calendar'else legacy_day(before,p.xannoron_date)
        wrecord,sector,seeded,state=wanderer.synthesize(before,wday,p.h1_timers[0],p.initial_state)
        modeled=bytearray(before);modeled[4051*137:4052*137]=wrecord;at=(50+sector)*137+93;modeled[at:at+4]=npc.qb.mbf.enc(1)
        record,ground,bank,timestamp,final=synthesize(bytes(modeled),day,p.xannoron_timer,state)
        hq=int(npc.qb.mbf.get(before,1,117))
        # Native targets become available only after independent prefix+birth synthesis.
        after=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes());link=after[(50+hq)*137+93:(50+hq)*137+97]
        assert record==after[4150*137:4151*137] and link==npc.qb.mbf.enc(100),'complete native Xannoron record/HQ link'
        rows.append(dict(name=c['name'],before_sha256=c['before_sha256'],wanderer_day=wday,wanderer_timer=p.h1_timers[0].hex(),initial_state=p.initial_state,
                         day=day,timer_hex=p.xannoron_timer.hex(),state=state,hq=hq,ground=ground,bank_hex=bank.hex(),timestamp_hex=timestamp.hex(),final_state=final,record_hex=record.hex(),link_hex=link.hex()))
    assert len(rows)==32
    sources={**d['sources'],'scripts/export_xannoron_birth_fixture.py':parent.SHA(Path(__file__).read_bytes()),
             'scripts/export_wanderer_birth_fixture.py':parent.SHA(Path(wanderer.__file__).read_bytes()),
             'scripts/replay_maintenance_npcs.py':parent.SHA(Path(npc.__file__).read_bytes()),'archive/dos-original/YTMAINT.EXE':npc.MAINT_SHA}
    return dict(format='qb-xannoron-birth-v1',sources=sources,cases=rows)

def check(path=FIXTURE):
    d=build();assert json.loads(Path(path).read_text())==d,'portable Xannoron fixture equals authenticated native records and modeled prefix';return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'whole native Xannoron records/HQ links and before-only Wanderer prefixes')
