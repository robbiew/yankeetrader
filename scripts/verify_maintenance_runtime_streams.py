"""Verify declared runtime instrumentation, complete event streams and native boundaries."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys
from verify_initial_maintenance import BINARIES, PINS as NATIVE_PINS, verify_launch
from verify_rng_clock import read_date, read_time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'research/yt-maint/runtime-stream-controls'
SHA = lambda b: hashlib.sha256(b).hexdigest()
CASES = {'midnight': ('baseline-split', '11/02/2026', '00:00:00', 24404, 62),
         'repeat': ('baseline-split', '11/02/2026', '00:00:00', 24404, 62),
         'second-one': ('second-one-split', '11/02/2026', '00:00:01', 28052, 61),
         'second-two': ('second-two-split', '11/02/2026', '00:00:02', 26354, 62),
         'new-year': ('new-year-split', '01/01/2027', '00:00:00', 24404, 62)}
# Fixed hashes describe reviewed instrumented observations, never untouched-native equality.
PINS = {'midnight': {'after-YTDATA.DAT.gz': 'fbad8639f3aaeedf9e0a372fc048e36888c398a3c9ec39c54c1b9d18a76cb213',
              'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
              'after-YTNEWS.DAT.gz': '496dd8e6f9d32228c2e3b50c714a33edfa97366e1e0609e9b2a2dfd555ad041c',
              'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
              'after-YTSCORE.ASC.gz': 'e8c51ad1607e48ad85896c41c18639abc180801b76d5d0a4dbc0bc0486c03aba',
              'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
              'before-YTDATA.DAT.gz': '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
              'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
              'before-YTNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
              'trace.bin.gz': 'fafd18cfaf4f13860aae198849c804e3ac36554b4916f9e7e603d691e9ea937a'},
 'new-year': {'after-YTDATA.DAT.gz': '27a2649fa3c668a4479ed8111eea85d904fef23b0af38a83f5c2289b33c944da',
              'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
              'after-YTNEWS.DAT.gz': '3ead9803ab7162a0aa4c21608eb7d969c1ee37f312288554316b58be96b215f0',
              'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
              'after-YTSCORE.ASC.gz': '2f6387d9cef22d07859666c0c0eccfdd7c7b4ab707b71cf19347a338e88ab176',
              'after-YTYNEWS.DAT.gz': '07901bde0493ec123c5cdad35c4fa32add64125f0511e05e90a74942e9352759',
              'before-YTDATA.DAT.gz': 'e6d5ab5b3fab7563b279e976cdde3c4e6e494c2dffd5c35a74a60fac38fdf328',
              'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
              'before-YTNEWS.DAT.gz': '07901bde0493ec123c5cdad35c4fa32add64125f0511e05e90a74942e9352759',
              'trace.bin.gz': 'f9cfff8211b71d32c200b34b25fb18b210aab16fd1be7674774a460b83c3fec7'},
 'repeat': {'after-YTDATA.DAT.gz': 'fbad8639f3aaeedf9e0a372fc048e36888c398a3c9ec39c54c1b9d18a76cb213',
            'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
            'after-YTNEWS.DAT.gz': '496dd8e6f9d32228c2e3b50c714a33edfa97366e1e0609e9b2a2dfd555ad041c',
            'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            'after-YTSCORE.ASC.gz': 'e8c51ad1607e48ad85896c41c18639abc180801b76d5d0a4dbc0bc0486c03aba',
            'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
            'before-YTDATA.DAT.gz': '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
            'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
            'before-YTNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
            'trace.bin.gz': 'fafd18cfaf4f13860aae198849c804e3ac36554b4916f9e7e603d691e9ea937a'},
 'second-one': {'after-YTDATA.DAT.gz': '3cf076bd31933fbb863053384c542231af48c3b9cb0993898f448fbe70389cc8',
                'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                'after-YTNEWS.DAT.gz': '0360df86b597a9770491afe657b1d8c824d18421dbd523d59f06e2c388eba108',
                'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                'after-YTSCORE.ASC.gz': '19246f1e8e9cfe685adb30cbc4d9687318f3baeb54e99167989c75273103a609',
                'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
                'before-YTDATA.DAT.gz': '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
                'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                'before-YTNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
                'trace.bin.gz': '88029f6aface140535b61fd6bd005e9c2001fb4d4f8862ee5cee3c4afc970c21'},
 'second-two': {'after-YTDATA.DAT.gz': '0cd3985c84668e50285c1592fc3c0f7a71d8faefdff30de25d20ab2c78ac655f',
                'after-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                'after-YTNEWS.DAT.gz': '5e2dc90c6e620f12f54207ac93da554a4fec76cd570f43e831c183f8b5811152',
                'after-YTRMSG.DAT.gz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                'after-YTSCORE.ASC.gz': '19246f1e8e9cfe685adb30cbc4d9687318f3baeb54e99167989c75273103a609',
                'after-YTYNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
                'before-YTDATA.DAT.gz': '0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
                'before-YTNAME.DAT.gz': 'af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f',
                'before-YTNEWS.DAT.gz': '1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a',
                'trace.bin.gz': 'ac6ba13e88c734df6ada464d4d2e414f48478a9978af3953850fcfc87b84bfa7'}}


def expected_runtime(original):
    assert SHA(original) == BINARIES['BRUN30.EXE']
    assert original[0xffb2:0xffee] == bytes(60), 'declared padding bytes'
    result = bytearray(original)
    # Displaced MOV [0235],AX / MOV AX,8800; common logger preserves flags,
    # registers and DS, puts marker/return-IP/state/FAC on SS and writes 14 bytes.
    payload = bytes.fromhex('a33502eb03b800889c601e8becff361c00ff361a00ff363602ff363402'
                            '36ff7614684721680052161f8bd4bb0100b90e00b440cd2183c40e1f619dc3')
    assert len(payload) == 60
    assert original[0xb506:0xb509] == bytes.fromhex('b80088')
    assert original[0xb54f:0xb552] == bytes.fromhex('a33502')
    result[0xb506:0xb509] = bytes.fromhex('e8ae4a')
    result[0xb54f:0xb552] = bytes.fromhex('e8604a')
    result[0xffb2:0xffee] = payload
    assert len(result) == len(original) and result[:512] == original[:512]
    return bytes(result), payload


def parse_trace(raw):
    assert raw.startswith(b'\0RG!'), 'startup seed record'
    events = []
    state = 5
    position = 0
    phases = {}
    phase = 'startup'
    markers = (b'Running port maintenance', b'Running planet maintenance', b'Processing the Xannor',
               b'Mercenary Maintenance', b'Running Super Planet Lottery')
    while True:
        at = raw.find(b'\0RG!', position)
        if at < 0: break
        text = raw[position:at]
        for marker in markers:
            if marker in text: phase = marker.decode()
        assert at + 14 <= len(raw), 'complete event frame'
        kind, observed, fac = struct.unpack('<HII', raw[at+4:at+14])
        assert kind in (0xb352, 0xb309), 'audited runtime return offset'
        if kind == 0xb352:
            expected = (state & 255) | (((fac & 65535) ^ (fac >> 16)) << 8)
        else:
            expected = (214013 * state + 1744579) & 0xffffff
        assert observed == expected, 'seed/draw recurrence'
        phases[(phase, kind)] = phases.get((phase, kind), 0) + 1
        events.append((kind, observed, fac))
        state = observed
        position = at + 14
    assert b'Daily Maintenance Completed OK' in raw[position:], 'complete maintenance after final event'
    assert events[0][0] == 0xb352
    assert ('Running port maintenance', 0xb309) not in phases, 'no measured port draws'
    assert phases.get(('Running planet maintenance', 0xb309)) == 4, 'bounded planet prefix'
    assert phases.get(('Mercenary Maintenance', 0xb309)) == 21, 'bounded mercenary draws'
    assert phases.get(('Processing the Xannor', 0xb352)) == 58, 'bounded Xannor reseeds'
    return events, phases


def verify(root=DEFAULT):
    assert {p.name for p in root.iterdir()} == set(CASES), 'complete matrix'
    runtime, payload = expected_runtime((ROOT / 'archive/dos-original/BRUN30.EXE').read_bytes())
    maintenance = (ROOT / 'archive/dos-original/YTMAINT.EXE').read_bytes()
    assert SHA(maintenance) == BINARIES['YTMAINT.EXE']
    for offset, hex_bytes in ((0x278, 'cd3d439090cd3fb19090bb1a00cd3e099090'),
                              (0x7af8, 'cd3d439090bb1a00cd3e099090'),
                              (0x7b3e, 'cd3d439090bb1a00cd3e099090')):
        expected = bytes.fromhex(hex_bytes)
        assert maintenance[offset:offset+len(expected)] == expected, 'native seed call contract'
    results = {}
    for name, (source, date, clock, count, seeds) in CASES.items():
        d = root / name; meta = json.loads((d / 'result.json').read_text())
        assert (meta['recipe'], meta['name'], meta['source_control']) == ('maintenance-runtime-rng-v1', name, source)
        assert (meta['date'], meta['time'], meta['cpu_cycles']) == (date, clock, 200000)
        assert meta['binaries'] == BINARIES
        assert meta['copied_runtime_sha256'] == SHA(runtime)
        assert meta['payload_file_offset'] == 0xffb2 and meta['payload_hex'] == payload.hex()
        files = set(PINS[name]) | {'trace-commands.txt', 'trace-dosbox.log', 'DOSDATE.LOG', 'DOSTIME.LOG',
                                  'ENDDATE.LOG', 'ENDTIME.LOG', 'RETURN.LOG'}
        assert set(meta['files']) == files == {p.name for p in d.iterdir()} - {'result.json'}
        for n, digest in meta['files'].items(): assert SHA((d / n).read_bytes()) == digest, n
        for n, digest in PINS[name].items(): assert SHA(gzip.decompress((d / n).read_bytes())) == digest, 'observation pin'
        commands = ['date ' + date, 'time ' + clock, 'date > DOSDATE.LOG', 'time > DOSTIME.LOG',
                    'ytmaint > TRACE.BIN', 'echo PROBE_RETURNED > RETURN.LOG',
                    'date > ENDDATE.LOG', 'time > ENDTIME.LOG']
        assert (d / 'trace-commands.txt').read_text() == '\n'.join(commands) + '\n'
        verify_launch(d, 'trace', commands)
        day = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        assert read_date((d / 'DOSDATE.LOG').read_bytes()) == day == read_date((d / 'ENDDATE.LOG').read_bytes())
        assert read_time((d / 'DOSTIME.LOG').read_bytes()) == {'00:00:00': 0, '00:00:01': .98, '00:00:02': 1.97}[clock]
        assert 0 < read_time((d / 'ENDTIME.LOG').read_bytes()) - read_time((d / 'DOSTIME.LOG').read_bytes()) < 3
        assert (d / 'RETURN.LOG').read_bytes() == b'PROBE_RETURNED\r\n'
        for n in ('YTDATA.DAT', 'YTNEWS.DAT', 'YTNAME.DAT'):
            baseline = ROOT / 'research/yt-maint/initial-controls' / source / ('before-' + n + '.gz')
            assert gzip.decompress((d / ('before-' + n + '.gz')).read_bytes()) == gzip.decompress(baseline.read_bytes())
        raw = gzip.decompress((d / 'trace.bin.gz').read_bytes())
        events, phases = parse_trace(raw)
        assert len(events) == count and sum(k == 0xb352 for k, _, _ in events) == seeds
        after = gzip.decompress((d / 'after-YTDATA.DAT.gz').read_bytes())
        native = gzip.decompress((ROOT / 'research/yt-maint/initial-controls' / source / 'after-YTDATA.DAT.gz').read_bytes())
        assert SHA(native) == NATIVE_PINS[source]['after-YTDATA.DAT.gz'], 'paired native world pin'
        assert len(after) == len(native) == 568687
        changed = [i for i, (a, b) in enumerate(zip(after, native)) if a != b]
        assert all(51 <= i // 137 < 3051 and i % 137 in
                   set(range(81, 89)) | set(range(93, 97)) | set(range(105, 109))
                   for i in changed), 'bounded instrumented/native differences'
        assert len(changed) == {'midnight': 51, 'repeat': 51, 'new-year': 51,
                                'second-one': 16, 'second-two': 0}[name], 'measured perturbation'

        results[name] = (raw, events)
    assert results['midnight'] == results['repeat'], 'exact independent repeat'
    assert results['midnight'][1] == results['new-year'][1], 'measured date-independent stream'
    print('Verified five complete instrumented maintenance streams and declared patch provenance')


if __name__ == '__main__': verify(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)
