"""Verify secret-free membership fixtures against preserved DOS team evidence."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
archive = root/'archive/analysis/yt-combat/experiments'
manifest = json.loads((root/'archive/analysis/yt-teams/scenarios.json').read_text())


def number(data, record, offset):
    start = (record-1)*137+offset
    raw = data[start:start+4]
    value = int.from_bytes(raw[:3], 'little')
    return int(0 if raw[3] == 0 else (-1 if value & 0x800000 else 1) *
               (1+(value & 0x7fffff)/2**23)*2.**(raw[3]-129))


rows = []
for name in ('create-confirm', 'join', 'wrong', 'full', 'quit', 'banish',
             'member-privilege', 'password', 'last', 'promote', 'rejoin',
             'successor', 'short-name', 'lowercase'):
    case = 'team-'+name
    directory = archive/case
    spec = manifest['validated'][case]
    row = {'Name': case, 'Actor': 3 if spec['player'].upper() == 'ENEMY' else 2}
    for label, filename in [('Before', 'before.dat'), ('After', 'YTDATA.DAT')]:
        data = (directory/filename).read_bytes()
        assert len(data) == 4151*137, case
        assert hashlib.sha256(data).hexdigest() == spec[label.lower()+'_sha256'], case
        row[label] = {
            'Members': {str(i): number(data, i, 89) for i in range(2, 7)},
            'Captain': number(data, 52, 77),
            'Roster': [number(data, 52, offset) for offset in (109, 117, 121, 125)],
            'Name': data[51*137:51*137+41].decode('ascii').strip(),
            'Credits': number(data, row['Actor'], 81),
            'Turns': number(data, row['Actor'], 49),
        }
        members = sorted(int(i) for i, team in row[label]['Members'].items() if team == 1)
        roster = sorted(i for i in row[label]['Roster'] if i)
        if name == 'promote':
            # This controlled DOS fixture deliberately leaves the former
            # captain in the cached roster after removing their membership.
            assert members == [3] and roster == [2, 3], (case, label)
        else:
            assert members == roster, (case, label)
    rows.append(row)
assert rows == json.loads((root/'internal/game/testdata/dos-teams.json').read_text()), 'Go fixtures differ from archived DOS results'
print('Verified 14 DOS team membership cases and 28 archived save hashes against Go fixtures.')
