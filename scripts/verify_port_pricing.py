"""Independently validate retained startup port-price probes; never launches DOS.

The expected displayed prices are fixed observations, not recomputed from the
candidate RNG. Amplified controls bracket each reference to roughly +/-0.005;
they do not establish every MBF intermediate rounding bit.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-trade-high'
RECIPE='startup-reference-pricing-v1'
RECIPE_SHA256='b5d9f8836f4aaf45d445ceeb1ea4063ef3a2a24e74a33de9a2d059b2844b043f'
BASELINE_SHA256='75b6cd8a0d6acab0ca0c82f524ca06974b290e691a36aeadc982092f828882ef'
BINARIES={
 'YT.EXE':'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037',
 'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
 'LOCAL.EXE':'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a',
 'KEYFEED.COM':'06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596',
}
REQUIRED_FILES={'DOSDATE.LOG','DOSTIME.LOG','KEYS.TXT','RETURN.LOG','after.dat.gz','before.dat.gz','dosbox.log','game.log.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt'}
GRAPH={1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
# Frozen fixture/scenario contract, intentionally independent of capture code.
COMMON=[[2,57,100],[2,81,1000000],[2,65,1000],[2,69,0],[2,73,0],[2,77,0],
 [151,65,2],[3053,93,100],[3053,97,0],[3053,45,297],[3053,49,1000],
 [3053,53,1000],[3053,57,1000],[3053,61,100],[3053,65,100],[3053,69,100]]
EXPECTED_SCENARIOS=[]
for name,coefficient,at,actor in [
 ('zero-midnight',0,'00:00:00','TESTER'),
 ('normal-midnight',-50,'00:00:00','TESTER'),
 ('amplified-midnight',-10000,'00:00:00','TESTER'),
 ('amplified-noon',-10000,'12:00:00','TESTER'),
 ('amplified-late',-10000,'23:45:00','TESTER'),
 ('amplified-other-actor',-10000,'00:00:00','ENEMY'),
]:
 patches=COMMON+[[3053,offset,coefficient]for offset in (73,77,81)]
 if actor=='ENEMY': patches += [[3,57,100],[3,65,1000],[3,69,0],[3,73,0],[3,77,0],[3,81,1000000]]
 EXPECTED_SCENARIOS.append(dict(name=name,command='P;0;0;0',patches=patches,coefficient=coefficient,time=at,actor=actor))
EXPECTED_SCENARIOS.append(dict(name='amplified-reload',parent='amplified-midnight',command='\r~~~~P;0;0;0',patches=[],coefficient=-10000,time='00:10:00'))
# Shared MBF record primitives only; neither this checker nor its tests import a
# capture/recovery writer or the candidate pricing implementation.
spec=importlib.util.spec_from_file_location('pricing_mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda payload:hashlib.sha256(payload).hexdigest()

def report_prices(text):
    values=[]
    for label in ('Ore','Organics','Equipment'):
        matches=re.findall(r'^'+label+r'\.+\s+(?:Buying|Selling|Neither|None)\s+[^\n]*?\s+([0-9]+)\s*$',text,re.M)
        if not matches:
            raise ValueError('missing '+label+' price report')
        values.append(int(matches[0]))
    return values


def verify(destination, *, require_full=True):
    destination=Path(destination)
    recipe=json.loads((destination/'recipe.json').read_text())
    assert recipe['recipe']==RECIPE
    if require_full:
        assert sha((destination/'recipe.json').read_bytes())==RECIPE_SHA256,'changed recipe or missing coverage'
    baseline=gzip.decompress((destination/'baseline.dat.gz').read_bytes())
    assert hashlib.sha256(baseline).hexdigest()==hashlib.sha256((SOURCE/'YTDATA.DAT').read_bytes()).hexdigest()
    assert sha(baseline)==BASELINE_SHA256,'changed baseline identity'
    outcomes=[]
    canonical={case['name']:case for case in EXPECTED_SCENARIOS}
    expected_prices={0:[20,29,41],-50:[30,44,62],-10000:[2025,2960,4162]}
    for case in recipe['scenarios']:
        assert case==canonical[case['name']], 'changed declared scenario'
        d=destination/case['name'];meta=json.loads((d/'result.json').read_text())
        for key,value in case.items(): assert meta[key]==value,(case['name'],key)
        assert meta['binaries']==BINARIES,'changed binary identity'
        assert set(meta['files'])==REQUIRED_FILES,'changed integrity coverage'
        for name,expected_digest in meta['binaries'].items():
            source=(ROOT/'archive/analysis/yt-combat/KEYFEED.COM') if name=='KEYFEED.COM' else ROOT/'archive/dos-original'/name
            assert hashlib.sha256(source.read_bytes()).hexdigest()==expected_digest,(case['name'],name)
        expected_keys=('\r~~~~~\r~'+case['command']+'\r~~~~'+'\rQ;Y\r~~'*24).encode()
        assert (d/'KEYS.TXT').read_bytes()==expected_keys,'changed command feed'

        assert meta['complete'] and meta['program_returned'] and not meta['timed_out']
        assert meta['recipe']==RECIPE and meta['coefficient']==case['coefficient']
        for name,digest in meta['files'].items():
            assert hashlib.sha256((d/name).read_bytes()).hexdigest()==digest,(case['name'],name)
        assert b'BROADCAST_PROGRAM_RETURNED' in (d/'RETURN.LOG').read_bytes()
        raw=gzip.decompress((d/'game.log.gz').read_bytes())
        assert raw.decode('cp437').replace('\r\n','\n')==(d/'transcript.txt').read_text(),'transcript/raw mismatch'
        assert b'Returning to Yankee Trader Local Logon Program...' in raw
        assert meta['baseline_sha256']==hashlib.sha256(baseline).hexdigest()
        side_before=json.loads(gzip.decompress((d/'side-before.json.gz').read_bytes()))

        before=gzip.decompress((d/'before.dat.gz').read_bytes())
        after=gzip.decompress((d/'after.dat.gz').read_bytes())
        if case.get('parent'):
            assert before==gzip.decompress((destination/case['parent']/'after.dat.gz').read_bytes())
            parent_side=json.loads(gzip.decompress((destination/case['parent']/'sidefiles.json.gz').read_bytes()))
            assert side_before=={name:value['hex'] for name,value in parent_side.items()},'reload auxiliary mismatch'
        else:
            expected_patches=[(2,o,v)for o,v in {45:0,49:500,57:1,89:0,93:0,105:0,125:0}.items()]
            expected_patches += [(3,o,v)for o,v in {45:0,57:2,61:42,53:7,89:0,125:1}.items()]
            expected_patches += [(52,65,1),(152,65,2),(3053,93,101),(153,93,2),(4053,73,0),(4053,77,12)]
            expected_patches += case['patches']
            assert meta['applied_patches']==[list(patch)for patch in expected_patches],'changed patch manifest'
            reconstructed=bytearray(baseline)
            for sector,warps in GRAPH.items():
                start=(51+sector-1)*137;reconstructed[start:start+137]=bytes(137)
                for offset,value in zip(range(41,65,4),warps):mbf.put(reconstructed,51+sector,offset,value)
            for record,offset,value in meta['applied_patches']:mbf.put(reconstructed,record,offset,value)
            assert bytes(reconstructed)==before,'undeclared patch'
            source_side={p.name:p.read_bytes().hex()for p in SOURCE.iterdir()if p.is_file()and p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP')and p.name!='YTDATA.DAT'}
            assert side_before==source_side,'unexpected auxiliary patch'
        record=3 if case.get('actor')=='ENEMY' else 2
        assert mbf.get(before,record,57)==100
        assert mbf.get(after,record,49)==mbf.get(before,record,49)-1,'not exactly one dock turn'
        assert mbf.get(after,record,81)==mbf.get(before,record,81),'probe traded credits'
        assert [mbf.get(after,record,o)for o in (69,73,77)]==[0,0,0],'probe traded cargo'
        assert [mbf.get(before,3053,o)for o in (73,77,81)]==[case['coefficient']]*3
        text=(d/'transcript.txt').read_text()
        prices=report_prices(text)
        assert prices==expected_prices[case['coefficient']],(case['name'],prices)
        outcomes.append(dict(name=case['name'],coefficient=case['coefficient'],prices=prices))
    return outcomes



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',nargs='?',type=Path,default=ROOT/'research/yt-port-generation/pricing-dos')
    args=parser.parse_args()
    outcomes=verify(args.destination)
    print(json.dumps(outcomes,indent=2))
    print('Verified seven normally returned price controls and exact reload chain.')

if __name__=='__main__':main()
