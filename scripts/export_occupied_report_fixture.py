"""Reuse existing occupied Python runs for modeled casualty-report inputs.

The complete Python world/events exist before five-file generation and native
comparison. Expected targets and RNG witnesses never correct synthesis.
"""
import argparse,base64,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import replay_maintenance_occupied_records as chain
import replay_maintenance_occupied_aux as aux
import verify_maintenance_occupied as native
import verify_maintenance_occupied_replay as source
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/occupied_reports.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()
def build():
    native.verify();source.verify();aux.original_literals();blobs={};rows=[];real=chain.auxiliary
    def blob(b):key=SHA(b);blobs[key]=PACK(b);return key
    def report(before,world,news_date,news_clock,score_date,score_clock,*,events=()):
        outputs,stats=real(before,world,news_date,news_clock,score_date,score_clock,events=events)
        rows.append(dict(before={n:blob(b)for n,b in before.items()},world_sha256=blob(world),news_date=news_date.isoformat(),news_clock=news_clock,score_date=score_date.isoformat(),score_clock=score_clock,events=events,
            expected_files={n:SHA(b)for n,b in outputs.items()},statistics=stats));return outputs,stats
    with patch.object(chain,'auxiliary',report):result=chain.compare_cases()
    assert len(rows)==30 and len(result['cases'])==180 and all(c['byte_mismatches']==0 for c in result['cases'])
    assert sum(s['rng_witness_checks']for s in result['statistics'])==1872
    for row,stats in zip(rows,result['statistics']):row['name']=stats['case']+'/'+stats['observation']
    assert sum(len(r['events'])for r in rows)==120
    sources=('scripts/export_occupied_report_fixture.py','scripts/replay_maintenance_occupied_records.py','scripts/replay_maintenance_occupied_aux.py','scripts/replay_maintenance_aux.py','scripts/replay_maintenance_occupied_npcs.py','scripts/replay_maintenance_occupied_mercenary.py','scripts/verify_maintenance_occupied.py','scripts/verify_maintenance_occupied_replay.py','research/yt-maint/occupied-route-controls/pins.json','research/yt-maint/occupied-replay-native/rea.json','archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-occupied-reports-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},blobs=blobs,cases=rows,native_six_file_comparisons=180,native_rng_witnesses=1872)
def validate(document,expected):
    def normalize(d):
        d=json.loads(json.dumps(d));d['blobs']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['blobs'].items()};return d
    assert normalize(document)==normalize(expected),'complete modeled report inputs/events and native-qualified outputs'
def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:check()
    else:FIXTURE.write_text(json.dumps(build(),indent=2)+'\n')
    print('Verified 30 five-file report sets /120 modeled events; 1080 native files /1872 witnesses')
