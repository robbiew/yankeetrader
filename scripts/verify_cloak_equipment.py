"""Independently verify original DOS cloak equipment evidence and bounded claims."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA256 = '04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec'
# Frozen declarations for the final 37 normally completed controls.
RECIPE_SHA256 = '4cf6cea449449cc729251a92fefd0ec0ddb18450833c931fa792102c3fae100a'
RECIPE = 'cloak-energy-anticloak-v1'
GRAPH = {1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
RANGES = {'0x16d7c':80,'0x1769a':180,'0x1774d':216,'0x178b0':107,'0x2874e':232,'0x1a539':60,'0x1a712':120,'0x28836':232,'0x16d3f':80,'0x17c2e':143}
KEEP = {'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def side(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def loaded(data):
    """Rebuild initialized MZ bytes, applying the observed 0x1000 load fixups."""
    header = struct.unpack_from('<H', data, 8)[0] * 16
    image = bytearray(data[header:])
    table = struct.unpack_from('<H', data, 24)[0]
    for i in range(struct.unpack_from('<H', data, 6)[0]):
        off, seg = struct.unpack_from('<HH', data, table + 4*i)
        at = seg*16 + off
        struct.pack_into('<H', image, at, (struct.unpack_from('<H', image, at)[0] + 0x1000) & 0xffff)
    return image


def verify_native(research, binary):
    records = read(research/'rea/yt.json')['records']
    assert len(records) == len(RANGES), 'native observation count'
    image, seen = loaded(binary), set()
    for e in records:
        v = e['normalized_result']
        address = v['address']
        assert address in RANGES and address not in seen, 'native address set'
        seen.add(address)
        count = RANGES[address]
        assert e['operation'] == 'read_bytes', 'native operation'
        assert e['subject']['digest']['sha256'] == sha(binary), 'native target identity'
        assert v['complete'] and v['requested_bytes'] == v['returned_bytes'] == count, 'incomplete native bytes'
        at = int(address, 16) - 0x10000
        assert bytes.fromhex(v['bytes_hex']) == image[at:at+count], 'native bytes'
    assert seen == set(RANGES), 'native address set'


def verify_semantics(name, before, after, text, mbf):
    """Check observed resource outcomes independently of the capture manifest."""
    get = mbf.get
    before_cash, after_cash = get(before,2,81), get(after,2,81)
    before_cloak, after_cloak = get(before,2,125), get(after,2,125)
    energy = {
        'energy-one-exact':(1000,.01), 'energy-one-above':(1000,.01),
        'energy-one-below':(0,0), 'energy-ten':(10000,.1),
        'energy-partial':(10000,.47), 'energy-fill':(10000,1),
        'energy-overfill':(0,.9), 'energy-over100':(0,0),
        'energy-full-positive':(0,1), 'energy-zero':(0,0),
        'energy-negative':(0,0), 'energy-fraction':(1000,.01),
        'energy-invalid':(0,0), 'energy-blank':(10000,1),
        'energy-poor-blank':(1000,.01), 'energy-full-blank':(0,1),
        'energy-repeat':(30000,.3), 'energy-reconnect':(0,.1),
    }
    anti_active = {'anti-exact','anti-above','anti-own-full','anti-empty','anti-far',
                   'anti-repeat','anti-recharge-after','anti-decay','anti-before-boundary'}
    anti_refused = {'anti-poor','anti-decline','anti-blank','anti-invalid'}
    reconnects = {'energy-reconnect','anti-reconnect','anti-recharge-reconnect','anti-boundary-reconnect'}
    movements = {'control-decay','anti-decay','anti-boundary-reconnect'}
    controls = {'control-look','control-earth','control-decay'}
    known = set(energy) | anti_active | anti_refused | reconnects | controls
    assert name in known, 'unknown semantic scenario'
    turns = int(name not in reconnects and name != 'control-look') + int(name in movements)
    assert get(after,2,49) == get(before,2,49)-turns, (name, 'turn debit')
    assert get(after,2,57) == (2 if name in movements else get(before,2,57)), (name, 'final sector')
    expected_cloak = before_cloak
    spent = 0
    if name in energy:
        spent, expected_cloak = energy[name]
        assert ('Buy how many points of Cloak Energy?' in text) == (name != 'energy-reconnect'), 'energy quantity prompt'
        if name in {'energy-overfill','energy-over100','energy-full-positive'}:
            assert "You can't have over 100% cloak!" in text, 'overfull rejection'
    if name in anti_active:
        activations = 2 if name == 'anti-repeat' else 1
        spent = activations*500000
        assert text.count('Anti-Cloaking device activated!') == activations, 'activation count'
        assert text.count('Anti-Cloaking Device works for this logon only. Buy one? [y/N]') == activations, 'activation confirmation'
        if name == 'anti-recharge-after':
            spent += 10000
            expected_cloak = .6
        if name != 'anti-empty':
            assert 'Enemy  is uncloaked!' in text, 'target reveal'
        else:
            assert 'is uncloaked!' not in text, 'unexpected empty reveal'
        assert 'Cloak Energy. : FAIL' in text, 'active display'
        positives = sum(get(before, record, 125) > 0 for record in range(2,52))
        assert text.count('is uncloaked!') == positives, 'global reveal count'
    if name in anti_refused:
        assert 'Anti-Cloaking device activated!' not in text and 'is uncloaked!' not in text, 'declined activation'
        if name == 'anti-poor':
            assert 'Anti-Cloaking Device works for this logon only.' not in text, 'poor confirmation'
        else:
            prompts = 2 if name == 'anti-invalid' else 1
            assert text.count('Anti-Cloaking Device works for this logon only. Buy one? [y/N]') == prompts, 'refusal confirmation'
            if name == 'anti-invalid':
                assert re.search(r'Buy one[?] \[y/N\].*?X\nAnti-Cloaking Device works', text, re.S), 'invalid confirmation reprompt'
    if name in {'control-decay','anti-boundary-reconnect'}:
        expected_cloak = .99
    if name in reconnects:
        assert 'Anti-Cloaking device activated!' not in text and 'Cloak Energy. : FAIL' not in text, 'reconnect retained activation'
    scans = re.findall(r'\[ Sensors Activated \](.*?)\[ End Sensor Scan \]', text, re.S)
    if name in {'control-look','control-earth'} | anti_refused | {'anti-reconnect','anti-recharge-reconnect'}:
        assert len(scans) == 1 and 'Enemy  - Fighters:' not in scans[0], 'concealed scan'
    if name in {'anti-exact','anti-above','anti-own-full','anti-empty','anti-repeat','anti-recharge-after'}:
        assert len(scans) == 1 and 'Enemy  - Fighters: 42 - Shields: 7' in scans[0], 'revealed scan'
    assert after_cash == before_cash-spent, (name, 'exact credit debit')
    assert get(after,2,109)-after_cash == 9890250, (name, 'unexpected cloak/device score bonus')
    at = 137+125
    assert after[at:at+4] == mbf.enc(expected_cloak), (name, 'cloak result')
    assert get(after,3,125) == get(before,3,125), 'victim stored cloak changed'
    if name == 'anti-far':
        assert get(before,3,57) == get(after,3,57) == 103, 'remote target position'
        assert len(scans) == 1 and 'Enemy  - Fighters:' not in scans[0], 'remote scan boundary'


def verify(research):
    droot = research/'dos'
    source = ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
    base = (source/'YTDATA.DAT').read_bytes()
    assert sha(base) == BASELINE_SHA256, 'baseline identity'
    assert gzip.decompress((droot/'baseline.dat.gz').read_bytes()) == base, 'retained baseline'
    raw = (droot/'recipe.json').read_bytes()
    assert sha(raw) == RECIPE_SHA256, 'frozen declarations'
    recipe = json.loads(raw)
    manifest = read(droot/'results.json')
    assert recipe['recipe'] == manifest['recipe'] == RECIPE, 'recipe identity'
    declarations = recipe['scenarios']
    specs = {c['name']: c for c in declarations}
    rows = manifest['scenarios']
    assert len(rows) == len(specs) == len(declarations), 'scenario count'
    assert len({c['name'] for c in rows}) == len(rows) and {c['name'] for c in rows} == set(specs), 'scenario identities'
    assert all(re.fullmatch(r'[a-z0-9-]+', name) for name in specs), 'scenario path'
    bins = {name:(ROOT/'archive/dos-original'/name).read_bytes() for name in ('YT.EXE','BRUN30.EXE','LOCAL.EXE')}
    bins['KEYFEED.COM'] = (ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
    spec = importlib.util.spec_from_file_location('mbf', ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mbf)
    worlds, sides, texts = {}, {}, {}
    for c in rows:
        name = c['name']
        decl, directory = specs[name], droot/name
        assert c == read(directory/'result.json'), 'manifest/result mismatch'
        assert all(c[k] == value for k, value in decl.items()), 'declaration mismatch'
        assert c['recipe'] == RECIPE and c['baseline_sha256'] == sha(base), 'session recipe/baseline'
        assert c['complete'] and not c['timed_out'] and c['timeout_seconds'] == 150, 'incomplete session'
        assert c['binaries'] == {n:sha(b) for n,b in bins.items()}, 'binary identity'
        assert set(c['files']) == KEEP, 'retained file set'
        assert {p.name for p in directory.iterdir() if p.is_file()} == KEEP | {'result.json'}, 'unexpected retained file'
        for file, digest in c['files'].items():
            assert sha((directory/file).read_bytes()) == digest, (name, file, 'file hash')
        assert c['date'] == '10/24/2026' and '10/24/2026' in (directory/'DOSDATE.LOG').read_text(), 'DOS date'
        clock = re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)', (directory/'DOSTIME.LOG').read_text())
        assert clock, 'DOS clock'
        hour, minute, second, fraction, ampm = clock.groups()
        actual = int(hour)%12 + (12 if ampm == 'pm' else 0)
        requested = list(map(int, c['time'].split(':')))
        target = requested[0]*3600 + requested[1]*60 + requested[2]
        observed = actual*3600 + int(minute)*60 + int(second) + int(fraction)/(10**len(fraction))
        assert abs(observed-target) <= .06, 'DOS clock mismatch'
        before = gzip.decompress((directory/'before.dat.gz').read_bytes())
        after = gzip.decompress((directory/'after.dat.gz').read_bytes())
        assert len(before) == len(after) == 568687, 'world size'
        parent = c.get('parent')
        if parent:
            assert parent in worlds, 'missing or unordered parent'
            expected, patches, initial = bytearray(worlds[parent][1]), [], sides[parent]
        else:
            expected = bytearray(base)
            for sector, warps in GRAPH.items():
                at = (51+sector-1)*137
                expected[at:at+137] = bytes(137)
                for off, value in zip(range(41,65,4), warps):
                    mbf.put(expected, 51+sector, off, value)
            patches = [[2,o,v] for o,v in {45:0,49:500,57:1,89:0,93:0,105:0,125:0}.items()]
            patches += [[3,o,v] for o,v in {45:0,57:2,61:42,53:7,89:0,125:1}.items()]
            patches += [[52,65,1],[152,65,2],[3053,93,101],[153,93,2],[4053,73,0],[4053,77,12]]
            initial = {f.name:f.read_bytes() for f in source.iterdir() if f.suffix.upper() in ('.DAT','.ASC') and f.name != 'YTDATA.DAT'}
        patches += decl['patches']
        assert c['applied_patches'] == patches, 'applied declarations'
        for record, off, value in patches:
            mbf.put(expected, record, off, value)
        assert before == expected, 'undeclared setup or broken world chain'
        assert {n:bytes.fromhex(v) for n,v in side(directory/'side-before.json.gz').items()} == initial, 'auxiliary input chain'
        aux = side(directory/'sidefiles.json.gz')
        assert set(aux) == set(initial), 'auxiliary file set'
        final = {}
        for n, entry in aux.items():
            final[n] = bytes.fromhex(entry['hex'])
            assert entry['before_sha256'] == sha(initial[n]) and entry['after_sha256'] == sha(final[n]), 'auxiliary output identity'
        worlds[name], sides[name] = (before, after), final
        tail = '\r0\r~Q;Y\r~~' if c.get('port_rescue') else '\rQ;Y\r~~'
        keys = ('\r~~~~~\r~' + c['command'] + '\r~~~~' + tail*24).encode()
        assert (directory/'KEYS.TXT').read_bytes() == keys, 'exact input stream'
        text = (directory/'transcript.txt').read_text()
        texts[name] = text
        assert 'Returning to Yankee Trader Local Logon Program...' in text, 'normal quit'
        # Only these actor resources and logout score caches may change. This
        # checks every other byte, including other players, banks and treasuries.
        conserved = bytearray(before)
        for off in (49,57,81,109,125):
            at = 137+off
            conserved[at:at+4] = after[at:at+4]
        for record in range(3,52):
            at = (record-1)*137+109
            conserved[at:at+4] = after[at:at+4]
        assert conserved == after, (name, 'undeclared world effect')
        assert mbf.get(after,2,45) == 0, 'unexpected player death'
        verify_semantics(name, before, after, text, mbf)
    verify_native(research, bins['YT.EXE'])
    print(f'Verified {len(rows)} completed cloak-equipment controls, exact world/auxiliary chains, resource conservation and {len(RANGES)} complete native byte observations.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', type=Path, default=ROOT/'research/yt-cloak-equipment')
    verify(parser.parse_args().research)
