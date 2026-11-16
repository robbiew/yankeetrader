"""Assemble three-day research CLI v2 recipes from existing qualified fixtures.

Only initial files and source clocks enter recipes. Expected hashes/states remain
in separate verification oracles, never consumed by the replay command.
"""
import argparse,base64,gzip,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'internal/qbmaint/testdata'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def load(name):return json.loads((FIXTURES/(name+'.json')).read_text())
def build():
    aux=load('evolved_auxiliary');ports=load('evolved_ports');planets=load('evolved_planets')
    births=load('convergence_day_one');homes=load('evolved_continuation');tails=load('evolved_tail')
    index=lambda d:{c['name']:c for c in d['cases']}
    pi,ei,bi,hi,ti=map(index,(ports,planets,births,homes,tails))
    sources={}
    for document in (aux,ports,planets,births,homes,tails):
        for name,value in document['sources'].items():
            assert name not in sources or sources[name]==value,'conflicting source fingerprints'
            sources[name]=value
    sources['scripts/export_chain_cli_recipes.py']=SHA(Path(__file__).read_bytes())
    rows=[]
    for observation in ('observed-a','observed-b','observed-c'):
        days=[];oracles=[];before=None
        for day in (1,2,3):
            name=f'{observation}/day-{day}';a=next(c for c in aux['cases']if c['name']==name)
            p,e,h,t=pi[name],ei[name],bi[name]if day==1 else hi[name],ti['convergence/'+name]
            if day==1:
                before={n:gzip.decompress(base64.b64decode(aux['blobs'][sha]))for n,sha in a['before'].items()}
                assert all(SHA(before[n])==sha for n,sha in a['before'].items())
            creation=[]if day!=1 else[{k:h[k]for k in ('wanderer_day','xannoron_day','base_day','xannoron_timer')}]
            days.append(dict(day=a['final_day'],initial_state=e['initial_state'],
                ports={k:p[k]for k in ('days','timer_minutes')},planets=e['clocks'],creation=creation,
                home_helpers=h['helpers'],tail_helpers=t['helpers'],
                aux={k:a[k]for k in ('news_date','news_clock','score_date','score_clock')}))
            oracles.append(dict(files=a['expected_files'],final_state=t['final_state'],draws=e['draws']+h['draws']+t['draws']))
        assert before is not None and len(before)==3
        recipe=dict(format='qbmaint-replay-v2',profile='convergence-three-day',name=observation,
            before_sha256={n:SHA(b)for n,b in before.items()},source_sha256=sources,days=days)
        rows.append(dict(name=observation,recipe=recipe,before=before,oracles=oracles))
    return rows

def export(out):
    rows=build();out=Path(out);out.mkdir()
    try:
        for row in rows:
            folder=out/row['name'];folder.mkdir();before=folder/'before';before.mkdir()
            for n,b in row['before'].items():(before/n).write_bytes(b)
            (folder/'recipe.json').write_text(json.dumps(row['recipe'],indent=2)+'\n')
            (folder/'oracles.json').write_text(json.dumps(row['oracles'],indent=2)+'\n')
    except BaseException:shutil.rmtree(out);raise
    return len(rows)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    print('Exported',export(a.out),'existing-fixture three-day CLI recipes to',a.out)
