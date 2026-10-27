"""Verify original-DOS loot/estate probes, provenance and bounded rule checks."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'research/yt-ships/loot-dos'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


mbf = module('mbf', ROOT/'archive/analysis/yt-maint/experiments.py')
runner = module('loot_runner', ROOT/'scripts/recover_loot.py')
rules = module('loot_rules', ROOT/'research/yt-ships/loot_rules.py')
digest = lambda b: hashlib.sha256(b).hexdigest()
source = ROOT/'archive/analysis/yt-combat/experiments/fixture-ship-kill'
exe = digest((ROOT/'archive/dos-original/YT.EXE').read_bytes())
assert exe == 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
baseline = gzip.decompress((EVIDENCE/'baseline.dat.gz').read_bytes())
assert baseline == bytes(runner.prepare_baseline(source, mbf))
manifest = json.loads((EVIDENCE/'results.json').read_text())
rows = manifest['scenarios']
assert len(rows) == 37 and len({r['name'] for r in rows}) == 37
cases = {}

for row in rows:
    name = row['name']
    directory = EVIDENCE/name
    assert row['complete'] and row['executable_sha256'] == exe, name
    assert row['source_sha256'] == digest((source/'YTDATA.DAT').read_bytes()), name
    assert row['baseline_sha256'] == digest(baseline), name
    assert row['keyfeed_sha256'] == digest((ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()), name
    assert row['dos_date'] == '10/24/2026', name
    assert row['dos_time'] == (f'{int(name[-2:]):02d}:00:00' if name.startswith('loot-clock-') else '00:00:00'), name
    for key, filename in [('keys', 'KEYS.TXT'), ('transcript', 'transcript.txt'), ('dosbox_log', 'dosbox.log')]:
        assert digest((directory/filename).read_bytes()) == row[key+'_sha256'], (name, key)
    text = (directory/'transcript.txt').read_text()
    command = b'A\r~~Y\r~~1000'
    if name.startswith('loot-self-') or name == 'loot-live-self-estate':
        command = b'!;100;1'
    if name.startswith('loot-live-mine-'):
        command = b'Q;Y'
    if name == 'loot-estate-collect':
        command += b'\r~~~~$'
    if name == 'loot-live-chain-death':
        command = b'A\r~~Y\r~100'
    assert (directory/'KEYS.TXT').read_bytes() == b'\r~~~~~\r~'+command+b'\r~~~~'+b'\rQ;Y\r~~'*24, name
    assert 'Returning to Yankee Trader Local Logon Program' in text, name
    assert all(error not in text for error in ('Syntax error', 'Illegal function call', 'Overflow')), name
    expected = bytearray(baseline)
    if name.startswith('loot-live-'):
        template = (ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-foreign/YTDATA.DAT').read_bytes()
        assert row['planet_template_sha256'] == digest(template), name
        for record in (4053, 4054, 4055):
            expected[(record-1)*137:record*137] = template[4052*137:4053*137]
    else:
        assert row['planet_template_sha256'] is None, name
    for patch in row['patches']:
        mbf.put(expected, patch['record'], patch['offset'], patch['value'])
    saves = {}
    for label in ('before', 'after'):
        raw = gzip.decompress((directory/(label+'.dat.gz')).read_bytes())
        assert len(raw) == 568687 and digest(raw) == row[label+'_sha256'], (name, label)
        saves[label] = raw
    before, after = saves['before'], saves['after']
    assert bytes(expected) == before, name
    g = lambda record, offset: mbf.get(after, record, offset)
    old = lambda record, offset: mbf.get(before, record, offset)
    negative = name.startswith('loot-self-') or name in ('loot-live-self-estate', 'loot-live-mine-death', 'loot-live-mine-fatal')
    if negative:
        assert g(2, 45) == g(3, 45) == 0, name
        for record in (3053, 3054, 3055, 4053, 4054, 4055):
            assert before[(record-1)*137:record*137] == after[(record-1)*137:record*137], (name, record)
        if 'mine-' in name:
            assert 'EMERGENCY WARP ENGAGED' in text and g(2, 57) != 100, name
        else:
            assert 'Missles self destructed!' in text and g(2, 49) == 499, name
    else:
        assert g(3, 45) == 2 and g(3, 57) == 0 and g(3, 89) == 0, name
        assert g(2, 49) == 500, name
        if name == 'loot-live-chain-death':
            assert g(2, 45) == 2 and g(2, 57) == 0 and g(2, 117) == 0, name
            assert [(g(r, 97), g(r, 89)) for r in (3053, 3054)] == [(0, 0), (0, 0)], name
            assert (g(3055, 97), g(3055, 89)) == (4, 555), name
            assert g(52, 129) == 60 and 'Your ship has been destroyed!' in text, name
        else:
            assert g(2, 45) == 0 and g(2, 57) == 100, name
        # Dead victim's sampled credits/weapons/cargo remain in its DOS record.
        for offset in (65, 69, 73, 77, 81, 97, 113, 121, 129):
            assert g(3, offset) == old(3, offset), (name, offset)
    if name.startswith('loot-live-'):
        for record, sector in ((4053, 110), (4054, 111), (4055, 112)):
            assert old(record, 85) == 11 and old(51+sector, 93) == record-4051, name
            assert before[(record-1)*137:record*137] == after[(record-1)*137:record*137], (name, 'active planet')
    estate = name in ('loot-estate', 'loot-estate-stale-count', 'loot-team-captain', 'loot-team-last', 'loot-own-prior-port', 'loot-estate-collect', 'loot-live-estate', 'loot-live-stale-count', 'loot-live-team-captain')
    if estate:
        stale = name in ('loot-estate-stale-count', 'loot-live-stale-count')
        assert [g(r, 97) for r in (3053, 3054)] == ([3, 3] if stale else [2, 2]), name
        collected = name == 'loot-estate-collect'
        assert [g(r, 89) for r in (3053, 3054)] == ([0, 0] if collected else [777, 333]), name
        assert (g(3055, 97), g(3055, 89)) == (2 if name == 'loot-own-prior-port' else 4, 555), name
        assert g(2, 117) == (1 if name == 'loot-own-prior-port' else 0)+(0 if stale else 2), name
        assert (g(161, 81), g(161, 85)) == (123, -2), name
        assert (g(162, 81), g(162, 85)) == (234, 4), name
        assert (g(163, 81), g(163, 85)) == (345, 2), name
        if not stale:
            assert 'The titles to 2 ports' in text, name
        assert g(3, 117) == 0, name
    if name in ('loot-team-captain', 'loot-live-team-captain', 'loot-team-last'):
        assert g(52, 77) == 3 and g(52, 109) == 0, name
        assert g(52, 117) == (0 if name == 'loot-team-last' else 4), name
    cases[name] = (before, after)

# Stable-clock scaling, zero/one boundaries and exact saved receipts.
for stock, gain in [(0, 0), (1, 0), (2, 1), (3, 2), (10, 7), (100, 76), (10000, 7675)]:
    before, after = cases[f'loot-credit-{stock}']
    assert mbf.get(after, 2, 81)-mbf.get(before, 2, 81) == gain
for name, want in {
    'loot-items': [1000, 0, 0, 0, 8680, 4, 31, 30, 2],
    'loot-holds-empty': [88, 9, 17, 30, 8680, 4, 31, 30, 2],
    'loot-holds-full': [88, 19, 17, 30, 8680, 4, 31, 30, 2],
    'loot-holds-990': [1000, 1, 3, 4, 8680, 4, 31, 30, 2],
    'loot-holds-999': [1000, 0, 0, 1, 8680, 4, 31, 30, 2],
    'loot-weapons-100': [1000, 0, 0, 0, 8680, 10, 73, 64, 45],
}.items():
    assert [mbf.get(cases[name][1], 2, o) for o in (65, 69, 73, 77, 81, 97, 113, 121, 129)] == want, name
for label, offset in [('ore', 69), ('org', 73), ('equip', 77)]:
    assert mbf.get(cases['loot-cargo-'+label][1], 2, 65) == 88
    assert mbf.get(cases['loot-cargo-'+label][1], 2, offset) == 78
assert mbf.get(cases['loot-cargo-empty'][1], 2, 65) == 88
assert mbf.get(cases['loot-credit-large'][1], 2, 81) == 176753744
assert mbf.get(cases['loot-estate-collect'][1], 2, 81) == 9790
# Research model sanity: controlled draws, no claim to original RNG replay.
draws = iter([.785, .76755, .105, .735, .645, .455])
result = rules.salvage(100, 10000, 41, 43, 47, 5, [11, 23, 37], 1000, lambda: next(draws))
assert result == dict(holds=0, credits=7675, missiles=4, plasma=31, ground=30, mines=2, cargo=[0, 0, 0])
draws = iter([.9, 0, 0, 0, 0, 0, 0, 0, 0])
assert rules.salvage(4, 0, 0, 0, 0, 0, [1, 1, 1], 10, lambda: next(draws))['cargo'] == [1, 1, 1]
print('Verified 37 DOS loot/estate cases, 74 save snapshots, active-planet controls and bounded model checks.')

# REA observed relocated load-image bytes, not raw file bytes or runtime effects.
bundle = json.loads((ROOT/'research/yt-ships/loot-rea.json').read_text())
raw = (ROOT/'archive/dos-original/YT.EXE').read_bytes()
word = lambda offset: int.from_bytes(raw[offset:offset+2], 'little')
header = word(8)*16
file_size = (word(4)-1)*512+(word(2) or 512)
loaded = bytearray(raw[header:file_size])
for index in range(word(6)):
    entry = word(24)+index*4
    offset = word(entry+2)*16+word(entry)
    value = int.from_bytes(loaded[offset:offset+2], 'little')
    loaded[offset:offset+2] = ((value+0x1000) & 0xffff).to_bytes(2, 'little')
assert len(bundle['records']) == 8
for record in bundle['records']:
    assert record['operation'] == 'read_bytes' and record['subject']['digest']['sha256'] == exe
    result = record['normalized_result']
    start = int(result['address'], 16)-0x10000
    assert result['complete'] and result['returned_bytes'] == result['requested_bytes']
    assert bytes(loaded[start:start+result['returned_bytes']]).hex() == result['bytes_hex']
print('Verified 8 REA static byte observations against the relocated original DOS load image.')
