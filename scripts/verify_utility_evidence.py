"""Verify DOS computer access/report rules and faction fighter encounters."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence', type=Path, default=root / 'research/yt-navigation/utility-dos')
args = parser.parse_args()
manifest = json.loads((args.evidence / 'results.json').read_text())


def number(data, record, offset):
    start = (record - 1) * 137 + offset
    raw = data[start:start + 4]
    mantissa = int.from_bytes(raw[:3], 'little')
    return 0 if raw[3] == 0 else (-1 if mantissa & 0x800000 else 1) * (1 + (mantissa & 0x7fffff)/2**23) * 2.0**(raw[3]-129)


expected = {f'utility-{n}' for n in ('menu', 'fighters', 'planets', 'planets-foreign',
    'port-known', 'port-empty', 'port-guarded', 'planet-report', 'planet-private',
    'planet-owned', 'planet-unguarded', 'planet-guarded', 'treasury', 'spies')}
expected.update(f'npc-{n}' for n in ('merc-attack', 'xannor-attack', 'human-surrender',
    'merc-bribe', 'merc-cancel', 'human-bribe', 'xannor-bribe', 'warp-cancel', 'warp-escape'))
cases = manifest['scenarios']
assert len(cases) == len(expected) and {c['name'] for c in cases} == expected
digest = lambda data: hashlib.sha256(data).hexdigest()
exe = digest((root / 'archive/dos-original/YT.EXE').read_bytes())
assert exe == 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
source = root / 'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT'
feeder = root / 'archive/analysis/yt-combat/KEYFEED.COM'
for case in cases:
    name = case['name']
    directory = args.evidence / name
    assert case['executable_sha256'] == exe and case['source_sha256'] == digest(source.read_bytes()), name
    assert case['keyfeed_sha256'] == digest(feeder.read_bytes()) and case['dos_time'] == '00:00:00', name
    for label, file in [('keys', 'KEYS.TXT'), ('transcript', 'transcript.txt'), ('dosbox_log', 'dosbox.log')]:
        assert digest((directory / file).read_bytes()) == case[label + '_sha256'], (name, label)
    assert (directory / 'KEYS.TXT').read_bytes().startswith(('\r~~~~~\r~' + case['command'] + '\r').encode()), name
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
        assert [number(before, 51+int(sector), o) for o in range(41, 65, 4)] == warps + [0]*(6-len(warps)), name
    text = (directory / 'transcript.txt').read_text()
    assert 'Returning to Yankee Trader Local Logon Program' in text, name
    assert (case['sector_before'], case['turns_before']) == (100, 500), name
    assert number(before, 2, 45) == number(after, 2, 45) == 0, name
    if name.startswith('utility-'):
        turns = 499 if name == 'utility-planet-guarded' else 500
        assert (case['sector_after'], case['turns_after']) == (100, turns), name
        for offset in (53, 61, 65, 69, 73, 77, 81, 93, 97, 113, 125):
            assert number(before, 2, offset) == number(after, 2, offset), (name, offset)
        body = text.split('<Computer activated>')[1].split('<Quit>')[0]
        if name == 'utility-menu':
            for label in ('17) Check Profits of Adjacent Ports', '11) Fighter Finder (Yours)', '15) Show Active Spies'):
                assert label in body, name
        elif name == 'utility-fighters':
            rows = re.findall(r'^\s*(\d+)\s+(\d+)\s*$', body, re.M)
            assert rows == [('101', '123'), ('106', '789')], (name, rows)
            assert '456' not in body, name
        elif name == 'utility-planets':
            assert re.search(r'Planet: Test Planet\s+Sector: 102', body), name
        elif name == 'utility-planets-foreign':
            assert 'None found!' in body and 'Planet: Test Planet' not in body, name
        elif name in {'utility-port-empty', 'utility-port-guarded', 'utility-planet-guarded'}:
            assert 'No information available.' in body, name
            assert 'Production' not in body and 'Commerce report' not in body, name
        elif name == 'utility-port-known':
            assert 'Commerce report for Test Port:' in body, name
            assert re.search(r'Ore\.+\s+Selling\s+1000\s+10\s+10', body), name
        elif name == 'utility-planet-private':
            assert 'Planet: Test Planet -*- Ground Forces: 12' in body, name
            assert 'Production' not in body and 'Credits......' not in body, name
        elif name in {'utility-planet-report', 'utility-planet-owned', 'utility-planet-unguarded'}:
            assert 'Planet: Test Planet' in body and 'Production' in body, name
            assert re.search(r'Credits\.+\s+99\s+10000\s+100000', body), name
        elif name == 'utility-treasury':
            assert "You don't OWN any ports!!!" in body, name
        elif name == 'utility-spies':
            assert 'You do not have any spies!' in body, name
    else:
        assert number(before, 2, 61) == 2000 and number(before, 152, 81) == 100, name
        if name == 'npc-warp-escape':
            match = re.search(r'sector (\d+)\. However, it takes you (\d+) turns to recharge', text)
            assert match is not None and '* EMERGENCY WARP ENGAGED! *' in text, name
            sector, cost = map(int, match.groups())
            assert (case['sector_after'], case['turns_after']) == (sector, 499-cost), name
        else:
            assert (case['sector_after'], case['turns_after']) == (101, 499), name
        assert number(after, 2, 81) == (50000 if name == 'npc-merc-bribe' else 100000), name
        if name in {'npc-merc-attack', 'npc-xannor-attack', 'npc-xannor-bribe'}:
            lost = int(re.search(r'You lost (\d+) fighter\(s\)', text)[1])
            assert number(after, 2, 61) == 2000-lost, name
            assert 'You destroyed 100 enemy fighters.' in text, name
            assert number(after, 152, 81) == number(after, 152, 85) == 0, name
            assert 'WE WISH TO SURRENDER!!!' not in text, name
        elif name in {'npc-human-surrender', 'npc-merc-bribe'}:
            assert number(after, 2, 61) == 2100, name
            assert number(after, 152, 81) == number(after, 152, 85) == 0, name
            assert ('100 fighters surrendered!' if name == 'npc-human-surrender' else 'Good Deal! We join up with you!') in text, name
        else:
            assert number(after, 2, 61) == 2000 and number(after, 152, 81) == 100, name
            assert number(after, 152, 85) == number(before, 152, 85), name
        if name in {'npc-human-bribe', 'npc-xannor-bribe'}:
            assert "We don't accept no Bribes" in text, name
        if name == 'npc-warp-cancel':
            assert '* EMERGENCY WARP ENGAGED! *' not in text, name
print(f'Verified {len(cases)} DOS utility/NPC sessions, {len(cases)*2} snapshots, report access/costs and fighter/credit conservation.')
