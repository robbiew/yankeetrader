"""Trace original maintenance with a declared 60-byte copied-runtime hook."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
from recover_initial_maintenance import BINARIES, ROOT, launch

SHA = lambda b: hashlib.sha256(b).hexdigest()
CASES = {'midnight': ('baseline-split', '11/02/2026', '00:00:00'),
         'repeat': ('baseline-split', '11/02/2026', '00:00:00'),
         'second-one': ('second-one-split', '11/02/2026', '00:00:01'),
         'second-two': ('second-two-split', '11/02/2026', '00:00:02'),
         'new-year': ('new-year-split', '01/01/2027', '00:00:00')}
PAYLOAD = bytes.fromhex('a33502eb03 b80088 9c601e8bec ff361c00ff361a00ff363602ff36340236ff7614 '
                        '684721680052161f8bd4bb0100b90e00b440cd2183c40e1f619dc3')


def patched_runtime(original):
    assert SHA(original) == BINARIES['BRUN30.EXE']
    assert original[0xffb2:0xffee] == bytes(60)
    patched = bytearray(original)
    for site, entry, expected in ((0xb506, 0xfdb7, 'b80088'), (0xb54f, 0xfdb2, 'a33502')):
        assert original[site:site+3] == bytes.fromhex(expected)
        patched[site:site+3] = b'\xe8' + struct.pack('<H', (entry - (site - 512) - 3) & 65535)
    patched[0xffb2:0xffee] = PAYLOAD
    assert len(patched) == len(original) and patched[:512] == original[:512]
    return bytes(patched)


def run(destination):
    originals = {n: (ROOT / 'archive/dos-original' / n).read_bytes() for n in BINARIES}
    assert {n: SHA(b) for n, b in originals.items()} == BINARIES
    copied = patched_runtime(originals['BRUN30.EXE'])
    destination.mkdir(parents=True, exist_ok=False)
    for name, (source, date, clock) in CASES.items():
        d = destination / name; d.mkdir()
        (d / 'BRUN30.EXE').write_bytes(copied)
        (d / 'YTMAINT.EXE').write_bytes(originals['YTMAINT.EXE'])
        baseline = ROOT / 'research/yt-maint/initial-controls' / source
        for n in ('YTDATA.DAT', 'YTNEWS.DAT', 'YTNAME.DAT'):
            data = gzip.decompress((baseline / ('before-' + n + '.gz')).read_bytes())
            (d / n).write_bytes(data)
            (d / ('before-' + n + '.gz')).write_bytes(gzip.compress(data, mtime=0))
        commands = ['date ' + date, 'time ' + clock, 'date > DOSDATE.LOG', 'time > DOSTIME.LOG',
                    'ytmaint > TRACE.BIN', 'echo PROBE_RETURNED > RETURN.LOG',
                    'date > ENDDATE.LOG', 'time > ENDTIME.LOG']
        launch(d, commands, 'trace')
        raw = (d / 'TRACE.BIN').read_bytes()
        assert b'Daily Maintenance Completed OK' in raw and raw.startswith(b'\0RG!')
        (d / 'trace.bin.gz').write_bytes(gzip.compress(raw, mtime=0)); (d / 'TRACE.BIN').unlink()
        for p in list(d.iterdir()):
            if p.suffix.upper() in ('.DAT', '.ASC'):
                (d / ('after-' + p.name + '.gz')).write_bytes(gzip.compress(p.read_bytes(), mtime=0))
                p.unlink()
        for n in ('YTMAINT.EXE', 'BRUN30.EXE'): (d / n).unlink()
        meta = dict(recipe='maintenance-runtime-rng-v1', name=name, source_control=source,
                    date=date, time=clock, cpu_cycles=200000, binaries=BINARIES,
                    copied_runtime_sha256=SHA(copied), payload_file_offset=0xffb2,
                    payload_hex=PAYLOAD.hex(), files={p.name: SHA(p.read_bytes()) for p in sorted(d.iterdir())})
        (d / 'result.json').write_text(json.dumps(meta, indent=2) + '\n')
        print(name, len(raw), SHA(raw), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    run(parser.parse_args().destination.resolve())
