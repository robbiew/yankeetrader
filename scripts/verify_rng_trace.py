"""Independently verify copied-executable raw QB RNG controls.

The TIMER FAC is measured, never inferred from the requested wall clock.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from verify_rng_clock import read_date, read_time

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2'
RUNTIME_SHA = '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
# name: mode, initial state, explicit FAC, requested date/time
CASES = {
    'unseeded-5': ('unseeded', 5, None, '11/02/2026', '00:00:00'),
    'timer-midnight': ('timer', 5, None, '11/02/2026', '00:00:00'),
    'timer-repeat': ('timer', 5, None, '11/02/2026', '00:00:00'),
    'timer-plus-one': ('timer', 5, None, '11/02/2026', '00:00:01'),
    'timer-noon': ('timer', 5, None, '11/02/2026', '12:34:00'),
    'timer-next-date': ('timer', 5, None, '11/03/2026', '00:00:00'),
    'raw-zero': ('raw', 5, '00000000', '11/02/2026', '00:00:00'),
    'raw-zero-residue': ('raw', 5, '00004800', '11/02/2026', '00:00:00'),
    'raw-100-half': ('raw', 5, '00004987', '11/02/2026', '00:00:00'),
    'raw-negative-100-half': ('raw', 5, '0000c987', '11/02/2026', '00:00:00'),
    'raw-preserved-low': ('raw', 0x1234ab, '00004987', '11/02/2026', '00:00:00'),
    'unseeded-zero': ('unseeded', 0, None, '11/02/2026', '00:00:00'),
    'unseeded-one': ('unseeded', 1, None, '11/02/2026', '00:00:00'),
    'unseeded-max': ('unseeded', 0xffffff, None, '11/02/2026', '00:00:00'),
    'unseeded-next-zero': ('unseeded', 7140929, None, '11/02/2026', '00:00:00'),
    'unseeded-next-max': ('unseeded', 12174572, None, '11/02/2026', '00:00:00'),
}
FILES = {'TRACE.BIN', 'DOSDATE.LOG', 'DOSTIME.LOG', 'RETURN.LOG', 'COMMANDS.TXT', 'dosbox.log'}


def expected_payload(mode, raw):
    """Rebuild the audited replacement machine-code contract without importing the writer."""
    def store(at, value):
        lo, hi = struct.unpack('<HH', value)
        return b'\xc7\x06' + struct.pack('<HH', at, lo) + b'\xc7\x06' + struct.pack('<HH', at + 2, hi)
    def output(at):
        return bytes.fromhex('bb0100b90400ba') + struct.pack('<H', at) + bytes.fromhex('b440cd21')
    result = store(0x1856, b'RNG1') + output(0x1856) + output(0x234)
    result += bytes.fromhex('cd3d439090') if mode == 'timer' else store(0x1a, bytes.fromhex(raw or '00000000'))
    result += output(0x1a)
    if mode != 'unseeded': result += bytes.fromhex('cd3fb19090')
    result += output(0x1a)
    if mode != 'unseeded': result += bytes.fromhex('bb1a00cd3e099090')
    result += output(0x234) + bytes.fromhex('b90001')
    body = bytes.fromhex('51cd3d349090') + output(0x234) + output(0x1a) + bytes.fromhex('59e2')
    result += body + struct.pack('b', -len(body) - 1)
    return result + store(0x1856, b'END!') + output(0x1856) + bytes.fromhex('b8004ccd21')


def decode_single(raw):
    assert len(raw) == 4
    if raw[3] == 0: return 0.0  # QB zero can retain mantissa/sign residue.
    fraction = int.from_bytes(raw[:3], 'little')
    return (-1 if fraction & 0x800000 else 1) * math.ldexp(1 + (fraction & 0x7fffff) / 2**23, raw[3] - 129)


def verify_trace(trace, mode, initial, raw):
    assert len(trace) == 2072 and trace[:4] == b'RNG1' and trace[-4:] == b'END!', 'trace framing'
    before = int.from_bytes(trace[4:8], 'little')
    fac, negative = trace[8:12], trace[12:16]
    seeded = int.from_bytes(trace[16:20], 'little')
    assert before == initial, 'initial seed'
    if mode != 'timer': assert fac == bytes.fromhex(raw or '00000000'), 'explicit FAC'
    if mode == 'unseeded':
        assert negative == fac and seeded == initial, 'unseeded control'
    else:
        expected_negative = bytearray(fac); expected_negative[2] ^= 0x80
        assert negative == expected_negative, 'raw negate including zero residue'
        low, high = struct.unpack('<HH', negative)
        assert seeded == (initial & 255) | ((low ^ high) << 8), 'RANDOMIZE xor-word seed'
    state = seeded
    for index in range(256):
        at = 20 + index * 8
        state = (214013 * state + 1744579) & 0xffffff
        assert int.from_bytes(trace[at:at + 4], 'little') == state, ('RND state', index)
        assert decode_single(trace[at + 4:at + 8]) == state / 2**24, ('RND FAC', index)
    return dict(initial=before, timer_or_input_fac=fac.hex(), input_value=decode_single(fac), seeded=seeded, final_state=state)


def fixture_document(destination):
    """Exact portable native records for model regression tests."""
    destination = Path(destination)
    cases = []
    for name, (mode, state, raw, date, time) in CASES.items():
        d = destination / name
        trace = (d / 'TRACE.BIN').read_bytes()
        meta = json.loads((d / 'result.json').read_text())
        cases.append(dict(name=name, mode=mode, initial=state,
                          raw_fac=trace[8:12].hex(), trace_hex=trace.hex(),
                          source_trace_sha256=SHA(trace),
                          copied_initializer_sha256=meta['copied_initializer_sha256'],
                          copied_runtime_sha256=meta['copied_runtime_sha256']))
    return dict(format='qb-native-rng-v1', samples_per_case=256, cases=cases)


def verify_fixture(destination, fixture):
    assert json.loads(Path(fixture).read_text()) == fixture_document(destination), 'portable native fixture differs'


def verify(destination, cases=None):
    """Verify the fixed parent corpus, or an explicitly supplied independent corpus."""
    cases = CASES if cases is None else cases
    destination = Path(destination)
    assert {p.name for p in destination.iterdir() if p.is_dir()} == set(cases), 'fixed case coverage'
    original = (ROOT / 'archive/dos-original/YT-INIT.EXE').read_bytes()
    runtime = (ROOT / 'archive/dos-original/BRUN30.EXE').read_bytes()
    assert SHA(original) == INIT_SHA and SHA(runtime) == RUNTIME_SHA, 'original binaries'
    outcomes = {}
    for name, (mode, state, raw, date, time) in cases.items():
        d = destination / name; meta = json.loads((d / 'result.json').read_text())
        assert meta['name'] == name and meta['mode'] == mode and meta.get('state', 5) == state
        assert meta.get('raw') == raw and meta.get('date', '11/02/2026') == date and meta.get('time', '00:00:00') == time
        assert meta['recipe'] == 'qb-rng-raw-v1' and meta['samples'] == 256
        assert meta['original_initializer_sha256'] == INIT_SHA and meta['original_runtime_sha256'] == RUNTIME_SHA
        payload = expected_payload(mode, raw)
        assert meta['payload_hex'] == payload.hex(), 'payload contract'
        assert meta['payload_file_offset'] == 0x26d and meta['payload_code_offset'] == 0x6d
        patched = bytearray(original)
        assert patched[0x23a:0x23f] == bytes.fromhex('cd3d439090')
        patched[0x23a:0x23f] = bytes.fromhex('e930009090')
        patched[0x26d:0x26d + len(payload)] = payload
        copied_runtime = bytearray(runtime); struct.pack_into('<I', copied_runtime, 0x10234, state)
        assert meta['copied_initializer_sha256'] == SHA(patched), 'entire copied initializer'
        assert meta['copied_runtime_sha256'] == SHA(copied_runtime), 'entire copied runtime'
        assert set(meta['files']) == FILES, 'artifact coverage'
        for filename, digest in meta['files'].items(): assert SHA((d / filename).read_bytes()) == digest, filename
        assert read_date((d / 'DOSDATE.LOG').read_bytes()).strftime('%m/%d/%Y') == date
        observed = read_time((d / 'DOSTIME.LOG').read_bytes())
        requested = sum(int(part) * multiplier for part, multiplier in zip(time.split(':'), (3600, 60, 1)))
        assert abs(observed - requested) <= .1, 'DOS clock control'
        commands = (d / 'COMMANDS.TXT').read_text().splitlines()
        assert len(commands) == 9 and commands[0].startswith('mount c ')
        assert commands[1:] == ['c:', 'date ' + date, 'time ' + time, 'date > DOSDATE.LOG', 'time > DOSTIME.LOG', 'yt-init > TRACE.BIN', 'echo PROBE_RETURNED > RETURN.LOG', 'exit']
        assert b'PROBE_RETURNED' in (d / 'RETURN.LOG').read_bytes(), 'DOS return marker'
        outcomes[name] = verify_trace((d / 'TRACE.BIN').read_bytes(), mode, state, raw)
        outcomes[name]['observed_shell_seconds'] = observed
        if name in ('unseeded-next-zero', 'unseeded-next-max'):
            trace = (d / 'TRACE.BIN').read_bytes()
            expected = 0 if name.endswith('zero') else 0xffffff
            assert int.from_bytes(trace[20:24], 'little') == expected, 'boundary first state'
            assert decode_single(trace[24:28]) == expected / 2**24, 'boundary first RND'
    return outcomes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?', type=Path, default=ROOT / 'research/yt-rng-seeding/trace-dos')
    parser.add_argument('--fixture', type=Path, default=ROOT / 'internal/qbrng/testdata/native_rng.json')
    args = parser.parse_args()
    outcomes = verify(args.destination)
    verify_fixture(args.destination, args.fixture)
    print(json.dumps(outcomes, indent=2))
