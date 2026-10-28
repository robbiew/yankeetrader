"""Compare Go sector battle fixtures with the preserved readable research model.

These are model comparisons, not new DOS runs or bit-exact MBF32 emulation.
"""
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('combat',ROOT/'research/yt-combat/recovered_rules.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
rows=json.loads((ROOT/'internal/game/testdata/sector-battles.json').read_text())
for row in rows:
    result=model.surrender(row['Attackers'],row['Defenders'],row['Cloak'],lambda:row['Draw'],accept=row['Accept'],owner=row['OriginalOwner'])
    assert result==row['Expected'],row['Name']
assert len(rows)==8
print('Verified 8 sector battle fixtures against the preserved research model (no new DOS execution).')
