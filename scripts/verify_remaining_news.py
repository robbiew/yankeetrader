"""Independently check remaining-news native bytes and retained DOS output."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-newspaper/remaining'
SHA=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('news_native_primitives',ROOT/'scripts/verify_spy_triggers.py')
primitive=importlib.util.module_from_spec(spec);spec.loader.exec_module(primitive)

def check(root=DEFAULT):
    root=Path(root)
    binary=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
    assert SHA(binary)=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
    image=primitive.loaded(binary)
    bundle=json.loads((root/'rea.json').read_text())
    reads=[r for r in bundle['records'] if r['operation']=='read_bytes']
    searches=[r for r in bundle['records'] if r['operation']=='search_bytes']
    assert len(reads)==8 and len(searches)==1
    for r in reads:
        v=r['normalized_result'];offset=int(v['address'],16)-0x10000
        assert r['subject']['digest']['sha256']==SHA(binary)
        assert v['complete'] and v['returned_bytes']==v['requested_bytes']
        assert bytes.fromhex(v['bytes_hex'])==image[offset:offset+v['returned_bytes']]
    search=searches[0];v=search['normalized_result']
    assert v['complete'] and v['next_cursor'] is None
    pattern=bytes.fromhex('9a9b1a421f')
    expected=[]
    for path,segment in [('archive/analysis/yt-combat/main/qb-annotated.txt',0x10000),('archive/analysis/yt-combat/sub/qb-annotated.txt',0x1f420)]:
        for line in (ROOT/path).read_text().splitlines():
            if 'target 1f42:1a9b' in line:
                expected.append(segment+int(line.split()[0].split(':')[1],16))
    assert sorted(int(m['address'],16) for m in v['matches'])==sorted(expected)
    assert len(expected)==61
    for address in expected:assert image[address-0x10000:address-0x10000+5]==pattern
    sources=json.loads((root/'sources.json').read_text())
    assert len(sources)==11
    for source in sources:
        path=ROOT/source['path'];raw=path.read_bytes();assert SHA(raw)==source['sha256']
        if path.name.endswith('.gz'):
            side=json.loads(gzip.decompress(raw))
            news=next(bytes.fromhex(v['hex']) for k,v in side.items() if k.upper()=='YTNEWS.DAT')
        else:news=raw
        assert SHA(news)==source['news_sha256']
        for fragment in source['fragments']:assert fragment.lower() in news.decode('cp437').lower()
    cases={'registration':(b'New Player Entered',0),'team-join':(b'Joined Team',1),'team-wrong-password':(None,0),'team-cancel':(None,0)}
    for name,(fragment,team) in cases.items():
        case=root/'dos'/name;result=json.loads((case/'result.json').read_text())
        assert result['complete'] and result['program_returned'] and not result['timed_out']
        assert result['binaries']['YT.EXE']==SHA(binary)
        for path,digest in result['files'].items():assert SHA((case/path).read_bytes())==digest
        before=json.loads(gzip.decompress((case/'side-before.json.gz').read_bytes()))
        after=json.loads(gzip.decompress((case/'sidefiles.json.gz').read_bytes()))
        key=next(k for k in before if k.upper()=='YTNEWS.DAT')
        old=bytes.fromhex(before[key]).rstrip(b'\x1a');new=bytes.fromhex(after[key]['hex']).rstrip(b'\x1a')
        assert new.startswith(old)
        suffix=new[len(old):]
        if name=='registration':
            assert b'Newsnew' in suffix and suffix.count(b'New Player Entered')==1 and b'Logged on' not in suffix
        else:
            assert suffix.count(b'Logged on')==1
            assert (b'Joined Team 1' in suffix)==(team==1)
            assert b'ABCD' not in suffix and b'WRNG' not in suffix
            world=gzip.decompress((case/'after.dat.gz').read_bytes())
            assert primitive.get(world,2,89)==team
        if fragment:assert fragment in suffix
    return len(expected),len(sources),len(cases)

if __name__=='__main__':
    calls,sources,cases=check(Path(sys.argv[1]) if len(sys.argv)>1 else DEFAULT)
    print(f'Remaining newspaper evidence passed: {calls} direct calls, {sources} retained news sources, {cases} fresh controls.')
