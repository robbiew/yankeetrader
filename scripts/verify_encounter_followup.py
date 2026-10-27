"""Verify cloak/team/warp follow-up snapshots and the bounded research models."""
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
parser.add_argument('--evidence', type=Path,
                    default=root / 'research/yt-navigation/followup-dos')
args = parser.parse_args()
manifest = json.loads((args.evidence / 'results.json').read_text())
spec = importlib.util.spec_from_file_location('rules', root / 'research/yt-navigation/encounter_rules.py')
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)


def number(data, record, offset):
    start = (record - 1) * 137 + offset
    raw = data[start:start + 4]
    mantissa = int.from_bytes(raw[:3], 'little')
    return 0 if raw[3] == 0 else (-1 if mantissa & 0x800000 else 1) * (1 + (mantissa & 0x7fffff)/2**23) * 2.0**(raw[3]-129)


digest = lambda b: hashlib.sha256(b).hexdigest()
expected = {'danger-team', 'danger-other-team', 'cloak-none', 'cloak-full', 'cloak-weak', 'cloak-half'}
expected.update(f'warp-scan-{n:02d}' for n in range(1, 17))
expected.update(f'warp-clock-{n:02d}' for n in range(1, 13))
expected.update(f'warp-look-{n:02d}' for n in (0, 1, 2, 4, 8, 16, 24, 32))
cases = manifest['scenarios']
assert len(cases) == len(expected) and {c['name'] for c in cases} == expected
exe = digest((root / 'archive/dos-original/YT.EXE').read_bytes())
assert exe == 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
source = root / 'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT'
feeder = root / 'archive/analysis/yt-combat/KEYFEED.COM'
meltdowns = 0
for case in cases:
    name = case['name']
    directory = args.evidence / name
    assert case['executable_sha256'] == exe, name
    assert case['source_sha256'] == digest(source.read_bytes()), name
    assert case['keyfeed_sha256'] == digest(feeder.read_bytes()), name
    for label, file in [('keys', 'KEYS.TXT'), ('transcript', 'transcript.txt')]:
        assert digest((directory / file).read_bytes()) == case[label + '_sha256'], (name, label)
    assert digest((directory / 'dosbox.log').read_bytes()) == case['dosbox_log_sha256'], name
    assert (directory / 'KEYS.TXT').read_bytes().startswith(('\r~~~~~\r~' + case['command'] + '\r').encode()), name
    assert case['dos_time'] == (f'{int(name[-2:]):02d}:00:00' if name.startswith('warp-clock-') else '00:00:00'), name
    saves = {}
    for label in ('before', 'after'):
        data = gzip.decompress((directory / (label + '.dat.gz')).read_bytes())
        assert len(data) == 568687 and digest(data) == case[label + '_sha256'], (name, label)
        assert number(data, 2, 49) == case['turns_' + label], name
        assert number(data, 2, 57) == case['sector_' + label], name
        saves[label] = data
    before, after = saves['before'], saves['after']
    assert (case['sector_before'], case['turns_before']) == (100, 500), name
    for sector, warps in manifest['graph'].items():
        assert [number(before, 51 + int(sector), o) for o in range(41, 65, 4)] == warps + [0] * (6-len(warps)), name
    for patch in case['patches']:
        # Fractional MBF values are quantized; compare their representation's tolerance.
        actual = number(before, patch['record'], patch['offset'])
        assert abs(actual - patch['value']) <= abs(patch['value']) * 1e-7, name
    text = (directory / 'transcript.txt').read_text()
    assert 'Returning to Yankee Trader Local Logon Program' in text, name
    if name.startswith('cloak-'):
        assert (case['sector_after'], case['turns_after']) == (100, 500), name
        assert number(after, 3, 125) == number(before, 3, 125), name
        scans = re.findall(r'\[ Sensors Activated \](.*?)\[ End Sensor Scan \]', text, re.S)
        visible = ['Enemy  - Fighters: 42 - Shields: 7' in scan for scan in scans]
        expected_visible = {'cloak-none': [True], 'cloak-full': [False],
                            'cloak-weak': [True, True], 'cloak-half': [False, True, True]}
        assert visible == expected_visible[name], (name, visible)
        assert text.count('You detect the shimmering of a cloaking device!') == (1 if name in {'cloak-weak', 'cloak-half'} else 0), name
    elif name.startswith('danger-'):
        warning = 'Danger Scanner has detected the following in sector 101!'
        friendly = name == 'danger-team'
        assert (warning not in text) if friendly else (warning in text), name
        assert (case['sector_after'], case['turns_after']) == ((101, 499) if friendly else (100, 500)), name
        assert number(after, 2, 61) == number(before, 2, 61), name
        assert number(after, 152, 81) == 100 and number(after, 152, 85) == 3, name
    else:
        if name.startswith('warp-scan-'):
            assert text.count('[ Sensors Activated ]') == int(name[-2:]), name
        assert text.count('* EMERGENCY WARP ENGAGED! *') == 1, name
        gauge = re.search(r'={32}\s*\[([*]*)', text)
        assert gauge is not None, name
        heat = len(gauge[1])
        meltdown = 'MELT DOWN!' in text
        assert meltdown == (heat == 31), (name, heat)
        assert 1 <= case['sector_after'] <= 3000, name
        if meltdown:
            meltdowns += 1
            assert case['turns_after'] == 0 and 'Your engines are disabled!' in text, name
            assert f"You are stranded in sector {case['sector_after']}." in text, name
        else:
            match = re.search(r'sector (\d+)\. However, it takes you (\d+) turns to recharge', text)
            assert match is not None, name
            destination, cost = map(int, match.groups())
            assert destination == case['sector_after'] and cost == 500 - case['turns_after'], name
            assert 4 * heat <= cost <= 4 * heat + 3, (name, heat, cost)
assert meltdowns > 0, 'Need a completed natural meltdown to close this boundary'

# These independent branches exercise the model; they do not emulate DOS RNG.
assert rules.sensor_visibility(1, .999) == (False, False, 1)
assert rules.sensor_visibility(.5, .5) == (False, False, .5)
assert rules.sensor_visibility(.5, .6) == (True, True, 0)
assert rules.sensor_visibility(0, .9) == (True, False, 0)
draws = iter([.1, .1] + [.9] * 14 + [.25, .99, .75])
assert rules.emergency_warp(500, 3000, lambda: next(draws)) == {'heat': 14, 'destination': 751, 'cost': 59, 'meltdown': False}
draws = iter([.1, .1] + [.9] * 14 + [.25, .01, .75])
assert rules.emergency_warp(1, 3000, lambda: next(draws))['cost'] == 1
draws = iter([.9, .9] + [.9] * 31 + [.25, .99, .75])
assert rules.emergency_warp(500, 3000, lambda: next(draws)) == {'heat': 31, 'destination': 751, 'cost': 500, 'meltdown': True}
print(f'Verified {len(cases)} follow-up DOS sessions, {len(cases)*2} snapshots, {meltdowns} natural meltdowns and research model branches.')
