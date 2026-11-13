"""Export portable clean-port inputs and native oracles from existing captures.
Synthesis takes only before bytes and independently observed clock inputs;
after-worlds are opened separately as validation oracles. No native acquisition.
"""
import argparse,base64,datetime,gzip,hashlib,json
from pathlib import Path
import verify_maintenance_calendar as calendar
import verify_maintenance_clock_matrix as matrix
from replay_maintenance_calendar import parameters
from replay_maintenance_clock_matrix import legacy_day
from replay_maintenance_ports import replay_ports,replay_capped_initial_ports

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/clean_ports.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
START=3051*137
SIZE=1000*137

def packed(raw):return base64.b64encode(gzip.compress(raw,mtime=0)).decode()

def case(before,days,timers,capped,target):
    # No target data is available to the synthesis API or clock-input extraction.
    modeled,stats=(replay_capped_initial_ports(before,days,timers)if capped else replay_ports(before,days[0],timers))
    observed=target()[START:START+SIZE]
    assert len(observed)==SIZE and modeled==observed,'all native port bytes; no masking or correction tables'
    return dict(before_sha256=SHA(before),days=list(days),timer_minutes=[t.hex()for t in timers],capped=capped,
                expected_gzip=packed(observed),expected_sha256=SHA(observed),class_counts=stats['class_counts'])

def build():
    # Authenticate old native/source manifests and observation neutrality first.
    calendar.verify();matrix.verify()
    worlds={};rows=[]
    for name in calendar.CASES:
        folder=calendar.DEFAULT/name;before=gzip.decompress((folder/'before-YTDATA.DAT.gz').read_bytes())
        worlds[SHA(before)]=packed(before)
        for mode in('observed-a','observed-b'):
            path=folder/mode;ob=json.loads(gzip.decompress((path/'host-time.json.gz').read_bytes()));p=parameters(name,ob)
            days=[p.date.timetuple().tm_yday]*1000
            row=case(before,days,p.port_timer_minutes,False,lambda p=path:gzip.decompress((p/'after-YTDATA.DAT.gz').read_bytes()))
            rows.append(dict(name='calendar/'+name+'/'+mode,**row))
    before=matrix.neutral.before_input_bytes()['YTDATA.DAT'];worlds[SHA(before)]=packed(before)
    for profile in matrix.PROFILES:
        for mode in('observed-a','observed-b','observed-c'):
            path=matrix.DEFAULT/profile/mode;ob=json.loads(gzip.decompress((path/'host-time.json.gz').read_bytes()));p=matrix.model_inputs(ob)
            days=[legacy_day(before,date)for date in p['port_dates']]
            row=case(before,days,p['port_minutes'],True,lambda p=path:gzip.decompress((p/'after-YTDATA.DAT.gz').read_bytes()))
            rows.append(dict(name='matrix/'+profile+'/'+mode,**row))
    assert len(rows)==32
    sources=('scripts/replay_maintenance_ports.py','scripts/export_clean_port_fixture.py',
             'scripts/verify_maintenance_calendar.py','scripts/verify_maintenance_clock_matrix.py',
             'research/yt-maint/calendar-pins.json','research/yt-maint/clock-matrix-pins.json')
    return dict(format='qb-clean-port-replay-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},worlds=worlds,cases=rows)

def validate(document,expected):
    # Compressed fixture containers are portable, not original observations.
    # Compare their complete uncompressed bytes, independent of zlib headers.
    import copy
    def normalized(d):
        d=copy.deepcopy(d)
        d['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['worlds'].items()}
        for row in d['cases']:row['expected_gzip']=base64.b64encode(gzip.decompress(base64.b64decode(row['expected_gzip'],validate=True))).decode()
        return d
    assert normalized(document)==normalized(expected),'portable fixture equals authenticated before inputs and native oracles'

def check(path=FIXTURE):
    d=build();validate(json.loads(Path(path).read_text()),d);return d

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'existing native port blocks /',len(d['cases'])*1000,'complete records')
