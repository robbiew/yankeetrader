"""Reuse retained five-day Python replay for modeled victorious Mercenary phases.

The full modeled parent and both children finish before native targets and RNG
witnesses audit them. No observed endpoint corrects phase synthesis.
"""
import argparse,base64,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import replay_maintenance_gateway_records as chain
import replay_maintenance_gateway_mercenary as phase
import verify_maintenance_gateway_hazards as native
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/gateway_victory.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
    native.verify();rows=[];worlds={};real=phase.maintain
    def wrapped(world,stream):
        before=bytes(world);state=stream.rng.state;draws=stream.rng.draws;start=stream.index;seed=len(stream.seeds)
        result=real(world,stream);worlds[SHA(before)]=PACK(before)
        rows.append(dict(before_sha256=SHA(before),initial_state=state,
            helpers=[dict(family=1 if f=='h1'else 2,caller=site,timer=t.hex())for f,site,t in stream.schedule[start:stream.index]],
            expected_sha256=SHA(world),final_state=stream.rng.state,draws=stream.rng.draws-draws,statistics=result,
            seeds=stream.seeds[seed:],gates=[chain.mbf.enc(a['gate']).hex()for a in result['activations']]))
        return result
    with patch.object(phase,'maintain',wrapped):report=chain.compare_cases()
    assert len(rows)==36 and len(report['cases'])==216 and all(c['byte_mismatches']==0 for c in report['cases'])
    witnesses=sum(s['rng_witness_checks']for s in report['statistics']);assert witnesses==1962
    for row,s in zip(rows,report['statistics']):
        row['name']=s['case']+'/child-'+str(s['child'])+'/'+s['observation'];row['rng_witness_checks']=s['rng_witness_checks']
    rows=[row for row in rows if row['name'].split('/')[0] in ('guarded-pickup','mine-guarded')]
    assert len(rows)==12
    worlds={row['before_sha256']:worlds[row['before_sha256']] for row in rows}
    names=('scripts/export_gateway_victory_fixture.py','scripts/replay_maintenance_gateway_records.py','scripts/replay_maintenance_gateway_mercenary.py','scripts/replay_maintenance_stock_mercenary.py','scripts/replay_maintenance_gateway_npcs.py','scripts/replay_maintenance_gateway_ports.py','scripts/replay_maintenance_gateway_planets.py','scripts/replay_maintenance_gateway_aux.py','scripts/replay_maintenance_evolved_combat_records.py','scripts/verify_maintenance_gateway_hazards.py','research/yt-maint/gateway-hazard-controls/pins.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-gateway-victory-v1',sources={n:SHA((ROOT/n).read_bytes())for n in names},worlds=worlds,cases=rows,native_audit=dict(exact_comparisons=216,files=1296,normalized_bytes=0,rng_witness_checks=witnesses),selected_native_audit=dict(exact_comparisons=72,files=432,rng_witness_checks=sum(r['rng_witness_checks']for r in rows)))
def validate(d,e):
    def norm(v):
        v=json.loads(json.dumps(v));v['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(b,validate=True))).decode()for k,b in v['worlds'].items()};return v
    assert norm(d)==norm(e),'complete modeled victorious phases and native qualification'
def check():
    e=build();validate(json.loads(FIXTURE.read_text()),e);return e
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 12 modeled gateway-victory phases;',d['native_audit'])
