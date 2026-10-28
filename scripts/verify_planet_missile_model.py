"""Verify shipped ground-loop bytes and independent research-model fixtures."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
sha=hashlib.sha256(raw).hexdigest()
assert sha=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
word=lambda p:int.from_bytes(raw[p:p+2],'little')
image=bytearray(raw[word(8)*16:(word(4)-1)*512+(word(2) or 512)])
for i in range(word(6)):
    table=word(24)+4*i;offset=word(table+2)*16+word(table)
    image[offset:offset+2]=((int.from_bytes(image[offset:offset+2],'little')+0x1000)&0xffff).to_bytes(2,'little')
bundle=json.loads((ROOT/'research/yt-missiles/planet-ground-rea.json').read_text())
assert len(bundle['records'])==1
row=bundle['records'][0];r=row['normalized_result']
assert row['operation']=='read_bytes' and row['subject']['digest']['sha256']==sha
assert r['address']=='0x27040' and r['complete'] and r['requested_bytes']==r['returned_bytes']==151
start=int(r['address'],16)-0x10000
assert image[start:start+151].hex()==r['bytes_hex']
spec=importlib.util.spec_from_file_location('missiles',ROOT/'research/yt-missiles/recovered_rules.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
rows=json.loads((ROOT/'internal/game/testdata/planet-ground-missiles.json').read_text())
assert len(rows)==6
for row in rows:
    ground,spent=model.planet_ground(row['Missiles'],row['Ground'],lambda:row['Draw'])
    assert ground==row['Remaining'] and spent==row['Missiles'],row['Name']
print('Verified ground-loop shipped bytes and 6 research-model fixtures; no new DOS execution.')
