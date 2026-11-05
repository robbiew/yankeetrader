"""Verify retained terminating first-hit maintenance RNG diagnostics, without DOSBox.

This checker does not import the capture runner. It checks identities, reconstructed
patches, witnesses, pinned bytes and bounded state transitions, not whole-run draw
counts or normal completion for a hit probe.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import math
import re
from pathlib import Path
import shlex
import struct

from verify_rng_clock import read_date, read_time
from verify_rng_native import image
from verify_initial_maintenance import PINS as INITIAL_PINS

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'research/yt-maint/rng-controls'
PINS_FILE = ROOT / 'research/yt-maint/rng-pins.json'
PINS_SHA = '3c778c520b2dc94c8f383a0b95cd605ce6139ff891625a463a41bb337599fbb2'
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINARIES = {
    'YTMAINT.EXE': '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
    'BRUN30.EXE': '3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
    'YT-INIT.EXE': '601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2',
}
# Independent fixed boundaries and original five-byte instructions.
PHASES = {
    'seed-timer': (0x7d, 'cd3fb19090'), 'seed-before': (0x85, 'cd3e099090'),
    'seed-after': (0x8d, 'cd3e209090'), 'helper1-before': (0x7900, 'cd3e099090'),
    'helper1-after': (0x7908, 'cd3d339090'), 'helper1-rnd-after': (0x790d, '8b7e06cd3f'),
    'helper1-argument': (0x7908, 'cd3d339090'),
    'wanderer-1-before': (0x2237, 'cd3d349090'), 'wanderer-1-after': (0x223c, 'bfac7ecd3f'),
    'wanderer-2-before': (0x226c, 'cd3d349090'), 'wanderer-2-after': (0x2271, 'bf8e83cd3f'),
    'wanderer-3-before': (0x2363, 'cd3d349090'), 'wanderer-3-after': (0x2368, 'bfbc83cd3f'),
    'helper2-before': (0x7946, 'cd3e099090'), 'helper2-after': (0x794e, 'cd3fa79090'),
    'helper2-rnd-before': (0x7989, 'cd3d339090'), 'helper2-rnd-after': (0x798e, '8b7e08cd3f'),
    'helper2-argument': (0x7989, 'cd3d339090'),
}
SITES = tuple(int(s, 16) for s in '''0ba5 0be0 0c1c 16a9 16bb 16e5 1719 173a 1758 17a1 17b2
18cc 2237 226c 2363 25a0 260e 2c56 3348 3c0e 46af 485a 4fbf 50b4 537e 5513 551e
5541 554c 5570 557b 55f5 5622 5a25 5bed 61b2 632e 6351 6383 63ae 7656 7908 7989'''.split())
HIT_SITES = {0x2237, 0x226c, 0x2363, 0x3348, 0x3c0e, 0x46af, 0x537e, 0x7908, 0x7989}
CASES = {
    'baseline': ('baseline-split', '11/02/2026', '00:00:00', False),
    'repeat': ('repeat-split', '11/02/2026', '00:00:00', False),
    'second-one': ('second-one-split', '11/02/2026', '00:00:01', False),
    'second-two': ('second-two-split', '11/02/2026', '00:00:02', False),
    'new-year': ('new-year-split', '01/01/2027', '00:00:00', False),
    'integrated': ('baseline-integrated', '11/02/2026', '00:00:00', True),
}
FILES = {'TRACE.BIN', 'HIT.LOG', 'MISS.LOG', 'RETURN.LOG', 'DOSDATE.LOG', 'DOSTIME.LOG',
         'ENDDATE.LOG', 'ENDTIME.LOG', 'COMMANDS.TXT', 'dosbox.log', 'partial-world.dat.gz'}
META_KEYS = {'recipe', 'case', 'phase', 'oracle', 'date', 'time', 'integrated', 'site', 'source',
             'hit', 'original_bytes', 'binaries', 'copied_maintenance_sha256', 'inputs', 'files'}
MAINT_BANNER = (b'\r\nYankee Trader Maintenance program\r\n        by Alan Davenport\r\n\r\n'
                b'       (Revision 03/14/94)\r\n\r\nThis should be run once per day.\r\n\r\n')


def patched_digest(original, site, source):
    # Assemble separately: return guard; DS/CS switch; stdout writes of marker,
    # runtime state and selected FAC/argument; exit. The guard is outside the hook.
    probe = bytes.fromhex('b8634ccd211e0e1fbb0100b90400ba6d00b440cd211fba3402b440cd21')
    probe += b'\xba' + struct.pack('<H', source) + bytes.fromhex('b440cd21b8004ccd214d535031')
    assert len(probe) == 45
    out = bytearray(original)
    out[0x244:0x271] = probe
    out[0x200+site:0x205+site] = b'\xe9' + struct.pack('<H', (0x49-site-3) & 0xffff) + b'\x90\x90'
    assert len(out) == len(original) and out[:512] == original[:512], 'same-size/header probe'
    return SHA(out)


def verify_native(path, original):
    records = json.loads(Path(path).read_text())['records']
    wanted = {'0x10073': 29, '0x178f3': 237}
    assert len(records) == 2, 'native coverage'
    loaded = image(original)
    seen = set()
    for record in records:
        value = record['normalized_result']
        address = value['address']
        assert record['operation'] == 'read_bytes', 'native operation'
        assert record['subject']['name'] == 'YTMAINT.EXE', 'native target name'
        assert record['subject']['digest'] == {'sha256': BINARIES['YTMAINT.EXE']}, 'native identity'
        assert address in wanted and address not in seen, 'native address'
        size = wanted[address]
        assert record['parameters'] == {'address': address, 'length': size}, 'native parameters'
        assert value['complete'] is True and value['requested_bytes'] == value['returned_bytes'] == size, 'native truncation'
        offset = int(address, 16) - 0x10000
        assert bytes.fromhex(value['bytes_hex']) == loaded[offset:offset+size], 'relocated native bytes'
        seen.add(address)
    assert seen == set(wanted), 'native coverage'


def verify_launch(folder, commands):
    lines = (folder / 'dosbox.log').read_text().splitlines()
    messages = [line.split(' | ', 1)[1] for line in lines if ' | ' in line]
    arguments = [m[len('arguments: '):] for m in messages if m.startswith('arguments: ')]
    assert len(arguments) == 1, 'one launch observation'
    argv = shlex.split(arguments[0])
    assert len(argv) > 8 and Path(argv[0]).name == 'dosbox-staging', 'emulator executable'
    mount = argv[8]
    assert mount.startswith('mount c '), 'isolated mount'
    mounted = Path(mount[len('mount c '):])
    assert mounted.is_absolute() and mounted.name == folder.name, 'mount control identity'
    expected = ['--noprimaryconf', '--nolocalconf', '--set', 'cpu_cycles=200000', '--set', 'nosound=true']
    expected += [v for c in [mount, 'c:'] + commands + ['exit'] for v in ('-c', c)]
    assert argv[1:] == expected, 'launch recipe'
    cpu = [m for m in messages if m.startswith('CPU:')]
    video = [m for m in messages if m.startswith('SDL:') and 'video initialised' in m]
    sound = [m for m in messages if m.startswith('MIXER: Sound output')]
    assert len(cpu) == 1 and cpu[0].startswith('CPU: Setting fixed 200000 cycles.'), 'applied CPU'
    assert video == ['SDL: dummy video initialised'], 'applied dummy video'
    assert sound == ["MIXER: Sound output disabled ('nosound' mode)"], 'applied sound'
    assert messages.count('dosbox-staging version 0.83.0 ()') == 1, 'emulator version'


def mbf(raw):
    assert len(raw) == 4
    if raw[3] == 0:
        return 0
    mantissa = int.from_bytes(raw[:3], 'little')
    return (-1 if mantissa & 0x800000 else 1) * math.ldexp(1 + (mantissa & 0x7fffff) / 2**23, raw[3]-129)


def verify_semantics(observations):
    for case in CASES:
        phases = {p: observations[case+'--'+p] for p in PHASES}
        state = lambda p: phases[p][0]
        fac = lambda p: phases[p][1]
        assert state('seed-timer') == state('seed-before') == 5, 'startup state five'
        timer = bytearray(fac('seed-timer')); timer[2] ^= 0x80
        assert fac('seed-before') == timer, 'startup negated TIMER'
        for before, after in [('seed-before', 'seed-after'), ('helper1-before', 'helper1-after'),
                              ('helper2-before', 'helper2-after')]:
            b0, b1, b2, exponent = fac(before)
            expected = (state(before) & 255) | ((b0 ^ b2) << 8) | ((b1 ^ exponent) << 16)
            assert fac(after) == fac(before), (case, before, 'RANDOMIZE input FAC alignment')
            assert state(after) == expected, (case, before, 'RANDOMIZE state')
        for before, after in [('helper1-after', 'helper1-rnd-after'),
                              ('helper2-rnd-before', 'helper2-rnd-after')] + [
                                  (f'wanderer-{i}-before', f'wanderer-{i}-after') for i in (1, 2, 3)]:
            assert state(after) == (214013 * state(before) + 1744579) % 2**24, (case, before, 'one RND step')
            assert mbf(fac(after)) == state(after) / 2**24, (case, after, 'RND FAC')
        assert state('helper1-before') == state('seed-after'), 'startup/helper boundary'
        assert state('wanderer-1-before') == state('helper1-rnd-after'), 'helper/Wanderer boundary'
        for i in (1, 2):
            assert state(f'wanderer-{i+1}-before') == state(f'wanderer-{i}-after'), 'consecutive Wanderer draws'
        assert state('helper2-rnd-before') == state('helper2-after'), 'second helper boundary'
        for i in (1, 2):
            argument = f'helper{i}-argument'
            assert fac(argument) == bytes.fromhex('00000081'), 'positive-one helper argument'
            assert state(argument) == state(f'helper{i}-after'), 'argument state'
    for phase in PHASES:
        assert observations['baseline--'+phase] == observations['repeat--'+phase], 'repeat phase state/FAC'
    for site, phase in [(0x2237, 'wanderer-1-before'), (0x226c, 'wanderer-2-before'),
                        (0x2363, 'wanderer-3-before'), (0x7908, 'helper1-after'), (0x7989, 'helper2-rnd-before')]:
        assert observations[f'baseline--rnd-{site:04x}'] == observations['baseline--'+phase], 'duplicate boundary agreement'


def verify_oracles(directory, pins):
    """Check fresh unchanged binaries with the identical prelaunch command recipe."""
    directory = Path(directory)
    assert {p.name for p in directory.iterdir()} == set(CASES), 'six fresh untouched oracles'
    worlds = {}
    data_files = {'after-'+n+'.gz' for n in ('YTDATA.DAT', 'YTNAME.DAT', 'YTNEWS.DAT', 'YTRMSG.DAT', 'YTSCORE.ASC', 'YTYNEWS.DAT')}
    common = {'TRACE.BIN', 'RETURN.LOG', 'COMMANDS.TXT', 'dosbox.log', 'DOSDATE.LOG', 'DOSTIME.LOG', 'ENDDATE.LOG', 'ENDTIME.LOG'}
    for case, (oracle, date, clock, integrated) in CASES.items():
        folder = directory / case
        m = json.loads((folder / 'result.json').read_text())
        assert set(m) == {'recipe', 'case', 'oracle', 'date', 'time', 'integrated', 'binaries', 'inputs', 'files'}, 'oracle metadata schema'
        assert (m['recipe'], m['case'], m['oracle'], m['date'], m['time'], m['integrated']) == (
            'maintenance-rng-untouched-v1', case, oracle, date, clock, integrated), 'oracle identity'
        assert m['binaries'] == BINARIES, 'untouched binary identities'
        inputs = {} if integrated else {n: INITIAL_PINS[oracle]['before-'+n+'.gz'] for n in ('YTDATA.DAT', 'YTNAME.DAT', 'YTNEWS.DAT')}
        assert m['inputs'] == inputs, 'oracle input identities'
        files = common | data_files | ({'ANSWERS.TXT'} if integrated else set())
        assert set(m['files']) == files and {p.name for p in folder.iterdir()} == files | {'result.json'}, 'oracle retained inventory'
        for n, digest in m['files'].items():
            assert SHA((folder / n).read_bytes()) == digest, 'oracle retained hash'
        raw_pins = pins['oracle--'+case]
        assert set(raw_pins) == data_files | {'TRACE.BIN'}, 'all oracle raw files pinned'
        for n, digest in raw_pins.items():
            raw = (folder / n).read_bytes()
            assert SHA(gzip.decompress(raw) if n.endswith('.gz') else raw) == digest, 'oracle raw byte pin'
        commands = ['date '+date, 'time '+clock, 'date > DOSDATE.LOG', 'time > DOSTIME.LOG',
                    'yt-init < ANSWERS.TXT > TRACE.BIN' if integrated else 'ytmaint > TRACE.BIN',
                    'echo ORIGINAL_RETURNED > RETURN.LOG', 'date > ENDDATE.LOG', 'time > ENDTIME.LOG']
        assert (folder / 'COMMANDS.TXT').read_text() == '\n'.join(commands)+'\n', 'oracle command recipe'
        verify_launch(folder, commands)
        assert (folder / 'RETURN.LOG').read_bytes() == b'ORIGINAL_RETURNED\r\n', 'oracle shell return'
        if integrated:
            assert (folder / 'ANSWERS.TXT').read_bytes() == b'Y\r\n\r\n', 'oracle answers'
        trace = (folder / 'TRACE.BIN').read_bytes()
        assert b'MSP1' not in trace and trace.count(b'Daily Maintenance Completed OK') == 1, 'untouched normal completion'
        if integrated:
            assert trace.startswith(b'\r\n            Yankee Trader Initialization Program\r\n'), 'oracle initializer banner'
            assert b'<YT-INIT Normal Termination>' in trace, 'oracle initializer completion'
        else:
            assert trace.startswith(MAINT_BANNER), 'oracle maintenance banner'
        expected_date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        for n in ('DOSDATE.LOG', 'ENDDATE.LOG'):
            raw = (folder / n).read_bytes()
            assert read_date(raw) == expected_date, 'oracle observed date'
            assert raw == ('Current date: '+expected_date.strftime('%a %m/%d/%Y')+'\r\n').encode() + b'Run \x1b[33;1mdate MM/DD/YYYY\x1b[0m to change the current date.\r\n', 'oracle complete date log'
        for n in ('DOSTIME.LOG', 'ENDTIME.LOG'):
            assert re.fullmatch(rb'Current time: \d{1,2}:\d{2}:\d{2}\.\d{2}(am|pm)\r\nRun \x1b\[33;1mtime hh:mm:ss\x1b\[0m to change the current time.\r\n', (folder / n).read_bytes()), 'oracle complete time log'
        start, end = [read_time((folder / n).read_bytes()) for n in ('DOSTIME.LOG', 'ENDTIME.LOG')]
        assert start == {'00:00:00': 0, '00:00:01': .98, '00:00:02': 1.97}[clock], 'oracle observed BIOS clock'
        assert start < end < start+30, 'oracle run clock interval'
        world = gzip.decompress((folder / 'after-YTDATA.DAT.gz').read_bytes())
        assert len(world) == 4151*137, 'oracle world size'
        worlds[case] = world
    assert worlds['baseline'] == worlds['repeat'], 'untouched fixed-clock repeat'
    return worlds


def verify(directory=DEFAULT, native=None, pins_path=PINS_FILE, oracles=None):
    directory = Path(directory)
    raw_pins = Path(pins_path).read_bytes()
    assert SHA(raw_pins) == PINS_SHA, 'immutable independent pins'
    pins = json.loads(raw_pins)
    originals = {n: (ROOT / 'archive/dos-original' / n).read_bytes() for n in BINARIES}
    assert {n: SHA(b) for n, b in originals.items()} == BINARIES, 'immutable original identities'
    original = originals['YTMAINT.EXE']
    verify_native(native or ROOT / 'research/yt-maint/rng-native/rea.json', original)
    inventory = {i-512 for i in range(512, len(original)-4)
                 if original[i:i+5] in (bytes.fromhex('cd3d339090'), bytes.fromhex('cd3d349090'))}
    assert inventory == set(SITES), 'finite original RND inventory'
    expected_names = {case+'--'+phase for case in CASES for phase in PHASES}
    expected_names |= {f'baseline--rnd-{site:04x}' for site in SITES}
    assert {p.name for p in directory.iterdir()} == expected_names, 'complete 151-control matrix'
    assert set(pins) == expected_names | {'oracle--'+c for c in CASES}, 'complete independent pins'
    oracle_worlds = verify_oracles(oracles or ROOT / 'research/yt-maint/rng-oracles', pins)
    observations = {}
    miss_worlds = set()
    for name in sorted(expected_names):
        folder = directory / name
        case, phase = name.split('--')
        oracle, date, clock, integrated = CASES[case]
        m = json.loads((folder / 'result.json').read_text())
        assert set(m) == META_KEYS, 'exact metadata schema'
        assert (m['recipe'], m['case'], m['phase'], m['oracle'], m['date'], m['time'], m['integrated']) == (
            'maintenance-rng-first-hit-v1', case, phase, oracle, date, clock, integrated), 'phase identity'
        if phase in PHASES:
            site, instruction = PHASES[phase]; hit = True
        else:
            site = int(phase[4:], 16); instruction = original[512+site:517+site].hex(); hit = site in HIT_SITES
        source = 0x7ea4 if phase.endswith('-argument') else 0x1a
        assert type(m['hit']) is bool and m['hit'] is hit, 'expected hit inventory'
        assert (m['site'], m['source'], m['original_bytes']) == (site, source, instruction), 'probe site/source identity'
        assert original[512+site:517+site].hex() == instruction, 'original boundary instruction'
        assert m['binaries'] == BINARIES, 'binary attribution'
        assert m['copied_maintenance_sha256'] == patched_digest(original, site, source), 'reconstructed probe identity'
        inputs = {} if integrated else {n: SHA(gzip.decompress((ROOT / 'research/yt-maint/initial-controls' / oracle / ('before-'+n+'.gz')).read_bytes()))
                                        for n in ('YTDATA.DAT', 'YTNAME.DAT', 'YTNEWS.DAT')}
        if not integrated:
            assert inputs == {n: INITIAL_PINS[oracle]['before-'+n+'.gz'] for n in inputs}, 'published input byte pins'
        assert m['inputs'] == inputs, 'original input identities'
        files = FILES | ({'ANSWERS.TXT'} if integrated else set())
        assert set(m['files']) == files and {p.name for p in folder.iterdir()} == files | {'result.json'}, 'exact retained files'
        for filename, digest in m['files'].items():
            assert SHA((folder / filename).read_bytes()) == digest, 'retained hash: '+filename
        commands = ['date '+date, 'time '+clock, 'date > DOSDATE.LOG', 'time > DOSTIME.LOG',
                    'yt-init < ANSWERS.TXT > TRACE.BIN' if integrated else 'ytmaint > TRACE.BIN',
                    'if errorlevel 99 echo PROBE_NOT_REACHED > MISS.LOG',
                    'if not errorlevel 1 echo PROBE_RECORDED > HIT.LOG',
                    'echo PROBE_RETURNED > RETURN.LOG', 'date > ENDDATE.LOG', 'time > ENDTIME.LOG']
        assert (folder / 'COMMANDS.TXT').read_text() == '\n'.join(commands)+'\n', 'command recipe'
        verify_launch(folder, commands)
        if integrated:
            assert (folder / 'ANSWERS.TXT').read_bytes() == b'Y\r\n\r\n', 'initializer answers'
        assert (folder / 'RETURN.LOG').read_bytes() == b'PROBE_RETURNED\r\n', 'shell return witness'
        witnesses = ((folder / 'HIT.LOG').read_bytes(), (folder / 'MISS.LOG').read_bytes())
        assert witnesses == ((b'PROBE_RECORDED\r\n', b'') if hit else (b'', b'PROBE_NOT_REACHED\r\n')), 'hit/miss witnesses'
        expected_date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        for filename in ('DOSDATE.LOG', 'ENDDATE.LOG'):
            raw_date = (folder / filename).read_bytes()
            assert read_date(raw_date) == expected_date, 'observed date'
            assert raw_date == ('Current date: '+expected_date.strftime('%a %m/%d/%Y')+'\r\n').encode() + b'Run \x1b[33;1mdate MM/DD/YYYY\x1b[0m to change the current date.\r\n', 'complete date log'
        for n in ('DOSTIME.LOG', 'ENDTIME.LOG'):
            assert re.fullmatch(rb'Current time: \d{1,2}:\d{2}:\d{2}\.\d{2}(am|pm)\r\nRun \x1b\[33;1mtime hh:mm:ss\x1b\[0m to change the current time.\r\n', (folder / n).read_bytes()), 'complete time log'
        start, end = [read_time((folder / n).read_bytes()) for n in ('DOSTIME.LOG', 'ENDTIME.LOG')]
        assert start == {'00:00:00': 0, '00:00:01': .98, '00:00:02': 1.97}[clock], 'observed BIOS clock'
        assert start <= end < start+30, 'bounded first-hit clock interval'
        trace = (folder / 'TRACE.BIN').read_bytes()
        world = gzip.decompress((folder / 'partial-world.dat.gz').read_bytes())
        assert set(pins[name]) == {'trace_sha256', 'world_sha256'}, 'raw pin schema'
        assert SHA(trace) == pins[name]['trace_sha256'], 'raw trace pin'
        assert SHA(world) == pins[name]['world_sha256'], 'partial world pin'
        assert len(world) == 4151*137, 'whole partial-world size'
        if hit:
            assert trace[-12:-8] == b'MSP1' and trace.count(b'MSP1') == 1, 'one first-hit packet'
            assert b'Daily Maintenance Completed OK' not in trace, 'terminating probe boundary'
            prefix = trace[:-12]
            if not integrated:
                assert (prefix == b'') if phase.startswith('seed-') else prefix.startswith(MAINT_BANNER), 'phase output prefix'
            else:
                assert prefix.startswith(b'\r\n            Yankee Trader Initialization Program\r\n                     By Alan Davenport\r\n'), 'integrated initializer banner'
                assert b'Running initial maintenance...' in prefix, 'integrated parent output'
                if not phase.startswith('seed-'):
                    assert MAINT_BANNER in prefix, 'integrated maintenance banner'
            state = int.from_bytes(trace[-8:-4], 'little')
            assert state < 2**24, '24-bit runtime state'
            observations[name] = (state, trace[-4:])
        else:
            assert b'MSP1' not in trace and trace.startswith(MAINT_BANNER), 'miss output identity'
            assert b'Daily Maintenance Completed OK' not in trace, 'return guard precedes normal completion banner'
            miss_worlds.add(SHA(world))
    assert miss_worlds == {SHA(oracle_worlds['baseline'])}, '34 unreached hooks match fresh untouched world'
    verify_semantics(observations)
    # Bounded correlation against separately pinned, untouched prior controls.
    # This does not infer the general helper/retry algorithm.
    for case, (oracle, _, _, _) in CASES.items():
        world = gzip.decompress((ROOT / 'research/yt-maint/initial-controls' / oracle / 'after-YTDATA.DAT.gz').read_bytes())
        assert SHA(world) == INITIAL_PINS[oracle]['after-YTDATA.DAT.gz'], 'published placement oracle'
        occupied = [r-51 for r in range(52, 3052)
                    if mbf(world[(r-1)*137+93:(r-1)*137+97]) == 1]
        first = observations[case+'--helper1-rnd-after'][0]
        assert occupied == [1 + 3000*first // 2**24], 'bounded first Wanderer draw correlation'
    return {'controls': len(expected_names), 'selected_phase_hits': 108, 'inventory_hits': 9, 'inventory_misses': 34, 'native_reads': 2, 'untouched_oracles': 6}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=DEFAULT)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
