"""Independently verify retained inputs to bounded maintenance record replay.

No acquisition or replay model is imported. Immutable raw pins, independently
reconstructed diagnostics, native bytes and cross-profile semantics are distinct
checks. The measured port606 timestamp perturbation is retained, not fitted away.
"""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

import verify_maintenance_sequence as sequence
from verify_initial_maintenance import PINS as INITIAL_PINS
from verify_maintenance_rng import MAINT_BANNER, verify_launch
from verify_rng_clock import read_date, read_time
from verify_rng_native import image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'research/yt-maint/record-input-controls'
NATIVE = ROOT / 'research/yt-maint/record-replay-native'
PINS_FILE = ROOT / 'research/yt-maint/record-replay-pins.json'
PINS_SHA = 'd2a6aa1d1209cd6b795c1aab76e42e666ecab12f6df130ae9a21c5182e156864'
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINARIES = sequence.BINARIES
COMMON = sequence.COMMON
DATA_FILES = sequence.DATA_FILES
PORTS = (1, 2, 500, 562, 593, 601, 604, 605, 606, 607, 609, 625, 750, 999, 1000)
READONLY_PORTS = (1, 605, 606, 607, 1000)
NATIVE_CONTRACTS = {
    'npc': {'0x11d9d': 436, '0x1213d': 677, '0x141c1': 695},
    'ports': {'0x107bf': 1928},
    'aux': {'0x15773': 61, '0x18234': 192, '0x17ed0': 129, '0x18534': 1202,
            '0x19b50': 1240, '0x18c90': 2130, '0x168b3': 107,
            '0x194e0': 128, '0x19b2a': 12, '0x18148': 236},
}


def mbf_integer(n):
    assert type(n) is int and 1 <= n <= 1000
    exponent = n.bit_length()
    return (n * (1 << (24 - exponent)) - (1 << 23)).to_bytes(3, 'little') + bytes([128 + exponent])


def expected_matrix():
    rows = {'entry/untouched': (None, 65535, 0x234),
            'entry/untouched-repeat': (None, 65535, 0x234),
            'entry/xannoron-timer': (0x218e, 1, 0x1a),
            'entry/startup-timer': (0x7d, 1, 0x1a),
            'port-default/untouched': (None, 65535, 0x234),
            'port-default/count-clock': (0x934, 65535, 0x1a),
            'port-readonly/untouched': (None, 65535, 0x234),
            'port-readonly/miss': (0x934, 65535, 0x1a)}
    rows.update({f'port-default/port-{n:04}': (0x934, n, 0x1a) for n in PORTS})
    rows.update({f'port-readonly/port-{n:04}': (0x934, 65535, 0x1a) for n in READONLY_PORTS})
    assert len(rows) == 28
    return rows


def reconstructed_readonly(original, target):
    """Independent386 CMP gate; no mutable counter or fixture bytes are used."""
    assert isinstance(target, bytes) and len(target) == 4, 'read-only comparison operand'
    site = 0x934
    displaced = original[512 + site:517 + site]
    assert displaced == bytes.fromhex('cd3f7d9090'), 'safe five-byte timestamp store boundary'
    # Entry44: normal-return guard prints CS:0000. Hook4b: save flags, compare
    # the four-byte MBF port-index variable DS7ad6 with the selected immediate.
    # On mismatch restore flags, run the displaced instruction and continue.
    diagnostic = bytes.fromhex('0e1fba0000eb0f9c66813ed67a') + target
    diagnostic += bytes.fromhex('7512ba1a00bb0100b90400b440cd21b8004ccd219d')
    diagnostic += displaced + b'\xe9' + struct.pack('<H', (site + 5 - 0x72) & 65535)
    assert len(diagnostic) == 46, 'read-only diagnostic extent'
    out = bytearray(original)
    out[0x244:0x272] = diagnostic
    out[512 + site:517 + site] = b'\xe9' + struct.pack('<H', (0x4b - site - 3) & 65535) + b'\x90\x90'
    assert len(out) == len(original) and out[:512] == original[:512], 'read-only same-size/header patch'
    return bytes(out)


def verify_native(root, original, pins=None):
    root = Path(root)
    assert {p.name for p in root.iterdir()} == set(NATIVE_CONTRACTS), 'native packet inventory'
    loaded = image(original)
    count = 0
    for group, wanted in NATIVE_CONTRACTS.items():
        path = root / group / 'rea.json'
        records = json.loads(path.read_text())['records']
        assert len(records) == len(wanted), 'native coverage'
        seen = set()
        for record in records:
            v = record['normalized_result']
            address = v['address']
            assert record['operation'] == 'read_bytes' and record['subject']['name'] == 'YTMAINT.EXE', 'native operation/subject'
            assert record['subject']['digest'] == {'sha256': BINARIES['YTMAINT.EXE']}, 'native identity'
            assert address in wanted and address not in seen, 'native selected address'
            size = wanted[address]
            assert record['parameters'] == {'address': address, 'length': size}, 'native parameters'
            assert v['complete'] is True and v['requested_bytes'] == v['returned_bytes'] == size, 'native truncation'
            at = int(address, 16) - 0x10000
            assert bytes.fromhex(v['bytes_hex']) == loaded[at:at + size], 'native relocated bytes'
            seen.add(address)
        assert seen == set(wanted), 'native completeness'
        if pins is not None:
            assert SHA(path.read_bytes()) == pins[group], 'immutable native packet'
        count += len(records)
    return count


def verify_control(folder, pin, original, group):
    folder = Path(folder)
    raw_meta = (folder / 'result.json').read_bytes()
    m = json.loads(raw_meta)
    key = group + '/' + folder.name
    assert key in expected_matrix(), 'selected control identity'
    readonly = group == 'port-readonly'
    assert set(m) == sequence.META_KEYS | ({'target_port_raw'} if readonly else set()), 'metadata schema'
    assert m['recipe'] == ('port-clock-readonly-compare-v1' if readonly else 'maintenance-nth-site-v1'), 'profile recipe'
    assert m['name'] == folder.name, 'control name'
    assert m['binaries'] == BINARIES, 'whole original binary identities'
    assert (m['site'], m['nth'], m['source']) == expected_matrix()[key], 'control site/threshold/source'
    assert m['clock'] == '00:00:00' and m['occupied'] == [] and m['patches'] == [], 'unmodified baseline fixture/clock'
    inputs, patches = sequence.expected_inputs([])
    assert m['inputs'] == inputs and m['patches'] == patches, 'immutable before-input identities'
    if m['site'] is None:
        copied = original
        if readonly:
            assert m['target_port_raw'] is None, 'untouched read-only profile'
    elif readonly:
        target = bytes.fromhex('ffffffff') if folder.name == 'miss' else mbf_integer(int(folder.name[5:]))
        assert m['target_port_raw'] == target.hex(), 'read-only selected port operand'
        copied = reconstructed_readonly(original, target)
    else:
        copied = sequence.reconstructed_probe(original, m['site'], m['nth'], m['source'])
    assert SHA(copied) == m['copied_sha256'], 'independent diagnostic reconstruction'
    data_files = set(m['files']) - COMMON
    assert {'after-' + n + '.gz' for n in ('YTDATA.DAT', 'YTNAME.DAT', 'YTNEWS.DAT')} <= data_files <= DATA_FILES, 'known data-file inventory'
    files = COMMON | data_files
    assert set(m['files']) == files and {p.name for p in folder.iterdir()} == files | {'result.json'}, 'exact retained inventory'
    for name, digest in m['files'].items():
        assert SHA((folder / name).read_bytes()) == digest, 'mutable artifact hash: ' + name
    wanted = sequence.commands('00:00:00')
    assert (folder / 'COMMANDS.TXT').read_text() == '\n'.join(wanted) + '\n', 'exact launch recipe'
    verify_launch(folder, wanted)
    assert (folder / 'ERROR.LOG').read_bytes() == b'', 'DOS error witness'
    assert (folder / 'OK.LOG').read_bytes() == b'PROGRAM_OK\r\n', 'DOS zero-exit witness'
    assert (folder / 'RETURN.LOG').read_bytes() == b'PROGRAM_RETURNED\r\n', 'shell return witness'
    date = datetime.date(2026, 11, 2)
    date_text = ('Current date: ' + date.strftime('%a %m/%d/%Y') + '\r\n').encode() + b'Run \x1b[33;1mdate MM/DD/YYYY\x1b[0m to change the current date.\r\n'
    for name in ('DOSDATE.LOG', 'ENDDATE.LOG'):
        assert read_date((folder / name).read_bytes()) == date and (folder / name).read_bytes() == date_text, 'complete date witness'
    for name in ('DOSTIME.LOG', 'ENDTIME.LOG'):
        assert re.fullmatch(rb'Current time: \d{1,2}:\d{2}:\d{2}\.\d{2}(am|pm)\r\nRun \x1b\[33;1mtime hh:mm:ss\x1b\[0m to change the current time.\r\n', (folder / name).read_bytes()), 'complete time witness'
    start, end = [read_time((folder / name).read_bytes()) for name in ('DOSTIME.LOG', 'ENDTIME.LOG')]
    assert start == 0 and start <= end < 30, 'bounded measured clock'
    trace = (folder / 'TRACE.BIN').read_bytes()
    if key == 'entry/startup-timer':
        # Entry007d precedes the first banner and even the world OPEN. A generic
        # body-phase classifier must not invent output that has not occurred.
        assert m['complete'] is False and len(trace) == 4, 'pre-banner startup stop'
        result = {'kind': 'nth-hit', 'raw': trace}
    elif not readonly or m['site'] is None:
        result = sequence.classify_trace(trace, m)
    else:
        assert trace.startswith(MAINT_BANNER) and b'Daily Maintenance Completed OK' not in trace, 'read-only instrumented identity'
        sample = trace[-4:]
        ended = sample == original[512:516]
        assert m['complete'] is ended, 'read-only body-end claim'
        if ended:
            assert folder.name == 'miss' and b'Generating Updated Scoreboard...' in trace[:-4], 'read-only miss return guard'
            assert b'N o n  -  H u m a n   P l a y e r s' in trace[:-4], 'read-only final phase witness'
            result = {'kind': 'body-end', 'raw': sample}
        else:
            assert folder.name != 'miss' and len(sample) == 4, 'read-only hit extent'
            result = {'kind': 'nth-hit', 'raw': sample}
    outputs = {name: gzip.decompress((folder / name).read_bytes()) for name in data_files}
    assert len(outputs['after-YTDATA.DAT.gz']) == 4151 * 137, 'complete retained world extent'
    assert set(pin) == {'metadata_sha256', 'raw'}, 'pin schema'
    assert SHA(raw_meta) == pin['metadata_sha256'], 'immutable metadata pin'
    assert set(pin['raw']) == files, 'complete raw pin inventory'
    for name, digest in pin['raw'].items():
        raw = (folder / name).read_bytes()
        assert SHA(gzip.decompress(raw) if name.endswith('.gz') else raw) == digest, 'immutable raw artifact pin: ' + name
    return dict(result, metadata=m, outputs=outputs)


def verify_semantics(rows):
    assert set(rows) == set(expected_matrix()), 'complete independent experiment matrix'
    untreated = rows['entry/untouched']['outputs']
    assert set(untreated) == DATA_FILES, 'all six untouched outputs'
    for name, value in untreated.items():
        assert SHA(value) == INITIAL_PINS['baseline-split'][name], 'untouched outputs match prior fixed baseline'
    for key in ('entry/untouched-repeat', 'port-default/untouched', 'port-readonly/untouched'):
        assert rows[key]['kind'] == 'untouched' and rows[key]['outputs'] == untreated, 'independent untouched whole-output equality'
    assert rows['entry/startup-timer']['raw'] == bytes.fromhex('00004800'), 'raw startup TIMER zero residue'
    startup = rows['entry/startup-timer']['outputs']
    assert set(startup) == {'after-' + name + '.gz' for name in ('YTDATA.DAT', 'YTNAME.DAT', 'YTNEWS.DAT')}, 'pre-open startup output inventory'
    for name, value in startup.items():
        assert SHA(value) == INITIAL_PINS['baseline-split'][name.replace('after-', 'before-')], 'startup stop preserves every input byte'
    assert rows['entry/xannoron-timer']['raw'] == bytes.fromhex('cdcc4c7c'), 'raw Xannoron TIMER input'
    for n in PORTS:
        assert rows[f'port-default/port-{n:04}']['kind'] == 'nth-hit', 'selected default port hit'
        assert rows[f'port-default/port-{n:04}']['raw'] == bytes.fromhex('00004800' if n <= 605 else '0e745a76'), 'default probe clock transition605/606'
    for n in READONLY_PORTS:
        row = rows[f'port-readonly/port-{n:04}']
        assert row['kind'] == 'nth-hit', 'read-only selected port hit'
        assert row['raw'] == rows[f'port-default/port-{n:04}']['raw'], 'read-only raw clock profile agrees'
        assert row['outputs'] == rows[f'port-default/port-{n:04}']['outputs'], 'independent partial whole-output equality'
    counter = rows['port-default/count-clock']
    assert counter['kind'] == 'body-end' and counter['count'] == 1000, 'complete1000port counter'
    readonly = rows['port-readonly/miss']
    assert readonly['kind'] == 'body-end' and readonly['outputs'] == counter['outputs'], 'read-only miss whole-output equality'
    instrumented = counter['outputs']
    assert set(instrumented) == DATA_FILES, 'all six instrumented body-end outputs'
    for name in DATA_FILES - {'after-YTDATA.DAT.gz'}:
        assert instrumented[name] == untreated[name], 'instrumentation preserves every auxiliary byte'
    a, b = untreated['after-YTDATA.DAT.gz'], instrumented['after-YTDATA.DAT.gz']
    at = (3051 + 606 - 1) * 137 + 101
    differences = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert differences == list(range(at, at + 4)), 'only port606 timestamp bytes differ'
    assert a[at:at + 4] == bytes.fromhex('00004800') and b[at:at + 4] == bytes.fromhex('0e745a76'), 'retained untouched/probe timestamp distinction'


def verify(root=DEFAULT, native=NATIVE, pins_path=PINS_FILE):
    root, native, pins_path = Path(root), Path(native), Path(pins_path)
    assert SHA(pins_path.read_bytes()) == PINS_SHA, 'immutable pin-file identity'
    pins = json.loads(pins_path.read_text())
    assert set(pins) == {'controls', 'native'} and set(pins['controls']) == set(expected_matrix()), 'pin matrix inventory'
    assert set(pins['native']) == set(NATIVE_CONTRACTS), 'native pin inventory'
    assert {p.name for p in root.iterdir()} == {'entry', 'port-default', 'port-readonly'}, 'control profile inventory'
    for group in ('entry', 'port-default', 'port-readonly'):
        assert {p.name for p in (root / group).iterdir()} == {key.split('/')[1] for key in expected_matrix() if key.startswith(group + '/')}, 'profile control inventory'
    originals = {name: (ROOT / 'archive/dos-original' / name).read_bytes() for name in BINARIES}
    assert {name: SHA(raw) for name, raw in originals.items()} == BINARIES, 'complete original binary bytes'
    rows = {key: verify_control(root / key, pin, originals['YTMAINT.EXE'], key.split('/')[0]) for key, pin in pins['controls'].items()}
    verify_semantics(rows)
    reads = verify_native(native, originals['YTMAINT.EXE'], pins['native'])
    return dict(controls=len(rows), profiles=3, untouched=4, native_reads=reads,
                port_counter=1000, differing_timestamp_bytes=4)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', nargs='?', type=Path, default=DEFAULT)
    print(json.dumps(verify(p.parse_args().root), indent=2))
