"""Assemble versioned CLI recipes from existing authenticated portable fixtures.

No native acquisition or after-world input. Oracles are written separately for
validation; they are never fields in the recipe consumed by the Go adapter.
"""
import argparse,base64,gzip,hashlib,json,os,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'internal/qbmaint/testdata'
SHA=lambda b:hashlib.sha256(b).hexdigest()
ORIGINAL='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
def load(name):return json.loads((FIXTURES/(name+'.json')).read_text())
def build():
    ports=load('clean_ports');x=load('xannoron_birth');mobile=load('mobile_groups');base=load('mercenary_base');tail=load('npc_tail');aux=load('initial_aux');late=load('late_clock')
    index=lambda d:{c['name']:c for c in d['cases']}
    xi,mi,bi,ti,ai,li=map(index,(x,mobile,base,tail,aux,late));rows=[]
    assert len(ports['cases'])==32 and len(ai)==29 and len(li)==3 and not(set(ai)&set(li))
    for pc in ports['cases']:
        name=pc['name'];world=gzip.decompress(base64.b64decode(ports['worlds'][pc['before_sha256']]))
        if name in li:
            c=li[name];days=c['days'];one=c['helper_one'];two=c['helper_two'];initial=c['initial_state'];timer=c['xannoron_timer']
            # Explicit names avoid relying on case folding in the recipe schema.
            clock={key:c['aux'][title]for key,title in [('news_date','NewsDate'),('news_clock','NewsClock'),('score_date','ScoreDate'),('score_clock','ScoreClock')]}
            before_aux=late['before_aux'];sources=dict(late['sources']);native=c['native_files'];final=c['final_state'];draws=c['draws'];encounters=18;profile='initial-wanderer'
        else:
            xc,mc,bc,tc,ac=xi[name],mi[name],bi[name],ti[name],ai[name]
            days=dict(wanderer=xc['wanderer_day'],xannoron=xc['day'],base=bc['day'],final=tc['final_day'])
            one=[xc['wanderer_timer']]+mc['helper_one']+[bc['timer_hex']]+([]if tc['candidate_timer']is None else[tc['candidate_timer']]);two=mc['helper_two'];initial=xc['initial_state'];timer=xc['timer_hex']
            clock={k:ac[k]for k in('news_date','news_clock','score_date','score_clock')};before_aux=aux['before_aux'][ac['before_aux']];sources=dict(aux['sources']);native=ac['native_files'];final=tc['final_state'];draws=5+mc['draws']+tc['draws'];encounters=0;profile='initial'
        before={'YTDATA.DAT':world,**{n:base64.b64decode(v)for n,v in before_aux.items()}}
        assert set(before)=={'YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT'}and SHA(world)==pc['before_sha256']
        sources['archive/dos-original/YTMAINT.EXE']=ORIGINAL;sources['scripts/export_replay_cli_recipes.py']=SHA(Path(__file__).read_bytes())
        recipe=dict(format='qbmaint-replay-v1',profile=profile,name=name,before_sha256={n:SHA(b)for n,b in before.items()},source_sha256=sources,
                    recipe=dict(ports=dict(days=pc['days'],timer_minutes=pc['timer_minutes'],capped=pc['capped']),wanderer_day=days['wanderer'],xannoron_day=days['xannoron'],base_day=days['base'],final_day=days['final'],initial_state=initial,helper_one=one,helper_two=two,xannoron_timer=timer,aux=clock))
        rows.append(dict(name=name,recipe=recipe,before=before,oracles=dict(native_files=native,final_state=final,draws=draws,encounters=encounters)))
    return rows

def export(out):
    rows=build();out=Path(out);out.mkdir() # Exclusive: never reuse a before/source/output directory.
    try:
        for row in rows:
            folder=out/row['name'].replace('/','-');folder.mkdir();before=folder/'before';before.mkdir()
            for n,b in row['before'].items():(before/n).write_bytes(b)
            (folder/'recipe.json').write_text(json.dumps(row['recipe'],indent=2)+'\n')
            (folder/'oracles.json').write_text(json.dumps(row['oracles'],indent=2)+'\n')
    except BaseException:shutil.rmtree(out);raise
    return len(rows)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print('Exported',export(a.out),'existing-fixture research CLI recipes to',a.out)
