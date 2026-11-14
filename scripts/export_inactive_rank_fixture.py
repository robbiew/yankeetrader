"""Reuse authenticated native captures for the bounded inactive rank/day writer.
No new acquisition and no target data enters the before-only synthesis.
"""
import argparse,datetime,gzip,json
from pathlib import Path
import export_clean_port_fixture as ports
from replay_maintenance_records import configuration_and_inactive_ranks
from replay_maintenance_clock_matrix import legacy_day
ROOT=ports.ROOT
FIXTURE=ROOT/'internal/qbmaint/testdata/inactive_ranks.json'

def writes(world):return world[81:85]+b''.join(world[i*137+109:i*137+113]for i in range(1,51))

def build():
    parent=ports.build();rows=[]
    import base64
    for c in parent['cases']:
        family,profile,mode=c['name'].split('/');folder=(ports.calendar.DEFAULT if family=='calendar'else ports.matrix.DEFAULT)/profile/mode
        before=gzip.decompress(base64.b64decode(parent['worlds'][c['before_sha256']]))
        if family=='calendar':
            date=datetime.datetime.strptime(ports.calendar.CASES[profile][0],'%m/%d/%Y').date();day=date.timetuple().tm_yday
        else:
            observation=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));raw=ports.matrix.model_inputs(observation);date=raw['final_date'];day=legacy_day(before,date)
        # Existing all-inactive Python writer takes a date and writes DOY. For
        # matrix base-year counts, its qualified calendar counterpart uses day.
        if family=='calendar':modeled=configuration_and_inactive_ranks(before,date)
        else:
            from replay_maintenance_clock_matrix import _watermark_and_inactive_ranks
            modeled=_watermark_and_inactive_ranks(before,day)
        native=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
        assert writes(modeled)==writes(native),'all 51 complete native writer fields'
        rows.append(dict(name=c['name'],before_sha256=c['before_sha256'],final_day=day,writes_hex=writes(native).hex()))
    sources={**parent['sources'],'scripts/export_inactive_rank_fixture.py':ports.SHA(Path(__file__).read_bytes()),
             'scripts/replay_maintenance_records.py':ports.SHA((ROOT/'scripts/replay_maintenance_records.py').read_bytes()),
             'scripts/replay_maintenance_clock_matrix.py':ports.SHA((ROOT/'scripts/replay_maintenance_clock_matrix.py').read_bytes())}
    return dict(format='qb-inactive-ranks-v1',sources=sources,cases=rows)

def check(path=FIXTURE):
    d=build();assert json.loads(Path(path).read_text())==d,'portable rank fixture equals authenticated native writer fields';return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'native rank/watermark slices /',len(d['cases'])*51,'complete four-byte fields')
