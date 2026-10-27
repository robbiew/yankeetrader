"""Verify original DOS disruption, mine damage and automatic escape evidence."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence', type=Path, default=root / 'research/yt-navigation/hazard-dos')
args = parser.parse_args()
manifest = json.loads((args.evidence / 'results.json').read_text())


def number(data, record, offset):
    start = (record - 1) * 137 + offset
    raw = data[start:start + 4]
    mantissa = int.from_bytes(raw[:3], 'little')
    return 0 if raw[3] == 0 else (-1 if mantissa & 0x800000 else 1) * (1 + (mantissa & 0x7fffff)/2**23) * 2.0**(raw[3]-129)


digest = lambda data: hashlib.sha256(data).hexdigest()
exe = digest((root / 'archive/dos-original/YT.EXE').read_bytes())
assert exe == 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
source = root / 'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT'
feeder = root / 'archive/analysis/yt-combat/KEYFEED.COM'
expected = {f'hazard-disrupt-{s}' for s in ('scan', 'no', 'yes', 'bare', 'last')}
expected.update(f'hazard-{kind}-clock-{n:02d}' for kind in ('shield', 'bare') for n in range(1, 13))
expected.update(f'hazard-small-clock-{n:02d}' for n in range(1, 13))
expected.update(f'hazard-burst-clock-{n:02d}' for n in range(1, 5))
expected.add('hazard-ten-holds')
cases = manifest['scenarios']
assert len(cases) == len(expected) and {c['name'] for c in cases} == expected
shield_losses = escapes = 0
for case in cases:
    name = case['name']
    directory = args.evidence / name
    assert case['executable_sha256'] == exe, name
    assert case['source_sha256'] == digest(source.read_bytes()), name
    assert case['keyfeed_sha256'] == digest(feeder.read_bytes()), name
    for label, file in [('keys', 'KEYS.TXT'), ('transcript', 'transcript.txt'), ('dosbox_log', 'dosbox.log')]:
        assert digest((directory / file).read_bytes()) == case[label + '_sha256'], (name, label)
    assert (directory / 'KEYS.TXT').read_bytes().startswith(('\r~~~~~\r~' + case['command'] + '\r').encode()), name
    assert case['dos_time'] == (f'{int(name[-2:]):02d}:00:00' if 'clock-' in name else '00:00:00'), name
    saves = {}
    for label in ('before', 'after'):
        data = gzip.decompress((directory / (label + '.dat.gz')).read_bytes())
        assert len(data) == 568687 and digest(data) == case[label + '_sha256'], (name, label)
        assert number(data, 2, 49) == case['turns_' + label], name
        assert number(data, 2, 57) == case['sector_' + label], name
        saves[label] = data
    before, after = saves['before'], saves['after']
    for patch in case['patches']:
        assert number(before, patch['record'], patch['offset']) == patch['value'], name
    for sector, warps in case['graph'].items():
        assert [number(before, 51 + int(sector), o) for o in range(41, 65, 4)] == warps + [0] * (6-len(warps)), name
    text = (directory / 'transcript.txt').read_text()
    assert 'Returning to Yankee Trader Local Logon Program' in text, name
    warp_count = text.count('* EMERGENCY WARP ENGAGED! *')
    costs = [int(n) for n in re.findall(r'it takes you (\d+) turns to recharge', text)]
    if name.startswith('hazard-disrupt-'):
        assert number(after, 2, 93) == number(before, 2, 93), name
        assert number(after, 2, 53) == number(before, 2, 53), name
        assert case['sector_before'] == 1 and case['turns_before'] == (1 if name.endswith('last') else 500), name
        assert number(before, 1, 57) - number(before, 1, 53) == 2, name
        if name.endswith('scan'):
            scan = text.split('[ Sensors Activated ]')[1].split('[ End Sensor Scan ]')[0]
            assert 'Sector: 2' in scan and '** Space-time disruption detected! **' in scan, name
        if name.endswith(('scan', 'no')):
            assert (case['sector_after'], case['turns_after']) == (1, 500) and warp_count == 0, name
        else:
            assert case['sector_after'] == 1 and warp_count >= 1, name
            assert 'A *-BLACK HOLE-* grabs you!' in text, name
            assert 'Are you sure you wish to do this?' not in text, name
        if name.endswith(('no', 'yes', 'last')):
            assert '** Space-time disruption! **' in text and 'Move into sector 2? [y/N]' in text, name
        if name.endswith('bare'):
            assert 'Danger Scanner has detected' not in text, name
    else:
        assert number(before, 2, 45) == 0 and number(after, 2, 45) == 0, name
        assert (case['sector_before'], case['turns_before']) == (100, 500), name
        assert '1 EXPLODE!' in text and number(after, 152, 129) == 0, name
        assert number(before, 2, 93) == -1, name
        destroyed = 'Danger scanner destroyed!' in text
        assert number(after, 2, 93) == (0 if destroyed else -1), name
        if name.startswith(('hazard-shield-', 'hazard-burst-')):
            assert 0 < number(after, 2, 53) < number(before, 2, 53), name
            assert number(after, 2, 65) == number(before, 2, 65), name
            assert number(after, 2, 61) == number(before, 2, 61), name
            shield_losses += destroyed
            if name.startswith('hazard-burst-'):
                assert text.count('EXPLODE!') == 19 and '2 EXPLODE!' in text, name
        else:
            assert number(after, 2, 53) == 0 and destroyed, name
        assert 'Are you sure you wish to do this?' not in text, name
        escapes += warp_count > 0
        if warp_count:
            assert number(after, 2, 65) < 10, name
        if not warp_count:
            assert (case['sector_after'], case['turns_after']) == (101, 499), name
    if 'MELT DOWN!' in text:
        assert case['turns_after'] == 0, name
    else:
        movement_cost = 0 if name.endswith(('disrupt-scan', 'disrupt-no')) else 1
        assert len(costs) == warp_count, name
        assert case['turns_after'] == case['turns_before'] - movement_cost - sum(costs), name
assert shield_losses > 0, 'Need observed scanner destruction through surviving shields'
assert escapes > 0, 'Need an observed automatic mine escape'

spec = importlib.util.spec_from_file_location('rules', root / 'research/yt-navigation/encounter_rules.py')
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)
assert rules.disruption_sector(2, .999) == 2
assert rules.disruption_sector(3000, 0) == 2
assert rules.disruption_sector(3000, .999999) == 2999
assert rules.scanner_after_mine(True, False, 100, .95)
assert not rules.scanner_after_mine(True, False, 100, .951)
assert rules.scanner_after_mine(True, False, 0, .999)
assert not rules.scanner_after_mine(True, True, 0, 0)
assert rules.automatic_mine_escape(9, .99)
assert not rules.automatic_mine_escape(10, .8)
assert not rules.automatic_mine_escape(10, .801)
print(f'Verified {len(cases)} DOS hazard sessions, {len(cases)*2} snapshots, {shield_losses} shielded scanner losses and {escapes} automatic mine escapes.')
