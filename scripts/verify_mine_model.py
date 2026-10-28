"""Check static evidence identity and independently generated injected-RNG fixtures."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
raw = (ROOT/'archive/dos-original/YT.EXE').read_bytes()
sha = hashlib.sha256(raw).hexdigest()
assert sha == 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
word = lambda p: int.from_bytes(raw[p:p+2], 'little')
header = word(8)*16
size = (word(4)-1)*512+(word(2) or 512)
image = bytearray(raw[header:size])
for i in range(word(6)):
    table = word(24)+4*i
    offset = word(table+2)*16+word(table)
    value = int.from_bytes(image[offset:offset+2], 'little')
    image[offset:offset+2] = ((value+0x1000) & 0xffff).to_bytes(2,'little')
bundle = json.loads((ROOT/'research/yt-ships/mines-rea.json').read_text())
assert len(bundle['records']) == 6
for row in bundle['records']:
    assert row['operation'] == 'read_bytes' and row['subject']['digest']['sha256'] == sha
    r = row['normalized_result']; start = int(r['address'],16)-0x10000
    assert r['complete'] and r['requested_bytes'] == r['returned_bytes']
    assert image[start:start+r['returned_bytes']].hex() == r['bytes_hex']
spec = importlib.util.spec_from_file_location('mine_rules', ROOT/'research/yt-ships/mine_rules.py')
rules = importlib.util.module_from_spec(spec); spec.loader.exec_module(rules)
fixtures = json.loads((ROOT/'internal/game/testdata/mine-model.json').read_text())
assert len(fixtures) == 8
for f in fixtures:
    actual, used = rules.burst(f['Player'],f['Burst'],f['Draws'])
    assert actual == f['Expected'] and used == len(f['Draws']), f['Name']
print('Verified 6 original-image REA byte observations and 8 injected-RNG mine burst model comparisons; not new DOS sessions.')
