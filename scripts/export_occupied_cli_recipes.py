"""Assemble occupied research CLI recipes from existing qualified fixtures.

Only original files and startup/source clocks enter the CLI recipe. Expected
outputs, modeled phase worlds, events and endpoints remain comparison-side.
"""
import argparse,base64,gzip,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'internal/qbmaint/testdata'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def load(n):return json.loads((FIXTURES/(n+'.json')).read_text())
def build():
    docs=[load('occupied_'+n)for n in ('planets','routing','reports','records')]
    planets,routing,reports,records=docs
    pi,ri,ai=({c['name']:c for c in d['cases']}for d in docs[:3])
    sources={}
    for d in docs:
        for n,h in d['sources'].items():
            assert n not in sources or sources[n]==h,'conflicting source identity'
            sources[n]=h
    sources['scripts/export_occupied_cli_recipes.py']=SHA(Path(__file__).read_bytes());rows=[]
    for c in records['cases']:
        name=c['name'];p,r,a=pi[name],ri[name],ai[name]
        before={n:gzip.decompress(base64.b64decode(reports['blobs'][sha]))for n,sha in a['before'].items()}
        assert all(SHA(before[n])==sha for n,sha in a['before'].items())
        recipe=dict(format='qbmaint-replay-v3',profile='occupied-day306',name=name.replace('/','-'),
            before_sha256=a['before'],source_sha256=sources,recipe=dict(initial_state=c['startup_state'],
            ports=dict(**p['ports'],capped=True),planets=p['clocks'],
            creation={k:r[k]for k in ('wanderer_day','xannoron_day','base_day','xannoron_timer')},
            routing_helpers=r['helpers'],tail_helpers=c['tail']['helpers'],final_day=c['final_day'],
            aux={k:a[k]for k in ('news_date','news_clock','score_date','score_clock')}))
        rows.append(dict(name=recipe['name'],recipe=recipe,before=before,oracle=dict(files=c['expected_files'],
            final_state=c['final_state'],draws=p['draws']+r['draws']+c['tail']['draws'],combat_events=len(r['events']),
            scores=[a['statistics']['scores'][str(k)]for k in (-1,-2)],losses=[a['statistics']['modeled_losses'][str(k)]for k in (-1,-2)],
            activations=len(c['mercenary']['activations']),candidate=c['candidate'])))
    assert len(rows)==30 and len({r['name']for r in rows})==30
    return rows

def export(out):
    rows=build();out=Path(out);out.mkdir()
    try:
        for row in rows:
            folder=out/row['name'];folder.mkdir();before=folder/'before';before.mkdir()
            for n,b in row['before'].items():(before/n).write_bytes(b)
            (folder/'recipe.json').write_text(json.dumps(row['recipe'],indent=2)+'\n')
            (folder/'oracles.json').write_text(json.dumps(row['oracle'],indent=2)+'\n')
    except BaseException:shutil.rmtree(out);raise
    return len(rows)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    print('Exported',export(a.out),'occupied CLI recipes to',a.out)
