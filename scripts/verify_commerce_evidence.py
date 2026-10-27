"""Verify DOS commerce utilities, spy purchases/reconnect and radio delivery."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence', type=Path, default=root / 'research/yt-navigation/commerce-dos')
args = parser.parse_args()
manifest = json.loads((args.evidence / 'results.json').read_text())


def number(data, record, offset):
    start = (record-1)*137 + offset
    raw = data[start:start+4]
    mantissa = int.from_bytes(raw[:3], 'little')
    return 0 if raw[3] == 0 else (-1 if mantissa & 0x800000 else 1) * (1 + (mantissa & 0x7fffff)/2**23) * 2.0**(raw[3]-129)


expected = {f'commerce-{n}' for n in ('nearest-all', 'nearest-ore', 'nearest-team',
    'pairs-oneway', 'pairs-twoway', 'profit-empty', 'profit-ports', 'profit-small')}
expected.update(f'intel-{n}' for n in ('hire-one', 'hire-three', 'limit-four', 'reconnect'))
expected.update(f'radio-{n}' for n in ('send', 'abort', 'log-empty', 'team-denied', 'read', 'read-again'))
cases = {c['name']: c for c in manifest['scenarios']}
assert len(manifest['scenarios']) == len(expected) and set(cases) == expected
digest = lambda data: hashlib.sha256(data).hexdigest()
exe = digest((root / 'archive/dos-original/YT.EXE').read_bytes())
assert exe == 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
source = root / 'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT'
feeder = root / 'archive/analysis/yt-combat/KEYFEED.COM'
links = {'intel-reconnect': 'intel-hire-one', 'radio-read': 'radio-send', 'radio-read-again': 'radio-read'}
mail = {}
for name, case in cases.items():
    directory = args.evidence / name
    player = 3 if name.startswith('radio-read') else 2
    assert case['player_record'] == player and case['actor'] == ('ENEMY' if player == 3 else 'TESTER'), name
    assert case['executable_sha256'] == exe and case['keyfeed_sha256'] == digest(feeder.read_bytes()), name
    assert case['dos_time'] == '00:00:00', name
    if name in links:
        parent = cases[links[name]]
        assert case['source_sha256'] == parent['after_sha256'] == case['before_sha256'], name
    else:
        assert case['source_sha256'] == digest(source.read_bytes()), name
    for label, file in [('keys', 'KEYS.TXT'), ('transcript', 'transcript.txt'), ('dosbox_log', 'dosbox.log')]:
        assert digest((directory/file).read_bytes()) == case[label+'_sha256'], (name, label)
    assert (directory/'KEYS.TXT').read_bytes().startswith(('\r~~~~~\r~'+case['command']+'\r').encode()), name
    saves = {}
    for label in ('before', 'after'):
        data = gzip.decompress((directory/(label+'.dat.gz')).read_bytes())
        assert len(data) == 568687 and digest(data) == case[label+'_sha256'], (name, label)
        assert number(data, player, 49) == case['turns_'+label], name
        assert number(data, player, 57) == case['sector_'+label], name
        saves[label] = data
    before, after = saves['before'], saves['after']
    overrides = {(p['record'], p['offset']): p['value'] for p in case['patches']}
    for (record, offset), value in overrides.items():
        assert number(before, record, offset) == value, name
    for sector, warps in case['graph'].items():
        record = 51+int(sector)
        want = [overrides.get((record,o), v) for o,v in zip(range(41,65,4),warps+[0]*(6-len(warps)))]
        assert [number(before,record,o) for o in range(41,65,4)] == want, name
    assert case['sector_before'] == case['sector_after'], name
    assert number(after,player,45) == 0, name
    for offset in (53,61,65,69,73,77,93,97,113,125):
        assert number(before,player,offset) == number(after,player,offset), (name,offset)
    auxiliary = {}
    for filename, hashes in case['auxiliary'].items():
        auxiliary[filename] = {}
        for label in ('before','after'):
            raw = gzip.decompress((directory/f'{filename}.{label}.gz').read_bytes())
            assert digest(raw) == hashes[label+'_sha256'], (name,filename,label)
            auxiliary[filename][label] = raw
    mail[name] = auxiliary['YTRMSG.DAT']
    text = (directory/'transcript.txt').read_text()
    assert 'Returning to Yankee Trader Local Logon Program' in text, name
    if name.startswith('commerce-'):
        assert (case['turns_before'],case['turns_after']) == (500,500), name
        assert number(before,2,81) == number(after,2,81), name
        assert {s:int(number(before,51+s,65)) for s in range(1,3001) if number(before,51+s,65)} == {101:2,107:3}, name
        body = text.split('<Computer activated>')[1].split('<Quit>')[0]
        if name == 'commerce-nearest-all':
            assert re.findall(r'Distance: (\d+)\s+Sector: (\d+)',body) == [('1','101'),('2','107')], name
            assert '101  B Ore @ 10  S Org @ 44' in body and '107  S Ore @ 30  B Org @ 15' in body, name
        elif name == 'commerce-nearest-ore':
            assert re.findall(r'Distance: (\d+)\s+Sector: (\d+)',body) == [('2','107')], name
        elif name == 'commerce-nearest-team':
            assert 'You dont belong to a team!' in body, name
        elif name == 'commerce-profit-empty':
            assert 'NO trading port in your sector!' in body, name
        else:
            assert re.findall(r'101, 107 Org -> Ore @ Profit of (\d+)',body) == ['49'], name
            assert 49 == (44-15)+(30-10)
            if name == 'commerce-pairs-oneway':
                assert 101 not in [number(before,158,o) for o in range(41,65,4)], name
    elif name.startswith('intel-'):
        if name in {'intel-hire-one','intel-hire-three'}:
            count = 1 if name.endswith('one') else 3
            assert number(before,2,81)-number(after,2,81) == 333000*count, name
            assert (case['turns_before'],case['turns_after']) == (500,499), name
            body = text.split('<Computer activated>')[1].split('<Quit>')[0]
            assert re.findall(r'Spy # (\d+) will hunt in sector (\d+)\.',body) == [(str(n),str(100+n)) for n in range(1,count+1)], name
        else:
            assert number(before,2,81) == number(after,2,81), name
            assert 'You do not have any spies!' in text, name
            assert (case['turns_before'],case['turns_after']) == ((499,499) if name.endswith('reconnect') else (500,499)), name
            if name == 'intel-limit-four':
                assert 'Max spies allowed is 3!' in text, name
    else:
        assert case['turns_before'] == case['turns_after'] == 500, name
        assert number(before,player,81) == number(after,player,81), name
        if name == 'radio-send':
            assert 'Transmission successful!' in text, name
            assert mail[name]['before'] == b'' and len(mail[name]['after']) == 86, name
            assert [number(mail[name]['after'],1,o) for o in (0,4,8)] == [1,3,2], name
            assert mail[name]['after'][12:].rstrip() == b'YT RADIO PROBE', name
        elif name == 'radio-read':
            assert text.count('YT RADIO PROBE') == 2 and 'Message to: Enemy  * From: Q ' in text, name
            assert number(mail[name]['before'],1,0) == 1 and number(mail[name]['after'],1,0) == 0, name
            assert mail[name]['before'][4:] == mail[name]['after'][4:], name
        else:
            assert mail[name]['before'] == mail[name]['after'], name
            assert 'Transmission successful!' not in text, name
            if name == 'radio-read-again':
                assert 'YT RADIO PROBE' not in text.split('<Computer activated>')[0], name
                assert text.count('YT RADIO PROBE') == 1 and 'Log of messages sent/recieved.' in text, name
            elif name == 'radio-team-denied':
                assert "You Don't belong to a team!" in text, name
for child,parent in links.items():
    assert mail[child]['before'] == mail[parent]['after'], child
    for filename,hashes in cases[child]['auxiliary'].items():
        assert hashes['before_sha256'] == cases[parent]['auxiliary'][filename]['after_sha256'], (child,filename)
print(f'Verified {len(cases)} DOS commerce/spy/radio sessions, {len(cases)*2} world snapshots, auxiliary snapshots and exact reconnect/delivery chains.')
