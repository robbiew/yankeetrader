"""Source-literal auxiliary synthesis and existing complete six-file native oracles."""
import argparse,base64,gzip,json
from pathlib import Path
import export_npc_tail_fixture as tail
import export_clean_port_fixture as parent
import replay_maintenance_calendar as calendar
import replay_maintenance_records as records
import replay_maintenance_clock_matrix as matrix
import replay_maintenance_aux as aux
FIXTURE=parent.ROOT/'internal/qbmaint/testdata/initial_aux.json'
def build():
    t=tail.build();rows=[];payloads={};literals=aux.original_literals()
    for c in t['cases']:
        family,profile,mode=c['name'].split('/');root=(parent.calendar.DEFAULT if family=='calendar'else parent.matrix.DEFAULT)/profile;folder=root/mode
        before_root=root if family=='calendar'else parent.ROOT/'research/yt-maint/initial-controls/baseline-split'
        before={n:gzip.decompress((before_root/('before-'+n+'.gz')).read_bytes())for n in('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT')}
        ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()));p=calendar.parameters(profile,ob)if family=='calendar'else matrix.inputs_from_observation(ob)
        if family=='calendar':out,_=records.synthesize(before,p);nd=sd=p.date;nc=sc=p.clock
        else:out,_=matrix.synthesize(before,p);nd=p.news_date;sd=p.score_date;nc=p.news_clock;sc=p.score_clock
        hashes={}
        for n,v in out.items():
            native=gzip.decompress((folder/('after-'+n+'.gz')).read_bytes());assert v==native,'complete six-file native synthesis';hashes[n]=parent.SHA(native)
        assert hashes['YTDATA.DAT']==c['native_world_sha256'],'Go world composition oracle handoff'
        key=parent.SHA(before['YTNAME.DAT']+b'\0'+before['YTNEWS.DAT']);payloads[key]={n:base64.b64encode(v).decode()for n,v in before.items()if n!='YTDATA.DAT'}
        rows.append(dict(name=c['name'],before_aux=key,news_date=nd.isoformat(),news_clock=nc,score_date=sd.isoformat(),score_clock=sc,native_files=hashes))
    sources={**t['sources'],'scripts/export_initial_aux_fixture.py':parent.SHA(Path(__file__).read_bytes()),'scripts/replay_maintenance_aux.py':parent.SHA(Path(aux.__file__).read_bytes())}
    return dict(format='qb-initial-aux-v1',sources=sources,before_aux=payloads,excluded_later_encounters=t['excluded_later_encounters'],cases=rows)
def check(path=FIXTURE):
    d=build();assert json.loads(Path(path).read_text())==d,'portable auxiliary fixture equals source literals, inputs and six complete native files';return d
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();d=check()if a.check else build()
    if not a.check:FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified',len(d['cases']),'complete six-file native output inventories and source-literal auxiliary models')
