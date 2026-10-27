"""Verify the bounded DOS danger-scanner/emergency-warp research evidence."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

def number(data, record, offset):
    """Decode a four-byte QuickBASIC MBF single from a one-based record."""
    start = (record - 1) * 137 + offset
    raw = data[start:start + 4]
    mantissa = int.from_bytes(raw[:3], 'little')
    if raw[3] == 0:
        return 0
    return (-1 if mantissa & 0x800000 else 1) * (1 + (mantissa & 0x7fffff)/2**23) * 2.0**(raw[3]-129)

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence', type=Path,
                    default=root / 'research/yt-navigation/encounter-dos')
args = parser.parse_args()
manifest = json.loads((args.evidence / 'results.json').read_text())
expected = {
    'danger-clear': (101, 499), 'danger-mines-no': (100, 500),
    'danger-mines-yes': (101, 499), 'danger-stacked-yes': (100, 500),
    'danger-fighters-no': (100, 500), 'danger-own-fighters': (101, 499),
    'danger-no-scanner': (101, 499), 'danger-autopilot-no': (100, 500),
    'warp-cancel': (100, 500), 'warp-default': (100, 500),
    'warp-yes': (60, 445), 'warp-one': (60, 0), 'warp-zero': (100, 0),
}
cases = manifest['scenarios']
assert len(cases) == len(expected)
assert {c['name'] for c in cases} == set(expected)
digest = lambda data: hashlib.sha256(data).hexdigest()
exe = digest((root / 'archive/dos-original/YT.EXE').read_bytes())
assert exe == 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
source = root / 'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT'
keyfeed = root / 'archive/analysis/yt-combat/KEYFEED.COM'
for case in cases:
    name = case['name']
    directory = args.evidence / name
    assert case['executable_sha256'] == exe, name
    assert case['source_sha256'] == digest(source.read_bytes()), name
    assert case['keyfeed_sha256'] == digest(keyfeed.read_bytes()), name
    for label, file in [('keys', 'KEYS.TXT'), ('transcript', 'transcript.txt')]:
        assert digest((directory / file).read_bytes()) == case[label + '_sha256'], (name, label)
    keys = ('\r~~~~~\r~' + case['command'] + '\r~~~~' + '\r' * 8 + 'Q;Y\r').encode()
    assert (directory / 'KEYS.TXT').read_bytes() == keys, name
    saves = {}
    for label in ('before', 'after'):
        data = gzip.decompress((directory / (label + '.dat.gz')).read_bytes())
        assert len(data) == 568687, name
        assert digest(data) == case[label + '_sha256'], (name, label)
        assert number(data, 2, 49) == case['turns_' + label], name
        assert number(data, 2, 57) == case['sector_' + label], name
        saves[label] = data
    before, after = saves['before'], saves['after']
    assert (case['sector_after'], case['turns_after']) == expected[name], name
    for patch in case['patches']:
        assert number(before, patch['record'], patch['offset']) == patch['value'], name
    for sector, warps in manifest['graph'].items():
        assert [number(before, 51 + int(sector), o) for o in range(41, 65, 4)] == warps + [0] * (6-len(warps)), name
    text = (directory / 'transcript.txt').read_text()
    assert 'Returning to Yankee Trader Local Logon Program' in text, name
    warning = 'Danger Scanner has detected the following in sector 101!'
    if name in {'danger-mines-no', 'danger-mines-yes', 'danger-stacked-yes',
                'danger-fighters-no', 'danger-autopilot-no'}:
        assert warning in text and '*** WARP DRIVE DEACTIVATED ***' in text, name
        assert 'Move into sector 101? [y/N]' in text, name
        if name == 'danger-fighters-no':
            assert '100 Fighters Belonging to Enemy' in text, name
        else:
            count = 1 if name == 'danger-mines-yes' else 10
            assert f'** {count} SECTOR MINES! **' in text, name
    if name in {'danger-clear', 'danger-own-fighters', 'danger-no-scanner'}:
        assert warning not in text, name
    if name in {'danger-mines-yes', 'danger-no-scanner'}:
        assert '1 EXPLODE!' in text, name
        assert number(before, 2, 53) == 10000 and number(after, 2, 53) == 9270, name
        assert number(before, 152, 129) == 1 and number(after, 152, 129) == 0, name
    if name in {'warp-yes', 'warp-one'}:
        cost = case['turns_before'] - case['turns_after']
        assert '* EMERGENCY WARP ENGAGED! *' in text, name
        assert f'sector 60. However, it takes you {cost} turns to recharge' in text, name
        assert 60 not in manifest['graph']['100'], name
    if name in {'warp-cancel', 'warp-default', 'warp-zero'}:
        assert '* EMERGENCY WARP ENGAGED! *' not in text, name

print('Verified 13 encounter DOS sessions, 26 snapshots, inputs, transcripts and source provenance.')
