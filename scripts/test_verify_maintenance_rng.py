"""Corruption controls for runtime traces and their declared provenance."""
import contextlib
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_maintenance_rng import DEFAULT, parse_trace, verify


class MaintenanceRNGTests(unittest.TestCase):
    def test_retained_controls(self):
        with contextlib.redirect_stdout(io.StringIO()): verify()

    def test_trace_semantics(self):
        raw = gzip.decompress((DEFAULT / 'midnight/trace.bin.gz').read_bytes())
        first_draw = next(i for i in range(len(raw)-14) if raw[i:i+6] == b'\0RG!\x09\xb3')
        for name, offset in [('startup seed', 6), ('draw state', first_draw+6),
                             ('seed FAC', 10), ('event kind', 4)]:
            with self.subTest(name=name):
                altered = bytearray(raw); altered[offset] ^= 1
                with self.assertRaises(AssertionError): parse_trace(bytes(altered))
        for altered in (raw[:12], raw.replace(b'Daily Maintenance Completed OK', b'FAILED'),
                        raw.replace(b'Running planet maintenance', b'UNKNOWN PHASE')):
            with self.subTest(tail=altered[-15:]):
                with self.assertRaises(AssertionError): parse_trace(altered)

    def test_rehashed_evidence_corruptions(self):
        cases = [('trace.bin.gz', lambda b: gzip.compress(gzip.decompress(b)[:-40], mtime=0)),
                 ('after-YTDATA.DAT.gz', lambda b: gzip.compress(bytes(568687), mtime=0)),
                 ('before-YTNEWS.DAT.gz', lambda b: gzip.compress(b'forged', mtime=0)),
                 ('trace-dosbox.log', lambda b: b''),
                 ('trace-dosbox.log', lambda b: b.replace(b'fixed 200000 cycles.', b'fixed 100000 cycles.')),
                 ('trace-commands.txt', lambda b: b.replace(b'00:00:00', b'00:00:02')),
                 ('RETURN.LOG', lambda b: b'FAILED\r\n'),
                 ('DOSDATE.LOG', lambda b: b.replace(b'11/02/2026', b'11/03/2026'))]
        for filename, mutate in cases:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / 'controls'; shutil.copytree(DEFAULT, root)
                d = root / 'midnight'; p = d / filename; old = p.read_bytes(); new = mutate(old)
                self.assertNotEqual(new, old); p.write_bytes(new)
                meta = json.loads((d / 'result.json').read_text())
                meta['files'][filename] = hashlib.sha256(new).hexdigest()
                (d / 'result.json').write_text(json.dumps(meta))
                with self.assertRaises(AssertionError), contextlib.redirect_stdout(io.StringIO()): verify(root)

    def test_missing_repeat_and_forged_runtime(self):
        for missing in (True, False):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / 'controls'; shutil.copytree(DEFAULT, root)
                if missing: shutil.rmtree(root / 'repeat')
                else:
                    p = root / 'midnight/result.json'; meta = json.loads(p.read_text())
                    meta['copied_runtime_sha256'] = '0' * 64; p.write_text(json.dumps(meta))
                with self.assertRaises(AssertionError), contextlib.redirect_stdout(io.StringIO()): verify(root)


if __name__ == '__main__': unittest.main()
