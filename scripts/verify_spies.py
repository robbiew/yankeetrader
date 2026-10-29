"""Verify preserved spy replay outcomes, immutable fixtures and REA bytes."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda b:hashlib.sha256(b).hexdigest()

def check(path):
    expected=json.loads((ROOT/'research/yt-spies/expected.json').read_text())
    results=json.loads((path/'results.json').read_text())['scenarios']
    source=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
    base=bytearray(source)
    for off,value in {57:1,81:2000000,89:0,125:0}.items():mbf.put(base,2,off,value)
    mbf.put(base,52,65,1)
    for sector,destination in [(100,1),(101,102),(102,101)]:
        r=51+sector;base[(r-1)*137:r*137]=bytes(137);mbf.put(base,r,41,destination)
    mbf.put(base,52,41,100);mbf.put(base,3,57,200)
    assert {r['name'] for r in results}==set(expected) and len(results)==len(expected)
    for result in results:
        name=result['name'];gold=expected[name];d=path/name
        assert json.loads((d/'result.json').read_text())==result
        assert result['complete'],name
        assert result['source_sha256']==sha(source) and result['baseline_sha256']==sha(base)
        assert result['executable_sha256']=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
        assert result['keyfeed_sha256']==sha((ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes())
        assert result['patches']==gold['patches']
        before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
        patched=bytearray(base)
        for r,o,v in gold['patches']:mbf.put(patched,r,o,v)
        assert before==patched and sha(before)==result['before_sha256'] and sha(after)==result['after_sha256']
        assert set(result['files'])=={'KEYS.TXT','transcript.txt','scoreboard.txt','dosbox.log'}
        for f,h in result['files'].items():assert sha((d/f).read_bytes())==h,(name,f)
        t=(d/'transcript.txt').read_text()
        assert 'Entering a new player' not in t and 'Entering a new ship' not in t
        assert 'Returning to Yankee Trader' in t
        assert [int(n) for n in re.findall(r'Spy # 1 will hunt in sector (\d+)',t)]==gold['locations'],name
        assert t.count('RADIO MESSAGE FROM SPY')==gold['reports'],name
        for fragment in gold['contains']:assert fragment in t,(name,fragment)
        assert mbf.get(after,2,49)==gold['turns'] and mbf.get(after,2,81)==1667000,name
    exe=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
    u16=lambda p:int.from_bytes(exe[p:p+2],'little')
    image=bytearray(exe[u16(8)*16:])
    for i in range(u16(6)):
        pos=u16(24)+i*4;o=u16(pos)+16*u16(pos+2)
        image[o:o+2]=((int.from_bytes(image[o:o+2],'little')+0x1000)&65535).to_bytes(2,'little')
    for e in json.loads((ROOT/'research/yt-spies/rea.json').read_text())['byte_evidence']:
        assert e['subject']['digest']['sha256']==sha(exe)
        r=e['normalized_result'];o=int(r['address'],16)-65536
        assert r['complete'] and r['requested_bytes']==r['returned_bytes']
        assert image[o:o+r['returned_bytes']].hex()==r['bytes_hex']
    print(f'Verified {len(results)} spy sessions, snapshots, fixed report outcomes and REA bytes.')

if __name__=='__main__':check(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'research/yt-spies/dos')
