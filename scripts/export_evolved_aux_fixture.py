"""Export evolved auxiliary/final-metadata inputs from existing modeled chains.

Native files, RNG witnesses and cache probes validate the complete Python chain
separately. No native child world or after-file enters synthesis.
"""
import argparse,base64,copy,gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
import verify_maintenance_convergence as convergence
import verify_maintenance_evolved_replay as native
import replay_maintenance_evolved_records as chain
import replay_maintenance_evolved_aux as auxiliary

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'internal/qbmaint/testdata/evolved_auxiliary.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PACK=lambda b:base64.b64encode(gzip.compress(b,mtime=0)).decode()

def build():
    convergence.verify();native.verify();auxiliary.original_literals()
    blobs={};phases=[];rows=[]
    original_final,original_aux=chain._watermark_and_inactive_ranks,chain.aux_synthesize
    def blob(raw):key=SHA(raw);blobs[key]=PACK(raw);return key
    def finalize(world,day):
        phases.append(dict(modeled_sha256=blob(world),final_day=day))
        return original_final(world,day)
    def publish(before,world,news_date,news_clock,score_date,score_clock,*,created=()):
        outputs,stats=original_aux(before,world,news_date,news_clock,score_date,score_clock,created=created)
        row=phases[-1];row.update(before={n:blob(v)for n,v in before.items()},
            news_date=news_date.isoformat(),news_clock=news_clock,score_date=score_date.isoformat(),score_clock=score_clock,
            created=[key in created for key in ('wanderer','xannoron','base')],
            expected_files={n:SHA(v)for n,v in {'YTDATA.DAT':world,**outputs}.items()})
        rows.append(row);return outputs,stats
    with patch.object(chain,'_watermark_and_inactive_ranks',finalize),patch.object(chain,'aux_synthesize',publish),patch.object(chain,'initial_before',lambda *_:convergence.initial_inputs()):
        report=chain.compare_cases()
    assert len(rows)==9 and len(report['cases'])==54 and all(c['byte_mismatches']==0 for c in report['cases'])
    assert sum(s['rng_witness_checks']for s in report['statistics'])==501
    assert sum(s['fields']for s in report['cache_checks'])==1440
    for row,stats in zip(rows,report['statistics']):row['name']=stats['observation']+'/'+stats['day']
    sources=('scripts/export_evolved_aux_fixture.py','scripts/replay_maintenance_evolved_records.py',
        'scripts/replay_maintenance_evolved_aux.py','scripts/replay_maintenance_aux.py',
        'scripts/replay_maintenance_clock_matrix.py','scripts/verify_maintenance_convergence.py',
        'scripts/verify_maintenance_evolved_replay.py','research/yt-maint/convergence-chain-controls/pins.json',
        'archive/dos-original/YTMAINT.EXE')
    return dict(format='qb-evolved-aux-v1',sources={n:SHA((ROOT/n).read_bytes())for n in sources},blobs=blobs,cases=rows,
        native_six_file_comparisons=54,native_rng_witnesses=501,native_cache_fields=1440)

def validate(document,expected):
    def normalized(d):
        d=copy.deepcopy(d);d['blobs']={k:base64.b64encode(gzip.decompress(base64.b64decode(v,validate=True))).decode()for k,v in d['blobs'].items()};return d
    assert normalized(document)==normalized(expected),'complete modeled auxiliary inputs and native-qualified output hashes'

def check(path=FIXTURE):
    expected=build();validate(json.loads(Path(path).read_text()),expected);return expected

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check:d=check()
    else:d=build();FIXTURE.write_text(json.dumps(d,indent=2)+'\n')
    print('Verified 9 evolved auxiliary/final phases; 324 native files /501 RNG witnesses /1440 cache fields')
