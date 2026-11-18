"""Reuse retained four-day Python runs for modeled clear-gateway positive stock phases.

The modeled parent/child phases are completed before independent native targets
or RNG witnesses are compared; neither supplies corrections to synthesis.
"""
import argparse,base64,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import replay_maintenance_stock_records as chain
import replay_maintenance_stock_mercenary as phase
import verify_maintenance_stock_conversion as native
import verify_maintenance_stock_conversion_native as source
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/clear_gateway_stock.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
    native.verify();source.verify();rows=[];worlds={};real=phase.maintain
    def wrapped(world,stream):
        before=bytes(world);state=stream.rng.state;draws=stream.rng.draws;start=stream.index;seed=len(stream.seeds)
        result=real(world,stream);worlds[SHA(before)]=PACK(before)
        rows.append(dict(before_sha256=SHA(before),initial_state=state,
            helpers=[dict(family=1 if f=='h1'else 2,caller=site,timer=t.hex())for f,site,t in stream.schedule[start:stream.index]],
            expected_sha256=SHA(world),final_state=stream.rng.state,draws=stream.rng.draws-draws,statistics=result,
            seeds=stream.seeds[seed:],gates=[chain.mbf.enc(a['gate']).hex()for a in result['activations']],
            raw_stock=chain.mbf.enc(result['events'][0]['raw_stock']).hex()))
        return result
    with patch.object(phase,'maintain',wrapped):report=chain.compare_cases()
    audit=chain.assert_comparisons(report)
    assert len(rows)==36 and audit['files']==1296
    for row,s in zip(rows,report['statistics']):row['name']=s['case']+'/'+s['observation']
    names=('scripts/export_clear_gateway_stock_fixture.py', 'scripts/replay_maintenance_stock_records.py', 'scripts/replay_maintenance_stock_mercenary.py', 'scripts/replay_maintenance_stock_npcs.py', 'scripts/replay_maintenance_stock_planets.py', 'scripts/replay_maintenance_stock_aux.py', 'scripts/replay_maintenance_gateway_ports.py', 'scripts/replay_maintenance_evolved_combat_records.py', 'scripts/verify_maintenance_stock_conversion.py', 'scripts/verify_maintenance_stock_conversion_native.py', 'research/yt-maint/stock-conversion-controls/pins.json', 'archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-clear-gateway-stock-v1',sources={n:SHA((ROOT/n).read_bytes())for n in names},worlds=worlds,cases=rows,native_audit=audit)
def validate(d,e):
    def norm(v):
        v=json.loads(json.dumps(v));v['worlds']={k:base64.b64encode(gzip.decompress(base64.b64decode(b,validate=True))).decode()for k,b in v['worlds'].items()};return v
    assert norm(d)==norm(e),'complete modeled phases and native qualification'
def check():
    e=build();validate(json.loads(FIXTURE.read_text()),e);return e
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 36 modeled clear-gateway stock phases;',d['native_audit'])
