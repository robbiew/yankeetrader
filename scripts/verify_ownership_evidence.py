"""Verify the nine DOS ownership snapshots and their executable Go fixtures."""
import gzip
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
evidence = root / 'research/yt-trade/ownership-dos'
manifest = json.loads((evidence / 'results.json').read_text())
golden = json.loads((root / 'internal/game/testdata/dos-ownership.json').read_text())
digest = lambda b: hashlib.sha256(b).hexdigest()
exe = digest((root / 'archive/dos-original/YT.EXE').read_bytes())
assert exe == 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'

def number(data, record, offset):
    start = (record-1)*137 + offset
    raw = data[start:start+4]
    v = int.from_bytes(raw[:3], 'little')
    return 0 if raw[3] == 0 else (-1 if v & 0x800000 else 1)*(1+(v & 0x7fffff)/2**23)*2.**(raw[3]-129)

expected = {'ownership-'+n for n in ('buyout','buy-collect','cancel','default','poor','unowned','self','collect','report')}
assert len(manifest['scenarios']) == len(golden) == 9
assert {c['name'] for c in manifest['scenarios']} == expected
rows = []
for case in manifest['scenarios']:
    name = case['name']; d = evidence / name
    assert case['executable_sha256'] == exe
    assert case['source_sha256'] == digest((root/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes())
    assert case['keyfeed_sha256'] == digest((root/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes())
    assert (d/'KEYS.TXT').read_bytes().startswith(('\r~~~~~\r~'+case['command']+'\r').encode())
    for key, filename in [('keys','KEYS.TXT'),('transcript','transcript.txt'),('dosbox_log','dosbox.log')]:
        assert digest((d/filename).read_bytes()) == case[key+'_sha256'], (name,key)
    assert 'Returning to Yankee Trader Local Logon Program' in (d/'transcript.txt').read_text(), name
    row = {'Name': name}; saves = {}
    for label in ('before','after'):
        b = gzip.decompress((d/(label+'.dat.gz')).read_bytes()); saves[label] = b
        assert digest(b) == case[label+'_sha256'] and len(b) == 568687, name
        assert number(b,2,49) == 500 and number(b,2,57) == case['sector_'+label], name
        for key,r,o in [('Buyer',2,81),('Seller',3,81),('Treasury',3053,89),('Owner',3053,97)]:
            row[key+label.title()] = int(number(b,r,o))
    before,after = saves['before'],saves['after']
    for patch in case['patches']:
        assert number(before,patch['record'],patch['offset']) == patch['value'], (name,patch)
    if name in {'ownership-buyout','ownership-buy-collect','ownership-unowned'}:
        assert row['BuyerBefore']-row['BuyerAfter'] == 31
        assert row['OwnerAfter'] == 2 and row['TreasuryAfter'] == 0
        assert number(after,2,117) == number(before,2,117)+1
        if name != 'ownership-unowned':
            assert row['SellerAfter']-row['SellerBefore'] == 808
            assert number(after,3,117) == number(before,3,117)-1
    elif name == 'ownership-collect':
        assert row['BuyerAfter']-row['BuyerBefore'] == 777 and row['TreasuryAfter'] == 0
    else:
        assert all(row[key+'Before'] == row[key+'After'] for key in ('Buyer','Seller','Treasury','Owner')), name
    if row['OwnerBefore']:
        assert sum(row[k+'Before'] for k in ('Buyer','Seller','Treasury')) == sum(row[k+'After'] for k in ('Buyer','Seller','Treasury')), name
    rows.append(row)
assert rows == golden, 'Go fixtures differ from the DOS snapshots'
print('Verified 9 DOS ownership cases, 18 save snapshots, transcripts and Go fixtures.')
